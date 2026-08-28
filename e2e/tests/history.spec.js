const { test, expect } = require("@playwright/test");

async function mockAnalyze(page) {
  await page.route("**/analyze", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/pdf",
      headers: {
        "content-disposition": 'attachment; filename="memo-report.pdf"',
      },
      body: Buffer.from("%PDF-1.4 fake report content"),
    });
  });
}

async function analyzeAFile(page) {
  await page.setInputFiles("input[type=file]", {
    name: "memo.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Team, please submit your reports by Friday."),
  });
  await page.getByRole("button", { name: /analizza/i }).click();
  await expect(page.locator("embed[data-role=report-preview]")).toBeVisible();
}

test("a successful analysis is added to the local history", async ({ page }) => {
  await mockAnalyze(page);
  await page.goto("/");

  await analyzeAFile(page);

  const historyItems = page.locator("[data-role=history-item]");
  await expect(historyItems).toHaveCount(1);
  await expect(historyItems.first()).toContainText("memo.txt");
});

test("history persists across a page reload", async ({ page }) => {
  await mockAnalyze(page);
  await page.goto("/");
  await analyzeAFile(page);

  await page.reload();

  await expect(page.locator("[data-role=history-item]")).toHaveCount(1);
});

test("reopening a history entry shows the report preview again", async ({ page }) => {
  await mockAnalyze(page);
  await page.goto("/");
  await analyzeAFile(page);
  await page.reload();

  await page.locator("[data-role=history-reopen]").click();

  await expect(page.locator("embed[data-role=report-preview]")).toBeVisible();
});
