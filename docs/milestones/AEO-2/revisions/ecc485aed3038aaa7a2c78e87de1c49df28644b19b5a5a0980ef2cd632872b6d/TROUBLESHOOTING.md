# Troubleshooting

- No Codex exe: set AEO_CODEX_EXECUTABLE to a native executable; doctor lists version/features.
- mcp-server unrecognized: expected on 0.164.0-alpha.11.1; use auto/exec. Do not install an
  older CLI silently or claim the cookbook's transport works here.
- Authentication unavailable: run codex login interactively or securely set CODEX_API_KEY.
  Never paste auth.json or tokens into prompts/logs. Login status is readiness, not a live proof.
- Execution disabled/pending: configure live_enabled and exact validator commands, then prepare
  a new request. Design approval, task-operation approval and human execution grant are distinct.
- Windows identity rejected: configure canonical SID allowlists; a noninteractive agent cannot
  approve. PIN-only/non-Windows accounts need an additional verified authentication adapter.
- Native probe failed: inspect the private isolation evidence. Missing MXC, disallowed paths,
  startup failures or managed requirements block execution. No weaker sandbox fallback exists.
- Context changed: revalidate/review source documents and prepare a new grant. Never edit an
  approved revision in place. Original dirty files are retained, not folded into a new worktree.
- Malformed JSON/runtime auth error: normalized state is failed, while bounded redacted output
  is retained. Model statements about tests are not validator evidence.
- Cancel requested but still running: the worker must confirm exit. Reconcile PID creation
  identity after restart; an inaccessible/unknown process blocks recovery rather than replaying.
- Cleanup refused: changed hashes, missing preservation or archive budget overruns require
  manual review. Source/user worktrees are never cleaned by recovery.
- Native sandbox passes but live status unverified: that proves the tested OS boundaries only.
  The optional model smoke must be run and succeed before reporting live integration verified.

~~~powershell
python scripts/verify_codex_runtime.py
python scripts/codex_live_smoke.py
python scripts/codex_live_smoke.py --live
~~~

The first command uses only temporary native canaries; no model/quota. The smoke without --live
prints SKIPPED. The --live transport-only test additionally requires interactive authorized
human authentication, may consume quota, creates only temporary fixture source/worktree data,
checks the expected generated file, compares original repository state and retains evidence.
It does not fabricate application design approval or claim full end-to-end milestone delivery.
