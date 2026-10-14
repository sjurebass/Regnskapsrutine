---
name: "reskontroavstemming"
description: "Avstemming av kunde- og leverandørreskontro i Tripletex: 1500 og 2400 mot hovedbok, vurdering av hver åpen post i året (forfalt, purring, tap, feil fortegn), tiltaksliste og kontoutskrift per motpart. Lukker Tally-oppgavene «Avstemming kundereskontro», «Avstemming leverandørreskontro» og «Gjennomgang kunde- og leverandørreskontro». Bruk ved «avstem reskontro», «reskontroavstemming», «avstem kundereskontro», «avstem leverandørreskontro», «åpne poster kunder», «åpne poster leverandører», «forfalte fakturaer», «hvem skylder <klient> penger», «kontoutskrift kunde»."
---

# Reskontroavstemming

Avstemming av kunde- og leverandørreskontro per siste dag i måneden: sum åpne poster mot 1500 og 2400, vurdering av hver åpen post datert i året
med kategori og alder etter `docs/avstemmingsmetodikk.md`, tiltak som krever ja, og kontoutskrift per motpart. Bank er `bankavstemming`; andre
balansekontoer er `balanseavstemming`; poster fra før året tas enkeltvis i `aarsoppgjoer-forberedelse`. `mva-kontroll` leser resultatet for terminens siste måned.

## Når

- Tally-oppgavene «Avstemming kundereskontro» og «Avstemming leverandørreskontro» (den 20., for forrige måned; nivå 2 i `periodeavslutning`) og «Gjennomgang kunde- og leverandørreskontro».
- Ferdig først: «Bilagsbehandling» og «Bankavstamming» for måneden. Ellers blir «betalt etter» og forfalt feil.
- Brukeren oppgir klient og periode `ÅÅÅÅ-MM` (standard forrige måned); S = siste dag, D = første dag etter perioden. Kontoutskrift: motparten med nummer eller org.nr.
- Steg 0 i tillegg: Missive (spørsmål til kunden).

## Kundeinstruks

«Regnskapssystem og byrå» (V) · «Reskontro og balanse» (purrerutine, inkasso, tapsvurdering, avrundingskonto) · «Bilagsføringsregler» (betalingsløsninger)
· «Kjente avvik» · «Årsoppgjør». Mangler «Reskontro og balanse»: avrundingskonto 7740, purrerutine «ikke avklart».

## Steg

Alle kall med `--client "<klient>"`. `<mappe>` = kort arbeidsmappe (for eksempel `%TEMP%\rr\reskontro-ÅÅÅÅ-MM`); store svar går dit med `--ut`.

### 1. Kontoer
`npm run -s api -- GET /ledger/account ledgerType=CUSTOMER fields=number,name` (og `ledgerType=VENDOR`) → reskontrokontoene (standard 1500 og 2400).
Bare de avstemmes; andre 15xx/24xx med saldo blir én linje til `balanseavstemming`.

### 2. Data (API)
- UB: `npm run -s api -- GET /balanceSheet dateFrom=ÅÅÅÅ-01-01 dateTo=<D> accountNumberFrom=1500 accountNumberTo=1599 fields=account(number),balanceOut`
  (og 2400–2499) → UB per konto, og UB 1580.
- Åpne poster med kategori: `npm run -s modul -- reskontro-vurdering --client "<klient>" --dato <S> --json --ut <mappe>` → `<mappe>/reskontro-vurdering.json`
  per konto og motpart: id, dato, forfall, `dagerForfalt`, beløp, fakturanr., bilag, motpart (id, navn, org.nr., privatperson), åpen i dag, kategori og
  Brreg-status. Konsollen gir sammendraget per konto og kategori. Kommandoen lager også en Silfer-PDF i `<mappe>`.
- Rådata ved behov (2400 tilsvarende; samme kall per i morgen med `fields=id` gir postene som fortsatt er åpne):
  `npm run -s api -- GET /ledger/posting/openPost date=<D> accountNumberFrom=1500 accountNumberTo=1500 sorted=false fields=id,date,amount,invoiceNumber,termOfPayment,voucher(number,year),customer(id,name,organizationNumber,isPrivateIndividual),supplier(id,name,organizationNumber,isPrivateIndividual) --sider --ut <mappe>/1500.json`

