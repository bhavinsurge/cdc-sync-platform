import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: "http://localhost:3007",
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: "yarn workspace @rivercdc/api start",
      url: "http://127.0.0.1:8007/",
      reuseExistingServer: true,
      timeout: 120000,
      cwd: "../..",
    },
    {
      command: "yarn workspace @rivercdc/web start",
      url: "http://localhost:3007",
      reuseExistingServer: true,
      timeout: 120000,
      cwd: "../..",
    },
  ],
});
