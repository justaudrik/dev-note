import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Local dev: leave DATABASE_URL unset — falls back to SQLite automatically.
# Production: set to your Supabase Session Pooler URL (Settings → Database → Connection Pooling → Session Mode)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./devnote.db")

# Railway and Supabase may provide "postgres://" — SQLAlchemy needs "postgresql+psycopg2://"
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+psycopg2://", 1)
elif DATABASE_URL.startswith("postgresql://") and "+psycopg2" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg2://", 1)

is_sqlite = DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # SQLite: disable same-thread check (needed for FastAPI's async handling)
    connect_args = {"check_same_thread": False}
elif "sslmode" in DATABASE_URL:
    # SSL mode already specified in the URL — don't duplicate it
    connect_args = {}
else:
    # PostgreSQL (Supabase, Render, etc.) — SSL is required
    connect_args = {"sslmode": "require"}

engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()