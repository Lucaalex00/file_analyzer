# Fix: corruzione PDF diluita, layout header, animazione drag&drop

## Contesto

Dopo il fix precedente (`docs/2026-08-30-fix-ocr-fallback-e-tema.md`),
l'utente ha ritestato e confermato che tema, colori e cambio lingua ora
funzionano bene ("il cambio lingua TOP"), ma ha segnalato che il testo del
cedolino continuava a estrarsi con le "s" al posto degli spazi — il fix OCR
non scattava. Ha inoltre chiesto di spostare il selettore lingua accanto al
bottone tema in alto, e di aggiungere un'animazione quando si trascina un
file sull'area di drop.

## Cosa è cambiato

### 1. Euristica di corruzione diluita da testo pulito

La causa del mancato trigger dell'OCR: `_looks_corrupted` valutava la
densità di spazi sull'intero documento concatenato. Un cedolino reale
mischia sezioni pulite (intestazione, importi con spazi regolari) con
sezioni corrotte (tabella con etichette incollate): la densità media
sull'intero testo può restare sopra la soglia anche se una sezione intera è
illeggibile, diluendo il segnale.

Aggiunto un secondo segnale in `src/extractors/pdf_extractor.py`: la
densità di transizioni minuscola→MAIUSCOLA senza spazio (`[a-zà-ü][A-ZÀ-Ü]`).
Il pattern di corruzione osservato incolla sempre una parola Title-Case
alla successiva tramite il carattere spurio ("PeriodosDisRetribuzione"),
producendo molte transizioni di questo tipo — un pattern quasi assente
nella prosa normale, quindi resta un segnale affidabile anche quando la
densità di spazi pura viene diluita da altre parti pulite del documento.

### 2. Selettore lingua spostato accanto al tema

`frontend/index.html`: rimosso dal form, spostato in un contenitore
`.header-controls` nell'header, di fianco al bottone tema. Nessun impatto
funzionale (il codice legge sempre `#language-select` per id/data-role,
indipendentemente dalla sua posizione nel DOM).

### 3. Animazione drag&drop

`frontend/app.js`: la dropzone ora aggiunge la classe `dropzone--active` su
`dragover` e la rimuove su `dragleave`/`drop`. `frontend/styles.css`: bordo
pieno, sfondo leggermente accentato e piccolo scale-up mentre la classe è
attiva.

## Known gap

- Il fix alla corruzione PDF non è ancora stato riverificato dall'utente
  contro il cedolino reale (file non condiviso per motivi di privacy) — è
  l'unico modo per confermare definitivamente che l'euristica combinata
  intercetta anche il caso reale, non solo il caso di test costruito a mano.

## Verification

- Backend: 136/136 test passati (nuovo test su corruzione diluita),
  97.05% coverage, `ruff check` pulito.
- Frontend unit: 12/12 test passati.
- Playwright e2e: 15/15 test passati (nuovo test sull'animazione drag&drop).
