---
name: "aksjonaerregister"
description: "Aksjonærregisteroppgaven (RF-1086) for AS-klienter i Tripletex: aksjonærer og aksjeklasser ved årsslutt fra fjorårets oppgave, endringer i året (kjøp, salg, emisjon, kapitalendring, egne aksjer), utbytte vedtatt og utbetalt mot regnskapet (2800/8920), aksjonærlån og Brreg-roller, og verdiene som skal leveres i Altinn. Leverer ikke selv. Lukker Tally-oppgaven «RF-1086». Bruk ved «aksjonærregister», «aksjonærregisteroppgaven», «RF-1086», «aksjeeierbok», «utbytte i aksjonærregisteret», «hvem eier <klient>», «aksjekapital endret»."
---

# Aksjonærregisteroppgaven (RF-1086)

Forbereder RF-1086: aksjonærer og hendelser i året avstemt mot hovedboken, fjorårets oppgave og Brreg, med sjekkliste og verdiene
regnskapsføreren legger inn. Tripletex har ikke aksjonærdata i API eller MCP. Levering i Altinn gjør regnskapsføreren, aldri Claude.

## Når

- Tally «RF-1086» (29.1; lovfrist 31.1). Først: `aarsoppgjoer-forberedelse` for samme år (mellomregning, egenkapital).
- Brukeren oppgir klient og regnskapsår (standard: fjoråret). Bare AS og ASA.

## Kundeinstruks

«Årsoppgjør» (eierskap beskrevet med roller, utbytte, aksjonærlån, hva som ble gjort i fjor) og «Kjente avvik».

## Steg

Utkast – kalibreres mot første klient. Følg stegene, men si fra om noe ikke stemmer med det verktøyene gir.

### 1. Selskap og frist
- Tally `lookup_brreg` (org.nr.) → organisasjonsform, styreleder, daglig leder, revisor. Ikke AS eller ASA: `mark_task_not_applicable` etter ja (AR1).
- Tripletex `lookup_company_in_brreg` → status (konkurs, avvikling, slettet).
- Tally `get_arsoppgjor_status` (fase `rf1086`) og `arsoppgjor_frister` (år).

### 2. Hovedboken (ett skript)
- `search_ledger_postings` for året: 2000–2099 (aksjekapital, overkurs, egne aksjer 2030, annen egenkapital 2050), 2800/8920 (avsatt utbytte),
  2920 (skyldig utbytte), 13xx/15xx/29xx mot aksjonær (lån) og renter på aksjonærlån.
- `get_balance_sheet` 2000–2099 IB og UB · `get_year_end_status` (år − 1) → fjorårets egenkapital.

### 3. Fjorårets oppgave og Altinn
- Tally `list_documents` (klient, kategori `ARSOPPGJOR`, søk «RF-1086» og «aksjonær») → fjorårets oppgave. Les den lokalt i scratch;
  den inneholder fødselsnummer og vises aldri.
- Tally `list_altinn_innboks` (Skatteetaten) → kvittering eller feilliste for i fjor og i år; `les_altinn_melding` ved feil.
- Finnes ikke fjorårets oppgave i Tally: spør regnskapsføreren hvor den ligger. Gjett aldri antall aksjer eller eiere.

### 4. Avstem
- AR2: 2000 UB = antall aksjer × pålydende (fjorårets oppgave ± kapitalendring). AR3: kapitalendring har protokoll og melding til Brreg.
- AR4: utbytte i hovedboken = vedtatt i protokollen = Σ per aksjonær; skyldig utbytte og utbetalingsdato.
- AR5: eierskifter mot aksjeeierboken og fjorårets oppgave. AR6: egne aksjer. AR7: roller i Brreg = de som signerer. E1: aksjonærlån per 31.12.
- AR8: levert innen 31.1 med kvittering, og fasen i Tally er oppdatert.
- Utslag, data og grunnlag: `references/kontroller.md`. Endring uten dokument er et spørsmål til kunden, ikke et AVVIK.
- Svar som gjelder klienten varig (eierstruktur med roller, utbyttepraksis), tilbys lagret i kundeinstruksen.

### 5. Verdiene til oppgaven og fil
- Selskapsnivå: aksjekapital, antall aksjer, pålydende, aksjeklasser, samlet utbytte, kapitalendringer.
- Per aksjonær, pseudonymisert «aksjonær n (rolle)»; selskapsaksjonærer med navn og org.nr.: aksjer IB, endring, aksjer UB, utbytte, lån per 31.12.
- Koblingen til fødselsnummer gjør regnskapsføreren fra fjorårets oppgave, ikke i chatten eller filen.
- Spec til `silfer-rapport`: «Sjekkliste» (AR1–AR8, E1), «Hendelser» (Dato · Type · Beløp · Bilag · Dokumentasjon · Med i oppgaven),
  «Aksjonærer» (pseudonymisert) og «Kilder». Filnavn `RF-1086 sjekkliste ÅÅÅÅ <Klient>.xlsx`.

### 6. Etter levering (etter ja)
- Regnskapsføreren leverer i Altinn eller årsoppgjørsmodulen. Kvitteringen leses med Tally `list_altinn_innboks` (AR8).
- Etter ja: Tally `update_arsoppgjor` fase `rf1086` = levert, og opplasting av sjekklisten (kvitteringen ligger allerede i Altinn-fanen i Tally).

## Svar

- Sjekkliste AR1–AR8 og E1 i funn-formatet (ID · Klient · Periode · Konto · Beløp · Status · Forslag · Krever), maks 10 linjer.
- Antall aksjonærer som tall, og hendelsene i året med dato, type og beløp.
- Aldri navn, fødselsnummer eller adresse på personlige aksjonærer; bruk «aksjonær n (rolle)». Selskaper med navn og org.nr. er greit.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `ARSOPPGJOR`, periode `ÅÅÅÅ`, samling `Årsoppgjør ÅÅÅÅ`, oppgave «RF-1086»).
Fullfør i Tally: se `tally-gjoremal`. «RF-1086» fullføres når Altinn-kvitteringen viser oppgaven mottatt, eller regnskapsføreren bekrefter levering. Kommentaren inneholder dato levert, antall aksjonærer og hendelsene i året.

## Fallgruver

- Aksjonærverktøy som dukker opp i ToolSearch (`listShareholders`, `shareholderRegisterSubmissionApi_*`), hører til ReAi, ikke Tripletex.
  De gjelder bare ReAi-klienter, og innsending (`…_submit`) gjøres aldri.
- RF-1086 for år X har utbyttet som er vedtatt i år X. Avsetningen på 8920/2800 per 31.12 i fjor er normalt det som ble vedtatt og utdelt i år.
- Tilleggsutbytte vedtatt i året føres mot annen egenkapital (2050), ikke over 8920. Det finnes i protokollen og i bevegelsene på 2000–2099.
- Fjorårets oppgave har fødselsnummer: les den lokalt, skriv det aldri ut, og slett scratch-filen når jobben er ferdig.
- Fristen er 31.1. Levert etter fristen kan gi tvangsmulkt; si det når fristen nærmer seg.

## Referanser

- `references/kontroller.md`: AR1–AR8, E1. Katalog: `docs/kontrollkatalog.md`.
- Naboskills: `aarsoppgjoer-forberedelse` (mellomregning, egenkapital), `balanseavstemming` (S5), `kundeinstruks` («Årsoppgjør»).
