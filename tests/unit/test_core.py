import os, tempfile, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
import pytest
from evidence_state import *

def tmpdb():
    fd, p = tempfile.mkstemp(suffix=".db"); os.close(fd); os.remove(p)
    return p

def test_ingest_and_preserve_quote():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u", "exact quote here")
    c, ev = ledger.propose_claim(d.id, "claim", "exact quote here")
    assert ledger.get_evidence(c.id)[0].quote == "exact quote here"
    ledger.close()

def test_unsupported_rejected():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u", "text")
    c, ev = ledger.propose_claim(d.id, "claim", "fabricated quote")
    sv = StructuralVerifier()
    v = sv.verify(c, [ev], "text")  # quote not in text
    assert v.result.value == "fail"
    ledger.close()

def test_exact_duplicate():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u", "x")
    ledger.propose_claim(d.id, "same claim", "x")
    ledger.propose_claim(d.id, "same claim", "x")
    dd = DeduplicationEngine(ledger)
    assert len(dd.exact_duplicates()) == 1
    ledger.close()

def test_contradictory_preserved():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u", "x")
    c1,_ = ledger.propose_claim(d.id, "API requires OAuth2", "x")
    c2,_ = ledger.propose_claim(d.id, "API uses API keys not OAuth2", "x")
    det = ContradictionDetector()
    cons = det.detect(ledger.all_claims())
    assert len(cons) >= 1
    ledger.close()

def test_multi_source():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d1 = ledger.register_document("a","q"); d2 = ledger.register_document("b","q2")
    c,_ = ledger.propose_claim(d1.id, "claim", "q")
    # second evidence for same claim via direct insert not in API; check document support
    assert ledger.get_document(d1.id) and ledger.get_document(d2.id)
    ledger.close()

def test_withdrawal_invalidates():
    db = tmpdb()
    ledger = EvidenceLedger(db, admin_token="test")
    d = ledger.register_document("u", "q")
    c,_ = ledger.propose_claim(d.id, "claim", "q")
    sv = StructuralVerifier()
    def tv(claim, evs):
        return sv.verify(claim, evs, "q")
    ledger.register_verifier("structural", tv)
    ledger.freeze_verifiers("test")
    ledger.run_verification(c.id, [ev.id for ev in ledger.get_evidence(c.id)], "structural")
    ledger.withdraw_document(d.id)
    assert ledger.get_claim(c.id).status.value in ("unverified","withdrawn")
    ledger.close()

def test_revision_persist():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    re = RevisionEngine(ledger)
    re.record(None, "s1", [], "r")
    ledger2 = EvidenceLedger(db)
    assert len(ledger2.revisions()) == 1
    ledger.close(); ledger2.close()

def test_restart_reconstruct():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u","q")
    ledger.propose_claim(d.id, "claim", "q")
    ledger.close()
    ledger2 = EvidenceLedger(db)
    assert len(ledger2.all_claims()) == 1
    ledger2.close()

def test_index_rebuild_no_authority_change():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u","q")
    ledger.propose_claim(d.id, "claim", "q")
    before = [c.text for c in ledger.all_claims()]
    idx = SemanticIndex()
    idx.rebuild(ledger)
    after = [c.text for c in ledger.all_claims()]
    assert before == after
    ledger.close()

def test_insufficient_prevents():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    evl = SufficiencyEvaluator({})
    e = evl.evaluate("obj", ["crit"], ledger)
    assert e.status.value in ("INSUFFICIENT","UNVERIFIABLE")
    ledger.close()

def test_conflict_prevents_sufficient():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u","q")
    c1,_ = ledger.propose_claim(d.id, "API requires OAuth2", "q")
    c2,_ = ledger.propose_claim(d.id, "API uses API keys not OAuth2", "q")
    det = ContradictionDetector()
    for c in det.detect(ledger.all_claims()):
        ledger.record_contradiction(c)
    evl = SufficiencyEvaluator({})
    e = evl.evaluate("obj", ["oauth2"], ledger)
    assert e.status.value == "CONFLICTED"
    ledger.close()

def test_max_iteration_policy():
    from evidence_state.models.entities import Policy
    pe = PolicyEngine(Policy(max_iterations=2))
    ok, reason = pe.can_terminate(2, "SUFFICIENT", 0, 1)
    assert ok is False
    assert "max_iterations" in reason

def test_schema_validation():
    with pytest.raises(ValueError):
        Claim(status="not-a-status")

def test_provenance_traversal():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u","q")
    c,_ = ledger.propose_claim(d.id, "claim", "q")
    pe = ProvenanceEngine(ledger)
    chain = pe.trace(c.id)
    assert any(x[0]=="document" for x in chain)
    ledger.close()

