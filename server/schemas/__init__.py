from schemas.employee import EmployeeRead, EmployeeCreate, EmployeeUpdate, EmployeeDelete, EmployeeWithTasks
from schemas.task import TaskRead, TaskCreate, TaskUpdate, TaskStatusUpdate, TaskDelete, TaskWithEmployee

EmployeeWithTasks.model_rebuild(_types_namespace={"TaskRead": TaskRead})
TaskWithEmployee.model_rebuild(_types_namespace={"EmployeeRead": EmployeeRead})