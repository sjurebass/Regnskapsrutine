# Kontrollkatalog – løpende regnskapskontroll

Referanse, ikke en skill. Hver kontroll har en ID som skillene bruker i funn-formatet (`docs/skill-mal.md`), en skill som eier den,
API-kallet eller kommandoen som gir dataene (`npm run -s …` eller endepunkt for `npm run -s api -- GET …`) og grunnlaget i én frase.

Kjør bare kontrollene som gjelder klienten. Kundeinstruksen i Tally sier om klienten har mva, lønn, prosjekt, varelager eller utleie
(skillen `kundeinstruks`). Mangler svaret, er kontrollen «ikke avklart», ikke «ok».

Avstemmingsposter klassifiseres etter `docs/avstemmingsmetodikk.md` (kategori 1–3, alder 0–30/31–60/61–90/over 90, eskalering mot V/2 og V).
Manuelle bilag kontrolleres etter `docs/foringskontroll.md` (J1–J12). Stikkprøver følger `docs/stikkprover.md` (U1–U14).

## Bank og likvider

| ID | Kontroll | Utslag | Skill | Data (API) | Grunnlag |
|---|---|---|---|---|---|
| B1 | Åpne bankposter per konto og måned | Poster eldre enn 30 dager | `bankavstemming` | `bankavstemming` | bokf.l. § 11 |
| B2 | Bokført saldo 19xx mot kontoutskrift | Differanse ≠ 0 | `bankavstemming`, `balanseavstemming` | `bankavstemming` | bokf.l. § 11 |
| B3 | Bankkonti uten avstemming | Konto med bevegelse og `not_started` | `bankavstemming` | `bankavstemming` | GRFS: avstemming ved pliktig rapportering |
| B4 | Negativ bank eller kasse | Saldo < 0 uten kredittramme | `bankavstemming`, `balanseavstemming` | `/balanceSheet` | bokf.l. § 11 |
| B5 | Gamle åpne poster | Åpne > 90 dager | `bankavstemming` | `bankavstemming` | bokf.l. § 7 |
| B6 | Oppstilling: bankens sluttsaldo ± i transitt = UB ± ikke bokført | Uforklart differanse ≠ 0,00 → stopp (ikke lukk, ikke RECONCILED) | `bankavstemming` | `bankavstemming` (`status.json`: `bankSaldo`, `ub`, `tx`, `bank[]`), `/bank/reconciliation/closedWithUnmatchedTransactions` | bokf.l. § 11 |
| B7 | Kategori (1 tidsforskjell, 2 krever føring, 3 må undersøkes) og alder for hver åpen bankpost | Kategori 3 over V → stopp; over V/2 → regnskapsfører; over V eller 90 dager → oppdragsansvarlig | `bankavstemming` | `bankavstemming` (`status.json`) | bokf.l. § 11; GRFS |
| B8 | Trend mot forrige måned | Sum over V, antall økt tre måneder på rad, eller samme post tre måneder på rad → prosessavvik | `bankavstemming`, `periodeavslutning` | `bankavstemming --fra` (alle måneder i året) | GRFS: oppfølging av avstemmingsposter |

## Reskontro

Reskontroavstemming er en reell vurdering av hver åpen post, ikke bare sum mot hovedbok. Per måned vurderes bare poster datert i
inneværende år; eldre poster blir én samlelinje «vurderes i årsoppgjøret». Kategoriene står i skillen `reskontroavstemming`.

