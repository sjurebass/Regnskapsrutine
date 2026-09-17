# Uttrekk av åpne poster fra Tripletex – Automatisk bankavstemming (Claude i Chrome)

Mekanikken for å lese uavstemte poster fra bankavstemmingssiden. Klient-uavhengig:
`contextId` og `accountId` oppdages per klient i økten. Bruk **kun lesemodus** –
aldri matche, lukke, endre eller slette noe.

---

## ⚡ Rask metode (bruk denne) – URL-navigasjon + browser_batch

Ikke klikk deg gjennom måneds-faner og screenshots. Naviger direkte via URL og
hent alle måneder for en konto i **ett** `browser_batch`-kall.

### Forberedelser (last verktøy i ETT ToolSearch-kall)
```
select:mcp__claude-in-chrome__tabs_context_mcp,mcp__claude-in-chrome__navigate,
mcp__claude-in-chrome__computer,mcp__claude-in-chrome__javascript_tool,
mcp__claude-in-chrome__browser_batch
```
(Ikke nødvendig med read_page/screenshot i lesemodus – bruk JS-uttrekket.)

### Steg 1 – Bytt inn i klienten, finn contextId
Naviger til `https://tripletex.no/page/bank/reconciliation`. Er du i regnskaps-
byråets egen kontekst («Ingen tilgang»), klikk selskaps-velgeren oppe til venstre,
søk opp klienten og velg den. **Klienten åpnes i en NY fane** med egen `contextId`
i URL-en (f.eks. `?contextId=1439297`). Jobb videre i den nye fanen. Les
`contextId` fra fanens URL (tab-context), ikke fra JS.

### Steg 2 – Finn accountId per konto (engangs, cache dem)
`accountId` ligger **ikke** lesbart i DOM (attributter redigeres bort av broen,
se Fallgruver). Hent dem slik, én gang per klient:
1. Åpne konto-velgeren (dropdown ved siden av søkefeltet).
2. Klikk en konto → URL-en får `&accountId=<id>`. Les `accountId` fra
   **tab-context-URL-en** i verktøysvaret (ikke via `location.href` i JS – blir blokkert).
3. Gjenta for hver konto. **Hopp over skattetrekkskontoen (typ. 1950).**

accountId-ene er stabile per klient – noter dem i økten og gjenbruk for alle
måneder. (Kjente eksempler er klient-spesifikke; må hentes på nytt per klient.)

Sørg for at filteret **«Ikke matchet»** er aktivt (blå). Det henger med i økten;
klikk det én gang om nødvendig. `type=unmatched` i URL trengs ikke.

### Steg 3 – URL-mønster
```
https://tripletex.no/page/bank/reconciliation?contextId={ctx}&period={start}%2C{slutt}&accountId={acc}
```
- `period` = første i måneden + første i NESTE måned, komma URL-encodes som `%2C`.
  Juni 2026 → `2026-06-01%2C2026-07-01`. Juli → `2026-07-01%2C2026-08-01`.

**Vi trenger som regel bare BANKSIDE-poster** (i bank, mangler bilag). Tripletex-
side (bokført, ikke sett i bank – ofte timing) tas normalt ikke med; generatoren
filtrerer dem bort som standard. Du kan derfor lese kun høyre side, men det er
greit å ta med begge i uttrekket.

### Steg 4 – Hent alle måneder for en konto i ETT browser_batch
For hver konto: kjør navigate → **wait ~6s** → JS-uttrekk, én sekvens per måned, alt
i samme `browser_batch`. JS-uttrekket returnerer **kun** radtekst (trygt), aldri URL.

⚠️ **Vent lenge nok (6 s), ellers mister du poster.** Tunge kontoer (mange
transaksjoner, Stripe/plasseringskonto) laster tregt. Leser du for tidlig får du
enten en **skjelett-visning** («lorem ipsum» / «amount lorem ipsum»-rader) eller
**tom `[]`** selv om måneden har poster. La uttrekks-JS returnere et `skel`-flagg
(sjekk `document.body.innerText` mot `/lorem ipsum/i`); er `skel:true` eller
uventet tomt på en konto du tror har poster – naviger på nytt og vent lenger før du
konkluderer. Ikke stol på et raskt `[]`.

