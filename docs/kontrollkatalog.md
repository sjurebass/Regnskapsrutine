# Kontrollkatalog – løpende regnskapskontroll

Referanse, ikke en skill. Hver kontroll har en ID som skillene bruker i funn-formatet (`docs/skill-mal.md`), en skill som eier den,
MCP-verktøyet som gir dataene og grunnlaget i én frase. «CLI-id» er kontrollen den speiler i byråets egen API-kobling, slik at MCP og
API-kobling gir samme svar.

Kjør bare kontrollene som gjelder klienten. Kundeinstruksen i Tally sier om klienten har mva, lønn, prosjekt, varelager eller utleie
(skillen `kundeinstruks`). Mangler svaret, er kontrollen «ikke avklart», ikke «ok».

## Bank og likvider

| ID | Kontroll | Utslag | Skill | Data (MCP) | Grunnlag |
|---|---|---|---|---|---|
| B1 | Åpne bankposter per konto og måned | Poster eldre enn 30 dager | `bankavstemming` | `get_unmatched_bank_transactions` | bokf.l. § 11 |
| B2 | Bokført saldo 19xx mot kontoutskrift | Differanse ≠ 0 | `bankavstemming`, `balanseavstemming` | `get_bank_reconciliation_periods` | bokf.l. § 11 |
| B3 | Bankkonti uten avstemming | Konto med bevegelse og `not_started` | `bankavstemming` | `get_bank_reconciliation_periods` | GRFS: avstemming ved pliktig rapportering |
| B4 | Negativ bank eller kasse | Saldo < 0 uten kredittramme | `bankavstemming`, `balanseavstemming` | `get_balance_sheet` | bokf.l. § 11 |
| B5 | Gamle åpne poster | Åpne > 90 dager | `bankavstemming` | `get_unmatched_bank_transactions` | bokf.l. § 7 |

## Reskontro

Reskontroavstemming er en reell vurdering av hver åpen post, ikke bare sum mot hovedbok. Per måned vurderes bare poster datert i
inneværende år; eldre poster blir én samlelinje «vurderes i årsoppgjøret». Kategoriene står i skillen `reskontroavstemming`.

| ID | Kontroll | Utslag | Skill | Data (MCP) | Grunnlag | CLI-id |
|---|---|---|---|---|---|---|
| R1 | Kundereskontro mot 1500 | Differanse ≥ 1 kr | `reskontroavstemming`, `balanseavstemming` | `search_open_postings`, `get_balance_sheet` | bokf.l. § 11; GRFS | RK1 |
| R2 | Leverandørreskontro mot 2400 | Differanse ≥ 1 kr | `reskontroavstemming`, `balanseavstemming` | samme | bokf.l. § 11; GRFS | RK2 |
| R3 | Feil fortegn per motpart | Kunde i kredit / leverandør i debet over V/10 | `reskontroavstemming` | `search_open_postings` | bokf.l. § 7 | RK4/RK5 |
| R4 | Aldersfordeling kunder | Forfalt > 90 dager over V → tapsvurdering, konkurs i Brreg | `reskontroavstemming` | `search_open_postings`, `search_reminders`, `lookup_company_in_brreg` | mval. § 4-7; rskl. § 5-2 | RK7 |
| R5 | Forfalte leverandørfakturaer | Forfall passert uten betaling, over V | `reskontroavstemming` | `search_supplier_invoices` | bokf.l. § 7 | RK9 |
| R6 | Dubletter | Samme leverandør (org.nr.) og fakturanr., eller samme beløp ±30 dager | `bilagskontroll`, `reskontroavstemming`, `bilagsforing` | `search_supplier_invoices`, `search_ledger_postings` | bokf.f. § 5-5-1 | MD1 |
| R7 | Poster som går i null | Gruppe per motpart som kan utlignes | `reskontroavstemming` | `search_open_postings` | GRFS: ajourhold | – |
| R8 | Småbeløp under 100 kr | Antall og sum → forslag om utligning | `reskontroavstemming` | `search_open_postings` | bokf.l. § 7 | – |
| R9 | Poster uten motpart på reskontrokonto | ≥ 1 | `reskontroavstemming` | `search_open_postings` | bokf.f. § 3-1 | RK3 |
| R10 | Betalt eller utlignet etter periodeslutt | Info | `reskontroavstemming` | `search_open_postings` (to datoer) | – | – |
| R11 | Poster datert før året | Én samlelinje | `reskontroavstemming`, `aarsoppgjoer-forberedelse` | `search_open_postings` | GRFS: årlig gjennomgang | – |
| R12 | Avsetning 1580 mot tapsvurderte poster | 1580 lavere enn forventet | `reskontroavstemming` | `get_balance_sheet` | rskl. § 5-2; sktl. § 6-2 | – |
| R13 | Kontoutskrift per motpart | IB + fakturert − innbetalt ≠ UB | `reskontroavstemming` | `search_ledger_postings`, `get_balance_sheet` | bokf.l. § 11 | – |

