"""
Structured employee query tools.

These hit PostgreSQL directly (not the vector store) so that enumeration and
aggregation questions — "who works in Engineering", "list all backend engineers",
"how many people per department" — return exact, exhaustive results that scale as
the database grows. The vector-based employee_knowledge_tool remains for fuzzy,
single-person lookups.
"""
from langchain_core.tools import tool
from pydantic import BaseModel, Field
from sqlmodel import Session, col, func, select

from database import engine
from models import Employee


class _QueryEmployeesInput(BaseModel):
    department: str | None = Field(
        default=None,
        description=(
            "Filter by department — e.g. 'Engineering', 'Sales', 'Product', 'HR', "
            "'Leadership', 'Data & AI'. Partial, case-insensitive match."
        ),
    )
    role: str | None = Field(
        default=None,
        description=(
            "Filter by job role/title — e.g. 'engineer', 'manager'. Partial, "
            "case-insensitive: 'engineer' matches every engineer role."
        ),
    )
    name: str | None = Field(
        default=None,
        description="Filter by first or last name. Partial, case-insensitive match.",
    )
    include_inactive: bool = Field(
        default=False,
        description="Include deactivated employees. Defaults to active employees only.",
    )
    limit: int = Field(default=100, description="Maximum number of employees to return.")


class _CountEmployeesInput(BaseModel):
    group_by: str | None = Field(
        default=None,
        description="Optional grouping: 'department' or 'role'. Omit for a single total headcount.",
    )
    include_inactive: bool = Field(
        default=False,
        description="Include deactivated employees. Defaults to active employees only.",
    )


@tool(args_schema=_QueryEmployeesInput)
def query_employees(
    department: str | None = None,
    role: str | None = None,
    name: str | None = None,
    include_inactive: bool = False,
    limit: int = 100,
) -> str:
    """List employees filtered by department, role, name, or status — returns ALL
    matching employees, never a similarity-ranked sample. Use this for enumeration
    and "who works..." questions such as 'who works in Engineering', 'list all
    backend engineers', or 'who is in Sales'. For a fuzzy question about one specific
    named person (their details or tasks), prefer employee_knowledge_tool."""
    try:
        with Session(engine) as session:
            stmt = select(Employee)
            if not include_inactive:
                stmt = stmt.where(Employee.is_active == True)  # noqa: E712
            if department:
                stmt = stmt.where(col(Employee.department).ilike(f"%{department}%"))
            if role:
                stmt = stmt.where(col(Employee.role).ilike(f"%{role}%"))
            if name:
                stmt = stmt.where(
                    col(Employee.first_name).ilike(f"%{name}%")
                    | col(Employee.last_name).ilike(f"%{name}%")
                )
            stmt = stmt.order_by(col(Employee.department), col(Employee.last_name)).limit(limit)
            employees = session.exec(stmt).all()

        if not employees:
            return "No employees match those filters."

        lines = [
            f"- {e.first_name} {e.last_name} — {e.role}, {e.department} "
            f"({e.email}), hired {e.hire_date}"
            + ("" if e.is_active else " [INACTIVE]")
            for e in employees
        ]
        return f"{len(employees)} employee(s) found:\n" + "\n".join(lines)
    except Exception as e:
        return f"Failed to query employees: {e}"


@tool(args_schema=_CountEmployeesInput)
def count_employees(group_by: str | None = None, include_inactive: bool = False) -> str:
    """Count employees, optionally grouped by 'department' or 'role'. Use for
    headcount questions like 'how many employees are there', 'how many people per
    department', or 'how many engineers do we have'."""
    try:
        with Session(engine) as session:
            if group_by in ("department", "role"):
                group_col = Employee.department if group_by == "department" else Employee.role
                stmt = select(col(group_col), func.count())
                if not include_inactive:
                    stmt = stmt.where(Employee.is_active == True)  # noqa: E712
                stmt = stmt.group_by(col(group_col)).order_by(func.count().desc())
                rows = session.exec(stmt).all()

                if not rows:
                    return "No employees found."
                total = sum(count for _, count in rows)
                lines = [f"- {value}: {count}" for value, count in rows]
                return f"Total: {total}\nBy {group_by}:\n" + "\n".join(lines)

            stmt = select(func.count()).select_from(Employee)
            if not include_inactive:
                stmt = stmt.where(Employee.is_active == True)  # noqa: E712
            total = session.exec(stmt).one()
            scope = "" if include_inactive else " (active)"
            return f"Total employees{scope}: {total}"
    except Exception as e:
        return f"Failed to count employees: {e}"