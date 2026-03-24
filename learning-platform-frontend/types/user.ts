export type UserRole = "super_admin" | "admin" | "teacher" | "mentor" | "student";
export type AssignableUserRole = Exclude<UserRole, "super_admin">;

export type User = {
  id: number;
  tenant_id: number;
  email: string;
  role: UserRole;
  created_at: string;
};

export type PageMeta = {
  total: number;
  limit: number;
  offset: number;
  next_offset: number | null;
  next_cursor: string | null;
};

export type UserPageResponse = {
  items: User[];
  meta: PageMeta;
};

export type CreateUserPayload = {
  email: string;
  password: string;
  role: AssignableUserRole;
};
