# Fix: asset statici (CSS/JS) senza header di cache, browser mostravano versioni vecchie

**Contesto:** dopo il deploy della [barra di progresso](2026-09-15-barra-progresso-attesa.md),
l'utente ha segnalato che sulla demo pubblica la barra appariva "schiacciatissima
di fianco al testo di caricamento" invece che a tutta larghezza sotto di esso.

## Diagnosi

Verificato visualmente (Playwright) che il markup e il CSS, quando caricati
freschi, renderizzano correttamente: barra a tutta larghezza, sotto la riga
spinner+testo. Controllando gli header HTTP di `/static/styles.css`, nessun
`Cache-Control` era presente -- solo `ETag`/`Last-Modified`. Senza
`Cache-Control` esplicito, i browser applicano una cache euristica (RFC 7234)
basata su `Last-Modified` e possono continuare a servire una versione vecchia
di CSS/JS dalla cache locale **senza nemmeno controllare col server**, anche
dopo un redeploy. L'utente aveva il sito già visitato più volte oggi durante
i test precedenti, quindi il suo browser aveva probabilmente in cache il CSS
di prima del deploy della barra di progresso (dove `#status` era ancora
`display: flex` in riga, non colonna) -- da cui l'effetto "schiacciata di
fianco al testo".

## Fix

Aggiunto un middleware in `src/api/main.py` che imposta
`Cache-Control: no-cache` su tutte le risposte sotto `/static/`. Questo non
disabilita la cache (il browser tiene comunque la copia locale) ma forza una
revalidazione col server ad ogni caricamento (richiesta condizionale con
`If-None-Match`/ETag, risposta `304 Not Modified` se il file non è cambiato)
-- quindi dopo ogni deploy futuro i client vedranno subito gli asset
aggiornati, con un costo trascurabile (un round-trip in più, niente
ri-scaricamento se il contenuto è invariato).

## Verifica

Nuovo test `test_static_assets_are_served_with_no_cache_so_browsers_always_revalidate`
in `tests/integration/test_static_cache_headers.py`. Suite completa: 372 test
verdi. Verificato dal vivo con Playwright che `/static/styles.css` ora
risponde con `Cache-Control: no-cache`.
