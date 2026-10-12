# Kontrollkatalog – løpende regnskapskontroll

Referanse, ikke en skill. Katalogen kommer fra den første månedskontrollen (Python, september 2026, tag `v1-python` i git).
Verktøyet er fjernet fordi det krevde lokale kundemapper og egne tokens. Kontrollene lever videre i skillene, og hver linje
under sier hvor den hører hjemme nå og hvilket MCP-verktøy som gir dataene.

Kjør bare kontrollene som gjelder klienten. Kundeinstruksen i Tally sier om klienten har mva, lønn, prosjekt, varelager eller utleie
(se skillen `kundeinstruks`). Mangler svaret, er kontrollen «ikke avklart», ikke «ok».

## Bank og likvider

| ID | Kontroll | Utslag | Skill | Data (MCP) |
|---|---|---|---|---|
| B1 | Åpne bankposter per konto og måned | Poster eldre enn 30 dager | `bankavstemming`, `mangelliste` | `get_unmatched_bank_transactions` |
| B2 | Bokført saldo 19xx mot kontoutskrift | Differanse ≠ 0 | `bankavstemming` | `get_bank_reconciliation_periods` (bankBalance/ledgerBalance) |
| B3 | Bankkonti uten avstemming | Konto med bevegelse og `not_started` | `bankavstemming` | `get_bank_reconciliation_periods` |
| B4 | Negativ bank eller kasse | Saldo < 0 uten kredittramme | `bankavstemming` (internt) | `get_balance_sheet` |
| B5 | Gamle åpne poster | Åpne > 90 dager | `bankavstemming` | `get_unmatched_bank_transactions` |

## Reskontro

| ID | Kontroll | Utslag | Skill | Data (MCP) |
|---|---|---|---|---|
| R1 | Kundereskontro mot 1500 | Differanse ≠ 0 | `mva-termin` del B | `search_open_postings`, `get_balance_sheet` |
| R2 | Leverandørreskontro mot 2400 | Differanse ≠ 0 | `mva-termin` del B | `search_open_postings`, `get_balance_sheet` |
| R3 | Feil fortegn | Kunder i kredit, leverandører i debet | `mva-termin` del B | `search_open_postings` |
| R4 | Aldersfordeling kunder | Forfalt > 90 dager (tap, inkasso, konkurs i Brreg) | `mva-termin` del B | `search_open_postings`, `lookup_company_in_brreg` |
| R5 | Forfalte leverandørfakturaer | Forfall passert uten betaling | `mva-termin` del B | `search_open_postings`, `search_supplier_invoices` |
| R6 | Dublettfakturaer | Samme leverandør, beløp og dato/fakturanr. | `bilagsforing` | `search_ledger_postings` |

Reskontroavstemming er en reell vurdering av hver åpen post, ikke bare sum mot hovedbok. Per termin vurderes bare poster datert
i inneværende år; eldre poster blir én samlelinje «vurderes i årsoppgjøret».

## Merverdiavgift

| ID | Kontroll | Utslag | Skill | Data (MCP) |
|---|---|---|---|---|
| M1 | Mva-konti mot mva-melding | Differanse ≠ 0 | `mva-termin` del B | `search_ledger_postings`, `fetch_report` |
| M2 | Oppgjørskonto 2740 nullstilt etter betaling | Restsaldo | `mva-termin` del C | `get_balance_sheet` |
| M3 | Rimelighet sats | Utgående mva mot 25/15/12 % av grunnlaget, avvik > 1 % | `mva-termin` del B | `search_ledger_postings` |
| M4 | Mva-kode mot konto | Representasjon, bil, gebyr, utland med uventet kode | `mva-termin` del B, `bilagsforing` | `search_ledger_postings` |
| M5 | Fradrag uten bilag | Inngående mva på bilag uten vedlegg | `mva-termin` del B | `search_ledger_postings` |
| M6 | Levert og betalt | Terminen levert og betaling bokført | `mva-termin` del A | `tripletex_run_script`, Tally `list_altinn_innboks` |

## Lønn

