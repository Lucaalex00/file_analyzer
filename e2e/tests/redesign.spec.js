const { test, expect } = require("@playwright/test");

async function mockAnalyzeReview(page, redFlags = []) {
  const fakePdfBase64 = Buffer.from("%PDF-1.4 fake report content").toString("base64");
  await page.route("**/analyze/review", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        analysis: {
          detected_context: "work",
          plain_explanation: "A short memo about a deadline.",
          summary: "A memo reminding the team of a Friday deadline.",
          red_flags: redFlags,
        },
        pdf_base64: fakePdfBase64,
      }),
    });
  });
}

async function analyzeAFile(page) {
  await page.setInputFiles("input[type=file]", {
    name: "memo.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Team, please submit your reports by Friday."),
  });
  await page.getByRole("button", { name: /analizza|analyze/i }).click();
  await expect(page.locator("embed[data-role=report-preview]")).toBeVisible();
}

test("a successful analysis renders the readable analysis panel", async ({ page }) => {
  await mockAnalyzeReview(page, [
    { title: "Tight deadline", description: "The deadline is very close.", severity: "medium", quote: "by Friday" },
  ]);
  await page.goto("/");
  await analyzeAFile(page);

  await expect(page.locator("[data-role=analysis-context]")).toHaveText("work");
  await expect(page.locator("[data-role=analysis-summary]")).toContainText("Friday deadline");
  await expect(page.locator("[data-role=analysis-explanation]")).toContainText("short memo");
  await expect(page.locator("[data-role=analysis-red-flags] li")).toContainText("Tight deadline");
});

test("copy buttons copy the extracted text and the analysis to the clipboard", async ({ page, context, browserName }) => {
  test.skip(browserName !== "chromium", "Clipboard permissions API is Chromium-only in Playwright");
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await mockAnalyzeReview(page);
  await page.goto("/");

  await page.setInputFiles("input[type=file]", {
    name: "memo.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Team, please submit your reports by Friday."),
  });
  await expect(page.locator("[data-role=extracted-text]")).toHaveText("Team, please submit your reports by Friday.");

  await page.locator("[data-role=copy-extracted-text]").click();
  const copiedExtracted = await page.evaluate(() => navigator.clipboard.readText());
  expect(copiedExtracted).toBe("Team, please submit your reports by Friday.");

  await page.getByRole("button", { name: /analizza|analyze/i }).click();
  await expect(page.locator("embed[data-role=report-preview]")).toBeVisible();

  await page.locator("[data-role=copy-analysis]").click();
  const copiedAnalysis = await page.evaluate(() => navigator.clipboard.readText());
  expect(copiedAnalysis).toContain("Friday deadline");
});

test("theme toggle switches the data-theme attribute and persists across reload", async ({ page }) => {
  await page.goto("/");

  const initialTheme = await page.evaluate(() => document.documentElement.dataset.theme);
  await page.locator("[data-role=theme-toggle]").click();
  const toggledTheme = await page.evaluate(() => document.documentElement.dataset.theme);
  expect(toggledTheme).not.toBe(initialTheme);

  await page.reload();
  const persistedTheme = await page.evaluate(() => document.documentElement.dataset.theme);
  expect(persistedTheme).toBe(toggledTheme);
});

test("switching the language translates the static UI labels", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByRole("button", { name: "Analizza" })).toBeVisible();

  await page.locator("[data-role=language-select]").selectOption("en");

  await expect(page.getByRole("button", { name: "Analyze" })).toBeVisible();
});

test("dragging a file over the dropzone shows an active visual state", async ({ page }) => {
  await page.goto("/");
  const dropzone = page.locator("#dropzone");

  await expect(dropzone).not.toHaveClass(/dropzone--active/);

  await dropzone.dispatchEvent("dragover", { dataTransfer: await page.evaluateHandle(() => new DataTransfer()) });
  await expect(dropzone).toHaveClass(/dropzone--active/);

  await dropzone.dispatchEvent("dragleave", { dataTransfer: await page.evaluateHandle(() => new DataTransfer()) });
  await expect(dropzone).not.toHaveClass(/dropzone--active/);
});

test("sections are collapsible accordions", async ({ page }) => {
  await mockAnalyzeReview(page);
  await page.goto("/");
  await analyzeAFile(page);

  const resultSection = page.locator("#result");
  await expect(resultSection).toHaveJSProperty("open", true);

  await resultSection.locator("summary").click();
  await expect(resultSection).toHaveJSProperty("open", false);
});
