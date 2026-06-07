from datetime import date
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlmodel import Session
from database import engine
from models import Employee, Task, Project
from models.project import ProjectStatus
from rag.sync import sync_single_employee
from schemas.project import ProjectCreate


class _DeactivateProjectInput(BaseModel):
    id: int = Field(..., description="ID of the project to deactivate")
    reason: str | None = Field(default=None, description="Optional reason for deactivation")


class _AssignEmployeeToProjectInput(BaseModel):
    employee_id: int = Field(..., description="ID of the employee to assign")
    project_id: int = Field(..., description="ID of the project to assign them to")
    task_title: str = Field(..., description="Title of the task linking the employee to the project")


@tool(args_schema=ProjectCreate)
def create_project_tool(name: str, description: str, deadline: date,
                        status: ProjectStatus = ProjectStatus.planning) -> str:
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


@tool(args_schema=_DeactivateProjectInput)
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