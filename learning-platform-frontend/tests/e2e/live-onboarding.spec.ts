import { expect, test } from "@playwright/test";

test("live independent learner onboarding reaches goal selection and starts diagnostic", async ({ page }) => {
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
  const tenantId = new URL(page.url()).searchParams.get("tenant_id") ?? "";
  expect(tenantId).not.toEqual("");

  const verificationResponsePromise = page.waitForResponse((response) => {
    return response.url().includes("/auth/email-verification/request") && response.request().method() === "POST";
  });

  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Tenant ID or Workspace").fill(tenantId);
  await page.getByRole("button", { name: /resend verification email/i }).click();
  const verificationResponse = await verificationResponsePromise;
  expect(verificationResponse.ok()).toBeTruthy();
  const verificationPayload = await verificationResponse.json();
  const verificationToken = String(verificationPayload?.token ?? "");
  expect(verificationToken).not.toEqual("");

  await page.goto(`/auth?mode=email-verification&token=${encodeURIComponent(verificationToken)}&email=${encodeURIComponent(email)}`);
  await page.waitForURL(/\/auth\?mode=login/);

  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: /sign in/i }).last().click();

  await expect(page).toHaveURL(/\/independent-learner\/welcome/);
  await expect(page.getByText(/workspace is almost ready/i)).toBeVisible();

  await page.getByRole("link", { name: /continue setup/i }).click();
  await expect(page).toHaveURL(/\/independent-learner\/onboarding/);
  await expect(page.getByRole("heading", { name: /build your learner profile/i })).toBeVisible();

  const fullNameInput = page.getByPlaceholder("Full name");
  await expect(fullNameInput).toBeVisible();
  await fullNameInput.fill("Independent Learner");
  await expect(fullNameInput).toHaveValue("Independent Learner");
  await page.getByRole("button", { name: /^next$/i }).click();

  const collegeInput = page.getByPlaceholder("College / university");
  const degreeInput = page.getByPlaceholder("Degree");
  const yearInput = page.getByPlaceholder("Year of study");
  await expect(collegeInput).toBeVisible();
  await collegeInput.fill("Independent Learners University");
  await degreeInput.fill("B.Tech");
  await yearInput.fill("4");
  await expect(collegeInput).toHaveValue("Independent Learners University");
  await expect(degreeInput).toHaveValue("B.Tech");
  await expect(yearInput).toHaveValue("4");
  await page.getByRole("button", { name: /^next$/i }).click();

  await page.getByRole("button", { name: /^next$/i }).click();

  await page.locator("select").nth(0).selectOption("beginner");
  await page.locator("select").nth(1).selectOption("1_to_2_hours");
  await page.locator("select").nth(2).selectOption("hands_on");
  await page.locator("select").nth(3).selectOption("3_months");
  const goalNoteInput = page.getByPlaceholder("What are you trying to achieve, and why does it matter right now?");
  await goalNoteInput.fill(
    "I want a strong backend engineering roadmap with clear practice priorities.",
  );
  await expect(goalNoteInput).toHaveValue("I want a strong backend engineering roadmap with clear practice priorities.");
  await page.getByRole("button", { name: /^next$/i }).click();

  await page.getByRole("button", { name: /generate my learning path/i }).click();

  await expect(page).toHaveURL(/\/independent-learner\/goals/);
  await expect(page.getByRole("heading", { name: /choose your learning goal/i })).toBeVisible();

  await page.locator("button").filter({ hasText: "Recommended" }).first().click().catch(async () => {
    await page.locator("button").filter({ hasText: "Roadmap preview" }).first().click();
  });
  await page.getByRole("button", { name: /^continue$/i }).click();

  await expect(page).toHaveURL(/\/independent-learner\/diagnostic/);
  await expect(page.getByRole("heading", { name: /complete your adaptive diagnostic|question 1/i })).toBeVisible();
});
