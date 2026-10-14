---
name: "mva-kontroll"
description: "Kontroll av mva for én klient og én termin før innsending: forutsetninger fra bank-, reskontro- og bilagskontrollen, 27xx og oppgjørskonto 2740 per måned, rimelighet per sats, unntaksliste på høyst 10 bilag med fradragsvurdering, kontroll av utkastet mot hovedboken og beslutningsliste med portfarge. Lukker Tally-oppgaven «MVA-kontroll». Bruk ved «mva-kontroll for <klient>», «avstem mva», «mva-avstemming», «kontroller mva for terminen», «mva termin <n> for <klient>», «klar til å sende mva», «nå har jeg opprettet utkast», «sjekk 2740»."
---

# Mva-kontroll før innsending

Lett kontroll av mva for én klient og én termin, med en kort beslutningsliste. Skillen leser resultatene fra `bankavstemming`, `reskontroavstemming` og
`bilagskontroll` og gjør bare terminkontrollene selv. Oversikt over alle klienter og etterarbeid etter sending: `mva-innlevering`.
Tunge kontroller (kontoplan, § 3-26, registreringsplikt, gamle reskontroposter) hører til `aarsoppgjoer-forberedelse`.

## Når

- Tally-oppgaven «MVA-kontroll», den 25. i måneden før fristen. Én klient om gangen; klient, termin og år må være sagt. Uklart → spør.
- Ferdig først: «Bilagsbehandling», «Bankavstamming» og «Kontroll av bilag» for begge månedene, og reskontro-oppgavene for terminens siste måned.
- Hold deg til terminen; tidligere terminer røres ikke. Steg 5 kjøres når regnskapsføreren sier «nå har jeg opprettet utkast».

## Kundeinstruks

«Mva» (registrert fra dato, termin, delvis fradrag, omvendt avgiftsplikt) · «Bank» (kontoer uten bankfeed) · «Kjente avvik» (samme nøkkel og beløp → «kjent, uendret»).

## Steg

### 1. Forutsetninger – les resultatet, ikke gjør arbeidet på nytt
`npm run -s mva -- "<klient>" --aar ÅÅÅÅ --termin N --json` (ca. 30 s) gir modus, port, `punkter` (alvor, kontroll, tittel, beløp), `tilVurdering`
(høyst 10 bilag) og arbeidsmappa (`mappe`). F0 = datasett som ikke kunne hentes; kontrollene som bruker dem, er ikke kjørt. Ny kjøring etter rettinger:
samme kommando (`--gjenbruk` bare når ingenting er ført siden).
- **Modus:** registrert, ikke registrert eller uklar (mva-innstillingene i Tripletex mot Enhetsregisteret; ved tvil Tally `lookup_brreg`).
  Uklar (for eksempel VAT_APPLICANT i Tripletex og registrert i Brreg) stopper kontrollen til brukeren har avklart det.
- **Bilag:** bilagsmottaket tomt og ingen ikke-bokførte leverandørfakturaer datert i terminen (punktene fra `mva`). Ellers → `bilagsforing`.
- **Bank:** alle kontoer lukket for begge månedene (punktene fra `mva`), eller åpne poster forklart i «Bankavstamming». Ellers → `bankavstemming`.
- **Reskontro:** «Avstemming kundereskontro» og «Avstemming leverandørreskontro» for siste måned fullført (Tally `list_tasks`) med arbeidsboka i
  samlingen `Reskontro ÅÅÅÅ` (`list_documents`). Konstatert tap på en kundefordring gir rett til å kreve tilbake utgående mva (mval. § 4-7); konkurs alene er ikke konstatert tap.
- **Bilagskontroll:** «Kontroll av bilag» for begge månedene fullført, med arbeidsboka i `Bilagskontroll ÅÅÅÅ`. Åpne BLOKK-funn (M4, M5, M7, M8, D3, R6)
  går rett inn i beslutningslista. Mangler en måned, kjøres steg 3 for den måneden.
