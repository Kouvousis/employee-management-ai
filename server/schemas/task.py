"""
Task Schemas — Pydantic models for request/response contracts.

Separate from the SQLModel table so that:
  - TaskRead:           controls what the API returns (id included)
  - TaskWithEmployee:   TaskRead with nested employee for project detail view
  - TaskCreate:         controls what the client sends to create a task
  - TaskUpdate:         partial update for title, status, employee, or project
  - TaskStatusUpdate:   partial update restricted to status field only
  - TaskDelete:         confirmation response after deletion
"""
from __future__ import annotations
from typing import TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, Field
from models.task import TaskStatus

if TYPE_CHECKING:
    from schemas.employee import EmployeeRead


class TaskRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: TaskStatus
    employee_id: int | None
    project_id: int | None


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, examples=["Fix login bug"])
    status: TaskStatus = TaskStatus.todo
    employee_id: int | None = None
    project_id: int | None = None


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    status: TaskStatus | None = None
    employee_id: int | None = None
    project_id: int | None = None


class TaskStatusUpdate(BaseModel):
    status: TaskStatus


class TaskDelete(BaseModel):
    id: int
    message: str = "Task deleted successfully"


class TaskWithEmployee(TaskRead):
    employee: EmployeeRead | None = None


TaskWithEmployee.model_rebuild()
