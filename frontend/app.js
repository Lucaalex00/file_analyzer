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

const HISTORY_MAX_ENTRIES = 10;

const ERROR_MESSAGES = {
  413: "Il file è troppo grande.",
  415: "Tipo di file non supportato. Sono accettati solo PDF, TXT e DOCX.",
  422: "Non è stato possibile leggere il contenuto del file (potrebbe essere corrotto o vuoto).",
  502: "Il servizio di analisi non ha risposto correttamente. Riprova tra poco.",
};

function friendlyErrorMessage(status) {
  return ERROR_MESSAGES[status] || "Si è verificato un errore imprevisto durante l'analisi.";
}

let lastExtractedText = "";
let lastAnalyzedFile = null;

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

function resetOutcome() {
  errorEl.hidden = true;
  errorEl.textContent = "";
  resultEl.hidden = true;
  downloadMarkdownButton.hidden = true;
  lastAnalyzedFile = null;
  if (previewEl.src) {
    URL.revokeObjectURL(previewEl.src);
    previewEl.src = "";
  }
}

async function downloadMarkdownReport(file) {
  const formData = new FormData();
  formData.append("file", file);

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
      return; // The definitive error surfaces when the user clicks Analizza.
    }

    const { text } = await response.json();
    lastExtractedText = text;
    extractedTextEl.textContent = text;
    extractedTextPanel.hidden = false;
  } catch (networkError) {
    // Silent: this is a best-effort preview, not the primary flow.
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

  history.forEach((entry, index) => {
    const item = document.createElement("li");
    item.dataset.role = "history-item";

    const label = document.createElement("span");
    label.textContent = `${new Date(entry.timestamp).toLocaleString("it-IT")} — ${entry.filename}`;
    item.appendChild(label);

    const reopenButton = document.createElement("button");
    reopenButton.type = "button";
    reopenButton.textContent = "Riapri";
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
    showExtractedTextPreview(file);
  } else {
    resetExtractedText();
  }
}

["dragover", "dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => event.preventDefault());
});

dropzone.addEventListener("drop", (event) => {
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

  statusEl.textContent = "Analisi in corso...";

  const formData = new FormData();
  formData.append("file", file);

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
    await addToHistory(file, blob, filename);
    lastAnalyzedFile = file;
    downloadMarkdownButton.hidden = false;

    if (lastExtractedText) {
      extractedTextEl.innerHTML = highlightRedFlags(lastExtractedText, analysis.red_flags);
    }
  } catch (networkError) {
    showError("Impossibile contattare il servizio di analisi.");
  } finally {
    statusEl.textContent = "";
  }
});

renderHistory();
