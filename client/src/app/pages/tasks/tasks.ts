import { Component, computed, inject, signal } from '@angular/core';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatMenuModule } from '@angular/material/menu';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

import { TaskService } from '../../core/api/task.service';
import { EmployeeService } from '../../core/api/employee.service';
import { ProjectService } from '../../core/api/project.service';
import { AuthService } from '../../core/auth/auth.service';
import { Employee, Project, Task, TaskStatus } from '../../core/models';
import { TaskFormDialog } from './task-form-dialog';
import { ConfirmDialog, ConfirmDialogData } from '../../shared/confirm-dialog/confirm-dialog';

const STATUS_LABELS: Record<TaskStatus, string> = {
  todo: 'To do',
  in_progress: 'In progress',
  completed: 'Completed',
};

const STATUS_CLASSES: Record<TaskStatus, string> = {
  todo: 'bg-gray-200 text-gray-700',
  in_progress: 'bg-amber-100 text-amber-800',
  completed: 'bg-green-100 text-green-800',
};

@Component({
  selector: 'app-tasks',
  imports: [
    MatTableModule,
    MatPaginatorModule,
    MatButtonModule,
    MatIconModule,
    MatMenuModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  templateUrl: './tasks.html',
})
export class Tasks {
  private readonly taskService = inject(TaskService);
  private readonly employeeService = inject(EmployeeService);
  private readonly projectService = inject(ProjectService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly auth = inject(AuthService);

  readonly isHrOrAdmin = this.auth.isHrOrAdmin;

  readonly tasks = signal<Task[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly pageIndex = signal(0);
  readonly pageSize = signal(10);

  // Reference data for name resolution and the form dialog dropdowns.
  readonly employees = signal<Employee[]>([]);
  readonly projects = signal<Project[]>([]);
  private readonly employeeMap = computed(
    () => new Map(this.employees().map((e) => [e.id, `${e.first_name} ${e.last_name}`])),
  );
  private readonly projectMap = computed(
    () => new Map(this.projects().map((p) => [p.id, p.name])),
  );

  readonly statuses: TaskStatus[] = ['todo', 'in_progress', 'completed'];

  readonly columns = computed(() => {
    const base = ['title', 'status', 'assignee', 'project'];
    return this.isHrOrAdmin() ? [...base, 'actions'] : base;
  });

  constructor() {
    this.loadReference();
    this.load();
  }

  private loadReference(): void {
    // Projects are listable by every role (employees get their own).
    this.projectService.list(0, 1000).subscribe({
      next: (page) => this.projects.set(page.items),
      error: () => {},
    });
    // The employee roster is HR/admin only.
    if (this.isHrOrAdmin()) {
      this.employeeService.list(0, 1000).subscribe({
        next: (page) => this.employees.set(page.items),
        error: () => {},
      });
    }
  }

  load(): void {
    this.loading.set(true);
    this.taskService.list(this.pageIndex() * this.pageSize(), this.pageSize()).subscribe({
      next: (page) => {
        this.tasks.set(page.items);
        this.total.set(page.total);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.notify('Failed to load tasks.');
      },
    });
  }

  onPage(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
    this.load();
  }

  statusLabel(status: TaskStatus): string {
    return STATUS_LABELS[status];
  }

  statusClass(status: TaskStatus): string {
    return STATUS_CLASSES[status];
  }

  assigneeName(task: Task): string {
    if (task.employee_id == null) return 'Unassigned';
    const mapped = this.employeeMap().get(task.employee_id);
    if (mapped) return mapped;
    // Employees can't load the roster, but their own tasks are theirs.
    const user = this.auth.user();
    if (user?.employee_id === task.employee_id && user.first_name) {
      return `${user.first_name} ${user.last_name ?? ''}`.trim();
    }
    return `#${task.employee_id}`;
  }

  projectName(task: Task): string {
    if (task.project_id == null) return '—';
    return this.projectMap().get(task.project_id) ?? `#${task.project_id}`;
  }

  changeStatus(task: Task, status: TaskStatus): void {
    if (task.status === status) return;
    this.taskService.updateStatus(task.id, status).subscribe({
      next: (updated) => {
        this.tasks.update((list) => list.map((t) => (t.id === task.id ? updated : t)));
        this.notify('Status updated.');
      },
      error: (err) => {
        this.notify(err?.error?.detail ?? 'Failed to update status.');
        this.load();
      },
    });
  }

  add(): void {
    this.dialog
      .open(TaskFormDialog, {
        data: { task: null, employees: this.employees(), projects: this.projects() },
        width: '520px',
      })
      .afterClosed()
      .subscribe((result) => {
        if (result) {
          this.notify('Task created.');
          this.load();
        }
      });
  }

  edit(task: Task): void {
    this.dialog
      .open(TaskFormDialog, {
        data: { task, employees: this.employees(), projects: this.projects() },
        width: '520px',
      })
      .afterClosed()
      .subscribe((result) => {
        if (result) {
          this.notify('Task updated.');
          this.load();
        }
      });
  }

  remove(task: Task): void {
    const data: ConfirmDialogData = {
      title: 'Delete task',
      message: `Permanently delete "${task.title}"? This cannot be undone.`,
      confirmText: 'Delete',
      danger: true,
    };
    this.dialog
      .open(ConfirmDialog, { data })
      .afterClosed()
      .subscribe((confirmed) => {
        if (!confirmed) return;
        this.taskService.remove(task.id).subscribe({
          next: () => {
            this.notify('Task deleted.');
            this.load();
          },
          error: (err) => this.notify(err?.error?.detail ?? 'Failed to delete task.'),
        });
      });
  }

  private notify(message: string): void {
    this.snackBar.open(message, 'Dismiss', { duration: 4000 });
  }
}