### 3. Oppstilling mot hovedbok (R1, R2, R9)
UB 1500/2400 per S mot Σ åpne poster per D, oppstilt som i metodikken. Differanse ≥ 1 kr er uforklart til årsaken er funnet: let etter poster
på reskontrokontoen uten motpart (R9) og utligning på tvers av D.

### 4. Vurder hver åpen post (R3–R8, R10–R12, R14, R15)
Kategoriser **nøyaktig etter `references/kategorier.md`** (rekkefølge, etiketter, nullgrupper, terskler); `reskontro-vurdering` bruker de samme reglene.
Kortversjon: betalt/utlignet etter → kan utlignes → småbeløp → ufordelt innbetaling/kreditnota (1500) eller betaling uten faktura (2400) → ikke forfalt
→ 1–30 → 31–90 → over 90 dager. Poster datert før året er én samlelinje.
- Hver post i året får i tillegg avstemmingskategori (1 tidsforskjell, 2 krever føring, 3 må undersøkes) og alder fra `dagerForfalt`
  (0–30, 31–60, 61–90, over 90), med eskalering over V/2 og V (R14). Tabellen står i `references/kategorier.md`.
- Trend (R15): samme kommando med `--dato` = forrige S, eller forrige måneds fil i Tally (samling `Reskontro ÅÅÅÅ`).
- Brreg-status står i JSON-en for motparter med org.nr. som krever oppfølging; mangler den, Tally `lookup_brreg`.
- Purretrinn for kunder forfalt over 30 dager: `npm run -s api -- GET /reminder dateFrom=ÅÅÅÅ-01-01 dateTo=<D> customerId=<id> fields=invoiceId,reminderDate,type`.
- Feil fortegn per motpart (R3), dubletter blant åpne poster (R6) og 1580 mot postene til tapsvurdering (R12) etter tersklene i referansen.

### 5. Kjente avvik
Nøkkel `konto · motpart · beløp` fra kundeinstruksen → «kjent, uendret». Nytt beløp er nytt funn.

### 6. Tiltak – nummerert, hvert punkt krever ja
1. Utligning av nullgrupper og småbeløp (differansen til avrundingskontoen).
2. Purring eller inkasso per kunde med purretrinn. Tally `lag_purring` lager utkast etter ja; kunden eller regnskapsføreren sender.
3. Tap og avsetning: tapsføring bare ved konstatert tap (da kreves utgående mva tilbake, mval. § 4-7). Konkurs alene gir avsetning i 1580, ikke tap.
4. Ompostering: innbetaling fra Skatteetaten på 2400 → riktig konto (for eksempel 2600). Dobbeltbetaling til leverandør → krav om tilbakebetaling.
5. Spørsmål til kunden (ufordelte innbetalinger, betaling uten faktura) → Missive-utkast etter ja.

**Stopp:** R1/R2-differansen er under 1 kr – ellers settes ikke RECONCILED og oppgaven fullføres ikke: vis oppstillingen og let etter årsaken.
**Stopp:** ingen post i kategori 3 over V står uten beslutning (R14) – ellers settes ikke RECONCILED: vis posten med `Krever: oppdragsansvarlig` og vent på svar.

**Skriving (etter ja):** hver kommando kjøres først uten `--bekreft` (viser gruppene eller postene).
1. Nullgrupper per motpart: `npm run -s modul -- utlign --client "<klient>" --konto 1500 --bekreft` (og `--konto 2400`). Én bestemt gruppe
   (én konto, én motpart, sum 0, for eksempel etter føring av småbeløp): `npm run -s modul -- lukk --client "<klient>" --ids <id,id,…> --bekreft`.
2. Avstemmingsmodulen, linjene 1500 og 2400 (BALANCE for måneden): id fra `modul -- perioder --client "<klient>" --aar ÅÅÅÅ --type BALANCE --json`,
   `accountId` fra `modul -- linjer --client "<klient>" --id <BALANCE-id> --konto 15` (og `24`). Last opp arbeidsboka og sett dokumentert saldo og status:
   `npm run -s modul -- last-opp --client "<klient>" --id <BALANCE-id> --ref <accountId> --fil <xlsx> --bekreft`
   `npm run -s modul -- sett-status --client "<klient>" --id <BALANCE-id> --konto <accountId> --status RECONCILED --dokumentert <beløp> --bekreft`
