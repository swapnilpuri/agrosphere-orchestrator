# AEO-5R actual test results

Final full validator: **275 passed in 537.42 seconds**, 0 failed, 0 errors, 0 skipped. All 18 required validator commands returned 0. All 163 original baseline IDs are retained, with 112 additional passing tests. The database used by the validator was a disposable SQLite backup.

[Exact command results](evidence/aeo5r-accepted-validation/commands.json), [full JUnit](evidence/aeo5r-accepted-validation/pytest.xml), [wrapper](evidence/aeo5r-accepted-validation/runner.json), [verified acceptance summary](evidence/acceptance-summary.json).

Targeted evidence: 101 delivery/provider/CLI/migration tests passed; 21 explicit-recovery/end-to-end/CLI checks passed; 27 provider transport checks passed; four separate-commit/AEO-2 compatibility checks passed. These overlap the final full inventory and are not added to its total.

Earlier failures and corrections, including the timed-out full attempt and long custom fixture-path failure, are preserved in [attempt history](evidence/validation-attempt-history.json). No failed attempt is counted as a successful run.

Live GitHub writes were not tested or performed. Mocked delivery evidence is explicitly marked simulated. [Actual mock report](evidence/mocked-end-to-end-delivery.json). [Acceptance report and limitations](AEO-5R_ACCEPTANCE_REPORT.md).