| ID | Kontroll | Utslag | Skill | Data (API) | Grunnlag |
|---|---|---|---|---|---|
| R1 | Kundereskontro mot 1500 | Differanse ≥ 1 kr | `reskontroavstemming`, `balanseavstemming` | `/ledger/posting/openPost`, `/balanceSheet` | bokf.l. § 11; GRFS |
| R2 | Leverandørreskontro mot 2400 | Differanse ≥ 1 kr | `reskontroavstemming`, `balanseavstemming` | samme | bokf.l. § 11; GRFS |
| R3 | Feil fortegn per motpart | Kunde i kredit / leverandør i debet over V/10 | `reskontroavstemming` | `/ledger/posting/openPost` | bokf.l. § 7 |
| R4 | Aldersfordeling kunder | Forfalt > 90 dager over V → tapsvurdering, konkurs i Brreg | `reskontroavstemming` | `/ledger/posting/openPost`, `/reminder`, Tally `lookup_brreg` | mval. § 4-7; rskl. § 5-2 |
| R5 | Forfalte leverandørfakturaer | Forfall passert uten betaling, over V | `reskontroavstemming` | `/supplierInvoice` | bokf.l. § 7 |
| R6 | Dubletter | Samme leverandør (org.nr.) og fakturanr., eller samme beløp ±30 dager | `bilagskontroll`, `reskontroavstemming`, `bilagsforing` | `/supplierInvoice`, `/ledger/posting` | bokf.f. § 5-5-1 |
| R7 | Poster som går i null | Gruppe per motpart som kan utlignes | `reskontroavstemming` | `/ledger/posting/openPost` | GRFS: ajourhold |
| R8 | Småbeløp under 100 kr | Antall og sum → forslag om utligning | `reskontroavstemming` | `/ledger/posting/openPost` | bokf.l. § 7 |
| R9 | Poster uten motpart på reskontrokonto | ≥ 1 | `reskontroavstemming` | `/ledger/posting/openPost` | bokf.f. § 3-1 |
| R10 | Betalt eller utlignet etter periodeslutt | Info | `reskontroavstemming` | `/ledger/posting/openPost` (to datoer) | – |
| R11 | Poster datert før året | Én samlelinje | `reskontroavstemming`, `aarsoppgjoer-forberedelse` | `/ledger/posting/openPost` | GRFS: årlig gjennomgang |
| R12 | Avsetning 1580 mot tapsvurderte poster | 1580 lavere enn forventet | `reskontroavstemming` | `/balanceSheet` | rskl. § 5-2; sktl. § 6-2 |
| R13 | Kontoutskrift per motpart | IB + fakturert − innbetalt ≠ UB | `reskontroavstemming` | `/ledger/posting`, `/balanceSheet` | bokf.l. § 11 |
| R14 | Avstemmingskategori og alder (dager forfalt) for hver åpen post i året | Kategori 3 over V uten beslutning → stopp før RECONCILED; over V/2 → regnskapsfører; over V → oppdragsansvarlig | `reskontroavstemming` | `modul reskontro-vurdering --json` (`dagerForfalt`, `kategori`) | bokf.l. § 11; GRFS |
| R15 | Trend mot forrige måned: antall og sum per aldersgruppe, kategori 3 | Forfalt over 60 dager over V og økende, eller samme post i kategori 3 tre måneder på rad → prosessavvik | `reskontroavstemming`, `periodeavslutning` | `modul reskontro-vurdering` for forrige måned, forrige fil i Tally | GRFS: oppfølging av avstemmingsposter |

## Merverdiavgift

| ID | Kontroll | Utslag | Skill | Data (API) | Grunnlag |
|---|---|---|---|---|---|
| M1 | Mva-konti mot mva-melding | Differanse ≠ 0 | `mva-kontroll` | `/ledger/posting`, `modul kontroll-utkast` | mval. § 15-1 |
| M2 | Oppgjørskonto 2740 nullstilt etter betaling | Restsaldo | `mva-innlevering`, `balanseavstemming` | `/balanceSheet` | mval. § 15-9 |
| M3 | Rimelighet sats | Utgående mva mot 25/15/12 % av grunnlaget, avvik > 1 % | `mva-kontroll` | `/ledger/posting` | mval. kap. 5 |
| M4 | Mva-kode mot konto | Kode på konto uten mva; fradrag på representasjon, bil, gebyr | `bilagskontroll` | `/ledger/posting` | mval. §§ 8-1, 8-3, 8-4 |
| M5 | Fradrag uten bilag | Inngående mva på bilag uten dokument | `bilagskontroll` | `/supplierInvoice`, `/supplierInvoice/{id}` | mval. § 15-10 |
| M6 | Levert og betalt | Terminen levert og betaling bokført | `mva-innlevering` | Tally `list_altinn_innboks`, `/balanceSheet` | mval. § 15-8 |
| M7 | Utland | Utenlandsk leverandør uten kode 86/88; 86 hos uregistrert | `bilagskontroll` | `/ledger/posting`, `leverandorindeks` | mval. §§ 3-30, 11-3 |
| M8 | Sats og EHF | Mva ≠ grunnlag × sats; EHF til annen kjøper; fradrag fra uregistrert | `bilagskontroll` | `/ledger/posting`, bilagsdokument | mval. § 11-4; bokf.f. § 5-1-1 |

## Lønn