## Merverdiavgift

| ID | Kontroll | Utslag | Skill | Data (MCP) | Grunnlag | CLI-id |
|---|---|---|---|---|---|---|
| M1 | Mva-konti mot mva-melding | Differanse ≠ 0 | `mva-kontroll` | `search_ledger_postings`, `fetch_report` | mval. § 15-1 | – |
| M2 | Oppgjørskonto 2740 nullstilt etter betaling | Restsaldo | `mva-innlevering`, `balanseavstemming` | `get_balance_sheet` | mval. § 15-9 | – |
| M3 | Rimelighet sats | Utgående mva mot 25/15/12 % av grunnlaget, avvik > 1 % | `mva-kontroll` | `search_ledger_postings` | mval. kap. 5 | – |
| M4 | Mva-kode mot konto | Kode på konto uten mva; fradrag på representasjon, bil, gebyr | `bilagskontroll` | `search_ledger_postings` | mval. §§ 8-1, 8-3, 8-4 | MK4/MF1/MF2 |
| M5 | Fradrag uten bilag | Inngående mva på bilag uten dokument | `bilagskontroll` | `search_supplier_invoices`, `get_supplier_invoice` | mval. § 15-10 | MF6 |
| M6 | Levert og betalt | Terminen levert og betaling bokført | `mva-innlevering` | Tally `list_altinn_innboks`, `get_balance_sheet` | mval. § 15-8 | – |
| M7 | Utland | Utenlandsk leverandør uten kode 86/88; 86 hos uregistrert | `bilagskontroll` | `search_ledger_postings`, `leverandorindeks` | mval. §§ 3-30, 11-3 | MO1/MO2, UR1/UR5/UR7 |
| M8 | Sats og EHF | Mva ≠ grunnlag × sats; EHF til annen kjøper; fradrag fra uregistrert | `bilagskontroll` | `search_ledger_postings`, bilagsdokument | mval. § 11-4; bokf.f. § 5-1-1 | MS1, EH1–EH6, MF5 |

## Lønn

| ID | Kontroll | Utslag | Skill | Data (MCP) | Grunnlag |
|---|---|---|---|---|---|
| L1 | A07 mot regnskap | Full terminavstemming | `lonnsavstemming` | `tripletex_run_script` + A07-XML | a-opplysningsl. § 4 |
| L2 | Skyldig trekk og AGA | 2600/2770 mot termin, forfall den 15.; negativt = for mye innbetalt | `a-melding`, `balanseavstemming` | `get_amelding_status` | sktbetl. § 10-10 |
| L3 | Feriepengeavsetning | 2940 mot grunnlag × sats | `lonnsavstemming`, `balanseavstemming` | `search_ledger_postings` | ferieloven § 10 |
| L4 | A-melding levert | Levert innen den 5. | `a-melding` | `get_amelding_status` | a-opplysningsl. § 4 |
| L5 | Lønn mot bank | Utbetalt netto mot bankutbetalinger | `lonnsavstemming` | `search_ledger_postings` | bokf.l. § 11 |
| L6 | Avvist eller endret etter innsending | Ny melding trengs | `a-melding` | `get_amelding_status` | a-opplysningsl. § 4 |
| L7 | Måned uten lønn | Arbeidsforhold, men ingen a-melding | `a-melding` | `get_amelding_status` | a-opplysningsl. § 3 |
| L8 | Skattetrekkskonto | 1950 lavere enn skyldig trekk (ikke ved direkte trekk) | `a-melding`, `balanseavstemming` | `get_balance_sheet` | sktbetl. § 5-12 |
| L9 | Tilbakemelding fra Skatteetaten | Feil i Altinn-tilbakemeldingen | `a-melding` | Tally `list_altinn_innboks` | a-opplysningsl. § 4 |
| L10 | Tally-oppgaven i takt | Sendt men åpen; lønn uten oppgave | `a-melding` | Tally `list_tasks` | GRFS: dokumentasjon |

