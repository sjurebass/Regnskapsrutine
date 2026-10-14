---
name: "lonnsavstemming"
description: "Avstemming av lønnsområdet mot A07 fra Skatteetaten: forskuddstrekk 2600, arbeidsgiveravgift 5400/2770, grunnlag per ytelse, pensjon og feriepenger, per termin eller for hele året → Silfer-Excel. Lukker Tally-oppgavene «Avstemming av AGA og forskuddstrekk» (termin) og «Årsavslutning lønn» (år). Bruk ved «lønnsavstemming», «avstem lønn», «avstem AGA», «avstem forskuddstrekk», «A07», «avstem lønn mot A07», «årsavslutning lønn», «feriepengeavsetning»."
---

# Lønnsavstemming A07 mot Tripletex

Avstemmer lønnsområdet for én klient og én termin (eller hele året) mot A07 fra Skatteetaten, hentet gjennom Tally, og leverer Silfer-Excel med seks ark.
A07 fra Tally har ingen personopplysninger, og det er ingen kontroll per ansatt. Status, innsending og skyldig trekk/AGA er `a-melding`; lønnskjøringen er `lonnskjoring`.

## Når

- «Avstemming av AGA og forskuddstrekk»: den 10. annenhver måned (jan, mar, mai, jul, sep, nov) for terminen før, før forfall den 15.
- «Årsavslutning lønn»: 29.1 for året før (steg 5).
- Lønnskjøringene skal være fullført og a-meldingene for terminen sendt (`a-melding`). Brukeren oppgir klient, termin og år.

## Kundeinstruks

«Lønn»: modell (direkte trekk eller skattetrekkskonto 1950) og pensjon (konto) styrer trekkradene og `konto.pensjon` i ledger.json.
«Kjente avvik»: restsaldoer på 2600/2770 som er forklart før, meldes som «kjent, uendret».

## Steg

### 1. Hent A07 fra Tally
1. `list_clients` → `client_id` for klienten.
2. `hent_amelding_rapport(client_id, start_month, end_month)` for terminens måneder (`ÅÅÅÅ-MM`, samme kalenderår). Lagre svaret uendret
   som `a07.json` i arbeidsmappa `<mappe>` (kort sti, for eksempel `%TEMP%\rr\lonn`).
3. Sier svaret at rapporten ikke er bestilt: `request_amelding_report(client_id, start_month, end_month)` gir først en forhåndsvisning. Vis den,
   og kall igjen med `confirmation_id` først etter ja. Hent på nytt etter noen minutter, én gang – ikke i løkke. Si det til brukeren og fortsett med steg 2 imens.
4. Les svaret før du går videre: flere innsendinger samme måned og `erstattet` (korrigeringer), negative trekk (tilbakebetaling), fradrag i
   `avgiftsgrunnlag` (NAV-refusjon), ukjente typer, og `null` – det betyr «ikke oppgitt», ikke 0.

Ingen XML og ingen nedlasting fra Altinn. Hent ikke personopplysninger fra andre kilder for å avstemme per ansatt.

### 2. Hent regnskapet (API)
1. `npm run -s lonn -- hent --client "<klient>" --aar ÅÅÅÅ --termin N --a07 <mappe>/a07.json --ut <mappe>` skriver `<mappe>/ledger.json`: selskap,
   org.nr., periode (forfall = 15. i måneden etter terminslutt), AGA-sats (fra A07), `balanser` og `posteringer` for terminen og `pensjon_historikk`
   hittil i år. Les `advarsler` (i utskriften og i ledger.json) først. Er A07 ikke kommet ennå: kjør uten `--a07` og på nytt med den når den er
   hentet (AGA-satsen og pensjonsgrunnlaget trenger den).
2. Første gang på en klient: sjekk at dato, bilag, konto og beløp er fylt i `posteringer`. Er de tomme, er det feil i kommandoen – si det, og fyll
   ikke inn for hånd.
3. `npm run -s amelding -- status --client "<klient>" --maned <siste måned i terminen> --json`: påløpt og ubetalt trekk og AGA skal stemme med A07
   (L2; feltene forklares i `a-melding`).
