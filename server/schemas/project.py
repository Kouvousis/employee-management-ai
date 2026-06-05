from datetime import date
from typing import List

from pydantic import BaseModel, Field, ConfigDict
from models.project import ProjectStatus
from schemas.employee import EmployeeRead
from schemas.task import TaskRead


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    deadline: date
    status: ProjectStatus
    tasks: List[TaskRead]
    employees: List[EmployeeRead]


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, examples=["New Website Launch"])
    description: str = Field(..., min_length=1, max_length=500, examples=["Launch a new company website by Q4"])
    deadline: date = Field(..., examples=["2024-12-31"])
    status: ProjectStatus = ProjectStatus.in_progress


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, min_length=1, max_length=500)
    deadline: date | None = Field(default=None, examples=["2024-12-31"])
    status: ProjectStatus | None = Field(default=None)


class ProjectDelete(BaseModel):
    id: int
    message: str = "Project deleted successfully"
