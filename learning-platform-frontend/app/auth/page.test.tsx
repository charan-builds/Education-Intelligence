import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import AuthPage from "@/app/auth/page";

const replaceMock = vi.fn();
const loginMock = vi.fn().mockResolvedValue({ role: "student" });

vi.mock("next/navigation", () => ({
  useRouter: () => ({ replace: replaceMock }),
}));

vi.mock("@/hooks/useAuth", () => ({
  useAuth: () => ({
    isAuthenticated: false,
    isReady: true,
    role: null,
    login: loginMock,
  }),
}));

describe("AuthPage", () => {
  it("redirects to the requested next path after login", async () => {
    window.history.replaceState({}, "", "/auth?next=/student/roadmap");
    const client = new QueryClient();

    render(
      <QueryClientProvider client={client}>
        <AuthPage />
      </QueryClientProvider>,
    );

    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));

    await waitFor(() => expect(loginMock).toHaveBeenCalled());
    await waitFor(() => expect(replaceMock).toHaveBeenCalledWith("/student/roadmap"));
  });
});
