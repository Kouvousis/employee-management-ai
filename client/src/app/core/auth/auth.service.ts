import { Injectable, computed, inject, signal } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable, switchMap, tap } from 'rxjs';

import { environment } from '../../../environments/environment';
import { CurrentUser } from '../models/user.model';

const TOKEN_KEY = 'novatech_token';

@Injectable({ providedIn: 'root' })
export class AuthService {
  private readonly http = inject(HttpClient);

  private readonly _token = signal<string | null>(localStorage.getItem(TOKEN_KEY));
  private readonly _user = signal<CurrentUser | null>(null);

  readonly user = this._user.asReadonly();
  readonly isAuthenticated = computed(() => this._token() !== null);
  readonly isHrOrAdmin = computed(() => {
    const role = this._user()?.access_rights;
    return role === 'admin' || role === 'human_resources';
  });
  readonly isAdmin = computed(() => this._user()?.access_rights === 'admin');

  token(): string | null {
    return this._token();
  }

  /** Authenticate, store the JWT, then load the current user's profile. */
  login(email: string, password: string): Observable<CurrentUser> {
    // The backend uses OAuth2PasswordRequestForm: form-encoded, email in `username`.
    const body = new URLSearchParams({ username: email, password });
    return this.http
      .post<{ access_token: string }>(`${environment.apiUrl}/auth/login`, body.toString(), {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      .pipe(
        tap((res) => this.storeToken(res.access_token)),
        switchMap(() => this.loadCurrentUser()),
      );
  }

  loadCurrentUser(): Observable<CurrentUser> {
    return this.http
      .get<CurrentUser>(`${environment.apiUrl}/auth/me`)
      .pipe(tap((user) => this._user.set(user)));
  }

  logout(): void {
    this._token.set(null);
    this._user.set(null);
    localStorage.removeItem(TOKEN_KEY);
  }

  private storeToken(token: string): void {
    this._token.set(token);
    localStorage.setItem(TOKEN_KEY, token);
  }
}