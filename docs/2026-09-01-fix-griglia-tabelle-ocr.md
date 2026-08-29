# Feature: ricostruzione a griglia delle tabelle rilevate + footer separato

## Contesto

Con l'OCR italiano ad alta risoluzione (`docs/2026-08-31-fix-qualita-ocr.md`)
il cedolino reale non aveva più le "s" spurie, ma la qualità restava bassa:
parole storpiate ("Odice Adenda" invece di "Codice Azienda"), righe di
rumore dalle linee della tabella lette come caratteri spuri, e contenuti
non pertinenti (banner banca, promo app, attribuzione software vendor)
mischiati nel mezzo del testo.

Discusso con l'utente (via brainstorming) un approccio diverso: invece di
fare OCR sull'intera pagina in un colpo solo, rilevare la struttura reale
della tabella nel PDF e leggerla cella per cella. Decisioni prese insieme:

- Rilevamento tabella: **automatico** via `pdfplumber.page.find_tables()`
  (basato sulle linee vettoriali reali del PDF), non categorie di
  documento predefinite — generico per qualunque PDF tabellare.
- Lettura celle: **OCR per singola cella** (più preciso, niente rumore di
  bordi/etichette laterali), non OCR sull'intera pagina.
- Contenuto sotto l'ultima tabella (footer/pubblicità): **mai scartato**
  (rischio di perdere qualcosa di rilevante su un documento
  finanziario/legale) — solo spostato in una sezione chiaramente separata
  e etichettata, non scartato né mescolato con la griglia.

## Cosa è cambiato

`src/extractors/pdf_extractor.py`:

- `_ocr_page_with_tables(page, image, scale)`: per ogni pagina, se
  `page.find_tables()` trova tabelle, ricostruisce il contenuto come:
  1. Blocco di intestazione (area sopra la tabella più in alto), OCR come
     blocco unico.
  2. Ogni tabella rilevata, ricostruita riga per riga con le celle unite
     da `" | "`.
  3. Tutto ciò che sta sotto l'ultima tabella, sotto l'etichetta
     `--- Altro contenuto nella pagina ---`.
  Se non viene rilevata nessuna tabella (contratti, lettere, email
  scansionate), il comportamento resta quello precedente: OCR sull'intera
  pagina.
- `_ocr_region(image, bbox, scale, psm=None)`: ritaglia l'immagine
  renderizzata secondo il bounding box (nello stesso spazio di coordinate
  top-down usato sia da pdfplumber che dall'immagine renderizzata) e fa
  OCR sul ritaglio.
- Scoperta empirica durante lo sviluppo: il modo pagina di Tesseract
  `--psm 6`/`7` (adatti a blocchi/linee) restituivano stringa vuota su
  ritagli piccoli delle singole celle, mentre `--psm 11` ("sparse text")
  legge correttamente il contenuto — usato per l'OCR per-cella.

## Known gap

- Non ancora verificato dall'utente contro il cedolino reale (file non
  condiviso per motivi di privacy) — resta da confermare che la
  ricostruzione a griglia migliori davvero la leggibilità su quel
  documento specifico, non solo sul PDF di test costruito a mano.
- Se una pagina ha più tabelle non allineate orizzontalmente (es. due
  tabelle affiancate, non una sopra l'altra), l'ordinamento per `bbox[1]`
  (top) potrebbe non riflettere l'ordine di lettura naturale — non
  osservato nei cedolini reali finora, ma è un limite noto dell'euristica.

## Verification

- Backend: 139/139 test passati (nuovi test su `_ocr_region` e sulla
  ricostruzione griglia con header/footer, PDF di test con vere linee
  vettoriali di tabella), 97.25% coverage, `ruff check` pulito.
- Playwright e2e: 15/15 test passati contro lo stack Docker ricostruito.
