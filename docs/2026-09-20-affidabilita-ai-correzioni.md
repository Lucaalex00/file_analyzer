# 2026-09-20 — Quattro correzioni allo strato di affidabilità AI

## Context

Audit dello strato di "AI reliability" contro sei domande: validazione
dell'output, retry e fallback, discrepanze fra regole e modello, eval e
regression test, osservabilità, limiti documentati. Il risultato era
discreto — schema Pydantic applicato ovunque, retry limitato con errore
esplicito, doppia fonte di rilevamento, tracing attento alla privacy, limiti
dichiarati — ma con quattro difetti concreti, di cui due che producevano
output sbagliato in produzione.

## What changed

**La deduplica fra regole e modello non funzionava fuori dall'italiano.**
I due insiemi di flag venivano uniti deduplicando per titolo esatto, ma il
titolo del modello è testo libero *tradotto nella lingua richiesta*, mentre
quello delle regole è una stringa fissa italiana: in inglese la collisione
non avveniva mai e ogni rischio visto da entrambe le fonti compariva due
volte. Ora la fusione avviene sul **passaggio citato** — l'unica cosa che le
due fonti esprimono allo stesso modo in qualunque lingua. Dove coincidono
sopravvive il testo del modello (specifico) invece di quello della regola
(boilerplate), ma vince la severità più alta: una regola che marca `high`
una penale non deve essere ammorbidita da un modello che la valuta `low`.
`RedFlag` ha ora un campo `source` (`llm` / `rule` / `both`), che è anche la
risposta alla domanda "cosa fa il sistema quando le due fonti divergono":
lo dichiara invece di nasconderlo.

**Una risposta malformata costava l'intera richiesta.** Gli errori di
validazione interrompevano il ciclo al primo tentativo, con il commento
"a bad response won't fix itself on retry" — affermazione discutibile per un
modello stocastico, dove la stessa domanda al secondo tentativo spesso
produce JSON valido. Ora vengono ritentati come qualunque altro errore,
entro lo stesso limite. Identico nel comparatore.

**Le citazioni non erano verificate, e la verifica ingenua era peggio del
problema.** Il prompt chiede citazioni verbatim e lo schema non può
controllarlo: una citazione inventata passava, finiva nel report e non
evidenziava nulla, in silenzio. Misurato sui tre documenti di esempio: **9
citazioni su 14 non erano sottostringhe esatte del testo.** Ma il primo
tentativo di correzione — scartare tutto ciò che non combacia — si è
rivelato sbagliato: verificando caso per caso, quelle citazioni erano
**autentiche**, e fallivano solo perché il testo estratto contiene a capo
forzati (colonne PDF, righe OCR) in punti dove il modello non li riproduce.
Scartarle avrebbe peggiorato l'explainability invece di sistemarla.

La correzione giusta (`src/analyzer/quote_grounding.py`) confronta a spazi
normalizzati e poi **riallinea la citazione al testo reale del documento**,
perché il frontend evidenzia cercando la sottostringa esatta: una citazione
giusta ma con un a capo diverso non evidenzia niente. Solo ciò che non si
trova nemmeno normalizzato perde la citazione e viene contato nei log.
Risultato misurato sugli stessi documenti: da 5 citazioni evidenziabili su
14 a **8 su 10**.

**Token e citazioni scartate nei log.** `completion.usage` veniva scartato:
il costo non era misurabile e il tetto orario contava le chiamate, trattando
come equivalenti un documento da 80.000 caratteri e una nota di una riga.
Ora `log_ai_attempt` registra prompt/completion/total token e il numero di
citazioni non ancorate.

## Known gap

Sul CV in PDF 2 citazioni su 3 restano non recuperabili, verosimilmente
perché attraversano il layout a due colonne e nel testo estratto non
esistono come sequenza contigua. La normalizzazione degli spazi non può
niente contro un riordino di blocchi.

Il tetto orario **conta ancora le chiamate, non i token**: ora i token sono
misurati, ma il budget non li usa.

Nessun backoff fra i tentativi: i retry restano immediati, quindi su un 429
del provider i tre tentativi colpiscono lo stesso limite.

## Verification

228 test verdi (13 nuovi: fusione per passaggio citato, severità
conservativa, provenienza, retry su output malformato per analyzer e
comparatore, riallineamento delle citazioni, token nei log). `ruff` pulito.

Misure reali contro Azure OpenAI sui tre documenti di esempio, prima e dopo,
riportate sopra — sono il motivo per cui la prima versione della correzione
sulle citazioni è stata buttata.
