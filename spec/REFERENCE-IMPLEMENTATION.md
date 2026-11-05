# Reference Implementation Mapping

| Requirement | Location | Test | Status |
|---|---|---|---|
| Trusted verifier | sqlite_ledger.register_verifier/run_verification | test_frozen_registry_blocks_untrusted | partial (process-local) |
| Source integrity | verify_source_integrity, run_verification | test_bad_offsets_rejected | implemented |
| Withdrawal | withdraw_document | test_withdrawal_invalidates | implemented |
| Verification binding | run_verification | (none dedicated) | implemented |
| Transaction atomicity | context managers | test_failure_injection_audit_rollback | partial |