## Bilag og bokføringskvalitet

| ID | Kontroll | Utslag | Skill | Data (MCP) | Grunnlag | CLI-id |
|---|---|---|---|---|---|---|
| D1 | Bilag uten vedlegg | Antall og beløp | `bilagskontroll` | `search_supplier_invoices` | bokf.l. § 10 | F1.6 |
| D2 | Observasjonskonti (1370, 7799 o.l.) | Saldo ≠ 0 | `bilagskontroll`, `balanseavstemming`, `periodeavslutning` | `get_balance_sheet` | bokf.l. § 7 | – |
| D3 | Feil periode | Fakturadato og bilagsdato i ulik termin | `bilagskontroll` | `search_ledger_postings` | mval. § 15-9; bokf.l. § 7 | MT2/MT3 |
| D4 | Periodelåsing | Forrige måned ikke lukket etter avslutning | `periodeavslutning` | `get_accounting_period_status` | bokf.l. § 7 | – |
| D5 | Runde beløp og manuelle poster | Manuelle bilag med runde beløp over V | `bilagskontroll` | `search_ledger_postings`, `search_voucher_types` | bokf.l. § 10 | – |
| D6 | Ubehandlet bilagsmottak | Dokumenter i mottaket, ikke bokførte bilag i perioden | `bilagsforing`, `bilagskontroll`, `periodeavslutning` | `get_voucher_inbox_count`, `search_supplier_invoices` | bokf.l. § 7 | F1.1/F1.3/F1.4 |
| D7 | Ny eller ukjent leverandør | Første bruk, uten org.nr., utenlandsk uten vurdering, konkurs | `bilagskontroll` | `list_suppliers`, `leverandorindeks` | bokf.f. § 5-1-1 | UR5/MF5 |

## Eier og nærstående

| ID | Kontroll | Utslag | Skill | Data (MCP) | Grunnlag |
|---|---|---|---|---|---|
| E1 | Mellomregning aksjonær | Debetsaldo mot personlig aksjonær | `balanseavstemming`, `aarsoppgjoer-forberedelse`, `aksjonaerregister` | `get_balance_sheet` | sktl. § 10-11 (4); asl. § 8-7 |
| E2 | Privatlignende kostnader | Signalord på kostnadskonti | `bilagskontroll` | `search_ledger_postings` | sktl. § 5-1; mval. § 8-3 |

## Drift og rimelighet

| ID | Kontroll | Utslag | Skill | Data |
|---|---|---|---|---|
| A1 | Måned mot normalnivå | Tallys byråterskler og over V | `periodeavslutning` | Tally `hent_kontoavstemming` |
| A2 | Mot samme måned i fjor | Avvik > 30 % og over V | `periodeavslutning` | Tally `kontoutvikling` |
| A3 | Manglende faste kostnader | Konto med poster i minst 9 av 12 måneder, 0 nå | `periodeavslutning` | Tally `kontoutvikling` |
| A4 | Avskrivninger og aktivering | Ikke bokført, eller anleggsmidler kostnadsført | `balanseavstemming`, `aarsoppgjoer-forberedelse` | `search_ledger_postings` |
| A5 | Sovende balansekonti | Saldo ≠ 0 og ingen bevegelse på 12 måneder | `balanseavstemming` | `get_balance_sheet` |

