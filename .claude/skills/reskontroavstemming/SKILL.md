---
name: "reskontroavstemming"
description: "Avstemming av kunde- og leverandørreskontro i Tripletex: 1500 og 2400 mot hovedbok, vurdering av hver åpen post i året (forfalt, purring, tap, feil fortegn), tiltaksliste og kontoutskrift per motpart. Lukker Tally-oppgavene «Avstemming kundereskontro», «Avstemming leverandørreskontro» og «Gjennomgang kunde- og leverandørreskontro». Bruk ved «avstem reskontro», «reskontroavstemming», «avstem kundereskontro», «avstem leverandørreskontro», «åpne poster kunder», «åpne poster leverandører», «forfalte fakturaer», «hvem skylder <klient> penger», «kontoutskrift kunde»."
---

# Reskontroavstemming

Avstemming av kunde- og leverandørreskontro per siste dag i måneden: sum åpne poster mot 1500 og 2400, vurdering av hver åpen post datert i året,
tiltak som krever ja, og kontoutskrift per motpart. Bank er `bankavstemming`; andre balansekontoer er `balanseavstemming`; poster fra før året
tas enkeltvis i `aarsoppgjoer-forberedelse`. `mva-kontroll` leser resultatet for terminens siste måned.

## Når

- Tally-oppgavene «Avstemming kundereskontro» og «Avstemming leverandørreskontro» (den 20., for forrige måned) og «Gjennomgang kunde- og leverandørreskontro».
- Ferdig først: «Bilagsbehandling» og «Bankavstamming» for måneden. Ellers blir «betalt etter» og forfalt feil.
- Brukeren oppgir klient og periode `ÅÅÅÅ-MM` (standard forrige måned); D = første dag etter perioden. Kontoutskrift: motparten med nummer eller org.nr.
- Steg 0 i tillegg: Missive (spørsmål til kunden).

## Kundeinstruks

«Regnskapssystem og byrå» (V) · «Reskontro og balanse» (purrerutine, inkasso, tapsvurdering, avrundingskonto) · «Bilagsføringsregler» (betalingsløsninger)
· «Kjente avvik» · «Årsoppgjør». Mangler «Reskontro og balanse»: avrundingskonto 7740, purrerutine «ikke avklart».

## Steg

### 1. Kontoer
`get_accounting_settings` → reskontrokontoene (standard 1500 og 2400). Bare de avstemmes; andre 15xx/24xx med saldo blir én linje til `balanseavstemming`.

### 2. Data – ett `tripletex_run_script`
- `get_balance_sheet` 1500–1599 og 2400–2499 fra 1.1 til D (eksklusiv) → UB per konto, og UB 1580.
- `search_open_postings` per D for begge kontoene: id, dato, forfall, beløp, fakturanr., bilag, motpart (id, navn, org.nr., privatperson).
- `search_open_postings` per i morgen, bare id → hvilke poster som fortsatt er åpne. `search_supplier_invoices` (fra 1.1) → forfall på 2400.
- Første kjøring på en klient: ett representativt kall først for å se feltnavnene.

### 3. Sum mot hovedbok (R1, R2, R9)
Σ åpne poster per D mot UB. Differanse ≥ 1 kr → let etter poster på reskontrokontoen uten motpart (R9) og utligning på tvers av D.

### 4. Vurder hver åpen post (R3–R8, R10–R12)
Kategoriser **nøyaktig etter `references/kategorier.md`** (rekkefølge, etiketter, nullgrupper, terskler). Kortversjon: betalt/utlignet etter → kan utlignes
→ småbeløp → ufordelt innbetaling/kreditnota (1500) eller betaling uten faktura (2400) → ikke forfalt → 1–30 → 31–90 → over 90 dager.
Poster datert før året er én samlelinje.
- Brreg (Tally `lookup_brreg` eller `lookup_company_in_brreg`) bare for motparter med org.nr. som krever oppfølging.
- `search_reminders` (fra 1.1) → purretrinn for kunder forfalt over 30 dager.
- Feil fortegn per motpart (R3), dubletter blant åpne poster (R6) og 1580 mot postene til tapsvurdering (R12) etter tersklene i referansen.

### 5. Kjente avvik
Nøkkel `konto · motpart · beløp` fra kundeinstruksen → «kjent, uendret». Nytt beløp er nytt funn.

### 6. Tiltak – nummerert, hvert punkt krever ja
1. Utligning av nullgrupper og småbeløp (differansen til avrundingskontoen).
2. Purring eller inkasso per kunde med purretrinn. Tally `lag_purring` lager utkast etter ja; kunden eller regnskapsføreren sender.
3. Tap og avsetning: tapsføring bare ved konstatert tap (da kreves utgående mva tilbake, mval. § 4-7). Konkurs alene gir avsetning i 1580, ikke tap.
4. Ompostering: innbetaling fra Skatteetaten på 2400 → riktig konto (for eksempel 2600). Dobbeltbetaling til leverandør → krav om tilbakebetaling.
5. Spørsmål til kunden (ufordelte innbetalinger, betaling uten faktura) → Missive-utkast etter ja.

