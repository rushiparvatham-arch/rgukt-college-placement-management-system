"""Lightweight SQLite column patches for evolving schema without Alembic."""
from __future__ import annotations

from sqlalchemy import inspect, text

from app.extensions import db


def _existing_columns(table: str) -> set[str]:
    inspector = inspect(db.engine)
    if table not in inspector.get_table_names():
        return set()
    return {col["name"] for col in inspector.get_columns(table)}


def ensure_schema():
    patches = [
        ("aptitude_tests", "branches", "VARCHAR(255) DEFAULT 'All Branches'"),
        ("aptitude_results", "answers_json", "TEXT"),
        ("aptitude_tests", "created_by", "INTEGER"),
        ("aptitude_tests", "published", "BOOLEAN DEFAULT 1"),
    ]
    with db.engine.begin() as conn:
        for table, column, ddl in patches:
            cols = _existing_columns(table)
            if cols and column not in cols:
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {ddl}"))