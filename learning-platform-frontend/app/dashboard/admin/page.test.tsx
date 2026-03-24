import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import AdminDashboardPage from "@/app/dashboard/admin/page";

vi.mock("@/components/routing/ClientRouteRedirect", () => ({
  default: ({ fallbackPath }: { fallbackPath: string }) => <div>Redirect:{fallbackPath}</div>,
}));

describe("AdminDashboardPage", () => {
  it("redirects the legacy route to the new admin workspace", () => {
    render(<AdminDashboardPage />);
    expect(screen.getByText("Redirect:/admin/dashboard")).toBeInTheDocument();
  });
});
