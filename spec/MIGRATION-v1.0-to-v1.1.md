# Migration v1.0 to v1.1

v1.0 invariants preserved. Breaking changes: offset semantics (code points vs unspecified), hash input (raw bytes). Data migration: recompute hashes over raw bytes; convert offsets to code points. Compatibility: v1.0 records interpretable as v1.1 with defaults.