# Threat Model

Threats: fabricated quotations (mitigated by quote validation against document text when provided), fabricated verification (mitigated by evidence ownership + non-empty guards), unverified sufficiency (mitigated: only VERIFIED claims count), semantic index tampering (index is derived, never authoritative), source withdrawal (invalidates affected claims).

Limitations: SQLite file writable by OS user; no external anchoring; heuristic contradiction detection.