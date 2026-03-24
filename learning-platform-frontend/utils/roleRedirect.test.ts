import { describe, expect, it } from "vitest";

import {
  getRoleRedirectPath,
  normalizeAccessRole,
  roleHasAccess,
} from "@/utils/roleRedirect";

describe("roleRedirect", () => {
  it("maps roles to the new workspace paths", () => {
    expect(getRoleRedirectPath("student")).toBe("/student/dashboard");
    expect(getRoleRedirectPath("teacher")).toBe("/teacher/dashboard");
    expect(getRoleRedirectPath("mentor")).toBe("/mentor/dashboard");
    expect(getRoleRedirectPath("admin")).toBe("/admin/dashboard");
    expect(getRoleRedirectPath("super_admin")).toBe("/super-admin/dashboard");
  });

  it("treats mentor as an explicit first-class role", () => {
    expect(normalizeAccessRole("mentor")).toBe("mentor");
    expect(roleHasAccess("mentor", ["teacher"])).toBe(false);
    expect(roleHasAccess("mentor", ["mentor"])).toBe(true);
    expect(roleHasAccess("mentor", ["student"])).toBe(false);
  });
});
