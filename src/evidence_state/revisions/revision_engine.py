from __future__ import annotations
from ..models.entities import Revision, new_id, now
from ..ledger.sqlite_ledger import EvidenceLedger

class RevisionEngine:
    def __init__(self, ledger: EvidenceLedger):
        self.ledger = ledger
    def record(self, previous, resulting, changed, reason, actor="system"):
        r = Revision(previous_state_id=previous, resulting_state_id=resulting, changed_entities=changed, reason=reason, actor=actor)
        self.ledger.record_revision(r)
        return r
    def history(self):
        return self.ledger.revisions()