export type TaskStatus = 'todo' | 'in_progress' | 'completed';

export interface Task {
  id: number;
  title: string;
  status: TaskStatus;
  employee_id: number | null;
  project_id: number | null;
}

export interface TaskCreate {
  title: string;
  status?: TaskStatus;
  employee_id?: number | null;
  project_id?: number | null;
}

export type TaskUpdate = Partial<TaskCreate>;