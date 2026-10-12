---
name: lonnsavstemming-a07
description: "Avstemmer lønnsområdet for en termin: A07 fra Skatteetaten mot Tripletex (forskuddstrekk 2600, AGA 5400/2770, grunnlag per ytelse, pensjon, feriepenger, per ansatt) → Silfer-Excel. Lukker Tally-oppgaven «Terminvis lønnsavstemming». Bruk ved «avstem lønnsområdet på …», «lønnsavstemming», «A07», «avstem a-melding», «skyldig arbeidsgiveravgift», «forskuddstrekk termin»."
---

# Lønnsavstemming A07 mot Tripletex

**Datakilde:** Regnskapsdata hentes via Tripletex-MCP-en (`search_client_companies`, `tripletex_run_script`, `get_amelding_status`, `get_balance_sheet`).
Ikke bruk nettleseren mot Tripletex. Er MCP-en nede: gjør det som kan gjøres uten regnskapsdata (parse A07, forbered ledger-strukturen),
si at Tripletex-koblingen må kobles til igjen, og vent. Hurtigvei for Sjur: `npm run api` i `C:\Users\Sjur\Tripletex API` gir de samme posteringene.

**Personvern:** A07 og lønnsbilag inneholder persondata. Excel-filen lagres i klientens dokumentarkiv i Tally (kundens egne data); i chatten vises bare
summer og avvik, aldri navn eller lønn per person. Slett A07-XML og ledger.json fra scratch når avstemmingen er levert.

Input: A07-fil for én termin (XML primærkilde; ODS er samme data) + klientnavn. Mangler A07: be om filen (Altinn → Skatteetaten → «Avstemmingsinformasjon a-melding», velg termin, last ned XML). Ikke start uten den.
Output: `Lønnsavstemming <Klient> termin <n> <år>.xlsx` (Silfer). Excel-ark: **Avstemming** (rent: post · A07/beregnet · regnskap · avvik · status, tre blokker forskuddstrekk/AGA/feriepenger + antall avvik) · Detaljer (kilde/bilag/merknad per kontroll, innsendingshistorikk, reverserte bilag, merknader) · Forskuddstrekk · Arbeidsgiveravgift (Sticos pkt. 1–5 + pensjon hittil i år + bevegelse 2770) · Per ansatt · Ytelser A07 · Posteringer. PDF-versjon finnes ikke ennå (`lag_pdf.py` er ikke skrevet); lever xlsx.
Filer i skillen: `scripts/hent_tripletex.js` (datauttrekk i `tripletex_run_script`), `scripts/lonnsavstemming_a07.py` (Excel), `scripts/a07.py` (XML-parser), `scripts/kobling.py` (beløpsmatching mot person), `scripts/stil.py` (Silfer-formatering), `scripts/ledger_eksempel.json` (utfylt eksempel), `assets/silfer_logo.png`, `references/kontrollogikk.md` (full kontrollogikk, ledger.json-format og kjente avvik – kortversjon nederst her). Verifiseringsverktøy: `scripts/ledger_fra_rapport.py` henter regnskapssiden ut av en godkjent rapport, `scripts/sammenlign.py` sammenligner ark for ark – kjør begge etter endringer i kontrollogikken.

## Steg

### 1. Les A07 (ikke skriv egen parser)
`parse_a07()` i skriptet leser innsendinger per måned (status, erstatterMeldingsId, levert, AGA, trekk per lønnsdato, KID), AGA-grunnlag lønn/pensjon/fradrag/sats/sone, inntektsmottakere med ytelser per opptjeningsperiode og trekk, betalingsinformasjon. Gjeldende innsendinger per måned = alle som IKKE er erstattet av en annen melding (`erstatterMeldingsId`), uansett status – også `MAA_KONTROLLERES`. De summeres. Statusfeltet avgjør altså ikke; dette er verifisert mot ferdige avstemminger. Ytelser uten opptjeningsperiode (feriepenger til sluttede) legges i måneden der grunnlaget mangler omtrent beløpet, pensjonsgrunnlaget medregnet.
Sjekk selv før du går videre: flere innsendinger samme måned (= korrigeringer/tillegg → forløpet skal forklares), negative trekkbeløp (tilbakebetaling av lønn), personer uten ansattnummer/opptjeningsperiode, `fradragIGrunnlagetForSone` (refusjon fra NAV → reduserer AGA-grunnlag).

