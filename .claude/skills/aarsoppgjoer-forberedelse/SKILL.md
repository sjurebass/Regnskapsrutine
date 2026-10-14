---
name: "aarsoppgjoer-forberedelse"
description: "Forberedelse av årsoppgjøret for en Tripletex-klient før Maestro: sjekkliste per 31.12 (tolv bankmåneder, reskontro, seks terminer med mva, lønn og feriepenger, periodiseringer, anleggsmidler, lån, mellomregning, egenkapital og skatt), hva som mangler fra kunden, årsoppgjørsfasene i Tally og notat til kundeinstruksen. Lukker Tally-oppgaven «Forberedelse». Bruk ved «forbered årsoppgjøret», «årsoppgjørsforberedelse», «hva mangler før årsoppgjøret», «sjekkliste årsoppgjør <klient>», «klar for Maestro», «avsetninger ved årsslutt», «periodiseringer 31.12»."
---

# Årsoppgjør – forberedelse

Sjekkliste per klient per 31.12: er året komplett i de løpende kontrollene, hva mangler fra kunden, og hvilken skill løser resten. Skillen
avstemmer ikke selv; den leser status og peker videre. Kontroll av ferdig årsregnskap og skattemelding er `aarsoppgjoer-kontroll`.

## Når

- Tally «Forberedelse» (15.1). Leverer videre til «RF-1086» (29.1, `aksjonaerregister`) og «Balanseavstemming» (26.2, `balanseavstemming`).
- Brukeren oppgir klient og regnskapsår (standard: fjoråret), eller «alle» for porteføljen (høyst 12 klienter per kjøring).
- Steg 0 i tillegg: Missive (utkast til kunden).

## Kundeinstruks

«Årsoppgjør» (det som bevisst har ventet, og hva som ble gjort i fjor) · «Bank» (alle kontoer, også uten feed) · «Mva» · «Lønn» · «Kjente avvik» ·
bransje (varelager styrer P3). Årets avgjørelser tilbys lagret under «Årsoppgjør» via `kundeinstruks`.

## Steg

Utkast – kalibreres mot første klient. Følg stegene, men si fra om noe ikke stemmer med det verktøyene gir.

### 1. Status i Tally
- `get_arsoppgjor_status` (klient, år) → fasene (forberedelse, rf1086, balanseavstemming, skattemelding, arsregnskap …). Uten klient: hele porteføljen.
- `arsoppgjor_frister` (år, klient) → frister. `get_client` → revisor og hovedkontakt (rolle, ikke navn).

### 2. Året i Tripletex (ett skript per klient, ca. 15 kall)
- `get_year_end_status` (året og året før) · `get_accounting_period_status` (tolv perioder) · `get_bank_reconciliation_periods` (alle måneder, differanse 0).
- `search_open_postings` per 1.1 året etter for 1500/2400 (sum, og eldre poster enkeltvis) · `get_balance_sheet` 1000–8999 for hele året.
- `search_ledger_postings`: 2700–2799 (seks oppgjørsbilag og betalinger), 1700–1799/2900–2999, 1200–1299 og 6000–6099, 1400–1499, 2200–2299,
  mellomregning 13xx/15xx/29xx, 2000–2099, 2500/1570, 2940/2780/2785, observasjonskonti.
- `get_amelding_status` (desember) · `get_voucher_inbox_count` · `search_supplier_invoices` ikke bokført, fakturadato til og med 31.12.
- Tally `list_altinn_innboks` (seks mva-kvitteringer, skatteoppgjør, forskuddsskatt) og `list_documents` (årsoppgave, kontoutskrift, lagerliste, protokoll).

### 3. Sjekkliste
Status per punkt: Ferdig · Mangler · Venter kunde · Ikke aktuelt. Det som har ventet til årsoppgjøret (kundeinstruksen), tas med nå.