| ID | Kontroll | Utslag | Skill | Data (API) | Grunnlag |
|---|---|---|---|---|---|
| L1 | A07 mot regnskap | Full terminavstemming (summer, ikke per ansatt) | `lonnsavstemming` | Tally `hent_amelding_rapport` + `lonn hent` | a-opplysningsl. § 4 |
| L2 | Skyldig trekk og AGA | 2600/2770 mot termin, forfall den 15.; negativt = for mye innbetalt | `a-melding`, `balanseavstemming` | `amelding status` | sktbetl. § 10-10 |
| L3 | Feriepengeavsetning | 2940 mot grunnlag × sats | `lonnsavstemming`, `balanseavstemming` | `/ledger/posting` | ferieloven § 10 |
| L4 | A-melding levert | Levert innen den 5. | `a-melding` | `amelding status` | a-opplysningsl. § 4 |
| L5 | Lønn mot bank | Utbetalt netto mot bankutbetalinger | `lonnsavstemming` | `/ledger/posting` | bokf.l. § 11 |
| L6 | Avvist eller endret etter innsending | Ny melding trengs | `a-melding` | `amelding status` | a-opplysningsl. § 4 |
| L7 | Måned uten lønn | Arbeidsforhold, men ingen a-melding | `a-melding` | `amelding status` | a-opplysningsl. § 3 |
| L8 | Skattetrekkskonto | 1950 lavere enn skyldig trekk (ikke ved direkte trekk) | `a-melding`, `balanseavstemming` | `/balanceSheet` | sktbetl. § 5-12 |
| L9 | Tilbakemelding fra Skatteetaten | Feil i Altinn-tilbakemeldingen | `a-melding` | Tally `list_altinn_innboks` | a-opplysningsl. § 4 |
| L10 | Tally-oppgaven i takt | Sendt men åpen; lønn uten oppgave | `a-melding` | Tally `list_tasks` | GRFS: dokumentasjon |

## Bilag og bokføringskvalitet

| ID | Kontroll | Utslag | Skill | Data (API) | Grunnlag |
|---|---|---|---|---|---|
| D1 | Bilag uten vedlegg | Antall og beløp | `bilagskontroll` | `/supplierInvoice` | bokf.l. § 10 |
| D2 | Observasjonskonti (1370, 7799 o.l.) | Saldo ≠ 0 | `bilagskontroll`, `balanseavstemming`, `periodeavslutning` | `/balanceSheet` | bokf.l. § 7 |
| D3 | Feil periode | Fakturadato og bilagsdato i ulik termin | `bilagskontroll` | `/ledger/posting` | mval. § 15-9; bokf.l. § 7 |
| D4 | Periodelåsing | Forrige måned ikke lukket etter avslutning | `periodeavslutning` | `/ledger/accountingPeriod` | bokf.l. § 7 |
| D5 | Runde beløp og manuelle poster | Manuelle bilag med runde beløp over V | `bilagskontroll` | `/ledger/posting`, `/ledger/voucherType` | bokf.l. § 10 |
| D6 | Ubehandlet bilagsmottak | Dokumenter i mottaket, ikke bokførte bilag i perioden | `bilagsforing`, `bilagskontroll`, `periodeavslutning` | `/voucherInbox/inboxCount`, `/supplierInvoice` | bokf.l. § 7 |
| D7 | Ny eller ukjent leverandør | Første bruk, uten org.nr., utenlandsk uten vurdering, konkurs | `bilagskontroll` | `/supplier`, `leverandorindeks` | bokf.f. § 5-1-1 |

## Føringskontroll

Kjøres før hvert manuelt bilag. Den maskinelle delen kjøres av tørrkjøringen `bilag manuell`; detaljer, vanlige feil, godkjenning og
dokumentasjonskrav står i `docs/foringskontroll.md`.

