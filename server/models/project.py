from datetime import date
from enum import Enum
from typing import TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .task import Task


class Status(str, Enum):
    planning = "planning"
    in_progress = "in_progress"
    completed = "completed"


class Project(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    description: str
    deadline: date
    status: Status = Field(default=Status.in_progress)
    tasks: list["Task"] = Relationship(back_populates="project")
