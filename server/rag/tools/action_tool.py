from langchain_core.tools import tool
from sqlmodel import Session
from database import engine
from models import Employee, Task
from rag.sync import sync_single_employee
from datetime import date


@tool
def add_employee_tool(first_name: str, last_name: str, email: str, department: str, hire_date: str, role: str) -> str:
    """Add a new employee to the NovaTech database.
    Use this when asked to hire or create a new employee record.
    Required fields: first_name, last_name, email, department, hire_date (YYYY-MM-DD), and role.
    If any required field is missing from the user's request, ask for it before calling this tool."""
    try:
        with Session(engine) as session:
            new_employee = Employee(
                first_name=first_name,
                last_name=last_name,
                email=email,
                department=department,
                hire_date=date.fromisoformat(hire_date),
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


@tool
def assign_task_tool(title: str, employee_id: int, project_id: int | None = None) -> str:
    """Assign a new task to an existing NovaTech employee.
    Use this when asked to create or assign a task.
    Requires the task title and the employee's ID. project_id is optional — omit if no project is specified."""

    try:
        with Session(engine) as session:
            employee = session.get(Employee, employee_id)
            if not employee:
                return f"Employee with ID {employee_id} not found."

            new_task = Task(title=title, employee_id=employee_id, project_id=project_id)
            session.add(new_task)
            session.commit()
            session.refresh(new_task)
            name = f"{employee.first_name} {employee.last_name}"

        sync_single_employee(employee_id)
        return f"Task '{title}' assigned to {name} successfully."
    except Exception as e:
        return f"Failed to assign task: {e}"
