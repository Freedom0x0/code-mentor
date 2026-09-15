from __future__ import annotations

from pathlib import Path

import typer

from .domain import SessionEvent
from .config import load_settings
from .queue import JobStore
from .index import DocumentIndex
from .vault import Vault
from .worker import process_one
from .gateways import select_gateway
import hashlib
from .rules import RuleMatcher

app = typer.Typer(no_args_is_help=True)
worker_app = typer.Typer(no_args_is_help=True)
app.add_typer(worker_app, name="worker")


def _store() -> JobStore:
    home = Path.home() / ".context-forge"
    return JobStore(home / "queue.db")


def _vault() -> Vault:
    settings = load_settings()
    return Vault(settings.root if settings else Path.home() / ".context-forge" / "vault")


def _index() -> DocumentIndex:
    vault = _vault().root
    key = hashlib.sha256(str(vault).encode("utf-8")).hexdigest()[:16]
    return DocumentIndex(Path.home() / ".context-forge" / f"index-{key}.db")


@app.command()
def capture(event_file: Path) -> None:
    """Queue a normalized hook event without calling a model."""
    event = SessionEvent.model_validate_json(event_file.read_text(encoding="utf-8"))
    created = _store().enqueue_event(event)
    typer.echo("queued" if created else "duplicate")


@app.command("jobs")
def jobs() -> None:
    """List queued and completed jobs."""
    for row in _store().list_jobs():
        typer.echo(f"{row['id']}\t{row['status']}\tattempts={row['attempts']}")


@app.command()
def doctor() -> None:
    """Check that the local queue is usable."""
    store = _store()
    typer.echo(f"queue: {store.path}")
    typer.echo(f"jobs: {len(store.list_jobs())}")
    settings = load_settings()
    if settings:
        settings.validate_vault()
        typer.echo(f"vault: {settings.root}")
    else:
        typer.echo("config: not found (using local default vault)")


@app.command("scan")
def scan() -> None:
    """Rebuild the local full-text index and regenerate index.md."""
    result = _vault().scan()
    typer.echo(f"indexed {result['files']} documents; index.md generated")


@app.command("watch")
def watch(interval: int = typer.Option(5, "--interval", min=1),
          iterations: int = typer.Option(0, "--iterations", min=0)) -> None:
    """Poll the vault and rebuild the index when files change.

    `iterations=0` runs forever; any positive number stops after that many
    cycles. The watcher compares mtimes and re-emits index.md + FTS only
    when something changed.
    """
    import time

    vault = _vault()
    index = _index()
    last_mtime = 0.0
    cycle = 0
    while iterations == 0 or cycle < iterations:
        mtime = max((p.stat().st_mtime for p in vault.root.rglob("*.md")
                     if p.name != "index.md"), default=0.0)
        if mtime > last_mtime:
            count = index.rebuild(vault.root)
            from .index import write_index
            write_index(vault.root)
            typer.echo(f"re-indexed {count} documents")
            last_mtime = mtime
        cycle += 1
        if iterations == 0 or cycle < iterations:
            time.sleep(interval)


@app.command("search")
def search(query: str) -> None:
    """Search indexed Markdown documents."""
    index = _index()
    for row in index.search(query):
        typer.echo(f"{row['path']}\t{row['snippet']}")


@app.command("review-list")
def review_list() -> None:
    """List generated review files."""
    for row in _store().list_reviews():
        typer.echo(f"{row['id']}\t{row['status']}\t{row['path']}")


@app.command("review-approve")
def review_approve(review_id: str) -> None:
    """Approve a generated review without overwriting its source."""
    reviews = [row for row in _store().list_reviews() if row["id"] == review_id]
    if not reviews:
        raise typer.BadParameter(f"review not found: {review_id}")
    store = _store()
    row = reviews[0]
    _vault().write_knowledge_proposal(review_id, Path(row["path"]))
    store.set_review_status(review_id, "approved")
    typer.echo(f"approved {review_id}")


@app.command("review-reject")
def review_reject(review_id: str) -> None:
    """Reject a generated review while retaining its audit record."""
    reviews = [row for row in _store().list_reviews() if row["id"] == review_id]
    if not reviews:
        raise typer.BadParameter(f"review not found: {review_id}")
    _store().set_review_status(review_id, "rejected")
    typer.echo(f"rejected {review_id}")