4. 2770 IB ≠ forrige termins a-meldte AGA: `npm run -s api -- GET /balanceSheet dateFrom=<forrige terminstart> dateTo=<terminstart>
   accountNumberFrom=2770 accountNumberTo=2770 fields=account(number),balanceIn,balanceChange,balanceOut --client "<klient>"`, og forklar restsaldoen.

### 3. Fullfør `ledger.json`
Kommandoen fyller alt unntatt `feriepenger_sats`, `forklart`, `merknader` og `kommentarer`. Fyll inn: `feriepenger_sats` (les 5020/5000 i et
lønnsbilag i `posteringer`), `ytelse_konto` bare der klienten avviker fra standard, `forklart` bare når merknaden forklarer avviket fullt ut.
KID, konto og forfall leses fra a07.json. Utfylt eksempel: `scripts/ledger_eksempel.json`; alle felt: `references/kontrollogikk.md`.

### 4. Kjør og verifiser
Arbeidsfilene (a07.json, ledger.json, Excel) ligger i `<mappe>` til Excel-fila er lagret i Tally. Stilen kommer fra `silfer-rapport`.
```bash
uv run --with openpyxl --with pillow python .claude/skills/lonnsavstemming/scripts/lonnsavstemming_a07.py <mappe>/a07.json <mappe>/ledger.json "<mappe>/Lønnsavstemming <Klient> termin <n> <år>.xlsx"
```
Formlene beregnes først når filen åpnes i Excel. Kontroller med openpyxl at ingen celle har feilverdier (`#REF!`, `#VALUE!`, `#DIV/0!`), at summene
i «Avstemming» stemmer med a07.json og ledger.json, og les alle ark. Krav før levering:
- «Avstemming»: AVVIK = 0, eller hvert AVVIK er reelt og har merknad. FORKLART bare med merknad. «ikke oppgitt» er AVVIK til det er avklart i Altinn.
- Trekk og AGA per måned: OK. «Ingen a-melding for måneden i A07» = send a-meldingen (`a-melding`) og hent A07 på nytt.
- «Ytelser A07»: alle konti OK (ellers feil `ytelse_konto`, eller tillegg ført utenfor lønnsbilag eller reiseregning).
- «Arbeidsgiveravgift» pkt. 2: «Uforklart differanse» = 0. Konti merket «NEI – kontroller» (typisk 5320) = mulig ikke-innrapportert fordel → merknad.
- Pensjon hittil i år: differanse 0; ellers merknad med AGA-effekt og «korriger i neste a-melding».
- Pkt. 3/4: «Kreditert 2770» og UB 2770 = innrapportert (ellers restsaldo → merknad).
- «Forskuddstrekk»: UB − IB − innbetalt + a-meldt = 0. Debetsaldo 2600 = for mye innbetalt trekk.
Merknader er korte faktasetninger med bilagsnr., beløp, årsak og tiltak – ikke prosa.

### 5. Årsmodus («Årsavslutning lønn») – kalibreres ved første årsavslutning
1. Alle seks terminer avstemt: terminfilene i samling `Lønn ÅÅÅÅ` (`list_documents`). Mangler en termin, kjør steg 1–4 for den.
2. Året mot A07 (L1): `hent_amelding_rapport` januar–desember (bestilles som i steg 1) mot bevegelsen på 5000–5999, 2600 og 2770 for året
   (`npm run -s api -- GET /balanceSheet dateFrom=ÅÅÅÅ-01-01 dateTo=<år+1>-01-01 accountNumberFrom=2600 accountNumberTo=5999 fields=account(number),balanceIn,balanceChange,balanceOut --client "<klient>"`).
3. UB 2600 og 2770 per 31.12 = skyldig for termin 6 (`npm run -s amelding -- status --client "<klient>" --maned ÅÅÅÅ-12 --json`, se `a-melding`).
4. Feriepenger (L3): UB 2940 = årets feriepengegrunnlag × sats, og 2785 = AGA av avsetningen.
5. Lønn mot bank (L5): netto i lønnsbilagene mot lønnsutbetalingene på 1920 for året.
6. Skriptet er per termin: årsoversikten (én rad per termin + punktene over) lages med `silfer-rapport` som `Lønnsavstemming <Klient> <år>.xlsx`.

