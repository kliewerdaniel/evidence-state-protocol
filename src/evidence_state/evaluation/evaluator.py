from __future__ import annotations
from ..models.entities import Evaluation, SufficiencyStatus, ClaimStatus
from ..ledger.sqlite_ledger import EvidenceLedger

class SufficiencyEvaluator:
    def __init__(self, policy=None):
        self.policy = policy or {}
    def evaluate(self, objective, required_criteria, ledger: EvidenceLedger) -> Evaluation:
        claims = ledger.all_claims()
        verified = [c for c in claims if c.status == ClaimStatus.VERIFIED]
        contradictions = ledger.contradictions()
        unresolved = [c for c in contradictions if c.resolution_status != "resolved"]
        satisfied = []
        unsatisfied = []
        missing = []
        # simple: a criterion satisfied if any verified claim text contains criterion keyword
        for crit in required_criteria:
            if any(crit.lower() in c.text.lower() for c in verified):
                satisfied.append(crit)
            else:
                unsatisfied.append(crit)
                missing.append(f"evidence for: {crit}")
        if unresolved:
            status = SufficiencyStatus.CONFLICTED
        elif len(satisfied) >= len(required_criteria) and len(required_criteria)>0 and len(verified) >= self.policy.get("required_evidence_threshold",1):
            status = SufficiencyStatus.SUFFICIENT
        elif len(verified) == 0:
            status = SufficiencyStatus.UNVERIFIABLE
        else:
            status = SufficiencyStatus.INSUFFICIENT
        ev = Evaluation(objective=objective, required_criteria=required_criteria, satisfied_criteria=satisfied, unsatisfied_criteria=unsatisfied, missing_information=missing, status=status, provenance="deterministic_policy")
        ledger.record_evaluation(ev)
        return ev