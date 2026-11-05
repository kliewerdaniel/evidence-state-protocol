# ESP Protocol Specification v1.1 (Normative)

## 1. Scope and terminology
ESP defines how evidence is accumulated, verified, revised, and evaluated. Models propose; protocol authorizes.

## 2. Entity schemas
(See esp_v1_1_spec.md for full schemas.) All entities use UUIDv4 IDs. Timestamps RFC3339. Hashes SHA-256 over raw bytes.

## 3. Serialization
UTF-8, NFC normalization, canonical JSON (sorted keys, compact). Offsets in Unicode code points.

## 4. State machines
Document: ACTIVE -> WITHDRAWN (terminal; reactivation requires admin revision)
Claim: PROPOSED -> VERIFIED|UNVERIFIED|REJECTED; VERIFIED -> SUPERSEDED|WITHDRAWN
Evidence: INCONCLUSIVE -> PASS|FAIL
Contradiction: UNRESOLVED -> RESOLVED (requires provenance)
Evaluation: terminal

## 5. Verification semantics
Trusted verifier required. Evidence must belong to claim and non-withdrawn document. Source content retained; hash recompute; quote validation; offsets. Result binding.

## 6. Sufficiency
SUFFICIENT: all criteria met, no unresolved contradictions, no UNVERIFIABLE. CONFLICTED if contradictions. INSUFFICIENT if missing. UNVERIFIABLE if empty.

## 7. Errors
ESP-ERR-INVALID-INPUT, ESP-ERR-UNAUTHORIZED, ESP-ERR-NOT-FOUND, ESP-ERR-CONFLICT, ESP-ERR-UNSUPPORTED, ESP-ERR-INTERNAL, ESP-ERR-FABRICATED-QUOTE, ESP-ERR-WITHDRAWN-SOURCE, ESP-ERR-EVIDENCE-MISMATCH, ESP-ERR-VERIFICATION-BINDING.

## 8. Transactions
Atomic state+audit. Serializable writers. Idempotency via key. Crash recovery via audit replay.

## 9. Conformance
15 cases (see CONFORMANCE.md).

## 10. Compatibility
v1.0 invariants preserved. Breaking: offset semantics (code points), hash input (raw bytes).