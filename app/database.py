from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import DATA_DIR, DATABASE_URL

DATA_DIR.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _column_names(table: str) -> set[str]:
    inspector = inspect(engine)
    if table not in inspector.get_table_names():
        return set()
    return {column["name"] for column in inspector.get_columns(table)}


def _add_column_if_missing(table: str, column: str, ddl: str) -> None:
    if column in _column_names(table):
        return
    with engine.begin() as conn:
        conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {ddl}"))


def migrate_schema() -> None:
    """Add columns introduced after initial deploy (SQLite has no ALTER from ORM)."""
    _add_column_if_missing("nodes", "branch_question_md", "branch_question_md TEXT DEFAULT ''")
    _add_column_if_missing("branches", "student_label", "student_label VARCHAR(256) DEFAULT ''")
    _add_column_if_missing("sessions", "display_phase", "display_phase VARCHAR(32) DEFAULT 'content'")
    _add_column_if_missing(
        "sessions",
        "navigation_history_json",
        "navigation_history_json TEXT DEFAULT '[]'",
    )
    _add_column_if_missing("sessions", "join_code", "join_code VARCHAR(4)")
    _add_column_if_missing("nodes", "layout", "layout VARCHAR(32) DEFAULT 'default'")
    _add_column_if_missing("assets", "sort_order", "sort_order INTEGER DEFAULT 0")


def _backfill_join_codes() -> None:
    from app.services.join_code import backfill_missing_join_codes

    db = SessionLocal()
    try:
        if backfill_missing_join_codes(db) > 0:
            db.commit()
    finally:
        db.close()


def init_db():
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    migrate_schema()
    _backfill_join_codes()
