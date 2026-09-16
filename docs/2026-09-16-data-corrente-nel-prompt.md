# 2026-09-16 — La data di oggi nel prompt

## Context

Aggiungendo un CV reale tra i documenti di esempio, l'analisi ha segnalato
come "date future" delle certificazioni datate marzo-maggio 2026 — passate da
mesi rispetto al giorno in cui girava. Il difetto non era il CV: il prompt non
ha mai detto al modello **che giorno è oggi**, quindi ogni giudizio su
scadenze, validità e imminenza veniva dato rispetto al training cutoff del
modello.

Vale ben oltre i CV. Capire se il termine di un contratto è scaduto, se un
preavviso di 60 giorni è ancora nei tempi o se una penale è ormai
inapplicabile è esattamente il mestiere di questo strumento, ed è tutta
aritmetica su una data che il modello non aveva.

## What changed

`build_user_prompt()` (`src/analyzer/prompts.py`) accetta ora un parametro
`today` (default `date.today()`) e inserisce nel prompt la data corrente in
formato ISO, chiedendo esplicitamente di valutare contro di essa se una
scadenza è passata, imminente o lontana e se un termine o un certificato è
scaduto o valido.

Il parametro è iniettabile apposta: rende il test deterministico senza
congelare l'orologio di sistema.

## Known gap

Il modello riceve la data ma resta un LLM: non fa aritmetica sulle date in
modo affidabile su casi complessi (mesi con lunghezze diverse, giorni
lavorativi, fusi orari). Il prompt gli dà il riferimento che prima mancava,
non una garanzia di calcolo corretto.

La stessa data non viene passata al confronto tra documenti
(`build_comparison_user_prompt`): lì il giudizio è su cosa è cambiato tra due
versioni, non su quanto manca a una scadenza, quindi per ora non serve.

## Verification

Due test in `tests/unit/test_document_analyzer.py`: che la data iniettata
compaia nel prompt e che di default compaia quella reale.

Verificato anche sul campo: rieseguita l'analisi dello stesso CV, le
segnalazioni di "date future" sono sparite e sono rimaste quelle legittime
(sovrapposizioni reali tra periodi dichiarati).
