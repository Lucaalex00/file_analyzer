# docs/

A dated log of every design decision and fix, in the order they actually
happened — not a polished changelog, the real working history. Start with
[OVERVIEW.md](../OVERVIEW.md) for the current architecture; come here for
*why* it ended up that way.

## MVP

- [2026-08-27 — Design](2026-08-27-file-analyzer-design.md)
- [2026-08-27 — Implementation plan](2026-08-27-file-analyzer-implementation-plan.md)
- [2026-08-27 — MVP](2026-08-27-file-analyzer-mvp.md)

## Fase 2 features

- [2026-08-28 — Roadmap](2026-08-28-fase2-roadmap.md) — the prioritized backlog everything below came from
- [2026-08-28 — Explainability](2026-08-28-explainability.md)
- [2026-08-28 — Frontend design](2026-08-28-frontend-design.md) / [minimal frontend](2026-08-28-frontend-minimale.md)
- [2026-08-28 — Local history](2026-08-28-cronologia-locale.md)
- [2026-08-28 — Hardening pack](2026-08-28-hardening-pack.md)
- [2026-08-28 — Before/after preview](2026-08-28-preview-prima-dopo.md)
- [2026-08-29 — Rule-based red flags](2026-08-29-rule-based-red-flags.md)
- [2026-08-29 — Rate limiting](2026-08-29-rate-limiting.md)
- [2026-08-29 — Email extractor](2026-08-29-estrattore-email.md)
- [2026-08-29 — Document comparison](2026-08-29-confronto-documenti.md)
- [2026-08-29 — Batch upload](2026-08-29-batch-upload.md)
- [2026-08-29 — Markdown export](2026-08-29-export-markdown.md)
- [2026-08-29 — Multi-language](2026-08-29-multi-lingua.md)
- [2026-08-29 — PDF branding](2026-08-29-branding-pdf.md)
- [2026-08-29 — Standalone CLI](2026-08-29-cli-standalone.md)
- [2026-08-29 — Image OCR](2026-08-29-ocr-immagini.md)

## PDF/OCR quality (a real user-reported bug, fixed in stages)

- [2026-08-30 — First fix attempt: pdfplumber](2026-08-30-fix-estrazione-pdf.md) (see also [ADR 0002](adr/0002-pdf-extraction-pdfplumber.md) — turned out insufficient on its own)
- [2026-08-30 — Frontend redesign](2026-08-30-redesign-frontend.md), [OCR fallback + theme fix](2026-08-30-fix-ocr-fallback-e-tema.md)
- [2026-08-31 — Diluted corruption + UX](2026-08-31-fix-corruzione-diluita-e-ux.md)
- [2026-08-31 — OCR quality (language pack, DPI)](2026-08-31-fix-qualita-ocr.md)
- [2026-09-01 — Table-grid OCR reconstruction](2026-09-01-fix-griglia-tabelle-ocr.md) — the actual root-cause fix
- [2026-09-01 — Rejecting non-document images](2026-09-01-fix-immagini-non-documento.md)
- [2026-09-02 — Silent preview failure fix](2026-09-02-fix-preview-silenziosa.md)

## AI reliability & demo mode

- [2026-09-08 — Prompt injection, eval suite, documented limits](2026-09-08-ai-reliability-injection-eval-limits.md)
- [2026-09-08 — AI call tracing](2026-09-08-ai-call-tracing.md)
- [2026-09-08 — Demo mode, one-command startup](2026-09-08-demo-mode-one-command.md)

## Going live on Azure

- [2026-09-14 — Weak-point analysis, recruiter simplification](2026-09-14-analisi-punti-deboli.md)
- [2026-09-14 — Real deploy on Azure Container Apps](2026-09-14-deploy-azure-container-apps.md) — Functions couldn't install WeasyPrint's system libraries
- [2026-09-15 — Azure OpenAI unblocked, httpx fix, Groq integration](2026-09-15-azure-openai-sbloccato.md)
- [2026-09-15 — Live demo updated with real Azure OpenAI](2026-09-15-live-demo-ai-reale.md)

## Analysis quality and speed

- [2026-09-15 — Anti-genericness prompt guardrail](2026-09-15-guardrail-prompt-e-progress-ux.md)
- [2026-09-15 — Latency: lowering reasoning_effort](2026-09-15-fix-latenza-analisi.md) — ~25s down to ~13s per call
- [2026-09-15 — Extracting the same document twice](2026-09-15-fix-doppia-estrazione.md) — the other half of the wait
- [2026-09-16 — Telling the model today's date](2026-09-16-data-corrente-nel-prompt.md) — found by analysing a real CV
- [2026-09-20 — Four fixes to the AI reliability layer](2026-09-20-affidabilita-ai-correzioni.md) — quote grounding, cross-language merge, retry on malformed output, token accounting
- [2026-09-20 — An eval against the real model](2026-09-20-eval-contro-modello-reale.md) — and the two defects it found on its first run

## The interface a reviewer actually sees

- [2026-09-15 — Estimated progress bar](2026-09-15-barra-progresso-attesa.md)
- [2026-09-15 — Original document beside the report](2026-09-15-confronto-documento-report.md)
- [2026-09-15 — The "book" workspace that fills in stage by stage](2026-09-15-workspace-immersivo.md)
- [2026-09-16 — Readable in thirty seconds: examples, in-app docs, spend cap](2026-09-16-demo-per-chi-valuta.md)
- [2026-09-21 — Showing what the analysis cost](2026-09-21-costo-analisi-in-pagina.md) — tokens and elapsed time, quietly, under the explanation

## Repo health

- [2026-09-15 — The example-generation script had never been runnable](2026-09-15-fix-script-esempi.md)
- [2026-09-15 — Static assets served without cache headers](2026-09-15-fix-cache-asset-statici.md) — stale CSS survived deploys
- [2026-09-16 — Dev image stage, social preview, viewport](2026-09-16-rifiniture-dev-stage-e-anteprima.md)
- [2026-09-16 — Cold start: measuring it before paying for it](2026-09-16-cold-start-misurato.md) — including the measurement that was wrong
- [2026-09-16 — Drift from the original design](2026-09-16-scostamenti-dal-design.md) — what August's design still holds, what changed and why

## Other

- [`adr/`](adr/) — architecture decision records (PDF generation, PDF extraction library choice)
- [`screenshots/`](screenshots/) — README images and demo GIF source
