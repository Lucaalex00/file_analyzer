(function (root, factory) {
  if (typeof module === "object" && module.exports) {
    module.exports = factory();
  } else {
    root.FileAnalyzerI18n = factory();
  }
})(typeof self !== "undefined" ? self : this, function () {
  const DEFAULT_LANGUAGE = "it";

  const TRANSLATIONS = {
    it: {
      subtitle:
        "Carica un contratto, una mail di lavoro o un documento personale — ricevi una spiegazione chiara, un riassunto e gli eventuali punti di attenzione.",
      dropzoneText: "Trascina un file qui, o clicca per selezionarlo (.pdf, .txt, .docx, .eml, .png, .jpg, .jpeg, .tiff, .bmp)",
      languageLabel: "Lingua della spiegazione",
      analyzeButton: "Analizza",
      statusAnalyzing: "Analisi in corso...",
      extractedTextHeading: "Testo estratto",
      analysisHeading: "Analisi",
      summaryLabel: "Riassunto",
      explanationLabel: "Spiegazione",
      contextLabel: "Contesto rilevato",
      redFlagsHeading: "Punti di attenzione",
      noRedFlags: "Nessun punto di attenzione rilevato.",
      reportHeading: "Report",
      downloadPdf: "Scarica PDF",
      downloadMarkdown: "Scarica anche in Markdown",
      historyHeading: "Cronologia (solo su questo browser)",
      historyReopen: "Riapri",
      copyButton: "Copia",
      copiedFeedback: "Copiato!",
      themeToggle: "Cambia tema",
      err413: "Il file è troppo grande.",
      err415: "Tipo di file non supportato.",
      err422: "Non è stato possibile leggere il contenuto del file (potrebbe essere corrotto o vuoto).",
      err502: "Il servizio di analisi non ha risposto correttamente. Riprova tra poco.",
      err429: "Troppe richieste, riprova tra poco.",
      errGeneric: "Si è verificato un errore imprevisto durante l'analisi.",
      errNetwork: "Impossibile contattare il servizio di analisi.",
    },
    en: {
      subtitle:
        "Upload a contract, a work email, or a personal document — get a clear explanation, a summary, and anything worth a second look.",
      dropzoneText: "Drag a file here, or click to select one (.pdf, .txt, .docx, .eml, .png, .jpg, .jpeg, .tiff, .bmp)",
      languageLabel: "Explanation language",
      analyzeButton: "Analyze",
      statusAnalyzing: "Analyzing...",
      extractedTextHeading: "Extracted text",
      analysisHeading: "Analysis",
      summaryLabel: "Summary",
      explanationLabel: "Explanation",
      contextLabel: "Detected context",
      redFlagsHeading: "Things to pay attention to",
      noRedFlags: "No notable red flags found.",
      reportHeading: "Report",
      downloadPdf: "Download PDF",
      downloadMarkdown: "Download as Markdown too",
      historyHeading: "History (this browser only)",
      historyReopen: "Reopen",
      copyButton: "Copy",
      copiedFeedback: "Copied!",
      themeToggle: "Switch theme",
      err413: "The file is too large.",
      err415: "Unsupported file type.",
      err422: "Could not read the file's content (it may be corrupt or empty).",
      err502: "The analysis service did not respond correctly. Please try again shortly.",
      err429: "Too many requests, please try again shortly.",
      errGeneric: "An unexpected error occurred during analysis.",
      errNetwork: "Could not reach the analysis service.",
    },
    fr: {
      subtitle:
        "Chargez un contrat, un e-mail professionnel ou un document personnel — obtenez une explication claire, un résumé et les points à surveiller.",
      dropzoneText: "Glissez un fichier ici, ou cliquez pour le sélectionner (.pdf, .txt, .docx, .eml, .png, .jpg, .jpeg, .tiff, .bmp)",
      languageLabel: "Langue de l'explication",
      analyzeButton: "Analyser",
      statusAnalyzing: "Analyse en cours...",
      extractedTextHeading: "Texte extrait",
      analysisHeading: "Analyse",
      summaryLabel: "Résumé",
      explanationLabel: "Explication",
      contextLabel: "Contexte détecté",
      redFlagsHeading: "Points d'attention",
      noRedFlags: "Aucun point d'attention détecté.",
      reportHeading: "Rapport",
      downloadPdf: "Télécharger le PDF",
      downloadMarkdown: "Télécharger aussi en Markdown",
      historyHeading: "Historique (ce navigateur uniquement)",
      historyReopen: "Rouvrir",
      copyButton: "Copier",
      copiedFeedback: "Copié !",
      themeToggle: "Changer de thème",
      err413: "Le fichier est trop volumineux.",
      err415: "Type de fichier non pris en charge.",
      err422: "Impossible de lire le contenu du fichier (il est peut-être corrompu ou vide).",
      err502: "Le service d'analyse n'a pas répondu correctement. Réessayez bientôt.",
      err429: "Trop de requêtes, réessayez bientôt.",
      errGeneric: "Une erreur inattendue s'est produite lors de l'analyse.",
      errNetwork: "Impossible de contacter le service d'analyse.",
    },
    de: {
      subtitle:
        "Laden Sie einen Vertrag, eine berufliche E-Mail oder ein persönliches Dokument hoch — erhalten Sie eine klare Erklärung, eine Zusammenfassung und alles, was einen zweiten Blick wert ist.",
      dropzoneText: "Datei hierher ziehen oder klicken zum Auswählen (.pdf, .txt, .docx, .eml, .png, .jpg, .jpeg, .tiff, .bmp)",
      languageLabel: "Sprache der Erklärung",
      analyzeButton: "Analysieren",
      statusAnalyzing: "Analyse läuft...",
      extractedTextHeading: "Extrahierter Text",
      analysisHeading: "Analyse",
      summaryLabel: "Zusammenfassung",
      explanationLabel: "Erklärung",
      contextLabel: "Erkannter Kontext",
      redFlagsHeading: "Punkte, auf die man achten sollte",
      noRedFlags: "Keine auffälligen Punkte gefunden.",
      reportHeading: "Bericht",
      downloadPdf: "PDF herunterladen",
      downloadMarkdown: "Auch als Markdown herunterladen",
      historyHeading: "Verlauf (nur dieser Browser)",
      historyReopen: "Erneut öffnen",
      copyButton: "Kopieren",
      copiedFeedback: "Kopiert!",
      themeToggle: "Thema wechseln",
      err413: "Die Datei ist zu groß.",
      err415: "Dateityp nicht unterstützt.",
      err422: "Der Inhalt der Datei konnte nicht gelesen werden (sie ist möglicherweise beschädigt oder leer).",
      err502: "Der Analysedienst hat nicht korrekt geantwortet. Bitte versuchen Sie es später erneut.",
      err429: "Zu viele Anfragen, bitte versuchen Sie es später erneut.",
      errGeneric: "Bei der Analyse ist ein unerwarteter Fehler aufgetreten.",
      errNetwork: "Der Analysedienst konnte nicht erreicht werden.",
    },
    es: {
      subtitle:
        "Sube un contrato, un correo de trabajo o un documento personal — obtén una explicación clara, un resumen y lo que merezca una segunda mirada.",
      dropzoneText: "Arrastra un archivo aquí, o haz clic para seleccionarlo (.pdf, .txt, .docx, .eml, .png, .jpg, .jpeg, .tiff, .bmp)",
      languageLabel: "Idioma de la explicación",
      analyzeButton: "Analizar",
      statusAnalyzing: "Analizando...",
      extractedTextHeading: "Texto extraído",
      analysisHeading: "Análisis",
      summaryLabel: "Resumen",
      explanationLabel: "Explicación",
      contextLabel: "Contexto detectado",
      redFlagsHeading: "Puntos a tener en cuenta",
      noRedFlags: "No se detectaron puntos de atención.",
      reportHeading: "Informe",
      downloadPdf: "Descargar PDF",
      downloadMarkdown: "Descargar también en Markdown",
      historyHeading: "Historial (solo este navegador)",
      historyReopen: "Reabrir",
      copyButton: "Copiar",
      copiedFeedback: "¡Copiado!",
      themeToggle: "Cambiar tema",
      err413: "El archivo es demasiado grande.",
      err415: "Tipo de archivo no compatible.",
      err422: "No se pudo leer el contenido del archivo (puede estar dañado o vacío).",
      err502: "El servicio de análisis no respondió correctamente. Inténtalo de nuevo en breve.",
      err429: "Demasiadas solicitudes, inténtalo de nuevo en breve.",
      errGeneric: "Se produjo un error inesperado durante el análisis.",
      errNetwork: "No se pudo contactar con el servicio de análisis.",
    },
  };

  function translate(language, key) {
    const dictionary = TRANSLATIONS[language] || TRANSLATIONS[DEFAULT_LANGUAGE];
    if (dictionary[key] !== undefined) {
      return dictionary[key];
    }
    return TRANSLATIONS[DEFAULT_LANGUAGE][key] !== undefined ? TRANSLATIONS[DEFAULT_LANGUAGE][key] : key;
  }

  function applyTranslations(language, root) {
    root.querySelectorAll("[data-i18n]").forEach((element) => {
      element.textContent = translate(language, element.dataset.i18n);
    });
  }

  return { translate, applyTranslations, DEFAULT_LANGUAGE };
});
