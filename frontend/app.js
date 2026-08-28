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

function filenameFromContentDisposition(header) {
  const match = /filename="([^"]+)"/.exec(header || "");
  return match ? match[1] : "report.pdf";
}

function resetOutcome() {
  errorEl.hidden = true;
  errorEl.textContent = "";
  resultEl.hidden = true;
  if (previewEl.src) {
    URL.revokeObjectURL(previewEl.src);
    previewEl.src = "";
  }
}

function resetExtractedText() {
  extractedTextPanel.hidden = true;
  extractedTextEl.textContent = "";
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
    const response = await fetch("/analyze", { method: "POST", body: formData });

    if (!response.ok) {
      showError(friendlyErrorMessage(response.status));
      return;
    }

    const blob = await response.blob();
    const filename = filenameFromContentDisposition(response.headers.get("content-disposition"));
    showResult(blob, filename);
    await addToHistory(file, blob, filename);
  } catch (networkError) {
    showError("Impossibile contattare il servizio di analisi.");
  } finally {
    statusEl.textContent = "";
  }
});

renderHistory();
