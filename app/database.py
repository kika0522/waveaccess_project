from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs, AsyncSession
from sqlalchemy.orm import DeclarativeBase, declared_attr

from app.config import settings

DATABASE_URL = settings.POSTGRES_URL

engine = create_async_engine(
    url=settings.POSTGRES_URL,
    future=True,
    echo=True
)

async_session_maker = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)

class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

async def get_db() -> AsyncGenerator:
    async with async_session_maker() as session:
        yield session
