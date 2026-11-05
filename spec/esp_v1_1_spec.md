# ESP v1.1 Normative Schema Reference

## Entity schemas (JSON-compatible)

### Document
{"id":"uuid","uri":"string","content_hash":"sha256 hex","source_type":"enum","retrieved_at":"RFC3339","metadata":{},"version":1}

### Claim
{"id":"uuid","text":"string","normalized":"string (NFC)","claim_type":"enum","status":"PROPOSED|VERIFIED|UNVERIFIED|REJECTED|SUPERSEDED|WITHDRAWN","revision_id":"uuid","created_at":"RFC3339"}

### Evidence
{"id":"uuid","claim_id":"uuid","document_id":"uuid","quote":"string","start_offset":"int (code points)","end_offset":"int (code points)","extraction_metadata":{},"verification_status":"INCONCLUSIVE|PASS|FAIL"}

### Verification
{"id":"uuid","claim_id":"uuid","evidence_ids":["uuid"],"method":"string","result":"PASS|FAIL","explanation":"string","verifier_id":"string","timestamp":"RFC3339"}

### Contradiction
{"id":"uuid","claim_ids":["uuid"],"classification":"enum","resolution_status":"UNRESOLVED|RESOLVED","resolution_provenance":"string"}

### Revision
{"id":"uuid","prev_state_id":"uuid|null","new_state_id":"uuid","changed_entities":["uuid"],"reason":"string","timestamp":"RFC3339","actor":"string"}

### Evaluation
{"id":"uuid","objective":"string","required_criteria":["string"],"satisfied":["string"],"unsatisfied":["string"],"missing":["string"],"decision":"SUFFICIENT|INSUFFICIENT|CONFLICTED|UNVERIFIABLE","provenance":"string"}

### Policy
{"max_iterations":"int","required_sources":"int","conflict_escalation":"bool","human_review_required":"bool","completion_criteria":["string"]}

### AuditEvent
{"id":"uuid","entity_id":"uuid","action":"string","timestamp":"RFC3339","actor":"string","payload":{}}

## Sufficiency precedence
CONFLICTED > INSUFFICIENT > UNVERIFIABLE > SUFFICIENT. If any unresolved contradiction -> CONFLICTED. Else if missing evidence -> INSUFFICIENT. Else if empty evidence -> UNVERIFIABLE. Else if all criteria met -> SUFFICIENT.

## Serialization
UTF-8, NFC normalization, canonical JSON (sorted keys, compact separators). Offsets in Unicode code points. Hashes SHA-256 over raw document bytes.

## State machines
Document: ACTIVE -> WITHDRAWN (terminal; reactivation requires admin revision creating new revision)
Claim: PROPOSED -> VERIFIED|UNVERIFIED|REJECTED; VERIFIED -> SUPERSEDED|WITHDRAWN
Evidence: INCONCLUSIVE -> PASS|FAIL
Contradiction: UNRESOLVED -> RESOLVED (requires resolution_provenance non-empty)
Evaluation: terminal decision

## Verification semantics
Trusted verifier required (registered + frozen registry). Evidence must belong to claim and non-withdrawn document. Source content retained; hash recompute; quote validation; offsets validated. Result binding: returned claim_id and evidence_ids must match request. Withdrawn docs cannot verify.

## Transactions
Atomic state+audit in same transaction. Serializable writers. Idempotency via idempotency_key. Crash recovery via audit log replay. Historical reconstruction via revision chain walk.

## Error taxonomy
ESP-ERR-INVALID-INPUT, ESP-ERR-UNAUTHORIZED, ESP-ERR-NOT-FOUND, ESP-ERR-CONFLICT, ESP-ERR-UNSUPPORTED, ESP-ERR-INTERNAL, ESP-ERR-FABRICATED-QUOTE, ESP-ERR-WITHDRAWN-SOURCE, ESP-ERR-EVIDENCE-MISMATCH, ESP-ERR-VERIFICATION-BINDING.