import os

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+psycopg://musicaccess:musicaccess@localhost:5432/musicaccess")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)
if engine.dialect.name == "sqlite":
    @event.listens_for(engine, "connect")
    def enable_foreign_keys(connection, _):
        connection.execute("PRAGMA foreign_keys=ON")

SessionLocal = sessionmaker(engine, expire_on_commit=False)


def get_db():
    with SessionLocal() as db:
        yield db
