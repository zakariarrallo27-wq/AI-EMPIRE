"""Authenticated HTTP API for AI-EMPIRE / Jarvis."""
from __future__ import annotations

import hmac
import os
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

from jarvis_bus import JarvisBus

DB_PATH = Path(os.getenv("JARVIS_DB_PATH", "data/jarvis.db"))
API_TOKEN = os.getenv("JARVIS_API_TOKEN", "")
bearer = HTTPBearer(auto_error=False)
bus = JarvisBus(DB_PATH)
app = FastAPI(
    title="AI-EMPIRE / Jarvis API",
    version="0.1.0",
    description="API autenticada para proyectos, tareas y mensajes compartidos.",
)


def require_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> None:
    if not API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El servidor no tiene configurado JARVIS_API_TOKEN.",
        )
    if credentials is None or not hmac.compare_digest(
        credentials.credentials, API_TOKEN
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token ausente o no válido.",
            headers={"WWW-Authenticate": "Bearer"},
        )


class ProjectIn(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class TaskIn(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    details: str = Field(default="", max_length=10000)
    assigned_to: str | None = Field(default=None, max_length=100)


class MessageIn(BaseModel):
    sender: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=20000)
    recipient: str | None = Field(default=None, max_length=100)
    message_type: str = Field(default="note", max_length=40)


class AgentIn(BaseModel):
    agent: str = Field(min_length=1, max_length=100)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "jarvis-api", "version": "0.1.0"}


@app.post("/v1/projects", dependencies=[Depends(require_token)], status_code=201)
def create_project(payload: ProjectIn) -> dict[str, str]:
    from jarvis_core import JarvisCoordinator

    project_id = JarvisCoordinator(db_path=DB_PATH).create_project(payload.title)
    return {"project_id": project_id, "title": payload.title.strip()}


@app.get("/v1/projects/{project_id}/tasks", dependencies=[Depends(require_token)])
def list_tasks(project_id: str, task_status: str | None = None) -> list[dict[str, Any]]:
    return bus.list_tasks(project_id, task_status)


@app.post(
    "/v1/projects/{project_id}/tasks",
    dependencies=[Depends(require_token)],
    status_code=201,
)
def create_task(project_id: str, payload: TaskIn) -> dict[str, str]:
    try:
        task_id = bus.add_task(
            project_id, payload.title, payload.details, payload.assigned_to
        )
        return {"task_id": task_id, "status": "pending"}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/v1/tasks/{task_id}/claim", dependencies=[Depends(require_token)])
def claim_task(task_id: str, payload: AgentIn) -> dict[str, Any]:
    claimed = bus.claim_task(task_id, payload.agent)
    if not claimed:
        raise HTTPException(
            status_code=409,
            detail="La tarea no existe, ya está reclamada o está asignada a otro agente.",
        )
    return {"task_id": task_id, "status": "in_progress", "claimed_by": payload.agent}


@app.post("/v1/tasks/{task_id}/complete", dependencies=[Depends(require_token)])
def complete_task(task_id: str, payload: AgentIn) -> dict[str, str]:
    if not bus.complete_task(task_id, payload.agent):
        raise HTTPException(
            status_code=409,
            detail="No se puede completar: la tarea no está reclamada por ese agente.",
        )
    return {"task_id": task_id, "status": "completed"}


@app.get("/v1/projects/{project_id}/messages", dependencies=[Depends(require_token)])
def get_inbox(project_id: str, agent: str) -> list[dict[str, Any]]:
    return bus.inbox(project_id, agent)


@app.post(
    "/v1/projects/{project_id}/messages",
    dependencies=[Depends(require_token)],
    status_code=201,
)
def send_message(project_id: str, payload: MessageIn) -> dict[str, int]:
    try:
        message_id = bus.send_message(
            project_id,
            payload.sender,
            payload.content,
            payload.recipient,
            payload.message_type,
        )
        return {"message_id": message_id}
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
