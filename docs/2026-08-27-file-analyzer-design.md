# 2026-08-27 — File Analyzer: design iniziale

## Context

Progetto 2 della roadmap personale (`OBJECTIVE.md`, Q4 2026). Estende l'idea originale
("posso fidarmi di questo PDF?") a un ambito più ampio: qualunque file testuale — legale,
lavorativo o personale — deve poter essere caricato e restituito all'utente come una
spiegazione chiara, un riassunto e un elenco di elementi da attenzionare (red flag). Il
progetto deve essere production-grade a livello di README/demo/CI-CD, coerente con lo
standard fissato dal Progetto 1 (TaskFlow), e deve far progredire lo studio Azure previsto
per l'esame **AZ-204**.

## Scope — MVP (Fase 1)

- Tipi di file: **PDF, TXT, DOCX**. OCR immagini ed email (.eml/.msg) sono esplicitamente
  fuori scope per l'MVP — vedi "Fase 2" sotto. Motivo: OCR e parsing email richiedono stack
  diversi dall'estrazione testo diretta; includerli subito rischia di allungare i tempi oltre
  il trimestre e ripete un pattern già visto ("iniziare il progetto successivo prima di
  chiudere bene il precedente").
- Nessun database, nessuno storage persistente. Il servizio è **stateless**: riceve un file,
  lo elabora in memoria, restituisce un report PDF. Nulla viene salvato lato server — scelta
  deliberata sia per privacy (documenti legali/personali) sia per restare a costo zero.
- Nessuna autenticazione: tool pubblico a singolo endpoint, nessun account utente.
- Contesto (legale/lavorativo/personale) rilevato **automaticamente** dall'LLM in base al
  contenuto, non selezionato manualmente.

## Fase 2 (fuori scope MVP, da pianificare dopo)

- `ImageExtractor` con OCR (Azure AI Vision, o Tesseract come alternativa locale)
- `EmailExtractor` per .eml/.msg, con focus su rilevamento phishing/red flag specifiche email
- Entrambi si aggiungono come nuove implementazioni di `BaseExtractor`, senza toccare
  Analyzer/ReportGenerator/pipeline.

## Architettura

**Stack**: Python 3.12 + FastAPI, deployato come Azure Function (HTTP trigger, Consumption/
free plan) tramite Azure Functions Python v2 (ASGI-compatible, FastAPI gira nativamente).
LLM: **Azure OpenAI**.

**Componenti** (`src/`, ciascuno testabile isolatamente):

- `extractors/` — interfaccia `BaseExtractor.extract(file) -> RawText`; implementazioni
  `PdfExtractor` (pypdf/pdfplumber), `TextExtractor` (txt/docx via python-docx).
  `ExtractorFactory` seleziona l'implementazione da MIME type/estensione.
- `analyzer/` — `DocumentAnalyzer` invia `RawText` ad Azure OpenAI con prompt strutturato;
  output validato via Pydantic (`AnalysisResult`: contesto rilevato, spiegazione in
  linguaggio semplice, riassunto, `red_flags[]`).
- `report/` — `ReportGenerator` renderizza `AnalysisResult` in un template HTML → PDF
  (WeasyPrint: più semplice da mantenere/testare di ReportLab, motivazione in
  `docs/adr/0001-pdf-generation-weasyprint.md`).
- `pipeline.py` — orchestratore sincrono: `Extractor → Analyzer → ReportGenerator`.
- `api/` — FastAPI app, endpoint `POST /analyze` (multipart upload → risposta PDF binaria).

## Data flow (happy path)

1. `POST /analyze` con file allegato (multipart)
2. `ExtractorFactory` sceglie l'estrattore → `RawText`
3. `DocumentAnalyzer` → Azure OpenAI → `AnalysisResult` (validato Pydantic)
4. `ReportGenerator` → PDF
5. Response: PDF in streaming; nessun salvataggio persistente in nessuno step

## Error handling

- File non supportato / troppo grande → 415/413, validato prima di entrare in pipeline
- Estrazione fallita (PDF corrotto, contenuto illeggibile) → errore esplicito, nessun
  fallback silenzioso verso l'LLM con testo vuoto
- Chiamata Azure OpenAI fallita/timeout → retry limitato (1-2 tentativi), poi 502 con
  messaggio utente-friendly, mai traceback grezzo in risposta
- Validazione Pydantic dell'output LLM fallita → errore esplicito, mai un report con dati
  incoerenti

## Configurazione "da zero in un comando"

- `docker compose up` (via `make up`) avvia tutto in locale, nessuna dipendenza Azure per
  sviluppare/testare la pipeline (Azure OpenAI restando l'unica dipendenza esterna reale,
  configurabile via `.env`)
- `.env.example` committato, documentato nel README
- `make demo` avvia da immagini già pubblicate su GHCR (nessuna build locale), per far
  provare il progetto al recruiter nel modo più rapido possibile
- `examples/` con 2-3 file sample (un contratto fittizio, un'email lavorativa, un TXT
  personale) + il PDF di report già generato per ciascuno, così il repo è esplorabile anche
  senza chiavi Azure configurate

## Struttura repo

```
file-analyzer/
├── src/
│   ├── extractors/     # BaseExtractor, PdfExtractor, TextExtractor, ExtractorFactory
│   ├── analyzer/        # DocumentAnalyzer, prompt templates, schemi Pydantic
│   ├── report/            # ReportGenerator, template HTML per il PDF
│   ├── api/                # FastAPI app, endpoint /analyze
│   └── pipeline.py
├── tests/
│   ├── unit/            # un modulo di test per componente, Azure OpenAI mockato
│   └── integration/    # pipeline end-to-end sui file in examples/
├── examples/             # file sample + PDF report già generati
├── scripts/              # bootstrap/setup
├── infra/                 # Bicep per Azure Function (deploy demo + tear-down)
├── docs/
│   ├── adr/               # Architecture Decision Records
│   └── YYYY-MM-DD-topic.md  # log per feature/commit-push (schema: Context / What
│                              #   changed / Known gap / Verification)
├── .github/workflows/  # CI: lint → unit test → integration test → docker build → push GHCR
├── docker-compose.yml
├── docker-compose.prebuilt.yml
├── Makefile
├── .env.example
├── README.md            # corto, alto impatto: pitch, quick start, screenshot/GIF
└── OVERVIEW.md          # dettagli tecnici approfonditi
```

## Testing

- TDD sui componenti core (extractors, analyzer, report generator), ciascuno mockabile/
  isolabile
- `DocumentAnalyzer` testato mockando la chiamata Azure OpenAI (nessun costo/dipendenza
  esterna nei test unitari)
- Test di integrazione sulla pipeline completa usando i file in `examples/`
- Coverage minima enforced in CI

## CI/CD

Riuso del pattern Progetto 1: GitHub Actions — lint → unit test → integration test →
docker build → push GHCR. Deploy Azure (Bicep) resta uno step manuale/demo separato dalla
CI automatica di default, coerente con "zero costo di deploy stabile" (si fa il deploy per
mostrare la demo, poi tear-down del resource group).

## Documentazione

- `docs/YYYY-MM-DD-topic.md`: un file per ogni feature/commit-push rilevante, stesso schema
  di TaskFlow (Context / What changed / Known gap / Verification)
- `docs/adr/000X-topic.md`: decisioni architetturali di fondo
- Nessuna cartella `specs/` o `contracts/` separata

## Known gaps (accettati per questo stage)

- OCR e parsing email rimandati a Fase 2 (vedi sopra)
- Nessuna autenticazione/rate-limiting sull'endpoint pubblico — accettabile per un tool
  stateless a costo zero senza dati persistiti, da rivalutare se il traffico reale lo
  richiedesse
