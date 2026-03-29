import { expect, Page, test } from "@playwright/test";

const APP_ORIGIN = "http://127.0.0.1:3000";

function fakeJwt(role: string): string {
  const payload = Buffer.from(JSON.stringify({ role })).toString("base64url");
  return `header.${payload}.signature`;
}

async function setAuthCookies(page: Page, role: string) {
  const token = fakeJwt(role);
  await page.context().addCookies([
    { name: "access_token", value: token, url: "http://127.0.0.1:3000" },
    { name: "refresh_token", value: token, url: "http://127.0.0.1:3000" },
    { name: "access_token", value: token, url: "http://localhost:3000" },
    { name: "refresh_token", value: token, url: "http://localhost:3000" },
  ]);
}

function buildStudentDashboard(stepStatus: "pending" | "in_progress" | "completed") {
  const completedSteps = stepStatus === "completed" ? 1 : 0;
  const inProgressSteps = stepStatus === "in_progress" ? 1 : 0;
  return {
    tenant_id: 1,
    user_id: 1,
    completion_percent: completedSteps === 1 ? 100 : inProgressSteps === 1 ? 50 : 0,
    streak_days: 4,
    focus_score: 81,
    xp: 540,
    roadmap_progress: {
      total_steps: 1,
      completed_steps: completedSteps,
      in_progress_steps: inProgressSteps,
      completion_percent: completedSteps === 1 ? 100 : inProgressSteps === 1 ? 50 : 0,
    },
    learning_velocity: [{ label: "Today", minutes: 42, completed_steps: completedSteps }],
    weak_topic_heatmap: [{ topic_id: 11, topic_name: "Graph Algorithms", score: 58, mastery_delta: 7, confidence: 0.82 }],
    weak_topics: [{ topic_id: 11, topic_name: "Graph Algorithms", score: 58, mastery_delta: 7, confidence: 0.82 }],
    cognitive_model: {
      confusion_level: "low",
      confusion_signals: ["Keeps momentum after feedback"],
      misunderstanding_patterns: ["Occasional traversal mix-ups"],
      teaching_style: "Blend concept explanation with guided practice.",
      adaptive_actions: ["Increase retrieval practice"],
    },
    mentor_suggestions: [
      {
        id: 301,
        title: "Recover graph traversal fluency",
        message: "Spend 20 minutes on BFS and DFS contrast drills.",
        why: "This is the biggest mastery gap in the current roadmap.",
        topic_id: 11,
        is_ai_generated: true,
      },
    ],
    retention: {
      tenant_id: 1,
      user_id: 1,
      average_retention_score: 74,
      due_reviews: [
        {
          topic_id: 11,
          topic_name: "Graph Algorithms",
          score: 58,
          retention_score: 62,
          review_interval_days: 3,
          review_due_at: null,
          is_due: true,
        },
      ],
      upcoming_reviews: [],
      recommended_resources: [
        {
          id: 501,
          topic_id: 11,
          topic_name: "Graph Algorithms",
          title: "Graph traversal review",
          resource_type: "quiz",
          difficulty: "intermediate",
          rating: 4.8,
          url: "https://example.com/resources/graph-traversal-review",
        },
      ],
    },
    skill_graph: [{ topic_id: 11, topic_name: "Graph Algorithms", status: stepStatus, dependencies: [] }],
    gamification: {
      badges: [{ name: "Consistency", description: "Maintained your streak.", awarded_at: "2026-03-28T00:00:00Z" }],
      leaderboard: [{ rank: 3, user_id: 1, name: "Alex", xp: 540, is_current_user: true }],
    },
    recent_activity: [{ event_type: "question_answered", created_at: "2026-03-28T00:00:00Z", topic_id: 11 }],
  };
}

