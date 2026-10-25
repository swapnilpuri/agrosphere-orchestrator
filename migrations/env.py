from alembic import context

from agrosphere_orchestrator import (
    orchestration_store,  # noqa: F401
    quality_store,  # noqa: F401
)
from agrosphere_orchestrator.config.settings import Settings
from agrosphere_orchestrator.persistence import Base, make_engine

if context.is_offline_mode():
    context.configure(
        url=Settings().database_url,
        target_metadata=Base.metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = make_engine(Settings().database_url)
    with engine.connect() as connection:
        context.configure(
            connection=connection, target_metadata=Base.metadata, render_as_batch=True
        )
        with context.begin_transaction():
            context.run_migrations()
    engine.dispose()
