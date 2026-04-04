import { expect, test } from "@playwright/test";

function fakeJwt(role: string): string {
  const payload = Buffer.from(JSON.stringify({ role })).toString("base64url");
  return `header.${payload}.signature`;
}

test("super admin tenant scope is forwarded to admin data requests", async ({ page }) => {
  let authenticated = false;
  const seenTenantHeaders: string[] = [];

  await page.route("**/*", async (route) => {
    const url = route.request().url();

    if (url.includes("/users/me")) {
      if (!authenticated) {
        await route.fulfill({ status: 401, contentType: "application/json", body: JSON.stringify({ detail: "Unauthorized" }) });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 99,
          tenant_id: 1,
          email: "superadmin@platform.learnova.ai",
          role: "super_admin",
          created_at: "2026-03-28T00:00:00Z",
        }),
      });
      return;
    }

    if (url.includes("/auth/login")) {
      authenticated = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          authenticated: true,
          token_type: "cookie",
          access_token_expires_in: 3600,
          refresh_token_expires_in: 86400,
          user: {
            id: 99,
            tenant_id: 1,
            email: "superadmin@platform.learnova.ai",
            role: "super_admin",
            created_at: "2026-03-28T00:00:00Z",
          },
        }),
      });
      return;
    }

    if (
      url.includes("/users?") ||
      url.endsWith("/users") ||
      url.includes("/topics") ||
      url.includes("/questions") ||
      url.includes("/goals") ||
      url.includes("/community/communities") ||
      url.includes("/community/threads") ||
      url.includes("/analytics/overview") ||
      url.includes("/analytics/roadmap-progress") ||
      url.includes("/feature-flags")
    ) {
      const tenantHeader = route.request().headers()["x-tenant-id"];
      if (tenantHeader) {
        seenTenantHeaders.push(tenantHeader);
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(
          url.includes("/analytics/overview")
            ? {
                tenant_id: Number(tenantHeader ?? 1),
                topic_mastery_distribution: { beginner: 1, needs_practice: 2, mastered: 3 },
                diagnostic_completion_rate: 72,
                roadmap_completion_rate: 48,
              }
            : url.includes("/analytics/roadmap-progress")
              ? {
                  tenant_id: Number(tenantHeader ?? 1),
                  student_count: 1,
                  average_completion_percent: 48,
                  average_mastery_percent: 56,
                  learners: [],
                  meta: { total: 0, limit: 20, offset: 0, next_offset: null, next_cursor: null },
                }
              : { items: [], meta: { total: 0, limit: 20, offset: 0, next_offset: null, next_cursor: null } },
        ),
      });
      return;
    }

    await route.fallback();
  });

  await page.goto("/auth");
  await page.getByLabel("Email").fill("superadmin@platform.learnova.ai");
  await page.getByLabel("Password").fill("SuperAdmin123!");
  await page.getByLabel("Tenant ID or Workspace").fill("1");
  await page.getByRole("button", { name: "Sign in" }).last().click();
  const token = fakeJwt("super_admin");
  await page.context().addCookies([
    { name: "access_token", value: token, url: "http://127.0.0.1:3000" },
    { name: "refresh_token", value: token, url: "http://127.0.0.1:3000" },
    { name: "access_token", value: token, url: "http://localhost:3000" },
    { name: "refresh_token", value: token, url: "http://localhost:3000" },
  ]);
  await page.goto("/super-admin/dashboard");
  await expect(page).toHaveURL(/\/super-admin\/dashboard/);

  await page.evaluate(() => {
    window.localStorage.setItem("active_tenant_id", "2");
    window.dispatchEvent(new Event("storage"));
  });

  await page.goto("/super-admin/dashboard");
  await expect(page.getByText(/Track cross-tenant learning performance and platform health/i)).toBeVisible();
  await expect.poll(() => seenTenantHeaders.includes("2")).toBeTruthy();
});