async function mockLearnerJourney(page: Page) {
  let authenticated = false;
  let answered = false;
  let stepStatus: "pending" | "in_progress" | "completed" = "pending";

  const roadmap = {
    id: 41,
    user_id: 1,
    goal_id: 1,
    test_id: 99,
    status: "ready",
    generated_at: "2026-03-28T00:00:00Z",
    steps: [
      {
        id: 401,
        topic_id: 11,
        phase: "Foundations",
        estimated_time_hours: 2,
        difficulty: "easy",
        priority: 1,
        deadline: "2026-04-05T00:00:00Z",
        progress_status: stepStatus,
      },
    ],
  };

  await page.route("**/*", async (route) => {
    const url = route.request().url();
    const method = route.request().method();
    const { pathname } = new URL(url);

    if (pathname === "/users/me") {
      if (!authenticated) {
        await route.fulfill({ status: 401, body: JSON.stringify({ detail: "Unauthorized" }), contentType: "application/json" });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          tenant_id: 1,
          email: "learner@example.com",
          role: "student",
          created_at: "2026-03-28T00:00:00Z",
        }),
      });
      return;
    }

    if (pathname === "/auth/register") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 1,
          tenant_id: 1,
          email: "learner@example.com",
          role: "student",
          created_at: "2026-03-28T00:00:00Z",
        }),
      });
      return;
    }

    if (pathname === "/auth/email-verification/request") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ success: true, detail: "sent", token: "verify-token" }) });
      return;
    }

    if (pathname === "/auth/email-verification") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ success: true, detail: "verified" }) });
      return;
    }

    if (pathname === "/auth/login") {
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
            id: 1,
            tenant_id: 1,
            email: "learner@example.com",
            role: "student",
            created_at: "2026-03-28T00:00:00Z",
          },
        }),
      });
      return;
    }

    if (pathname === "/dashboard/student") {
      roadmap.steps[0].progress_status = stepStatus;
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(buildStudentDashboard(stepStatus)) });
      return;
    }

    if (pathname === "/goals") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [{ id: 1, name: "Backend Engineering", description: "Master API, data, and async systems." }],
          meta: { total: 1, limit: 20, offset: 0, next_offset: null, next_cursor: null },
        }),
      });
      return;
    }

    if (pathname === "/diagnostic/start") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: 99, user_id: 1, goal_id: 1, started_at: "2026-03-28T00:00:00Z", completed_at: null, answered_count: 0 }),
      });
      return;
    }

    if (pathname === "/diagnostic/99") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          id: 99,
          user_id: 1,
          goal_id: 1,
          started_at: "2026-03-28T00:00:00Z",
          completed_at: answered ? "2026-03-28T00:10:00Z" : null,
          answered_count: answered ? 1 : 0,
        }),
      });
      return;
    }

    if (pathname === "/diagnostic/next/99") {
      if (answered) {
        await route.fulfill({ status: 200, contentType: "application/json", body: "null" });
        return;
      }
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          test_id: 99,
          id: 701,
          topic_id: 11,
          difficulty: 1,
          difficulty_label: "easy",
          question_type: "multiple_choice",
          question_text: "Which traversal uses a queue?",
          answer_options: ["Breadth-first search", "Depth-first search"],
        }),
      });
      return;
    }

    if (pathname === "/diagnostic/answer") {
      answered = true;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ test_id: 99, question_id: 701, answered_count: 1, completed_at: null }),
      });
      return;
    }

    if (pathname === "/diagnostic/submit") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({ id: 99, user_id: 1, goal_id: 1, started_at: "2026-03-28T00:00:00Z", completed_at: "2026-03-28T00:10:00Z" }),
      });
      return;
    }

    if (pathname === "/diagnostic/result") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          test_id: 99,
          topic_scores: { 11: 58, 12: 74 },
          roadmap,
        }),
      });
      return;
    }

    if (pathname === "/roadmap/1") {
      roadmap.steps[0].progress_status = stepStatus;
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [roadmap],
          meta: { total: 1, limit: 20, offset: 0, next_offset: null, next_cursor: null },
        }),
      });
      return;
    }

    if (pathname === "/roadmap/steps/401" && method === "PATCH") {
      const payload = route.request().postDataJSON() as { progress_status: "pending" | "in_progress" | "completed" };
      stepStatus = payload.progress_status;
      roadmap.steps[0].progress_status = stepStatus;
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(roadmap.steps[0]) });
      return;
    }

    if (pathname === "/topics") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          items: [{ id: 11, name: "Graph Algorithms", description: "Traversal and shortest path", tenant_id: 1 }],
          meta: { total: 1, limit: 20, offset: 0, next_offset: null, next_cursor: null },
        }),
      });
      return;
    }

    if (pathname === "/files/upload-request") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          asset_id: 601,
          object_key: "tenant/1/resume.pdf",
          upload_url: "https://upload.example/resume.pdf",
          upload_method: "PUT",
          upload_headers: { "Content-Type": "application/pdf" },
          cdn_url: null,
          expires_in_seconds: 900,
          max_bytes: 25000000,
        }),
      });
      return;
    }

    if (url === "https://upload.example/resume.pdf") {
      await route.fulfill({ status: 200, body: "" });
      return;
    }

    if (pathname === "/files/finalize") {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          asset_id: 601,
          object_key: "tenant/1/resume.pdf",
          cdn_url: null,
          size_bytes: 1024,
          metadata: { document_type: "resume" },
        }),
      });
      return;
    }

    if (pathname.startsWith("/mentor/chat/status/")) {
      await route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          request_id: "mentor-request",
          status: "ready",
          reply: "Focus on BFS vs DFS tradeoffs, then practice queue-based traversal.",
        }),
      });
      return;
    }

    if (pathname === "/mentor/chat/ack") {
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "acked" }) });
      return;
    }

    await route.fallback();
  });
}

