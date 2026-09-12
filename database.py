"""Database setup for the V3 email classifier."""

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

load_dotenv()

database_url = os.getenv("DATABASE_URL")
if not database_url:
    raise RuntimeError("DATABASE_URL is required. Add it to your .env file.")

engine = create_engine(database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def init_database() -> None:
    # Importing here registers every model before SQLAlchemy creates tables.
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
