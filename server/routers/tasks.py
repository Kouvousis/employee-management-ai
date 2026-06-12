from sqlalchemy import func
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from database import get_session
from models import Task, User
from routers.auth import get_current_user, require_hr_or_admin
from schemas.task import TaskCreate, TaskDelete, TaskPage, TaskRead, TaskStatusUpdate, TaskUpdate, TaskWithEmployee

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=TaskPage)
def list_tasks(
    skip: int = 0,
    limit: int = 50,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Return a paginated list of tasks visible to the current user.

    HR and admin see all tasks. Employees see only their own assigned tasks.
    Use `skip` and `limit` to paginate: `?skip=0&limit=50`, `?skip=50&limit=50`, etc.
    """
    is_hr_or_admin = current_user.access_rights.value in ("admin", "human_resources")

    if is_hr_or_admin:
        total = session.exec(select(func.count(Task.id))).one()
        items = session.exec(select(Task).offset(skip).limit(limit)).all()
    else:
        base = select(Task).where(Task.employee_id == current_user.employee_id)
        total = session.exec(select(func.count(Task.id)).where(Task.employee_id == current_user.employee_id)).one()
        items = session.exec(base.offset(skip).limit(limit)).all()

    return TaskPage(items=items, total=total, skip=skip, limit=limit)


@router.get("/{task_id}", response_model=TaskWithEmployee)
def get_task(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Return a single task with its assigned employee.

    HR and admin can access any task. Employees can only access their own tasks.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    is_hr_or_admin = current_user.access_rights.value in ("admin", "human_resources")
    if not is_hr_or_admin and task.employee_id != current_user.employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    return task


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(
    data: TaskCreate,
    session: Session = Depends(get_session),
    _: User = Depends(require_hr_or_admin),
):
    """Create a new task. Requires HR or admin access."""
    task = Task(**data.model_dump())
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    data: TaskUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Update one or more fields on a task.

    HR and admin can update any task field. Employees can only update the status
    of their own tasks.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    is_hr_or_admin = current_user.access_rights.value in ("admin", "human_resources")

    if not is_hr_or_admin:
        if task.employee_id != current_user.employee_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        allowed_fields = {"status"}
        payload = {k: v for k, v in data.model_dump(exclude_none=True).items() if k in allowed_fields}
    else:
        payload = data.model_dump(exclude_none=True)

    for field, value in payload.items():
        setattr(task, field, value)

    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.patch("/{task_id}/status", response_model=TaskRead)
def update_task_status(
    task_id: int,
    data: TaskStatusUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    """
    Update only the status of a task.

    HR and admin can update any task. Employees can only update their own tasks.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    is_hr_or_admin = current_user.access_rights.value in ("admin", "human_resources")
    if not is_hr_or_admin and task.employee_id != current_user.employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    task.status = data.status
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


@router.delete("/{task_id}", response_model=TaskDelete)
def delete_task(
    task_id: int,
    session: Session = Depends(get_session),
    _: User = Depends(require_hr_or_admin),
):
    """
    Permanently delete a task (hard delete — cannot be undone).

    Requires HR or admin access.
    """
    task = session.get(Task, task_id)
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    session.delete(task)
    session.commit()
    return TaskDelete(id=task_id)