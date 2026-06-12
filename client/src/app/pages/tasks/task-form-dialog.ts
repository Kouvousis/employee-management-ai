import { Component, inject, signal } from '@angular/core';
import { form, FormField, required } from '@angular/forms/signals';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { TaskService } from '../../core/api/task.service';
import { Employee, Project, Task, TaskCreate, TaskStatus } from '../../core/models';

const STATUSES: { value: TaskStatus; label: string }[] = [
  { value: 'todo', label: 'To do' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
];

export interface TaskDialogData {
  task: Task | null;
  employees: Employee[];
  projects: Project[];
}

interface TaskFormModel {
  title: string;
  status: TaskStatus;
  employee_id: number | null;
  project_id: number | null;
}

@Component({
  selector: 'app-task-form-dialog',
  imports: [
    FormField,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './task-form-dialog.html',
})
export class TaskFormDialog {
  private readonly service = inject(TaskService);
  private readonly ref = inject(MatDialogRef<TaskFormDialog>);
  readonly data = inject<TaskDialogData>(MAT_DIALOG_DATA);

  readonly statuses = STATUSES;
  readonly employees = this.data.employees;
  readonly projects = this.data.projects;
  readonly isEdit = this.data.task !== null;
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  readonly model = signal<TaskFormModel>(
    this.data.task
      ? {
          title: this.data.task.title,
          status: this.data.task.status,
          employee_id: this.data.task.employee_id,
          project_id: this.data.task.project_id,
        }
      : { title: '', status: 'todo', employee_id: null, project_id: null },
  );

  readonly taskForm = form(this.model, (path) => {
    required(path.title, { message: 'Required' });
  });

  save(): void {
    if (!this.taskForm().valid()) return;

    this.saving.set(true);
    this.error.set(null);

    const v = this.model();
    const payload: TaskCreate = {
      title: v.title,
      status: v.status,
      employee_id: v.employee_id,
      project_id: v.project_id,
    };

    const request = this.data.task
      ? this.service.update(this.data.task.id, payload)
      : this.service.create(payload);

    request.subscribe({
      next: (task) => {
        this.saving.set(false);
        this.ref.close(task);
      },
      error: (err) => {
        this.saving.set(false);
        this.error.set(err?.error?.detail ?? 'Could not save the task. Please try again.');
      },
    });
  }
}
