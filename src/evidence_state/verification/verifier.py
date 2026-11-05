from __future__ import annotations
import hashlib, re
from typing import Callable, Optional
from ..models.entities import *

class StructuralVerifier:
    def verify(self, claim: Claim, evidence: list[Evidence], document_text: Optional[str]=None) -> Verification:
        # structural: non-empty, quote non-empty
        if not claim.text.strip() or not evidence or not all(e.quote.strip() for e in evidence):
            return Verification(claim_id=claim.id, evidence_ids=[e.id for e in evidence], method="structural", result=VerificationResult.FAIL, explanation="missing claim text or evidence quote", verifier_identity="structural")
        # quote validation against document text if provided
        if document_text is not None:
            for e in evidence:
                if e.quote not in document_text:
                    return Verification(claim_id=claim.id, evidence_ids=[x.id for x in evidence], method="quote_validation", result=VerificationResult.FAIL, explanation=f"quote not found in source: {e.quote[:60]}", verifier_identity="quote_validator")
        return Verification(claim_id=claim.id, evidence_ids=[e.id for e in evidence], method="structural+quote", result=VerificationResult.PASS, explanation="structural and quote checks passed", verifier_identity="structural")

class FaithfulnessVerifier:
    def __init__(self, fn: Optional[Callable[[str,str], bool]] = None):
        self.fn = fn
    def verify(self, claim: Claim, evidence: list[Evidence]) -> Verification:
        if self.fn is None:
            # default heuristic: claim keyword overlap
            ok = any(claim.text.lower().split()[0:1] and claim.text.lower() in e.quote.lower() or e.quote.lower() in claim.text.lower() for e in evidence) if evidence else False
            # be lenient: pass if any evidence quote shares >=3 words
            if not ok:
                for e in evidence:
                    words = set(claim.text.lower().split()) & set(e.quote.lower().split())
                    if len(words) >= 3:
                        ok = True
            res = VerificationResult.PASS if ok else VerificationResult.INCONCLUSIVE
            return Verification(claim_id=claim.id, evidence_ids=[e.id for e in evidence], method="faithfulness_heuristic", result=res, explanation="heuristic overlap", verifier_identity="faithfulness")
        # pluggable
        passed = False
        for e in evidence:
            if self.fn(claim.text, e.quote):
                passed = True
        return Verification(claim_id=claim.id, evidence_ids=[e.id for e in evidence], method="faithfulness_pluggable", result=VerificationResult.PASS if passed else VerificationResult.FAIL, explanation="pluggable verifier", verifier_identity="faithfulness")