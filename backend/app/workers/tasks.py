import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool
from app.workers.celery_app import celery_app
from app.core.config import settings


@celery_app.task(bind=True, max_retries=2)
def index_repository_task(self, repository_id: str):
    from app.services.ingestion_service import ingest_repository

    async def _run():
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=False,
            connect_args={"ssl": False},
            poolclass=NullPool,
        )
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        try:
            async with session_factory() as db:
                await ingest_repository(db, repository_id)
        finally:
            await engine.dispose()

    try:
        asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
