from enum import Enum
from sqlmodel import Field, SQLModel, Relationship
from .employee import Employee
from .project import Project


class Status(str, Enum):
    todo = "todo"
    in_progress = "in_progress"
    completed = "completed"


class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    status: Status = Field(default=Status.in_progress)
    employee_id: int | None = Field(default=None, foreign_key="employee.id")
    employee: Employee | None = Relationship(back_populates="tasks")
    project_id: int | None = Field(default=None, foreign_key="project.id")
    project: Project | None = Relationship(back_populates="tasks")
