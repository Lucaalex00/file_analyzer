const test = require("node:test");
const assert = require("node:assert/strict");

const { translate, applyTranslations } = require("../../frontend/i18n.js");

test("translate returns the string for a known language and key", () => {
  assert.equal(translate("en", "analyzeButton"), "Analyze");
  assert.equal(translate("it", "analyzeButton"), "Analizza");
});

test("translate falls back to Italian when the language is unknown", () => {
  assert.equal(translate("xx", "analyzeButton"), translate("it", "analyzeButton"));
});

test("translate falls back to the key itself when the key is unknown", () => {
  assert.equal(translate("it", "nonExistentKey"), "nonExistentKey");
});

test("applyTranslations sets textContent on every element with data-i18n", () => {
  const elements = [
    { dataset: { i18n: "analyzeButton" }, textContent: "" },
    { dataset: { i18n: "downloadPdf" }, textContent: "" },
  ];
  const root = {
    querySelectorAll: () => elements,
  };

  applyTranslations("en", root);

  assert.equal(elements[0].textContent, "Analyze");
  assert.equal(elements[1].textContent, "Download PDF");
});
