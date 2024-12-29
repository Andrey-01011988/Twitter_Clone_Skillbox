import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Строка подключения к тестовой базе данных
DATABASE_URL = "postgresql+asyncpg://test:test@localhost:5433/test_twitter"

# Создание асинхронного движка SQLAlchemy
test_engine = create_async_engine(DATABASE_URL, echo=True)

# Создание асинхронного сессии
AsyncSessionTest = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

test_session = AsyncSessionTest()
