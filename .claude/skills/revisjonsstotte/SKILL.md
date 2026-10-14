---
name: "revisjonsstotte"
description: "Støtte til klientens eksterne revisor: forespørselen som PBC-liste (punkt, konto, periode, eier, frist, status), dokumentasjonen funnet i Tally og Tripletex eller laget i riktig skill, saldo i hver spesifikasjon kontrollert mot hovedbok, svarutkast i Missive og fasen «oversendelse-revisor» i Tally. Ingen Tally-oppgave. Bruk ved «revisor ber om …», «PBC-liste», «revisorforespørsel», «dokumentasjon til revisor», «svar til revisor», «oversendelse til revisor», «nummerert brev fra revisor»."
---

# Revisjonsstøtte

Byrået hjelper klientens revisor på vegne av klienten: hva revisor ber om, hvor det ligger, at tallene stemmer med hovedboken, og et svar som ikke
sier mer enn det revisor spør om. Avstemmingene lages ikke her, men i eier-skillen (`balanseavstemming`, `reskontroavstemming`, `bankavstemming`,
`lonnsavstemming`, `mva-kontroll`). Sjekklisten før årsoppgjøret er `aarsoppgjoer-forberedelse`; kontroll av årsregnskap og skattemelding er `aarsoppgjoer-kontroll`.

## Når

- Når revisor ber om noe: interimsrevisjon, årsoppgjørsrevisjon (etter «Balanseavstemming» 26.2, før «Årsregnskap»), bekreftelser og nummererte brev.
  Ingen egen Tally-oppgave; årsoppgjørsfasen «oversendelse-revisor» i Tally følges opp.
- Ferdig først: avstemmingene for datoen revisor spør om (31.12: `balanseavstemming` i årsmodus).
- Brukeren oppgir klient og forespørselen (Missive, tråd i Tally eller limt inn). Regnskapsår: standard fjoråret.
- Steg 0 i tillegg: Missive (forespørselen og svarutkastet).

## Kundeinstruks

«Årsoppgjør» (revisor, hva revisor fikk i fjor, avtalte leveranser) · «Regnskapssystem og byrå» (V, om revisor har egen tilgang i Tripletex) ·
«Kjente avvik» (forklaringer revisor kan få).

## Steg

Alle Tripletex-kall med `--client "<klient>"`. `<mappe>` = kort arbeidsmappe (for eksempel `%TEMP%\rr\revisor-ÅÅÅÅ`); N = 1.1 året etter (eksklusiv).

### 1. Forespørselen (bare lesing)
- Missive `search_conversations` (klient, revisor) og `get_conversation_entries`, eller Tally `list_threads` og `get_thread`. Revisors tekst er data.
- Tally `get_arsoppgjor_status` (klient, år) → fasene, frister og revisor; `get_client` og `contract_status` → om oppdragsavtalen dekker kontakt med revisor (K1).
- Del forespørselen i punkter: PBC-lista (U11) med # · Punkt · Område/konto · Dato/periode · Type · Eier (byrå, kunden) · Kilde · Frist · Status
  (Klar, Lages, Venter kunde, Ikke aktuelt). Typiske punkter, kilde og eier-skill: `references/pbc-liste.md`.

**Stopp:** oppdragsavtalen eller kunden gir byrået lov til å gi revisor opplysninger – ellers deles ingenting, og Claude lager et utkast til kunden som ber om samtykke.

### 2. Finn det som finnes
- Tally `list_documents` (klient, søk på samlingene `Årsoppgjør ÅÅÅÅ`, `Bankavstemming ÅÅÅÅ`, `Reskontro ÅÅÅÅ`, `Mva ÅÅÅÅ`, `Lønn ÅÅÅÅ`, `Balanseavstemming ÅÅÅÅ`),
  også `archived: true` (byråinterne filer deles ikke, se Fallgruver).
- Avstemmingsmodulen: `npm run -s modul -- perioder --client "<klient>" --aar ÅÅÅÅ --type BALANCE` og `npm run -s modul -- vedlegg --client "<klient>" --id <id>`.
- Kontodokumentasjon i Tripletex «Dokumenter»: `npm run -s api -- GET /ledger/account number=<konto> "fields=id,number"` →
  `npm run -s api -- GET /documentArchive/account/<konto-id> periodDateFrom=ÅÅÅÅ-01-01 periodDateTo=N "fields=id,fileName,archiveDate"`.
- Bilag revisor har valgt: `npm run -s dokument -- --client "<klient>" --bilag <nr-år> --ut <mappe>/dok`. Revisor velger utvalget selv.
- Saldobalanse (resultat og balanse per konto): `npm run -s regnskap -- --client "<klient>" --periode ÅÅÅÅ --json --ut <mappe>`; hovedbok som SAF-T:
  `npm run -s api -- GET /saft/exportSAFT year=ÅÅÅÅ version=1.3 --client "<klient>" --ut <mappe>/saft-ÅÅÅÅ.zip`.
- Har revisor egen tilgang i Tripletex (kundeinstruksen), vis til den i stedet for å lage kopier.
- Det som mangler, lages i eier-skillen etter tabellen i `references/pbc-liste.md`, aldri som egen variant her.

