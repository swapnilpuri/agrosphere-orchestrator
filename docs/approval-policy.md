# Approval policy

config/approvals.yaml defines required_operations, exempt_operations, approvers and
an explicit default_require_approval flag. Required takes precedence over exempt;
unknown operations require approval with the shipped policy. Plan/inspect/validate
are exempt. Code-write, git-write, remote-access and deploy require approval; none
of these write operations has an executor or allowed role operation in AEO-1.

Only allowlisted actors may record an approved/denied decision. The decision must match
the task operation. Decisions and their audit events are append-only through service APIs.
The latest decision governs start; later denial overrides earlier approval. Allowlist
changes take effect at start. Denied transitions leave no partial run or state update.

Actors are trusted local identity strings, not authenticated principals. Approvals are
not single-use, do not expire, and are reusable for retries of the immutable task in
AEO-1. Authentication, expiry, revocation scopes and adapter enforcement require
explicit AEO-2 design review before enabling any execution side effects.

## Authenticated design and delivery decisions

The foundation actor-string task approval remains operation bookkeeping; it cannot satisfy
a design approval. Requirements, exact design bundle and as-built delivery decisions use
HumanVerifier with interactive Windows credential validation and canonical SID allowlisting.
Default design allowlist is empty. No --actor or noninteractive approval bypass exists.
Each decision binds milestone, scope/revision, validation and bundle digest; decisions are
append-only and checked again at implementation gates. See design-workflow.md for setup
and the trusted-administrator boundary.
