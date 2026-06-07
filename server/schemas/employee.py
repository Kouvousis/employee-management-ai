"""
Employee Schemas — Pydantic models for request/response contracts.

Separate from the SQLModel table so that:
  - EmployeeRead:        controls what the API returns (id included)
  - EmployeeCreate:      controls what the client sends to create an employee
  - EmployeeUpdate:      allows partial updates (all fields optional)
  - EmployeeDelete:      confirmation response after deletion
  - EmployeeWithTasks:   EmployeeRead with nested task list for the detail view
"""
from __future__ import annotations
from datetime import date
from typing import TYPE_CHECKING
from pydantic import BaseModel, ConfigDict, Field, EmailStr

if TYPE_CHECKING:
    from schemas.task import TaskRead


class EmployeeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: EmailStr
    department: str
    hire_date: date
    role: str


class EmployeeCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50, examples=["John"])
    last_name: str = Field(..., min_length=1, max_length=50, examples=["Doe"])
    email: EmailStr
    department: str = Field(..., min_length=1, examples=["Engineering"])
    hire_date: date
    role: str = Field(..., min_length=1, examples=["Backend Engineer"])


class EmployeeUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=50)
    last_name: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = None
    department: str | None = Field(default=None, min_length=1)
    hire_date: date | None = None
    role: str | None = Field(default=None, min_length=1)


class EmployeeDelete(BaseModel):
    id: int
    message: str = "Employee deleted successfully"


class EmployeeWithTasks(EmployeeRead):
    tasks: list[TaskRead] = []
