from __future__ import annotations
import hashlib
from typing import List, Tuple
from ..models.entities import Claim

def normalize(text: str) -> str:
    return " ".join(text.lower().split())

def exact_hash(text: str) -> str:
    return hashlib.sha256(normalize(text).encode()).hexdigest()

class DeduplicationEngine:
    def __init__(self, ledger):
        self.ledger = ledger
    def exact_duplicates(self) -> List[Tuple[str,str]]:
        claims = self.ledger.all_claims()
        seen = {}
        dups = []
        for c in claims:
            h = exact_hash(c.text)
            if h in seen:
                dups.append((seen[h], c.id))
            else:
                seen[h] = c.id
        return dups
    def semantic_candidates(self, threshold: float = 0.8) -> List[Tuple[str,str,float]]:
        # optional index; default returns empty (no embeddings). adapters provide.
        return []