import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import StudentDashboardPage from "@/app/dashboard/student/page";

vi.mock("@/components/routing/ClientRouteRedirect", () => ({
  default: ({ fallbackPath }: { fallbackPath: string }) => <div>Redirect:{fallbackPath}</div>,
}));

describe("StudentDashboardPage", () => {
  it("redirects the legacy route to the new student workspace", () => {
    render(<StudentDashboardPage />);
    expect(screen.getByText("Redirect:/student/dashboard")).toBeInTheDocument();
  });
});
