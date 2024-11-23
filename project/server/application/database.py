# from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
# from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql+asyncpg://admin:admin@postgres_container:5432/twitter" # for containers
# DATABASE_URL = "postgresql+asyncpg://admin:admin@localhost/twitter" # for local machine
proj_engine = create_async_engine(DATABASE_URL)
AsyncSessionApp = async_sessionmaker(proj_engine, class_=AsyncSession, expire_on_commit=False)