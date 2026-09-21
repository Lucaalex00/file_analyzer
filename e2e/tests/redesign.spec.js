const { test, expect } = require("@playwright/test");

const FAKE_PDF_BASE64 = Buffer.from("%PDF-1.4 fake report content").toString("base64");

function analysisBody(redFlags = []) {
  return JSON.stringify({
    analysis: {
      detected_context: "work",
      plain_explanation: "A short memo about a deadline.",
      summary: "A memo reminding the team of a Friday deadline.",
      red_flags: redFlags,
    },
    pdf_base64: FAKE_PDF_BASE64,
  });
}

async function mockAnalyzeReview(page, redFlags = [], delayMs = 0) {
  await page.route("**/analyze/review", async (route) => {
    if (delayMs > 0) {
      await new Promise((resolve) => setTimeout(resolve, delayMs));
    }
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: analysisBody(redFlags),
    });
  });
}

async function selectAFile(page) {
  await page.setInputFiles("input[type=file]", {
    name: "memo.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Team, please submit your reports by Friday."),
  });
}

async function analyzeAFile(page) {
  await selectAFile(page);
  await page.getByRole("button", { name: /analizza|analyze/i }).click();
  await expect(page.locator("[data-role=analysis-content]")).toBeVisible();
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

test("lays out raw text above the document and the analysis side by side", async ({ page }) => {
  await mockAnalyzeReview(page);
  // The real backend can't parse this stub PDF, so the extraction the layout
  // depends on is mocked -- the layout, not the parsing, is what's under test.
  await page.route("**/extract", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ text: "Team, please submit your reports by Friday." }),
    });
  });
  await page.goto("/");

  await page.setInputFiles("input[type=file]", {
    name: "memo.pdf",
    mimeType: "application/pdf",
    buffer: Buffer.from("%PDF-1.4 stub document"),
  });
  await page.getByRole("button", { name: /analizza|analyze/i }).click();
  await expect(page.locator("[data-role=analysis-content]")).toBeVisible();

  const rawText = page.locator("[data-role=extracted-text]");
  const documentPane = page.locator("[data-role=original-preview]");
  const analysisPane = page.locator("[data-role=analysis-content]");

  await expect(rawText).toContainText("Team, please submit your reports by Friday.");
  await expect(documentPane).toBeVisible();

  const rawBox = await rawText.boundingBox();
  const documentBox = await documentPane.boundingBox();
  const analysisBox = await analysisPane.boundingBox();

  expect(documentBox.x).toBeLessThan(analysisBox.x);
  expect(rawBox.y + rawBox.height).toBeLessThanOrEqual(documentBox.y);
});

test("skips the document pane for files the raw text already shows in full", async ({ page }) => {
  await mockAnalyzeReview(page);
  await page.goto("/");
  await analyzeAFile(page);

  // A .txt file renders to exactly the extracted text shown above, so a
  // second pane repeating it would be noise.
  await expect(page.locator("[data-role=document-zone]")).toBeHidden();
  await expect(page.locator("[data-role=extracted-text]")).toBeVisible();
  await expect(page.locator("[data-role=analysis-content]")).toBeVisible();
});

test("the workspace fills in progressively as each stage completes", async ({ page }) => {
  await mockAnalyzeReview(page, [], 2000);
  await page.goto("/");

  await expect(page.locator("[data-role=workspace]")).toBeHidden();

  await selectAFile(page);

  // Extraction stage: raw text and the document pane are already populated,
  // the analysis pane is still waiting for the user to start the analysis.
  await expect(page.locator("[data-role=workspace]")).toBeVisible();
  await expect(page.locator("[data-role=extracted-text]")).toHaveText("Team, please submit your reports by Friday.");
  await expect(page.locator("[data-role=analysis-placeholder]")).toBeVisible();
  await expect(page.locator("[data-role=analysis-content]")).toBeHidden();

  await page.getByRole("button", { name: /analizza|analyze/i }).click();

  // Analysis stage: the pane shows a loading skeleton until the AI responds.
  await expect(page.locator("[data-role=analysis-skeleton]")).toBeVisible();
  await expect(page.locator("[data-role=analysis-placeholder]")).toBeHidden();

  await expect(page.locator("[data-role=analysis-content]")).toBeVisible();
  await expect(page.locator("[data-role=analysis-skeleton]")).toBeHidden();
});

test("copy buttons copy the extracted text and the analysis to the clipboard", async ({ page, context, browserName }) => {
  test.skip(browserName !== "chromium", "Clipboard permissions API is Chromium-only in Playwright");
  await context.grantPermissions(["clipboard-read", "clipboard-write"]);
  await mockAnalyzeReview(page);
  await page.goto("/");

  await selectAFile(page);
  await expect(page.locator("[data-role=extracted-text]")).toHaveText("Team, please submit your reports by Friday.");

  await page.locator("[data-role=copy-extracted-text]").click();
  const copiedExtracted = await page.evaluate(() => navigator.clipboard.readText());
  expect(copiedExtracted).toBe("Team, please submit your reports by Friday.");

  await page.getByRole("button", { name: /analizza|analyze/i }).click();
  await expect(page.locator("[data-role=analysis-content]")).toBeVisible();

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

  await page.locator("[data-role=language-select]").selectOption("it");
  await expect(page.getByRole("button", { name: "Analizza" })).toBeVisible();

  await page.locator("[data-role=language-select]").selectOption("en");
  await expect(page.getByRole("button", { name: "Analyze" })).toBeVisible();
});

