import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import TeacherDashboardPage from "@/app/dashboard/teacher/page";

vi.mock("@/components/routing/ClientRouteRedirect", () => ({
  default: ({ fallbackPath }: { fallbackPath: string }) => <div>Redirect:{fallbackPath}</div>,
}));

describe("TeacherDashboardPage", () => {
  it("redirects the legacy route to the new teacher workspace", () => {
    render(<TeacherDashboardPage />);
    expect(screen.getByText("Redirect:/teacher/dashboard")).toBeInTheDocument();
  });
});