**Krever skriving utenfor MCP: Tripletex-UI (eller API-kobling):**
1. Utlign postene i reskontroen (finner ToolSearch et verktøy for å lukke poster, brukes det etter ja).
2. Før tap, avsetning og omposteringer som bilag, alltid med dokumentasjon.
3. Last opp arbeidsboka på linjene 1500 og 2400 i avstemmingsmodulen (BALANCE for måneden); sett dokumentert saldo og status etterpå.

### 7. Kontoutskrift per motpart (R13)
På forespørsel, og automatisk for kunder med poster forfalt over 30 dager. Mønster: `silfer-rapport/scripts/eksempler/kontoutskrift_reskontro.json`.
1. IB og UB uavhengig av bevegelsene: `get_balance_sheet` med `customerIds` (leverandør: tilsvarende filter) fra 1.1 til D.
2. Bevegelser: `search_ledger_postings` på kontoen for perioden, filtrert på motparten i skriptet (det finnes ikke kundefilter), sortert på dato.
   Mangler raden kunden, lages ingen PDF: «krever API-kobling».
3. Bevegelser: Dato · Bilag · Tekst · Forfall · Fakturert · Innbetalt (leverandør: Betalt) · Saldo, fra «Inngående saldo» med løpende saldo til «Utgående saldo».
   Fakturarader (kreditnota negativ) er Fakturert, alle andre Innbetalt. Leverandør: fortegn snudd, så gjelden vises positiv.
4. «Åpne poster per <siste dag>»: Dato · Forfall · Fakt.nr. · Tekst · Beløp, med «Sum åpne poster» lik utgående saldo.
5. Kontrollinje: «Kontrollert: inngående saldo X + fakturert Y − innbetalt Z = utgående saldo W, som stemmer».
   **Stemmer ikke summen med uavhengig UB, lages ikke PDF-en.** Rapporter differansen som R13.

## Svar

- Første linje: port · R1/R2-differanse · antall åpne poster og sum per konto.
- Kategoritabell per konto (Kategori · Poster · Beløp), så motpartene som krever oppfølging i funn-formatet (høyst 5 per konto, størst først).
- Nummerert ja-liste til slutt, og hva som ikke ble lest (for eksempel forfall på leverandørposter).
- Firmanavn er greit; privatpersoner står som «privatkunde n». Ingen posteringstekster i chatten.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `BILAG`, periode `ÅÅÅÅ-MM`, samling `Reskontro ÅÅÅÅ`, oppgave «Avstemming kundereskontro»): `Reskontroavstemming ÅÅÅÅ-MM <Klient>.xlsx` med arkene Sammendrag (port, R1/R2, kategoritabell per konto, 1580) · Kunder · Leverandører · Tiltak (med «Krever»).
Kontoutskrift: `Kontoutskrift kundereskontro <kundenr.> ÅÅÅÅ-MM <Klient>.pdf` (leverandør tilsvarende; nummer, ikke navn), kategori `BILAG`, samling `Reskontro ÅÅÅÅ`, oppgave «Gjennomgang kunde- og leverandørreskontro».
Fullfør i Tally: se `tally-gjoremal`. «Avstemming kundereskontro» og «Avstemming leverandørreskontro» fullføres når R1/R2 er 0 og hver post som krever oppfølging har en beslutning; «Gjennomgang kunde- og leverandørreskontro» når tiltakslista er avgjort. Kommentaren inneholder periode, port, differanse, antall poster til oppfølging og tiltak som venter.

## Fallgruver

- `search_open_postings`: datoen er eksklusiv (bruk D, ikke siste dag). Forfall og dager forfalt finnes bare på kunderader.
- `search_ledger_postings` har leverandørfilter, men ikke kundefilter, og radene kommer i bilagsrekkefølge. Filtrer og sorter i skriptet.
- «Betalt etter» krever to uttrekk med samme kontoer: per D og per i morgen.
- Nullgrupper søkes bare blant poster som er åpne i dag; grupper på 3 eller flere bare når motparten har høyst 16 slike poster.
- Konstatert tap er ikke det samme som konkurs. Tapsføring endrer mva og avgjøres av regnskapsfører.
- Kontoutskrift til en privatperson lages bare når brukeren ber om den.
- Reskontrostatus «gjennomgått» settes bare i Tripletex-UI.

## Referanser

Kontroller: R1–R13 (`docs/kontrollkatalog.md`; bokførte dubletter er R6 i `bilagskontroll`). Kategorier og terskler: `references/kategorier.md`.
Mønster: `.claude/skills/silfer-rapport/scripts/eksempler/kontoutskrift_reskontro.json`.
Naboskills: `bankavstemming`, `balanseavstemming`, `mva-kontroll`, `aarsoppgjoer-forberedelse`, `kundeinstruks`, `tally-gjoremal`.
