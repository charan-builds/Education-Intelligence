export type UserRole = "super_admin" | "admin" | "teacher" | "mentor" | "student" | "independent_learner";
export type AssignableUserRole = Exclude<UserRole, "super_admin">;

export type User = {
  id: number;
  tenant_id: number;
  email: string;
  role: UserRole;
  full_name?: string | null;
  display_name?: string | null;
  phone_number?: string | null;
  linkedin_url?: string | null;
  college_name?: string | null;
  avatar_url?: string | null;
  preferences?: Record<string, unknown>;
  mfa_enabled?: boolean;
  is_email_verified?: boolean;
  is_phone_verified?: boolean;
  email_verified_at?: string | null;
  is_profile_completed?: boolean;
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
  full_name?: string | null;
  display_name?: string | null;
  phone_number?: string | null;
  linkedin_url?: string | null;
  college_name?: string | null;
  avatar_url?: string | null;
  preferences?: Record<string, unknown>;
};

export type CompleteUserProfilePayload = {
  full_name: string;
  phone_number: string;
  linkedin_url: string;
  college_name?: string | null;
};