| ID | Kontroll | Utslag | Skill | Data (API) | Grunnlag |
|---|---|---|---|---|---|
| J1 | Manuelt bilag går i null (NOK, minst to linjer) | Differanse → FEIL | `periodisering`, `bilagsforing`, `bankavstemming` | `bilag manuell` / `bilag før` (tørrkjøring) | bokf.l. § 4 |
| J2 | Dato i åpen periode: regnskapsperiode, bankavstemming (19xx), mva-termin, årsoppgjør | Lukket eller levert → FEIL; levert årsoppgjør → oppdragsansvarlig | `periodisering`, `bilagsforing`, `bankavstemming` | `/ledger/accountingPeriod`, `/bank/reconciliation`, `/vatReturns/status`, Tally `get_arsoppgjor_status` | bokf.l. § 7; mval. § 15-9 |
| J3 | Kontoene finnes og er aktive | Ukjent eller inaktiv → FEIL | `periodisering`, `bilagsforing`, `bankavstemming` | `/ledger/account` | klientens kontoplan (NS 4102) |
| J4 | Mva-kode lovlig på kontoen; 0 på periodisering; ingen fradrag etter § 8-3 | Ulovlig → FEIL; periodisering eller § 8-3 → ADVARSEL | `periodisering`, `bilagsforing`, `bankavstemming` | `/ledger/account`, `/ledger/vatType`, `/ledger/vatSettings` | mval. §§ 8-1, 8-3, 15-10 |
| J5 | Avdeling og prosjekt finnes, er aktive og er satt der kontoen krever det | → FEIL | `periodisering`, `bilagsforing` | `/department`, `/project`, `/ledger/account` | klientens dimensjoner |
| J6 | Reskontropart på 1500/2400, én leverandør per bilag; periodisering ikke mot reskontro | Mangler → FEIL; periodisering mot reskontro → ADVARSEL | `periodisering`, `bilagsforing` | `/ledger/account` (`ledgerType`), `/supplier`, `/customer` | bokf.f. § 3-1 |
| J7 | Dublett: ref, samme dato + konto + beløp, Tripletex fører selv, faktura alt bokført | Treff i hovedboken → ADVARSEL; Tripletex fører selv eller faktura bokført → FEIL | `periodisering`, `bilagsforing`, `bankavstemming` | `<plan>.resultat.json`, `/ledger/posting`, `/supplierInvoice` | bokf.l. § 4 |
| J8 | Tilbakeføring etter dato og i åpen periode; satt på påløpte poster, ikke på forskudd eller avskrivning | Dato → FEIL; type → ADVARSEL | `periodisering` | planen, `/ledger/accountingPeriod` | rskl. § 4-1 |
| J9 | Bilag over V | ADVARSEL; ja med beløpet nevnt | `periodisering`, `bilagsforing`, `bankavstemming` | `bilag manuell --vesentlighet` | GRFS; kundeinstruks (V) |
| J10 | Runde beløp og estimater uten beregning | Rundt beløp → INFO; estimat → ADVARSEL | `periodisering` | planen | bokf.l. § 10; rskl. § 4-1 |
| J11 | Kildedokument eller beregning som vedlegg | Uten vedlegg → ADVARSEL; ingen dokumentasjon → FEIL | `periodisering`, `bilagsforing`, `bankavstemming` | `vedlegg`, `dokument`, Tally `list_documents` | bokf.l. § 10; bokf.f. kap. 5 |
| J12 | Beskrivelsen er revisjonsvennlig og uten personopplysninger | Mangler → FEIL; kort eller ufullstendig → ADVARSEL | `periodisering`, `bilagsforing`, `bankavstemming` | planen | bokf.l. §§ 4, 10 |

## Eier og nærstående

| ID | Kontroll | Utslag | Skill | Data (API) | Grunnlag |
|---|---|---|---|---|---|
| E1 | Mellomregning aksjonær | Debetsaldo mot personlig aksjonær | `balanseavstemming`, `aarsoppgjoer-forberedelse`, `aksjonaerregister` | `/balanceSheet` | sktl. § 10-11 (4); asl. § 8-7 |
| E2 | Privatlignende kostnader | Signalord på kostnadskonti | `bilagskontroll` | `/ledger/posting` | sktl. § 5-1; mval. § 8-3 |

## Drift og rimelighet

| ID | Kontroll | Utslag | Skill | Data |
|---|---|---|---|---|
| A1 | Måned mot normalnivå | Tallys byråterskler og over V | `periodeavslutning` | Tally `hent_kontoavstemming` |
| A2 | Mot samme måned i fjor | Avvik > 30 % og over V | `periodeavslutning` | Tally `kontoutvikling` |
| A3 | Manglende faste kostnader | Konto med poster i minst 9 av 12 måneder, 0 nå | `periodeavslutning` | Tally `kontoutvikling` |
| A4 | Avskrivninger og aktivering | Ikke bokført, eller anleggsmidler kostnadsført | `balanseavstemming`, `aarsoppgjoer-forberedelse`, `periodisering` | `/ledger/posting` |
| A5 | Sovende balansekonti | Saldo ≠ 0 og ingen bevegelse på 12 måneder | `balanseavstemming` | `/balanceSheet` |

