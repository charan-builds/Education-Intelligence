import { expect, test } from "@playwright/test";

const apiUrl = process.env.E2E_API_URL ?? "http://127.0.0.1:8000";
const password = process.env.E2E_PASSWORD ?? "Secret123!";

test("super admin can switch tenant scope and see tenant-specific admin content", async ({ page, request }) => {
  const email = `e2e_super_admin_${Date.now()}@example.com`;

  const registerResponse = await request.post(`${apiUrl}/auth/register`, {
    data: {
      email,
      password,
      tenant_id: 1,
      role: "super_admin",
    },
  });
  expect(registerResponse.ok()).toBeTruthy();

  await page.goto("/auth");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();

  await page.goto("/dashboard/super-admin");
  await expect(page.getByText("Tenant Inspection Scope")).toBeVisible();

  await page.getByLabel("Active Tenant Scope").selectOption("1");
  await expect(page.getByText("Inspection Tenant #1")).toBeVisible();

  await page.goto("/dashboard/admin");
  await expect(page.getByText("tenant #1", { exact: false })).toBeVisible();
  await expect(page.getByText("Linear Algebra")).toBeVisible();
  await expect(page.getByText("Machine Learning")).toBeVisible();

  await page.goto("/dashboard/super-admin");
  await page.getByLabel("Active Tenant Scope").selectOption("2");
  await expect(page.getByText("Inspection Tenant #2")).toBeVisible();

  await page.goto("/dashboard/admin");
  await expect(page.getByText("tenant #2", { exact: false })).toBeVisible();
  await expect(page.getByText("Reading Comprehension")).toBeVisible();
  await expect(page.getByText("Basic Algebra")).toBeVisible();
  await expect(page.getByText("STEM Foundations")).toBeVisible();
  await expect(page.getByText("Linear Algebra")).not.toBeVisible();
});
