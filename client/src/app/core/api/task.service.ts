import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Page } from '../models';
import { Task, TaskCreate, TaskStatus, TaskUpdate } from '../models';

@Injectable({ providedIn: 'root' })
export class TaskService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/tasks`;

  list(skip = 0, limit = 50): Observable<Page<Task>> {
    return this.http.get<Page<Task>>(this.base, { params: { skip, limit } });
  }

  get(id: number): Observable<Task> {
    return this.http.get<Task>(`${this.base}/${id}`);
  }

  create(data: TaskCreate): Observable<Task> {
    return this.http.post<Task>(this.base, data);
  }

  update(id: number, data: TaskUpdate): Observable<Task> {
    return this.http.patch<Task>(`${this.base}/${id}`, data);
  }

  updateStatus(id: number, status: TaskStatus): Observable<Task> {
    return this.http.patch<Task>(`${this.base}/${id}/status`, { status });
  }

  /** HR/admin hard delete. */
  remove(id: number): Observable<{ id: number; message: string }> {
    return this.http.delete<{ id: number; message: string }>(`${this.base}/${id}`);
  }
}
