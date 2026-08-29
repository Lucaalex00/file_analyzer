const form = document.getElementById("analyze-form");
const fileInput = document.getElementById("file-input");
const dropzone = document.getElementById("dropzone");
const statusEl = document.getElementById("status");
const errorEl = document.getElementById("error-message");
const resultEl = document.getElementById("result");
const previewEl = document.getElementById("report-preview");
const downloadEl = document.getElementById("download-link");
const extractedTextPanel = document.getElementById("extracted-text-panel");
const extractedTextEl = document.getElementById("extracted-text");
const historyListEl = document.getElementById("history-list");
const downloadMarkdownButton = document.getElementById("download-markdown-button");
const languageSelect = document.getElementById("language-select");
const themeToggleButton = document.getElementById("theme-toggle");
const analysisPanel = document.getElementById("analysis-panel");
const analysisContextEl = document.querySelector("[data-role=analysis-context]");
const analysisSummaryEl = document.querySelector("[data-role=analysis-summary]");
const analysisExplanationEl = document.querySelector("[data-role=analysis-explanation]");
const analysisRedFlagsEl = document.querySelector("[data-role=analysis-red-flags]");

const HISTORY_MAX_ENTRIES = 10;
const THEME_STORAGE_KEY = "file-analyzer-theme";

function friendlyErrorMessage(status) {
  const key = { 413: "err413", 415: "err415", 422: "err422", 429: "err429", 502: "err502" }[status];
  return FileAnalyzerI18n.translate(languageSelect.value, key || "errGeneric");
}

let lastExtractedText = "";
let lastAnalyzedFile = null;
let extractionPromise = Promise.resolve();

function escapeHtml(text) {
  return text
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function highlightRedFlags(rawText, redFlags) {
  let html = escapeHtml(rawText);
  (redFlags || []).forEach((flag) => {
    if (!flag.quote) {
      return;
    }
    const escapedQuote = escapeHtml(flag.quote);
    if (!html.includes(escapedQuote)) {
      return;
    }
    const mark = `<mark class="severity-${flag.severity}" title="${escapeHtml(flag.title)}">${escapedQuote}</mark>`;
    html = html.split(escapedQuote).join(mark);
  });
  return html;
}

function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  try {
    localStorage.setItem(THEME_STORAGE_KEY, theme);
  } catch (storageError) {
    // Best-effort only: a private window or blocked storage shouldn't break theming.
  }
}

function initTheme() {
  let stored = null;
  try {
    stored = localStorage.getItem(THEME_STORAGE_KEY);
  } catch (storageError) {
    stored = null;
  }
  const prefersDark = window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches;
  applyTheme(stored || (prefersDark ? "dark" : "light"));
}

themeToggleButton.addEventListener("click", () => {
  const current = document.documentElement.dataset.theme === "dark" ? "dark" : "light";
  applyTheme(current === "dark" ? "light" : "dark");
});

function applyLanguageToUI() {
  FileAnalyzerI18n.applyTranslations(languageSelect.value, document);
  const themeToggleLabel = FileAnalyzerI18n.translate(languageSelect.value, "themeToggle");
  themeToggleButton.title = themeToggleLabel;
  themeToggleButton.setAttribute("aria-label", themeToggleLabel);
}

languageSelect.addEventListener("change", applyLanguageToUI);

async function copyToClipboard(text, button) {
  try {
    await navigator.clipboard.writeText(text);
    const original = button.textContent;
    button.textContent = FileAnalyzerI18n.translate(languageSelect.value, "copiedFeedback");
    setTimeout(() => {
      button.textContent = original;
    }, 1500);
  } catch (clipboardError) {
    // Clipboard access can be denied by the browser; silently no-op.
  }
}

document.querySelector("[data-role=copy-extracted-text]").addEventListener("click", (event) => {
  copyToClipboard(extractedTextEl.textContent, event.currentTarget);
});

document.querySelector("[data-role=copy-analysis]").addEventListener("click", (event) => {
  const parts = [
    analysisContextEl.textContent,
    analysisSummaryEl.textContent,
    analysisExplanationEl.textContent,
    ...Array.from(analysisRedFlagsEl.querySelectorAll("li")).map((li) => li.textContent),
  ];
  copyToClipboard(parts.filter(Boolean).join("\n\n"), event.currentTarget);
});

function resetOutcome() {
  errorEl.hidden = true;
  errorEl.textContent = "";
  resultEl.hidden = true;
  analysisPanel.hidden = true;
  downloadMarkdownButton.hidden = true;
  lastAnalyzedFile = null;
  if (previewEl.src) {
    URL.revokeObjectURL(previewEl.src);
    previewEl.src = "";
  }
}

function renderAnalysis(analysis) {
  analysisContextEl.textContent = analysis.detected_context;
  analysisSummaryEl.textContent = analysis.summary;
  analysisExplanationEl.textContent = analysis.plain_explanation;
  analysisRedFlagsEl.innerHTML = "";

  const redFlags = analysis.red_flags || [];
  if (redFlags.length === 0) {
    const li = document.createElement("li");
    li.textContent = FileAnalyzerI18n.translate(languageSelect.value, "noRedFlags");
    analysisRedFlagsEl.appendChild(li);
  } else {
    redFlags.forEach((flag) => {
      const li = document.createElement("li");
      li.className = `severity-${flag.severity}`;
      li.textContent = `${flag.title} (${flag.severity}): ${flag.description}`;
      analysisRedFlagsEl.appendChild(li);
    });
  }

  analysisPanel.hidden = false;
}

