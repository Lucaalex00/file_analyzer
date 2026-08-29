# Fix: estrazione PDF con OCR di fallback, tema rotto, colori troppo accesi

## Contesto

Dopo il redesign del frontend (`docs/2026-08-30-redesign-frontend.md`) e il
primo tentativo di fix sull'estrazione PDF (`docs/adr/0002-pdf-extraction-pdfplumber.md`),
l'utente ha ritestato l'app manualmente con un cedolino reale (Zucchetti) e
un browser reale, segnalando che:

1. Il testo estratto era ancora corrotto — ogni spazio sostituito da una
   lettera casuale ("VocisVariabilisDelsMese" invece di "Voci Variabili Del
   Mese").
2. Il pulsante di cambio tema appariva rotto (icona sostituita da testo
   che andava a capo nel cerchio).
3. Entrambi i temi (chiaro e scuro) erano troppo accesi/contrastati
   ("si impallano gli occhi").
4. Non era chiaro se il cambio lingua funzionasse.

## Cosa è cambiato

### 1. Estrazione PDF: root cause reale + fallback OCR

Il passaggio da `pypdf` a `pdfplumber` (fix precedente) non ha risolto il
problema: pypdf e pdfplumber usano algoritmi di estrazione completamente
diversi (ordine dello stream vs. posizione dei caratteri sulla pagina) ma
producevano la stessa identica corruzione. Questo dimostra che il difetto
non è nell'algoritmo di estrazione ma nel PDF sorgente stesso: il font
incorporato ha una ToUnicode CMap che mappa il glifo dello spazio a un
carattere sbagliato.

Fix implementato in `src/extractors/pdf_extractor.py`:

- `_looks_corrupted(text)`: euristica basata sulla densità di spazi
  (< 6% di spazi su testo ≥ 50 caratteri → probabile corruzione).
- `_ocr_pdf_pages(file_bytes)`: quando il testo estratto risulta vuoto o
  corrotto, ogni pagina viene renderizzata come immagine (via
  `pdfplumber`/`pypdfium2`, già dipendenza transitiva — zero nuovi pacchetti)
  e letta con Tesseract OCR, che legge i pixel visivi bypassando
  completamente la codifica interna del font.
- L'OCR è iniettabile (`PdfExtractor(ocr_fn=...)`) per restare testabile
  senza rendering reale nei test mockati.

### 2. Pulsante cambio tema rotto

Causa: l'attributo `data-i18n="themeToggle"` sul bottone, sommato all'emoji
🌓 come contenuto statico. `applyTranslations()` sovrascrive il
`textContent`, quindi l'emoji veniva rimpiazzata dalla stringa tradotta
"Cambia tema", che andava a capo nel bottone circolare.

Fix: rimosso `data-i18n` dal bottone (resta solo l'emoji), `title`/
`aria-label` impostati via `FileAnalyzerI18n.translate()` direttamente in
`applyLanguageToUI()` (`frontend/app.js`). CSS di `#theme-toggle` reso più
robusto (`display:flex; align-items:center; justify-content:center;
flex-shrink:0; padding:0; line-height:1;`) così il layout non si rompe più
indipendentemente dal contenuto.

### 3. Palette colori troppo accese

Sostituiti tutti i valori delle custom properties CSS (`frontend/styles.css`)
con toni meno saturi e meno contrastati, sia per il tema chiaro che per
quello scuro — niente più sfondi vicini al nero/bianco puro né accenti
completamente saturi.

## Known gap

- Il fix OCR non è stato ancora riverificato dall'utente contro il
  cedolino reale che ha causato la segnalazione (file non condiviso,
  correttamente, per motivi di privacy dei dati anagrafici/retributivi).
- Le nuove palette colore non sono ancora state confermate visivamente
  dall'utente.
- Il cambio lingua non risultava visibilmente rotto in alcun test
  automatico (il test e2e dedicato passa); la segnalazione "non vedo il
  cambio lingua" potrebbe essere dovuta al fatto che l'attenzione era sul
  bottone del tema rotto, non a un bug reale — da riconfermare.

## Verification

- Backend: 135/135 test passati, 97.01% coverage, `ruff check` pulito
  (via container Docker `api`).
- Frontend unit: 12/12 test passati (`node --test` in `e2e/`).
- Playwright e2e: 14/14 test passati, incluso il test dedicato al toggle
  tema e quello al cambio lingua.