test("student learner journey stays intact across auth, diagnostic, roadmap, upload, mentor, and progress", async ({ page }) => {
  await mockLearnerJourney(page);

  await page.goto("/auth?mode=register");
  await page.getByLabel("Email").fill("learner@example.com");
  await page.getByLabel("Password").fill("Secret123!");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page.getByText("Account created. Sign in with your new credentials.")).toBeVisible();

  await page.goto("/auth?mode=email-verification");
  await page.getByLabel("Tenant ID or Workspace").fill("1");
  await page.getByLabel("Email").fill("learner@example.com");
  await page.getByRole("button", { name: "Issue verification token" }).click();
  await expect(page.getByText(/Verification token issued|instructions sent/i)).toBeVisible();

  await page.goto("/auth?mode=login");
  await page.getByLabel("Email").fill("learner@example.com");
  await page.getByLabel("Password").fill("Secret123!");
  await page.getByLabel("Tenant ID or Workspace").fill("1");
  await Promise.all([
    setAuthCookies(page, "student"),
    page.getByRole("button", { name: "Sign in" }).last().click(),
  ]);
  await expect(page).toHaveURL(/\/student\/dashboard/);

  await page.goto(`${APP_ORIGIN}/student/goals`);
  await expect(page.getByRole("button", { name: /Backend Engineering/i })).toBeVisible();
  await page.getByRole("button", { name: /Backend Engineering/i }).click();
  await page.getByRole("button", { name: "Start Diagnostic" }).click();
  await expect(page).toHaveURL(/\/student\/diagnostic\?(?:goal_id=1&test_id=99|test_id=99&goal_id=1)/);

  await page.getByRole("button", { name: "Breadth-first search" }).click();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL(/\/student\/diagnostic\/result\?test_id=99/);
  await expect(page.getByRole("heading", { name: "Roadmap generation" })).toBeVisible();

  await page.goto(`${APP_ORIGIN}/student/roadmap`);
  await page.getByRole("button", { name: "Start" }).click();
  await page.getByRole("button", { name: "Complete" }).click();
  await expect(page.getByText(/Mission planner/i)).toBeVisible();

  await page.goto(`${APP_ORIGIN}/student/career`);
  await page.setInputFiles('input[type="file"]', {
    name: "resume.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("resume"),
  });
  await expect(page.getByText(/private resume vault/i)).toBeVisible();
  await expect(page.getByText(/Stored resume\.pdf/i)).toBeVisible();

  await setAuthCookies(page, "mentor");
  await page.goto(`${APP_ORIGIN}/mentor/chat?prompt=Help%20me%20recover%20graph%20algorithms.`);
  await page
    .getByPlaceholder("Ask for guidance on a roadmap step or weak topic")
    .fill("Help me recover graph algorithms.");
  await page.getByRole("button", { name: /Send/i }).click();
  await page.waitForTimeout(4500);
  await expect(page.getByText(/Focus on BFS vs DFS tradeoffs/i)).toBeVisible();

  await setAuthCookies(page, "student");
  await page.goto(`${APP_ORIGIN}/student/progress`);
  await expect(page.getByText(/Understand your momentum/i)).toBeVisible();
  await expect(page.getByText("Graph Algorithms", { exact: true })).toBeVisible();
});
