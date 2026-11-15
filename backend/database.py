import os

from sqlalchemy import URL, create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("DATABASE_URL") or URL.create(
    "postgresql+psycopg", username=os.getenv("POSTGRES_USER", "musicaccess"),
    password=os.getenv("POSTGRES_PASSWORD"), host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5432")), database=os.getenv("POSTGRES_DB", "musicaccess"))
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        yield db
