from __future__ import annotations
import tempfile, os
from ..ledger.sqlite_ledger import EvidenceLedger
from ..verification.verifier import StructuralVerifier

REQUIRED = ["id", "document_content", "claim", "quote", "expected_result"]

def _validate_fixture(fixture):
    if not isinstance(fixture, dict):
        raise ValueError("fixture must be object")
    for k in REQUIRED:
        if k not in fixture:
            raise ValueError(f"missing {k}")
    if fixture["expected_result"] not in ("verification_fail", "verification_pass"):
        raise ValueError("invalid expected_result")

def run_fixture(fixture, tmp_path=None):
    _validate_fixture(fixture)
    tmp = tmp_path or tempfile.mkdtemp()
    db = os.path.join(tmp, "cf.db")
    fid = fixture["id"]
    if fid != "ESP-CF-002":
        return {"id": fid, "passed": False, "reason": "unsupported fixture"}
    doc_content = fixture["document_content"]
    claim_text = fixture["claim"]
    quote = fixture["quote"]
    expected = fixture["expected_result"]
    ledger = EvidenceLedger(db, admin_token="t")
    try:
        sv = StructuralVerifier()
        ledger.register_verifier("structural", lambda c, evs: sv.verify(c, evs, doc_content))
        ledger.freeze_verifiers("t")
        d = ledger.register_document("u", doc_content)
        c, ev = ledger.propose_claim(d.id, claim_text, quote)
        try:
            ledger.run_verification(c.id, [ev.id], "structural")
            actual = "verification_pass"
        except ValueError as e:
            actual = "verification_fail" if "fabricated quotation" in str(e) else f"other_error:{e}"
        except Exception as e:
            actual = f"unexpected:{e}"
        passed = (actual == expected)
        return {"id": fid, "passed": passed, "actual": actual, "expected": expected}
    finally:
        ledger.close()
