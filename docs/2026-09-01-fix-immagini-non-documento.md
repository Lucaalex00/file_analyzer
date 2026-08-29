# Fix: qualità OCR immagini + rifiuto di immagini senza testo affidabile

## Contesto

Testando `image_extractor.py` (percorso separato da `pdf_extractor.py`,
usato quando si carica direttamente un'immagine invece di un PDF) l'utente
ha segnalato due problemi:

1. Un **flyer promozionale** (corso di danza "Danzatricità", layout
   grafico con font decorativi e icone) — testo estratto molto confuso.
2. Un **logo** — testo estratto completamente senza senso: Tesseract
   "inventa" caratteri dalle forme grafiche quando non c'è vero testo da
   leggere.

`image_extractor.py` non aveva nessuno dei miglioramenti già applicati a
`pdf_extractor.py` (lingua italiana, pre-processing).

## Cosa è cambiato

- **`src/extractors/ocr_utils.py`** (nuovo): estratte da `pdf_extractor.py`
  le funzioni di pre-processing OCR condivise, più una nuova
  `mean_ocr_confidence(image, lang)` che usa `pytesseract.image_to_data`
  per calcolare la confidenza media che Tesseract stesso assegna alle
  parole che ha effettivamente riconosciuto (0-100 per parola, -1 per le
  aree che non ha trattato come testo). `pdf_extractor.py` ora importa da
  qui invece di duplicare la logica.
- **`src/extractors/image_extractor.py`**: allineato a `pdf_extractor.py`
  con `lang="ita"` e lo stesso pre-processing scala di grigi + soglia.
  Aggiunto un controllo di affidabilità: se il testo estratto non è vuoto
  ma la confidenza media OCR è sotto una soglia (40), viene sollevato un
  `ExtractionError` con un messaggio chiaro ("non sembra contenere testo
  leggibile in modo affidabile — potrebbe essere un logo, un grafico o
  un'immagine decorativa") invece di mandare avanti testo spazzatura
  all'analisi AI. La soglia è iniettabile (`ImageExtractor(confidence_fn=...)`)
  per restare testabile senza dipendere dal comportamento reale, spesso
  imprevedibile, di Tesseract su immagini sintetiche.

## Known gap

- Per il flyer con font decorativi e layout grafico misto (non un logo
  puro, contiene vero testo) non c'è un fix magico: l'OCR su design
  grafici stilizzati resta un problema difficile in generale, anche per
  servizi commerciali. Lingua italiana + pre-processing possono aiutare
  un po', ma non aspettarsi risultati equivalenti a un documento normale.
- La soglia di confidenza (40) è una euristica calibrata su casi sintetici
  costruiti a mano (non è stato possibile testare contro le immagini reali
  dell'utente, giustamente non condivise) — potrebbe richiedere
  ricalibrazione se in futuro si osservano falsi positivi/negativi.

## Verification

- Backend: 144/144 test passati (nuovi test su `ocr_utils` e sul rifiuto
  per bassa confidenza in `ImageExtractor`), 97.33% coverage, `ruff check`
  pulito.
- Playwright e2e: 15/15 test passati contro lo stack Docker ricostruito.
