from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, List
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .task import Task


class ProjectStatus(str, Enum):
    planning = "planning"
    in_progress = "in_progress"
    completed = "completed"


class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str
    deadline: date
    status: ProjectStatus = Field(default=ProjectStatus.in_progress)
    tasks: List["Task"] = Relationship(back_populates="project")