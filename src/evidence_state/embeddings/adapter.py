from __future__ import annotations
from typing import Protocol, List

class EmbeddingAdapter(Protocol):
    def embed(self, texts: List[str]) -> List[List[float]]:
        ...

class OllamaEmbeddingAdapter:
    def __init__(self, model="nomic-embed-text", base_url="http://localhost:11434"):
        self.model = model; self.base_url = base_url
    def embed(self, texts):
        import urllib.request, json
        out = []
        for t in texts:
            req = urllib.request.Request(f"{self.base_url}/api/embeddings", data=json.dumps({"model":self.model,"prompt":t}).encode(), headers={"Content-Type":"application/json"})
            with urllib.request.urlopen(req) as r:
                out.append(json.loads(r.read())["embedding"])
        return out