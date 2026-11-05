from __future__ import annotations
import tempfile, os, json
from ..ledger.sqlite_ledger import EvidenceLedger
from ..verification.verifier import StructuralVerifier

def _validate_fixture(fixture):
    if not isinstance(fixture, dict):
        raise ValueError("fixture must be object")
    if "id" not in fixture:
        raise ValueError("missing id")

def run_fixture(fixture, tmp_path=None):
    _validate_fixture(fixture)
    tmp = tmp_path or tempfile.mkdtemp()
    db = os.path.join(tmp, "cf.db")
    fid = fixture.get("id")
    if fid != "ESP-CF-002":
        return {"id": fid, "passed": False, "reason": "unsupported fixture"}
    # fixture-driven inputs with defaults
    doc_content = fixture.get("document_content", "real text")
    claim_text = fixture.get("claim", "claim")
    quote = fixture.get("quote", "fake quote")
    expected = fixture.get("expected_result", "verification_fail")
    ledger = EvidenceLedger(db, admin_token="t")
    try:
        sv = StructuralVerifier()
        ledger.register_verifier("structural", lambda c, evs: sv.verify(c, evs, doc_content))
        ledger.freeze_verifiers("t")
        d = ledger.register_document("u", doc_content)
        c, ev = ledger.propose_claim(d.id, claim_text, quote)
        try:
            ledger.run_verification(c.id, [ev.id], "structural")
            actual = "pass"
        except ValueError as e:
            actual = "fail" if "fabricated quotation" in str(e) else f"other_error:{e}"
        passed = (actual == "fail" and expected == "verification_fail") or (actual == "pass" and expected == "verification_pass")
        return {"id": fid, "passed": passed, "actual": actual, "expected": expected}
    finally:
        ledger.close()
