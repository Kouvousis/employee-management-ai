from datetime import date
from enum import Enum
from typing import TYPE_CHECKING
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .Task import Task


class AccessRights(str, Enum):
    admin = "admin"
    employee = "employee"
    human_resources = "human_resources"


class Employee(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str
    department: str
    hire_date: date
    role: str
    access_rights: AccessRights = Field(default=AccessRights.employee)
    tasks: list["Task"] = Relationship(back_populates="employee")
