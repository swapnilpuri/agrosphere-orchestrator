# Acceptance criteria and test matrix

No new AEO-5 test named below has been implemented or executed. These are proposed verification obligations, not test results. The existing baseline inventory is 163 tests.

| Requirement | Required new verification |
| --- | --- |
| AEO5-AUTH | test_auth_failure_blocks_write, test_repository_lookup_validates_identity, test_insufficient_permissions_redacted |
| AEO5-BRANCH | test_branch_name_and_base_rejected, test_isolated_create_preserves_dirty_source, test_matching_branch_reused, test_branch_conflict_blocks |
| AEO5-PR | test_pr_body_uses_stored_evidence, test_pr_created_once, test_existing_pr_reconciled, test_multiple_matches_block, test_closed_merged_no_replacement |
| AEO5-COORD | test_manifest_links_existing_tasks, test_cycles_rejected, test_repository_lease_conflicts, test_dependency_pr_not_available, test_partial_multirepo_recovery |
| AEO5-CI | test_required_success_and_failure, test_optional_success_cannot_replace_missing, test_stale_sha_blocked, test_unknown_policy_blocked, test_ruleset_requirements |
| AEO5-REVIEW | test_missing_human_review, test_bot_author_self_review_not_counted, test_dismissal_invalidates, test_codeowners_unknown_blocks |
| AEO5-APPROVAL | test_missing_aeo4_blocks_publish, test_publish_scope_sha_remote_bound, test_expired_revoked_rejected, test_stale_quality_blocks |
| AEO5-DURABLE | test_0007_preserves_0006_records, test_sqlite_restart_preserves_intent, test_history_append_only, test_transaction_failure_retains_reconcilable_intent |
| AEO5-RECOVERY | test_crash_after_push, test_crash_after_pr, test_timeout_after_remote_success_no_duplicate, test_auth_rate_limit_network_fail_closed |
| AEO5-EVIDENCE | test_report_actual_sha_pr_checks_reviews_hashes, test_changed_observation_preserves_history, test_unknown_not_success, test_secret_redaction |
| AEO5-CLI | test_nine_commands_help_and_exit_codes, test_status_checks_reviews_reconcile_recover_report_never_write, test_plan_invalid_manifest |
| AEO5-BOUNDARY | test_unauthorized_write_rejected_before_provider, test_no_merge_deploy_port, test_unrelated_repo_unchanged, test_baseline_163_pass |

Acceptance requires actual implementation, all baseline and new tests passing, migration preservation, duplicate/recovery failure injection, exact-head policy/review enforcement and actual stored delivery evidence. Documentation, interface stubs, fixture assertions about absent code and a review package alone cannot satisfy acceptance.

The AEO-5R acceptance report must continue to say NOT ACCEPTED while approval or implementation is missing. Record live authentication checks separately from mocked delivery behavior. Never infer least-privilege token scope, production readiness, approval, GitHub write success or completion from an accessible repository.
