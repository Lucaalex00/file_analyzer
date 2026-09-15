# UX: documento originale e report affiancati per il confronto a occhio

**Contesto:** richiesta esplicita dell'utente -- "il pdf che genera lui
metterlo a destra con la preview, a sinistra di questo un'altra preview con
il DOCUMENTO che invece tu stesso hai inserito. cosi uno può fare compare
ad occhio."

## Fix

- `frontend/index.html`: la sezione "Report" ora contiene una griglia a due
  colonne (`.comparison-grid`): a sinistra il documento originale caricato,
  a destra il report PDF generato (comportamento invariato).
- `frontend/app.js`: `showOriginalPreview(file)` sceglie il rendering in
  base al tipo di file:
  - `application/pdf` → embed diretto del PDF originale (confronto PDF vs
    PDF)
  - `image/*` → `<img>` con l'immagine originale
  - tutto il resto (.txt, .docx, .eml) → riusa il testo già estratto per il
    pannello "Testo estratto" (nessuna nuova lettura del file)

  Nota: riaprire una voce dalla cronologia non mostra il documento
  originale a sinistra (il `File` originale non viene salvato in
  cronologia, solo il PDF risultante) -- gestito senza errori invece di
  far crashare `showResult`.
- `frontend/styles.css`: nuovo layout `.comparison-grid`/`.comparison-pane`,
  responsive (le due colonne si impilano sotto i ~700px già gestiti dal
  media query esistente, essendo un flex-wrap).
- `frontend/i18n.js`: due nuove chiavi (`originalDocumentHeading`,
  `generatedReportHeading`) in tutte e 5 le lingue supportate.

## Verifica

Nuovo test e2e "shows the original document side by side with the
generated report" (verifica visibilità di entrambi i pannelli e che il
pannello sinistro abbia una coordinata x minore di quello destro, cioè
siano davvero affiancati). Durante l'implementazione scoperto e corretto un
bug reale: riaprire una voce di cronologia crashava silenziosamente
`showResult` (chiamava `showOriginalPreview(undefined)`), lasciando il
pannello del report nascosto -- coperto ora dal test
"reopening a history entry shows the report preview again" già esistente,
che infatti falliva prima del fix.

Suite e2e completa: 21 test verdi. Suite backend: 372 test verdi (nessun
file backend toccato da questa modifica).
