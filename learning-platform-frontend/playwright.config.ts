import { defineConfig } from "@playwright/test";

const frontendPort = Number(process.env.E2E_FRONTEND_PORT ?? "3000");

export default defineConfig({
  testDir: "./tests/e2e",
  timeout: 120_000,
  expect: {
    timeout: 10_000,
  },
  use: {
    baseURL: `http://127.0.0.1:${frontendPort}`,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: `sh -lc "npm run build && npm run start -- --hostname 127.0.0.1 --port ${frontendPort}"`,
    port: frontendPort,
    reuseExistingServer: true,
    timeout: 180_000,
  },
});
