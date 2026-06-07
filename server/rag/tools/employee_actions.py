from datetime import date
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlmodel import Session
from database import engine
from models import Employee
from rag.sync import sync_single_employee
from schemas.employee import EmployeeCreate, EmployeeUpdate


class _UpdateEmployeeInput(EmployeeUpdate):
    employee_id: int = Field(..., description="ID of the employee to update")


class _DeactivateEmployeeInput(BaseModel):
    id: int = Field(..., description="ID of the employee to deactivate")
    reason: str | None = Field(default=None, description="Optional reason for deactivation")


@tool(args_schema=EmployeeCreate)
def add_employee_tool(first_name: str, last_name: str, email: str, department: str, hire_date: date, role: str) -> str:
    """Add a new employee to the NovaTech database.
    Use this only when asked to hire or onboard a brand-new employee — not to correct an existing record."""
    try:
        with Session(engine) as session:
            new_employee = Employee(
                first_name=first_name,
                last_name=last_name,
                email=email,
                department=department,
                hire_date=hire_date,
                role=role,
            )
            session.add(new_employee)
            session.commit()
            session.refresh(new_employee)
            assert new_employee.id is not None
            employee_id = new_employee.id

        sync_single_employee(employee_id)
        return f"Employee {first_name} {last_name} added successfully with ID {employee_id}."
    except Exception as e:
        return f"Failed to add employee: {e}"


@tool(args_schema=_UpdateEmployeeInput)
def update_employee_tool(employee_id: int, first_name: str | None = None, last_name: str | None = None,
                         email: str | None = None, department: str | None = None, hire_date: date | None = None,
                         role: str | None = None) -> str:
    """Update one or more fields on an existing employee record.
    Use this when asked to correct, edit, or change an employee's details.
    Only provide the fields that need to change — all fields are optional except employee_id."""
    try:
        with Session(engine) as session:
            employee = session.get(Employee, employee_id)
            if not employee:
                return f"Employee with ID {employee_id} not found."

            if first_name is not None:
                employee.first_name = first_name
            if last_name is not None:
                employee.last_name = last_name
            if email is not None:
                employee.email = email
            if department is not None:
                employee.department = department
            if hire_date is not None:
                employee.hire_date = hire_date
            if role is not None:
                employee.role = role

            session.add(employee)
            session.commit()
            name = f"{employee.first_name} {employee.last_name}"

        sync_single_employee(employee_id)
        return f"Employee record updated successfully. Current name: {name}."
    except Exception as e:
        return f"Failed to update employee: {e}"


@tool(args_schema=_DeactivateEmployeeInput)
def deactivate_employee_tool(id: int, reason: str | None = None) -> str:
    """Deactivate an existing employee (soft delete — sets is_active to False).
    Use this only when explicitly asked to deactivate or disable an employee.
    Do not use this to correct or fix an employee record.
    This does not delete the record — it can be reactivated by an admin.
    User accounts are not affected by this tool."""
    try:
        with Session(engine) as session:
            employee = session.get(Employee, id)
            if not employee:
                return f"Employee with ID {id} not found."
            if not employee.is_active:
                return f"{employee.first_name} {employee.last_name} is already inactive."

            employee.is_active = False
            session.add(employee)
            session.commit()
            name = f"{employee.first_name} {employee.last_name}"

        sync_single_employee(id)
        msg = f"{name} has been deactivated."
        if reason:
            msg += f" Reason: {reason}."
        return msg
    except Exception as e:
        return f"Failed to deactivate employee: {e}"
