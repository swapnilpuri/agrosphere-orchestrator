# SQLite, SQLAlchemy and Alembic

Status: Accepted for AEO-1

Decision: Use SQLAlchemy transactional services, SQLite foreign keys and versioned Alembic migration 0001. Protect audit rows using UPDATE/DELETE triggers.

Consequences: Simple local durability without infrastructure. No distributed concurrency or tamper-proof audit guarantee; database owners remain trusted. Destructive downgrade is refused to preserve history.
