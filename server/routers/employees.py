from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import selectinload
from sqlalchemy import func
from sqlmodel import Session, select

from database import get_session
from models import Employee, Task, User, AccessRights
from rag.sync import delete_employee_vector, sync_single_employee
from routers.auth import get_current_user, require_admin, require_hr_or_admin
from schemas.employee import EmployeeCreate, EmployeeDelete, EmployeePage, EmployeeRead, EmployeeUpdate, \
    EmployeeWithTasks

router = APIRouter(prefix="/employees", tags=["employees"])


@router.get("", response_model=EmployeePage)
def list_employees(
        skip: int = 0,
        limit: int = 50,
        session: Session = Depends(get_session),
        _: User = Depends(require_hr_or_admin),
):
    """
    Return a paginated list of active employees. Requires HR or admin access.

    Use `skip` and `limit` to paginate: `?skip=0&limit=50`, `?skip=50&limit=50`, etc.
    """
    total = session.exec(select(func.count(Employee.id))).one()
    items = session.exec(select(Employee).offset(skip).limit(limit)).all()
    return EmployeePage(items=items, total=total, skip=skip, limit=limit)


@router.get("/{employee_id}", response_model=EmployeeWithTasks)
def get_employee(
        employee_id: int,
        session: Session = Depends(get_session),
        current_user: User = Depends(get_current_user),
):
    """
    Return a single employee with their assigned tasks.

    Employees may only access their own record. HR and admin can access any record.
    """
    is_hr_or_admin = current_user.access_rights in (AccessRights.admin, AccessRights.human_resources)
    if not is_hr_or_admin and current_user.employee_id != employee_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")

    employee = session.exec(
        select(Employee)
        .where(Employee.id == employee_id)
        .options(selectinload(Employee.tasks))
    ).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    return employee


@router.post("", response_model=EmployeeRead, status_code=status.HTTP_201_CREATED)
def create_employee(
        data: EmployeeCreate,
        session: Session = Depends(get_session),
        _: User = Depends(require_hr_or_admin),
):
    """Create a new employee record. Requires HR or admin access."""
    employee = Employee(**data.model_dump())
    session.add(employee)
    session.commit()
    session.refresh(employee)
    assert employee.id is not None
    sync_single_employee(employee.id)
    return employee


@router.patch("/{employee_id}", response_model=EmployeeRead)
def update_employee(
        employee_id: int,
        data: EmployeeUpdate,
        session: Session = Depends(get_session),
        _: User = Depends(require_hr_or_admin),
):
    """Update one or more fields on an existing employee. Requires HR or admin access."""
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    for field, value in data.model_dump(exclude_none=True).items():
        setattr(employee, field, value)

    session.add(employee)
    session.commit()
    session.refresh(employee)
    sync_single_employee(employee_id)
    return employee


@router.post("/{employee_id}/deactivate", response_model=EmployeeRead)
def deactivate_employee(
        employee_id: int,
        session: Session = Depends(get_session),
        _: User = Depends(require_hr_or_admin),
):
    """
    Deactivate an employee (soft delete — sets is_active to False).

    The record is preserved and can be reactivated by an admin.
    Requires HR or admin access.
    """
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")
    if not employee.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Employee is already inactive")

    employee.is_active = False
    session.add(employee)
    session.commit()
    session.refresh(employee)
    sync_single_employee(employee_id)
    return employee


@router.delete("/{employee_id}", response_model=EmployeeDelete)
def delete_employee(
        employee_id: int,
        session: Session = Depends(get_session),
        _: User = Depends(require_admin),
):
    """
    Permanently delete an employee record (hard delete — cannot be undone).

    Tasks assigned to this employee will be unassigned but preserved.
    Requires HR or admin access.
    """
    employee = session.get(Employee, employee_id)
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found")

    for task in session.exec(select(Task).where(Task.employee_id == employee_id)).all():
        task.employee_id = None
        session.add(task)

    session.delete(employee)
    session.commit()
    delete_employee_vector(employee_id)
    return EmployeeDelete(id=employee_id)
