from schemas.employee import EmployeeRead, EmployeeCreate, EmployeeUpdate, EmployeeDelete, EmployeeWithTasks, EmployeePage
from schemas.task import TaskRead, TaskCreate, TaskUpdate, TaskStatusUpdate, TaskDelete, TaskWithEmployee, TaskPage
from schemas.project import ProjectRead, ProjectCreate, ProjectUpdate, ProjectDelete, ProjectWithTasks, ProjectPage
from schemas.auth import LoginRequest, TokenResponse
from schemas.chat import ChatRequest, ChatResponse

EmployeeWithTasks.model_rebuild(_types_namespace={"TaskRead": TaskRead})
TaskWithEmployee.model_rebuild(_types_namespace={"EmployeeRead": EmployeeRead})