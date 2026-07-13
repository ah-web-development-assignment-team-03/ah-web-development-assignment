import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from alembic import context

from app.db.base import Base

load_dotenv()

target_metadata = Base.metadata
engine = create_engine(os.getenv("DATABASE_URL"))

with engine.connect() as connection:
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()