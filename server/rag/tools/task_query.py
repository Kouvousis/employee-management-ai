"""
Structured task query tool.

Answers task-ownership and task-status questions by querying PostgreSQL directly
(joining Task -> Employee and Task -> Project), so results are exact and exhaustive
regardless of database size. Vector similarity search is unsuitable here: task
assignments live inside employee documents and a top-k search silently drops any
task whose owner doesn't rank in the top few matches.
"""
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from database import engine
from models import Employee, Project, Task
from models.task import TaskStatus


class _QueryTasksInput(BaseModel):
    title: str | None = Field(
        default=None, description="Filter by task title (partial, case-insensitive)."
    )
    status: str | None = Field(
        default=None,
        description="Filter by status: 'todo', 'in_progress', or 'completed'.",
    )
    employee: str | None = Field(
        default=None,
        description="Filter by assignee first or last name (partial, case-insensitive).",
    )
    project: str | None = Field(
        default=None, description="Filter by project name (partial, case-insensitive)."
    )
    limit: int = Field(default=50, description="Maximum number of tasks to return.")


@tool(args_schema=_QueryTasksInput)
def query_tasks(
    title: str | None = None,
    status: str | None = None,
    employee: str | None = None,
    project: str | None = None,
    limit: int = 50,
) -> str:
    """Look up tasks and who is assigned to them. Use this for questions like
    'who is in charge of <task>', 'who is working on <task>', 'what is the status of
    <task>', or 'what tasks are in <project>'. Returns each matching task with its
    assignee and project — exact results straight from the database, not a sample."""
    try:
        with Session(engine) as session:
            stmt = select(Task).options(
                selectinload(Task.employee), selectinload(Task.project)
            )
            if title:
                stmt = stmt.where(col(Task.title).ilike(f"%{title}%"))
            if status:
                try:
                    stmt = stmt.where(Task.status == TaskStatus(status))
                except ValueError:
                    return (
                        f"Unknown status '{status}'. Valid values: todo, in_progress, completed."
                    )
            if employee:
                stmt = stmt.join(Employee, Task.employee_id == Employee.id).where(
                    col(Employee.first_name).ilike(f"%{employee}%")
                    | col(Employee.last_name).ilike(f"%{employee}%")
                )
            if project:
                stmt = stmt.join(Project, Task.project_id == Project.id).where(
                    col(Project.name).ilike(f"%{project}%")
                )

            tasks = session.exec(stmt.limit(limit)).all()

        if not tasks:
            return "No tasks match those filters."

        lines = []
        for t in tasks:
            assignee = (
                f"{t.employee.first_name} {t.employee.last_name}"
                if t.employee
                else "Unassigned"
            )
            proj = t.project.name if t.project else "no project"
            lines.append(
                f'- "{t.title}" (status: {t.status.value}) — assigned to {assignee} — project: {proj}'
            )
        return f"{len(tasks)} task(s) found:\n" + "\n".join(lines)
    except Exception as e:
        return f"Failed to query tasks: {e}"