import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AuthPageClient from "@/components/auth/AuthPageClient";

const replaceMock = vi.fn();
const mockAuthState = {
  isAuthenticated: true,
  isReady: true,
  requiresProfileCompletion: false,
  role: "student",
  login: vi.fn(),
};

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock }),
  useSearchParams: () => new URLSearchParams(window.location.search),
}));

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => mockAuthState,
}));

describe("AuthPageClient", () => {
  beforeEach(() => {
    replaceMock.mockReset();
    mockAuthState.isAuthenticated = true;
    mockAuthState.isReady = true;
    mockAuthState.requiresProfileCompletion = false;
    mockAuthState.role = "student";
  });

  it("redirects authenticated users to the requested canonical next path", async () => {
    window.history.replaceState({}, "", "/auth?mode=login&next=/student/roadmap");
    const client = new QueryClient();

    render(
      <QueryClientProvider client={client}>
        <AuthPageClient initialMode="login" />
      </QueryClientProvider>,
    );

    await waitFor(() => expect(replaceMock).toHaveBeenCalledWith("/student/roadmap"));
  });

  it("does not render a password field for forgot-password mode", () => {
    mockAuthState.isAuthenticated = false;
    window.history.replaceState({}, "", "/auth?mode=forgot-password");
    const client = new QueryClient();

    render(
      <QueryClientProvider client={client}>
        <AuthPageClient initialMode="forgot-password" />
      </QueryClientProvider>,
    );

    expect(screen.queryByLabelText("Password")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Email")).toBeInTheDocument();
    expect(screen.getByLabelText("Tenant ID or Workspace")).toBeInTheDocument();
  });

  it("renders a password field for reset-password mode", () => {
    mockAuthState.isAuthenticated = false;
    window.history.replaceState({}, "", "/auth?mode=reset-password&token=demo-token");
    const client = new QueryClient();

    render(
      <QueryClientProvider client={client}>
        <AuthPageClient initialMode="reset-password" />
      </QueryClientProvider>,
    );

    expect(screen.getByLabelText("New password")).toBeInTheDocument();
  });
});
