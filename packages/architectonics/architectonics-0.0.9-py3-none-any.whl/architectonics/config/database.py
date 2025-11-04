from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from architectonics.config.base_database_settings import base_database_settings

engine = create_async_engine(
    base_database_settings.DATABASE_CONNECTION_STRING,
    future=True,
    echo=base_database_settings.DEBUG,
)

session = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
