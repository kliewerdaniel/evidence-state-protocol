# AUDIT.md

## Implementation state

| Subsystem | Status |
|---|---|
| EvidenceLedger (SQLite) | Implemented and verified |
| Provenance | Implemented and verified |
| Verification | Implemented; heuristic default, pluggable |
| Deduplication | Exact implemented; semantic candidate via optional index |
| Contradictions | Heuristic detection; preserved |
| Revisions | Implemented; metadata-level reconstruction |
| Sufficiency | Implemented; only VERIFIED claims count |
| Policy | Implemented |
| Semantic index | Optional adapter |
| Adapters | Not implemented (deferred) |

## Hardening applied in Phase 2

- Foreign-key enforcement + PRAGMA foreign_keys=ON
- NOT NULL on evidence claim_id/document_id, verifications claim_id
- Sufficiency evaluator only counts VERIFIED claims
- Source content hashing at registration

## Unresolved risks

- Single-writer SQLite; no external tamper anchoring
- Heuristic contradiction/faithfulness detection
- No hash-chained audit log (deferred)
- Adapters not implemented

## Test count

15 passing tests.