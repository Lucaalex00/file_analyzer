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

test("successful analysis embeds the returned PDF and offers a download link", async ({ page }) => {
  const fakePdfBytes = Buffer.from("%PDF-1.4 fake report content");

  await page.route("**/analyze", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/pdf",
      headers: {
        "content-disposition": 'attachment; filename="memo-report.pdf"',
      },
      body: fakePdfBytes,
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
