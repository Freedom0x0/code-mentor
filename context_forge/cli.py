from __future__ import annotations

import os
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
    """Run read-only diagnostics for vault, queue, index and provider."""
    from . import doctor as diag
    rows = diag.run_all()
    output, failed = diag.render(rows)
    typer.echo(output)
    if failed:
        raise typer.Exit(code=1)


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


@app.command("knowledge-edit")
def knowledge_edit(knowledge_id: str, editor: str = typer.Option("", "--editor")) -> None:
    """Open a knowledge proposal in $EDITOR (or the value of --editor).

    Records the file hash before and after the edit; if the hash changed,
    the FTS index is rebuilt on the next `forge scan`. The file is the
    source of truth — this command never writes for the user.
    """
    import hashlib
    import subprocess

    found = _vault()._find_knowledge(knowledge_id)
    if found is None:
        raise typer.BadParameter(f"knowledge not found: {knowledge_id}")
    chosen = editor or os.environ.get("EDITOR") or "notepad"
    before = hashlib.sha256(found.read_bytes()).hexdigest()
    try:
        subprocess.run([chosen, str(found)], check=True)
    except FileNotFoundError as exc:
        raise typer.BadParameter(f"editor not found: {chosen}") from exc
    after = hashlib.sha256(found.read_bytes()).hexdigest()
    if before == after:
        typer.echo("no changes")
    else:
        typer.echo("changed — run forge scan to refresh the index")


@app.command("knowledge-accept")
def knowledge_accept(knowledge_id: str,
                      rule_project: str = typer.Option("", "--rule-project"),
                      rule_instruction: str = typer.Option("", "--rule-instruction"),
                      rule_paths: str = typer.Option("", "--rule-paths")) -> None:
    """Accept a knowledge proposal and move it to knowledge/accepted/.

    If `--rule-project` and `--rule-instruction` are given, also seed a
    matching `RuleProposal` so the user can `forge rule-enable` directly.
    """
    vault = _vault()
    paths = [p.strip() for p in rule_paths.split(",") if p.strip()]
    if rule_project or rule_instruction:
        if not (rule_project and rule_instruction):
            raise typer.BadParameter(
                "rule_project and rule_instruction must be set together"
            )
        # Write the candidate fields into the proposal frontmatter before accept
        proposal = vault._find_knowledge(knowledge_id, statuses=("proposed",))
        if proposal is not None:
            text = proposal.read_text(encoding="utf-8")
            text = _inject_candidate_fields(
                text, rule_project, rule_instruction, paths,
            )
            vault._atomic_write(proposal, text)
    path = vault.accept_knowledge(knowledge_id)
    typer.echo(str(path.relative_to(vault.root)))


def _inject_candidate_fields(text: str, project: str, instruction: str,
                              paths: list[str]) -> str:
    """Append or replace `candidate_*` lines in a knowledge proposal frontmatter."""
    from .index import parse_frontmatter
    front, body = parse_frontmatter(text)
    keys = {k: v for k, v in front.items()
            if not k.startswith("candidate_")}
    keys["candidate_project"] = project
    keys["candidate_instruction"] = instruction
    keys["candidate_paths"] = ",".join(paths)
    lines = "\n".join(f"{k}: {v}" for k, v in keys.items())
    return f"---\n{lines}\n---\n\n{body.lstrip()}"


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
    gateway = select_gateway(provider, settings)
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


@app.command("provider-check")
def provider_check() -> None:
    """Ping the configured model provider and report reachability.

    For `remote`: hits Anthropic /v1/messages with a tiny prompt.
    For `local`: hits Ollama /api/chat with a tiny prompt.
    Anything else reports the gateway that would be used and exits 0.
    """
    from .provider_http import GatewayError
    settings = load_settings()
    provider = settings.model_provider if settings else "none"
    if provider not in {"remote", "local"}:
        typer.echo(f"provider={provider}; no live check needed")
        return
    try:
        gateway = select_gateway(provider, settings)
    except GatewayError as exc:
        typer.echo(f"provider={provider} FAILED to construct: {exc}")
        raise typer.Exit(code=1)
    # Minimal call to confirm reachability. The model returns nothing useful
    # but a 200 response proves auth + network + model name are valid.
    try:
        gateway._post(  # type: ignore[attr-defined]
            url=gateway.api_url,  # type: ignore[attr-defined]
            headers={"content-type": "application/json"},
            body={"model": gateway.model,  # type: ignore[attr-defined]
                  "max_tokens": 8,
                  "messages": [{"role": "user", "content": "ping"}]},
        )
    except GatewayError as exc:
        typer.echo(f"provider={provider} UNREACHABLE: {exc}")
        raise typer.Exit(code=1)
    typer.echo(f"provider={provider} OK ({gateway.name})")


