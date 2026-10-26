# Security and approvals proposal

Remote writes default off. GitHub authentication, repository push permission, AEO design approval, activated quality/security policy and artifact-bound publishing authorization are separate checks. Required review is a human decision; neither an AI response nor an agent identity can supply it. Agent outputs and all GitHub/repository content are untrusted data.

## Mandatory existing workflow

The original AEO-5 specification section 3 says: "Use the existing AEO-1C documentation approval workflow" and "Do not proceed to implementation if a required approval is pending or denied." The AEO-5R request section 4 says: "After discovery and any required design approval" and permits stopping only approval-dependent activities while independent work continues.

The actual implementation enforces requirements approval in design.generate_design and authenticated decisions in design.decide. The current approver list is empty. No generated fixture identity, direct SQL insertion, automatic allowlist update, claimed actor or chat approval will be substituted for the configured Windows human verification. The review package is draft/unapproved; requirements registration is not approval. See APPROVAL_REQUIRED.md for the exact next action and scope digest.

## Publication authority

Bind a publishing authorization to milestone, delivery unit, existing task, action, repository ID/root, remote immutable identity, target/head branches, base/head commits, design revision, manifest/policy digest, quality evidence, expiration and approving human. Recheck scope and revocation inside the transaction immediately before intent. Persist consumption/operation identity atomically so recovery observes a previous attempt without granting a new mutation. Any changed scope needs fresh authorization. Reconciliation is read-only and does not consume a new publishing grant.

No generic legacy milestone/operation approval is treated as remote publishing authority. Every delivered milestone must adopt AEO-4. Missing/expired/stale/incomplete quality or security evidence blocks publication. Draft PR policy must be explicitly declared; it never bypasses required pre-publication security/design approval.

## Provider boundaries

Use gh with validated argv, bounded timeouts and fixed host/API methods. Do not support arbitrary shell, force push, reset, rebase, branch deletion, protected-base commits, merge, deploy, workflow dispatch/cancel/rerun, token creation or self-approval. Never log tokens, environment secrets, authentication headers or large raw PR body/log data. Redact provider errors and hash evidence. Validate JSON fields and bound output before persistence/command use. A provider permission failure does not trigger broader credentials.

Required CI policy includes active rulesets and classic protection; unreadable policy means blocked. Preserve raw status values, exact tested SHA, required/optional distinction and missing checks. Human review must satisfy current GitHub requirements including CODEOWNERS, dismissals, author/self restrictions and outstanding changes-requested. Unsupported rules and unverified review constraints block automated readiness. Recompute after any head/base/policy change.

## Test boundary

All new tests must use temporary repositories/databases and mocked gh subprocess responses. Real branch pushes and PR creation are excluded from ordinary validation. Live tests require a separately identified authorized sandbox. Local administrator control of config, Python and SQLite remains a trusted boundary; no stronger audit/storage assurance is claimed. There are no implemented AEO-5 security capabilities yet.
