import type { User } from "@/types/user";

export type LoginPayload = {
  email: string;
  password: string;
};

export type AuthResponse = {
  authenticated: boolean;
  token_type: string;
  access_token_expires_in: number;
  refresh_token_expires_in?: number | null;
  user: User;
};
