---
name: "periodeavslutning"
description: "Ferdigstillelse av perioderegnskapet for en Tripletex-klient: statustavle etter avhengighetsnivå (bilag, lønn, bank, reskontro, balanse, mva), port før låsing, rimelighet mot fjoråret og byråets terskler, hovedtall og utkast til månedsrapport i Tally, avslutningsnøkkeltall og retrospektiv. Lukker Tally-oppgavene «Ferdigstillelse perioderegnskap» og «Lukking av regnskapsperiode». Bruk ved «periodeavslutning», «ferdigstill perioderegnskapet», «månedsavslutning for <klient>», «er <måned> klar til å lukkes», «lukk perioden», «månedsrapport», «perioderapport», «hva blokkerer månedsavslutningen»."
---

# Periodeavslutning

Sjekkpunktet etter månedens kontroller: hvor langt klienten har kommet etter avhengighetsnivåene i `references/lukkekalender.md`, hva som blokkerer,
om tallene er rimelige, og om perioden er klar til å lukkes. Skillen avstemmer ikke selv; den leser resultatet fra nivå 1–3 (`bilagsforing`,
`bankavstemming`, `reskontroavstemming`, `balanseavstemming`, `a-melding`, `mva-innlevering`) og peker på det som mangler. Resultat og balanse lages i
`regnskapsrapport`, forklaring av avvik i `avviksanalyse`. Publisering av månedsrapporten, lukking i Tally og periodelås gjør regnskapsføreren.

## Når

- Tally «Ferdigstillelse perioderegnskap» og «Lukking av regnskapsperiode» (uten frist): nivå 4–5, etter bilag, lønn og periodisering (nivå 1),
  bank, reskontro og mva-kontroll (nivå 2), balanse, korrigeringer og mva-innlevering (nivå 3).
- Brukeren oppgir klient og periode `ÅÅÅÅ-MM`. «Alle» gir statustavlen på tvers av klientene (steg 1), ikke rimelighet eller rapport.
  Statustavlen kan kjøres når som helst i måneden for å se hva som er blokkert eller i fare.

## Kundeinstruks

«Regnskapssystem og byrå» (V) · «Mva» (termin: er perioden terminslutt?) · «Lønn» · «Periodiseringer» · «Reskontro og balanse» · «Kjente avvik»
(dempes i A1–A3) · bransje (prosjekt, varelager, utleie) styrer P1–P4. Retrospektiven (steg 8) gir forslag til endringer i instruksen.

## Steg

Utkast – kalibreres mot første klient. Følg stegene, men si fra om noe ikke stemmer med det verktøyene gir.

D = første dag etter måneden (`dateTo` og `date` er eksklusive). Lesing: `npm run -s api -- GET <sti> <parametre> "fields=…" --client "<klient>"`.

### 1. Statustavle og port
- `npm run -s status -- --client "<klient>" --maaned ÅÅÅÅ-MM --json` → bilagsmottak, ikke bokførte bilag i perioden, bank lukket per konto,
  1500/2400 åpne poster mot UB, a-melding (gruppe), observasjonskonti, perioder lukket og mva for siste termin.
- `npm run -s amelding -- status --client "<klient>" --maned ÅÅÅÅ-MM --json` → ubetalt trekk og arbeidsgiveravgift med forfall den 15.
- I terminmåneder: mva levert og betalt fra `status`; kvitteringen ligger i Tally `list_altinn_innboks` (2740 som i `mva-innlevering`).
- Tally `list_tasks` (klient, `scope: all`) → månedsoppgavene for perioden med status og frist; `get_task` gir kommentarene på avstemmingsoppgavene (F7).
- Statustavle: Nivå · Arbeid · Skill · Frist · Status (Ikke startet, Pågår, Ferdig, Blokkert, I fare) · Blokkert av · Neste steg, etter `references/lukkekalender.md`.
- Port: F1–F7 og D4 med nivå i `references/kontroller.md`. Rødt punkt: Blokkert, pek på skillen som løser det, og stopp før steg 5.
- «Alle»: `npm run -s status -- --alle --maaned ÅÅÅÅ-MM --json` og Tally `list_tasks` (`title`, `scope: overdue`, `group_by: klient`) → én linje per klient.

