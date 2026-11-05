# Evidence State Protocol (ESP)

> A model-independent foundation for governed knowledge acquisition and verification.

A language model may propose claims, retrieve information, interpret evidence, and recommend actions. It must **not** independently determine the authoritative state of evidence, certify its own conclusions, or authorize operations. ESP provides the infrastructure that enforces this separation.

ESP externalizes evidence into an authoritative, inspectable, append-only ledger so that reliability does **not** depend on trusting the model.

## Why this exists

Agent memory and retrieval stacks today conflate four distinct operations:

1. **Generating information** (the model)
2. **Establishing evidence** (provenance + quotation)
3. **Verifying claims** (faithfulness + contradiction)
4. **Evaluating sufficiency** (independent completion decision)

When these collapse into one component, unsupported claims pass as verified facts, contradictory evidence gets silently merged, and the same model that produced a conclusion also certifies it. ESP splits them into independently testable, governable subsystems.

## Core principle

**Intelligence generates candidate knowledge. The protocol determines what evidence is accepted, how it is maintained, and when it is sufficient to support a conclusion.**

## Architecture

Two storage layers, strictly separated:

### A. Authoritative Evidence Ledger (source of truth)
SQLite-backed, independently inspectable without the generating model. Maintains documents, atomic claims, exact source quotations, spans, claim↔source links, verification results, contradictions, duplicates, dependencies, immutable revision history, evaluations, sufficiency status, and audit events. Mutations are transactional; history is never silently overwritten.

### B. Derived Semantic Index (optimization, not authority)
Embedding-based similarity search, candidate duplicate discovery, related-claim discovery, clustering. Rebuildable from ledger records. Changing embedding models or rebuilding the index never changes authoritative evidence. Vector similarity **never** automatically merges or discards claims.

## Subsystems

- **Evidence Ingestion** — preserves raw source → candidate claim → validated claim → accepted evidence distinction.
- **Provenance Engine** — source identification, content hashing, exact quotation, span tracking, claim-to-evidence traversal. A claim without adequate provenance is never represented as verified.
- **Claim Verifier** — layered pipeline: structural validation → quotation validation → faithfulness → contradiction discovery → decision recording. Pluggable verifier interface (local models or external systems). Verifiers cannot rewrite original evidence.
- **Deduplication Engine** — three distinct operations: exact hash dedup, semantic candidate discovery, human/independent adjudication. Similarity ≠ equivalence. Contradictory but similar claims are preserved and linked.
- **Revision Engine** — immutable revision history, claim supersession, evidence withdrawal, verification invalidation, contradiction resolution, state reconstruction, historical inspection.
- **Sufficiency Evaluator** — independent decision: `SUFFICIENT` / `INSUFFICIENT` / `CONFLICTED` / `UNVERIFIABLE`, with missing-information reporting. The extraction agent cannot override it.
- **Policy & Termination Engine** — max iterations, evidence thresholds, mandatory sources, conflict escalation, human review, explicit completion criteria. A model-generated `FINAL` response never independently terminates a governed process.

## Protocol entities

Typed Pydantic models: `Document`, `Claim`, `Evidence`, `Verification`, `Contradiction`, `Revision`, `Evaluation`, `Policy`. Relationships, constraints, and lifecycle states are explicit.

## Public API (illustrative)

```python
from evidence_state import EvidenceLedger, StructuralVerifier

ledger = EvidenceLedger("./evidence.db", admin_token="admin-secret")
sv = StructuralVerifier()
ledger.register_verifier("structural", lambda c, evs: sv.verify(c, evs, None))
ledger.freeze_verifiers("admin-secret")

document = ledger.register_document("https://example.com/api", content)
candidate, evidence = ledger.propose_claim(
    document_id=document.id,
    claim="The API requires OAuth2 authentication.",
    source_quote="Requests must include an OAuth2 bearer token.",
)

verification = ledger.run_verification(candidate.id, [evidence.id], "structural")

evaluation = SufficiencyEvaluator({}).evaluate(
    objective="Determine auth requirement",
    required_criteria=["oauth2 requirement"],
    ledger=ledger,
)
print(evaluation.status, evaluation.missing_information)
ledger.close()
```

## Installation

```bash
pip install -e .
# optional
pip install chromadb   # semantic index adapter
# Ollama embeddings: ensure Ollama running locally
```

Core requires only `pydantic`. Works fully offline without Ollama, ChromaDB, LangGraph, AutoGen, or any external API.

## Usage

```bash
PYTHONPATH=src python examples/evidence_lifecycle_demo.py
```

## Tests

```bash
PYTHONPATH=src python -m pytest tests/ -q
```

18 tests covering ingestion, quotation preservation, unsupported-claim rejection, exact dedup, semantic duplicate surfacing, contradiction preservation, multi-source support, withdrawal invalidation, revision persistence, restart reconstruction, index rebuild non-authority, insufficiency, conflict, max-iteration policy, schema validation, provenance traversal, and fabricated-quote adversarial cases.

## Repository layout

```
evidence-state-protocol/
├── README.md
├── pyproject.toml
├── src/evidence_state/
│   ├── models/          # typed entities
│   ├── ledger/          # SQLite authoritative ledger
│   ├── provenance/      # source traceability
│   ├── verification/    # layered verifier
│   ├── deduplication/   # exact + semantic candidate
│   ├── contradictions/  # contradiction detection
│   ├── revisions/       # immutable history
│   ├── evaluation/      # sufficiency evaluator
│   ├── policies/        # termination policy
│   ├── embeddings/      # derived semantic index + Ollama adapter
│   └── adapters/        # framework adapters (optional)
├── examples/            # end-to-end lifecycle demo
├── tests/               # unit, integration, adversarial
└── docs/                # specification, architecture, threat model
```

## Security & limitations (honest)

- Append-only records and hashing improve auditability; they do **not** constitute tamper-proof security. A party with filesystem write access can alter the SQLite file. For tamper-evidence, add external anchoring (not included in v0.1).
- Contradiction detection is heuristic in v0.1; pluggable verifiers can replace it.
- Faithfulness verification defaults to a heuristic; production use should supply a pluggable verifier (local model or external service).
- Semantic similarity is candidate discovery only; it never auto-merges.
- Concurrency: single-writer SQLite; multi-process writers should serialize externally.

## What ESP does not solve

- It does not make a model more reliable. It makes reliability *inspectable and governable*.
- It does not replace human judgment on ambiguous contradictions.
- It does not provide tamper-proof storage without external anchoring.

## License

MIT.