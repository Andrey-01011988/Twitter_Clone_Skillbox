from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession


DATABASE_URL = "postgresql+asyncpg://test:test@test_postgres_container:5432/test_twitter"
test_engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionTest = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)

test_session = AsyncSessionTest()
