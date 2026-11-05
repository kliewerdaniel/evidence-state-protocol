from __future__ import annotations
from ..models.entities import Policy

class PolicyEngine:
    def __init__(self, policy: Policy):
        self.policy = policy
    def can_terminate(self, iteration, evaluation_status, contradictions_unresolved, verified_count):
        if iteration >= self.policy.max_iterations:
            return False, "max_iterations_exceeded"
        if self.policy.require_no_unresolved_contradictions and contradictions_unresolved > 0:
            return False, "unresolved_contradictions"
        if self.policy.require_verification and verified_count < self.policy.required_evidence_threshold:
            return False, "insufficient_verified_evidence"
        if evaluation_status != "SUFFICIENT":
            return False, f"evaluation_{evaluation_status}"
        return True, "ok"