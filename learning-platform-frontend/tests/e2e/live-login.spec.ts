import { expect, test } from "@playwright/test";

const tenantId = process.env.E2E_TENANT_ID ?? "2";
const email = process.env.E2E_STUDENT_EMAIL ?? "maya.chen@demo.learnova.ai";
const password = process.env.E2E_STUDENT_PASSWORD ?? "Student123!";

test("live student login reaches the real dashboard", async ({ page }) => {
  await page.goto("/auth?mode=login");

  const emailInput = page.getByLabel("Email");
  const passwordInput = page.getByLabel("Password");
  const tenantInput = page.getByLabel("Tenant ID or Workspace");

  await expect(emailInput).toBeVisible();
  await expect(passwordInput).toBeVisible();
  await expect(tenantInput).toBeVisible();

  await emailInput.fill(email);
  await passwordInput.fill(password);
  await tenantInput.fill(tenantId);

  await expect(emailInput).toHaveValue(email);
  await expect(passwordInput).toHaveValue(password);
  await expect(tenantInput).toHaveValue(tenantId);

  await page.getByRole("button", { name: /sign in/i }).last().click();

  await expect(page).toHaveURL(/\/student\/dashboard/);
  await expect(page.getByText(/Student workspace/i)).toBeVisible();
  await expect(page.getByText(/adaptive learning command center|focus mode: one clear path forward/i)).toBeVisible();
});
