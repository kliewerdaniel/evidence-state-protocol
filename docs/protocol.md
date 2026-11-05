# Protocol Specification

ESP separates candidate information, evidence, verified evidence, conclusions, and authorized actions.

- Candidate information: proposed claims (PROPOSED status).
- Evidence: claim + source quotation + document.
- Verified evidence: claim status VERIFIED after record_verification PASS with valid evidence.
- Conclusions: sufficiency evaluation output.
- Authorized actions: only after policy can_terminate returns True.

Invariants: unverified claims never count toward sufficiency; contradictions preserved; semantic index never mutates ledger.