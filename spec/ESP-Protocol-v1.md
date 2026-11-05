# ESP Protocol Specification v1.0

## Core concepts
Document, Source, Evidence, Claim, Verification, Contradiction, Revision, Evaluation, Policy, AuditEvent.

## State machines
- Document: ACTIVE -> WITHDRAWN (terminal-ish; reactivation requires admin)
- Claim: PROPOSED -> VERIFIED/UNVERIFIED/REJECTED; VERIFIED -> SUPERSEDED/WITHDRAWN
- Evidence: INCONCLUSIVE -> PASS/FAIL
- Verification: recorded result
- Evaluation: SUFFICIENT/INSUFFICIENT/CONFLICTED/UNVERIFIABLE

## Verification semantics
Trusted verifier required, registry frozen. Evidence must belong to claim and document. Source content retained; hash recompute; quote validation; offsets. Withdrawn docs cannot verify. Result binding.

## Invariants
- ESP-INV-001: Untrusted callers cannot issue trusted verification results.
- ESP-INV-002: Verification requires trusted verifier initialization.
- ESP-INV-003: Evidence must belong to the requested claim.
- ESP-INV-004: Evidence must be grounded in registered source content.
- ESP-INV-005: Source hashes must match.
- ESP-INV-006: Withdrawn documents cannot support current verification.
- ESP-INV-007: Verification results must match their requested operation.
- ESP-INV-008: Invalid evidence sets are rejected.
- ESP-INV-009: VERIFIED and SUFFICIENT are distinct states.
- ESP-INV-010: Insufficient evidence cannot produce SUFFICIENT.
- ESP-INV-011: Audit events and state transitions are atomic.
- ESP-INV-012: Failed operations cannot contaminate later operations.
- ESP-INV-013: Historical records cannot silently restore invalidated state.
Only VERIFIED claims count. Conflicts -> CONFLICTED. Empty -> UNVERIFIABLE.

## Persistence and audit
Atomic transactions; audit event in same commit; rollback on failure. Historical records preserved.