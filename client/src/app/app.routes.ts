import { Routes } from '@angular/router';

import { authGuard, hrOrAdminGuard } from './core/auth/auth.guard';

export const routes: Routes = [
  {
    path: 'login',
    loadComponent: () => import('./pages/auth/login/login').then((m) => m.Login),
  },
  {
    path: '',
    loadComponent: () => import('./pages/side-menu/side-menu.component').then((m) => m.SideMenu),
    canActivate: [authGuard],
    children: [
      { path: '', redirectTo: 'employees', pathMatch: 'full' },
      {
        path: 'employees',
        canActivate: [hrOrAdminGuard],
        loadComponent: () => import('./pages/employees/employees').then((m) => m.Employees),
      },
      {
        path: 'projects',
        loadComponent: () => import('./pages/projects/projects').then((m) => m.Projects),
      },
      {
        path: 'tasks',
        loadComponent: () => import('./pages/tasks/tasks').then((m) => m.Tasks),
      },
      {
        path: 'chat',
        loadComponent: () => import('./pages/chat/chat').then((m) => m.Chat),
      },
    ],
  },
  { path: '**', redirectTo: '' },
];