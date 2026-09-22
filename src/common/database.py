from src.common.config import settings
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

DATABASE_URL = settings.database_url

engine = create_async_engine(DATABASE_URL, echo=True, pool_pre_ping=True, connect_args={
        "statement_cache_size": 0,
        "prepared_statement_cache_size": 0
    })


AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
#expire_on_commit: prevent object attribute expire after commit, i.e. user.id will still exist after db.commit() -> so when return user all the attribure still exist

# the base for sqlalchemy to read the class in models as table
class Base(DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session