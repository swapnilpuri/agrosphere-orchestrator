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

## AEO-2 execution metadata

The same nine roles now include developer-priority instructions, schema names, allowed
repositories/operations, context/validation requirements, approval requirements and handoff
contracts. Developer specializations additionally include Data/PostGIS and Integration.
All live tasks need exact human grants and sandbox enforcement. Handoff output is advisory;
it cannot start another agent. See the AEO-2 artifact bundle and CLI agents describe.


AEO-3 scheduling, handoffs, resource leases, and operator commands are described in [the orchestration guide](aeo-3/README.md).