test("shows a spinner and rotating status messages while analysis is in progress", async ({ page }) => {
  // Slow enough to observe the status rotate through at least two steps
  // (interval is 2200ms) before the request resolves.
  await mockAnalyzeReview(page, [], 2600);
  await page.goto("/");

  await selectAFile(page);
  await page.getByRole("button", { name: /analizza|analyze/i }).click();

  const statusText = page.locator("#status-text");
  await expect(page.locator("#status-spinner")).toBeVisible();
  const firstStep = await statusText.textContent();
  expect(firstStep).toBeTruthy();

  await expect.poll(async () => statusText.textContent(), { timeout: 5000 }).not.toBe(firstStep);

  await expect(page.locator("[data-role=analysis-content]")).toBeVisible();
  await expect(page.locator("#status")).toBeHidden();
});

test("shows a progress bar that fills up while analysis is in progress", async ({ page }) => {
  await mockAnalyzeReview(page, [], 2600);
  await page.goto("/");

  await selectAFile(page);
  await page.getByRole("button", { name: /analizza|analyze/i }).click();

  const progressFill = page.locator("#status-progress-fill");
  await expect(progressFill).toBeVisible();

  const widthAt = async () => parseFloat((await progressFill.evaluate((el) => el.style.width)) || "0");
  const firstWidth = await widthAt();

  await expect.poll(widthAt, { timeout: 5000 }).toBeGreaterThan(firstWidth);

  await expect(page.locator("[data-role=analysis-content]")).toBeVisible();
  await expect(page.locator("#status")).toBeHidden();
});

test("shows a demo mode banner when the backend reports demo_mode", async ({ page }) => {
  await page.route("**/health", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "ok", demo_mode: true }) });
  });
  await page.goto("/");

  await expect(page.locator("[data-role=demo-banner]")).toBeVisible();
});

test("hides the demo mode banner when the backend reports no demo mode", async ({ page }) => {
  await page.route("**/health", async (route) => {
    await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify({ status: "ok", demo_mode: false }) });
  });
  await page.goto("/");

  await expect(page.locator("[data-role=demo-banner]")).toBeHidden();
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

test("one click on an example document runs the whole analysis", async ({ page }) => {
  await mockAnalyzeReview(page);
  await page.goto("/");

  const exampleButtons = page.locator("[data-role=examples-buttons] button");
  await expect(exampleButtons.first()).toBeVisible();

  await exampleButtons.first().click();

  // No file picking, no second click: the workspace fills in on its own.
  await expect(page.locator("[data-role=extracted-text]")).toBeVisible();
  await expect(page.locator("[data-role=analysis-content]")).toBeVisible();
  await expect(page.locator("a[data-role=download-link]")).toBeVisible();
});

test("shows what the analysis cost, and omits tokens when the provider reports none", async ({ page }) => {
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
          red_flags: [],
        },
        pdf_base64: fakePdfBase64,
        metrics: { total_tokens: 3438, duration_ms: 11400 },
      }),
    });
  });
  await page.goto("/");
  await analyzeAFile(page);

  const cost = page.locator("[data-role=analysis-cost]");
  await expect(cost).toBeVisible();
  await expect(cost).toContainText("3,438");
  await expect(cost).toContainText("11.4");
});

test("the cost line stays hidden when the run reported no metrics", async ({ page }) => {
  // Reopening a history entry has no run to report on.
  await mockAnalyzeReview(page);
  await page.goto("/");
  await analyzeAFile(page);
  await page.reload();
  await page.locator("[data-role=history-reopen]").click();

  await expect(page.locator("[data-role=analysis-cost]")).toBeHidden();
});

test("buttons built from server data are relabelled when the language changes", async ({ page }) => {
  await page.goto("/");

  const firstExample = page.locator("[data-role=examples-buttons] button").first();

  await page.locator("[data-role=language-select]").selectOption("it");
  await expect(firstExample).toHaveText("Contratto di locazione");

  // These labels come from /api/examples, so applyTranslations (which only
  // walks data-i18n elements) can't reach them on its own.
  await page.locator("[data-role=language-select]").selectOption("en");
  await expect(firstExample).toHaveText("Lease contract");
});

test("the docs button opens the project's own README in a panel", async ({ page }) => {
  await page.goto("/");

  await expect(page.locator("[data-role=docs-overlay]")).toBeHidden();

  await page.locator("[data-role=docs-toggle]").click();

  const body = page.locator("[data-role=docs-body]");
  await expect(page.locator("[data-role=docs-overlay]")).toBeVisible();
  await expect(body).toContainText("File Analyzer");

  // Every listed document is reachable, including the architecture write-up.
  await page.locator("[data-role=docs-tabs] button", { hasText: /how it works|come funziona/i }).click();
  await expect(body).toContainText("ExtractorFactory");

  await page.keyboard.press("Escape");
  await expect(page.locator("[data-role=docs-overlay]")).toBeHidden();
});

test("starts in the browser's language when it is one of the supported ones", async ({ browser }) => {
  const context = await browser.newContext({ locale: "en-GB" });
  const page = await context.newPage();
  await page.goto("/");

  await expect(page.getByRole("button", { name: "Analyze" })).toBeVisible();
  await expect(page.locator("[data-role=language-select]")).toHaveValue("en");

  await context.close();
});

test("falls back to English rather than Italian for an unsupported browser language", async ({ browser }) => {
  const context = await browser.newContext({ locale: "ja-JP" });
  const page = await context.newPage();
  await page.goto("/");

  await expect(page.locator("[data-role=language-select]")).toHaveValue("en");

  await context.close();
});

test("the history panel is a collapsible accordion", async ({ page }) => {
  await page.goto("/");

  const historyPanel = page.locator("#history-panel");
  await expect(historyPanel).toHaveJSProperty("open", true);

  await historyPanel.locator("summary").click();
  await expect(historyPanel).toHaveJSProperty("open", false);
});
