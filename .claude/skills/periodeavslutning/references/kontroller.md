# Kontroller – periodeavslutning

Utkast – kalibreres mot første klient. ID-ene står også i `docs/kontrollkatalog.md`. V er vesentlighetsgrensen fra kundeinstruksen.
Hvert funn rapporteres i funn-formatet (`docs/skill-mal.md`) med status OK, AVVIK, FORKLART, KJENT eller IKKE AVKLART.

F-punktene er porten: de leser resultatet av månedens skills og avstemmer ikke selv. Et rødt F-punkt peker på skillen som løser det.

## Port

| ID | Kontroll | Utslag | Data (MCP) | Grunnlag |
|---|---|---|---|---|
| F1 | Bilagsmottaket er tomt, og ingen leverandørfakturaer datert i perioden er ubokført (D6) | > 0 → `bilagsforing` | `get_voucher_inbox_count`, `search_supplier_invoices` | bokf.l. § 7 |
| F2 | Banken er lukket for måneden på alle kontoer, differanse 0, ingen umatchede poster (B1–B3) | Ellers → `bankavstemming` | `get_bank_reconciliation_periods` | bokf.l. § 11; GRFS: avstemming ved pliktig rapportering |
| F3 | Reskontro avstemt: 1500/2400 = Σ åpne poster (R1/R2), og reskontrooppgavene er fullført | Ellers → `reskontroavstemming` | `search_open_postings`, `get_balance_sheet`, Tally `list_tasks` | bokf.l. § 11; GRFS |
| F4 | A-melding sendt og godkjent (L4); trekk og arbeidsgiveravgift betalt ved forfall (L2); i terminmåneder mva levert og betalt (M6) | Ellers → `a-melding` eller `mva-innlevering` | `get_amelding_status`, Tally `list_altinn_innboks` | a-opplysningsl. § 4; sktbetl. § 10-10; mval. § 15-8 |
| F5 | Observasjonskonti (konto for manglende bilag, typisk 1370 eller 7799) = 0 (D2) | ≠ 0 → forslag om ompostering, `bilagskontroll` | `get_balance_sheet` | bokf.l. § 7 |
| F6 | Månedsoppgavene i Tally for perioden er fullført: Bilagsbehandling, Oversendelse mangelliste, Bankavstamming, Kontroll av bilag, Avstemming kundereskontro, Avstemming leverandørreskontro, Avstemming balansekontoer, A-melding; i terminmåneder også MVA-kontroll og MVA-innlevering | Åpen oppgave → liste med skill | Tally `list_tasks` | GRFS: oppdragsdokumentasjon |
| D4 | Forrige periode er låst i Tripletex; denne er klar til låsing | Ikke låst → UI-instruks (steg 6) | `get_accounting_period_status` | bokf.l. § 7 |

## Rimelighet

| ID | Kontroll | Utslag | Data (MCP) | Grunnlag |
|---|---|---|---|---|
| A1 | Måned mot normalnivå (snitt siste tre måneder) med byråets terskler i Tally | Flagget konto over V | Tally `hent_kontoavstemming`, `hent_posteringer` | GRFS: rimelighetskontroll før rapportering |
| A2 | Mot samme måned i fjor | Avvik over 30 % og over V | Tally `kontoutvikling` | GRFS: rimelighetskontroll før rapportering |
| A3 | Faste kostnader som mangler (husleie, forsikring, abonnement) | Konto med poster i minst 9 av 12 måneder, 0 nå | Tally `kontoutvikling`, `hent_kontoavstemming` | rskl. § 4-1 (sammenstilling) |

## Bransje (bare når kundeinstruksen sier det)

| ID | Kontroll | Utslag | Data (MCP) | Grunnlag |
|---|---|---|---|---|
| P1 | Ufakturerte timer (prosjekt) | Opptjent, ikke fakturert over V → periodisering | `search_hour_entries`, `search_project_order_lines`, `fetch_report` | rskl. § 4-1 |
| P2 | Prosjektmargin | Negativ margin eller stort fall mot forrige måned | `fetch_report` | – |
| P3 | Varelager mot telling, ukurans | Lagerendring uten telling eller bilag | `get_balance_sheet` | rskl. § 5-2 |
| P4 | Leieinntekter mot avtale | Måned uten faktura eller avvik fra avtalt leie | `search_invoices` | rskl. § 4-1 |

## Terskler

- Avvik under V vises ikke. Kjent avvik i kundeinstruksen med samme beløp: KJENT. Kundens kommentar i Tally forklarer: FORKLART.
- Port: grønn = F1–F6 og D4 OK; gul = bare spørsmål eller avvik under V; rød = noe som stopper avslutningen.
