export type ProjectStatus = 'planning' | 'in_progress' | 'completed';

export interface Project {
  id: number;
  name: string;
  description: string;
  /** ISO date string (YYYY-MM-DD). */
  deadline: string;
  status: ProjectStatus;
  is_active: boolean;
}

export interface ProjectCreate {
  name: string;
  description: string;
  deadline: string;
  status?: ProjectStatus;
}

export type ProjectUpdate = Partial<ProjectCreate>;