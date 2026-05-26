import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: 1,
  timeout: 120000,
  expect: {
    timeout: 15000,
  },

  reporter: process.env.CI ? "github" : "list",

  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],

  webServer: [
    {
      command: "cd ../api && uv run python app/testing/e2e_app.py",
      port: 8001,
      reuseExistingServer: !process.env.CI,
      timeout: 30000,
      env: {
        DATABASE_URL: process.env.DATABASE_URL || "postgresql+asyncpg://postgres:postgres@localhost:5432/influencerflow",
        FERNET_KEY: process.env.FERNET_KEY || "test-fernet-key-do-not-use-in-production-1234567890==",
        JWT_SECRET: "e2e-test-jwt-secret",
        CELERY_TASK_ALWAYS_EAGER: "true",
        RUNNING_TESTS: "true",
      },
    },
    {
      command: "pnpm dev --port 3000",
      port: 3000,
      reuseExistingServer: !process.env.CI,
      timeout: 60000,
      env: {
        API_BASE: "http://localhost:8001",
      },
    },
  ],
});