async function downloadMarkdownReport(file) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", languageSelect.value);

  const response = await fetch("/analyze/markdown", { method: "POST", body: formData });
  if (!response.ok) {
    showError(friendlyErrorMessage(response.status));
    return;
  }

  const markdown = await response.text();
  const disposition = response.headers.get("content-disposition") || "";
  const match = /filename="([^"]+)"/.exec(disposition);
  const filename = match ? match[1] : FileAnalyzerFilename.reportFilenameFor(file.name).replace(/\.pdf$/, ".md");

  const blob = new Blob([markdown], { type: "text/markdown" });
  const objectUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = objectUrl;
  link.setAttribute("download", filename);
  link.click();
  URL.revokeObjectURL(objectUrl);
}

downloadMarkdownButton.addEventListener("click", () => {
  if (lastAnalyzedFile) {
    downloadMarkdownReport(lastAnalyzedFile);
  }
});

function resetExtractedText() {
  extractedTextPanel.hidden = true;
  extractedTextEl.textContent = "";
  lastExtractedText = "";
}

async function showExtractedTextPreview(file) {
  resetExtractedText();

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/extract", { method: "POST", body: formData });
    if (!response.ok) {
      showError(friendlyErrorMessage(response.status));
      return;
    }

    const { text } = await response.json();
    lastExtractedText = text;
    extractedTextEl.textContent = text;
    extractedTextPanel.hidden = false;
  } catch (networkError) {
    showError(FileAnalyzerI18n.translate(languageSelect.value, "errNetwork"));
  }
}

function showError(message) {
  errorEl.hidden = false;
  errorEl.textContent = message;
}

function showResult(blob, filename) {
  const objectUrl = URL.createObjectURL(blob);
  previewEl.src = objectUrl;
  downloadEl.href = objectUrl;
  downloadEl.setAttribute("download", filename);
  resultEl.hidden = false;
}

function blobToBase64(blob) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result.split(",")[1]);
    reader.onerror = () => reject(reader.error);
    reader.readAsDataURL(blob);
  });
}

function base64ToBlob(base64, mimeType) {
  const byteChars = atob(base64);
  const byteNumbers = new Array(byteChars.length);
  for (let i = 0; i < byteChars.length; i++) {
    byteNumbers[i] = byteChars.charCodeAt(i);
  }
  return new Blob([new Uint8Array(byteNumbers)], { type: mimeType });
}

function renderHistory() {
  const history = FileAnalyzerHistory.loadHistory(localStorage);
  historyListEl.innerHTML = "";

  history.forEach((entry) => {
    const item = document.createElement("li");
    item.dataset.role = "history-item";

    const label = document.createElement("span");
    label.textContent = `${new Date(entry.timestamp).toLocaleString("it-IT")} — ${entry.filename}`;
    item.appendChild(label);

    const reopenButton = document.createElement("button");
    reopenButton.type = "button";
    reopenButton.textContent = FileAnalyzerI18n.translate(languageSelect.value, "historyReopen");
    reopenButton.dataset.role = "history-reopen";
    reopenButton.addEventListener("click", () => {
      const blob = base64ToBlob(entry.pdfBase64, "application/pdf");
      showResult(blob, entry.reportFilename);
      // The original File object isn't stored in history, so the Markdown
      // re-export (which needs to re-run the pipeline) isn't available here.
      lastAnalyzedFile = null;
      downloadMarkdownButton.hidden = true;
    });
    item.appendChild(reopenButton);

    historyListEl.appendChild(item);
  });
}

async function addToHistory(file, blob, reportFilename) {
  const pdfBase64 = await blobToBase64(blob);
  FileAnalyzerHistory.saveHistoryEntry(
    localStorage,
    {
      timestamp: new Date().toISOString(),
      filename: file.name,
      reportFilename,
      pdfBase64,
    },
    HISTORY_MAX_ENTRIES,
  );
  renderHistory();
}

function handleFileSelected() {
  const file = fileInput.files[0];
  resetOutcome();
  if (file) {
    extractionPromise = showExtractedTextPreview(file);
  } else {
    resetExtractedText();
  }
}

["dragover", "dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => event.preventDefault());
});

dropzone.addEventListener("dragover", () => {
  dropzone.classList.add("dropzone--active");
});

dropzone.addEventListener("dragleave", () => {
  dropzone.classList.remove("dropzone--active");
});

dropzone.addEventListener("drop", (event) => {
  dropzone.classList.remove("dropzone--active");
  const droppedFiles = event.dataTransfer?.files;
  if (droppedFiles && droppedFiles.length > 0) {
    fileInput.files = droppedFiles;
    handleFileSelected();
  }
});

fileInput.addEventListener("change", handleFileSelected);

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetOutcome();

  const file = fileInput.files[0];
  if (!file) {
    return;
  }

  statusEl.textContent = FileAnalyzerI18n.translate(languageSelect.value, "statusAnalyzing");

  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", languageSelect.value);

  try {
    const response = await fetch("/analyze/review", { method: "POST", body: formData });

    if (!response.ok) {
      showError(friendlyErrorMessage(response.status));
      return;
    }

    const { analysis, pdf_base64: pdfBase64 } = await response.json();
    const blob = base64ToBlob(pdfBase64, "application/pdf");
    const filename = FileAnalyzerFilename.reportFilenameFor(file.name);
    showResult(blob, filename);
    renderAnalysis(analysis);
    await addToHistory(file, blob, filename);
    lastAnalyzedFile = file;
    downloadMarkdownButton.hidden = false;

    await extractionPromise; // ensure /extract has resolved before using its result
    if (lastExtractedText) {
      extractedTextEl.innerHTML = highlightRedFlags(lastExtractedText, analysis.red_flags);
    }
  } catch (networkError) {
    showError(FileAnalyzerI18n.translate(languageSelect.value, "errNetwork"));
  } finally {
    statusEl.textContent = "";
  }
});

initTheme();
applyLanguageToUI();
renderHistory();