### 2. Hent regnskapet fra Tripletex (MCP)
1. `search_client_companies` → klientens navn slik Tripletex skriver det.
2. Kjør `scripts/hent_tripletex.js` i `tripletex_run_script`: les fila, sett `KLIENT`, `D1` (første dag i termin), `D2` (første dag etter termin) og `Y1` (1. januar), og send hele teksten som `code`. Den henter posteringer 1950/2600/2770–2799/2900–2999/5000–5999/7100–7199/7740 + lønnslinjer på 1920, saldoer og pensjon hittil i år, og returnerer `{balanser, posteringer, pensjon_rader, advarsler}`. Les `advarsler` først. Første gang på en klient: sjekk at feltene (dato, bilag, konto, beløp) er fylt; er de tomme, se formen med ett `search_ledger_postings`-kall og rett `felt()` i `rad()`. Er svaret for stort, del terminen i to kall (én måned hver).
3. `get_amelding_status` for siste måned i terminen: `accrued`/`notPaid` taxDeduction + payrollTax skal stemme med A07 (negativ notPaid taxDeduction = for mye innbetalt trekk).
4. Hvis 2770 IB ≠ forrige termins a-meldte AGA: hent 2770 for forrige termin og forklar restsaldoen.

### 3. Bygg `ledger.json` (kopier strukturen fra `ledger_eksempel.json`)
`selskap`, `orgnr`, `tripletex_id`, `periode{fra,til,termin,forfall}` (forfall = 15. i måneden etter terminslutt), `aga_sats`, `feriepenger_sats` (les 5020/5000 i et lønnsbilag: 0,12 / 0,125 / 0,143), `kid_aga`, `kid_trekk{}`, `ytelse_konto{}` (kun avvik fra standard, f.eks. `"elektroniskKommunikasjon": 5390` når EK er utgiftsgodtgjørelse), `konto{pensjon}` (autodetekt 5945/5950), `balanser[{a,n,ib,ch,ub}]`, `posteringer[[dato,bilag,konto,kontonavn,tekst,beløp]]`, `pensjon_historikk[[«YYYY-MM», tekst 594x, beløp, tekst pensjonsbilag, grunnlag]]` for hele året (grunnlag = AGA i pensjonsbilaget / sats), `forklart[]` (prefiks på kontrollrader som skal vises FORKLART i stedet for AVVIK – kun når merknaden forklarer avviket fullt ut), `merknader[]` (Excel, kan være utfyllende), `merknader_kort[]` (PDF: én setning per punkt med beløp + bilag + tiltak).

### 4. Kjør og verifiser
Arbeidsfilene (A07-XML, ledger.json, Excel) ligger i scratch til de er lagret i Tally.
```bash
uv run --with openpyxl --with pillow python .claude/skills/lonnsavstemming-a07/scripts/lonnsavstemming_a07.py <scratch>/a07.xml <scratch>/ledger.json "<scratch>/Lønnsavstemming <Klient> termin <n> <år>.xlsx"
```
LibreOffice finnes ikke på maskinene, så formlene beregnes først når filen åpnes i Excel. Kontroller med openpyxl at ingen celle inneholder feilverdier (`#REF!`, `#VALUE!`, `#DIV/0!`) og at summene i «Avstemming» stemmer med ledger.json. Dump alle ark og les dem. Krav før levering:
- «Avstemming»: antall AVVIK = 0, eller hvert AVVIK er reelt og har merknad. FORKLART kun med merknad.
- «Per ansatt»: alle rader OK, ingen «Koblingsproblemer» (ellers: feil `ytelse_konto`, eller tillegg ført utenfor lønnsbilag/reiseregning).
- «Arbeidsgiveravgift» pkt. 2: «Uforklart differanse» = 0. Konti merket «NEI – kontroller» (bevegelse uten lønnsbilag, typisk 5320) = mulig ikke-innrapportert fordel → merknad.
- Pensjonstabell hittil i år: differanse 0; ellers merknad med AGA-effekt og «korriger i neste a-melding».
- Pkt. 3/4: «Kreditert 2770» = innrapportert; UB 2770 = innrapportert (ellers restsaldo → merknad).
- «Forskuddstrekk»: UB − IB − innbetalt + a-meldt = 0. Debetsaldo 2600 = for mye innbetalt (trekk betalt på lønnsdato, reversering kjørt etterpå).
Merknader = korte faktasetninger med bilagsnr., beløp, årsak, tiltak – ikke prosa.

