const test = require("node:test");
const assert = require("node:assert/strict");

const { reportFilenameFor } = require("../../frontend/filename.js");

test("builds a -report.pdf filename from the original stem", () => {
  assert.equal(reportFilenameFor("my report.pdf"), "my_report-report.pdf");
});

test("strips directory components", () => {
  assert.equal(reportFilenameFor("../../etc/passwd.txt"), "passwd-report.pdf");
});

test("falls back to 'report' when the stem is empty", () => {
  assert.equal(reportFilenameFor(".pdf"), "report-report.pdf");
});

test("falls back to 'upload' as the base name when none is given", () => {
  assert.equal(reportFilenameFor(""), "upload-report.pdf");
});
