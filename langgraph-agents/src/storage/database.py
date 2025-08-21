from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
from typing import Any, Iterable

from sqlalchemy import Column, DateTime, Integer, MetaData, String, Table, create_engine, insert, select
from sqlalchemy.exc import IntegrityError


class Database:
    def __init__(self, db_path: str | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[2]
        data_dir = base_dir / "data"
        data_dir.mkdir(parents=True, exist_ok=True)
        env_path = os.getenv("DATABASE_PATH")
        resolved = Path(env_path) if env_path else None
        self.db_file = Path(db_path) if db_path else (resolved or data_dir / "books.db")
        self.engine = create_engine(f"sqlite:///{self.db_file}", future=True, connect_args={"check_same_thread": False})
        self.metadata = MetaData()
        self.books = Table(
            "books",
            self.metadata,
            Column("md5", String(32), primary_key=True),
            Column("title", String, nullable=False),
            Column("author", String, nullable=True),
            Column("year", Integer, nullable=True),
            Column("format", String, nullable=True),
            Column("size", String, nullable=True),
            Column("added_at", DateTime, nullable=False, default=datetime.utcnow),
        )
        self.sessions = Table(
            "search_sessions",
            self.metadata,
            Column("id", Integer, primary_key=True, autoincrement=True),
            Column("query", String, nullable=False),
            Column("timestamp", DateTime, nullable=False, default=datetime.utcnow),
            Column("result_count", Integer, nullable=False),
        )
        self.metadata.create_all(self.engine)

    def save_books(self, books: Iterable[dict[str, Any] | Any]) -> int:
        inserted = 0
        with self.engine.begin() as conn:
            for b in books:
                data = b.model_dump() if hasattr(b, "model_dump") else dict(b)
                row = {
                    "md5": data.get("md5"),
                    "title": data.get("title"),
                    "author": data.get("author"),
                    "year": data.get("year"),
                    "format": data.get("file_format"),
                    "size": data.get("filesize"),
                    "added_at": datetime.utcnow(),
                }
                try:
                    conn.execute(insert(self.books).values(row))
                    inserted += 1
                except IntegrityError:
                    continue
        return inserted

    def get_books(self, limit: int = 100) -> list[dict[str, Any]]:
        with self.engine.begin() as conn:
            stmt = select(
                self.books.c.md5,
                self.books.c.title,
                self.books.c.author,
                self.books.c.year,
                self.books.c.format,
                self.books.c.size,
                self.books.c.added_at,
            ).order_by(self.books.c.added_at.desc()).limit(limit)
            rows = conn.execute(stmt).mappings().all()
            return [dict(r) for r in rows]

    def save_session(self, query: str, result_count: int) -> int:
        with self.engine.begin() as conn:
            res = conn.execute(insert(self.sessions).values(query=query, timestamp=datetime.utcnow(), result_count=result_count))
            return int(res.inserted_primary_key[0]) if res.inserted_primary_key else 0


