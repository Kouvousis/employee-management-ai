import {
  ApplicationConfig,
  inject,
  provideAppInitializer,
  provideBrowserGlobalErrorListeners,
} from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withFetch, withInterceptors } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

import { routes } from './app.routes';
import { authInterceptor } from './core/auth/auth.interceptor';
import { AuthService } from './core/auth/auth.service';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withFetch(), withInterceptors([authInterceptor])),
    // If a token is already stored, hydrate the current user before the first
    // route resolves so role guards have access_rights available.
    provideAppInitializer(() => {
      const auth = inject(AuthService);
      if (!auth.token()) return;
      return firstValueFrom(auth.loadCurrentUser()).catch(() => auth.logout());
    }),
  ],
};