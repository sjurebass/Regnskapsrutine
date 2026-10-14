---
name: "lonnsavstemming"
description: "Avstemming av lønnsområdet mot A07 fra Skatteetaten: forskuddstrekk 2600, arbeidsgiveravgift 5400/2770, grunnlag per ytelse, pensjon, feriepenger og per ansatt, per termin eller for hele året → Silfer-Excel. Lukker Tally-oppgavene «Avstemming av AGA og forskuddstrekk» (termin) og «Årsavslutning lønn» (år). Bruk ved «lønnsavstemming», «avstem lønn», «avstem AGA», «avstem forskuddstrekk», «A07», «avstem lønn mot A07», «årsavslutning lønn», «feriepengeavsetning»."
---

# Lønnsavstemming A07 mot Tripletex

Avstemmer lønnsområdet for én klient og én termin (eller hele året) mot A07 fra Skatteetaten, og leverer Silfer-Excel med sju ark.
Status, innsending og skyldig trekk/AGA er `a-melding`; lønnskjøringen er `lonnskjoring`.

## Når

- «Avstemming av AGA og forskuddstrekk»: den 10. annenhver måned (jan, mar, mai, jul, sep, nov) for terminen før, før forfall den 15.
- «Årsavslutning lønn»: 29.1 for året før (steg 5).
- Lønnskjøringene skal være fullført og a-meldingene for terminen sendt (`a-melding`). Brukeren oppgir klient, termin og år, og A07-fila.

## Kundeinstruks

«Lønn»: modell (direkte trekk eller skattetrekkskonto 1950) og pensjon (konto) styrer trekkradene og `konto.pensjon` i ledger.json.
«Kjente avvik»: restsaldoer på 2600/2770 som er forklart før, meldes som «kjent, uendret».

## Steg

### 1. Les A07
Input er A07-fila for terminen (XML er primærkilde; ODS er samme data). Mangler A07: be om filen (Altinn → Skatteetaten → «Avstemmingsinformasjon a-melding», velg termin, last ned XML). Ikke start uten den.
`parse_a07()` i skriptet leser innsendinger, AGA-grunnlag, ytelser per person og trekk; skriv ikke egen parser. Gjeldende innsendinger er alle som
ikke er erstattet av en annen (`erstatterMeldingsId`), uansett status, og de summeres. Sjekk før du går videre: flere innsendinger samme måned,
negative trekk, personer uten ansattnummer eller opptjeningsperiode, og `fradragIGrunnlagetForSone` (NAV-refusjon).

### 2. Hent regnskapet (MCP)
1. Kjør `scripts/hent_tripletex.js` i `tripletex_run_script`: les fila, sett `KLIENT` (navnet fra `search_client_companies`), `D1` (første dag i
   terminen), `D2` (første dag etter terminen) og `Y1` (1. januar), og send hele teksten som `code`. Svaret er `{balanser, posteringer,
   pensjon_rader, advarsler}`; les `advarsler` først.
2. Første gang på en klient: sjekk at dato, bilag, konto og beløp er fylt. Er de tomme, se formen med ett `search_ledger_postings`-kall og rett
   `felt()` i `rad()`. Er svaret for stort, del terminen i to kall (én måned hver).
3. `get_amelding_status` for siste måned i terminen: påløpt og ubetalt trekk og AGA skal stemme med A07 (L2; feltene forklares i `a-melding`).
4. 2770 IB ≠ forrige termins a-meldte AGA: hent 2770 for forrige termin og forklar restsaldoen.

### 3. Bygg `ledger.json`
Kopier strukturen fra `scripts/ledger_eksempel.json` og fyll inn fra steg 2: selskap, org.nr., periode (forfall = 15. i måneden etter terminslutt),
AGA-sats, feriepengesats (les 5020/5000 i et lønnsbilag), `balanser`, `posteringer` og `pensjon_historikk` for hele året (KID leses fra A07).
`ytelse_konto` bare der klienten avviker fra standard; `forklart` bare når merknaden forklarer avviket fullt ut. Alle felt: `references/kontrollogikk.md`.

### 4. Kjør og verifiser
Arbeidsfilene (A07-XML, ledger.json, Excel) ligger i scratch til de er lagret i Tally. Stilen kommer fra `silfer-rapport`.
```bash
uv run --with openpyxl --with pillow python .claude/skills/lonnsavstemming/scripts/lonnsavstemming_a07.py <scratch>/a07.xml <scratch>/ledger.json "<scratch>/Lønnsavstemming <Klient> termin <n> <år>.xlsx"
```
Formlene beregnes først når filen åpnes i Excel. Kontroller med openpyxl at ingen celle har feilverdier (`#REF!`, `#VALUE!`, `#DIV/0!`), at summene
i «Avstemming» stemmer med ledger.json, og les alle ark. Krav før levering:
- «Avstemming»: AVVIK = 0, eller hvert AVVIK er reelt og har merknad. FORKLART bare med merknad.
- «Per ansatt»: alle rader OK, ingen «Koblingsproblemer» (ellers feil `ytelse_konto`, eller tillegg ført utenfor lønnsbilag eller reiseregning).
- «Arbeidsgiveravgift» pkt. 2: «Uforklart differanse» = 0. Konti merket «NEI – kontroller» (typisk 5320) = mulig ikke-innrapportert fordel → merknad.
- Pensjon hittil i år: differanse 0; ellers merknad med AGA-effekt og «korriger i neste a-melding».
- Pkt. 3/4: «Kreditert 2770» og UB 2770 = innrapportert (ellers restsaldo → merknad).
- «Forskuddstrekk»: UB − IB − innbetalt + a-meldt = 0. Debetsaldo 2600 = for mye innbetalt trekk.
Merknader er korte faktasetninger med bilagsnr., beløp, årsak og tiltak – ikke prosa.

