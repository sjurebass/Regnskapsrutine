---
name: "avviksanalyse"
description: "Forklarer avvik på resultatlinjer og kontoer i Tripletex mot forrige periode, samme periode i fjor eller budsjett: terskler mot V, prioritering, dekomponering i drivere (lønn, volum, skjønn, kontrakt, engangs, timing, mva og valuta), drill-down til leverandør og bilag, fast narrativ per avvik og en bro som går opp. Fører ingenting. Ingen Tally-oppgave. Bruk ved «avviksanalyse», «forklar avviket på <konto>», «hvorfor er <kostnad> høyere», «fluxanalyse», «bro fra i fjor», «sammenlign mot budsjett»."
---

# Avviksanalyse

Finner driverne bak avvikene som `regnskapsrapport` flagger, forklarer dem etter fast mal og bygger en bro fra sammenligningen til perioden.
Fører ingenting: timing går til `periodisering`, feilføringer til korrigeringsbilag i `periodisering`, mva-koder til `bilagskontroll`.

## Når

- Ingen Tally-oppgave: brukes av `regnskapsrapport` (N2), `periodeavslutning` (A1–A2) og når kunden eller regnskapsfører spør om et avvik.
- Brukeren oppgir klient, periode og sammenligning (forrige periode, i fjor eller budsjett), og eventuelt én linje eller konto. Uten linje: alle avvik over V.
- Perioden bør være ajourført (bilag og bank). Ellers forklares avvik som egentlig er manglende bilag – si det først.

## Kundeinstruks

«Regnskapssystem og byrå» (V) · «Kjente avvik» (KJENT, forklares ikke på nytt) · «Periodiseringer» (faste poster som forklarer timing) ·
«Lønn» (antall ansatte og stillingsprosent, aggregert) · «Bilagsføringsregler» (konto per leverandør).

## Steg

Terskler, typer, formler, mal og bro: `references/metode.md`. `<mappe>` = kort arbeidsmappe, for eksempel `%TEMP%\rr\avvik-ÅÅÅÅ-MM`.

### 1. Tallene (lesing)
Bruk `regnskap.json` fra `regnskapsrapport` i samme økt, ellers:
`npm run -s regnskap -- --client "<klient>" --periode ÅÅÅÅ-MM [--hittil] --sammenlign <forrige|ifjor|budsjett> --vesentlighet <V> --ut <mappe>`.
Behold per linje og konto: denne perioden, sammenligningen, avvik kr og %. Tallene i analysen kommer herfra, aldri fra kundens tekst.

### 2. Velg avvikene (N2)
- Over V: skal forklares. Over terskelen (budsjett 10 %, i fjor 15 %, forrige periode 20 %) og minst V/2: «følg med». Resten samles i broen.
- Prioriter: størst i kroner, størst i prosent, uventet retning, nytt avvik, voksende avvik. Høyst 10 linjer; blir det flere, si hvorfor.
- Kjent avvik i kundeinstruksen med samme beløp: KJENT.

### 3. Dekomponer
- Gi hver linje en type: lønnsdrevet, volumdrevet, skjønnsmessig, kontraktsfast, engangs, periodisering/timing, mva- eller valutaeffekt.
- Lønn: antall lønnsslipper per måned × snittkostnad (`npm run -s lonn -- datoer --client "<klient>" --fra ÅÅÅÅ-MM --til ÅÅÅÅ-MM --json`).
  Bare antall og summer – aldri per ansatt.
- Volum og pris: antall utgående fakturaer og snitt per faktura i begge periodene:
  `npm run -s api -- GET /invoice invoiceDateFrom=<fra> invoiceDateTo=<D> "fields=id,amountExcludingVat" --sider --ut <mappe>/faktura-<periode>.json --client "<klient>"`.
- Kontraktsfast: forventet beløp per periode mot bokført; avviket er prisendring, ny avtale, manglende eller dobbel føring.
- Summen av driverne skal være hele avviket. Det som ikke kan forklares, er «diverse».

### 4. Drill-down: konto → leverandør → bilag
```
npm run -s api -- GET /ledger/posting dateFrom=<fra> dateTo=<D> accountNumberFrom=<konto> accountNumberTo=<konto> "fields=id,date,amount,voucher(number,year),supplier(id,name,organizationNumber,isPrivateIndividual)" --sider --ut <mappe>/poster-<konto>-<periode>.json --client "<klient>"
```
- Én gang for perioden og én for sammenligningen (`dateTo` er eksklusiv; ett kall om gangen). Grupper per leverandør med et lite skript:
  sum nå, sum før, endring, ny leverandør. Topp 3 bilag per konto: bilagsnummer, dato, beløp.
- Inntekter: `customer(id,name,organizationNumber,isPrivateIndividual)` i stedet for `supplier(…)`. Privatpersoner vises som antall og sum.
- Lønnskontoer (5000–5999) drilles ikke ned på ansatt. Fritekst fra posteringene siteres ikke.

