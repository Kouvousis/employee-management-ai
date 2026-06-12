"""
Project Schemas — Pydantic models for request/response contracts.

Separate from the SQLModel table so that:
  - ProjectRead:          controls what the API returns (id included, no nested data)
  - ProjectCreate:        controls what the client sends to create a project
  - ProjectUpdate:        partial update (all fields optional)
  - ProjectDelete:        confirmation response after deletion
  - ProjectWithTasks:     ProjectRead with nested task list for the detail view
"""
from datetime import date
from pydantic import BaseModel, Field, ConfigDict
from models.project import ProjectStatus
from schemas.task import TaskWithEmployee


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    deadline: date
    status: ProjectStatus
    is_active: bool


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["New Website Launch"])
    description: str = Field(..., min_length=1, max_length=500, examples=["Launch a new company website by Q4"])
    deadline: date
    status: ProjectStatus = ProjectStatus.planning


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    deadline: date | None = None
    status: ProjectStatus | None = None


class ProjectDelete(BaseModel):
    id: int
    message: str = "Project deleted successfully"


class ProjectWithTasks(ProjectRead):
    tasks: list[TaskWithEmployee] = []


class ProjectPage(BaseModel):
    items: list[ProjectRead]
    total: int
    skip: int
    limit: int