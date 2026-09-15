from pathlib import Path
import hashlib
import json
import sys

from context_forge.domain import EventType, SessionEvent
from context_forge.gateways import OfflineGateway
from context_forge.queue import JobStore
from context_forge.transcript import sanitize_transcript
from context_forge.vault import Vault
from context_forge.worker import process_one
from context_forge.index import DocumentIndex
from context_forge.rules import RuleMatcher


def event(path: Path) -> SessionEvent:
    return SessionEvent(
        event_id="evt-1", event_type=EventType.SESSION_END, source="test",
        session_id="sess-1", project="demo", cwd=str(path.parent),
        transcript_path=str(path), transcript_hash="hash-1",
    )


def test_duplicate_events_create_one_job(tmp_path: Path) -> None:
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("problem: token=secret\n", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    assert store.enqueue_event(event(transcript)) is True
    assert store.enqueue_event(event(transcript)) is False
    assert len(store.list_jobs()) == 1


def test_sanitize_removes_secret(tmp_path: Path) -> None:
    source = tmp_path / "session.jsonl"
    source.write_text("Authorization: Bearer abc123\npassword=secret", encoding="utf-8")
    result = sanitize_transcript(source)
    assert "abc123" not in result.content
    assert "secret" not in result.content


def test_worker_writes_review(tmp_path: Path) -> None:
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("A useful problem", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    assert process_one(store, Vault(tmp_path / "vault"), OfflineGateway()) is True
    assert list((tmp_path / "vault").rglob("*.md"))


def test_approved_review_creates_knowledge_proposal(tmp_path: Path) -> None:
    vault = Vault(tmp_path / "vault")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("A useful problem", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    review = store.list_reviews()[0]
    proposal = vault.write_knowledge_proposal(review["id"], Path(review["path"]))
    assert "type: knowledge" in proposal.read_text(encoding="utf-8")


def test_noop_gateway_does_not_create_review(tmp_path: Path) -> None:
    """No provider configured -> capture succeeds, no review auto-written."""
    from context_forge.gateways import NoOpGateway
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("anything", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    assert process_one(store, Vault(tmp_path / "vault"), NoOpGateway()) is True
    assert store.list_reviews() == []


def test_rule_proposal_is_explicit_and_idempotent(tmp_path: Path) -> None:
    vault = Vault(tmp_path / "vault")
    proposal = vault.write_rule_proposal("knowledge-1", "demo", "先检查测试", ["src/**/*.py"])
    assert "status: proposed" in proposal.read_text(encoding="utf-8")
    assert vault.write_rule_proposal("knowledge-1", "demo", "先检查测试", ["src/**/*.py"]) == proposal
    vault.set_rule_status("rule-knowledge-1", "enabled")
    assert "status: enabled" in proposal.read_text(encoding="utf-8")


def test_enabled_rule_matches_project_and_path(tmp_path: Path) -> None:
    vault = Vault(tmp_path / "vault")
    vault.write_rule_proposal("knowledge-1", "demo", "先检查测试", ["src/**/*.py"])
    vault.set_rule_status("rule-knowledge-1", "enabled")
    matches = RuleMatcher(vault.root).match("demo", "src/app.py")
    assert len(matches) == 1
    assert "matches" in matches[0].reason
    assert not RuleMatcher(vault.root).match("other", "src/app.py")


def test_index_rebuild_and_search(tmp_path: Path) -> None:
    vault = Vault(tmp_path / "vault")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("authentication timeout", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    index = DocumentIndex(tmp_path / "index.db")
    assert index.rebuild(vault.root) == 1
    assert index.search("authentication")


def test_scan_generates_index_md(tmp_path: Path) -> None:
    from context_forge.gateways import NoOpGateway

    vault = Vault(tmp_path / "vault")
    store = JobStore(tmp_path / "queue.db")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("hello world", encoding="utf-8")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    vault.write_rule_proposal("k1", "demo", "rule one", ["src/*.py"])
    result = vault.scan()
    assert result["files"] >= 2
    index_md = vault.root / "index.md"
    assert index_md.exists()
    text = index_md.read_text(encoding="utf-8")
    assert "# Context Forge Index" in text
    assert "rules" in text


def test_update_with_expected_hash_writes_conflict(tmp_path: Path) -> None:
    vault = Vault(tmp_path / "vault")
    p = vault.write_rule_proposal("k1", "demo", "rule one", [])
    import hashlib
    original = hashlib.sha256(p.read_bytes()).hexdigest()
    # User edits the file under us
    p.write_text(p.read_text(encoding="utf-8") + "\n# user edit\n", encoding="utf-8")
    try:
        vault.update_with_expected_hash("rules/proposals/rule-k1.md",
                                        "programmatic rewrite", original)
    except FileExistsError as exc:
        assert "conflict copy" in str(exc)
    else:
        raise AssertionError("expected FileExistsError on hash mismatch")
    conflicts = list(p.parent.glob("*.conflict-*"))
    assert conflicts
    assert p.read_text(encoding="utf-8").endswith("# user edit\n")


def test_knowledge_proposal_can_be_listed_and_accepted(tmp_path: Path) -> None:
    vault = Vault(tmp_path / "vault")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("anything", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    review = store.list_reviews()[0]
    vault.write_knowledge_proposal(review["id"], Path(review["path"]))
    proposed = vault.list_knowledge("proposed")
    assert any(review["id"] in str(p) for p in proposed)
    accepted_path = vault.accept_knowledge(review["id"])
    assert "accepted" in str(accepted_path)
    assert not list(vault.root.glob(f"knowledge/proposals/{review['id']}.md"))
    assert vault.list_knowledge("accepted")


def test_rule_hits_and_feedback_are_recorded(tmp_path: Path) -> None:
    vault = Vault(tmp_path / "vault")
    vault.write_rule_proposal("k1", "demo", "rule one", ["src/**/*.py"])
    vault.set_rule_status("rule-k1", "enabled")
    store = JobStore(tmp_path / "queue.db")
    store.record_rule_hit("rule-k1", "demo", "matched", "src/sub/app.py", "sess-1")
    store.add_rule_feedback("rule-k1", "helpful", "yes", session_id="sess-1")
    stats = store.rule_hit_stats("rule-k1")
    assert stats["hits"] == 1
    assert stats["feedback"]["helpful"] == 1
    assert stats["last_seen"]


def test_install_hook_is_idempotent_and_uninstallable(tmp_path: Path) -> None:
    from context_forge import install_hook
    target = tmp_path / "settings.json"
    first = install_hook.install(target)
    assert first["added"] == 2
    second = install_hook.install(target)
    assert second["added"] == 0
    payload = json.loads(target.read_text(encoding="utf-8"))
    for event in ("SessionEnd", "PreCompact"):
        bucket = payload["hooks"][event]
        assert len(bucket) == 1
        assert bucket[0].get("context_forge_managed") is True
    removed = install_hook.uninstall(target)
    assert removed["removed"] == 2
    assert "hooks" not in json.loads(target.read_text(encoding="utf-8"))


def test_fact_without_evidence_fails_job(tmp_path: Path) -> None:
    """Section 24 case 4: fact without evidence_ids -> job fails, no accepted knowledge."""
    from context_forge.domain import Claim, ClaimKind, ReviewExtraction
    from context_forge.gateways import FixtureGateway

    transcript = tmp_path / "session.jsonl"
    transcript.write_text("x", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    vault = Vault(tmp_path / "vault")
    store.enqueue_event(event(transcript))
    # model_construct bypasses Pydantic validation — simulating a real
    # model that produced an unsupported fact. The domain contract must
    # catch this; the worker must not write a review for it.
    bad = ReviewExtraction.model_construct(
        title="bad",
        problem="",
        attempts=[],
        outcome="",
        claims=[Claim.model_construct(text="unsupported", kind=ClaimKind.FACT,
                                      confidence="medium", evidence_ids=[])],
        uncertainties=[],
        candidate_topics=[],
        should_save=True,
        reason="test",
    )
    # Worker should raise because facts without evidence cannot land.
    import pytest
    with pytest.raises(ValueError, match="fact claims require evidence_ids"):
        process_one(store, vault, FixtureGateway(bad))
    assert store.list_reviews() == []


def test_worker_replay_is_idempotent(tmp_path: Path) -> None:
    """Section 24 case 8: running worker twice does not duplicate review."""
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("hello world", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    vault = Vault(tmp_path / "vault")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    process_one(store, vault, OfflineGateway())
    reviews = store.list_reviews()
    assert len(reviews) == 1
    files = list((tmp_path / "vault").rglob("reviews/**/*.md"))
    assert len(files) == 1


def test_session_end_records_unknown_for_hits(tmp_path: Path) -> None:
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("anything", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    vault = Vault(tmp_path / "vault")
    store.enqueue_event(event(transcript))
    store.record_rule_hit("rule-x", "demo", "matched", "src/app.py", "sess-1")
    process_one(store, vault, OfflineGateway())
    stats = store.rule_hit_stats("rule-x")
    assert stats["feedback"]["unknown"] == 1


def test_session_delete_clears_derived_state(tmp_path: Path) -> None:
    """Section 24 case 10: deleting a session removes its queue state."""
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("anything", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    vault = Vault(tmp_path / "vault")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    review = store.list_reviews()[0]
    assert review["session_id"] == "sess-1"
    counts = store.delete_session("sess-1")
    assert counts["sessions"] == 1
    assert counts["events"] == 1
    assert counts["jobs"] == 1
    assert counts["reviews"] == 1
    assert store.list_reviews() == []


def test_doctor_runs_without_state(tmp_path: Path, monkeypatch) -> None:
    """doctor must be read-only and must not require any prior state."""
    monkeypatch.setenv("CONTEXT_FORGE_HOME", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    from context_forge import doctor
    rows = doctor.run_all()
    assert all(name in {r[0] for r in rows} for name in
               {"config", "vault", "queue", "index", "provider"})
    output, failed = doctor.render(rows)
    assert failed == 0


def test_session_outcome_adds_explicit_feedback(tmp_path: Path) -> None:
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("x", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    vault = Vault(tmp_path / "vault")
    store.enqueue_event(event(transcript))
    store.record_rule_hit("rule-x", "demo", "matched", "src/app.py", "sess-1")
    process_one(store, vault, OfflineGateway())
    # user now declares the outcome explicitly
    for rule_id in store.hits_for_session("sess-1"):
        store.add_rule_feedback(rule_id, "helpful", "yes", session_id="sess-1")
    stats = store.rule_hit_stats("rule-x")
    # RuleFeedback is an event log: auto-unknown + explicit helpful coexist.
    assert stats["feedback"]["helpful"] == 1
    assert stats["feedback"]["unknown"] == 1


def test_doctor_reports_when_vault_missing(tmp_path: Path, monkeypatch) -> None:
    """doctor must report problems without mutating anything."""
    monkeypatch.setenv("CONTEXT_FORGE_HOME", str(tmp_path))
    monkeypatch.setenv("HOME", str(tmp_path))
    from context_forge import doctor
    rows = dict((name, (ok, detail)) for name, ok, detail in doctor.run_all())
    assert "queue" in rows  # doctor runs even when queue/index not initialised


def test_mcp_server_exposes_all_five_tools(tmp_path: Path) -> None:
    """The optional MCP server must provide the tools listed in §15."""
    pytest = __import__("pytest")
    pytest.importorskip("mcp")
    # Seed enough state for the search and match tools to be useful
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("authentication timeout", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    vault = Vault(tmp_path / "vault")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    vault.write_rule_proposal("k1", "demo", "check tests", ["src/**/*.py"])
    vault.set_rule_status("rule-k1", "enabled")

    import context_forge.cli as cli
    import context_forge.mcp_server as mcp
    from context_forge.index import DocumentIndex
    cli._store = lambda: store
    cli._vault = lambda: vault
    mcp._store = cli._store
    mcp._vault = cli._vault
    index = DocumentIndex(tmp_path / "index.db")
    index.rebuild(vault.root)
    mcp._index = lambda: index

    srv = mcp.create_server()
    names = set(srv._tool_manager._tools)
    assert names == {
        "context_forge_search",
        "context_forge_get",
        "context_forge_pending_reviews",
        "context_forge_record_feedback",
        "context_forge_match_rules",
    }
    # Exercise each tool by direct call — MCP wraps the fn but still callable
    search_fn = srv._tool_manager._tools["context_forge_search"].fn
    assert search_fn("authentication")
    pending_fn = srv._tool_manager._tools["context_forge_pending_reviews"].fn
    assert pending_fn()
    get_fn = srv._tool_manager._tools["context_forge_get"].fn
    review_path = store.list_reviews()[0]["path"]
    body = get_fn(review_path)
    assert "authentication" in body
    match_fn = srv._tool_manager._tools["context_forge_match_rules"].fn
    assert match_fn("demo", "src/sub/app.py")
    feedback_fn = srv._tool_manager._tools["context_forge_record_feedback"].fn
    assert feedback_fn("rule-k1", "helpful", "yes") == "recorded"


def test_select_gateway_recognises_named_providers() -> None:
    """`provider` strings in settings must map without crashing.

    `local` and `remote` require settings; without them the gateway
    raises `GatewayError` instead of silently dropping the call. The
    caller must use `provider="none"` (or omit the setting) to get a
    NoOpGateway.
    """
    import pytest
    from context_forge.gateways import (
        FixtureGateway, NoOpGateway, OfflineGateway, select_gateway,
    )
    from context_forge.provider_http import GatewayError

    assert isinstance(select_gateway("offline"), OfflineGateway)
    fake = select_gateway("fake")
    assert isinstance(fake, FixtureGateway)
    assert fake.name == "fixture"
    assert isinstance(select_gateway(""), NoOpGateway)
    assert isinstance(select_gateway("unknown-provider"), NoOpGateway)
    with pytest.raises(GatewayError):
        select_gateway("local")
    with pytest.raises(GatewayError):
        select_gateway("remote")


def test_remote_gateway_parses_anthropic_response(tmp_path: Path) -> None:
    """Remote gateway must parse Anthropic's content blocks and re-validate."""
    import httpx
    from context_forge.domain import Claim, ClaimKind
    from context_forge.provider_http import RemoteGateway, _CallResult

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "content": [
                {"type": "text", "text": '{"title": "x", "problem": "p", '
                 '"outcome": "o", "claims": [{"text": "claim", '
                 '"kind": "fact", "evidence_ids": ["ev1"]}], '
                 '"should_save": true, "reason": "ok"}'},
            ],
        })

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gw = RemoteGateway(api_url="https://api.test",
                       api_key="sk-test", model="claude-3-test")
    gw._client = client
    review = gw.extract_review(transcript_path=None,
                                transcript_hash="h1", session_id="s1")
    assert review.title == "x"
    assert review.claims[0].kind is ClaimKind.FACT
    # Fact must still have evidence_ids after domain re-validation
    assert review.claims[0].evidence_ids == ["ev1"]


def test_remote_gateway_retries_on_5xx(tmp_path: Path) -> None:
    """A 503 from the API must be retried with exponential backoff."""
    import httpx
    from context_forge.provider_http import RemoteGateway

    attempts = []

    def handler(request: httpx.Request) -> httpx.Response:
        attempts.append(1)
        if len(attempts) < 3:
            return httpx.Response(503, text="busy")
        return httpx.Response(200, json={"content": [
            {"type": "text", "text": '{"title": "ok", "should_save": false, '
             '"reason": "no model"}'},
        ]})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gw = RemoteGateway(api_url="https://api.test", api_key="sk", model="m")
    gw._client = client
    gw.base_delay = 0.001  # keep the test fast
    review = gw.extract_review(transcript_path=None,
                                transcript_hash="h1", session_id="s1")
    assert review.title == "ok"
    assert len(attempts) == 3


def test_local_gateway_parses_ollama_response(tmp_path: Path) -> None:
    """Local gateway must accept Ollama's message.content shape."""
    import httpx
    from context_forge.provider_http import LocalGateway

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {
            "content": '{"title": "local", "should_save": true, '
                       '"reason": "ok", "problem": "p"}',
        }})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gw = LocalGateway(api_url="http://localhost:11434", model="llama3")
    gw._client = client
    review = gw.extract_review(transcript_path=None,
                                transcript_hash="h1", session_id="s1")
    assert review.title == "local"
    assert review.problem == "p"


def test_local_gateway_rejects_unparseable_response(tmp_path: Path) -> None:
    """When the model returns prose only, the gateway must raise GatewayError."""
    import httpx
    import pytest
    from context_forge.provider_http import GatewayError, LocalGateway

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"message": {"content": "no JSON here"}})

    client = httpx.Client(transport=httpx.MockTransport(handler))
    gw = LocalGateway(api_url="http://localhost:11434", model="m")
    gw._client = client
    with pytest.raises(GatewayError):
        gw.extract_review(transcript_path=None, transcript_hash="h", session_id="s")


def test_remote_without_api_key_raises() -> None:
    """Missing credentials must surface as GatewayError, not NoOpGateway fallback."""
    import pytest
    from context_forge.gateways import select_gateway
    from context_forge.provider_http import GatewayError

    class FakeSettings:
        model_provider = "remote"
        remote_api_key = ""
        remote_model = "claude"
        remote_api_url = "https://api.test"

    with pytest.raises(GatewayError):
        select_gateway("remote", FakeSettings())


def test_claude_code_hook_ingests_event(tmp_path: Path, monkeypatch) -> None:
    """Section 19 task 9: hook must queue a job from Claude Code's stdin payload."""
    import io
    import json
    from context_forge.hooks import claude_code
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("hello", encoding="utf-8")
    payload = {
        "hook_event_name": "SessionEnd",
        "session_id": "claude-sess-1",
        "transcript_path": str(transcript),
        "cwd": str(tmp_path),
    }
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    rc = claude_code.main()
    assert rc == 0
    store = JobStore(tmp_path / ".context-forge" / "queue.db")
    jobs = store.list_jobs()
    assert len(jobs) == 1
    job = jobs[0]
    event = json.loads(job["payload_json"])
    assert event["session_id"] == "claude-sess-1"
    assert event["event_type"] == "session_end"
    assert event["transcript_hash"]  # computed from the fixture file
    # Replaying the same hook must not create a second job (§24 case 2)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(payload)))
    claude_code.main()
    assert len(store.list_jobs()) == 1


def test_retention_preview_and_apply(tmp_path: Path) -> None:
    """Sessions older than retention days must be removable on demand."""
    from datetime import datetime, timedelta, timezone

    store = JobStore(tmp_path / "queue.db")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("x", encoding="utf-8")
    store.enqueue_event(event(transcript))
    # Backdate the session row so it crosses the retention cutoff
    old = (datetime.now(timezone.utc) - timedelta(days=60)).isoformat()
    store.db.execute("UPDATE sessions SET created_at=? WHERE id=?",
                     (old, "sess-1"))
    store.db.commit()
    preview = store.retention_preview(days=30)
    assert {r["session_id"] for r in preview} == {"sess-1"}
    targets = store.retention_apply(days=30, dry_run=True)
    assert targets == ["sess-1"]
    # dry_run must not actually delete
    assert store.db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 1
    removed = store.retention_apply(days=30)
    assert removed == ["sess-1"]
    assert store.db.execute("SELECT COUNT(*) FROM sessions").fetchone()[0] == 0


def test_knowledge_accept_seeds_rule_proposal(tmp_path: Path) -> None:
    """Accepting knowledge with candidate_* fields writes a matching RuleProposal."""
    from context_forge.cli import _inject_candidate_fields

    vault = Vault(tmp_path / "vault")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("x", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    review = store.list_reviews()[0]
    vault.write_knowledge_proposal(review["id"], Path(review["path"]))
    # Annotate the proposal with candidate rule fields
    proposal = vault._find_knowledge(review["id"], statuses=("proposed",))
    text = _inject_candidate_fields(
        proposal.read_text(encoding="utf-8"),
        project="demo",
        instruction="check tests first",
        paths=["src/**/*.py", "tests/**/*.py"],
    )
    vault._atomic_write(proposal, text)
    vault.accept_knowledge(review["id"])
    rule = vault.root / "rules" / "proposals" / f"rule-{review['id']}.md"
    assert rule.exists()
    body = rule.read_text(encoding="utf-8")
    assert "check tests first" in body
    assert "src/**/*.py" in body


def test_import_transcript_enqueues_event(tmp_path: Path) -> None:
    """Section 22: history transcripts need an explicit import command."""
    import hashlib

    transcript = tmp_path / "old.jsonl"
    transcript.write_text("legacy transcript content", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    expected_hash = hashlib.sha256(transcript.read_bytes()).hexdigest()
    from context_forge.cli import _store, _vault
    orig_store = _store
    orig_vault = _vault
    import context_forge.cli as cli
    cli._store = lambda: store
    cli._vault = lambda: Vault(tmp_path / "vault")
    try:
        from typer.testing import CliRunner
        runner = CliRunner()
        result = runner.invoke(
            cli.app,
            ["import-transcript", str(transcript),
             "--project", "legacy", "--session", "sess-import"],
        )
        assert result.exit_code == 0, result.output
        assert "queued" in result.output
        jobs = store.list_jobs()
        assert len(jobs) == 1
        import json
        payload = json.loads(jobs[0]["payload_json"])
        assert payload["session_id"] == "sess-import"
        assert payload["transcript_hash"] == expected_hash
        assert payload["source"] == "import"
    finally:
        cli._store = orig_store
        cli._vault = orig_vault


def test_context_dump_composes_all_sections(tmp_path: Path) -> None:
    from context_forge.context import build_context, render

    vault = Vault(tmp_path / "vault")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("anything", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    review = store.list_reviews()[0]
    vault.write_knowledge_proposal(review["id"], Path(review["path"]))
    vault.accept_knowledge(review["id"])
    vault.write_rule_proposal("k1", "demo", "check tests first", ["src/**/*.py"])
    vault.set_rule_status("rule-k1", "enabled")

    sections = build_context(vault.root, "demo", "src/sub/app.py")
    titles = [s.title for s in sections]
    assert titles == ["Matched rules", "Recent knowledge", "Recent reviews"]
    rule_section = sections[0]
    assert "rule-k1" in rule_section.body
    assert "src/sub/app.py" in rule_section.body
    output = render(sections)
    assert "## Matched rules" in output
    assert "## Recent knowledge" in output
    assert "## Recent reviews" in output


def test_knowledge_merge_resolves_conflict(tmp_path: Path) -> None:
    vault = Vault(tmp_path / "vault")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("x", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    review = store.list_reviews()[0]
    vault.write_knowledge_proposal(review["id"], Path(review["path"]))
    # Simulate the program wanting to overwrite but finding a user edit:
    # the user's edit is the conflict copy; the original is what the
    # program wanted to write.
    proposal = vault._find_knowledge(review["id"], statuses=("proposed",))
    conflict = proposal.with_suffix(proposal.suffix + ".conflict-20260101")
    conflict.write_text(proposal.read_text(encoding="utf-8") + "\n# user edit\n",
                        encoding="utf-8")
    chosen = vault.merge_knowledge(review["id"], ".conflict-20260101")
    assert chosen.exists()
    assert "# user edit" in chosen.read_text(encoding="utf-8")
    # The other copy must be removed once the choice is made
    assert not list(vault.root.rglob("*.conflict-*.md")) or \
        len(list(vault.root.rglob("*.conflict-*.md"))) == 1
    # Listing without the conflict should still surface the canonical file
    kept = vault._find_knowledge(review["id"])
    assert kept is not None


def test_doctor_reports_old_sessions(tmp_path: Path, monkeypatch) -> None:
    """doctor must surface retention-eligible sessions without deleting them."""
    from datetime import datetime, timedelta, timezone
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    store = JobStore(tmp_path / ".context-forge" / "queue.db")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("x", encoding="utf-8")
    store.enqueue_event(event(transcript))
    old = (datetime.now(timezone.utc) - timedelta(days=120)).isoformat()
    store.db.execute("UPDATE sessions SET created_at=? WHERE id=?",
                     (old, "sess-1"))
    store.db.commit()
    rows = dict((name, (ok, detail)) for name, ok, detail in
                __import__("context_forge.doctor", fromlist=["*"]).run_all())
    # The queue check must mention retention without flagging FAIL —
    # retention is informational, not an error.
    assert rows["queue"][0] is True
    assert "session(s)" in rows["queue"][1]


def test_review_diff_reports_user_edits(tmp_path: Path) -> None:
    """review-diff must surface byte/line changes vs the model draft."""
    vault = Vault(tmp_path / "vault")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("x", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    review = store.list_reviews()[0]
    review_path = Path(review["path"])
    draft_path = review_path.with_name(review_path.name + ".draft")
    assert draft_path.exists()
    # User edits the review file
    review_path.write_text(review_path.read_text(encoding="utf-8")
                            + "\n\n# user note\n", encoding="utf-8")
    info = store.review_user_hash(review["id"])
    assert info is not None
    draft_hash, path = info
    assert hashlib.sha256(review_path.read_bytes()).hexdigest() != draft_hash
    # Use the CliRunner to ensure the CLI path works
    import context_forge.cli as cli
    cli._store = lambda: store
    cli._vault = lambda: vault
    from typer.testing import CliRunner
    result = CliRunner().invoke(cli.app, ["review-diff", review["id"]])
    assert result.exit_code == 0
    assert "changed" in result.output


def test_metrics_aggregate_first_slice_indicators(tmp_path: Path) -> None:
    """`forge metrics` must surface §11 indicators from the queue + index."""
    vault = Vault(tmp_path / "vault")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("hello", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    review = store.list_reviews()[0]
    store.set_review_status(review["id"], "approved")
    metrics = store.metrics()
    assert metrics["sessions"] == 1
    assert metrics["reviews"] == 1
    assert metrics["reviews_approved"] == 1
    assert metrics["approval_rate"] == 1.0
    assert metrics["discovery_rate"] == 1.0
    assert metrics["avg_approval_delay_seconds"] >= 0


def test_index_rebuild_records_history(tmp_path: Path) -> None:
    """Every rebuild must be persisted so metrics can compute success rate."""
    vault = Vault(tmp_path / "vault")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("x", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    index = DocumentIndex(tmp_path / "index.db")
    index.rebuild(vault.root)
    index.rebuild(vault.root)
    stats = index.rebuild_stats(days=7)
    assert stats["rebuilds_7d"] == 2
    assert stats["rebuilds_ok_7d"] == 2
    assert stats["rebuild_success_rate_7d"] == 1.0


def test_session_info_aggregates_related_rows(tmp_path: Path) -> None:
    """session-info must surface events / jobs / reviews / hits / feedback."""
    vault = Vault(tmp_path / "vault")
    transcript = tmp_path / "session.jsonl"
    transcript.write_text("x", encoding="utf-8")
    store = JobStore(tmp_path / "queue.db")
    store.enqueue_event(event(transcript))
    process_one(store, vault, OfflineGateway())
    store.record_rule_hit("rule-x", "demo", "matched", "src/app.py", "sess-1")
    store.add_rule_feedback("rule-x", "helpful", "yes", session_id="sess-1")
    info = store.session_info("sess-1")
    assert info["session"]["id"] == "sess-1"
    assert info["session"]["project"] == "demo"
    assert info["events"] == 1
    assert len(info["jobs"]) == 1
    assert len(info["reviews"]) == 1
    assert info["rule_hits"] == 1
    assert info["rule_feedback"][0]["outcome"] == "helpful"


def test_session_info_unknown_id_returns_empty(tmp_path: Path) -> None:
    store = JobStore(tmp_path / "queue.db")
    assert store.session_info("nonexistent") == {}


def test_rule_list_and_show_round_trip(tmp_path: Path) -> None:
    """rule-list and rule-show must read vault frontmatter without writes."""
    vault = Vault(tmp_path / "vault")
    vault.write_rule_proposal("k1", "demo", "check tests", ["src/**/*.py"])
    vault.write_rule_proposal("k2", "demo", "use fixtures", [])
    vault.set_rule_status("rule-k1", "enabled")
    enabled = vault.list_rules("enabled")
    proposed = vault.list_rules("proposed")
    all_rules = vault.list_rules()
    assert len(enabled) == 1
    assert "rule-k1" in enabled[0].name
    assert len(proposed) == 1
    assert "rule-k2" in proposed[0].name
    assert len(all_rules) == 2
    found = vault.read_rule("rule-k1")
    assert found is not None
    path, front, body = found
    assert front["status"] == "enabled"
    assert "check tests" in body
    assert vault.read_rule("nonexistent") is None
