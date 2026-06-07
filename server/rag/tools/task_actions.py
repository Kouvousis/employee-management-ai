from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlmodel import Session
from database import engine
from models import Employee, Task
from models.task import TaskStatus
from rag.sync import sync_single_employee
from schemas.task import TaskCreate


class _DeleteTaskInput(BaseModel):
    task_id: int = Field(..., description="ID of the task to permanently delete")


@tool(args_schema=TaskCreate)
def assign_task_tool(title: str, status: TaskStatus = TaskStatus.todo, employee_id: int | None = None,
                     project_id: int | None = None) -> str:
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


@tool(args_schema=TaskCreate)
def add_task_to_project_tool(title: str, status: TaskStatus = TaskStatus.todo, project_id: int | None = None,
                             employee_id: int | None = None) -> str:
    """Add a new task to an existing project.
    Use this when asked to add a task or work item to a project.
    project_id is required. employee_id is optional — omit if not yet assigned to a specific employee."""
    if project_id is None:
        return "project_id is required to add a task to a project."
    try:
        with Session(engine) as session:
            from models import Project
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


@tool(args_schema=_DeleteTaskInput)
def delete_task_tool(task_id: int) -> str:
    """Permanently delete a task from the database (hard delete — cannot be undone).
    Use this only when asked to delete or remove a task.
    Do not use this for employees or projects — those can only be deactivated."""
    try:
        with Session(engine) as session:
            task = session.get(Task, task_id)
            if not task:
                return f"Task with ID {task_id} not found."

            employee_id = task.employee_id
            title = task.title
            session.delete(task)
            session.commit()

        if employee_id is not None:
            sync_single_employee(employee_id)

        return f"Task '{title}' (ID {task_id}) has been permanently deleted."
    except Exception as e:
        return f"Failed to delete task: {e}"