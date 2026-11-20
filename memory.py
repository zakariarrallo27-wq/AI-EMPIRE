import sqlite3
from pathlib import Path
from datetime import datetime

DB_DIR = Path(__file__).parent / "data"
DB_PATH = DB_DIR / "jarvis_memory.db"


def initialize_memory():
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)


def save_memory(content, category="general"):
    initialize_memory()
    with sqlite3.connect(DB_PATH) as connection:
        connection.execute(
            """
            INSERT INTO memories (category, content, created_at)
            VALUES (?, ?, ?)
            """,
            (category, content, datetime.now().isoformat(timespec="seconds"))
        )


def list_memories(limit=20):
    if isinstance(limit, bool) or not isinstance(limit, int) or limit <= 0:
        raise ValueError("limit debe ser un entero positivo.")

    if not DB_PATH.is_file():
        raise RuntimeError(f"No existe la base de datos de memoria: {DB_PATH}")

    database_uri = DB_PATH.resolve().as_uri() + "?mode=ro"

    try:
        with sqlite3.connect(database_uri, uri=True) as connection:
            return connection.execute(
                """
                SELECT id, category, content, created_at
                FROM memories
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
    except sqlite3.Error as exc:
        raise RuntimeError(
            f"No se pudo consultar la memoria en modo solo lectura: {exc}"
        ) from exc