- Mangler noe: si hva og pek på skillen. Brukeren velger mellom å vente og å fortsette med «ikke kontrollert» på punktet.

### 2. Mva-kontoene (M3 og 2740)
Saldo 2700–2799 per månedsslutt: `npm run -s api -- GET /balanceSheet dateFrom=<månedsstart> dateTo=<dagen etter månedsslutt> accountNumberFrom=2700
accountNumberTo=2799 fields=account(number),balanceIn,balanceChange,balanceOut --client "<klient>"`. Posteringene i terminen med mva-kode:
`npm run -s api -- GET /ledger/posting dateFrom=<terminstart> dateTo=<dagen etter terminslutt> fields=date,account(number),vatType(number),amount,amountGross,voucher(number)
--client "<klient>" --sider --ut <mappe>/posteringer.json`. `dateTo` er eksklusiv. Behold summer per kode og måned; ingen tekster.
- **Sats (M3):** utgående mva per kode mot 25, 15 eller 12 % av grunnlaget. Avvik over 1 % → funn med koden og bilagene som skiller.
- **2740 per måned:** IB, oppgjørsbilaget for forrige termin, innbetaling eller tilbakebetaling, og saldo per månedsslutt. Hver saldo får én forklaring
  (for eksempel «skyldig termin 3, betalt 12.09»). Saldo uten forklaring → funn.
- **27xx:** før «Opprett» er saldoen på 2700–2739 terminens mva. Posteringer i terminen med feil kode listes med bilagsnummer.
- **Ikke registrert:** `mva` kjører kontrollene for uregistrerte selv (punktene). 27xx skal være tom, bortsett fra omvendt avgiftsplikt (kode 87, 89, 92).
  Kjøp av fjernleverbare tjenester fra utlandet over 2 000 kr i et kvartal krever melding for omvendt avgiftsplikt (frist 10.5, 31.8, 10.11 og 10.2).

### 3. Unntaksliste – bare når en bilagskontroll mangler
Utvalget er `tilVurdering` fra steg 1 (`overlevering.json` i `mappe`): høyst 10 bilag sortert etter mva-effekt. Samme agent og svarkontrakt som
`bilagskontroll` steg 4 (`.claude/skills/bilagskontroll/references/kontroller.md`): én lesende agent med `docs/fradragsregler-kort.md`, oppslag i
`leverandorindeks` og bilagene fra `npm run -s dokument -- --client "<klient>" --bilag <nr-år> --ut <mappe>` (PDF og maskert .txt). Ingen agent når lista
er tom. Nye vurderinger av en leverandør tilbys lagret i `leverandorindeks` etter ja.

### 4. Beslutningsliste og rettinger etter ja
Lista (se Svar) har det som må rettes først. Hvert punkt rettes etter ja. Svar som gjelder klienten varig, tilbys lagret i kundeinstruksen.

**Skriving (etter ja):** `npm run -s modul -- utlign --client "<klient>" --konto 1500|2400 --bekreft` for poster som går i null (én konto, én motpart,
sum 0,00). Kjør først uten `--bekreft`; tørrkjøringen viser gruppene.

**Bare i Tripletex-UI:**
1. Rett mva-koden eller beløpet direkte på bilaget når terminen er åpen og bilaget kan endres.
2. Bank- og OCR-bilag gir 422: før et korrigeringsbilag i terminen som reverserer feil linje og fører riktig, med henvisning til originalen.
3. Les på nytt (steg 1–2) når brukeren sier at det er gjort, og oppdater lista. Til da står punktet som «ikke gjort».

### 5. Utkastet (M1) – etter at regnskapsføreren har trykket «Opprett»
`npm run -s modul -- kontroll-utkast --client "<klient>" --aar ÅÅÅÅ --termin N` gir linjene per kode (grunnlag og mva) mot hovedboken, fortegn og oppgjør.
- Utkastet viser hele kroner avkortet; under 1 kr per linje er ikke avvik. Kode 86 gir to linjer (ut og inn). Summen av linjene = beløp å betale eller
  til gode, også i hovedboken.
