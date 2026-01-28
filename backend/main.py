"""FastAPI implementation for Sync To-Do backend
Implements required endpoints:
  - GET /tasks
  - POST /tasks
  - PATCH /tasks/{id}
Default storage is in-memory; optional Cassandra layer can be enabled via USE_CASSANDRA env var.
"""

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import uuid4
import os

# Attempt to import Cassandra driver; backend works without it if not installed
try:
    from cassandra.cluster import Cluster  # type: ignore
except ImportError:  # pragma: no cover
    Cluster = None  # type: ignore


# -------------------------------------------------
# Pydantic models
# -------------------------------------------------
class Task(BaseModel):
    id: str
    title: str = Field(..., max_length=140)
    completed: bool = False


class TaskCreate(BaseModel):
    title: str = Field(..., max_length=140)


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=140)
    completed: Optional[bool] = None


# -------------------------------------------------
# Storage interface and implementations
# -------------------------------------------------
class Storage:
    """Abstract storage interface."""

    def list_tasks(self) -> List[Task]:
        raise NotImplementedError

    def create_task(self, title: str) -> Task:
        raise NotImplementedError

    def update_task(self, task_id: str, data: TaskUpdate) -> Task:
        raise NotImplementedError


class InMemoryStorage(Storage):
    """Simple in-memory task store."""

    def __init__(self):
        self._tasks: dict[str, Task] = {}

    # GET /tasks
    def list_tasks(self) -> List[Task]:
        # Return newest-first order by creation (UUID randomness acceptable for demo)
        return list(self._tasks.values())[::-1]

    # POST /tasks
    def create_task(self, title: str) -> Task:
        new_task = Task(id=str(uuid4()), title=title, completed=False)
        self._tasks[new_task.id] = new_task
        return new_task

    # PATCH /tasks/{id}
    def update_task(self, task_id: str, data: TaskUpdate) -> Task:
        if task_id not in self._tasks:
            raise KeyError("not_found")
        current = self._tasks[task_id]
        updated = current.copy(update=data.dict(exclude_unset=True))
        self._tasks[task_id] = updated
        return updated


class CassandraStorage(Storage):
    """Cassandra-based storage (stub). Enabled when USE_CASSANDRA=true."""

    def __init__(self):
        if Cluster is None:
            raise RuntimeError("cassandra-driver not installed")
        cluster = Cluster()
        self.session = cluster.connect()
        # NOTE: For brevity, keyspace/table creation is omitted.

    def list_tasks(self) -> List[Task]:
        # Dummy implementation – returns empty list
        return []

    def create_task(self, title: str) -> Task:
        raise NotImplementedError("Cassandra layer not implemented yet")

    def update_task(self, task_id: str, data: TaskUpdate) -> Task:
        raise NotImplementedError("Cassandra layer not implemented yet")


# -------------------------------------------------
# Application factory
# -------------------------------------------------

def get_storage() -> Storage:
    """Chooses storage backend based on environment variable."""
    if os.getenv("USE_CASSANDRA", "").lower() == "true":
        try:
            return CassandraStorage()
        except Exception as exc:
            # Fallback to in-memory if Cassandra init fails
            print(f"Cassandra storage unavailable: {exc}. Falling back to in-memory.")
    return InMemoryStorage()


app = FastAPI(title="Sync To-Do API", version="1.0.0")
storage: Storage = get_storage()


# -------------------------------------------------
# API endpoints (spec-compliant)
# -------------------------------------------------

@app.get("/tasks", response_model=List[Task])  # GET /tasks
def get_tasks() -> List[Task]:
    """Return list of all tasks (newest-first)."""
    return storage.list_tasks()


@app.post("/tasks", response_model=Task, status_code=status.HTTP_201_CREATED)  # POST /tasks
def create_task(payload: TaskCreate) -> Task:
    """Create a new task."""
    try:
        return storage.create_task(payload.title)
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"code": "invalid_input", "message": str(exc)}
        ) from exc


@app.patch("/tasks/{task_id}", response_model=Task)  # PATCH /tasks/{id}
def update_task(task_id: str, payload: TaskUpdate) -> Task:
    """Update task title and/or completion status."""
    try:
        return storage.update_task(task_id, payload)
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail={"code": "not_found", "message": "Task not found"}
        )


# -------------------------------------------------
# Local development entrypoint
# -------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