### 5. Narrativ (per avvik over V)
«<Linje>: gunstig/ugunstig avvik på <kr> (<%>) mot <sammenligning> for <periode>. Driver: … Utsikt: engangs/vedvarende/snur neste periode.
Tiltak: ingen/følg med/undersøk/periodiser/rett føringen.» Konkret, tallfestet, med motgående poster, 2–4 setninger. Anti-mønstrene i `references/metode.md` § 6 brukes ikke.

### 6. Bro (N3, N4)
- Start = linjen (eller driftsresultatet) i sammenligningen, slutt = samme linje nå, begge fra steg 1. 5–8 drivere i linjens fortegn
  (for resultatlinjer: effekten på resultatet; for en kostnadslinje: økt kostnad som pluss), pluss «Øvrige linjer under V/2» (diverse).
- N3: start + Σ drivere − slutt = 0 på øret. N4: |diverse| / |slutt − start| under 20 %.

**Stopp:** broen går ikke opp, eller «diverse» er 20 % eller mer av avviket – ingen forklaring merkes FORKLART og ingen fil lages; dekomponer videre (steg 3–4) eller si at avviket ikke er forklart.

### 7. Oppfølging (N9)
- Timing: forslag til `periodisering` (konto, beløp, periode, tilbakeføring). Feilføring (feil konto, periode, dobbel føring): korrigeringsbilag
  via `periodisering`, som kjører `bilag manuell` med tørrkjøring. Mva-kode: `bilagskontroll` (M4). Manglende fast kostnad: `periodeavslutning` (A3).
- Vis forslagene som en nummerert ja-liste for de skillene. Kjente avvik som skal kvitteres ut, tilbys lagret i kundeinstruksen.

### 8. Fil
Skriv `<mappe>/avvik.json` (formatet står øverst i `lag_spec.py` i `regnskapsrapport`: rad-id og sammenligning, type, driver, utsikt, tiltak,
status, og en bro med linje-id, sammenligning og drivere – start og slutt hentes fra `regnskap.json`, aldri skrevet inn). Så:
```
uv run --with openpyxl --with pillow --with pypdf python .claude/skills/regnskapsrapport/scripts/lag_spec.py "<mappe>/regnskap.json" --mappe <mappe> --avvik "<mappe>/avvik.json" --bare-avvik
```
Gir «Avviksanalyse <periode> <Klient>.xlsx» med arkene Avvik og Bro, og skriver N3 og N4. Exit 3 = stopp: ingen fil. `sjekk.py` fra `silfer-rapport` skal være grønn.
Uten `--bare-avvik` kommer forklaringene og broen inn i regnskapsrapporten.

## Svar

- Tabell: Linje · Avvik kr (%) · Type · Driver · Utsikt · Tiltak, høyst 10 linjer, størst først. «Følg med»-linjer på én linje hver.
- Broen som liten tabell med kontrollinjen (start + drivere = slutt) og andelen «diverse».
- Funn i funn-formatet for N2–N4 og N9, og ja-listen fra steg 7. Port: rød når N3 eller N4 feiler.
- Firmanavn på leverandører er greit; privatpersoner, ansatte og lønn per person vises aldri.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `ANNET`, periode `ÅÅÅÅ-MM | ÅÅÅÅ-T<n> | ÅÅÅÅ`, samling `Perioderapporter ÅÅÅÅ`, oppgave «Ferdigstillelse perioderegnskap» når den er åpen; byråintern versjon arkiveres rett etter opplasting).

## Fallgruver

- Avvik vises i presentasjonsfortegn: for kostnader er positivt avvik ugunstig. I broen er fortegnet effekten på resultatet.
- Timing gir to avvik (opp nå, ned neste periode). Sjekk fakturaperioden før et avvik kalles vedvarende.
- Brutto bokført kostnad (feil mva-kode) gir 25 % for høy kostnad. Sjekk M4 før driveren kalles pris.
- Budsjett i Tripletex er ofte fordelt likt per måned; sesongvariasjon er ikke drift – si det.
- «Diverse» på 20 % eller mer betyr at analysen ikke er ferdig, ikke at avviket er uvesentlig.
- Hent aldri `employee`-felt i drill-down. `/ledger/posting` uten `--sider` gir bare første side.

## Referanser

- `references/metode.md`: terskler, prioritering, dekomponering, drill-down, narrativ, anti-mønstre, bro og videre til andre skills.
- `docs/kontrollkatalog.md`: N2, N3, N4, N9 (N1 og N5–N8 i `regnskapsrapport`).
- Naboskills: `regnskapsrapport` (tall og `scripts/lag_spec.py`), `periodisering`, `bilagskontroll`, `periodeavslutning`, `silfer-rapport`.
