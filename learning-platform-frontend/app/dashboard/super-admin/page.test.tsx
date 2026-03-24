import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import SuperAdminDashboardPage from "@/app/dashboard/super-admin/page";

vi.mock("@/components/routing/ClientRouteRedirect", () => ({
  default: ({ fallbackPath }: { fallbackPath: string }) => <div>Redirect:{fallbackPath}</div>,
}));

describe("SuperAdminDashboardPage", () => {
  it("redirects the legacy route to the new super-admin workspace", () => {
    render(<SuperAdminDashboardPage />);
    expect(screen.getByText("Redirect:/super-admin/dashboard")).toBeInTheDocument();
  });
});
