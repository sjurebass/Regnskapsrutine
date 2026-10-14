---
name: "periodeavslutning"
description: "Ferdigstillelse av perioderegnskapet for en Tripletex-klient: sjekk at bilag, bank, reskontro, balanse, a-melding og mva for perioden er ferdige, rimelighet mot fjoråret og byråets terskler, manglende faste kostnader, hovedtall og utkast til månedsrapport i Tally, og perioden klar til låsing. Lukker Tally-oppgavene «Ferdigstillelse perioderegnskap» og «Lukking av regnskapsperiode». Bruk ved «periodeavslutning», «ferdigstill perioderegnskapet», «månedsavslutning for <klient>», «er <måned> klar til å lukkes», «lukk perioden», «månedsrapport», «perioderapport»."
---

# Periodeavslutning

Sjekkpunktet etter månedens kontroller: er alt ferdig for perioden, er tallene rimelige, og er perioden klar til å lukkes. Skillen avstemmer
ikke selv; den leser resultatet fra `bankavstemming`, `reskontroavstemming`, `balanseavstemming`, `a-melding` og `mva-innlevering` og peker
på det som mangler. Publisering av månedsrapporten, lukking i Tally og periodelås i Tripletex gjør regnskapsføreren.

## Når

- Tally «Ferdigstillelse perioderegnskap» og «Lukking av regnskapsperiode» (uten frist), sist i måneden: bilag → bank → reskontro og balanse → mva og lønn.
- Brukeren oppgir klient og periode `ÅÅÅÅ-MM`. «Alle» gir bare porttabellen fra steg 1, ikke rimelighet eller rapport.

## Kundeinstruks

«Regnskapssystem og byrå» (V) · «Mva» (termin: er perioden terminslutt?) · «Lønn» · «Reskontro og balanse» · «Kjente avvik» (dempes i A1–A3) ·
bransje (prosjekt, varelager, utleie) styrer P1–P4.

## Steg

Utkast – kalibreres mot første klient. Følg stegene, men si fra om noe ikke stemmer med det verktøyene gir.

D = første dag etter måneden (`dateTo` og `date` er eksklusive). Lesing: `npm run -s api -- GET <sti> <parametre> "fields=…" --client "<klient>"`.

### 1. Port (kommando og Tally)
- `npm run -s status -- --client "<klient>" --maaned ÅÅÅÅ-MM --json` → bilagsmottak, ikke bokførte bilag i perioden, bank lukket per konto,
  1500/2400 åpne poster mot UB, a-melding (gruppe), observasjonskonti, perioder lukket og mva for siste termin. «Alle»: `--alle` i stedet for `--client`.
- `npm run -s amelding -- status --client "<klient>" --maned ÅÅÅÅ-MM --json` → ubetalt trekk og arbeidsgiveravgift med forfall den 15.
- I terminmåneder: mva levert og betalt fra `status`; kvitteringen ligger i Tally `list_altinn_innboks` (2740 som i `mva-innlevering`).
- Tally `list_tasks` (klient, åpne) → månedsoppgavene for perioden.
- F1 bilagsmottak · F2 bank · F3 reskontro · F4 a-melding, trekk og mva · F5 observasjonskonti · F6 Tally-oppgaver · D4 forrige periode låst.
  Detaljer i `references/kontroller.md`. Rødt punkt: pek på skillen som løser det, og stopp før steg 4.

### 2. Rimelighet (A1–A3)
- Tally `hent_kontoavstemming` (klient, periode, bare flaggede) → kontoer over byråets terskler, med kundens beslutninger og kommentarer (A1).
- Tally `kontoutvikling` (siste 12 måneder, sammenlignet med i fjor) → A2 (over 30 % og over V) og A3 (fast kostnad i minst 9 av 12 måneder, 0 nå).
- Tally `hent_posteringer` for å forklare en flagget konto. Kjente avvik dempes; avvik under V vises ikke.
- P1–P4 bare når kundeinstruksen sier prosjekt, varelager eller utleie.

### 3. Hovedtall (fra `/balanceSheet`)
- `/balanceSheet dateFrom=<fra> dateTo=D accountNumberFrom=3000 accountNumberTo=8999 "fields=account(number,name),balanceChange"` for måneden
  (`dateFrom` = ÅÅÅÅ-MM-01) og hittil i år (`dateFrom` = ÅÅÅÅ-01-01), og det samme for i fjor: driftsinntekter (3000–3999), driftsresultat
  (3000–7999), resultat før skatt (3000–8299, uten 83xx). Inntekter har negativt fortegn.
