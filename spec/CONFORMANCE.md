# ESP Conformance Specification

Language-independent JSON fixtures. Each fixture: id, invariant_ids, title, inputs, operations, expected_result, expected_state, expected_error.

15 cases:
1. ESP-CF-001 valid verification (unsupported in current impl)
2. ESP-CF-002 fabricated quote (executed)
3. evidence ownership mismatch
4. withdrawn source
5. verification binding
6. empty evidence set
7. duplicate evidence
8. contradiction preserves both
9. sufficiency verified only
10. conflict -> CONFLICTED
11. missing -> INSUFFICIENT
12. transaction rollback
13. historical preservation
14. restart recovery
15. unsupported operation

Only ESP-CF-002 currently executed by Python reference.