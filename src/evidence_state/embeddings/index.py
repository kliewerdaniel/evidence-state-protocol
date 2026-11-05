from __future__ import annotations
from typing import List, Tuple

class SemanticIndex:
    """Derived index; never authoritative."""
    def __init__(self, adapter=None):
        self.adapter = adapter
        self._store = {}  # id -> vector
    def rebuild(self, ledger):
        claims = ledger.all_claims()
        if self.adapter is None:
            return
        vecs = self.adapter.embed([c.text for c in claims])
        for c, v in zip(claims, vecs):
            self._store[c.id] = v
    def candidates(self, threshold=0.8) -> List[Tuple[str,str,float]]:
        # cosine similarity brute force
        import math
        def cos(a,b):
            dot=sum(x*y for x,y in zip(a,b))
            na=math.sqrt(sum(x*x for x in a)); nb=math.sqrt(sum(x*x for x in b))
            return dot/(na*nb) if na and nb else 0.0
        ids=list(self._store)
        out=[]
        for i in range(len(ids)):
            for j in range(i+1,len(ids)):
                s=cos(self._store[ids[i]], self._store[ids[j]])
                if s>=threshold:
                    out.append((ids[i],ids[j],s))
        return out