### 2. Blokkeringer
For hver blokkering: hva, nivå, eier (kunden, regnskapsfører, oppdragsansvarlig, Tripletex-UI) og hva som løser den (`references/lukkekalender.md`).
Kunden: mangelliste eller Missive-utkast etter ja. Tally: én kort kommentar med årsaken på oppgaven etter ja (`tally-gjoremal`); oppgaven fullføres ikke.

### 3. Rimelighet (A1–A3, nivå 4)
- Tally `hent_kontoavstemming` (klient, periode, bare flaggede) → kontoer over byråets terskler, med kundens beslutninger og kommentarer (A1).
- Tally `kontoutvikling` (siste 12 måneder, sammenlignet med i fjor) → A2 (over 30 % og over V) og A3 (fast kostnad i minst 9 av 12 måneder, 0 nå).
- Kjente avvik dempes; avvik under V vises ikke. Forklaring av en flagget konto (bilag, motpart, pris og mengde): `avviksanalyse`.
  Tally `hent_posteringer` holder for en rask titt.
- P1–P4 bare når kundeinstruksen sier prosjekt, varelager eller utleie.

### 4. Hovedtall (nivå 4)
- Resultat og balanse med sammenligning fra `regnskapsrapport`:
  `npm run -s regnskap -- --client "<klient>" --periode ÅÅÅÅ-MM --hittil --sammenlign ifjor --json --ut <mappe>`.
- Uten den: `/balanceSheet dateFrom=<fra> dateTo=D accountNumberFrom=3000 accountNumberTo=8999 "fields=account(number,name),balanceChange"` for måneden og
  hittil i år, i år og i fjor (inntekter har negativt fortegn), og 1000–2999 med `balanceOut` for bank, 1500, 2400, 2740 og 2600/2770.
- Nøkkeltall: omsetning for måneden og hittil mot i fjor, driftsresultat, likviditet, forfalte kundefordringer og forfalt leverandørgjeld
  (`/ledger/posting/openPost date=D` på 1500 og 2400 med `"fields=amount,termOfPayment"`, forfalt = `termOfPayment` før D).

### 5. Utkast til månedsrapport (etter ja, nivå 5)
- Vis utkastet: tittel, kommentar på høyst fem setninger i kundens språk, nøkkeltall og anbefalinger. Ingen personopplysninger.
- Etter ja: Tally `save_monthly_report_draft`. Claude publiserer aldri; regnskapsføreren publiserer i Tally.
- Vil kunden ha fil: PDF `Perioderapport ÅÅÅÅ-MM <Klient>.pdf` via `silfer-rapport` (hovedtall, nøkkeltall, kommentar, avvik).

### 6. Månedsavslutning i Tally (nivå 5)
- Tally `close_month` (klient, periode) uten `confirmation_id` gir bare en forhåndsvisning. Vis den, og si at avslutningen er synlig for kunden og ikke kan angres.
- Regnskapsføreren lukker måneden i Tally. Claude kaller ikke `close_month` igjen med `confirmation_id`.
- Avviser Tally avslutningen (avsetningsbilag ville gått til Tripletex), si det og hvorfor.

### 7. Periodelås i Tripletex (nivå 5)
**Stopp:** porten er grønn eller gul (F1–F7 og D4), alle bankmåneder er lukket, mva-meldingen er levert i terminmåneder, og ingen avstemming har åpent stopp (uforklart differanse, kategori 3 over V) – ellers anbefales ikke låsing: vis porttabellen med blokkeringene og hvem som løser dem.
**Bare i Tripletex-UI:**
1. Lås regnskapsperioden. Låsing har ikke API.
Kontroller etterpå med `npm run -s api -- GET /ledger/accountingPeriod startFrom=ÅÅÅÅ-MM-01 startTo=D "fields=number,start,end,isClosed" --client "<klient>"`
at `isClosed` er satt, før «Lukking av regnskapsperiode» fullføres.

