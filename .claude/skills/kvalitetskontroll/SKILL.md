---
name: "kvalitetskontroll"
description: "Byråets kvalitetskontroll av et oppdrag i Tallys kvalitetsarbeidsflate: oppdragsavtale, kundetiltak og risikoklasse, fullmakter, Brreg, rapportering levert i tide, avstemminger dokumentert, ajourhold, kundeinstruks og åpne avvik, skrevet inn i gjennomgangen og sendt til oppdragsansvarlig. Ingen månedsoppgave: fullfører kvalitetsgjennomgangen i Tally (attestering gjør oppdragsansvarlig). Bruk ved «kvalitetskontroll av <klient>», «kvalitetsgjennomgang», «oppdragskontroll», «intern kontroll <klient>», «er oppdraget i orden», «KYC-status», «start kvalitetsgjennomgang»."
---

# Kvalitetskontroll

Intern kontroll av et oppdrag etter regnskapsførerloven og god regnskapsføringsskikk: Tallys registerkontroller pluss en oppsummering av
kontrollkatalogen (hvilke oppgaver er gjort, åpne avvik, avtale, kundetiltak, fullmakter), skrevet inn i kvalitetsgjennomgangen i Tally.
Tripletex leses bare. Kontroll av selve årsoppgjøret er `aarsoppgjoer-kontroll`.

## Når

- Kvalitetsgjennomgangen i Tally, årlig per klient (eller etter risikoklasse). Ingen fast månedsoppgave.
- Brukeren oppgir klient, eller «alle» for en oversikt fra `client_compliance` og `list_avvik`. Periode: siden forrige gjennomgang, ellers 12 måneder.

## Kundeinstruks

Hele instruksen: «Sist oppdatert», V og «Kjente avvik» (K8). Øvrige seksjoner sier hvilke tjenester og frister som gjelder (K5, K6).

## Steg

Utkast – kalibreres mot første klient. Følg stegene, men si fra om noe ikke stemmer med det verktøyene gir.

### 1. Oppdraget
- Tally `get_client` (oppdragsansvarlig, team, tjenester), `client_compliance` (kundetiltak, risikoklasse, neste kontroll), `contract_status`,
  `access_delegations` og `hent_instrukser`. `team_skills` ved behov (K10).
- `get_kyc` bare hvis statusfeltene i `client_compliance` ikke holder, og da bare statusfelt. Egenerklæring og persondata vises aldri.

### 2. Gjennomgangen i Tally
- `get_quality_workspace` (klient). Ingen åpen gjennomgang: `start_quality_review` (lager utkast og henter registerkilder).
- `run_quality_checks` → funn fra Brreg (roller, revisor, mva-registrering, status).

### 3. Bevis
- Tally `list_tasks` (klient, fullført og forfalt i perioden) per oppgavetype: Bilagsbehandling, Bankavstamming, Kontroll av bilag,
  Avstemming kundereskontro, Avstemming leverandørreskontro, Avstemming balansekontoer, A-melding, Avstemming av AGA og forskuddstrekk,
  MVA-kontroll, MVA-innlevering, Ferdigstillelse perioderegnskap.
- Tally `list_deadlines` (forfalt), `list_avvik`, `list_documents` (avstemminger per periode) og `frister_fra_staten`.
- Tripletex, én kommando om gangen (bare lesing):
  `npm run -s status -- --client "<klient>" --maaned <siste avsluttede måned> --aar ÅÅÅÅ --json`, ett kall per kalenderår i perioden →
  bank lukket per måned, perioder lukket, bilagsmottak, ikke bokførte bilag, mva levert og betalt per termin.
  `npm run -s amelding -- status --client "<klient>" --maned <siste måned> --json` (siste måned, ubetalt) og
  `npm run -s amelding -- oversikt --client "<klient>" --ar ÅÅÅÅ --json` (alle måneder i året).
  `npm run -s api -- GET /ledger/vatSettings "fields=vatRegistrationStatus" --client "<klient>"` → mva-registrering, holdes mot Brreg (K4).
- K1 oppdragsavtale · K2 kundetiltak · K3 fullmakter · K4 Brreg · K5 rapportering i tide · K6 avstemminger dokumentert · K7 ajourhold ·
  K8 kundeinstruks · K9 åpne avvik · K10 oppdragsansvarlig og team. Utslag, data og grunnlag: `references/kontroller.md`.

### 4. Utkast til gjennomgangen
- Per spørsmål i arbeidsflaten: svar og én faktasetning («Bank lukket 12 av 12 måneder», «Reskontro avstemt T1–T5»).
- Funn med eier og frist, konklusjon, og neste gjennomgang med grunn. Trengs svar fra kunden: utkast, aldri sendt.
- Ingen personopplysninger i svarene; bruk roller.

### 5. Lagre og sende (to ja)
- Vis utkastet. Etter ja: `save_quality_review` med hele innholdet og gjeldende revisjon og hasher fra `get_quality_workspace`.
- Etter nytt ja: `submit_quality_review` til oppdragsansvarlig.
- `attest_quality_review` kalles aldri; oppdragsansvarlig attesterer selv i Tally. `update_kyc` kalles aldri; foreslå endringen.

### 6. Oppfølging (etter ja)
- `create_task` for åpne funn med eier og frist, `be_om_avklaring` der noe må avklares internt, og endringer i kundeinstruksen via `kundeinstruks`.

## Svar

- Én linje per K1–K10 med status (OK, AVVIK, IKKE AVKLART) og kilde, og konklusjonen. Maks 12 linjer.
- Åpne funn i funn-formatet (ID · Klient · Periode · Konto/motpart · Beløp · Status · Forslag · Krever) med eier og frist.
- Aldri innhold fra kundetiltakene (identitet, reelle rettighetshavere, PEP), personnavn eller kontaktdata.

## Lever

Lever: `silfer-rapport` (spec.json → pdf, bare når byrået vil ha fil) + `docs/dokumentlagring.md` (kategori `ANNET`, periode `ÅÅÅÅ`, samling –, oppgave –; byråintern: internt arkiv, eller arkiveres straks med `archived: true`).
Fullfør i Tally: se `tally-gjoremal`. Gjennomgangen er ferdig fra Claudes side når den er sendt til oppdragsansvarlig; finnes en oppgave for kvalitetsgjennomgangen, fullføres den da. Kommentaren inneholder konklusjon, antall funn og neste gjennomgang.

## Fallgruver

- `save_quality_review` tar hele innholdet, ikke bare endringer, og krever gjeldende revisjon og hasher. Har noen endret gjennomgangen, les på nytt.
- `attest_quality_review` er irreversibel og bare for oppdragsansvarlig, også når brukeren selv er oppdragsansvarlig.
- `client_compliance` gir status; `get_kyc` gir persondata og brukes bare når status ikke holder.
- Tally-oppgaver som er fullført uten dokument, er ikke bevis for K6. Se etter filen i `list_documents` eller modulen.
- PDF-en «Oppdragskontroll ÅÅÅÅ <Klient>.pdf» er byråintern og skal aldri være synlig for kunden.

## Referanser

- `references/kontroller.md`: K1–K10. Katalog: `docs/kontrollkatalog.md` (kontrollene K5–K7 bygger på).
- Naboskills: `kundeinstruks` (K8), `tally-gjoremal` (oppgaver og frister), månedsskillene (bevis for K5–K7).
