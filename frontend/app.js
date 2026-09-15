const form = document.getElementById("analyze-form");
const fileInput = document.getElementById("file-input");
const dropzone = document.getElementById("dropzone");
const statusEl = document.getElementById("status");
const statusSpinnerEl = document.getElementById("status-spinner");
const statusTextEl = document.getElementById("status-text");
const statusProgressFillEl = document.getElementById("status-progress-fill");
const errorEl = document.getElementById("error-message");
const workspaceEl = document.getElementById("workspace");
const workspaceActionsEl = document.querySelector("[data-role=workspace-actions]");
const previewEl = document.getElementById("report-preview");
const originalPreviewEl = document.getElementById("original-preview");
const originalPreviewImageEl = document.getElementById("original-preview-image");
const originalPreviewTextEl = document.getElementById("original-preview-text");
const documentZoneEl = document.querySelector("[data-role=document-zone]");
const rawSkeletonEl = document.querySelector("[data-role=raw-skeleton]");
const downloadEl = document.getElementById("download-link");
const extractedTextEl = document.getElementById("extracted-text");
const historyListEl = document.getElementById("history-list");
const downloadMarkdownButton = document.getElementById("download-markdown-button");
const languageSelect = document.getElementById("language-select");
const themeToggleButton = document.getElementById("theme-toggle");
const analysisTitleEl = document.querySelector("[data-role=analysis-title]");
const analysisPlaceholderEl = document.querySelector("[data-role=analysis-placeholder]");
const analysisSkeletonEl = document.querySelector("[data-role=analysis-skeleton]");
const analysisContentEl = document.querySelector("[data-role=analysis-content]");
const copyAnalysisButton = document.querySelector("[data-role=copy-analysis]");
const analysisContextEl = document.querySelector("[data-role=analysis-context]");
const analysisSummaryEl = document.querySelector("[data-role=analysis-summary]");
const analysisExplanationEl = document.querySelector("[data-role=analysis-explanation]");
const analysisRedFlagsEl = document.querySelector("[data-role=analysis-red-flags]");
const demoBannerEl = document.getElementById("demo-banner");

const HISTORY_MAX_ENTRIES = 10;
const THEME_STORAGE_KEY = "file-analyzer-theme";

function friendlyErrorMessage(status) {
  const key = { 413: "err413", 415: "err415", 422: "err422", 429: "err429", 502: "err502" }[status];
  return FileAnalyzerI18n.translate(languageSelect.value, key || "errGeneric");
}

let lastExtractedText = "";
let lastAnalyzedFile = null;
let extractionPromise = Promise.resolve();
let reportObjectUrl = "";

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

// The analysis zone shows exactly one of: a prompt to start, a loading
// skeleton, the explanation, or -- for a reopened history entry -- the
// stored PDF.
function setAnalysisState(state) {
  analysisPlaceholderEl.hidden = state !== "placeholder";
  analysisSkeletonEl.hidden = state !== "loading";
  analysisContentEl.hidden = state !== "ready";
  previewEl.hidden = state !== "report";
  copyAnalysisButton.hidden = state !== "ready";
  // Swapping the key (not just the text) keeps the title correct when the
  // user later changes language, since applyTranslations reads data-i18n.
  analysisTitleEl.dataset.i18n = state === "report" ? "generatedReportHeading" : "analysisHeading";
  analysisTitleEl.textContent = FileAnalyzerI18n.translate(languageSelect.value, analysisTitleEl.dataset.i18n);
}

function releaseReportUrl() {
  if (reportObjectUrl) {
    URL.revokeObjectURL(reportObjectUrl);
    reportObjectUrl = "";
  }
  previewEl.removeAttribute("src");
  downloadEl.removeAttribute("href");
}

function resetOutcome() {
  errorEl.hidden = true;
  errorEl.textContent = "";
  workspaceEl.classList.remove("workspace--report-only");
  workspaceActionsEl.hidden = true;
  downloadMarkdownButton.hidden = true;
  lastAnalyzedFile = null;
  setAnalysisState("placeholder");
  releaseReportUrl();
}

