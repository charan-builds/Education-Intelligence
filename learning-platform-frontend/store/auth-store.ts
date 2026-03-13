"use client";

import { jwtDecode } from "jwt-decode";

type JwtPayload = {
  sub?: string;
  exp?: number;
  tenant_id?: number;
  role?: string;
};

export function saveAccessToken(token: string): void {
  localStorage.setItem("access_token", token);
}

export function clearAccessToken(): void {
  localStorage.removeItem("access_token");
}

export function getDecodedToken(): JwtPayload | null {
  const token = localStorage.getItem("access_token");
  if (!token) {
    return null;
  }

  try {
    return jwtDecode<JwtPayload>(token);
  } catch {
    return null;
  }
}
