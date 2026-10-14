---
name: "periodisering"
description: "Manuelle føringer i Tripletex med kontroll før bokføring: påløpte kostnader (29xx), forskuddsbetalte kostnader (17xx), avskrivninger mot anleggsregisteret, feriepenger og påløpt lønn, forskuddsfakturert og opptjent ikke fakturert inntekt, omposteringer og korrigeringsbilag, med tilbakeføring. Ingen Tally-oppgave. Bruk ved «periodiser <kostnad>», «påløpte kostnader for <måned>», «forskuddsbetalt <kostnad>», «avskrivninger for <måned>», «manuell føring», «ompostering», «korrigeringsbilag», «tilbakefør periodiseringen»."
---

# Periodisering og manuelle føringer

Beregner, viser og fører manuelle bilag for en periode: periodiseringer, avskrivninger, lønnsperiodiseringer, inntektsperiodisering, omposteringer
og korrigeringer – alltid gjennom føringskontrollen J1–J12 og én tørrkjøring. Bilag fra mottaket mot bank føres i `bilagsforing`; avstemming av
17xx/29xx er `balanseavstemming`; sjekklisten per 31.12 er `aarsoppgjoer-forberedelse`.

## Når

- Ingen egen Tally-oppgave: føringene er en del av «Ferdigstillelse perioderegnskap», som `periodeavslutning` eier og fullfører. Kjøres etter
  `bilagsforing` og `bankavstemming`, før `balanseavstemming` og `periodeavslutning`, og når en av dem foreslår en retting.
- Brukeren oppgir klient, periode `ÅÅÅÅ-MM` og hva som skal føres (én post, en type eller «faste periodiseringer»). Uten mer: postene i «Periodiseringer».

## Kundeinstruks

«Periodiseringer» (faste poster: konto, beløp per måned, fra–til, tilbakeføring) · «Regnskapssystem og byrå» (V) · «Lønn» (feriepengesats) ·
«Bilagsføringsregler» (konto per leverandør) · «Årsoppgjør» (det som bevisst venter) · «Kjente avvik». Mangler «Periodiseringer»: «ikke avklart».

## Steg

Alle kall med `--client "<klient>"`. `<mappe>` = kort arbeidsmappe (for eksempel `%TEMP%\rr\periodisering-ÅÅÅÅ-MM`). D = første dag etter perioden
(`dateTo` er eksklusiv). Typene, beregningen og typiske kontoer: `references/typer.md`. Planformatet og tilbakelesingen: `references/plan.md`.

### 1. Grunnlag (bare lesing)
1. Postene: «Periodiseringer» i kundeinstruksen, det brukeren ber om, og forslag fra naboskillene (A3, S3, A4, L3, P1).
2. Forrige periodes tilsvarende føring på de samme kontoene:
   `npm run -s api -- GET /ledger/posting dateFrom=<forrige mnd>-01 dateTo=ÅÅÅÅ-MM-01 accountNumberFrom=<fra> accountNumberTo=<til> "fields=date,amount,description,account(number),department(departmentNumber),voucher(id,number,year)" --sider --ut <mappe>/forrige.json`
3. Saldo: `npm run -s regnskap -- --client "<klient>" --periode ÅÅÅÅ-MM --sammenlign forrige --json --ut <mappe>`, eller `/balanceSheet` med
   `dateFrom=ÅÅÅÅ-01-01 dateTo=D accountNumberFrom=1500 accountNumberTo=2999 "fields=account(number,name),balanceIn,balanceChange,balanceOut"`.
4. Gjør Tripletex jobben selv? Periodisering på leverandørbilaget (`amortizationAccount` på posteringen), avskrivning fra anleggsregisteret
   (`/asset`, `/asset/<id>/postings`; `npm run -s finn -- anlegg avskrivning`), feriepenger fra lønnskjøringen (2940 på lønnsbilag). Da er jobben kontroll.