| ID | Kontroll | Utslag | Skill | Data (MCP) |
|---|---|---|---|---|
| L1 | A07 mot regnskap | Full terminavstemming | `lonnsavstemming-a07` | `tripletex_run_script` + A07-XML |
| L2 | Skyldig trekk og AGA | 2600/2770 mot termin, forfall den 15. | `lonn` | `get_amelding_status` (notPaid) |
| L3 | Feriepengeavsetning | Avsetning mot 10,2/12 % av grunnlaget | `lonnsavstemming-a07` | `search_ledger_postings` |
| L4 | A-melding levert | Levert innen den 5. | `lonn` | `get_amelding_status` |
| L5 | Lønn mot bank | Utbetalt netto mot bankutbetalinger | `lonnsavstemming-a07` | `search_ledger_postings` |

## Bilag og bokføringskvalitet

| ID | Kontroll | Utslag | Skill | Data (MCP) |
|---|---|---|---|---|
| D1 | Bilag uten vedlegg | Antall og beløp | `bilagsforing` | `search_ledger_postings` |
| D2 | Observasjonskonti (1370, 7799 o.l.) | Saldo ≠ 0 | `mangelliste`, `bilagsforing` | `get_balance_sheet`, `search_ledger_postings` |
| D3 | Feil periode | Bilagsdato og periode spriker | `bilagsforing` | `search_ledger_postings` |
| D4 | Periodelåsing | Forrige måned ikke lukket etter avslutning | `tally-gjoremal` | `get_accounting_period_status` |
| D5 | Runde beløp og manuelle poster | Manuelle bilag med runde beløp over terskel | årsoppgjør | `search_ledger_postings` |
| D6 | Ubehandlet bilagsmottak | Dokumenter som ligger i mottaket | `bilagsforing`, `mangelliste` | `get_voucher_inbox_count` |

## Eier og nærstående

| ID | Kontroll | Utslag | Skill | Data (MCP) |
|---|---|---|---|---|
| E1 | Mellomregning aksjonær | Debetsaldo mot aksjonær (lån fra AS til personlig aksjonær beskattes som utbytte) | årsoppgjør | `get_balance_sheet` |
| E2 | Privatuttak i drift | Kostnader som ser private ut | `bilagsforing` | `search_ledger_postings` |

## Drift og rimelighet

| ID | Kontroll | Utslag | Data |
|---|---|---|---|
| A1 | Måned mot måned | Avvik > 30 % eller over terskel | Tally `hent_kontoavstemming` (byråets terskler, kundens kommentarer) |
| A2 | Mot samme måned i fjor | Samme | `fetch_report` |
| A3 | Manglende faste kostnader | Husleie, forsikring, abonnement som pleier å komme | Tally `hent_kontoavstemming` |
| A4 | Avskrivninger | Ikke bokført, eller anleggsmidler kostnadsført | `search_ledger_postings` |
| A5 | Sovende balansekonti | Ingen bevegelse på 12 måneder | `get_balance_sheet` |

## Bransje (bare der kundeinstruksen sier det)

| ID | Kontroll | Data |
|---|---|---|
| P1 | Ufakturerte timer | `search_hour_entries`, `search_project_order_lines` |
| P2 | Prosjektmargin | `fetch_report` |
| P3 | Varelager mot telling, ukurans | `get_balance_sheet` |
| P4 | Leieinntekter mot avtale | `search_invoices` |

## Terskler og støy

En kontroll som gir 400 treff i måneden blir ignorert.

- **Vesentlighetsgrense per klient**, typisk høyeste av 5 000 kr og 0,5 % av omsetningen. Den står i kundeinstruksen.
- **Kjente avvik kvitteres ut én gang** i kundeinstruksens seksjon «Kjente avvik» (nøkkel · beløp · forklaring · gyldig til).
  Et kjent avvik meldes som «kjent, uendret» så lenge beløpet er det samme, og som nytt når beløpet endrer seg.
- Målet er **under 10 linjer per klient per måned**.

## Det som aldri gjøres automatisk

- Ingen bokføring uten ja. Claude foreslår posteringer; føring skjer etter bekreftelse.
- Ingen innsending av mva-melding eller skattemelding. A-melding sendes bare etter eksplisitt ja for klient og måned.
- Ingen utsendelse av e-post. Claude lager utkast i Missive; den ansvarlige sender.
- Ingen godkjenning av betalinger eller lønn. Ingen periodelåsing.
- Faglig skjønn (tapsavsetning, ulovlig lån, grensetilfeller på fradragsrett) flagges med forslag og avgjøres av regnskapsfører.
