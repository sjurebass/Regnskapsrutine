# Kontroller – årsoppgjør, forberedelse

Utkast – kalibreres mot første klient. ID-ene står også i `docs/kontrollkatalog.md`. V er vesentlighetsgrensen fra kundeinstruksen.
Sjekklisten har status Ferdig · Mangler · Venter kunde · Ikke aktuelt. Det som mangler, rapporteres i funn-formatet (`docs/skill-mal.md`)
med status AVVIK og «Krever» = `kunden` eller skillen som løser det.

Alle punkter gjelder stillingen per 31.12 i regnskapsåret. Skillen avstemmer ikke selv; den leser status og peker på skillen.
Stier er `npm run -s api -- GET <sti> …` (se steg 2 i SKILL.md); kommandoer er `npm run -s <kommando> -- …`.

| ID | Kontroll | Utslag | Data (API) | Grunnlag |
|---|---|---|---|---|
| AO1 | Tolv måneder lukket i banken på alle kontoer, differanse 0 (B1–B3) | Åpen måned → `bankavstemming` | `status --aar` (bank per konto og måned) | bokf.l. § 11 |
| AO2 | Reskontro ren per 31.12: R1/R2 = 0; poster eldre enn året vurdert enkeltvis (R11); avsetning 1580 mot tapsvurderte poster (R12) | Avvik → `reskontroavstemming` | `/ledger/posting/openPost`, `/balanceSheet` | bokf.l. § 11; rskl. § 5-2 |
| AO3 | Seks terminer levert og betalt (M6); 2700–2799 = 0 og 2740 = siste termin eller 0 (M2); årets mva-grunnlag rimelig mot omsetningen på 3xxx | Mangler → `mva-innlevering`, `mva-kontroll` | `status --aar` (mva per termin), `/ledger/posting` 27xx, Tally `list_altinn_innboks` | mval. § 15-8 |
| AO4 | Tolv a-meldinger (L4); terminene avstemt (L1); 2600/2770 = skyldig for siste termin (L2); 2940 = grunnlag × sats (L3); 2780/2785 | Mangler → `a-melding`, `lonnsavstemming` | `amelding oversikt --ar`, `/ledger/posting` 2600–2799 og 2940 | a-opplysningsl. § 4; ferieloven § 10 |
| AO5 | Periodiseringer 1700–1799 og 2900–2999 dokumentert per 31.12 (S3) | Post uten grunnlag → `balanseavstemming` | `/ledger/posting` | rskl. § 4-1 |
| A4 | Anleggsregister komplett og lik 12xx; årets avskrivninger bokført; tilganger fra 30 000 kr aktivert; avgang ført | Mangler → `balanseavstemming` | `/asset`, `/asset/balanceAccountsSum`, `/ledger/posting` 1200–1299 og 6000–6099 | rskl. § 5-3; sktl. § 14-40 |
| P3 | Varelager: telling per 31.12 (bare når kundeinstruksen sier varelager) | Mangler → be kunden | `/balanceSheet` 1400–1499, Tally `list_documents` | rskl. § 5-2 |
| AO6 | Skattekonto: 2500 = 0 etter forskuddsskatt (eller rest), 1570 til gode; krav og renter på skattekontoen | Avvik → `balanseavstemming` | `/balanceSheet`, `/claimsAndPayments`, Tally `list_altinn_innboks` | sktbetl. §§ 10-20, 10-21 |
| S7 | Lån 2200–2299 = låneoppgave per 31.12; renter bokført | Mangler oppgave → be kunden | `/balanceSheet`, Tally `list_documents` | bokf.l. § 11 |
| E1 | Mellomregning aksjonær: debetsaldo mot personlig aksjonær → utbytte, eller lån med avtale, renter og protokoll | Debet → `balanseavstemming`, `aksjonaerregister` | `/ledger/posting` | sktl. § 10-11 (4); asl. § 8-7 |
| S5 / S6 | Egenkapital 2000–2099 og skatt 2500: IB = fjorårets UB (`/balanceSheet` år − 1); utbytte har protokoll; aksjekapital = Brreg | Avvik → `balanseavstemming` | `/balanceSheet` (i år og år − 1), `/ledger/annualAccount` | asl. §§ 3-1, 8-1 |
| D4 / D6 | Tolv regnskapsperioder låst i Tripletex; bilagsmottaket tomt; ingen ubokførte bilag datert i året | Ellers → `periodeavslutning`, `bilagsforing` | `status --aar` (perioder, bilagsmottak, ikke bokførte bilag) | bokf.l. § 7 |
| AO7 | Dokumenter fra kunden mottatt (kontoutskrifter og årsoppgaver, låneoppgaver, lagerliste, kasseoppgjør, protokoller, avtaler, OTP, forsikring, aksjer og fond, tilskudd, ufakturert, utestående) | Mangler → Missive-utkast | Tally `list_documents` | bokf.l. § 10 |
| AO8 | Frister og faser i Tally satt: RF-1086 (31.1), balanseavstemming (26.2), skattemelding (31.5), årsregnskap (31.7), revisor | Mangler → `update_arsoppgjor` etter ja | Tally `arsoppgjor_frister`, `get_arsoppgjor_status` | rskl. § 8-2; sktfvl. § 8-2 |

## Terskler

- Saldoavvik under 1 kr er OK. Avvik over V er rødt; under V gult.
- Kjent avvik i kundeinstruksen med samme beløp: KJENT. Det som bevisst har ventet til årsoppgjøret, er nå «Mangler» med merknad, ikke KJENT.
- Ikke aktuelt krever grunn: ingen lønn, ikke mva-registrert, ikke varelager, ikke AS (for E1 og S5).
