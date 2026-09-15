from pathlib import Path
import json

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
