import { expect, test } from "@playwright/test";

/**
 * E2E smoke flow against a running backend (mock mode) seeded with demo data:
 *   cd backend && .venv/Scripts/python -m uvicorn app.main:app --port 8000
 *   cd backend && .venv/Scripts/python ../scripts/seed.py
 */
test("login with demo account and view dashboard", async ({ page }) => {
  await page.goto("/login");
  await page.getByRole("button", { name: "Use demo credentials" }).click();
  await page.getByRole("button", { name: "Sign in" }).click();

  await expect(page).toHaveURL(/dashboard/);
  await expect(page.getByText("Dashboard")).toBeVisible();
});

test("register a new account", async ({ page }) => {
  await page.goto("/register");
  await page.fill("#name", "E2E Tester");
  await page.fill("#email", `e2e-${Date.now()}@researchcollision.dev`);
  await page.fill("#password", "password123");
  await page.getByRole("button", { name: "Create account" }).click();
  await expect(page).toHaveURL(/dashboard/);
});

test("unauthenticated user is redirected to login", async ({ page }) => {
  await page.goto("/dashboard");
  await expect(page).toHaveURL(/login/);
});