### 5. Årsmodus («Årsavslutning lønn») – kalibreres ved første årsavslutning
1. Alle seks terminer avstemt: terminfilene i samling `Lønn ÅÅÅÅ` (`list_documents`). Mangler en termin, kjør steg 1–4 for den.
2. Året mot A07 (L1): Tally `hent_amelding_rapport` januar–desember (bestilles med `request_amelding_report` etter ja; bare summer) mot bevegelsen
   på 5000–5999, 2600 og 2770 for året.
3. UB 2600 og 2770 per 31.12 = skyldig for termin 6 (`get_amelding_status` for desember, se `a-melding`).
4. Feriepenger (L3): UB 2940 = årets feriepengegrunnlag × sats, og 2785 = AGA av avsetningen.
5. Lønn mot bank (L5): netto i lønnsbilagene mot lønnsutbetalingene på 1920 for året.
6. Skriptet er per termin: årsoversikten (én rad per termin + punktene over) lages med `silfer-rapport` som `Lønnsavstemming <Klient> <år>.xlsx`.

### 6. Avstemmingsmodulen i Tripletex
**Krever skriving utenfor MCP: Tripletex-UI (eller API-kobling):** bare når byrået bruker modulen for lønn (`tripletex-api/docs/avstemmingsmodul.md`):
1. Hent A07 i lønnsavstemmingen for terminen. 2. Kommentar på hvert avvik, én kort setning (for eksempel «Utbetalte feriepenger.» på 2940/2785, eller
«Kravet skyldes ubetalt AGA etter korreksjon, se vedlegg.»). 3. Legg Excel-fila ved. 4. Fullfør lønnsavstemmingen (da avstemmes 2600/2770 automatisk).

## Svar

3–6 linjer: stemmer eller avvik, skyldig trekk og AGA med forfall og KID, og hvert avvik med beløp og tiltak. Ingen navn eller beløp per person.

## Lever

Lever: `silfer-rapport` (stil via `scripts/lonnsavstemming_a07.py`; årsoversikten via spec.json) + `docs/dokumentlagring.md` (kategori `LONN`, periode `ÅÅÅÅ-T<n>` (år: `ÅÅÅÅ`), samling `Lønn ÅÅÅÅ`, oppgave «Avstemming av AGA og forskuddstrekk» (år: «Årsavslutning lønn»)).
Excel-fila og A07-XML lagres begge. Slett A07-XML, ledger.json og Excel-fila fra scratch når de ligger i Tally.
Fullfør i Tally: se `tally-gjoremal`. «Avstemming av AGA og forskuddstrekk» («Årsavslutning lønn») fullføres når fila er lagret i Tally og alle AVVIK har merknad. Kommentaren inneholder termin (år), skyldig trekk og AGA med forfall, antall avvik og hva som gjenstår.

## Fallgruver

- Ikke nettleseren mot Tripletex. Er MCP-en nede: parse A07 og forbered ledger.json, si at koblingen må kobles til igjen, og vent.
- Ikke skriv skriptene på nytt. Rett feil i `scripts/` og verifiser mot en godkjent rapport (`references/kontrollogikk.md`). Celletekst starter aldri med `=`.
- `get_balance_sheet` utelater 2600 når IB, bevegelse og UB er 0 – bruk posteringene.
- A07 gir trekk per person for hele terminen; fordelingen per måned kommer fra 2600-linjene.
- EK: naturalytelse (5210 + motkonto 5290) eller utgiftsgodtgjørelse (5390, kontant) – les `fordel` og sett `ytelse_konto`.
- AGA av utbetalte feriepenger går 2785/2780 → 2770, ikke via 5400. NAV-refusjon er `fradragIGrunnlagetForSone`, ofte i egen tilleggsmelding med negativ AGA.
- Tripletex runder AGA ned til hele kroner per måned; 0–1 kr per måned er normalt. Avrundingsbilaget «A-melding lønn» kan være reversert og kjørt på nytt.
- Sticos «for året» kan mangle terminer – saldobalansen i Tripletex er fasit hittil i år.

## Referanser

- `docs/kontrollkatalog.md`: L1, L3, L5 (L2 og skyldig trekk/AGA: `a-melding`). Naboskills: `a-melding`, `lonnskjoring`, `balanseavstemming` (2600/2770/2940), `silfer-rapport`.
- `scripts/`: `hent_tripletex.js` (uttrekk i `tripletex_run_script`), `a07.py` (A07-parser), `kobling.py` (beløpsmatching per person), `lonnsavstemming_a07.py` (de sju arkene),
  `ledger_eksempel.json` (utfylt eksempel), `ledger_fra_rapport.py` og `sammenlign.py` (verifisering etter endringer i kontrollogikken).
- `references/kontrollogikk.md`: arkene, ledger.json-formatet, kontrollogikken, typiske funn og verifiseringsstatus. Les den før første kjøring på en ny klient.
