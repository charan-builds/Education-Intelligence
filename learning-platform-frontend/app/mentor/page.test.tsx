import React from "react";
import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import MentorPage from "@/app/mentor/page";

vi.mock("@/components/routing/ClientRouteRedirect", () => ({
  default: ({ fallbackPath }: { fallbackPath: string }) => <div>Redirect:{fallbackPath}</div>,
}));

describe("MentorPage", () => {
  it("redirects the legacy route to the new mentor workspace", () => {
    render(<MentorPage />);
    expect(screen.getByText("Redirect:/mentor/dashboard")).toBeInTheDocument();
  });
});
