from __future__ import annotations
import tempfile, os
from ..ledger.sqlite_ledger import EvidenceLedger
from ..verification.verifier import StructuralVerifier

def run_fixture(fixture, tmp_path=None):
    tmp = tmp_path or tempfile.mkdtemp()
    db = os.path.join(tmp, "cf.db")
    ledger = EvidenceLedger(db, admin_token="t")
    sv = StructuralVerifier()
    ledger.register_verifier("structural", lambda c, evs: sv.verify(c, evs, "content"))
    ledger.freeze_verifiers("t")
    # minimal supported: fabricated_quote
    fid = fixture.get("id")
    if fid == "ESP-CF-002":
        d = ledger.register_document("u", "real text")
        c, ev = ledger.propose_claim(d.id, "claim", "fake quote")
        try:
            ledger.run_verification(c.id, [ev.id], "structural")
            ledger.close()
            return {"id": fid, "passed": False, "reason": "expected rejection but passed"}
        except ValueError:
            ledger.close()
            return {"id": fid, "passed": True}
    ledger.close()
    return {"id": fid, "passed": False, "reason": "unsupported fixture"}
