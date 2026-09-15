# Fix: `scripts/generate_examples.py` non era mai stato eseguibile

**Contesto:** per la mandate "se vedi altro da sistemare, fallo autonomamente"
data dall'utente dopo il lavoro su Azure OpenAI/Groq/guardrail, ho fatto un
audit del repo cercando problemi reali non ancora notati. Lo script
`scripts/generate_examples.py`, documentato in `examples/README.md` come il
modo per rigenerare i due PDF di esempio contro un vero provider AI, non
aveva mai funzionato.

## Problemi trovati

1. `scripts/` è escluso dall'immagine Docker (vedi `.dockerignore`) e non era
   montato come volume in `docker-compose.yml` -- quindi
   `python scripts/generate_examples.py` falliva subito con
   `can't open file '/app/scripts/generate_examples.py'`.
2. Anche montando `scripts/`, l'invocazione diretta (`python
   scripts/generate_examples.py`) falliva con `ModuleNotFoundError: No
   module named 'src'`, perché Python mette la directory dello script (non
   `/app`) in cima a `sys.path` in quella modalità di esecuzione.

## Fix

- Aggiunti `./scripts:/app/scripts` e `./examples:/app/examples` ai
  `volumes:` di `docker-compose.yml`.
- Creato `scripts/__init__.py` (vuoto) per rendere `scripts` un package
  Python vero, così l'esecuzione con `python -m scripts.generate_examples`
  risolve correttamente `from src...`.
- Aggiornato `examples/README.md` con il comando corretto:
  `docker compose exec api python -m scripts.generate_examples`.
- Aggiunta la riga mancante `examples/*.report.pdf` a `.gitignore` -- i PDF
  generati non erano mai stati effettivamente esclusi da git, solo
  documentati come "non committati" in `examples/README.md`.

## Verifica

Eseguito per davvero: `docker compose exec api python -m
scripts.generate_examples` ha generato due PDF reali contro Azure OpenAI
(`gpt-5-mini`, ~24-25s per chiamata), confermando anche che il tracing delle
chiamate AI (vedi
[2026-09-08 — AI call tracing](2026-09-08-ai-call-tracing.md)) funziona
correttamente in uso reale. PDF cancellati dopo il test, come da policy
documentata in `examples/README.md`.

Suite di test completa (183 test) rieseguita dopo il fix batch: verde.
