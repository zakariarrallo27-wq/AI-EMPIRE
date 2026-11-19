"""Persistent coordination core for AI-EMPIRE / Jarvis.

This first milestone runs one sequential agent round and stores projects,
messages, and tasks in SQLite. It does not yet expose a network API or connect
multiple devices; those are separate deployment milestones.
"""
from __future__ import annotations

import argparse
import os
import sqlite3
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from openai import OpenAI

MODEL = os.getenv("AI_EMPIRE_MODEL", "gpt-4.1-mini")
DB_PATH = Path(os.getenv("JARVIS_DB_PATH", "data/jarvis.db"))

AGENTS = (
    ("Estratega", "Analiza el reto, separa hechos de hipótesis, identifica oportunidades y riesgos, y propone una dirección."),
    ("Creadora", "Usa el análisis previo para diseñar una solución concreta: usuario, problema, propuesta de valor y validación."),
    ("Ejecutora", "Convierte lo anterior en tareas pequeñas, ordenadas y verificables. Indica dependencias y primera acción."),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class JarvisCoordinator:
    """Coordinates agents and persists their shared working context."""

    def __init__(self, db_path: Path = DB_PATH, client: OpenAI | None = None):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.client = client
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA foreign_keys = ON;
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

    def create_project(self, title: str) -> str:
        title = title.strip()
        if not title:
            raise ValueError("El título del proyecto no puede estar vacío.")
        project_id = str(uuid.uuid4())
        with self._connect() as db:
            db.execute(
                "INSERT INTO projects(id, title, created_at) VALUES (?, ?, ?)",
                (project_id, title, utc_now()),
            )
            db.execute(
                "INSERT INTO messages(project_id, agent, content, created_at) VALUES (?, ?, ?, ?)",
                (project_id, "Usuario", title, utc_now()),
            )
        return project_id

    def _ask_agent(self, name: str, role: str, context: str) -> str:
        if self.client is None:
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise RuntimeError(
                    "Falta OPENAI_API_KEY. Configúrala como variable de entorno; "
                    "nunca la guardes en el repositorio."
                )
            self.client = OpenAI(api_key=api_key)

        prompt = (
            f"Eres {name}, un agente de AI-EMPIRE. Tu responsabilidad: {role}\n\n"
            "Trabaja con el contexto compartido. Responde en español. No inventes datos, "
            "no afirmes haber ejecutado acciones y señala las incertidumbres. "
            "Cuando propongas tareas, hazlas concretas y comprobables.\n\n"
            f"CONTEXTO COMPARTIDO:\n{context}"
        )
        result = self.client.responses.create(model=MODEL, input=prompt)
        answer = result.output_text.strip()
        if not answer:
            raise RuntimeError(f"El agente {name} devolvió una respuesta vacía.")
        return answer

    def run_round(self, project_id: str) -> list[tuple[str, str]]:
        with self._connect() as db:
            project = db.execute(
                "SELECT id, title FROM projects WHERE id = ?", (project_id,)
            ).fetchone()
            if project is None:
                raise ValueError("No existe ese proyecto.")
            rows = db.execute(
                "SELECT agent, content FROM messages WHERE project_id = ? ORDER BY id",
                (project_id,),
            ).fetchall()

        context = "\n\n".join(f"{row['agent']}: {row['content']}" for row in rows)
        outputs: list[tuple[str, str]] = []
        for name, role in AGENTS:
            answer = self._ask_agent(name, role, context)
            with self._connect() as db:
                db.execute(
                    "INSERT INTO messages(project_id, agent, content, created_at) VALUES (?, ?, ?, ?)",
                    (project_id, name, answer, utc_now()),
                )
            context += f"\n\n{name}: {answer}"
            outputs.append((name, answer))
        return outputs

    def list_projects(self) -> Iterable[sqlite3.Row]:
        with self._connect() as db:
            return db.execute(
                "SELECT id, title, status, created_at FROM projects ORDER BY created_at DESC"
            ).fetchall()

    def get_messages(self, project_id: str) -> Iterable[sqlite3.Row]:
        with self._connect() as db:
            return db.execute(
                "SELECT agent, content, created_at FROM messages "
                "WHERE project_id = ? ORDER BY id",
                (project_id,),
            ).fetchall()


def main() -> int:
    parser = argparse.ArgumentParser(description="Núcleo inicial de coordinación Jarvis")
    subparsers = parser.add_subparsers(dest="command", required=True)
    create_parser = subparsers.add_parser("new", help="Crear un proyecto")
    create_parser.add_argument("title", help="Nombre o reto del proyecto")
    run_parser = subparsers.add_parser("run", help="Ejecutar una ronda de agentes")
    run_parser.add_argument("project_id", help="ID del proyecto")
    subparsers.add_parser("list", help="Listar proyectos guardados")
    args = parser.parse_args()

    try:
        jarvis = JarvisCoordinator()
        if args.command == "new":
            project_id = jarvis.create_project(args.title)
            print(f"Proyecto creado: {project_id}")
        elif args.command == "run":
            for agent, answer in jarvis.run_round(args.project_id):
                print(f"\n--- {agent} ---\n{answer}")
        elif args.command == "list":
            for project in jarvis.list_projects():
                print(f"{project['id']} | {project['status']} | {project['title']}")
        return 0
    except (RuntimeError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
