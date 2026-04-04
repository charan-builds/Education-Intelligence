import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

import StudentMentorPage from "./page";

const mockUseSearchParams = vi.fn();
const mockHistoryQuery = {
  isLoading: false,
  data: [],
};

vi.mock("next/navigation", () => ({
  useSearchParams: () => mockUseSearchParams(),
}));

vi.mock("@/components/providers/ToastProvider", () => ({
  useToast: () => ({ toast: vi.fn() }),
}));

vi.mock("@tanstack/react-query", async () => {
  const actual = await vi.importActual<typeof import("@tanstack/react-query")>("@tanstack/react-query");
  return {
    ...actual,
    useQuery: () => mockHistoryQuery,
    useMutation: () => ({ mutate: vi.fn(), isPending: false }),
    useQueryClient: () => ({ invalidateQueries: vi.fn() }),
  };
});

vi.mock("@/components/layouts/PageHeader", () => ({
  default: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock("@/components/ui/SurfaceCard", () => ({
  default: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}));

vi.mock("@/components/ui/Button", () => ({
  default: (props: React.ButtonHTMLAttributes<HTMLButtonElement>) => <button {...props} />,
}));

vi.mock("@/components/ui/Input", () => ({
  default: (props: React.InputHTMLAttributes<HTMLInputElement>) => <input {...props} />,
}));

vi.mock("@/components/ui/SmartLoadingState", () => ({
  default: ({ title }: { title: string }) => <div>{title}</div>,
}));

vi.mock("@/components/chat/MarkdownMessage", () => ({
  default: ({ content }: { content: string }) => <div>{content}</div>,
}));

describe("StudentMentorPage", () => {
  beforeEach(() => {
    mockUseSearchParams.mockReturnValue(new URLSearchParams(""));
  });

  it("seeds the composer from the prompt query parameter", async () => {
    mockUseSearchParams.mockReturnValue(
      new URLSearchParams("prompt=Help%20me%20understand%20joins"),
    );

    const client = new QueryClient();

    render(
      <QueryClientProvider client={client}>
        <StudentMentorPage />
      </QueryClientProvider>,
    );

    await waitFor(() => {
      expect(
        screen.getByDisplayValue("Help me understand joins"),
      ).toBeInTheDocument();
    });
  });
});
