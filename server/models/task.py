from enum import Enum
from typing import Optional
from sqlmodel import Field, SQLModel, Relationship
from .employee import Employee
from .project import Project


class TaskStatus(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    completed = "completed"


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    status: TaskStatus = Field(default=TaskStatus.in_progress)
    employee_id: int | None = Field(default=None, foreign_key="employee.id")
    employee: Optional[Employee] = Relationship(back_populates="tasks")
    project_id: int | None = Field(default=None, foreign_key="project.id")
    project: Optional[Project] = Relationship(back_populates="tasks")