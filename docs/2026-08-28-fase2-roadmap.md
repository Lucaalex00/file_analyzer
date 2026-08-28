# 2026-08-28 — Fase 2 roadmap (backlog prioritizzato)

## Context

MVP pubblicato e funzionante (v1: PDF/TXT/DOCX, stateless, CI verde, immagine
pubblicata su GHCR). Con ~2 mesi disponibili prima della prossima scadenza di
roadmap, questo documento fissa un backlog di 20 feature per la Fase 2,
ordinate per priorità (4 = più importante, 1 = meno urgente), da rivedere e
scremare mano a mano che si avanza — non tutte e 20 vanno necessariamente
implementate.

## Backlog

| # | Priorità | Feature | Motivazione |
|---|---|---|---|
| 1 | 4 | Frontend minimale drag&drop con preview del risultato | Primo contatto per recruiter/utente; oggi esiste solo l'API |
| 2 | 4 | Pacchetto hardening dai minor della review finale (`Content-Disposition`, fail-fast config, `.dockerignore`, utente non-root, `HEALTHCHECK`) | Basso rischio, alto valore "production-grade" |
| 3 | 4 | Deploy reale su Azure Functions + demo registrata | Chiude il gap più visibile della roadmap originale (AZ-204) |
| 4 | 3 | Estrattore OCR immagini (Azure AI Vision / Tesseract) | Primo estrattore Fase 2 pluggable |
| 5 | 3 | Estrattore email (.eml/.msg) con red flag phishing | Secondo estrattore Fase 2 |
| 6 | 3 | Smoke test reale contro Azure OpenAI in CI (gated da secret) | Nessun test ha mai parlato con l'LLM vero |
| 7 | 3 | Rate limiting di base sull'endpoint pubblico | Necessario appena l'API è esposta in demo |
| 8 | 3 | Preview "prima/dopo" nel frontend (testo estratto + spiegazione) | Migliora la UX di anteprima |
| 9 | 3 | Spiegazione multi-lingua (auto-detect o scelta utente) | Rilevante per uso legale/lavorativo reale |
| 10 | 2 | Pre-check red flag rule-based prima dell'LLM | Aumenta affidabilità, riduce dipendenza dal modello |
| 11 | 2 | Confronto tra due versioni di un documento | Feature ad alto impatto per il caso legale |
| 12 | 2 | Cronologia locale lato client (localStorage) | Utile senza violare il vincolo "no database" |
| 13 | 2 | Export anche in Markdown oltre al PDF | Riprende l'idea originale del progetto |
| 14 | 2 | Explainability: evidenziare nel testo i passaggi dietro ogni red flag | Aumenta la fiducia nell'output |
| 15 | 2 | CLI standalone senza passare dal server | Secondo entry point per un pubblico tecnico |
| 16 | 2 | Batch upload (più file in una richiesta) | Uso reale oltre la demo singolo-file |
| 17 | 1 | Modello locale opzionale (Ollama) come alternativa ad Azure OpenAI | Idea originale della roadmap |
| 18 | 1 | Branding/temi personalizzabili del report PDF | Polish estetico, basso effort |
| 19 | 1 | Estensione browser/bookmarklet | Esplorativo, effort alto/ritorno incerto |
| 20 | 1 | Consegna via webhook/email del report | Nice-to-have infrastrutturale |

## Known gap

Nessuna di queste feature è ancora progettata in detaglio — ogni voce, quando
si decide di affrontarla, passa dal proprio ciclo brainstorming → design →
piano prima dell'implementazione.

## Verification

N/A — documento di pianificazione, nessun codice coinvolto.