## Balanse

| ID | Kontroll | Utslag | Skill | Grunnlag |
|---|---|---|---|---|
| S1 | Dokumentert saldo for alle konti over V | Mangler kilde | `balanseavstemming` | GRFS: dokumentert avstemming; bokf.l. § 11 |
| S2 | Skattetrekkskonto 1950 mot 2600 – samme kontroll som L8 | 1950 lavere | `balanseavstemming` (leser L8) | sktbetl. § 5-12 |
| S3 | Periodiseringer 17xx og 29xx | Post uten grunnlag eller eldre enn 12 måneder | `balanseavstemming`, `periodisering` | rskl. § 4-1 |
| S5 | Egenkapital 2000–2099 | Bevegelse uten protokoll; IB ≠ fjorårets UB | `balanseavstemming` | asl. §§ 3-1, 8-1 |
| S6 | Skatt 2500/1570 | IB ≠ fjorårets betalbar skatt; rest etter betaling | `balanseavstemming` | sktbetl. |
| S7 | Lån 2200–2299 | Saldo ≠ årsoppgave | `balanseavstemming` | bokf.l. § 11 |
| S8 | Varelager | Saldo ≠ telling (bare når kundeinstruksen sier varelager) | `balanseavstemming` | rskl. § 5-2 |
| S9 | Balansen går opp | Eiendeler ≠ EK og gjeld | `balanseavstemming` | bokf.l. § 11 |
| S10 | Oppstilling per konto: UB ± avstemmingsposter = dokumentert saldo | Uforklart differanse ≥ 1 kr → stopp før RECONCILED | `balanseavstemming` | bokf.l. § 11 |
| S11 | Kategori og alder for hver avstemmingspost på balansekonti | Kategori 3 over V → stopp; over V/2 → regnskapsfører; over 90 dager → oppdragsansvarlig | `balanseavstemming` | GRFS: avstemming av balanseposter |
| S12 | Trend mot forrige periode | Sum avstemmingsposter over V og økende, eller samme post tre perioder på rad → prosessavvik | `balanseavstemming`, `periodeavslutning` | GRFS: oppfølging av avstemmingsposter |
| S13 | Mellomværende i konsern mot motpartens saldo (motsatt fortegn) | Differanse ≥ 1 kr → AVVIK; motpart ikke klient og ingen saldobekreftelse → IKKE AVKLART | `balanseavstemming` | bokf.l. § 11; GRFS |

## Periodeavslutning, årsoppgjør og kvalitet

Detaljene står i `references/kontroller.md` i hver skill.

| ID-serie | Skill | Innhold |
|---|---|---|
| F1–F7 | `periodeavslutning` | Bilagsmottak tomt, bank lukket, reskontro avstemt, mva og lønn levert, observasjonskonti 0, alle månedsoppgaver i Tally fullført, ingen åpne stopp i avstemmingene (uforklart differanse, kategori 3 over V); nivå i `references/lukkekalender.md` |
| AO1–AO8 | `aarsoppgjoer-forberedelse` | Tolv måneder i bank, reskontro 31.12, seks terminer, lønn for året, periodiseringer, skattekonto, dokumenter fra kunden, frister i Tally |
| AR1–AR8 | `aksjonaerregister` | Selskapsform, aksjekapital, kapitalendringer, utbytte, eierskifter, egne aksjer, roller, levering innen 31.1 |
| K1–K10 | `kvalitetskontroll` | Oppdragsavtale, kundetiltak (KYC), fullmakter, registerkontroll, rapportering i tide, avstemminger dokumentert, ajourhold, kundeinstruks, åpne avvik, oppdragsansvarlig |

## Regnskapsrapport og avvik

Oppstilling, fortegn, nøkkeltall og normalområder: `.claude/skills/regnskapsrapport/references/oppstilling.md`; metode for avvik og bro:
`.claude/skills/avviksanalyse/references/metode.md`.

