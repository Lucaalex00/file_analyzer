# Redesign: il workspace "libro" che si popola a tappe

**Contesto:** richiesta dell'utente di rendere il sito più immersivo e più
"da prodotto", pensando a chi deve valutare a colpo d'occhio cosa
l'applicazione sa fare: *"immagina come fosse un libro che quando gli
inserisci dentro un documento si popola SOPRA con il testo grezzo preso
dall'OCR, A SINISTRA con il reale documento aperto in preview e A DESTRA con
la reale spiegazione dell'IA"*.

Due decisioni concordate prima di partire:

1. il nuovo layout **sostituisce** le tre sezioni accordion esistenti
   (Testo estratto / Analisi / Report) invece di aggiungersi ad esse;
2. il PDF generato resta **scaricabile ma non più in anteprima** nel flusso
   normale, perché il pannello di destra mostra già la stessa spiegazione in
   forma leggibile.

## Cosa è cambiato

**Layout (`frontend/index.html`, `styles.css`)**

Un unico `#workspace` con tre zone:

- fascia alta a tutta larghezza: testo grezzo estratto (con i punti di
  attenzione evidenziati dopo l'analisi);
- colonna sinistra: il documento originale renderizzato davvero;
- colonna destra: la spiegazione dell'IA.

Le zone sono card con ombra, bordo che si accende in hover e un leggero
sollevamento; i punti di attenzione scorrono di lato in hover; il pulsante
"Scarica PDF" è diventato un vero bottone pieno. Tutte le animazioni sono
disattivate sotto `prefers-reduced-motion`.

**Riempimento progressivo (`frontend/app.js`)**

Il workspace si apre alla selezione del file e si riempie per tappe, non
tutto insieme alla fine:

1. selezione del file → si apre il workspace, il documento originale appare
   subito (viene dal file, non serve il server) e la fascia alta mostra uno
   **skeleton animato** mentre `/extract` lavora;
2. `/extract` risponde → il testo grezzo prende il posto dello skeleton;
3. click su "Analizza" → il pannello destro passa allo skeleton;
4. l'IA risponde → la spiegazione entra in dissolvenza e compaiono i
   pulsanti di download.

Il pannello analisi è una piccola macchina a stati (`setAnalysisState`) con
quattro stati: invito a iniziare, caricamento, spiegazione, report salvato.

**Pannello documento adattivo — scoperto durante la verifica visiva**

Con un `.txt` la fascia alta e il pannello sinistro mostravano *lo stesso
identico testo*: ridondanza che sembra un bug. Ora il pannello del documento
compare solo per i file che il browser sa davvero renderizzare (PDF e
immagini); per `.txt`/`.docx`/`.eml` il testo estratto in alto **è** già il
documento, quindi quella colonna sta giù e la spiegazione si prende tutto lo
spazio.

**Cronologia**

Una voce di cronologia salva solo il PDF generato (non il file originale, non
l'analisi), quindi riaprirla mostra il report da solo, con le altre due zone
nascoste e il titolo della zona che diventa "Report generato".

## Bug reali trovati e corretti strada facendo

- **Altezze delle zone ignorate.** `flex: 1` sul corpo della zona faceva
  risolvere l'altezza dal contenuto, sovrascrivendo silenziosamente le
  altezze fisse: i pannelli crescevano a dismisura invece di scorrere, e il
  "libro" diventava una pagina lunghissima. Risolto con `flex: 0 0 auto`
  (commentato nel CSS, perché è esattamente il tipo di riga che qualcuno
  "ripulirebbe" per sbaglio).

## Verifica

- e2e Playwright: 23 test verdi, inclusi i nuovi
  "the workspace fills in progressively as each stage completes",
  "lays out raw text above the document and the analysis side by side"
  (con un PDF, verificando anche le posizioni relative dei riquadri) e
  "skips the document pane for files the raw text already shows in full".
- Backend: 372 test verdi. Unit frontend: 12 verdi.
- Verifica visiva reale con Playwright su tema chiaro e scuro, sia con `.txt`
  sia con un PDF vero (riusando un report generato come documento di input).
