"""Shared task queue and agent mailbox for the Jarvis coordinator.

Uses the same SQLite database as jarvis_core.py. Safe for multiple local
processes: task claims use BEGIN IMMEDIATE and a conditional status update.
This is a local persistence layer, not yet a network service.
"""
from __future__ import annotations

import argparse
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_PATH = Path(os.getenv("JARVIS_DB_PATH", "data/jarvis.db"))


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JarvisBus:
    def __init__(self, db_path: Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _db(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.db_path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        db.execute("PRAGMA busy_timeout = 15000")
        return db

    def _initialize(self) -> None:
        with self._db() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'active',
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL REFERENCES projects(id),
                    agent TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL REFERENCES projects(id),
                    title TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL
                );
                """
            )
            task_columns = {r["name"] for r in db.execute("PRAGMA table_info(tasks)")}
            additions = {
                "details": "TEXT NOT NULL DEFAULT ''",
                "assigned_to": "TEXT",
                "claimed_by": "TEXT",
                "updated_at": "TEXT",
            }
            for name, sql_type in additions.items():
                if name not in task_columns:
                    db.execute(f"ALTER TABLE tasks ADD COLUMN {name} {sql_type}")
            message_columns = {r["name"] for r in db.execute("PRAGMA table_info(messages)")}
            if "recipient" not in message_columns:
                db.execute("ALTER TABLE messages ADD COLUMN recipient TEXT")
            if "message_type" not in message_columns:
                db.execute("ALTER TABLE messages ADD COLUMN message_type TEXT NOT NULL DEFAULT 'note'")
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_tasks_project_status ON tasks(project_id, status, created_at)"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_messages_inbox ON messages(project_id, recipient, id)"
            )

    def add_task(
        self, project_id: str, title: str, details: str = "", assigned_to: str | None = None
    ) -> str:
        title = title.strip()
        if not title:
            raise ValueError("El título de la tarea no puede estar vacío.")
        task_id = str(uuid.uuid4())
        timestamp = now()
        with self._db() as db:
            exists = db.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not exists:
                raise ValueError("No existe el proyecto indicado.")
            db.execute(
                """INSERT INTO tasks
                   (id, project_id, title, status, created_at, details, assigned_to, updated_at)
                   VALUES (?, ?, ?, 'pending', ?, ?, ?, ?)""",
                (task_id, project_id, title, timestamp, details, assigned_to, timestamp),
            )
        return task_id

    def claim_task(self, task_id: str, agent: str) -> bool:
        if not agent.strip():
            raise ValueError("Indica el nombre del agente.")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            result = db.execute(
                """UPDATE tasks
                   SET status = 'in_progress', claimed_by = ?, updated_at = ?
                   WHERE id = ? AND status = 'pending'
                     AND (assigned_to IS NULL OR assigned_to = ?)""",
                (agent, now(), task_id, agent),
            )
            return result.rowcount == 1

    def complete_task(self, task_id: str, agent: str) -> bool:
        with self._db() as db:
            result = db.execute(
                """UPDATE tasks SET status = 'completed', updated_at = ?
                   WHERE id = ? AND status = 'in_progress' AND claimed_by = ?""",
                (now(), task_id, agent),
            )
            return result.rowcount == 1

    def list_tasks(self, project_id: str, status: str | None = None) -> list[dict[str, Any]]:
        with self._db() as db:
            if status:
                rows = db.execute(
                    "SELECT * FROM tasks WHERE project_id = ? AND status = ? ORDER BY created_at",
                    (project_id, status),
                ).fetchall()
            else:
                rows = db.execute(
                    "SELECT * FROM tasks WHERE project_id = ? ORDER BY created_at",
                    (project_id,),
                ).fetchall()
            return [dict(row) for row in rows]

    def send_message(
        self, project_id: str, sender: str, content: str,
        recipient: str | None = None, message_type: str = "note"
    ) -> int:
        sender, content = sender.strip(), content.strip()
        if not sender or not content:
            raise ValueError("El remitente y el contenido son obligatorios.")
        with self._db() as db:
            exists = db.execute("SELECT 1 FROM projects WHERE id = ?", (project_id,)).fetchone()
            if not exists:
                raise ValueError("No existe el proyecto indicado.")
            cursor = db.execute(
                """INSERT INTO messages
                   (project_id, agent, content, created_at, recipient, message_type)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (project_id, sender, content, now(), recipient, message_type),
            )
            return int(cursor.lastrowid)

    def inbox(self, project_id: str, agent: str) -> list[dict[str, Any]]:
        with self._db() as db:
            rows = db.execute(
                """SELECT id, agent AS sender, recipient, message_type, content, created_at
                   FROM messages
                   WHERE project_id = ? AND (recipient IS NULL OR recipient = ?)
                   ORDER BY id""",
                (project_id, agent),
            ).fetchall()
            return [dict(row) for row in rows]


def main() -> int:
    parser = argparse.ArgumentParser(description="Mensajería y tareas compartidas de Jarvis")
    parser.add_argument("--db", default=str(DB_PATH), help="Ruta de la base SQLite")
    commands = parser.add_subparsers(dest="command", required=True)

    task = commands.add_parser("add-task")
    task.add_argument("project_id")
    task.add_argument("title")
    task.add_argument("--details", default="")
    task.add_argument("--assigned-to")

    claim = commands.add_parser("claim")
    claim.add_argument("task_id")
    claim.add_argument("agent")

    done = commands.add_parser("complete")
    done.add_argument("task_id")
    done.add_argument("agent")

    listing = commands.add_parser("tasks")
    listing.add_argument("project_id")
    listing.add_argument("--status")

    send = commands.add_parser("send")
    send.add_argument("project_id")
    send.add_argument("sender")
    send.add_argument("content")
    send.add_argument("--to", dest="recipient")

    inbox = commands.add_parser("inbox")
    inbox.add_argument("project_id")
    inbox.add_argument("agent")

    args = parser.parse_args()
    bus = JarvisBus(Path(args.db))
    try:
        if args.command == "add-task":
            print(bus.add_task(args.project_id, args.title, args.details, args.assigned_to))
        elif args.command == "claim":
            print("Tarea reclamada." if bus.claim_task(args.task_id, args.agent) else "No disponible: ya reclamada, inexistente o asignada a otro agente.")
        elif args.command == "complete":
            print("Tarea completada." if bus.complete_task(args.task_id, args.agent) else "No se pudo completar: comprueba que la reclamaste tú.")
        elif args.command == "tasks":
            print(json.dumps(bus.list_tasks(args.project_id, args.status), ensure_ascii=False, indent=2))
        elif args.command == "send":
            print(f"Mensaje guardado: {bus.send_message(args.project_id, args.sender, args.content, args.recipient)}")
        elif args.command == "inbox":
            print(json.dumps(bus.inbox(args.project_id, args.agent), ensure_ascii=False, indent=2))
        return 0
    except ValueError as exc:
        parser.error(str(exc))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
