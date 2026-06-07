from datetime import date
from enum import Enum
from typing import TYPE_CHECKING, List
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .task import Task


class ProjectStatus(str, Enum):
    """Lifecycle stage of a project. Named ProjectStatus (not Status) to avoid a PostgreSQL enum type collision with TaskStatus."""

    planning = "planning"
    in_progress = "in_progress"
    completed = "completed"


class Project(SQLModel, table=True):
    """A company initiative that groups one or more Tasks."""

    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str
    deadline: date
    status: ProjectStatus = Field(default=ProjectStatus.in_progress)
    tasks: List["Task"] = Relationship(back_populates="project")
    is_active: bool = Field(default=True, description="Whether the project is active and can be modified.")