5. Dokumenter: originalbilaget med `npm run -s dokument -- --client "<klient>" --bilag <nr-år> --ut <mappe>/dok`; avtaler i Tally `list_documents`.
6. Låser: `/ledger/accountingPeriod startFrom=ÅÅÅÅ-MM-01 startTo=D "fields=id,start,end,isClosed"`. Linjer på 19xx: `lukket` fra
   `npm run -s bankavstemming -- --til ÅÅÅÅ-MM --client "<klient>" --ut <mappe>`. Linjer med mva-kode: `npm run -s mva -- status --client "<klient>" --aar ÅÅÅÅ --termin N --json`.
   Dato i fjoråret: Tally `get_arsoppgjor_status`.

**Stopp:** perioden er låst, bankavstemmingen for en linje på bankkonto er lukket, eller terminen for en mva-linje er levert – si hva som er lukket,
og foreslå føring i åpen periode eller termin; gjenåpning avgjør regnskapsfører (`docs/foringskontroll.md`, «Godkjenning»).
**Stopp:** datoen ligger i et år der årsoppgjøret er levert – før ingenting; legg forslaget fram for oppdragsansvarlig.

### 2. Beregn
- Én beregning per post: formel, tall og kilde (avtale, faktura, anleggskort, samlet lønnsgrunnlag). Konto fra kundeinstruksen, så forrige periodes
  føring, så kontoplanen (`/ledger/account number=<nr> "fields=id,number,name,isInactive,vatLocked,requiresDepartment,requiresProject"`). Aldri gjett.
- Mva-kode 0 på periodiseringsbilag (mva følger fakturaen). Lønn bare som sum per konto, aldri per ansatt.

**Stopp:** et estimat har verken kildedokument eller beregning – spør brukeren (eller kunden via brukeren); før aldri et rundt beløp «til fakturaen kommer».

### 3. Forslag (fast format)
Per bilag en tabell Linje · Konto · Navn · Debet · Kredit · Avd. · Tekst med sumlinje (eksempel i `references/plan.md`), så tre linjer:
**Grunnlag** (beregning og dokument) · **Tilbakeføring** (ja + dato, eller nei) · **Forrige periode** (bilag og beløp, endring i kr og %, eller «ingen»).
Endring over 10 % mot forrige periode forklares i grunnlaget.

### 4. Kontroll (J1–J12)
Kjør `docs/foringskontroll.md` i rekkefølge. Tørrkjøringen (steg 5) tar den maskinelle delen av J1–J12; Claude går gjennom resten før tørrkjøringen:
levert årsoppgjør (J2), mva på periodisering og § 8-3 (J4), periodisering mot reskontro (J6), «Tripletex fører selv» og faktura allerede bokført (J7),
tilbakeføring for andre typer enn 296x (J8), estimat uten beregning (J10), grunnlaget (J11) og innholdet i beskrivelsen (J12).

**Stopp:** linjene går ikke i null (J1), eller en kontroll gir FEIL – rett planen og kjør tørrkjøringen på nytt.
**Stopp:** beløp over V (J9) uten forklaring i grunnlaget – be om forklaringen; ja-et må nevne beløpet.

### 5. Tørrkjøring
Skriv `<mappe>/manuell.json` (Write, UTF-8): én rad per bilag, stabil `ref`, `tilbakefor` på påløpte poster, kildedokument og beregning i `vedlegg`. Så:
`npm run -s bilag -- manuell --client "<klient>" --plan <mappe>/manuell.json --vesentlighet <V>` – ingenting føres. Sammenlign sum debet/kredit og
PASS/FEIL/ADVARSEL/INFO per kontroll med forslaget i steg 3. Endrer noe seg, vis forslaget på nytt.

### 6. Ett samlet ja
Nummerert liste: ref · dato · beløp · tilbakeføring · vedlegg, og hvem som må si ja (`docs/foringskontroll.md`, «Godkjenning»). Svarformat: «ja», «ja 1–3, 4 vent».

**Skriving (etter ja):** `npm run -s bilag -- manuell --client "<klient>" --plan <mappe>/manuell.json --vesentlighet <V> --bekreft` – kjør først uten --bekreft og vis tørrkjøringen.
Oppretter bilaget, laster opp og bekrefter vedlegget, og lager tilbakeføringen. Mange bilag: først ett med `--bare <ref>`, så resten.

