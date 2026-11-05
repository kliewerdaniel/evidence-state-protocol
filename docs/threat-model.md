# Threat Model

Threats: fabricated quotations (mitigated by quote validation against document text when provided), fabricated verification (mitigated by evidence ownership + non-empty guards), unverified sufficiency (mitigated: only VERIFIED claims count), semantic index tampering (index is derived, never authoritative), source withdrawal (invalidates affected claims).

## Trust boundary table

| Asset | Actor | Boundary | Enforcement | Limitation |
|---|---|---|---|---|
| Claim verification | Untrusted agent/API | Ledger API | Issued-verification gate | In-process code can inspect token |
| Source content | Untrusted caller | Stored content/hash | Hash recompute + quote check | Content must be retained |
| Verifier registry | Untrusted caller | Admin token + freeze | PermissionError | In-memory only |