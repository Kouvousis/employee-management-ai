from datetime import date
from typing import TYPE_CHECKING, List, Optional
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .task import Task
    from .user import User


class Employee(SQLModel, table=True):
    """HR record for a NovaTech employee. Auth concerns (password, access rights) live in User;
    this model holds identity and organizational data only."""

    id: int | None = Field(default=None, primary_key=True)
    first_name: str
    last_name: str
    email: str
    department: str
    hire_date: date
    role: str
    tasks: List["Task"] = Relationship(back_populates="employee")
    user: Optional["User"] = Relationship(back_populates="employee")
    is_active: bool = Field(default=True, description="Whether the employee is active and can be modified.")
