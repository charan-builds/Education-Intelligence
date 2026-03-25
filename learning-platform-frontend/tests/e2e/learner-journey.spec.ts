import { expect, test } from "@playwright/test";

const apiUrl = process.env.E2E_API_URL ?? "http://127.0.0.1:8000";
const tenantId = Number(process.env.E2E_TENANT_ID ?? "1");
const goalId = Number(process.env.E2E_GOAL_ID ?? "1");
const password = process.env.E2E_PASSWORD ?? "Secret123!";

test("student learner journey from login to roadmap progress", async ({ page, request }) => {
  const email = `e2e_student_${Date.now()}@example.com`;

  const registerResponse = await request.post(`${apiUrl}/auth/register`, {
    data: {
      email,
      password,
      tenant_id: tenantId,
      role: "student",
    },
  });
  expect(registerResponse.ok()).toBeTruthy();

  await page.goto("/auth");
  await page.getByLabel("Email").fill(email);
  await page.getByLabel("Password").fill(password);
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/\/student\/dashboard/);
  await page.goto("/student/goals");
  await expect(page.getByText("Available Goals")).toBeVisible();

  const goalCards = page.locator("section button");
  if ((await goalCards.count()) === 0) {
    test.skip(true, "No goals available for E2E flow");
  }
  await goalCards.first().click();
  await page.getByRole("button", { name: "Start Diagnostic" }).click();

  await expect(page).toHaveURL(/\/student\/diagnostic/);

  for (let index = 0; index < 5; index += 1) {
    const radioOptions = page.locator('input[type="radio"]');
    if (await radioOptions.count()) {
      await radioOptions.first().check();
    } else if (await page.getByPlaceholder("Type your answer here").count()) {
      await page.getByPlaceholder("Type your answer here").fill("Sample answer");
    } else {
      break;
    }

    await page.getByRole("button", { name: /Continue|Submitting|Loading/ }).click();
    if (/\/student\/diagnostic\/result/.test(page.url())) {
      break;
    }
  }

  await expect(page).toHaveURL(/\/student\/diagnostic\/result/);
  const resultUrl = new URL(page.url());
  const testId = Number(resultUrl.searchParams.get("test_id"));
  expect(testId).toBeGreaterThan(0);

  const loginResponse = await request.post(`${apiUrl}/auth/login`, {
    data: { email, password },
  });
  expect(loginResponse.ok()).toBeTruthy();
  const loginPayload = (await loginResponse.json()) as { access_token: string };

  const roadmapResponse = await request.post(`${apiUrl}/roadmap/generate`, {
    headers: {
      Authorization: `Bearer ${loginPayload.access_token}`,
    },
    data: {
      goal_id: goalId,
      test_id: testId,
    },
  });
  expect(roadmapResponse.ok()).toBeTruthy();

  await page.goto("/student/roadmap");
  await expect(page.getByText("Learning Roadmap")).toBeVisible();

  const actionButton = page.getByRole("button", { name: /Start Topic|Mark Complete|Reopen/ }).first();
  await expect(actionButton).toBeVisible();
  await actionButton.click();

  await expect(page.getByText("Roadmap progress updated successfully.")).toBeVisible();
});