| ID | Punkt | Løses i |
|---|---|---|
| AO1 | Tolv bankmåneder lukket på alle kontoer, differanse 0 | `bankavstemming` |
| AO2 | Reskontro per 31.12: R1/R2 = 0, eldre poster vurdert enkeltvis, 1580 | `reskontroavstemming` |
| AO3 | Seks terminer levert og betalt, 27xx = 0, mva-grunnlag rimelig mot omsetningen | `mva-innlevering`, `mva-kontroll` |
| AO4 | Tolv a-meldinger, terminene avstemt, 2600/2770 = siste termin, 2940 | `a-melding`, `lonnsavstemming` |
| AO5 | Periodiseringer 17xx/29xx dokumentert per 31.12 | `balanseavstemming` |
| A4 | Anleggsmidler, årets avskrivninger, tilganger fra 30 000 kr aktivert | `balanseavstemming` |
| P3 | Varelager: telling per 31.12 (bare når kundeinstruksen sier varelager) | kunden |
| AO6 | Skattekonto: 2500/1570 mot forskudds- og restskatt | `balanseavstemming` |
| S7 | Lån 2200–2299 mot årsoppgave | kunden, `balanseavstemming` |
| E1 | Mellomregning aksjonær: debet → utbytte, eller lån med avtale og renter | `balanseavstemming`, `aksjonaerregister` |
| S5 / S6 | Egenkapital og skatt: IB = fjorårets UB, utbytte har protokoll | `balanseavstemming` |
| D4 / D6 | Tolv perioder låst, bilagsmottaket tomt, ingen ubokførte bilag | `periodeavslutning`, `bilagsforing` |
| AO7 | Dokumenter fra kunden mottatt (steg 4) | kunden |
| AO8 | Frister og faser i Tally satt (RF-1086, skattemelding, årsregnskap, revisor) | steg 5 |

Utslag, data og grunnlag per punkt: `references/kontroller.md`.

### 4. Dokumenter fra kunden (etter ja)
- Bare det som mangler i `list_documents`: kontoutskrifter og årsoppgaver per 31.12 for alle bank-, kort-, spare- og skattetrekkskontoer; låneoppgaver;
  lagerliste; kjørebok eller bilbruk; kasseoppgjør; styre- og generalforsamlingsprotokoller; avtaler (leie, aksjonærlån); pensjon (OTP);
  forsikring; aksjer og fond; tilskudd; ufakturerte leveranser; vurdering av utestående.
- Missive-utkast (`compose_draft`) som punktliste til kundens hovedkontakt, uten personopplysninger. Ett ja per klient; Claude sender ikke.

### 5. Faser i Tally (etter ja)
- `update_arsoppgjor`: fase `forberedelse` med status og kort notat (antall mangler, hva som venter kunden).
- Overlevering: fase `balanseavstemming` med frist 26.2 hvis den ikke er satt. Mangler andre frister, sett dem fra `arsoppgjor_frister`.

### 6. Fil
- Spec til `silfer-rapport`: «Sjekkliste» (ID · Punkt · Status · Saldo/beløp · Kilde · Løses i · Ansvar byrå/kunde · Frist), «Dokumenter fra kunden»
  (Dokument · Gjelder konto · Mottatt/mangler · Tally-dokument), «Frister» og «Saldobalanse 31.12» (Konto · UB · Dokumentert?), som `balanseavstemming` bruker.
- Filnavn `Årsoppgjør forberedelse ÅÅÅÅ <Klient>.xlsx`.

## Svar

- Én klient: bare punktene med Mangler og Venter kunde, i funn-formatet (status AVVIK, Krever `kunden` eller skillen), maks 10 linjer, og neste frist.
- Portefølje: Klient · Fase · Antall mangler · Venter kunde · Neste frist.
- Kontaktpersoner og aksjonærer omtales med rolle, aldri navn.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `ARSOPPGJOR`, periode `ÅÅÅÅ`, samling `Årsoppgjør ÅÅÅÅ`, oppgave «Forberedelse»; dokumenter fra kunden likt, kontoutskrifter per 31.12 som `BILAG`, `ÅÅÅÅ-12`, `Bankavstemming ÅÅÅÅ`, «Bankavstamming»).
Fullfør i Tally: se `tally-gjoremal`. «Forberedelse» fullføres når sjekklisten er levert, utkastet til kunden er laget og fasene er oppdatert. Kommentaren inneholder antall mangler, hva som venter kunden og neste frist.

## Fallgruver

- Anleggsregisteret og skattekontoen kan ikke leses i MCP-en. Bruk bilagene og brev i Altinn-innboksen, eller be kunden om tallene (A4, AO6).
- Ett skript tåler 200 kall og 2 minutter. Med ca. 15 kall per klient: høyst 12 klienter per kjøring.
- Mva-kvitteringen finnes bare i Altinn-innboksen i Tally; levert betyr kvittering, betalt betyr 2740 nullstilt.
- `search_open_postings` med dato 1.1 året etter (eksklusiv) gir stillingen per 31.12.
- Periodelåsen i Tripletex settes i UI (`periodeavslutning`), ikke her.
- Be aldri om dokumenter kunden allerede har levert: sjekk `list_documents` før lista lages.

## Referanser

- `references/kontroller.md`: AO1–AO8, A4, P3, S5–S7, E1, D4, D6. Katalog: `docs/kontrollkatalog.md`.
- Naboskills: `balanseavstemming` (26.2), `aksjonaerregister` (29.1), `aarsoppgjoer-kontroll` (skattemelding og årsregnskap), `kundeinstruks`.
