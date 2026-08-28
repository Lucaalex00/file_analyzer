const form = document.getElementById("analyze-form");
const fileInput = document.getElementById("file-input");
const dropzone = document.getElementById("dropzone");
const statusEl = document.getElementById("status");
const errorEl = document.getElementById("error-message");
const resultEl = document.getElementById("result");
const previewEl = document.getElementById("report-preview");
const downloadEl = document.getElementById("download-link");

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

["dragover", "dragleave", "drop"].forEach((eventName) => {
  dropzone.addEventListener(eventName, (event) => event.preventDefault());
});

dropzone.addEventListener("drop", (event) => {
  const droppedFiles = event.dataTransfer?.files;
  if (droppedFiles && droppedFiles.length > 0) {
    fileInput.files = droppedFiles;
  }
});

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
  } catch (networkError) {
    showError("Impossibile contattare il servizio di analisi.");
  } finally {
    statusEl.textContent = "";
  }
});