## Balanse

| ID | Kontroll | Utslag | Skill | Grunnlag |
|---|---|---|---|---|
| S1 | Dokumentert saldo for alle konti over V | Mangler kilde | `balanseavstemming` | GRFS: dokumentert avstemming; bokf.l. § 11 |
| S2 | Skattetrekkskonto 1950 mot 2600 – samme kontroll som L8 | 1950 lavere | `balanseavstemming` (leser L8) | sktbetl. § 5-12 |
| S3 | Periodiseringer 17xx og 29xx | Post uten grunnlag eller eldre enn 12 måneder | `balanseavstemming` | rskl. § 4-1 |
| S5 | Egenkapital 2000–2099 | Bevegelse uten protokoll; IB ≠ fjorårets UB | `balanseavstemming` | asl. §§ 3-1, 8-1 |
| S6 | Skatt 2500/1570 | IB ≠ fjorårets betalbar skatt; rest etter betaling | `balanseavstemming` | sktbetl. |
| S7 | Lån 2200–2299 | Saldo ≠ årsoppgave | `balanseavstemming` | bokf.l. § 11 |
| S8 | Varelager | Saldo ≠ telling (bare når kundeinstruksen sier varelager) | `balanseavstemming` | rskl. § 5-2 |
| S9 | Balansen går opp | Eiendeler ≠ EK og gjeld | `balanseavstemming` | bokf.l. § 11 |

## Periodeavslutning, årsoppgjør og kvalitet

Detaljene står i `references/kontroller.md` i hver skill.

| ID-serie | Skill | Innhold |
|---|---|---|
| F1–F6 | `periodeavslutning` | Bilagsmottak tomt, bank lukket, reskontro avstemt, mva og lønn levert, observasjonskonti 0, alle månedsoppgaver i Tally fullført |
| AO1–AO8 | `aarsoppgjoer-forberedelse` | Tolv måneder i bank, reskontro 31.12, seks terminer, lønn for året, periodiseringer, skattekonto, dokumenter fra kunden, frister i Tally |
| AR1–AR8 | `aksjonaerregister` | Selskapsform, aksjekapital, kapitalendringer, utbytte, eierskifter, egne aksjer, roller, levering innen 31.1 |
| K1–K10 | `kvalitetskontroll` | Oppdragsavtale, kundetiltak (KYC), fullmakter, registerkontroll, rapportering i tide, avstemminger dokumentert, ajourhold, kundeinstruks, åpne avvik, oppdragsansvarlig |

## Bransje (bare der kundeinstruksen sier det)

| ID | Kontroll | Skill | Data |
|---|---|---|---|
| P1 | Ufakturerte timer | `periodeavslutning` | `search_hour_entries`, `search_project_order_lines` |
| P2 | Prosjektmargin | `periodeavslutning` | `fetch_report` |
| P3 | Varelager mot telling, ukurans | `balanseavstemming`, `aarsoppgjoer-forberedelse` | `get_balance_sheet` |
| P4 | Leieinntekter mot avtale | `periodeavslutning` | `search_invoices` |

## Terskler og støy

En kontroll som gir 400 treff i måneden blir ignorert.

- **Vesentlighetsgrense V per klient** står i kundeinstruksen; standard er høyeste av 5 000 kr og 0,5 % av omsetningen.
- **Kjente avvik kvitteres ut én gang** i kundeinstruksens seksjon «Kjente avvik» (nøkkel · beløp · forklaring · gyldig til).
  Et kjent avvik meldes som «KJENT» så lenge beløpet er det samme, og som nytt når beløpet endrer seg.
- Målet er **under 10 funn per klient per måned**.

Det som aldri gjøres automatisk, står i `CLAUDE.md` («Det Claude aldri gjør»).