| ID | Kontroll | Utslag | Skill | Data (API) | Grunnlag |
|---|---|---|---|---|---|
| N1 | Resultat mot balanse | Rest etter «Årets resultat (ikke disponert)» og «Udisponert resultat tidligere år» ≠ 0 → AVVIK og stopp; udisponert tidligere år ≠ 0 → FORKLART til og med juni, ellers MERKNAD | `regnskapsrapport` | `regnskap` (`kontroll.balanse`) | rskl. § 6-2; bokf.l. § 5 |
| N2 | Vesentlige avvik i resultatet | \|avvik\| ≥ V (AVVIK), eller \|avvik %\| ≥ 10/15/20 (budsjett/i fjor/forrige) og ≥ V/2 (MERKNAD); over V uten driver, utsikt og tiltak | `regnskapsrapport`, `avviksanalyse` | `regnskap` (`resultat.rader[].avvik`) | GRFS: rimelighetskontroll av perioderegnskapet |
| N3 | Broen går opp | start + Σ drivere − slutt ≠ 0 → stopp | `avviksanalyse` | `regnskap`, `lag_spec.py --avvik` | GRFS: dokumentert analyse |
| N4 | «Diverse» i broen | \|diverse\| ≥ 20 % av avviket → stopp | `avviksanalyse` | `regnskap`, `lag_spec.py --avvik` | GRFS: dokumentert analyse |
| N5 | Nøkkeltall utenfor normalområdet | Margin eller lønnsandel endret ≥ 5 pp; driftsmargin < 0; likviditetsgrad 1 < 1 (< 0,5 AVVIK); EK-andel < 10 % (negativ EK AVVIK); driftsinntekter under V → IKKE AKTUELT | `regnskapsrapport` | `regnskap` (`nokkeltall`) | asl. §§ 3-4, 3-5 |
| N6 | Fullstendig oppstilling | Sum kontoer ≠ gruppe eller resultat ≠ −Σ 3000–8999 (AVVIK); saldo på 8500–8799 (MERKNAD) | `regnskapsrapport` | `regnskap` (`kontroll.resultat`) | rskl. § 6-1; NS 4102 |
| N7 | Sammenligningstall på samme grunnlag | Ulik periodelengde, kontoplanendring eller ompostering mellom grupper | `regnskapsrapport` | `regnskap` (`kolonner`) | rskl. § 6-6 |
| N8 | Uventet fortegn | Konto mot gruppens fortegn ≥ V/10 (unntatt 1580, 2010, 2080, 3080–3099, 5800–5899) | `regnskapsrapport`, `avviksanalyse` | `regnskap` | bokf.l. § 4 |
| N9 | Timing og feilføring fulgt opp | Avvik forklart som timing uten forslag i `periodisering`, eller feilføring uten korrigeringsbilag | `avviksanalyse` | `/ledger/posting` | rskl. § 4-1 |

## Stikkprøver og revisjonsstøtte

Metode, utvalgsstørrelse, arbeidspapir, bevisstandard og avviksgrad: `docs/stikkprover.md`.

