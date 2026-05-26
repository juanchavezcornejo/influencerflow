import type { Page } from "@playwright/test";

const TEST_USER = {
  email: "e2e@test.com",
  password: "e2e-test-password",
};

/**
 * Log in via the UI. After login, the cookie is set and we can navigate.
 * Does NOT wait for /dashboard URL since server-side redirect may occur.
 */
export async function login(page: Page): Promise<void> {
  await seedTestUser();
  await page.goto("/login");
  await page.fill('input[id="email"]', TEST_USER.email);
  await page.fill('input[id="password"]', TEST_USER.password);
  await page.click('button[type="submit"]');

  // Wait for login response and cookie propagation
  await page.waitForTimeout(2000);

  // Navigate to dashboard explicitly (sends cookie with this request)
  await page.goto("/dashboard");
  await page.waitForTimeout(1000);
}

async function seedTestUser(): Promise<void> {
  const apiBase = process.env.API_BASE || "http://localhost:8001";
  try {
    const res = await fetch(`${apiBase}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(TEST_USER),
    });
    if (res.ok) return;
  } catch {
    void 0;
  }
}
