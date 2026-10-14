# Kontroller – periodeavslutning

Utkast – kalibreres mot første klient. ID-ene står også i `docs/kontrollkatalog.md`. V er vesentlighetsgrensen fra kundeinstruksen.
Hvert funn rapporteres i funn-formatet (`docs/skill-mal.md`) med status OK, AVVIK, FORKLART, KJENT eller IKKE AVKLART.

F-punktene er porten: de leser resultatet av månedens skills og avstemmer ikke selv. Et rødt F-punkt peker på skillen som løser det, og
statusen i tavla er da Blokkert (eller I fare når fristen er passert). Nivå er avhengighetsnivået i `references/lukkekalender.md`:
et punkt kan bare bli OK når nivåene under er det.
Stier er `npm run -s api -- GET <sti> …`; kommandoer er `npm run -s <kommando> -- …`. D er første dag etter perioden.

## Port

| ID | Nivå | Kontroll | Utslag | Data (API) | Grunnlag |
|---|---|---|---|---|---|
| F1 | 1 | Bilagsmottaket er tomt, og ingen leverandørfakturaer datert i perioden er ubokført (D6) | > 0 → `bilagsforing` | `status --maaned` (bilagsmottak, ikke bokførte bilag) | bokf.l. § 7 |
| F2 | 2 | Banken er lukket for måneden på alle kontoer, differanse 0, ingen umatchede poster (B1–B3, B6) | Ellers → `bankavstemming` | `status --maaned` (bank lukket per konto); differanse og umatchede i `bankavstemming` | bokf.l. § 11; GRFS: avstemming ved pliktig rapportering |
| F3 | 2 | Reskontro avstemt: 1500/2400 = Σ åpne poster (R1/R2), og reskontrooppgavene er fullført | Ellers → `reskontroavstemming` | `status --maaned` (1500/2400 mot UB), `/ledger/posting/openPost`, Tally `list_tasks` | bokf.l. § 11; GRFS |
| F4 | 1–3 | A-melding sendt og godkjent (L4); trekk og arbeidsgiveravgift betalt ved forfall (L2); i terminmåneder mva levert og betalt (M6) | Ellers → `a-melding` eller `mva-innlevering` | `status --maaned` (a-melding, mva), `amelding status --maned` (ubetalt), Tally `list_altinn_innboks` | a-opplysningsl. § 4; sktbetl. § 10-10; mval. § 15-8 |
| F5 | 3 | Observasjonskonti (konto for manglende bilag, typisk 1370 eller 7799) = 0 (D2) | ≠ 0 → forslag om ompostering, `bilagskontroll`, `periodisering` | `status --maaned` (observasjonskonti) | bokf.l. § 7 |
| F6 | 1–3 | Månedsoppgavene i Tally for perioden er fullført: Bilagsbehandling, Oversendelse mangelliste, Bankavstamming, Kontroll av bilag, Avstemming kundereskontro, Avstemming leverandørreskontro, Avstemming balansekontoer, A-melding; i terminmåneder også MVA-kontroll og MVA-innlevering | Åpen oppgave → liste med skill og status (Blokkert, I fare) | Tally `list_tasks` | GRFS: oppdragsdokumentasjon |
| F7 | 3 | Ingen avstemming har åpent stopp: ingen uforklart differanse (B6, R1/R2, S10) og ingen post i kategori 3 over V uten beslutning (B7, R14, S11) | Ellers → skillen; Krever `oppdragsansvarlig` | kommentarene på avstemmingsoppgavene (Tally `get_task`), ellers skillene | bokf.l. § 11; GRFS |
| D4 | 5 | Forrige periode er låst i Tripletex; denne er klar til låsing | Ikke låst → UI-instruks (steg 7) | `status --maaned` (perioder lukket), `/ledger/accountingPeriod` (`isClosed`) | bokf.l. § 7 |

## Rimelighet (nivå 4)

| ID | Kontroll | Utslag | Data (API) | Grunnlag |
|---|---|---|---|---|
| A1 | Måned mot normalnivå (snitt siste tre måneder) med byråets terskler i Tally | Flagget konto over V | Tally `hent_kontoavstemming`, `hent_posteringer` | GRFS: rimelighetskontroll før rapportering |
| A2 | Mot samme måned i fjor | Avvik over 30 % og over V | Tally `kontoutvikling` | GRFS: rimelighetskontroll før rapportering |
| A3 | Faste kostnader som mangler (husleie, forsikring, abonnement) | Konto med poster i minst 9 av 12 måneder, 0 nå | Tally `kontoutvikling`, `hent_kontoavstemming` | rskl. § 4-1 (sammenstilling) |

Forklaring av et flagget avvik (drill-down til bilag og motpart) gjøres i `avviksanalyse`.

## Bransje (bare når kundeinstruksen sier det)

| ID | Kontroll | Utslag | Data (API) | Grunnlag |
|---|---|---|---|---|
| P1 | Ufakturerte timer (prosjekt) | Opptjent, ikke fakturert over V → periodisering | `/project/batchPeriod/invoicingReserveByProjectIds` (`ids`, `dateFrom`, `dateTo`), `/project/orderline` | rskl. § 4-1 |
| P2 | Prosjektmargin | Negativ margin eller stort fall mot forrige måned | `/balanceSheet` 3000–7999 med `projectId` | – |
| P3 | Varelager mot telling, ukurans | Lagerendring uten telling eller bilag | `/balanceSheet` 1400–1499 | rskl. § 5-2 |
| P4 | Leieinntekter mot avtale | Måned uten faktura eller avvik fra avtalt leie | `/invoice` (`invoiceDateFrom`, `invoiceDateTo`, `customerId`) | rskl. § 4-1 |

## Terskler

- Avvik under V vises ikke. Kjent avvik i kundeinstruksen med samme beløp: KJENT. Kundens kommentar i Tally forklarer: FORKLART.
- Port: grønn = F1–F7 og D4 OK; gul = bare spørsmål eller avvik under V; rød = noe som stopper avslutningen (blant annet F7).