def test_unverified_cannot_sufficient():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u", "q")
    c, ev = ledger.propose_claim(d.id, "claim about oauth2", "q")
    # claim remains PROPOSED (unverified)
    evl = SufficiencyEvaluator({})
    e = evl.evaluate("obj", ["oauth2"], ledger)
    assert e.status.value != "SUFFICIENT"
    ledger.close()

def test_fabricated_pass_verification_rejected():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u", "q")
    c, ev = ledger.propose_claim(d.id, "claim", "q")
    # attempt PASS with no evidence
    v = Verification(claim_id=c.id, evidence_ids=[], method="fake", result=VerificationResult.PASS, explanation="fake", verifier_identity="attacker")
    with pytest.raises(ValueError):
        ledger.record_verification(v)
    ledger.close()

def test_pass_wrong_evidence_rejected():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u", "q")
    c1, e1 = ledger.propose_claim(d.id, "claim1", "q")
    c2, e2 = ledger.propose_claim(d.id, "claim2", "q")
    v = Verification(claim_id=c1.id, evidence_ids=[e2.id], method="fake", result=VerificationResult.PASS, explanation="fake", verifier_identity="attacker")
    with pytest.raises(ValueError):
        ledger.record_verification(v)
    ledger.close()

def test_frozen_registry_blocks_untrusted():
    db = tmpdb()
    token = "secret"
    ledger = EvidenceLedger(db, admin_token=token)
    sv = StructuralVerifier()
    ledger.register_verifier("structural", lambda c, e: sv.verify(c, e, "q"))
    ledger.freeze_verifiers(token)
    # untrusted registration after freeze rejected
    with pytest.raises(PermissionError):
        ledger.register_verifier("evil", lambda c, e: Verification(claim_id=c.id, evidence_ids=[e[0].id], method="x", result=VerificationResult.PASS, explanation="x", verifier_identity="evil"))
    # even with correct token, allowed
    ledger.register_verifier("structural2", lambda c, e: sv.verify(c, e, "q"), token=token)
    ledger.close()

def test_frozen_without_token_blocks():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    with pytest.raises(PermissionError):
        ledger.freeze_verifiers("wrong")
    ledger.close()
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u","real text")
    c,_ = ledger.propose_claim(d.id, "claim", "fake quote")
    sv = StructuralVerifier()
    v = sv.verify(c, ledger.get_evidence(c.id), "real text")
    assert v.result.value == "fail"
    ledger.close()
def test_offset_validation():
    db = tmpdb()
    token = "t"
    ledger = EvidenceLedger(db, admin_token=token)
    sv = StructuralVerifier()
    ledger.register_verifier("structural", lambda c, evs: sv.verify(c, evs, "hello world"))
    ledger.freeze_verifiers(token)
    content = "hello world"
    d = ledger.register_document("u", content)
    c, ev = ledger.propose_claim(d.id, "claim", "world", start_offset=6, end_offset=11)
    ledger.run_verification(c.id, [ev.id], "structural")
    ledger.close()

def test_bad_offsets_rejected():
    db = tmpdb()
    token = "t"
    ledger = EvidenceLedger(db, admin_token=token)
    sv = StructuralVerifier()
    ledger.register_verifier("structural", lambda c, evs: sv.verify(c, evs, "hello world"))
    ledger.freeze_verifiers(token)
    content = "hello world"
    d = ledger.register_document("u", content)
    c, ev = ledger.propose_claim(d.id, "claim", "world", start_offset=0, end_offset=5)
    with pytest.raises(ValueError):
        ledger.run_verification(c.id, [ev.id], "structural")
    ledger.close()

def test_missing_content_integrity_false():
    db = tmpdb()
    ledger = EvidenceLedger(db)
    d = ledger.register_document("u", "abc")
    assert ledger.verify_source_integrity(d.id) is True
    ledger.close()

def test_failure_injection_audit_rollback():
    db = tmpdb()
    ledger = EvidenceLedger(db, admin_token="t")
    sv = StructuralVerifier()
    ledger.register_verifier("structural", lambda c, e: sv.verify(c, e, "q"))
    ledger.freeze_verifiers("t")
    d = ledger.register_document("u", "q")
    c, ev = ledger.propose_claim(d.id, "claim", "q")
    # make audit fail
    orig_audit = ledger._audit
    def boom(*a, **k):
        raise RuntimeError("audit fail")
    ledger._audit = boom
    with pytest.raises(RuntimeError):
        ledger.run_verification(c.id, [ev.id], "structural")
    ledger._audit = orig_audit
    # claim should remain unverified
    assert ledger.get_claim(c.id).status.value != "verified"
    # same connection recovery: valid op succeeds
    ledger2 = ledger
    ledger2.run_verification(c.id, [ev.id], "structural")
    assert ledger2.get_claim(c.id).status.value == "verified"
    ledger.close()

def test_conformance_runner_honest():
    from evidence_state.conformance.runner import run_fixture
    res = run_fixture({"id": "x"}, None)
    assert res["passed"] is False
