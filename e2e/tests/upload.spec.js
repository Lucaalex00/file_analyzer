const { test, expect } = require("@playwright/test");

test("home page shows the upload form", async ({ page }) => {
  await page.goto("/");

  await expect(page.locator("input[type=file]")).toBeAttached();
  await expect(page.getByRole("button", { name: /analizza/i })).toBeVisible();
});

test("uploading an unsupported file type shows a readable error, not raw JSON", async ({ page }) => {
  await page.goto("/");

  await page.setInputFiles("input[type=file]", {
    name: "photo.png",
    mimeType: "image/png",
    buffer: Buffer.from([0x89, 0x50, 0x4e, 0x47]),
  });
  await page.getByRole("button", { name: /analizza/i }).click();

  const errorLocator = page.locator("[data-role=error-message]");
  await expect(errorLocator).toBeVisible();
  await expect(errorLocator).not.toContainText("{");
  await expect(errorLocator).not.toContainText("Traceback");
});

test("selecting a file shows the extracted text preview before submitting", async ({ page }) => {
  await page.goto("/");

  await page.setInputFiles("input[type=file]", {
    name: "memo.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Team, please submit your reports by Friday."),
  });

  const extractedText = page.locator("[data-role=extracted-text]");
  await expect(extractedText).toBeVisible();
  await expect(extractedText).toHaveText("Team, please submit your reports by Friday.");
});

test("successful analysis embeds the returned PDF and offers a download link", async ({ page }) => {
  const fakePdfBase64 = Buffer.from("%PDF-1.4 fake report content").toString("base64");

  await page.route("**/analyze/review", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        analysis: {
          detected_context: "work",
          plain_explanation: "A short memo.",
          summary: "A memo about a deadline.",
          red_flags: [],
        },
        pdf_base64: fakePdfBase64,
      }),
    });
  });

  await page.goto("/");

  await page.setInputFiles("input[type=file]", {
    name: "memo.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Team, please submit your reports by Friday."),
  });
  await page.getByRole("button", { name: /analizza/i }).click();

  await expect(page.locator("embed[data-role=report-preview]")).toBeVisible();

  const downloadLink = page.locator("a[data-role=download-link]");
  await expect(downloadLink).toBeVisible();
  await expect(downloadLink).toHaveAttribute("download", "memo-report.pdf");
});

test("red flags with a matching quote are highlighted in the extracted text", async ({ page }) => {
  const fakePdfBase64 = Buffer.from("%PDF-1.4 fake report content").toString("base64");

  await page.route("**/analyze/review", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        analysis: {
          detected_context: "work",
          plain_explanation: "A short memo.",
          summary: "A memo about a deadline.",
          red_flags: [
            {
              title: "Tight deadline",
              description: "The deadline is very close.",
              severity: "medium",
              quote: "by Friday",
            },
          ],
        },
        pdf_base64: fakePdfBase64,
      }),
    });
  });

  await page.goto("/");

  await page.setInputFiles("input[type=file]", {
    name: "memo.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Team, please submit your reports by Friday."),
  });
  await page.getByRole("button", { name: /analizza/i }).click();

  const highlighted = page.locator("[data-role=extracted-text] mark.severity-medium");
  await expect(highlighted).toBeVisible();
  await expect(highlighted).toHaveText("by Friday");
});

test("the Markdown download button appears after a successful analysis and downloads a .md file", async ({
  page,
}) => {
  const fakePdfBase64 = Buffer.from("%PDF-1.4 fake report content").toString("base64");

  await page.route("**/analyze/review", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        analysis: {
          detected_context: "work",
          plain_explanation: "A short memo.",
          summary: "A memo about a deadline.",
          red_flags: [],
        },
        pdf_base64: fakePdfBase64,
      }),
    });
  });

  await page.route("**/analyze/markdown", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "text/markdown; charset=utf-8",
      headers: { "content-disposition": 'attachment; filename="memo-report.md"' },
      body: "# Analysis report\n\nA memo about a deadline.",
    });
  });

  await page.goto("/");

  await page.setInputFiles("input[type=file]", {
    name: "memo.txt",
    mimeType: "text/plain",
    buffer: Buffer.from("Team, please submit your reports by Friday."),
  });
  await page.getByRole("button", { name: /analizza/i }).click();

  const markdownButton = page.locator("[data-role=download-markdown-button]");
  await expect(markdownButton).toBeVisible();

  const [download] = await Promise.all([page.waitForEvent("download"), markdownButton.click()]);

  expect(download.suggestedFilename()).toBe("memo-report.md");
});
