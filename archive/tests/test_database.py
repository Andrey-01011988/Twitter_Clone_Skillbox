import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


DATABASE_URL = "postgresql+asyncpg://test:test@test_postgres_container:5432/test_twitter"
POOL_DATABASE_URL = "postgresql://test:test@test_postgres_container:5432/test_twitter"
test_engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionTest = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

# Создание пула соединений
async def create_pool():
    return await asyncpg.create_pool(dsn=POOL_DATABASE_URL)

# Функция для закрытия пула
async def close_pool(pool):
    await pool.close()
