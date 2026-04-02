import { expect, test } from "@playwright/test";

const tenantId = "1";

test("live onboarding completes register, verify email, login, and required profile completion", async ({ page }) => {
  const nonce = `${Date.now()}`;
  const email = `independent.${nonce}@example.com`;
  const password = "Stronger123!";

  await page.goto("/auth?mode=register");

  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  const registerResponsePromise = page.waitForResponse((response) => {
    return response.url().includes("/auth/register") && response.request().method() === "POST";
  });
  await page.getByRole("button", { name: /create account/i }).click();
  const registerResponse = await registerResponsePromise;
  expect(registerResponse.ok()).toBeTruthy();
  await page.waitForURL(/\/auth\?mode=email-verification/);

  const verificationResponsePromise = page.waitForResponse((response) => {
    return response.url().includes("/auth/email-verification/request") && response.request().method() === "POST";
  });

  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Tenant ID or Workspace").fill(tenantId);
  await page.getByRole("button", { name: /issue verification token/i }).click();

  const verificationResponse = await verificationResponsePromise;
  expect(verificationResponse.ok()).toBeTruthy();
  const verificationPayload = await verificationResponse.json();
  const verificationToken = String(verificationPayload.token ?? "");
  expect(verificationToken).toBeTruthy();

  await page.goto(`/auth?mode=email-verification&token=${encodeURIComponent(verificationToken)}`);
  await page.locator("form").getByRole("button", { name: /verify email/i }).click();

  await expect(page.getByText(/email verified/i)).toBeVisible();

  await page.goto("/auth?mode=login");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByLabel("Tenant ID or Workspace").fill(tenantId);
  await page.getByRole("button", { name: /sign in/i }).last().click();

  await expect(page).toHaveURL(/\/student\/profile/);
  await expect(page.getByText(/complete your profile/i)).toBeVisible();

  await page.getByPlaceholder("Full name").first().fill("Independent Learner");
  await page.getByPlaceholder("+14155550123").fill("+14155550123");
  await page.getByPlaceholder("https://www.linkedin.com/in/your-profile/").fill("https://www.linkedin.com/in/independent-learner/");
  await page.getByPlaceholder("College or institution (optional)").fill("Independent Learners");
  await page.getByRole("button", { name: /^complete profile$/i }).click();

  await expect(page).toHaveURL(/\/student\/dashboard/);
  await expect(page.getByRole("heading", { name: /an adaptive learning command center/i })).toBeVisible();
});
