import { describe, expect, it } from "vitest";

import {
  getRoleRedirectPath,
  normalizeAccessRole,
  roleHasAccess,
} from "@/utils/roleRedirect";

describe("roleRedirect", () => {
  it("maps roles to the new workspace paths", () => {
    expect(getRoleRedirectPath("student")).toBe("/student/dashboard");
    expect(getRoleRedirectPath("independent_learner")).toBe("/independent-learner/dashboard");
    expect(getRoleRedirectPath("teacher")).toBe("/teacher/dashboard");
    expect(getRoleRedirectPath("mentor")).toBe("/mentor/dashboard");
    expect(getRoleRedirectPath("admin")).toBe("/admin/dashboard");
    expect(getRoleRedirectPath("super_admin")).toBe("/super-admin/dashboard");
  });

  it("falls back to the workspace auth home for missing or unknown roles", () => {
    expect(getRoleRedirectPath(null)).toBe("/auth");
    expect(getRoleRedirectPath("")).toBe("/auth");
    expect(getRoleRedirectPath("unknown")).toBe("/auth");
  });

  it("treats mentor as an explicit first-class role", () => {
    expect(normalizeAccessRole("mentor")).toBe("mentor");
    expect(roleHasAccess("mentor", ["teacher"])).toBe(false);
    expect(roleHasAccess("mentor", ["mentor"])).toBe(true);
    expect(roleHasAccess("mentor", ["student"])).toBe(false);
  });

  it("treats independent learner as a first-class learner workspace", () => {
    expect(normalizeAccessRole("independent-learner")).toBe("independent_learner");
    expect(roleHasAccess("independent_learner", ["independent_learner"])).toBe(true);
    expect(roleHasAccess("independent_learner", ["student"])).toBe(false);
  });
});