| ID | Kontroll | Utslag | Skill | Data (API) | Grunnlag |
|---|---|---|---|---|---|
| U1 | Utvalget er dokumentert og kan gjentas: populasjon (antall, sum), metode, seed og antall etter tabellen | Mangler seed, skjønnsmessig utvalg eller færre enn tabellen | `bilagskontroll`, `kvalitetskontroll` | `utvalg` (`utvalg.json`) | GRFS: dokumentasjon av utført arbeid |
| U2 | Bilaget har vedlegg som er gyldig salgs- eller kjøpsdokument | Mangler eller ugyldig → avvik; formfeil → merknad | `bilagskontroll`, `kvalitetskontroll` | `utvalg`, `dokument --bilag` | bokf.l. § 10; bokf.f. kap. 5 |
| U3 | Konto, mva-kode og beløp stemmer med dokumentet (gjenberegning) | Avvik ≥ 1 kr; ≥ V → vesentlig | `bilagskontroll`, `kvalitetskontroll` | `dokument`, `/ledger/voucher/{id}` (postings) | bokf.l. § 4; mval. § 15-10 |
| U4 | Riktig periode: leverings- eller fakturadato og bilagsdato i samme periode, særlig siste og første dager | Annen periode → avvik; annen mva-termin og ≥ V → vesentlig | `bilagskontroll`, `kvalitetskontroll` | `utvalg --metode maalrettet`, `/ledger/posting` | bokf.l. § 7; rskl. § 4-1 |
| U5 | Godkjenning: leverandørfaktura godkjent med dato etter kundeinstruksen | Mangler → avvik; ingen godkjenningsflyt i instruksen → «–» | `bilagskontroll`, `kvalitetskontroll` | `/supplierInvoice/{id}` (`approvalListElements(status,actionDate)`) | GRFS: oppdragsavtale og rutiner |
| U6 | Oppgjør: bilaget er matchet mot bank eller står som åpen post i reskontro | Verken bank eller åpen post | `bilagskontroll`, `kvalitetskontroll` | `/ledger/posting`, `/ledger/posting/openPost` | bokf.l. § 11 |
| U7 | Månedlige og terminvise kontroller er utført i tide og dokumentert i utvalgte perioder, og saldo i dokumentet = hovedbok | Ikke utført, udokumentert eller saldo ≠ hovedbok; nøkkelkontroll → vesentlig | `kvalitetskontroll` | Tally `list_tasks`, `list_documents`; `modul -- perioder`, `/balanceSheet` | GRFS: dokumentert avstemming; bokf.l. § 11 |
| U8 | Avvik er klassifisert og aggregert, og vesentlige avvik er meldt oppdragsansvarlig før noe attesteres eller lukkes | Ikke meldt, eller samlet feil ≥ V uten vesentlig avvik | `bilagskontroll`, `kvalitetskontroll` | arbeidspapiret, Tally `get_quality_workspace` | GRFS: kvalitetskontroll |
| U9 | Ny test etter tiltak: kontroll med tidligere avvik er testet på nytt (ny seed, ett trinn større) og bestått | Ikke testet etter frist, eller avvik igjen → vesentlig | `kvalitetskontroll` | Tally `list_avvik`, `list_tasks`, forrige arbeidspapir | GRFS: oppfølging av avvik |
| U10 | Nærstående: transaksjoner med nærstående er funnet, dokumentert (avtale, vedtak) og ført riktig | Uten dokumentasjon → avvik; lån til aksjonær uten vedtak → vesentlig | `kvalitetskontroll`, `bilagskontroll` | Tally `lookup_brreg`, `/ledger/posting` | asl. §§ 3-8, 8-7; sktl. § 13-1 |
| U11 | Revisors forespørsel er en PBC-liste: hvert punkt har område, periode, eier, frist og status | Punkt uten eier eller forfalt | `revisjonsstotte` | Missive, Tally `get_arsoppgjor_status` | GRFS: oppdragsdokumentasjon |
| U12 | Saldo i dokumentasjonen til revisor = hovedbok på samme dato, per konto | Differanse ≥ 1 kr → sendes ikke | `revisjonsstotte` | `/balanceSheet`, `modul -- linjer`, Tally `list_documents` | bokf.l. § 11 |
| U13 | Oversendelsen er dokumentert (hva, når, kanal) og inneholder ikke mer persondata enn revisor trenger | Mangler logg, eller persondata utenfor forespørselen | `revisjonsstotte` | Tally `update_arsoppgjor` (`oversendelse-revisor`), `list_documents` | GRFS: dokumentasjon; GDPR art. 5 (dataminimering) |
| U14 | Revisors merknader (nummerert brev, korrigeringer) har rotårsak, tiltak, eier og frist | Merknad uten tiltak eller eier | `revisjonsstotte`, `kvalitetskontroll` | Tally `list_tasks`, `list_documents` | GRFS: oppfølging av avvik |

## Bransje (bare der kundeinstruksen sier det)

| ID | Kontroll | Skill | Data |
|---|---|---|---|
| P1 | Ufakturerte timer | `periodeavslutning` | `/timesheet/entry`, `/project/orderline` |
| P2 | Prosjektmargin | `periodeavslutning` | `modul kontroll-utkast` |
| P3 | Varelager mot telling, ukurans | `balanseavstemming`, `aarsoppgjoer-forberedelse` | `/balanceSheet` |
| P4 | Leieinntekter mot avtale | `periodeavslutning` | `/invoice` |

## Terskler og støy

En kontroll som gir 400 treff i måneden blir ignorert.

- **Vesentlighetsgrense V per klient** står i kundeinstruksen; standard er høyeste av 5 000 kr og 0,5 % av omsetningen.
- **Kjente avvik kvitteres ut én gang** i kundeinstruksens seksjon «Kjente avvik» (nøkkel · beløp · forklaring · gyldig til).
  Et kjent avvik meldes som «KJENT» så lenge beløpet er det samme, og som nytt når beløpet endrer seg.
- Målet er **under 10 funn per klient per måned**.

Det som aldri gjøres automatisk, står i `CLAUDE.md` («Det Claude aldri gjør»).
