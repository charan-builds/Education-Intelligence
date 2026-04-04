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

  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Tenant ID or Workspace").fill(tenantId);
  await page.getByRole("button", { name: /resend verification email/i }).click();

  const mailpitMessagesResponse = await page.request.get("http://127.0.0.1:8025/api/v1/messages");
  expect(mailpitMessagesResponse.ok()).toBeTruthy();
  const mailpitMessages = await mailpitMessagesResponse.json();
  const verificationMessage = Array.isArray(mailpitMessages?.messages)
    ? mailpitMessages.messages.find((message: { To?: Array<{ Address?: string }> }) =>
        Array.isArray(message.To) && message.To.some((recipient) => recipient.Address === email),
      )
    : null;
  expect(verificationMessage).toBeTruthy();

  const messageId = String(verificationMessage.ID);
  const messageResponse = await page.request.get(`http://127.0.0.1:8025/api/v1/message/${messageId}`);
  expect(messageResponse.ok()).toBeTruthy();
  const messageBody = await messageResponse.json();
  const html = String(messageBody.HTML ?? "");
  const verificationUrlMatch = html.match(/http:\/\/127\.0\.0\.1:3000\/auth\?mode=email-verification[^"'\\s<]+/);
  expect(verificationUrlMatch).toBeTruthy();

  await page.goto(String(verificationUrlMatch?.[0] ?? ""));
  await page.waitForURL(/\/auth\?mode=login/);

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
