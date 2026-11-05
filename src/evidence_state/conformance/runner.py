from __future__ import annotations
import tempfile, os
from ..ledger.sqlite_ledger import EvidenceLedger
from ..verification.verifier import StructuralVerifier

def run_fixture(fixture, tmp_path=None):
    tmp = tmp_path or tempfile.mkdtemp()
    db = os.path.join(tmp, "cf.db")
    fid = fixture.get("id")
    if fid != "ESP-CF-002":
        return {"id": fid, "passed": False, "reason": "unsupported fixture"}
    ledger = EvidenceLedger(db, admin_token="t")
    try:
        sv = StructuralVerifier()
        ledger.register_verifier("structural", lambda c, evs: sv.verify(c, evs, "real text"))
        ledger.freeze_verifiers("t")
        d = ledger.register_document("u", "real text")
        c, ev = ledger.propose_claim(d.id, "claim", "fake quote")
        try:
            ledger.run_verification(c.id, [ev.id], "structural")
            return {"id": fid, "passed": False, "reason": "expected rejection but passed", "actual": "pass"}
        except ValueError as e:
            if "fabricated quotation" in str(e):
                return {"id": fid, "passed": True, "reason": "rejected fabricated quotation"}
            return {"id": fid, "passed": False, "reason": f"wrong rejection: {e}"}
    finally:
        ledger.close()
