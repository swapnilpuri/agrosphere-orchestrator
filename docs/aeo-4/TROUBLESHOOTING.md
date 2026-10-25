# Troubleshooting and CLI

Start with aeo quality policies. Missing AEO_GOVERNANCE_APPROVERS blocks activation; configure verified SID identities as a trusted administrator. Never work around failures with arbitrary actor IDs.

Commands:

    aeo quality activate --milestone AGRO-M3C
    aeo quality validate --milestone AGRO-M3C
    aeo quality report --milestone AGRO-M3C --markdown
    aeo security report --milestone AGRO-M3C
    aeo quality remediate --milestone AGRO-M3C
    aeo approvals request --milestone AGRO-M3C --reason "Reviewed scope; request delivery review"
    aeo approvals pending
    aeo approvals inspect APPROVAL-ID
    aeo approvals decide APPROVAL-ID --decision approved --reason "Reviewed exact evidence"
    aeo approvals decide APPROVAL-ID --decision revoked --reason "Review withdrawn"
    aeo milestone readiness --milestone AGRO-M3C

JSON is default. Reports recalculate live artifact hashes and persist new assessments. READY_FOR_APPROVAL is not permission to deliver. Missing evidence, unavailable tools, unsupported sandbox, policy edits and absent test mappings remain explicit blockers. Install/configure tools only through a separately authorized administrator workflow.

A read-only runner can block builds that write caches or reports. Use an explicitly authorized isolated execution with narrowly scoped writable outputs; standalone gates never broaden permissions automatically. Multiple independent write worktrees for one repository require reconciliation into a coherent validated artifact. Artifacts over the existing fingerprint size limit block instead of truncating scope.

PlantUML source checks do not imply render success. Run scripts/verify_aeo4_docs.py to record actual local rendering results. No remote includes, network rendering or automatic tool installation is used.

Legacy milestones require explicit quality policy activation to adopt the AEO-4 delivery guard. Review-role summaries do not constitute deterministic test evidence. Production identity federation, semantic compliance beyond configured tools/rules and remote tamper-resistant storage remain future integration work.