Uttrekks-JS (kompakt, med skjelett-vakt; brukes som `text` i hvert javascript_tool-steg):
```javascript
(function(){const mid=innerWidth/2;const skel=/lorem ipsum/i.test(document.body.innerText);
const out=Array.from(document.querySelectorAll('.pbc-entries-table')).map(t=>{
const r=t.getBoundingClientRect();
return{side:(r.left+r.width/2)<mid?'TX':'BANK',
rows:Array.from(t.children).slice(1).map(c=>c.innerText.trim().replace(/\s+/g,' '))}});
return JSON.stringify({skel,out})})()
```
Trenger du bare bankside: filtrer `out` på `side==='BANK'` før du bruker radene.
Batch-eksempel (én konto, juni+juli):
```
browser_batch([
 {navigate: URL(ctx, "2026-06-01%2C2026-07-01", acc)},
 {computer: wait 2s},
 {javascript_tool: <uttrekks-JS>},
 {navigate: URL(ctx, "2026-07-01%2C2026-08-01", acc)},
 {computer: wait 2s},
 {javascript_tool: <uttrekks-JS>},
])
```
Svaret gir uttrekkene i rekkefølge. `[]` = ingen åpne poster den måneden.
`side:"TX"` = venstre = **Tripletex-side** (bokført, ikke sett i bank).
`side:"BANK"` = høyre = **Bankside** (i bank, mangler bilag).

Kjør ett batch-kall per konto (eller slå sammen flere kontoer i ett kall hvis få
måneder). Ingen screenshots trengs – gå rett til `data.json`.

---

## Sideoppslag (om du likevel tar screenshot)
| DOM-signal | Betydning |
|---|---|
| «Perioden er avstemt og lukket» | Lukket periode – ingen uavstemte poster |
| «Perioden er avstemt og kan lukkes.» | Åpen, i balanse – ingen uavstemte poster |
| Tom `.pbc-entries-table`-liste (`[]`) | Ingen uavstemte poster den måneden/siden |
| Avvik ≠ 0 men ingen rader | Saldo-avvik uten enkeltposter (f.eks. verdipapirkonto uten bankfeed) – ingen post å dokumentere, nevn det kort til bruker |

## Radformat
```
2026-06-12 −590,00 ZETTLE_*TICKETCO NORGE
2026-06-08 5 060,50 Oase Of Norway AS | Detaljer: Fylt på
```
Felt: `dato (YYYY-MM-DD)` · `beløp (− foran for debet, mellomrom som tusenskille)` ·
`beskrivelse`. `generer_excel.py` tar rå-strenger via `"raw"` og tolker formatet.

## Fallgruver
- **Broen blokkerer URL-/id-lignende output**: `location.href`, element-attributter
  med id-er, og lange token-strenger returneres som «[BLOCKED: Cookie/query string
  data]». Derfor: les `contextId`/`accountId` fra **tab-context-URL-en**, og la
  JS-uttrekket returnere kun radtekst.
- **Navigasjon nullstiller nettverkslogg** – ikke stol på read_network_requests for
  å finne API-et; Tripletex sitt interne API fanges ikke pålitelig, og svar ville
  uansett bli redigert. URL-navigasjon er den robuste veien.
- «Fylt på»-poster (kortpåfyll) og bank-/kortgebyr krever ingen dokumentasjon –
  generatoren filtrerer dem bort automatisk. Ta dem gjerne med.
- Identiske rader (mange × −76,00 Posten) er **ekte** dubletter – ikke fjern dem.
- Vent ~2 s etter hver navigasjon før uttrekk; leser du for tidlig er tabellen tom.

## recalc.py-sti
Ligger ulikt per miljø. Finn den: `find / -name recalc.py 2>/dev/null` – ofte
`/root/.claude/skills/xlsx/scripts/recalc.py` eller `/mnt/skills/public/xlsx/scripts/recalc.py`.
