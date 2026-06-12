import { Component, inject, signal } from '@angular/core';
import { Router } from '@angular/router';
import { email as emailValidator, form, FormField, required } from '@angular/forms/signals';
import { MatButtonModule } from '@angular/material/button';
import { MatCardModule } from '@angular/material/card';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatProgressSpinnerModule } from '@angular/material/progress-spinner';

import { AuthService } from '../../../core/auth/auth.service';

interface LoginModel {
  email: string;
  password: string;
}

@Component({
  selector: 'app-login',
  imports: [
    FormField,
    MatButtonModule,
    MatCardModule,
    MatFormFieldModule,
    MatInputModule,
    MatProgressSpinnerModule,
  ],
  templateUrl: './login.html',
})
export class Login {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly loading = signal(false);
  readonly error = signal<string | null>(null);

  readonly model = signal<LoginModel>({ email: '', password: '' });
  readonly loginForm = form(this.model, (path) => {
    required(path.email, { message: 'Email is required' });
    emailValidator(path.email, { message: 'Enter a valid email address' });
    required(path.password, { message: 'Password is required' });
  });

  submit(): void {
    if (!this.loginForm().valid()) return;

    this.loading.set(true);
    this.error.set(null);
    const { email, password } = this.model();

    this.auth.login(email, password).subscribe({
      next: () => {
        this.loading.set(false);
        this.router.navigate(['/']);
      },
      error: (err) => {
        this.loading.set(false);
        this.error.set(err?.error?.detail ?? 'Login failed. Please check your credentials.');
      },
    });
  }
}
