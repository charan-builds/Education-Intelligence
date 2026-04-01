import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import AuthPageClient from "@/components/auth/AuthPageClient";

const replaceMock = vi.fn();
const mockAuthState = {
  isAuthenticated: true,
  isReady: true,
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
});
