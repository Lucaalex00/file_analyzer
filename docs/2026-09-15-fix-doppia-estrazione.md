# Fix: il documento veniva estratto due volte durante l'analisi

**Contesto:** dopo il fix del `reasoning_effort` (vedi
[2026-09-15 — Fix: latenza analisi](2026-09-15-fix-latenza-analisi.md)),
l'utente ha segnalato via screenshot del pannello di rete del browser che
`/analyze/review` impiegava comunque ~42s, molto più dei ~12-14s della sola
chiamata AI misurati in precedenza.

## Causa

Il frontend estrae il testo **due volte** per lo stesso file:

1. Alla selezione del file, `showExtractedTextPreview()` chiama `/extract`
   per mostrare l'anteprima del testo (nello screenshot: 17.15s, verosimilmente
   OCR).
2. Al click su "Analizza", `/analyze/review` richiama internamente
   `pipeline.run_with_analysis()`, che **ri-estrae da zero** lo stesso file
   (stesso costo di estrazione/OCR) prima di chiamare l'AI.

I log del Container App confermavano: la chiamata AI vera e propria durava
~12s, ma tra la fine di `/extract` e l'inizio della chiamata AI dentro
`/analyze/review` passavano altri ~16s -- la seconda estrazione.

## Fix

- `DocumentAnalysisPipeline` (`src/pipeline.py`): estratto il codice comune
  di analisi (chiamata AI + merge dei red flag basati su regole + generazione
  PDF) in un metodo privato `_analyze_raw_text()`. Aggiunto
  `run_with_analysis_from_text(text, filename, language)`, che salta
  l'estrazione e lavora direttamente sul testo già disponibile.
- `/analyze/review` (`src/api/main.py`): nuovo campo form opzionale
  `extracted_text`. Se presente, il pipeline usa
  `run_with_analysis_from_text()` invece di `run_with_analysis()`,
  bypassando la seconda estrazione. Se assente (client vecchi, o se
  l'anteprima è fallita), il comportamento resta quello di prima.
- Frontend (`frontend/app.js`): il submit ora attende che la promise
  dell'anteprima (`extractionPromise`) sia risolta prima di costruire la
  richiesta, e allega `lastExtractedText` come `extracted_text` quando
  disponibile.

## Verifica

- Nuovi test: `test_run_with_analysis_from_text_skips_extraction_entirely`,
  `test_run_with_analysis_from_text_merges_rule_based_flags` (pipeline),
  `test_analyze_review_uses_pre_extracted_text_when_provided_skipping_re_extraction`
  (endpoint).
- Suite completa: 371 test unit/integration verdi, 19 test e2e Playwright
  verdi.
- Misurato dal vivo contro Azure OpenAI reale: `/analyze/review` con
  `extracted_text` già popolato impiega ~14.4s totali (vs ~42s osservati
  nello screenshot originale) -- il tempo si riduce essenzialmente alla sola
  chiamata AI.
