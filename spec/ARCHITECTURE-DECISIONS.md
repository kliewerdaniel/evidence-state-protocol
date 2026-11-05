# Architecture Decisions

- UUIDv4 for IDs
- SHA-256 raw bytes for document hash
- NFC + UTF-8 canonical
- Code-point offsets
- Immutable verification history
- Withdrawal invalidates future verification only
- Reactivation requires admin revision
- Claim supersession via revision
- Sufficiency precedence: CONFLICTED > INSUFFICIENT > UNVERIFIABLE > SUFFICIENT
- Audit replay for recovery
- Idempotency via key