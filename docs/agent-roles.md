# Agent role registry

The canonical typed registry is config/roles.yaml. Each of nine roles declares
responsibilities, named input/output artifact contracts, allowed operations, handoffs,
boundaries and optional specializations. Developer specializations are Java, Python and
Angular. Configuration uses the same plan/inspect/validate operation allowlist for all
roles during AEO-1. These are declared organizational roles, not running agents.

Program Manager owns portfolio priorities and hands roadmaps to Project Manager.
Project Manager owns milestone decomposition and hands requirements, designs and checks
to Business Analyst, Solution Architect and QA Engineer. Business Analyst defines
requirements and acceptance criteria. Solution Architect defines architecture and ADRs
and hands designs to Developer, Security Engineer and DevOps Engineer. Developer
produces proposed patches and evidence in later approved phases. QA Engineer assesses
acceptance evidence. Security Engineer assesses threats and boundaries. DevOps Engineer
designs repeatable operations. Technical Writer maintains user docs and release notes.

Input/output contracts are named artifacts in AEO-1. Typed SDK message envelopes,
artifact provenance and machine-enforced handoff schemas are deferred to AEO-2. The
registry validator rejects duplicate role IDs and unknown handoff targets. Plan validation
rejects unknown roles and operations outside their declared allowlists. No role can grant
human approval, change repository boundaries or authorize work in an unverified repository.