@app.command("knowledge-list")
def knowledge_list(status: str = typer.Option("proposed", "--status")) -> None:
    """List knowledge items filtered by status."""
    for path in _vault().list_knowledge(status):
        typer.echo(str(path.relative_to(_vault().root)))


@app.command("knowledge-show")
def knowledge_show(knowledge_id: str) -> None:
    """Print the content of a knowledge item."""
    found = _vault()._find_knowledge(knowledge_id)
    if found is None:
        raise typer.BadParameter(f"knowledge not found: {knowledge_id}")
    typer.echo(found.read_text(encoding="utf-8"), nl=False)


@app.command("knowledge-accept")
def knowledge_accept(knowledge_id: str) -> None:
    """Accept a knowledge proposal and move it to knowledge/accepted/."""
    path = _vault().accept_knowledge(knowledge_id)
    typer.echo(str(path.relative_to(_vault().root)))


@app.command("rule-propose")
def rule_propose(knowledge_id: str, project: str, instruction: str) -> None:
    """Create a reviewable rule proposal from accepted knowledge."""
    path = _vault().write_rule_proposal(knowledge_id, project, instruction)
    typer.echo(str(path))


@app.command("rule-enable")
def rule_enable(rule_id: str) -> None:
    path = _vault().set_rule_status(rule_id, "enabled")
    typer.echo(str(path))


@app.command("rule-disable")
def rule_disable(rule_id: str) -> None:
    path = _vault().set_rule_status(rule_id, "disabled")
    typer.echo(str(path))


@app.command("rule-feedback")
def rule_feedback(rule_id: str, outcome: str, note: str = "") -> None:
    if outcome not in {"helpful", "harmful", "irrelevant", "unknown"}:
        raise typer.BadParameter("outcome must be helpful, harmful, irrelevant, or unknown")
    _store().add_rule_feedback(rule_id, outcome, note or None)
    typer.echo(f"recorded {rule_id}: {outcome}")


@app.command("rule-match")
def rule_match(project: str, changed_path: str = "",
               session_id: str = typer.Option("", "--session"),
               record: bool = typer.Option(False, "--record")) -> None:
    """Show enabled rules that apply to a project and optional path."""
    matches = RuleMatcher(_vault().root).match(project, changed_path or None)
    if record:
        store = _store()
        for match in matches:
            store.record_rule_hit(
                match.rule_id, project, match.reason,
                changed_path or None, session_id or None,
            )
    for match in matches:
        typer.echo(f"{match.rule_id}\t{match.reason}\t{match.path}")


@app.command("rule-stats")
def rule_stats(rule_id: str) -> None:
    """Show hit and feedback counts for a single rule."""
    stats = _store().rule_hit_stats(rule_id)
    typer.echo(f"hits: {stats['hits']}")
    typer.echo(f"last_seen: {stats['last_seen'] or 'never'}")
    for outcome, count in stats["feedback"].items():
        typer.echo(f"feedback {outcome}: {count}")


@worker_app.command("run")
def worker_run(once: bool = typer.Option(False, "--once")) -> None:
    """Process queued review jobs."""
    if not once:
        raise typer.BadParameter("only --once is supported in the MVP")
    home = Path.home() / ".context-forge"
    settings = load_settings()
    provider = settings.model_provider if settings else "none"
    gateway = select_gateway(provider)
    processed = process_one(_store(), _vault(), gateway)
    typer.echo("processed" if processed else "empty")


@app.command("install-hook")
def install_hook(target: Path = typer.Option(None, "--target"),
                  uninstall: bool = typer.Option(False, "--uninstall")) -> None:
    """Install or remove the Claude Code SessionEnd/PreCompact hooks."""
    from . import install_hook as installer

    result = installer.uninstall(target) if uninstall else installer.install(target)
    if uninstall:
        typer.echo(f"removed {result['removed']} hook entries at {result['path']}")
    else:
        typer.echo(f"added {result['added']} hook entries at {result['path']}")


if __name__ == "__main__":
    app()