**Bare i Tripletex-UI:**
1. Avskrivninger for klienter med anleggsregister: Anleggsregister → Avskrivninger → velg måned → bokfør. API-et har ikke kall for å kjøre dem.
2. Gjenåpne en låst periode, og lås den igjen etterpå – bare etter regnskapsførerens ja.

### 7. Tilbakelesing og kvittering
- `<mappe>/manuell.resultat.json`: ref → bilagsnummer, tilbakeføring, vedlegg og feil. En ref med feil er «ikke gjort»; ny kjøring hopper over ferdige.
- Les saldoen fra steg 1.3 på nytt og vis UB før og etter på de berørte kontoene. Etter UI-steget: `/asset/<id>/postings` for måneden.

## Svar

- Først «Fra instruksen» (faste poster og V, maks fire linjer), så forslaget per bilag (steg 3).
- Funn fra J1–J12 i funn-formatet (ID · Klient · Periode · Konto/motpart · Beløp · Status · Forslag · Krever), bare FEIL og ADVARSEL, maks 10 linjer.
- Nummerert ja-liste og UI-punktene til slutt. UI-punkter er «ikke gjort» til de er lest tilbake.
- Kvittering: ref · bilag · beløp · tilbakeføring (bilag, dato) · vedlegg · status, og hva som står igjen.
- Lønn bare som sum per konto. Ingen navn, ingen beløp per person, ingen banktekster.

## Lever

Ingen fil i Tally og ingen Tally-oppgave. Leveransen er bilaget i Tripletex med kildedokument eller beregning som vedlegg (`docs/dokumentlagring.md`,
«Tripletex i tillegg»). Beregning som ikke står i et kildedokument: `silfer-rapport` (spec.json → pdf, `Periodisering ÅÅÅÅ-MM <Klient>.pdf`).
Nye eller endrede faste poster tilbys lagret i «Periodiseringer» (`kundeinstruks`). Arbeidsmappa slettes etter kvitteringen.

## Fallgruver

- Tripletex fordeler selv en kostnad som er ført med periodisering på bilaget (`amortizationAccount`, `amortizationStartDate`, `amortizationEndDate`). Et manuelt bilag i tillegg gir dobbel kostnad.
- `bilag manuell` kobler ikke posteringer til et anlegg. Manuell avskrivning mot 12xx når klienten har anleggsregister gir register ≠ hovedbok; bruk UI-steget.
- `/asset` gir 403 når nøkkelen eller klienten mangler anleggsmodulen: si «anleggsregisteret ikke lest», les 60xx i hovedboken og spør om klienten har
  registeret. `/asset/<id>/postings` har `dateFrom`/`dateToExclusive` lik i dag som standard – sett perioden. `lifetime` er i måneder.
- Avdeling på posteringer heter `department(departmentNumber)`; `department(number)` gir 400. I planen er avdeling og prosjekt id-er, ikke nummer.
- Lønnsbilag kan ikke reverseres med API. Feil i lønn og feriepenger fra lønnskjøringen rettes i lønn (`lonnskjoring`), ikke med et manuelt bilag.
- `ref` må være stabil (`<type>-<post>-ÅÅÅÅ-MM`): ny ref for samme post gir dublett ved ny kjøring.
- Bank- og OCR-bilag gir 422 ved endring. Rett med et korrigeringsbilag som viser til originalen, aldri ved å endre originalen.

## Referanser

- `docs/foringskontroll.md`: J1–J12, vanlige feil, godkjenning, dokumentasjon per føring. `references/typer.md` (typene), `references/plan.md` (manuell.json).
- `docs/kontrollkatalog.md`: S3 (17xx/29xx), A3 (manglende faste kostnader), A4 (avskrivning og aktivering), L3 (feriepenger), P1 (ufakturerte timer), D5.
- Naboskills: `periodeavslutning` (eier Tally-oppgaven), `balanseavstemming`, `lonnsavstemming`, `aarsoppgjoer-forberedelse`, `bilagsforing`, `bilagskontroll`, `kundeinstruks`.
