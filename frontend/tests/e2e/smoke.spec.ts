import { test, expect } from "@playwright/test";

test("home and login smoke", async ({ page }) => {
  await page.goto("/");
  await expect(page.getByText("RiverCDC").first()).toBeVisible();
  await expect(page.getByRole("link", { name: /open console/i })).toBeVisible();

  await page.goto("/login");
  await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
  await page.getByLabel("Email").fill("admin@rivercdc.local");
  await page.getByLabel("Password").fill("Password123!");
  await page.getByRole("button", { name: /sign in/i }).click();
  await expect(page.getByRole("heading", { name: /overview/i })).toBeVisible({
    timeout: 15000,
  });
  await expect(page.getByRole("link", { name: /pipelines/i })).toBeVisible();
});
