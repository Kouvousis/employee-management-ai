import { Component, inject } from '@angular/core';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MatListModule } from '@angular/material/list';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatToolbarModule } from '@angular/material/toolbar';
import { MatTooltipModule } from '@angular/material/tooltip';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-shell',
  imports: [
    RouterOutlet,
    RouterLink,
    RouterLinkActive,
    MatButtonModule,
    MatIconModule,
    MatListModule,
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
