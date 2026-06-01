from enum import Enum
from typing import TYPE_CHECKING, Optional
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .employee import Employee


class AccessRights(str, Enum):
    admin = "admin"
    employee = "employee"
    human_resources = "human_resources"


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    hashed_password: str
    access_rights: AccessRights = Field(default=AccessRights.employee)
    employee_id: int | None = Field(default=None, foreign_key="employee.id")
    employee: Optional["Employee"] = Relationship(back_populates="user")