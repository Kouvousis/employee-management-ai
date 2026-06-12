import { Component, inject } from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import {
  NavigationCancel,
  NavigationEnd,
  NavigationError,
  NavigationSkipped,
  NavigationStart,
  Router,
  RouterLink,
  RouterLinkActive,
  RouterOutlet,
} from '@angular/router';
import { filter, map } from 'rxjs';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatProgressBarModule } from '@angular/material/progress-bar';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-side-menu',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatButtonModule,
    MatIconModule,
    MatListModule,
    MatProgressBarModule,
    MatSidenavModule,
    MatToolbarModule,
    MatTooltipModule,
  ],
  templateUrl: './side-menu.component.html',
})
export class SideMenu {
  private readonly auth = inject(AuthService);
  private readonly router = inject(Router);

  readonly user = this.auth.user;
  readonly isHrOrAdmin = this.auth.isHrOrAdmin;

  // True while a route (including its lazy-loaded chunk) is navigating.
  readonly navigating = toSignal(
    this.router.events.pipe(
      filter(
        (e) =>
          e instanceof NavigationStart ||
          e instanceof NavigationEnd ||
          e instanceof NavigationCancel ||
          e instanceof NavigationError ||
          e instanceof NavigationSkipped,
      ),
      map((e) => e instanceof NavigationStart),
    ),
    { initialValue: false },
  );

  displayName(): string {
    const u = this.user();
    if (u?.first_name) {
      return `${u.first_name} ${u.last_name ?? ''}`.trim();
    }
    return u?.access_rights === 'admin' ? 'Administrator' : 'User';
  }

  logout(): void {
    this.auth.logout();
    this.router.navigate(['/login']);
  }
}
