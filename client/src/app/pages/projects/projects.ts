import { Component, computed, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

import { ProjectService } from '../../core/api/project.service';
import { AuthService } from '../../core/auth/auth.service';
import { Project, ProjectStatus } from '../../core/models';
import { ProjectFormDialog } from './project-form-dialog';
import { ConfirmDialog, ConfirmDialogData } from '../../shared/confirm-dialog/confirm-dialog';

const STATUS_LABELS: Record<ProjectStatus, string> = {
  planning: 'Planning',
  in_progress: 'In progress',
  completed: 'Completed',
};

@Component({
  selector: 'app-projects',
  imports: [
    DatePipe,
    MatTableModule,
    MatPaginatorModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  templateUrl: './projects.html',
})
export class Projects {
  private readonly service = inject(ProjectService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly auth = inject(AuthService);

  readonly isHrOrAdmin = this.auth.isHrOrAdmin;
  readonly isAdmin = this.auth.isAdmin;

  readonly projects = signal<Project[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly pageIndex = signal(0);
  readonly pageSize = signal(10);

  // Employees see a read-only table (no actions column).
  readonly columns = computed(() => {
    const base = ['name', 'description', 'deadline', 'status', 'active'];
    return this.isHrOrAdmin() ? [...base, 'actions'] : base;
  });

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.service.list(this.pageIndex() * this.pageSize(), this.pageSize()).subscribe({
      next: (page) => {
        this.projects.set(page.items);
        this.total.set(page.total);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.notify('Failed to load projects.');
      },
    });
  }

  onPage(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
    this.load();
  }

  statusLabel(status: ProjectStatus): string {
    return STATUS_LABELS[status];
  }

  add(): void {
    this.dialog
      .open(ProjectFormDialog, { data: null, width: '560px' })
      .afterClosed()
      .subscribe((result) => {
        if (result) {
          this.notify('Project created.');
          this.load();
        }
      });
  }

  edit(project: Project): void {
    this.dialog
      .open(ProjectFormDialog, { data: project, width: '560px' })
      .afterClosed()
      .subscribe((result) => {
        if (result) {
          this.notify('Project updated.');
          this.load();
        }
      });
  }

  deactivate(project: Project): void {
    const data: ConfirmDialogData = {
      title: 'Deactivate project',
      message: `Deactivate "${project.name}"? It is preserved and can be reactivated by an admin.`,
      confirmText: 'Deactivate',
      danger: true,
    };
    this.dialog
      .open(ConfirmDialog, { data })
      .afterClosed()
      .subscribe((confirmed) => {
        if (!confirmed) return;
        this.service.deactivate(project.id).subscribe({
          next: () => {
            this.notify('Project deactivated.');
            this.load();
          },
          error: (err) => this.notify(err?.error?.detail ?? 'Failed to deactivate project.'),
        });
      });
  }

  remove(project: Project): void {
    const data: ConfirmDialogData = {
      title: 'Delete project',
      message: `Permanently delete "${project.name}"? This cannot be undone. Its tasks will be unassigned.`,
      confirmText: 'Delete',
      danger: true,
    };
    this.dialog
      .open(ConfirmDialog, { data })
      .afterClosed()
      .subscribe((confirmed) => {
        if (!confirmed) return;
        this.service.remove(project.id).subscribe({
          next: () => {
            this.notify('Project deleted.');
            this.load();
          },
          error: (err) => this.notify(err?.error?.detail ?? 'Failed to delete project.'),
        });
      });
  }

  private notify(message: string): void {
    this.snackBar.open(message, 'Dismiss', { duration: 4000 });
  }
}