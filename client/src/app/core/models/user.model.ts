export type AccessRights = 'admin' | 'human_resources' | 'employee';

export interface CurrentUser {
  id: number;
  access_rights: AccessRights;
  employee_id: number | null;
  first_name: string | null;
  last_name: string | null;
}
