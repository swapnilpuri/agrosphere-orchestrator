# Implementation plan awaiting approval

## Execution order

1. Complete recovery inventory, reviewable local design, six rendered diagrams and requirement-scope registration. Obtain authenticated requirements approval. Address the internal-documentation ownership compatibility prerequisite under that approved scope, then generate, validate and obtain authenticated design approval before AEO-5 delivery implementation.
2. Add strict models and a provider port/gh adapter. Verify installed flags and official API contracts. Mock authentication, permission, JSON, pagination, rate-limit, network and redaction cases.
3. Add additive migration 0007, durable operation identity/intent and append-only observation/evidence history. Test upgrade preservation from 0006 and prior records, transaction failure and restart.
4. Add isolated branch management and publication under existing leases and exact AEO-4 grants. Test safe naming, dirty preservation, baseline conflicts, reuse, hook isolation and disabled writes.
5. Add PR body generation, existing/open/closed/merged reconciliation and duplicate detection. Test create response loss, external competing PR and no blind retry.
6. Add manifest DAG/dependency readiness; CI/current-head policy and human-review verification. Preserve unsupported/unavailable policy as blockers. Test invalidation and independent partial completion.
7. Add recovery, reports and all nine Typer commands. Read-only commands must have spy assertions prohibiting write-port calls. Add restart/transaction/timeout failure injection, no-merge/deploy checks, report hash/provenance and full mocked end-to-end delivery.
8. Run all 163 baseline tests plus new tests; Ruff, formatting, dependency consistency, disposable database upgrade/check and established validation. Update recovery/operational guides, exact results, implementation inventory and acceptance report. Keep live capability claims separate. Stop before AEO-6.

## Planned implementation files

github_models.py, github_provider.py, delivery_models.py, delivery_store.py and delivery.py in src/agrosphere_orchestrator; additive settings/CLI integration, migration 0007_delivery.py and tests/test_github.py, test_delivery.py and test_delivery_cli.py. File decomposition may change after review; these files do not currently exist and are not reported as completed work.

## Approval boundary

Independent discovery, source assessment, draft documentation, local diagram rendering, requirements registration and existing regression checks are authorized and performed before waiting. Production delivery code, schema changes, executable delivery task import and remote publication remain gated. No live remote write is authorized by this implementation request. No user work may be cleaned or overwritten.
