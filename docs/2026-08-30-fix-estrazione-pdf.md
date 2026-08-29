# 2026-08-30 — Fix: estrazione PDF illeggibile su documenti tabellari

## Context

Test manuale dell'utente con un cedolino paga reale (PDF generato da
software Zucchetti, layout a tabella con molte celle posizionate): il testo
estratto risultava illeggibile — parole spezzate con caratteri estranei
inseriti tra le sillabe (es. "PERIODO DI RETRIBUZIONE" diventava
"PE RIODOsDIsR E TR IBUZIONE").

## What changed

- `src/extractors/pdf_extractor.py`: sostituita `pypdf` con `pdfplumber`
  per l'estrazione testo. `pypdf.extract_text()` segue l'ordine interno del
  content stream del PDF, che su documenti tabellari (cedolini, fatture,
  moduli) produce un ordinamento e una spaziatura sbagliati. `pdfplumber`
  ricostruisce il testo raggruppando i caratteri per posizione reale (x, y)
  sulla pagina — molto più affidabile su questo tipo di layout.
- `requirements.txt`: aggiunta `pdfplumber==0.11.4`. `pypdf` resta come
  dipendenza solo per costruire fixture nei test (`PdfWriter`), non è più
  usata da nessun percorso di produzione.
- `docs/adr/0002-pdf-extraction-pdfplumber.md` (nuovo): motivazione della
  scelta.
- `tests/unit/test_pdf_extractor.py`: nuovo test di regressione — due
  "celle" di testo posizionate separatamente (come in una riga di tabella)
  devono restare separate da uno spazio ("Codice Azienda", non
  "CodiceAzienda") — riproduce esattamente il tipo di bug segnalato.

## Known gap

Non è stato possibile verificare il fix contro il cedolino reale dell'utente
(dati sensibili, giustamente non condivisi) — il fix affronta la causa più
probabile e nota di questo tipo di artefatto, ma va confermato ricaricando
lo stesso file nell'interfaccia.

## Verification

- `pytest --cov=src --cov-fail-under=80 -v` + `ruff check src tests`:
  128/128 test (1 nuovo, di regressione sulla spaziatura tra celle), 96.89%
  coverage, lint pulito.
- `npx playwright test` (via `make test-e2e`): 9/9, nessuna regressione.
