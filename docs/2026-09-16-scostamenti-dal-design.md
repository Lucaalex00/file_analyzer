# 2026-09-16 — Scostamenti dal design iniziale

## Context

Verifica del progetto così com'è oggi contro
[il design del 2026-08-27](2026-08-27-file-analyzer-design.md), per capire
cosa è stato rispettato, cosa è cambiato deliberatamente e cosa era invece
andato alla deriva senza che nessuno lo scrivesse.

Il grosso del design regge: stack, componenti (`extractors/`, `analyzer/`,
`report/`, `pipeline.py`, `api/`), statelessness, assenza di autenticazione,
rilevamento automatico del contesto, error handling (415/413, estrazione
fallita esplicita, retry poi 502, validazione Pydantic), avvio con un
comando, struttura del repo, TDD con Azure OpenAI mockato, coverage all'80%
imposta in CI, pipeline CI lint → test → build → push GHCR. La Fase 2 è
stata completata per la parte OCR ed `.eml`, aggiunta come previsto con
nuove implementazioni di `BaseExtractor` senza toccare analyzer, report o
pipeline.

## What changed

**Azure Functions → Azure Container Apps.** WeasyPrint ha bisogno di
librerie di sistema (pango, cairo) che il piano Consumption di Functions non
permette di installare. Il design prevedeva Functions; l'obiettivo vero
(deploy su Azure a costo quasi nullo, con IaC) è rimasto, la tecnologia no.
Vedi [`infra/README.md`](../infra/README.md) e
[2026-09-14](2026-09-14-deploy-azure-container-apps.md).

**Rate limiting e tetto di spesa, che il design escludeva.** Il documento
diceva "nessuna autenticazione/rate-limiting … da rivalutare se il traffico
reale lo richiedesse". È stato rivalutato: un link pubblico collegato a un
modello a pagamento va protetto comunque, quindi c'è un limite per IP e un
tetto orario globale sulle chiamate AI
([2026-09-16](2026-09-16-demo-per-chi-valuta.md)).

**Interfaccia web.** Il design descriveva solo `POST /analyze` con risposta
PDF. L'endpoint esiste ancora identico ed è il contratto stabile per
curl/CLI, ma sopra ci è cresciuta una UI completa. Non era previsto: è nato
dal bisogno di far vedere il progetto a chi non usa un terminale.

**Tre provider AI invece di uno.** Il design dava Azure OpenAI per scontato.
Oggi la catena è Azure OpenAI → Groq → demo mode, nata mentre la quota Azure
era bloccata e rimasta perché rende il progetto eseguibile da chiunque senza
credenziali.

**I PDF di esempio, ora rimessi a posto.** Il design chiedeva `examples/`
con i report già generati, "così il repo è esplorabile anche senza chiavi
Azure configurate". Erano finiti in `.gitignore`. L'intento era coperto
altrimenti (demo mode, demo pubblica), ma il requisito letterale no: ora i
report sono committati.

## Known gap

**Lo schema di questi documenti è andato alla deriva.** Il design fissava
*Context / What changed / Known gap / Verification*, lo stesso di TaskFlow.
Le voci di settembre usano una struttura più libera (Contesto / Cosa è stato
fatto / Verifica) e spesso saltano "Known gap" — cioè proprio la sezione che
costringe a scrivere ciò che non funziona. Questo documento torna allo
schema originale; le voci passate restano come sono, perché riscriverle a
posteriori falserebbe un diario di bordo.

**`.msg` non è supportato.** Era in Fase 2 insieme a `.eml`. Il formato è
binario (OLE di Outlook) e non esiste un modo pratico di generare un `.msg`
valido da codice: servirebbe un file reale come fixture per poterlo
sviluppare in TDD. Resta dichiarato nella roadmap del README.

**Il README non è più "corto".** Il design lo voleva "corto, alto impatto:
pitch, quick start, screenshot/GIF"; oggi contiene anche tabella degli
endpoint, CLI, architettura, sviluppo e limiti noti. È una deviazione
consapevole che non verrà corretta: la sezione "Limitations" in particolare
è tra le parti che dicono di più a un lettore tecnico, e accorciare il README
per rispettare una riga di un documento di agosto peggiorerebbe il progetto.
Meglio registrare lo scostamento che obbedirgli.

## Verification

- Suite backend: 212 test verdi, coverage ≥ 80% imposta in CI.
- e2e Playwright: 28 test verdi. Unit frontend: 12.
- `ruff check src tests`: pulito.
- Report di esempio rigenerati contro Azure OpenAI reale e committati.
