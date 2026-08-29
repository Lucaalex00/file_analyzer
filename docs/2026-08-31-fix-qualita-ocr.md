# Fix: qualità OCR bassa sul cedolino reale

## Contesto

Con i fix precedenti l'OCR ora scatta correttamente e le "s" spurie sono
sparite, come confermato dall'utente ritestando col proprio cedolino reale
(Zucchetti). Ma il testo OCR risultante aveva una qualità bassa: parole
storpiate ("Odice Adenda" invece di "Codice Azienda", "Tindirizzo" invece
di "Indirizzo"), righe di rumore dalle linee della tabella lette come
caratteri ("[", "|"), valori numerici in alcune celle non corretti.

## Cosa è cambiato

In `src/extractors/pdf_extractor.py` (`_ocr_pdf_pages`):

1. **Lingua italiana esplicita**: `pytesseract.image_to_string(image,
   lang="ita")` invece del default (inglese). Il modello linguistico di
   Tesseract corregge le ambiguità OCR verso il vocabolario della lingua
   dichiarata — usare l'inglese su un documento italiano peggiora la
   correzione automatica.
2. **Risoluzione più alta**: il rendering della pagina passa da 200 a 300
   DPI, per glifi più nitidi (specialmente nelle celle piccole della
   tabella contributi/trattenute).
3. **Pre-processing in scala di grigi + soglia binaria** (`_preprocess_for_ocr`):
   i cedolini hanno linee sottili di bordo tabella e ombreggiature di
   sfondo che Tesseract può leggere come caratteri spuri ("[", "|"). Una
   soglia semplice (`> 150 → bianco, altrimenti nero`) rimuove queste linee
   deboli mantenendo il testo pieno.

`Dockerfile` e `.github/workflows/ci.yml`: aggiunto il pacchetto
`tesseract-ocr-ita` (il traineddata italiano non era installato, quindi
`lang="ita"` avrebbe altrimenti fallito).

## Known gap

- Il pre-processing è una soglia fissa (150), non adattiva — potrebbe non
  essere ottimale per scansioni con contrasto molto diverso. Va
  riverificato dall'utente sul cedolino reale; se la qualità resta
  insufficiente, il prossimo passo naturale è un pre-processing adattivo
  (es. soglia di Otsu) o un `--psm` di Tesseract dedicato al layout
  tabellare.
- Non è possibile validare automaticamente l'accuratezza OCR su un
  documento reale nei test (nessun file reale nel repo, correttamente, per
  motivi di privacy) — la verifica di qualità resta manuale da parte
  dell'utente.

## Verification

- Backend: 137/137 test passati (nuovo test che verifica `lang="ita"`
  passato a Tesseract), 97.07% coverage, `ruff check` pulito.
- Playwright e2e: 15/15 test passati contro lo stack Docker ricostruito
  con il pacchetto `tesseract-ocr-ita`.
