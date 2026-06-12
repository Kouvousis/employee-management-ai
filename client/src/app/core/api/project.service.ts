import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

import { environment } from '../../../environments/environment';
import { Project, ProjectCreate, ProjectUpdate } from '../models';
import { Page } from '../models';

@Injectable({ providedIn: 'root' })
export class ProjectService {
  private readonly http = inject(HttpClient);
  private readonly base = `${environment.apiUrl}/projects`;

  list(skip = 0, limit = 50): Observable<Page<Project>> {
    return this.http.get<Page<Project>>(this.base, { params: { skip, limit } });
  }

  get(id: number): Observable<Project> {
    return this.http.get<Project>(`${this.base}/${id}`);
  }

  create(data: ProjectCreate): Observable<Project> {
    return this.http.post<Project>(this.base, data);
  }

  update(id: number, data: ProjectUpdate): Observable<Project> {
    return this.http.patch<Project>(`${this.base}/${id}`, data);
  }

  deactivate(id: number): Observable<Project> {
    return this.http.post<Project>(`${this.base}/${id}/deactivate`, {});
  }

  /** Admin-only hard delete. */
  remove(id: number): Observable<{ id: number; message: string }> {
    return this.http.delete<{ id: number; message: string }>(`${this.base}/${id}`);
  }
}
