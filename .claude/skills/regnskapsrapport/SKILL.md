---
name: "regnskapsrapport"
description: "Resultatregnskap og balanse for en Tripletex-klient for måned, termin, år eller hittil i år, artsinndelt etter rskl. §§ 6-1 og 6-2 for små foretak, med sammenligning mot forrige periode, i fjor og budsjett, avvik i kr og %, nøkkeltall og vesentlige avvik med oppfølging, som Silfer-Excel og -PDF. Ingen Tally-oppgave. Bruk ved «regnskapsrapport», «resultatregnskap for <klient>», «balansen per <dato>», «hvordan går det for <klient>», «sammenlign med i fjor», «nøkkeltall for <klient>», «resultat hittil i år»."
---

# Regnskapsrapport

Lager tallene og filen: resultat og balanse i norsk oppstilling med sammenligningstall, avvik, nøkkeltall og en liste over vesentlige avvik.
Hvorfor et avvik oppstod, forklares i `avviksanalyse`. Utkast til månedsrapport i Tally og periodelås eier `periodeavslutning`;
avstemming av balansekontoene er `balanseavstemming`.

## Når

- Ingen Tally-oppgave: rapporten er grunnlag for «Ferdigstillelse perioderegnskap» (`periodeavslutning`), styremøter, kundens spørsmål og årsoppgjøret.
  `periodeavslutning` kaller skillen for hovedtall og fil; den fullfører oppgaven selv.
- Tallene er ikke bedre enn ajourholdet. Kjør etter `bilagsforing` og `bankavstemming` for perioden; ellers merkes rapporten «foreløpig».
- Brukeren oppgir klient og periode: `ÅÅÅÅ-MM`, `ÅÅÅÅ-T<n>` (tomånederstermin), `ÅÅÅÅ` eller «hittil i år». Standard sammenligning: forrige periode og samme periode i fjor, budsjett når det finnes.

## Kundeinstruks

«Regnskapssystem og byrå» (V, regnskapsår, selskapsform – AS styrer egenkapitalflagget) · «Reskontro og balanse» (kontoplanavvik) ·
«Kjente avvik» (KJENT i avvikslisten) · bransje (varelager: varetelling og 4090; prosjekt). Mangler V: standarden i CLAUDE.md.

## Steg

`<mappe>` = kort arbeidsmappe, for eksempel `%TEMP%\rr\regnskap-ÅÅÅÅ-MM`. Alle kall med `--client "<klient>"`.

### 1. Ajourhold (lesing)
`npm run -s status -- --client "<klient>" --maaned ÅÅÅÅ-MM --json` (siste måned i perioden) → bilagsmottak, bank lukket, perioder.
Åpent mottak, åpne bankmåneder eller ubehandlede bilag: rapporten får «Foreløpig – ikke ferdig ajourført» i periodeteksten, og svaret sier hvorfor.

### 2. Tallene
```
npm run -s regnskap -- --client "<klient>" --periode ÅÅÅÅ-MM [--hittil] --sammenlign forrige,ifjor,budsjett --vesentlighet <V> --ut <mappe>
```
- `--periode ÅÅÅÅ-T<n>` for termin, `ÅÅÅÅ` for år. `--hittil` gir 1.1 til periodens slutt, sammenlignet med samme månedsantall i fjor.
- Konsollen gir grupper, summer, flaggede kontoer, nøkkeltall og kontrollene; alt ligger i `<mappe>/regnskap.json`. Ikke bruk `--json`
  (hele filen til konsollen). Konsollens flagg bruker én terskel; tersklene per sammenligning brukes i steg 4–5.
- «Budsjett ikke funnet»: kolonnen utelates, og rapporten sier det. Claude lager aldri budsjett selv.

### 3. Kontroller (N1, N5–N8)
Grupper, fortegn, nøkkeltall og normalområder: `references/oppstilling.md`.
- **N1 Resultat mot balanse:** sum eiendeler = sum egenkapital og gjeld med «Årets resultat (ikke disponert)» (−Σ 3000–8999). «Udisponert
  resultat tidligere år» ≠ 0: FORKLART til og med juni, MERKNAD fra juli. Rest etter de to linjene: AVVIK.
- **N6 Fullstendig oppstilling:** alle kontoer med saldo ligger i en gruppe, og sum gruppene = saldobalansen. Saldo på 8500–8799: MERKNAD.
- **N7 Sammenligningstall på samme grunnlag:** samme antall måneder, samme kontoer i gruppene; kontoplanendring eller ompostering mellom grupper nevnes (rskl. § 6-6).
- **N8 Uventet fortegn:** konto mot gruppens fortegn med minst V/10 (inntekt i debet, kostnad i kredit, bank i minus); kontrakontoer unntatt.
- **N5 Nøkkeltall utenfor normalområdet:** bruttomargin, driftsmargin, lønn i % av inntekt, likviditetsgrad 1, egenkapitalandel.

