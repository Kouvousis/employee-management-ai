from sqlalchemy import func
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models import Project, Task, User
from models.user import AccessRights
from routers.auth import get_current_user, require_admin, require_hr_or_admin
from schemas.project import ProjectCreate, ProjectDelete, ProjectPage, ProjectRead, ProjectUpdate, ProjectWithTasks

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=ProjectPage)
def list_projects(
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Return a paginated list of active projects.

    HR and admin see all projects. Employees see only projects they are assigned to via a task.
    Use `skip` and `limit` to paginate: `?skip=0&limit=50`, `?skip=50&limit=50`, etc.
    """
    is_hr_or_admin = current_user.access_rights in (AccessRights.admin, AccessRights.human_resources)

    if is_hr_or_admin:
        total = session.exec(select(func.count(Project.id))).one()
        items = session.exec(select(Project).offset(skip).limit(limit)).all()
    else:
        base = (
            select(Project)
            .join(Task, Task.project_id == Project.id)
            .where(Project.is_active == True)
            .where(Task.employee_id == current_user.employee_id)
            .distinct()
        )
        total = session.exec(select(func.count()).select_from(base.subquery())).one()
        items = session.exec(base.offset(skip).limit(limit)).all()

    return ProjectPage(items=items, total=total, skip=skip, limit=limit)


@router.get("/{project_id}", response_model=ProjectWithTasks)
def get_project(
    project_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Return a single project with its tasks and assigned employees.

    HR and admin can access any project. Employees can only access projects they are assigned to.
    """
    is_hr_or_admin = current_user.access_rights in (AccessRights.admin, AccessRights.human_resources)

    if not is_hr_or_admin:
        assigned = session.exec(
            select(Task)
            .where(Task.project_id == project_id)
            .where(Task.employee_id == current_user.employee_id)
        ).first()
        if not assigned:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    project = session.exec(
        select(Project)
        .where(Project.id == project_id)
        .options(selectinload(Project.tasks))
    ).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(
    data: ProjectCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_hr_or_admin),
):
    """Create a new project. Requires HR or admin access."""
    project = Project(**data.model_dump())
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int,
    data: ProjectUpdate,
    session: Session = Depends(get_session),
    _: User = Depends(require_hr_or_admin),
):
    """Update one or more fields on an existing project. Requires HR or admin access."""
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(project, field, value)

    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.post("/{project_id}/deactivate", response_model=ProjectRead)
def deactivate_project(
    project_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_hr_or_admin),
):
    """
    Deactivate a project (soft delete — sets is_active to False).

    The record is preserved and can be reactivated by an admin.
    Requires HR or admin access.
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if not project.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project is already inactive")

    project.is_active = False
    session.add(project)
    session.commit()
    session.refresh(project)
    return project


@router.delete("/{project_id}", response_model=ProjectDelete)
def delete_project(
    project_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_admin),
):
    """
    Permanently delete a project (hard delete — cannot be undone).

    Tasks belonging to this project will be unassigned but preserved.
    Requires admin access.
    """
    project = session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    for task in session.exec(select(Task).where(Task.project_id == project_id)).all():
        task.project_id = None
        session.add(task)

    session.delete(project)
    session.commit()
    return ProjectDelete(id=project_id)