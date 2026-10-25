# Release readiness workflow

1. Approve requirements and design through AEO-1C. Prepare and authenticate AEO-2/AEO-3 execution grants normally.
2. Configure milestone-scoped gates and acceptance mappings. Authenticate quality policy activation.
3. Developers implement; QA, security, architect and writer review through the existing role registry/dependency scheduler. Required review roles must have successful independent READ_ONLY executions. Their prose is advisory.
4. Run quality validate. Every required gate must have complete fresh deterministic evidence; business criteria need explicit verified tests or scoped human procedures.
5. Failed retry-eligible build/test/lint/type/contract/documentation gates can enter quality remediate. It preserves original failure, execution identity, validation ID and bounded retry count in governance and existing orchestration evidence. The existing scheduler prepares repair; write retries always need another exact grant. Original/new execution results retain changed files and new evidence. Security exceptions and policy changes are never automated repairs.
6. Run validation again after repair. A new artifact context invalidates prior results.
7. READY_FOR_APPROVAL permits a scoped DELIVERY_APPROVAL request. Authenticate its decision. Readiness becomes APPROVED_FOR_DELIVERY only while all checks and authorization remain valid.
8. Existing AEO-1C as-built reconciliation and final delivery review still apply. The delivery guard rechecks governance and consumes authorization in the same transaction. No merge/deployment occurs.

The additive quality lifecycle is IMPLEMENTED → VALIDATING → QUALITY_REVIEW → SECURITY_REVIEW → READY_FOR_DELIVERY_REVIEW → AWAITING_DELIVERY_APPROVAL → DELIVERY_APPROVED. Legacy succeeded denotes implementation/dependency completion only. Artifacts changing after approval reset quality readiness to validation; history is preserved.
