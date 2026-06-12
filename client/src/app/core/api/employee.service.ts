import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Employee, EmployeeCreate, EmployeeUpdate } from '../models';
import { Page } from '../models';

@Injectable({ providedIn: 'root' })
export class EmployeeService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/employees`;

  list(skip = 0, limit = 50): Observable<Page<Employee>> {
    return this.http.get<Page<Employee>>(this.base, { params: { skip, limit } });
  }

  get(id: number): Observable<Employee> {
    return this.http.get<Employee>(`${this.base}/${id}`);
  }

  create(data: EmployeeCreate): Observable<Employee> {
    return this.http.post<Employee>(this.base, data);
  }

  update(id: number, data: EmployeeUpdate): Observable<Employee> {
    return this.http.patch<Employee>(`${this.base}/${id}`, data);
  }

  deactivate(id: number): Observable<Employee> {
    return this.http.post<Employee>(`${this.base}/${id}/deactivate`, {});
  }

  /** Admin-only hard delete. */
  remove(id: number): Observable<{ id: number; message: string }> {
    return this.http.delete<{ id: number; message: string }>(`${this.base}/${id}`);
  }
}
