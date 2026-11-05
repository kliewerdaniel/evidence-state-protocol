from __future__ import annotations
from ..ledger.sqlite_ledger import EvidenceLedger

class ProvenanceEngine:
    def __init__(self, ledger: EvidenceLedger):
        self.ledger = ledger
    def trace(self, claim_id):
        # claim -> evidence -> document
        chain = []
        claim = self.ledger.get_claim(claim_id)
        if not claim: return chain
        chain.append(("claim", claim.id, claim.text))
        for ev in self.ledger.get_evidence(claim_id):
            chain.append(("evidence", ev.id, ev.quote))
            doc = self.ledger.get_document(ev.document_id)
            if doc:
                chain.append(("document", doc.id, doc.source_uri))
        return chain