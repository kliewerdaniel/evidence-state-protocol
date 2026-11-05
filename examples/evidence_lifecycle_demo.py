import os, tempfile, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from evidence_state import *

db = os.path.join(tempfile.gettempdir(), "esp_demo.db")
if os.path.exists(db): os.remove(db)
ledger = EvidenceLedger(db, admin_token="admin-secret")

# documents
d1 = ledger.register_document("doc1", "The API requires OAuth2 authentication. Requests must include an OAuth2 bearer token.")
d2 = ledger.register_document("doc2", "The API requires OAuth2 authentication. Use OAuth2 bearer tokens.")
d3 = ledger.register_document("doc3", "The API uses API keys, not OAuth2.")
print("Registered 3 documents")

# claims
c1,_ = ledger.propose_claim(d1.id, "The API requires OAuth2 authentication.", "The API requires OAuth2 authentication.")
c2,_ = ledger.propose_claim(d2.id, "The API requires OAuth2 authentication.", "The API requires OAuth2 authentication.")
c3,_ = ledger.propose_claim(d3.id, "The API uses API keys instead of OAuth2.", "The API uses API keys, not OAuth2.")
print("Proposed 3 claims")

# verify
from evidence_state.verification.verifier import StructuralVerifier
sv = StructuralVerifier()
def trusted_verifier(claim, evs):
    return sv.verify(claim, evs, None)
ledger.register_verifier("structural", trusted_verifier)
ledger.freeze_verifiers("admin-secret")

for c in [c1,c2,c3]:
    ev = ledger.get_evidence(c.id)
    ledger.run_verification(c.id, [e.id for e in ev], "structural")
print("Verified")

# contradiction detection
det = ContradictionDetector()
cons = det.detect(ledger.all_claims())
for c in cons:
    ledger.record_contradiction(c)
print("Contradictions:", len(cons))

# dedup
dd = DeduplicationEngine(ledger)
print("Exact duplicates:", dd.exact_duplicates())

# evaluation
evl = SufficiencyEvaluator({"required_evidence_threshold":1})
evaluation = evl.evaluate("Determine if API requires OAuth2", ["oauth2 requirement"], ledger)
print("Evaluation:", evaluation.status.value, evaluation.missing_information)

# withdraw source
affected = ledger.withdraw_document(d3.id)
print("Withdrawn d3 affected:", affected)

# sufficiency after
evaluation2 = evl.evaluate("Determine if API requires OAuth2", ["oauth2 requirement"], ledger)
print("Evaluation after withdrawal:", evaluation2.status.value)

# provenance
pe = ProvenanceEngine(ledger)
print("Provenance c1:", pe.trace(c1.id))

# revisions
re = RevisionEngine(ledger)
re.record(None, "state1", [c1.id], "initial")
print("Revisions:", len(re.history()))

# policy
from evidence_state.models.entities import Policy
pe2 = PolicyEngine(Policy())
print("Can terminate:", pe2.can_terminate(1, evaluation.status.value, len(cons), len([x for x in ledger.all_claims() if x.status.value=="verified"])))

ledger.close()
print("Demo complete")