import { Component, inject, signal } from '@angular/core';
import { email as emailValidator, form, FormField, required } from '@angular/forms/signals';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import moment from 'moment';

import { EmployeeService } from '../../core/api/employee.service';
import { Employee, EmployeeCreate } from '../../core/models';

const DEPARTMENTS = ['Engineering', 'Product', 'Leadership', 'HR', 'Sales', 'Data & AI'];

interface EmployeeFormModel {
  first_name: string;
  last_name: string;
  email: string;
  department: string;
  role: string;
  hire_date: Date | null;
}

@Component({
  selector: 'app-employee-form-dialog',
  imports: [
    FormField,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './employee-form-dialog.html',
})
export class EmployeeFormDialog {
  private readonly service = inject(EmployeeService);
  private readonly ref = inject(MatDialogRef<EmployeeFormDialog>);
  /** Employee to edit, or null to create a new one. */
  readonly data = inject<Employee | null>(MAT_DIALOG_DATA);

  readonly departments = DEPARTMENTS;
  readonly isEdit = this.data !== null;
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  readonly model = signal<EmployeeFormModel>(
    this.data
      ? {
          first_name: this.data.first_name,
          last_name: this.data.last_name,
          email: this.data.email,
          department: this.data.department,
          role: this.data.role,
          hire_date: moment(this.data.hire_date).toDate(),
        }
      : {
          first_name: '',
          last_name: '',
          email: '',
          department: '',
          role: '',
          hire_date: null,
        },
  );

  readonly employeeForm = form(this.model, (path) => {
    required(path.first_name, { message: 'Required' });
    required(path.last_name, { message: 'Required' });
    required(path.email, { message: 'Required' });
    emailValidator(path.email, { message: 'Enter a valid email' });
    required(path.department, { message: 'Required' });
    required(path.role, { message: 'Required' });
    required(path.hire_date, { message: 'Required' });
  });

  save(): void {
    if (!this.employeeForm().valid()) return;

    this.saving.set(true);
    this.error.set(null);

    const v = this.model();
    const payload: EmployeeCreate = {
      first_name: v.first_name,
      last_name: v.last_name,
      email: v.email,
      department: v.department,
      role: v.role,
      hire_date: moment(v.hire_date).format('YYYY-MM-DD'),
    };

    const request = this.data
      ? this.service.update(this.data.id, payload)
      : this.service.create(payload);

    request.subscribe({
      next: (employee) => {
        this.saving.set(false);
        this.ref.close(employee);
      },
      error: (err) => {
        this.saving.set(false);
        this.error.set(err?.error?.detail ?? 'Could not save the employee. Please try again.');
      },
    });
  }
}