### 5. Lever
- **Lagre i Tally** etter ja (`docs/dokumentlagring.md`): Excel-filen og A07-XML, kategori `LONN`, periode `ÅÅÅÅ-T<n>`, samling `Lønn ÅÅÅÅ`, knyttet til oppgaven
  «Terminvis lønnsavstemming». Kontroller med `list_documents` og gi lenken. Kan den ikke lagres, si det og del filen i chatten.
- Bruker byrået avstemmingsmodulen i Tripletex for lønn, er kommentarer og vedlegg der **Krever CLI (Sjur) eller Tripletex-UI:** (se `tripletex-api/docs/avstemmingsmodul.md`).
  Kommentarer er én kort setning, for eksempel «Utbetalte feriepenger.» eller «Kravet skyldes ubetalt AGA etter korreksjon, se vedlegg.»
- Svar 3–6 linjer: stemmer/avvik, skyldig AGA + forfall + KID, hvert avvik med beløp og tiltak. Ingen navn eller beløp per person.
- Fullfør i Tally: foreslå tidsbruk, spør, og ved ja `add_task_comment` + `log_time` + `complete_task` (se `tally-gjoremal`).
- Slett A07-XML, ledger.json og Excel-filen fra scratch når de er lagret i Tally.

## Skriptene

Ligger i `scripts/`. Excel-skriptene er verifisert mot ferdige avstemminger fra september 2026; `hent_tripletex.js` er nytt (oktober 2026) og må kontrolleres mot ett ekte uttrekk første gang:

| Fil | Gjør |
|---|---|
| `hent_tripletex.js` | datauttrekk i `tripletex_run_script`: posteringer, saldoer og pensjon hittil i år |
| `a07.py` | parser A07-XML: innsendinger, grunnlag, ytelser per person, trekk |
| `kobling.py` | kobler A07-beløp mot lønnsbilagslinjer ved beløpsmatching |
| `stil.py` | Silfer-formatering (farger, fonter, statusregler) |
| `lonnsavstemming_a07.py` | bygger de sju arkene |
| `ledger_eksempel.json` | utfylt eksempel på regnskapssiden |

`references/kontrollogikk.md` har full kontrollogikk, formatet på `ledger.json`,
verifiseringsstatus og hva som avhenger av riktig oppsett (særlig `ytelse_konto`
og `pensjon_historikk`). Les den før første kjøring på en ny klient.

Ikke skriv skriptet på nytt. Finner du en feil, rett den i `scripts/` og kjør
verifiseringen mot en eksisterende rapport på nytt.

## Fallgruver
- **Ikke nettleseren mot Tripletex.** MCP-en nede → si fra, vent, prøv igjen.
- `get_balance_sheet` utelater 2600 når IB/bevegelse/UB = 0 – bruk posteringene.
- A07 gir trekk per person for hele terminen; månedsfordeling kommer fra 2600-linjene.
- EK: naturalytelse (5210 + motkonto 5290) eller utgiftsgodtgjørelse (5390, kontant) – les `fordel`.
- AGA av utbetalte feriepenger går 2785/2780 → 2770, ikke via 5400.
- NAV-refusjon (sykepenger/foreldrepenger) rapporteres som `fradragIGrunnlagetForSone` – ofte i egen tilleggsmelding med negativ AGA; i regnskapet 2770-debet / 5400-kredit (AGA) og 58xx/5000-kredit (grunnlag).
- Tripletex runder AGA ned til hele kroner per måned; 0–1 kr/måned er normalt. Avrundingsbilag «A-melding lønn» kan være reversert og kjørt på nytt.
- Sticos «for året» kan mangle terminer – Tripletex saldobalanse er fasit hittil i år.
- Ikke start celletekst med `=`.

## Kontrollogikk (kortversjon – full versjon i references/kontrollogikk.md)
**Begreper:** Reversert bilag = «Reversering av bilag N-ÅÅÅÅ» + original N, nettes til null → utenfor alle kontroller, listes i egen tabell. Avrundingsbilag = «A-melding lønn <mnd>» (øre på 2770/2600 mot 7740). Lønnsbilag = tekst «Lønnsbilag N-ÅÅÅÅ», ikke «Betaling:».

