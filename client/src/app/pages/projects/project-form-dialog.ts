import { Component, inject, signal } from '@angular/core';
import { form, FormField, required } from '@angular/forms/signals';
import { TextFieldModule } from '@angular/cdk/text-field';
import { MAT_DIALOG_DATA, MatDialogModule, MatDialogRef } from '@angular/material/dialog';
import { MatButtonModule } from '@angular/material/button';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatSelectModule } from '@angular/material/select';
import { MatDatepickerModule } from '@angular/material/datepicker';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';
import moment from 'moment';

import { ProjectService } from '../../core/api/project.service';
import { Project, ProjectCreate, ProjectStatus } from '../../core/models';

const STATUSES: { value: ProjectStatus; label: string }[] = [
  { value: 'planning', label: 'Planning' },
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
];

interface ProjectFormModel {
  name: string;
  description: string;
  deadline: Date | null;
  status: ProjectStatus;
}

@Component({
  selector: 'app-project-form-dialog',
  imports: [
    FormField,
    TextFieldModule,
    MatDialogModule,
    MatButtonModule,
    MatFormFieldModule,
    MatInputModule,
    MatSelectModule,
    MatDatepickerModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './project-form-dialog.html',
})
export class ProjectFormDialog {
  private readonly service = inject(ProjectService);
  private readonly ref = inject(MatDialogRef<ProjectFormDialog>);
  /** Project to edit, or null to create a new one. */
  readonly data = inject<Project | null>(MAT_DIALOG_DATA);

  readonly statuses = STATUSES;
  readonly isEdit = this.data !== null;
  readonly saving = signal(false);
  readonly error = signal<string | null>(null);

  readonly model = signal<ProjectFormModel>(
    this.data
      ? {
          name: this.data.name,
          description: this.data.description,
          deadline: moment(this.data.deadline).toDate(),
          status: this.data.status,
        }
      : { name: '', description: '', deadline: null, status: 'planning' },
  );

  readonly projectForm = form(this.model, (path) => {
    required(path.name, { message: 'Required' });
    required(path.description, { message: 'Required' });
    required(path.deadline, { message: 'Required' });
  });

  save(): void {
    if (!this.projectForm().valid()) return;

    this.saving.set(true);
    this.error.set(null);

    const v = this.model();
    const payload: ProjectCreate = {
      name: v.name,
      description: v.description,
      deadline: moment(v.deadline).format('YYYY-MM-DD'),
      status: v.status,
    };

    const request = this.data
      ? this.service.update(this.data.id, payload)
      : this.service.create(payload);

    request.subscribe({
      next: (project) => {
        this.saving.set(false);
        this.ref.close(project);
      },
      error: (err) => {
        this.saving.set(false);
        this.error.set(err?.error?.detail ?? 'Could not save the project. Please try again.');
      },
    });
  }
}