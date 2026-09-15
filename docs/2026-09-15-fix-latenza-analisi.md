# Fix: analisi troppo lenta (oltre 30s)

**Contesto:** l'utente ha segnalato che l'analisi impiegava troppo, oltre i
30s. Verificato che il tempo è quasi interamente la chiamata AI: `gpt-5-mini`
è un modello "reasoning" e, di default, usa uno sforzo di ragionamento medio
prima di rispondere -- il resto della pipeline (estrazione testo,
generazione PDF) è pressoché istantaneo.

## Fix

Aggiunto `extra_body={"reasoning_effort": "low"}` alla chiamata
`chat.completions.create` sia in `DocumentAnalyzer` che in
`DocumentComparator`. Usato `extra_body` invece del parametro nominale
`reasoning_effort` perché l'SDK `openai==1.51.0` pinnato nel progetto non lo
espone ancora come kwarg diretto su `create()` -- `extra_body` inoltra il
campo grezzo nel body della richiesta indipendentemente dalla versione
dell'SDK.

`DemoAIClient._FakeCompletions.create` aggiornato per accettare il nuovo
kwarg `extra_body` (prima il fake aveva una firma rigida senza `**kwargs`,
quindi la chiamata reale sarebbe fallita in modalità demo).

## Verifica

Misurato con `docker compose exec api python -m scripts.generate_examples`
contro Azure OpenAI reale:

- Prima: ~24-25s per chiamata AI (vedi
  [2026-09-15 — Fix: script di generazione esempi](2026-09-15-fix-script-esempi.md))
- Dopo: ~12-14s per chiamata AI -- circa dimezzato

Suite di test completa (368 test, inclusi i 2 nuovi che verificano
`reasoning_effort="low"` sulla chiamata) verde.