@app.command("session-delete")
def session_delete(session_id: str) -> None:
    """Remove a session and all its derived queue state.

    Does NOT delete files on disk; callers should also clean vault files
    manually or rely on retention. The FTS index should be rebuilt after.
    """
    counts = _store().delete_session(session_id)
    for table, n in counts.items():
        typer.echo(f"{table}: {n}")


@app.command("session-outcome")
def session_outcome(session_id: str, outcome: str,
                    note: str = typer.Option("", "--note")) -> None:
    """Record an explicit outcome for every rule hit in a session.

    Overrides any auto-recorded `unknown` for that session.
    """
    if outcome not in {"helpful", "harmful", "irrelevant", "unknown"}:
        raise typer.BadParameter("outcome must be helpful, harmful, irrelevant, or unknown")
    store = _store()
    hits = store.hits_for_session(session_id)
    if not hits:
        typer.echo(f"no rule hits recorded for {session_id}")
        return
    for rule_id in hits:
        store.add_rule_feedback(rule_id, outcome, note or None, session_id=session_id)
    typer.echo(f"recorded {outcome} for {len(hits)} rule hit(s)")


@app.command("retention")
def retention(days: int = typer.Option(30, "--days", min=0),
               dry_run: bool = typer.Option(False, "--dry-run")) -> None:
    """List or delete sessions older than `--days` (default 30)."""
    targets = _store().retention_apply(days, dry_run=dry_run)
    verb = "would delete" if dry_run else "deleted"
    typer.echo(f"{verb} {len(targets)} session(s)")
    for sid in targets:
        typer.echo(f"  {sid}")


@app.command("import-transcript")
def import_transcript(path: Path,
                       project: str = typer.Option("", "--project"),
                       session_id: str | None = typer.Option(None, "--session")) -> None:
    """Backfill an old transcript into the queue without a live hook.

    Computes a transcript hash, constructs a SessionEvent and enqueues a
    job. Use this to migrate history captured before Context Forge was
    installed (§22).
    """
    import hashlib

    if not path.exists():
        raise typer.BadParameter(f"transcript not found: {path}")
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    from .domain import EventType, SessionEvent
    from .config import load_settings
    cwd = str(path.parent)
    settings = load_settings()
    proj = project or (settings.root.name if settings else path.parent.name)
    sid = session_id or f"import-{digest[:12]}"
    event = SessionEvent(
        event_id=f"evt-import-{digest[:12]}",
        event_type=EventType.SESSION_END,
        source="import",
        session_id=sid,
        project=proj,
        cwd=cwd,
        transcript_path=str(path),
        transcript_hash=digest,
    )
    queued = _store().enqueue_event(event)
    typer.echo("queued" if queued else "duplicate")


@app.command("context")
def context_cmd(project: str, changed_path: str = typer.Option("", "--path")) -> None:
    """Compose one context dump for the given project and optional path.

    Combines enabled rules matching the scope with recent accepted
    knowledge and recent reviews. Output is plain text suitable for
    pasting into an LLM prompt.
    """
    from .context import build_context, render
    sections = build_context(_vault().root, project,
                              changed_path or None)
    typer.echo(render(sections), nl=False)


@app.command("knowledge-merge")
def knowledge_merge(knowledge_id: str,
                     keep: str = typer.Option(..., "--keep",
                                               help="proposed | accepted | <suffix>")) -> None:
    """Resolve a conflict by choosing one of the `.conflict-*` copies."""
    path = _vault().merge_knowledge(knowledge_id, keep)
    typer.echo(str(path.relative_to(_vault().root)))


if __name__ == "__main__":
    app()
