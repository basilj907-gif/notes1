from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()


def init_db(base) -> None:
	base.metadata.create_all(bind=engine)

	inspector = inspect(engine)
	if "notes" not in inspector.get_table_names():
		return

	note_columns = {column["name"] for column in inspector.get_columns("notes")}
	if "user_id" in note_columns:
		return

	with engine.begin() as connection:
		connection.execute(text("ALTER TABLE notes ADD COLUMN user_id INTEGER"))
