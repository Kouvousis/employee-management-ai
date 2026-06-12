export interface Employee {
  id: number;
  first_name: string;
  last_name: string;
  email: string;
  department: string;
  /** ISO date string (YYYY-MM-DD). */
  hire_date: string;
  role: string;
  is_active: boolean;
}

export interface EmployeeCreate {
  first_name: string;
  last_name: string;
  email: string;
  department: string;
  hire_date: string;
  role: string;
}

export type EmployeeUpdate = Partial<EmployeeCreate>;