**Forskuddstrekk (2600):** per lønnsdato: A07 `sumForskuddstrekkPerLoennsutbetalingsdato` (gjeldende) = −Σ 2600 i lønnsbilag samme dato (±1 kr). Termin: A07 Σ per person = −Σ 2600 lønnsbilag − avrundingsbilag. Innbetalt = Σ 2600-debet «Betaling:…»; avvik mot a-meldt = for mye (−)/for lite (+). Alltid: UB − IB − innbetalt + a-meldt = 0. Direkte-modell (Tripletex «Betaling: Lønnsbilag» 2600/1920 på lønnsdato): 2600 = 0, 1950 ubrukt. Skattetrekkskonto-modell: 1950 ≥ 2600. Negativt trekk = tilbakebetaling; betalt trekk + reversering → 2600 debet = tilgodehavende → motregn 15. / krev tilbake.

**AGA-grunnlag (pkt. 2):** A07 grunnlag lønn = Σ ytelser med `utloeserArbeidsgiveravgift=true`, avrundet ned per måned. Regnskap = bevegelse 5000–5399 (unntatt 5020, 5290) + 5500–5599 + utbetalte feriepenger (2940-debet i lønnsbilag uten lønnslinjer) + pensjonskonto − NAV-refusjon (58xx). Mapping: fastloenn/timeloenn/overtid/uregelmessige tillegg→5000, bonus→5001, sykepenger→5030, feriepenger→2940 debet, bil→5200, elektroniskKommunikasjon→5210 eller 5390, annet→5260, reiseKost + trekkpl. km→5510; avgiftsfri km/passasjer/kost overnatting→7100/7150 (utenfor grunnlag). Differanse forklares: (1) pensjon periodisering = innrapportert (pensjonsbilag/sats) − 594x i perioden, hittil i år skal være 0; (2) konti med bevegelse uten lønnsbilag = ikke innrapportert fordel; (3) avrunding < 1 kr/mnd.

**AGA (pkt. 1/3/4):** beregnet = (lønn + pensjon − refusjon) × sats; innrapportert = Σ gjeldende per måned (0–1 kr/mnd under beregnet); kostnadsført = 5400 + AGA av utbetalte feriepenger (2780/2785-debet) ≈ beregnet (øre); kreditert 2770 (lønnsbilag + pensjonsbilag − avrundingsbilag) = innrapportert nøyaktig; UB 2770 = innrapportert (avvik = gammel rest). Per måned: (grunnlag lønn mnd + pensjonsgrunnlag mnd − refusjon mnd) × sats ≈ innrapportert mnd. Betaling 15. i mnd etter termin, KID `kidForArbeidsgiveravgift`.

**Feriepenger:** linjerekkefølge per konto i lønnsbilag = samme ansatt (5000↔5020↔5401), men 2600 mangler linje ved trekk 0 → beløpsmatching. 5020 = sats × 5000-linje; 5401 = AGA-sats × 5020; Σ 5020 = −Σ 2940-kredit; negativ kjøring gir negative 5020/5401 (ikke utbetaling). Utbetalte feriepenger = 2940-debet i lønnsbilag uten lønnslinjer = A07 `feriepenger`.

**Personkobling:** per måned/konto: mål per person fra A07 (Σ ytelser med samme konto) → fordel lønnsbilagslinjer ved backtracking (±0,02; flere linjer per person tillatt). AGA per person: 2770-kreditter i lønnsbilag mot Σ AGA-pliktig × sats (±0,06). Trekk per person: 2600-linjer for hele terminen mot A07 (±1 kr).

**Typiske funn:** 2600 debet = negativt trekk i A07 → motregn; flere innsendinger/måned → bruk GODKJENT (erstatninger erstatter, tillegg summeres), forklar; pensjon periode≠, hittil i år = 0 → forklart; hittil i år ≠ 0 → korriger a-melding (AGA-effekt = diff × sats); 2770 UB ≠ innrapportert → rydd; 53xx uten lønnsbilag → avklar skatteplikt; person uten ansattnr/periode → feriepenger til sluttet (2940-debet).