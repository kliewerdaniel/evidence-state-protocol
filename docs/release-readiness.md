# Release Readiness

## Protocol v1.0
Specification published in spec/ESP-Protocol-v1.md. Conformance suite minimal (1 executable case).

## Reference implementation
Python/SQLite. Partial coverage.

## Guarantees implemented
- Trusted verifier registry (process-local)
- Source content + hash integrity
- Withdrawal finality
- Verification binding
- Evidence-set validity
- Atomic transactions

## Not implemented
- Heuristic contradiction/faithfulness (pluggable)
- Single-writer SQLite concurrency
- External tamper anchoring
- Persistent registry
- Broad conformance coverage

## Test count
29 unit tests + 1 executable conformance case.