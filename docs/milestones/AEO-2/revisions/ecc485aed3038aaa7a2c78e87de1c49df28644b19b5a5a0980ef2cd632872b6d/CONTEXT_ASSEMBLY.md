# Context assembly design — as built

Context is selected from the exact approved MilestoneSpec/design revision, requirement and
artifact hashes, relevant architecture/contracts/PlantUML, target README/AGENTS instructions,
repository inventory, dependency states and prior dependency results. Approved context references
supply selected ADRs and service contracts. Project goals are the approved milestone title and
requirements; no goals are inferred from roadmap completion claims.

Only the target and relevant architecture/contracts artifacts are selected. SVG bytes and
whole repository dumps are excluded. Selected source documents have a 20 KB limit and the
whole context has a configurable byte budget. Oversized inputs fail for explicit narrowing.
Paths, source HEADs, hashes and revisions remain traceable. Sensitive environment values and
common credential patterns are redacted. Repository text is task data and cannot enlarge
permissions. Registry instructions use the documented developer_instructions configuration.
[Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference)

An execution digest binds the input snapshots, source HEAD, task, role/schema/specialization,
policy, exact validator argv, binary hash/version and runtime options. Context is rebuilt before
preparation, before starting a task and after runtime completion. Changed approved artifacts,
requirements, roles or policy invalidate acceptance and require a newly reviewed execution.
Artifacts are archived as versions; generated proposals do not rewrite approved design files.
