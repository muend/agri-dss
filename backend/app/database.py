"""Veritabanı oturum yönetimi (SQLAlchemy 2.0)."""
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import settings

engine = create_engine(settings.database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    """Tüm ORM modellerinin temel sınıfı."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI bağımlılığı: istek başına bir DB oturumu."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