- Fortegn: en linje med fortegn motsatt av det Skatteetaten forventer (typisk fradragslinjen når kreditnotaer fra tidligere terminer er større enn kjøpene)
  må ha merknad, for eksempel «kreditnota».
- Oppgjørsbilaget nullstiller 2700–2739 mot 2740 og er datert siste dag i terminen. Etterpå er 2740 i siste måned −(beløp å betale), eller + ved tilgode.

## Svar

- Første linje: port (grønn/gul/rød etter `docs/skill-mal.md`) · termin · beløp å betale eller til gode ifølge hovedboken.
- Funn-tabellen (ID · Konto/motpart · Beløp · Status · Forslag · Krever): må rettes og spørsmål først, så følg opp. Høyst 10 linjer.
- Nummerert liste over det som krever ja. Kjente avvik står som én linje «kjent, uendret».
- Aldri bilagstekster eller leverandørtekster; bilagsnummer, konto, kode og beløp holder.

## Lever

Lever: `silfer-rapport` (via `npm run -s modul -- notat-2740 --client "<klient>" --aar ÅÅÅÅ --termin N --forklaring-MM "beløp|tekst" --ut <mappe>`) + `docs/dokumentlagring.md` (kategori `MVA_RAPPORT`, periode `ÅÅÅÅ-T<n>`, samling `Mva ÅÅÅÅ`, oppgave «MVA-kontroll»): 2740-notatet som PDF (saldo per månedsslutt med forklaring, bevegelser, terminene i året, kontroll per kode).
**Skriving (etter ja):** `npm run -s modul -- last-opp --client "<klient>" --id <BALANCE-id> --ref <linje> --fil <notat.pdf> --bekreft` på 2740 i begge månedene, deretter `modul -- sett-status --client "<klient>" --id <BALANCE-id> --konto <konto-id> --status RECONCILED --dokumentert <saldo> --bekreft` for 2740 og for 27xx (0) i siste måned. Id-er fra `modul -- perioder --type BALANCE` og `modul -- linjer --konto 27`. Status «avstemt» settes først etter at notatet er lastet opp.
Fullfør i Tally: se `tally-gjoremal`. «MVA-kontroll» fullføres når beslutningslista er grønn (eller gul med alt avklart) og meldingen er klar til innsending. Kommentaren inneholder termin, port, beløp å betale eller til gode og hva som gjenstår.

## Fallgruver

- Ikke avstem hele balansen og ikke fullfør BALANCE i modulen uten at brukeren ber om det. 19xx dokumenteres i `bankavstemming`, 1500/2400 i `reskontroavstemming`.
- 2740 blir automatisk avstemt i begge terminmånedene først når mva-avstemmingen er fullført etter innsending (`mva-innlevering`). 2700–2739 blir aldri det.
- Registrert midt i året: terminnummeret i Tripletex teller fra registreringsdatoen. Sjekk at perioden er riktig.
- Notatet lages ikke før 2740 er forklart for begge månedene. «Mangler forklaring» skal ikke stå i et notat som lastes opp.
- En bilagskontroll som er eldre enn siste føring i måneden, er utdatert. Kjør `bilagskontroll` på nytt for den måneden.
- `mva` er fullt utbygd for ikke registrerte. For registrerte gir den forutsetningene (bilag, bank, reskontro, skattekonto); steg 2 gjøres med `api`.

## Referanser

Kontroller: M1, M3 (her); M4, M5, M7, M8, D3, R6 (`bilagskontroll`); R1–R13 (`reskontroavstemming`); B1–B5 (`bankavstemming`); M2, M6 (`mva-innlevering`).
Regler: `docs/fradragsregler-kort.md` (agentens svarkontrakt), `docs/fradragsregler.md` (rettsgrunnlag). Avstemmingsmodulen: `tripletex-api/docs/avstemmingsmodul.md`.
Naboskills: `leverandorindeks`, `kundeinstruks`, `aarsoppgjoer-forberedelse`, `tally-gjoremal`.
