from datetime import datetime
from typing import Annotated, AsyncGenerator
from sqlalchemy.dialects.postgresql import UUID
from uuid import uuid4
from sqlalchemy import func, JSON
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncAttrs, AsyncSession
from sqlalchemy.orm import DeclarativeBase, declared_attr, Mapped, mapped_column

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

# настройка аннотаций
int_pk = Annotated[int, mapped_column(primary_key=True)]
created_at = Annotated[datetime, mapped_column(server_default=func.now())]
updated_at = Annotated[datetime, mapped_column(server_default=func.now(), onupdate=datetime.now)]
str_uniq = Annotated[str, mapped_column(unique=True, nullable=False)]
str_null_true = Annotated[str, mapped_column(nullable=True)]
uuid4 = Annotated[UUID(as_uuid=True), mapped_column(primary_key=True, default=uuid4)]
json = Annotated[JSON, mapped_column(nullable=True)]

class Base(AsyncAttrs, DeclarativeBase):
    __abstract__ = True

    @declared_attr.directive
    def __tablename__(cls) -> str:
        return f"{cls.__name__.lower()}s"

async def get_db() -> AsyncGenerator:
    async with async_session_maker() as session:
        yield session
