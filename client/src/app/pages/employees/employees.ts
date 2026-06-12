import { Component, inject, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { MatTableModule } from '@angular/material/table';
import { MatPaginatorModule, PageEvent } from '@angular/material/paginator';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatTooltipModule } from '@angular/material/tooltip';
import { MatDialog } from '@angular/material/dialog';
import { MatSnackBar } from '@angular/material/snack-bar';

import { EmployeeService } from '../../core/api/employee.service';
import { AuthService } from '../../core/auth/auth.service';
import { Employee } from '../../core/models';
import { EmployeeFormDialog } from './employee-form-dialog';
import { ConfirmDialog, ConfirmDialogData } from '../../shared/confirm-dialog/confirm-dialog';

@Component({
  selector: 'app-employees',
  imports: [
    DatePipe,
    MatTableModule,
    MatPaginatorModule,
    MatButtonModule,
    MatIconModule,
    MatProgressBarModule,
    MatTooltipModule,
  ],
  templateUrl: './employees.html',
})
export class Employees {
  private readonly service = inject(EmployeeService);
  private readonly dialog = inject(MatDialog);
  private readonly snackBar = inject(MatSnackBar);
  private readonly auth = inject(AuthService);

  readonly isAdmin = this.auth.isAdmin;

  readonly employees = signal<Employee[]>([]);
  readonly total = signal(0);
  readonly loading = signal(false);
  readonly pageIndex = signal(0);
  readonly pageSize = signal(10);

  readonly columns = ['name', 'email', 'department', 'role', 'hire_date', 'status', 'actions'];

  constructor() {
    this.load();
  }

  load(): void {
    this.loading.set(true);
    this.service.list(this.pageIndex() * this.pageSize(), this.pageSize()).subscribe({
      next: (page) => {
        this.employees.set(page.items);
        this.total.set(page.total);
        this.loading.set(false);
      },
      error: () => {
        this.loading.set(false);
        this.notify('Failed to load employees.');
      },
    });
  }

  onPage(event: PageEvent): void {
    this.pageIndex.set(event.pageIndex);
    this.pageSize.set(event.pageSize);
    this.load();
  }

  add(): void {
    this.dialog
      .open(EmployeeFormDialog, { data: null, width: '560px' })
      .afterClosed()
      .subscribe((result) => {
        if (result) {
          this.notify('Employee added.');
          this.load();
        }
      });
  }

  edit(employee: Employee): void {
    this.dialog
      .open(EmployeeFormDialog, { data: employee, width: '560px' })
      .afterClosed()
      .subscribe((result) => {
        if (result) {
          this.notify('Employee updated.');
          this.load();
        }
      });
  }

  deactivate(employee: Employee): void {
    const data: ConfirmDialogData = {
      title: 'Deactivate employee',
      message: `Deactivate ${employee.first_name} ${employee.last_name}? Their record is preserved and can be reactivated by an admin.`,
      confirmText: 'Deactivate',
      danger: true,
    };
    this.dialog
      .open(ConfirmDialog, { data })
      .afterClosed()
      .subscribe((confirmed) => {
        if (!confirmed) return;
        this.service.deactivate(employee.id).subscribe({
          next: () => {
            this.notify('Employee deactivated.');
            this.load();
          },
          error: (err) => this.notify(err?.error?.detail ?? 'Failed to deactivate employee.'),
        });
      });
  }

  remove(employee: Employee): void {
    const data: ConfirmDialogData = {
      title: 'Delete employee',
      message: `Permanently delete ${employee.first_name} ${employee.last_name}? This cannot be undone.`,
      confirmText: 'Delete',
      danger: true,
    };
    this.dialog
      .open(ConfirmDialog, { data })
      .afterClosed()
      .subscribe((confirmed) => {
        if (!confirmed) return;
        this.service.remove(employee.id).subscribe({
          next: () => {
            this.notify('Employee deleted.');
            this.load();
          },
          error: (err) => this.notify(err?.error?.detail ?? 'Failed to delete employee.'),
        });
      });
  }

  private notify(message: string): void {
    this.snackBar.open(message, 'Dismiss', { duration: 4000 });
  }
}
