"""
Structured project query tool.

Answers questions about a project's own attributes (name, description, deadline,
status, active state, task count) by querying PostgreSQL directly. Projects are not
held in any vector store, so this is the only way the agent can read live project
data exactly and exhaustively.
"""
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlalchemy.orm import selectinload
from sqlmodel import Session, col, select

from database import engine
from models import Project
from models.project import ProjectStatus


class _QueryProjectsInput(BaseModel):
    name: str | None = Field(
        default=None, description="Filter by project name (partial, case-insensitive)."
    )
    status: str | None = Field(
        default=None,
        description="Filter by status: 'planning', 'in_progress', or 'completed'.",
    )
    include_inactive: bool = Field(
        default=False,
        description="Include deactivated projects. Defaults to active projects only.",
    )
    limit: int = Field(default=50, description="Maximum number of projects to return.")


@tool(args_schema=_QueryProjectsInput)
def query_projects(
    name: str | None = None,
    status: str | None = None,
    include_inactive: bool = False,
    limit: int = 50,
) -> str:
    """List projects and their details — name, description, deadline, status, and how
    many tasks each has. Use for project questions like 'what projects do we have',
    'what is the deadline for <project>', 'what status is <project> in', or 'which
    projects are in planning'. Returns exact results from the database, not a sample."""
    try:
        with Session(engine) as session:
            stmt = select(Project).options(selectinload(Project.tasks))
            if not include_inactive:
                stmt = stmt.where(Project.is_active == True)  # noqa: E712
            if name:
                stmt = stmt.where(col(Project.name).ilike(f"%{name}%"))
            if status:
                try:
                    stmt = stmt.where(Project.status == ProjectStatus(status))
                except ValueError:
                    return (
                        f"Unknown status '{status}'. Valid values: planning, in_progress, completed."
                    )
            stmt = stmt.order_by(col(Project.deadline)).limit(limit)
            projects = session.exec(stmt).all()

            if not projects:
                return "No projects match those filters."

            lines = []
            for p in projects:
                active = "" if p.is_active else " [INACTIVE]"
                lines.append(
                    f'- "{p.name}" (status: {p.status.value}, deadline: {p.deadline}, '
                    f"tasks: {len(p.tasks)}){active}\n  {p.description}"
                )
            return f"{len(projects)} project(s) found:\n" + "\n".join(lines)
    except Exception as e:
        return f"Failed to query projects: {e}"