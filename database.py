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
    from sqlalchemy import inspect, text

    Base.metadata.create_all(bind=engine)

    # Safe lightweight schema migration for existing PostgreSQL databases
    if engine.dialect.name == "postgresql":
        with engine.begin() as conn:
            inspector = inspect(conn)

            if inspector.has_table("users"):
                user_columns = {col["name"]: col for col in inspector.get_columns("users")}
                if "google_id" in user_columns and not user_columns["google_id"].get("nullable", True):
                    try:
                        conn.execute(text("ALTER TABLE users ALTER COLUMN google_id DROP NOT NULL;"))
                    except Exception:
                        pass
                if "password_hash" not in user_columns:
                    try:
                        conn.execute(text("ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);"))
                    except Exception:
                        pass
                if "gmail_refresh_token" not in user_columns:
                    try:
                        conn.execute(text("ALTER TABLE users ADD COLUMN gmail_refresh_token TEXT;"))
                    except Exception:
                        pass
                if "gmail_history_id" not in user_columns:
                    try:
                        conn.execute(text("ALTER TABLE users ADD COLUMN gmail_history_id VARCHAR(64);"))
                    except Exception:
                        pass
                if "gmail_watch_expiration" not in user_columns:
                    try:
                        conn.execute(text("ALTER TABLE users ADD COLUMN gmail_watch_expiration TIMESTAMPTZ;"))
                    except Exception:
                        pass

            if inspector.has_table("emails"):
                email_columns = {col["name"] for col in inspector.get_columns("emails")}
                if "user_id" not in email_columns:
                    try:
                        conn.execute(text("ALTER TABLE emails ADD COLUMN user_id INTEGER REFERENCES users(id);"))
                    except Exception:
                        pass