**Stopp:** N1 er AVVIK – ingen fil til kunden; vis differansen og send saken til `balanseavstemming` (S9) før rapporten lages.

### 4. Vesentlige avvik (N2)
- Per linje og sammenligning: AVVIK når |avvik| ≥ V; MERKNAD når |avvik %| ≥ terskel (budsjett 10, i fjor 15, forrige periode 20) og
  |avvik| ≥ V/2; KJENT når kundeinstruksen har samme beløp. `lag_spec.py` gjør utvalget: én linje per konto, størst først, maks 10.
- Hver linje får retning (gunstig/ugunstig) og foreslått oppfølging: «forklar i `avviksanalyse`», «følg med», «periodisering mangler →
  `periodisering`», «vurder aktivering» (6500–6599 over 30 000 kr) eller «undersøk føringen».
- Er `avviksanalyse` kjørt i samme økt, brukes forklaringen og broen derfra (`<mappe>/avvik.json`), og status blir FORKLART.

### 5. Fil
```
uv run --with openpyxl --with pillow --with pypdf python .claude/skills/regnskapsrapport/scripts/lag_spec.py "<mappe>/regnskap.json" --mappe <mappe> [--avvik "<mappe>/avvik.json"] [--bare-grupper] [--format xlsx,pdf]
uv run --with openpyxl --with pypdf python .claude/skills/silfer-rapport/scripts/sjekk.py "<mappe>/Regnskapsrapport <periode> <Klient>.xlsx" "<…>.pdf"
```
- Ark: Resultat og Balanse (oppstilling med formler for summer, resultatlinjer og avvik), Nøkkeltall, Avvik, og Bro når `avvik.json` har en bro.
- `--bare-grupper` gir én linje per gruppe (kortversjon til kunden); standard er kontolinjer under hver gruppe.
- Skriptet skriver hovedtallene, N1, N2, N5, N6 og N8 (N7 vurderes i steg 3); de skal stemme med steg 2–3. Exit 3 = stopp (N1 AVVIK, eller broen går ikke opp):
  ingen fil er laget. `sjekk.py` skal være grønn før filen lagres. `--forelopig "<grunn>"` merker rapporten fra steg 1.

## Svar

- Port (grønn/gul/rød) og hovedtall på 3–5 linjer: driftsinntekter, driftsresultat, periodens resultat, bank og egenkapital, med sammenligning i kr og %.
- Nøkkeltall: Nøkkeltall · Denne · Forrige · I fjor · Status.
- Vesentlige avvik i funn-formatet (ID · Klient · Periode · Konto/motpart · Beløp · Status · Forslag · Krever), maks 10 linjer.
- Aldri lønn per ansatt, navn på personer eller banktekster. Filen er leveransen; oppstillingen limes ikke inn i chatten.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `ANNET`, periode `ÅÅÅÅ-MM | ÅÅÅÅ-T<n> | ÅÅÅÅ`, samling `Perioderapporter ÅÅÅÅ`, oppgave «Ferdigstillelse perioderegnskap» når den er åpen for perioden).

## Fallgruver

- Tripletex har inntekter, egenkapital og gjeld med minus. Oppstillingen viser dem positive; for kostnader er positivt avvik ugunstig.
- Midt i året er årets resultat ikke overført til 2050/2080. Uten «udisponert resultat hittil i år» går balansen ikke opp.
- Skattekostnad, avskrivninger, periodiseringer og varetelling kan mangle før årsoppgjøret. Si det i merknaden, ikke i tallene.
- Grupper følger kontonummer (NS 4102), ikke kontonavn. Klienter med egne kontoer utenfor intervallene gir N6.
- Termin er to måneder; forrige periode for et år er fjoråret, og hittil i år sammenlignes med samme månedsantall.
- Små foretak har ikke kontantstrømoppstilling (rskl. § 3-2); endring i bank leses av balansen.

## Referanser

- `references/oppstilling.md`: grupper og kontointervaller, fortegn, flagg, nøkkeltall og normalområder, årsregnskapsnoter.
- `scripts/lag_spec.py`: `regnskap.json` (+ `avvik.json`) → spec → xlsx/pdf via `silfer-rapport` (oppstilling og bro).
- `docs/kontrollkatalog.md`: N1, N2, N5–N8 (N3, N4 og N9 i `avviksanalyse`). Naboskills: `avviksanalyse`, `periodeavslutning`,
  `balanseavstemming`, `periodisering`, `silfer-rapport`.