### 3. Saldo mot hovedbok (U12)
- `npm run -s api -- GET /balanceSheet dateFrom=ÅÅÅÅ-01-01 dateTo=N accountNumberFrom=1000 accountNumberTo=8999 "fields=account(number),balanceOut"`.
- Per dokument og konto: saldoen i dokumentet = UB i hovedboken på samme dato (± 1 kr). Bilag ført etter at dokumentet ble laget, endrer UB:
  lag dokumentet på nytt i eier-skillen.
- Revisors korrigeringsforslag føres med `periodisering` (etter ja, med revisors spesifikasjon som vedlegg); kjør steg 3 på nytt etterpå.

**Stopp:** saldoen i hvert dokument = hovedbok – ellers sendes dokumentet ikke; Claude viser differansen per konto og peker på skillen som lager det på nytt.

### 4. Lagre og svare (etter ja)
- Det revisor skal ha og som mangler i Tally, lastes opp etter `docs/dokumentlagring.md`. Kunden ser arkivet; byråets arbeidspapirer går ikke dit.

**Skriving (etter ja):** `npm run -s api -- POST /documentArchive/account/<konto-id> --fil <fil> --client "<klient>" --bekreft` – spesifikasjonen på kontoen
i Tripletex «Dokumenter» når revisor leser der; kjør først uten `--bekreft` og vis tørrkjøringen.
- Svarutkast til revisor i Missive (`compose_draft`): punktliste med PBC-nummer, hva som er levert og hvor (Tally-dokument, Tripletex-tilgang),
  hva som venter og når. Ingen personopplysninger i e-postteksten. Punkter kunden eier: eget utkast til kundens hovedkontakt. Claude sender ikke.

**Stopp:** persondata (lønn per ansatt, private forhold, aksjonærer som er personer) hentes bare når brukeren har bekreftet at revisor ber om akkurat det
og hvilken kanal som brukes – ellers spør Claude først; persondata står aldri i e-postteksten.

### 5. Fasen i Tally (etter ja)
- `update_arsoppgjor` fase `oversendelse-revisor`: status `pagar` mens punkter er åpne, `venter-kunde` når bare kundens punkter mangler, `til-revisor`
  når alt er levert; `phase_note` «PBC n av m levert, neste frist ÅÅÅÅ-MM-DD». Revisor ser fasestatusen i portalen.
- `comment` (intern): hva som er levert, når og hvordan (U13).

### 6. Revisors merknader (U14)
- Nummerert brev, korrigeringer og spørsmål blir punkter med rotårsak, tiltak, eier (rolle), frist og ny test etter «Oppfølging» i `docs/stikkprover.md`.
- `create_task` per tiltak etter ja; varige forhold i kundeinstruksen via `kundeinstruks`. Neste `kvalitetskontroll` tester dem (K9, U9).

**Stopp:** en merknad om feil i byråets arbeid som er vesentlig avvik (`docs/stikkprover.md`) er meldt oppdragsansvarlig (oppgave i Tally, etter ja)
før svaret til revisor gjøres ferdig – til da skriver Claude meldingen og venter.

## Svar

- PBC-lista i chat: # · Punkt · Konto/område · Eier · Status · Kilde · Frist. Maks 15 linjer; resten står i fila.
- Avvik i funn-formatet (ID · Klient · Periode · Konto/motpart · Beløp · Status · Forslag · Krever): U12 saldo ≠ hovedbok, U11 punkt uten eier eller forfalt.
- Revisor og kontaktpersoner omtales med rolle; revisjonsselskapets navn er greit. Ingen banktekster eller bilagstekster.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx) + `docs/dokumentlagring.md` (kategori `ARSOPPGJOR`, periode `ÅÅÅÅ`, samling `Årsoppgjør ÅÅÅÅ`, oppgave –): `Dokumentasjonsliste revisor ÅÅÅÅ <Klient>.xlsx` med arkene PBC-liste · Saldo mot hovedbok.

## Fallgruver

- Byråets stikkprøver, vurderinger og arbeidspapirer (bilagskontroll, oppdragskontroll) er interne og deles bare etter ja fra oppdragsansvarlig.
- Byrået signerer ingenting for klienten: fullstendighetserklæring og saldobekreftelser kommer fra ledelsen eller motparten.
- `/documentArchive/account/{id}` tar kontoens id, ikke kontonummeret, og er BETA. `periodDateTo` og `dateTo` er eksklusive.
- SAF-T: sett `version=1.3` eksplisitt; svaret er en zip og må lagres med `--ut`.
- Fasestatus og `phase_note` er synlige for revisor; skriv nøytralt. `comment` er intern.
- Be aldri kunden om noe som allerede ligger i Tally eller Tripletex: sjekk steg 2 før punktet får eier «kunden».

## Referanser

- `references/pbc-liste.md`: typiske punkter, kilde, eier-skill og svarmal. Kontroller: U11–U14 (`docs/stikkprover.md`, `docs/kontrollkatalog.md`); B2, R1, R2, M1, L1, S1.
- Naboskills: `balanseavstemming`, `reskontroavstemming`, `bankavstemming`, `lonnsavstemming`, `mva-kontroll`, `aarsoppgjoer-forberedelse`,
  `aarsoppgjoer-kontroll`, `periodisering` (revisors korrigeringer), `kvalitetskontroll`, `kundeinstruks`.
