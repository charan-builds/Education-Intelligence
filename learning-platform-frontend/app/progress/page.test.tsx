import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import ProgressPage from "@/app/progress/page";

vi.mock("@/components/routing/ClientRouteRedirect", () => ({
  default: ({ fallbackPath }: { fallbackPath: string }) => <div>Redirect:{fallbackPath}</div>,
}));

describe("ProgressPage", () => {
  it("redirects the legacy route to the new student progress workspace", () => {
    render(<ProgressPage />);
    expect(screen.getByText("Redirect:/student/progress")).toBeInTheDocument();
  });
});