### 6. Avstemmingsmodulen i Tripletex
**Bare i Tripletex-UI:** bare når byrået bruker modulen for lønn (`tripletex-api/docs/avstemmingsmodul.md`); `modul` er ikke testet på lønnsavstemmingen:
1. Hent A07 i lønnsavstemmingen for terminen. 2. Kommentar på hvert avvik, én kort setning (for eksempel «Utbetalte feriepenger.» på 2940/2785, eller
«Kravet skyldes ubetalt AGA etter korreksjon, se vedlegg.»). 3. Legg Excel-fila ved. 4. Fullfør lønnsavstemmingen (da avstemmes 2600/2770 automatisk).

## Svar

3–6 linjer: stemmer eller avvik, skyldig trekk og AGA med forfall og KID, og hvert avvik med beløp og tiltak. Ingen navn eller beløp per person.

## Lever

Lever: `silfer-rapport` (stil via `scripts/lonnsavstemming_a07.py`; årsoversikten via spec.json) + `docs/dokumentlagring.md` (kategori `LONN`, periode `ÅÅÅÅ-T<n>` (år: `ÅÅÅÅ`), samling `Lønn ÅÅÅÅ`, oppgave «Avstemming av AGA og forskuddstrekk» (år: «Årsavslutning lønn»)).
Bare Excel-fila lastes opp; A07 ligger i Altinn og Tally og lagres ikke som fil. Slett `<mappe>` (a07.json, ledger.json og Excel-fila) når Excel-fila ligger i Tally.
Fullfør i Tally: se `tally-gjoremal`. «Avstemming av AGA og forskuddstrekk» («Årsavslutning lønn») fullføres når fila er lagret i Tally og alle AVVIK har merknad. Kommentaren inneholder termin (år), skyldig trekk og AGA med forfall, antall avvik og hva som gjenstår.

## Fallgruver

- Ikke nettleseren mot Tripletex. Svarer ikke API-koblingen (utløpt nøkkel, 401): hent A07 imens, si at nøkkelen må fornyes (`npm run set-token`), og vent.
- Ikke skriv skriptene på nytt. Rett feil i `scripts/` og verifiser mot en godkjent rapport (`references/kontrollogikk.md`). Celletekst starter aldri med `=`.
- A07 fra Tally gir trekk og AGA per måned, og grunnlag og ytelser for hele perioden – ikke per lønnsdato og ikke per person.
- Direkte-modell: «Overføring skattetrekk» i selve lønnsbilaget er innbetalt trekk, ikke trekk. `bilag` i ledger.json er bilagsnummeret, ikke nummeret i teksten.
- Saldobalansen utelater 2600 når IB, bevegelse og UB er 0. `lonn hent` regner da fra posteringene med IB 0 og gir en advarsel – sjekk IB.
- EK: naturalytelse (5210 + motkonto 5290) eller utgiftsgodtgjørelse (5390, kontant) – les `fordel` og sett `ytelse_konto`.
- AGA av utbetalte feriepenger går 2785/2780 → 2770, ikke via 5400. NAV-refusjon er fradrag i `avgiftsgrunnlag`, ofte i egen tilleggsmelding med negativ AGA.
- Tripletex runder AGA ned til hele kroner per måned; 0–1 kr per måned er normalt. Avrundingsbilaget «A-melding lønn» kan være reversert og kjørt på nytt.
- Sticos «for året» kan mangle terminer – saldobalansen i Tripletex er fasit hittil i år.

## Referanser

- `docs/kontrollkatalog.md`: L1, L3, L5 (L2 og skyldig trekk/AGA: `a-melding`). Naboskills: `a-melding`, `lonnskjoring`, `balanseavstemming` (2600/2770/2940), `silfer-rapport`.
- Regnskapssiden: `npm run -s lonn -- hent` (ledger.json). `scripts/`: `a07.py` (leser A07-JSON fra Tally), `lonnsavstemming_a07.py` (de seks arkene),
  `a07_tally_eksempel.json` og `ledger_eksempel.json` (utfylte eksempler), `ledger_fra_rapport.py` og `sammenlign.py` (verifisering etter endringer i kontrollogikken).
- `references/kontrollogikk.md`: A07-formen fra Tally, arkene, ledger.json-formatet, kontrollogikken, hva som ikke kan kontrolleres og verifiseringsstatus. Les den før første kjøring på en ny klient.