### 8. Nøkkeltall og retrospektiv (etter lukking)
- Avslutningsnøkkeltall: dager til lukket, føringer etter lukking, gjenåpnede perioder, uforklarte poster og forsinkede oppgaver, med kall og mål
  i `references/lukkekalender.md`. Sammenlign med kommentaren fra forrige måneds lukking.
- Retrospektiv: de fem spørsmålene i referansen, høyst fem linjer. Svar som gjelder klienten varig, blir forslag til kundeinstruksen (`kundeinstruks`, etter ja).

## Svar

- Statustavle per nivå med port (grønn/gul/rød), og porttabell: Punkt · Nivå · Status (OK, AVVIK, IKKE AVKLART) · Kilde · Gjenstår for F1–F7 og D4.
- Hovedtall på tre–fire linjer. Funn fra A1–A3 i funn-formatet (ID · Klient · Periode · Konto · Beløp · Status · Forslag · Krever), maks 10 linjer.
- Nummerert ja-liste: lagre utkastet, kommentarer på blokkerte oppgaver, månedsavslutning i Tally og periodelås i Tripletex-UI (regnskapsfører),
  endringer i kundeinstruksen fra retrospektiven.
- «Alle»: én linje per klient (Klient · Høyeste ferdige nivå · Blokkert/I fare · Neste skill), I fare først.

## Lever

Lever: `silfer-rapport` (spec.json → pdf, bare når kunden vil ha fil) + `docs/dokumentlagring.md` (kategori `ANNET`, periode `ÅÅÅÅ-MM`, samling `Perioderapporter ÅÅÅÅ`, oppgave «Ferdigstillelse perioderegnskap»).
Fullfør i Tally: se `tally-gjoremal`. «Ferdigstillelse perioderegnskap» fullføres når F1–F7 er OK eller forklart og utkastet til månedsrapport er lagret; «Lukking av regnskapsperiode» først når `/ledger/accountingPeriod` viser `isClosed` for perioden. Kommentaren inneholder periode, hovedtall, avvik fra A1–A3, hva som er lukket og avslutningsnøkkeltallene.

## Fallgruver

- `hent_kontoavstemming`, `kontoutvikling` og `hent_posteringer` dekker bare resultatkontoer og bare Tripletex-klienter.
- `/ledger/accountingPeriod` er bare lesing. Tripletex-perioden låses i UI.
- Tally `close_month` (kundens månedsavslutning) og periodelåsen i Tripletex (hindrer nye føringer) er to forskjellige ting. Begge gjøres av regnskapsføreren.
- Et lagret utkast er ikke publisert. Publisering er et eget steg i Tally.
- Balansefristen (16.) kommer før reskontrofristen (20.): en balanse som venter på reskontro, er Blokkert, ikke I fare.
- `list_tasks` har frist og status, men ikke når oppgaven ble fullført; det står i `handlinger` i `get_task`.
- Lukk aldri en periode med åpne bankmåneder eller ubehandlet bilagsmottak.

## Referanser

- `references/kontroller.md`: F1–F7, D4, A1–A3, P1–P4. `references/lukkekalender.md`: nivåer, kritisk vei, status, blokkeringer, nøkkeltall, retrospektiv.
- Katalog: `docs/kontrollkatalog.md`. Metode: `docs/avstemmingsmetodikk.md`.
- Naboskills: `bilagsforing`, `periodisering`, `bilagskontroll`, `bankavstemming`, `reskontroavstemming`, `balanseavstemming`, `a-melding`, `mva-innlevering`,
  `regnskapsrapport`, `avviksanalyse`, `kundeinstruks`, `tally-gjoremal`.