function resetOriginalPreview() {
  documentZoneEl.hidden = true;
  originalPreviewEl.hidden = true;
  originalPreviewImageEl.hidden = true;
  if (originalPreviewEl.src) {
    URL.revokeObjectURL(originalPreviewEl.src);
    originalPreviewEl.removeAttribute("src");
  }
  if (originalPreviewImageEl.src) {
    URL.revokeObjectURL(originalPreviewImageEl.src);
    originalPreviewImageEl.removeAttribute("src");
  }
}

function showOriginalPreview(file) {
  resetOriginalPreview();

  // Only files the browser can actually render get their own pane. For
  // .txt/.docx/.eml the extracted text above already *is* the document, so a
  // second pane would just repeat it -- the analysis takes that space instead.
  const type = file.type || "";
  if (type === "application/pdf") {
    originalPreviewEl.src = URL.createObjectURL(file);
    originalPreviewEl.type = "application/pdf";
    originalPreviewEl.hidden = false;
    documentZoneEl.hidden = false;
  } else if (type.startsWith("image/")) {
    originalPreviewImageEl.src = URL.createObjectURL(file);
    originalPreviewImageEl.hidden = false;
    documentZoneEl.hidden = false;
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

  setAnalysisState("ready");
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
  rawSkeletonEl.hidden = true;
  extractedTextEl.hidden = true;
  extractedTextEl.textContent = "";
  lastExtractedText = "";
}

async function showExtractedTextPreview(file) {
  resetExtractedText();
  rawSkeletonEl.hidden = false;

  const formData = new FormData();
  formData.append("file", file);

  try {
    const response = await fetch("/extract", { method: "POST", body: formData });
    if (!response.ok) {
      rawSkeletonEl.hidden = true;
      showError(friendlyErrorMessage(response.status));
      return;
    }

    const { text } = await response.json();
    lastExtractedText = text;
    rawSkeletonEl.hidden = true;
    extractedTextEl.textContent = text;
    extractedTextEl.hidden = false;
  } catch (networkError) {
    rawSkeletonEl.hidden = true;
    showError(FileAnalyzerI18n.translate(languageSelect.value, "errNetwork"));
  }
}

function showError(message) {
  errorEl.hidden = false;
  errorEl.textContent = message;
}

function setReportDownload(blob, filename) {
  releaseReportUrl();
  reportObjectUrl = URL.createObjectURL(blob);
  downloadEl.href = reportObjectUrl;
  downloadEl.setAttribute("download", filename);
  workspaceActionsEl.hidden = false;
}

// A history entry stores only the generated PDF -- no original file, no
// analysis -- so the workspace shows that report on its own.
function showStoredReport(blob, filename) {
  workspaceEl.hidden = false;
  workspaceEl.classList.add("workspace--report-only");
  setReportDownload(blob, filename);
  previewEl.src = reportObjectUrl;
  setAnalysisState("report");
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
      resetExtractedText();
      resetOriginalPreview();
      showStoredReport(blob, entry.reportFilename);
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
  if (!file) {
    resetExtractedText();
    resetOriginalPreview();
    workspaceEl.hidden = true;
    return;
  }

  // The workspace opens as soon as a file is chosen and fills in stage by
  // stage: the document pane first (straight from the file), then the raw
  // text once /extract returns, then the analysis once the AI answers.
  workspaceEl.hidden = false;
  showOriginalPreview(file);
  extractionPromise = showExtractedTextPreview(file);
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

// Real analysis takes a few seconds end to end (extraction + LLM call);
// these step messages are illustrative reassurance, not literal
// real-time progress -- the backend is a single request/response, it has
// no way to report intermediate stages back to the browser.
const ANALYZING_STEP_KEYS = ["statusStep1", "statusStep2", "statusStep3"];
const ANALYZING_STEP_INTERVAL_MS = 2200;
let analyzingStepTimer = null;

// Estimated total time for a single analysis (extraction + AI call), based
// on real measurements against Azure OpenAI gpt-5-mini -- see
// docs/2026-09-15-fix-latenza-analisi.md and
// docs/2026-09-15-fix-doppia-estrazione.md. The bar eases toward a cap
// below 100% instead of the real estimate, so a slower-than-usual request
// never leaves it looking stuck at "100% but not actually done".
const PROGRESS_ESTIMATE_MS = 30000;
const PROGRESS_CAP_PERCENT = 92;
const PROGRESS_TICK_MS = 200;
let progressTimer = null;

function startAnalyzingStatus() {
  statusEl.hidden = false;
  let stepIndex = 0;
  const showStep = () => {
    statusTextEl.textContent = FileAnalyzerI18n.translate(languageSelect.value, ANALYZING_STEP_KEYS[stepIndex]);
    stepIndex = (stepIndex + 1) % ANALYZING_STEP_KEYS.length;
  };
  showStep();
  analyzingStepTimer = setInterval(showStep, ANALYZING_STEP_INTERVAL_MS);

  statusProgressFillEl.style.width = "0%";
  const startedAt = Date.now();
  progressTimer = setInterval(() => {
    const elapsed = Date.now() - startedAt;
    const percent = Math.min(PROGRESS_CAP_PERCENT, (elapsed / PROGRESS_ESTIMATE_MS) * PROGRESS_CAP_PERCENT);
    statusProgressFillEl.style.width = `${percent}%`;
  }, PROGRESS_TICK_MS);
}

function stopAnalyzingStatus() {
  if (analyzingStepTimer) {
    clearInterval(analyzingStepTimer);
    analyzingStepTimer = null;
  }
  if (progressTimer) {
    clearInterval(progressTimer);
    progressTimer = null;
  }
  statusEl.hidden = true;
  statusTextEl.textContent = "";
  statusProgressFillEl.style.width = "0%";
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  resetOutcome();

  const file = fileInput.files[0];
  if (!file) {
    return;
  }

  startAnalyzingStatus();
  workspaceEl.hidden = false;
  setAnalysisState("loading");

  // Wait for the preview's /extract call so its result can be reused below --
  // avoids re-extracting (and, for scanned files, re-OCRing) the same file twice.
  await extractionPromise;

  const formData = new FormData();
  formData.append("file", file);
  formData.append("language", languageSelect.value);
  if (lastExtractedText) {
    formData.append("extracted_text", lastExtractedText);
  }

  try {
    const response = await fetch("/analyze/review", { method: "POST", body: formData });

    if (!response.ok) {
      setAnalysisState("placeholder");
      showError(friendlyErrorMessage(response.status));
      return;
    }

    const { analysis, pdf_base64: pdfBase64 } = await response.json();
    const blob = base64ToBlob(pdfBase64, "application/pdf");
    const filename = FileAnalyzerFilename.reportFilenameFor(file.name);
    setReportDownload(blob, filename);
    renderAnalysis(analysis);
    await addToHistory(file, blob, filename);
    lastAnalyzedFile = file;
    downloadMarkdownButton.hidden = false;

    if (lastExtractedText) {
      extractedTextEl.innerHTML = highlightRedFlags(lastExtractedText, analysis.red_flags);
    }
  } catch (networkError) {
    setAnalysisState("placeholder");
    showError(FileAnalyzerI18n.translate(languageSelect.value, "errNetwork"));
  } finally {
    stopAnalyzingStatus();
  }
});

async function checkDemoMode() {
  try {
    const response = await fetch("/health");
    if (!response.ok) {
      return;
    }
    const { demo_mode: demoMode } = await response.json();
    demoBannerEl.hidden = !demoMode;
  } catch (networkError) {
    // Best-effort only: not knowing demo status shouldn't block the page.
  }
}

initTheme();
applyLanguageToUI();
renderHistory();
checkDemoMode();
