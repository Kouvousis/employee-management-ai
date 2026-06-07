from datetime import date
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlmodel import Session
from database import engine
from models import Employee, Task, Project
from models.task import TaskStatus
from models.project import ProjectStatus
from rag.sync import sync_single_employee
from schemas.employee import EmployeeCreate
from schemas.task import TaskCreate
from schemas.project import ProjectCreate


@tool
def get_current_date() -> str:
    """Return today's date in YYYY-MM-DD format.
    Call this whenever the user refers to 'today', 'now', or an unspecified date."""
    return date.today().isoformat()


class _DeactivateInput(BaseModel):
    id: int = Field(..., description="ID of the record to deactivate")
    reason: str | None = Field(default=None, description="Optional reason for deactivation")


class _AssignEmployeeToProjectInput(BaseModel):
    employee_id: int = Field(..., description="ID of the employee to assign")
    project_id: int = Field(..., description="ID of the project to assign them to")
    task_title: str = Field(..., description="Title of the task linking the employee to the project")


@tool(args_schema=EmployeeCreate)
def add_employee_tool(first_name: str, last_name: str, email: str, department: str, hire_date: date, role: str) -> str:
    """Add a new employee to the NovaTech database.
    Use this when asked to hire or create a new employee record.
    Infer department and role from context where possible — only ask if genuinely ambiguous."""
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


@tool(args_schema=TaskCreate)
def assign_task_tool(title: str, status: TaskStatus = TaskStatus.todo, employee_id: int | None = None, project_id: int | None = None) -> str:
    """Assign a new task to an existing NovaTech employee.
    Use this when asked to create or assign a task to an employee.
    employee_id is required to assign to a specific employee. project_id is optional."""
    try:
        with Session(engine) as session:
            employee = None
            if employee_id is not None:
                employee = session.get(Employee, employee_id)
                if not employee:
                    return f"Employee with ID {employee_id} not found."

            new_task = Task(title=title, status=status, employee_id=employee_id, project_id=project_id)
            session.add(new_task)
            session.commit()
            name = f"{employee.first_name} {employee.last_name}" if employee else "unassigned"

        if employee_id is not None:
            sync_single_employee(employee_id)

        return f"Task '{title}' assigned to {name} successfully."
    except Exception as e:
        return f"Failed to assign task: {e}"


@tool(args_schema=ProjectCreate)
def create_project_tool(name: str, description: str, deadline: date, status: ProjectStatus = ProjectStatus.planning) -> str:
    """Create a new project in the NovaTech database.
    Use this when asked to start or create a new project.
    Infer status from context where possible. Defaults to planning if not specified."""
    try:
        with Session(engine) as session:
            project = Project(
                name=name,
                description=description,
                deadline=deadline,
                status=status,
            )
            session.add(project)
            session.commit()
            session.refresh(project)
            assert project.id is not None
            project_id = project.id

        return f"Project '{name}' created successfully with ID {project_id}."
    except Exception as e:
        return f"Failed to create project: {e}"


@tool(args_schema=_AssignEmployeeToProjectInput)
def assign_employee_to_project_tool(employee_id: int, project_id: int, task_title: str) -> str:
    """Assign an existing employee to an existing project by creating a task that links them.
    In NovaTech's data model, employees are connected to projects through tasks.
    Use this when asked to add an employee to a project."""
    try:
        with Session(engine) as session:
            employee = session.get(Employee, employee_id)
            if not employee:
                return f"Employee with ID {employee_id} not found."

            project = session.get(Project, project_id)
            if not project:
                return f"Project with ID {project_id} not found."

            task = Task(title=task_title, employee_id=employee_id, project_id=project_id)
            session.add(task)
            session.commit()
            name = f"{employee.first_name} {employee.last_name}"
            project_name = project.name

        sync_single_employee(employee_id)
        return f"{name} assigned to project '{project_name}' with task '{task_title}'."
    except Exception as e:
        return f"Failed to assign employee to project: {e}"


@tool(args_schema=TaskCreate)
def add_task_to_project_tool(title: str, status: TaskStatus = TaskStatus.todo, project_id: int | None = None, employee_id: int | None = None) -> str:
    """Add a new task to an existing project.
    Use this when asked to add a task or work item to a project.
    project_id is required. employee_id is optional — omit if not yet assigned to a specific employee."""
    if project_id is None:
        return "project_id is required to add a task to a project."
    try:
        with Session(engine) as session:
            project = session.get(Project, project_id)
            if not project:
                return f"Project with ID {project_id} not found."

            employee_name = None
            if employee_id is not None:
                employee = session.get(Employee, employee_id)
                if not employee:
                    return f"Employee with ID {employee_id} not found."
                employee_name = f"{employee.first_name} {employee.last_name}"

            task = Task(title=title, status=status, project_id=project_id, employee_id=employee_id)
            session.add(task)
            session.commit()
            project_name = project.name

        if employee_id is not None:
            sync_single_employee(employee_id)

        msg = f"Task '{title}' added to project '{project_name}'."
        if employee_name:
            msg += f" Assigned to {employee_name}."
        return msg
    except Exception as e:
        return f"Failed to add task to project: {e}"


@tool(args_schema=_DeactivateInput)
def deactivate_employee_tool(id: int, reason: str | None = None) -> str:
    """Deactivate an existing employee (soft delete — sets is_active to False).
    Use this when asked to deactivate, disable, or remove an employee.
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


@tool(args_schema=_DeactivateInput)
def deactivate_project_tool(id: int, reason: str | None = None) -> str:
    """Deactivate an existing project (soft delete — sets is_active to False).
    Use this when asked to close, deactivate, or archive a project.
    This does not delete the record — it can be reactivated by an admin."""
    try:
        with Session(engine) as session:
            project = session.get(Project, id)
            if not project:
                return f"Project with ID {id} not found."
            if not project.is_active:
                return f"Project '{project.name}' is already inactive."

            project.is_active = False
            session.add(project)
            session.commit()
            name = project.name

        msg = f"Project '{name}' has been deactivated."
        if reason:
            msg += f" Reason: {reason}."
        return msg
    except Exception as e:
        return f"Failed to deactivate project: {e}"