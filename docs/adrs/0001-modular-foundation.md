# Modular Python foundation

Status: Accepted for AEO-1

Decision: Use a src-layout package, Python 3.12+, Pydantic v2, Typer and YAML. Keep domain validation separate from CLI and persistence.

Consequences: A single process and explicit service calls make policies testable before execution exists. Distribution currently assumes a checkout containing config and migrations.
