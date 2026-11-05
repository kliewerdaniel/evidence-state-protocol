from __future__ import annotations
from ..models.entities import Contradiction, Claim
from typing import List

NEGATION_PAIRS = [("requires","does not require"),("mandatory","optional"),("expires in december","expires in january")]

class ContradictionDetector:
    def detect(self, claims: List[Claim]) -> List[Contradiction]:
        out = []
        for i in range(len(claims)):
            for j in range(i+1, len(claims)):
                a, b = claims[i].text.lower(), claims[j].text.lower()
                # simple heuristic: same subject, differing predicate keywords
                if self._likely_contradict(a, b):
                    out.append(Contradiction(claim_ids=[claims[i].id, claims[j].id], classification="potential"))
        return out
    def _likely_contradict(self, a, b):
        # same leading noun phrase heuristic: share >=2 words but differ on key terms
        wa, wb = set(a.split()), set(b.split())
        shared = wa & wb
        if len(shared) < 2:
            return False
        # negation
        if ("not" in wa) != ("not" in wb):
            return True
        # differing month/year terms
        months = {"january","february","march","april","may","june","july","august","september","october","november","december"}
        ma, mb = wa & months, wb & months
        if ma and mb and ma != mb:
            return True
        # oauth vs api key
        if ("oauth2" in wa) != ("oauth2" in wb) and ("api" in wa and "api" in wb):
            return True
        return False