export type UserRole = "super_admin" | "admin" | "teacher" | "mentor" | "student";
export type AssignableUserRole = Exclude<UserRole, "super_admin">;

export type User = {
  id: number;
  tenant_id: number;
  email: string;
  role: UserRole;
  display_name?: string | null;
  avatar_url?: string | null;
  preferences?: Record<string, unknown>;
  mfa_enabled?: boolean;
  email_verified_at?: string | null;
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

export type UpdateUserProfilePayload = {
  display_name?: string | null;
  avatar_url?: string | null;
  preferences?: Record<string, unknown>;
};
