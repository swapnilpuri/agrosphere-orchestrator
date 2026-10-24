# Deferred execution and explicit approvals

Status: Accepted for AEO-1

Decision: Represent OpenAI Agents SDK and Codex behind protocols without SDK imports, credentials or network calls. Keep approval requirements in typed configuration and default to approval for unknown operations.

Consequences: AEO-1 records state only. Approval actor authentication, result envelopes and workspace isolation must be designed before enabling an executor.