- `/balanceSheet dateFrom=ÅÅÅÅ-01-01 dateTo=D accountNumberFrom=1000 accountNumberTo=2999 "fields=account(number,name),balanceOut"`: bank (19xx),
  1500, 2400, skyldig mva (2740), trekk og arbeidsgiveravgift (2600/2770), egenkapital med udisponert resultat (Σ 3000–8999 hittil i år).
- Nøkkeltall: omsetning for måneden og hittil mot i fjor, driftsresultat, likviditet, forfalte kundefordringer og forfalt leverandørgjeld
  (`/ledger/posting/openPost date=D` på 1500 og 2400 med `"fields=amount,termOfPayment"`, forfalt = `termOfPayment` før D).

### 4. Utkast til månedsrapport (etter ja)
- Vis utkastet: tittel, kommentar på høyst fem setninger i kundens språk, nøkkeltall og anbefalinger. Ingen personopplysninger.
- Etter ja: Tally `save_monthly_report_draft`. Claude publiserer aldri; regnskapsføreren publiserer i Tally.
- Vil kunden ha fil: PDF `Perioderapport ÅÅÅÅ-MM <Klient>.pdf` via `silfer-rapport` (hovedtall, nøkkeltall, kommentar, avvik).

### 5. Månedsavslutning i Tally
- Tally `close_month` (klient, periode) uten `confirmation_id` gir bare en forhåndsvisning. Vis den, og si at avslutningen er synlig for kunden og ikke kan angres.
- Regnskapsføreren lukker måneden i Tally. Claude kaller ikke `close_month` igjen med `confirmation_id`.
- Avviser Tally avslutningen (avsetningsbilag ville gått til Tripletex), si det og hvorfor.

### 6. Periodelås i Tripletex
**Bare i Tripletex-UI:**
1. Lås regnskapsperioden når alle bankmåneder er lukket og, i terminmåneder, mva-meldingen er levert. Låsing har ikke API.
Kontroller etterpå med `npm run -s api -- GET /ledger/accountingPeriod startFrom=ÅÅÅÅ-MM-01 startTo=D "fields=number,start,end,isClosed" --client "<klient>"`
at `isClosed` er satt, før «Lukking av regnskapsperiode» fullføres.

## Svar

- Porttabell: Punkt · Status (OK, AVVIK, IKKE AVKLART) · Kilde · Gjenstår, én linje per F1–F6 og D4, med port (grønn/gul/rød).
- Hovedtall på tre–fire linjer. Funn fra A1–A3 i funn-formatet (ID · Klient · Periode · Konto · Beløp · Status · Forslag · Krever), maks 10 linjer.
- Nummerert ja-liste: lagre utkastet, månedsavslutning i Tally (regnskapsfører), periodelås i Tripletex-UI (regnskapsfører).
- «Alle»: én linje per klient (Klient · Røde punkter · Neste skill).

## Lever

Lever: `silfer-rapport` (spec.json → pdf, bare når kunden vil ha fil) + `docs/dokumentlagring.md` (kategori `ANNET`, periode `ÅÅÅÅ-MM`, samling `Perioderapporter ÅÅÅÅ`, oppgave «Ferdigstillelse perioderegnskap»).
Fullfør i Tally: se `tally-gjoremal`. «Ferdigstillelse perioderegnskap» fullføres når F1–F6 er OK eller forklart og utkastet til månedsrapport er lagret; «Lukking av regnskapsperiode» først når `/ledger/accountingPeriod` viser `isClosed` for perioden. Kommentaren inneholder periode, hovedtall, avvik fra A1–A3 og hva som er lukket.

## Fallgruver

- `hent_kontoavstemming`, `kontoutvikling` og `hent_posteringer` dekker bare resultatkontoer og bare Tripletex-klienter.
- `/ledger/accountingPeriod` er bare lesing. Tripletex-perioden låses i UI.
- Tally `close_month` (kundens månedsavslutning) og periodelåsen i Tripletex (hindrer nye føringer) er to forskjellige ting. Begge gjøres av regnskapsføreren.
- Et lagret utkast er ikke publisert. Publisering er et eget steg i Tally.
- Det finnes ingen rapport-API: hovedtallene bygges fra `/balanceSheet`, og kontogruppene følger klientens kontoplan (sjekk 8xxx).
- Lukk aldri en periode med åpne bankmåneder eller ubehandlet bilagsmottak.

## Referanser

- `references/kontroller.md`: F1–F6, D4, A1–A3, P1–P4. Katalog: `docs/kontrollkatalog.md`.
- Naboskills: `bilagsforing`, `bilagskontroll`, `bankavstemming`, `reskontroavstemming`, `balanseavstemming`, `a-melding`, `mva-innlevering`.