3. Føringer i kategori 2 (småbeløp mot avrundingskontoen, avsetning 1580, ompostering, tap etter regnskapsførers beslutning): `periodisering`
   (`bilag manuell`) med kunde eller leverandør på reskontrolinjene og dokumentasjonen som vedlegg, med egen tørrkjøring.

**Bare i Tripletex-UI:**
1. Reskontrostatus «gjennomgått».

### 7. Kontoutskrift per motpart (R13)
På forespørsel, og automatisk for kunder med poster forfalt over 30 dager. Kall, kolonner og kontrollinje: `references/kontoutskrift.md`.
**Stemmer ikke IB + fakturert − innbetalt med uavhengig UB, lages ikke PDF-en.** Rapporter differansen som R13.

## Svar

- Første linje: port · R1/R2-differanse · antall åpne poster og sum per konto.
- Kategoritabell per konto (Kategori · Poster · Beløp) og aldersfordeling (0–30 · 31–60 · 61–90 · over 90, antall og sum per avstemmingskategori),
  så motpartene som krever oppfølging i funn-formatet med kategori og alder først i Forslag (høyst 5 per konto, størst først).
- Nummerert ja-liste til slutt, og hva som ikke ble lest.
- Firmanavn er greit; privatpersoner står som «privatkunde n». Ingen posteringstekster i chatten.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `BILAG`, periode `ÅÅÅÅ-MM`, samling `Reskontro ÅÅÅÅ`, oppgave «Avstemming kundereskontro»): `Reskontroavstemming ÅÅÅÅ-MM <Klient>.xlsx` med arkene Sammendrag (port, R1/R2, kategoritabell og aldersfordeling per konto, 1580) · Kunder · Leverandører (med kolonnene Kategori og Alder) · Tiltak (med «Krever»).
Kontoutskrift: `Kontoutskrift kundereskontro <kundenr.> ÅÅÅÅ-MM <Klient>.pdf` (leverandør tilsvarende; nummer, ikke navn), kategori `BILAG`, samling `Reskontro ÅÅÅÅ`, oppgave «Gjennomgang kunde- og leverandørreskontro».
Fullfør i Tally: se `tally-gjoremal`. «Avstemming kundereskontro» og «Avstemming leverandørreskontro» fullføres når R1/R2 er 0, ingen stopp står åpen og hver post som krever oppfølging har en beslutning; «Gjennomgang kunde- og leverandørreskontro» når tiltakslista er avgjort. Kommentaren inneholder periode, port, differanse, poster per kategori og aldersgruppe, og tiltak som venter.

## Fallgruver

- `openPost`: datoen er eksklusiv (bruk D, ikke siste dag). `reskontro-vurdering --dato` tar siste dag (S). Forfall er `termOfPayment` på posteringen.
- `/ledger/posting` kommer i bilagsrekkefølge; sorter på dato i skriptet. `/balanceSheet` har kundefilter, men ikke leverandørfilter.
- «Betalt etter» krever to uttrekk med samme kontoer: per D og per i morgen (`reskontro-vurdering` gjør begge).
- Nullgrupper søkes bare blant poster som er åpne i dag; grupper på 3 eller flere bare når motparten har høyst 16 slike poster.
- Konstatert tap er ikke det samme som konkurs. Tapsføring endrer mva og avgjøres av regnskapsfører.
- Reskontrokategorien (fra kommandoen) og avstemmingskategorien (1–3) er to felt. Endre aldri etikettene i `references/kategorier.md` uten kommandoen.

## Referanser

Kontroller: R1–R15 (`docs/kontrollkatalog.md`; bokførte dubletter er R6 i `bilagskontroll`). Metode: `docs/avstemmingsmetodikk.md`.
Kategorier, alder og terskler: `references/kategorier.md`. Kontoutskrift: `references/kontoutskrift.md`.
Naboskills: `bankavstemming`, `balanseavstemming`, `periodeavslutning`, `mva-kontroll`, `aarsoppgjoer-forberedelse`, `kundeinstruks`, `tally-gjoremal`.
