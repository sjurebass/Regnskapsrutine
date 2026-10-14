---
name: "mva-innlevering"
description: "Mva-terminen på tvers av klientene: hvem har levert og betalt (Tripletex direkte, Fiken og PowerOffice via Altinn-innboksen i Tally), fristene, og etterarbeidet for én klient etter at meldingen er sendt (kvittering, KID og forfall, 2740 til null, periode klar til låsing). Lukker Tally-oppgaven «MVA-innlevering». Bruk ved «hvem mangler mva for t<n>», «mva-innlevering», «hvem har ikke levert mva», «sendt og synkronisert», «etterarbeid mva», «betalingsinfo mva», «KID for mva», «er mva betalt»."
---

# Mva-innlevering

Del A er oversikten over alle klientene for en termin: levert, betalt, til gode eller gjenstår. Del C er etterarbeidet for én klient etter at
regnskapsføreren har sendt. Kontrollen før innsending og 2740-notatet lages i `mva-kontroll`. Låsing av perioden hører til `periodeavslutning`.

## Når

- Tally-oppgaven «MVA-innlevering», den 1. i fristmåneden. Frister for tomånedlig termin: T1 10.4, T2 10.6, T3 31.8, T4 10.10, T5 10.12, T6 10.2.
  Helg eller helligdag → neste virkedag. Tally `frister_fra_staten` og `list_deadlines` viser fristene byrået har registrert.
- Del A: termin og år (uklart → spør), alle klienter eller navngitte. Del C: én klient, når brukeren sier «sendt og synkronisert».
- ID-porten-økten varer 10 minutter og gjelder alle klientene. Ha alt klart før regnskapsføreren logger inn.

## Kundeinstruks

«Regnskapssystem og byrå» (Tripletex, Fiken eller PowerOffice) · «Mva» (registrert fra dato, termin eller årstermin, kompensasjon, særregler).

## Steg

### 1. Del A – oversikt over alle klientene (bare lesing)
1. **Tripletex:** `npm run -s mva -- status --alle --aar ÅÅÅÅ --termin N --json` (navngitte klienter: `--client "<klient>"` per klient).
   Per klient: registrering, terminlengde, levert (`deliveryStatus`), betalt (`paymentStatus`), rest, forfall, KID, saldo 2740 og åpne mva-krav
   på skattekontoen. Hold VAT_REGISTERED, VAT_APPLICANT, VAT_NOT_REGISTERED og VAT_COMPENSATION adskilt. Feil (ingen mva-innstillinger,
   mangler tilgang) er egen gruppe «kunne ikke leses», aldri «ikke registrert».
2. **Status:** levert = kvittering mottatt hos Skatteetaten (`deliveryStatus`). Betalt = `paymentStatus` betalt og 2740 = 0 etter oppgjøret.
   Til gode: Skatteetatens utbetaling kommer på 2740 når den er mottatt; skattekontoen viser om den er utbetalt.
3. **Fiken og PowerOffice (og kontroll av Tripletex-avvik):** Tally `list_altinn_innboks` per klient (avsender Skatteetaten) → «Kvittering for
   mottatt mva-melding» for terminen. `les_altinn_melding` bare når det trengs (avvisning, betalingsinformasjon).
4. **Tally i takt:** `list_tasks` («MVA-innlevering», åpne) mot resultatet. Levert og betalt, men åpen → fullfør (Lever). Ikke registrert → oppgaven er
   ikke aktuell (etter ja, via `tally-gjoremal`). Levert uten oppgave → nevn det.

### 2. Del C – etter innsending (én klient)
1. **Status:** `npm run -s modul -- kontroll-utkast --client "<klient>" --aar ÅÅÅÅ --termin N` gir meldingens status (fra «sendt – venter på svar» til
   «kvittering mottatt»), utkastet mot hovedboken, KID og forfall. Skatteetatens tall kan komme timer etter kvitteringen og krever ny synk.
2. **Betalingsinformasjon:** KID, beløp og forfall fra punkt 1 (Fiken og PowerOffice: kvitteringen i Altinn, `les_altinn_melding`). Forfall i helg
   flyttes til neste virkedag. Betalingen opprettes av regnskapsføreren og legger seg til godkjenning hos kunden. Til gode: ingen betaling; forventet
   utbetaling noteres.
3. **2740-notatet** fra `mva-kontroll` lages på nytt som «levert»: `npm run -s modul -- notat-2740 --client "<klient>" --aar ÅÅÅÅ --termin N --ut <mappe>`
   (`--forklaring-MM "beløp|tekst"` for måneder uten automatisk forklaring). Silfer-PDF med kvittering, beløp, KID, forfall og saldo per månedsslutt.
4. **Etter betaling (M2):** 2740 = 0 (`mva status --client`). Restsaldo → finn årsaken (renter, delbetaling, tilgode som ikke er kommet) og si den.

**Skriving (etter ja):** kjør først uten `--bekreft` og vis hva som skjer.
1. `npm run -s modul -- fullfor --client "<klient>" --id <VAT-id> --bekreft` når hovedbok, rapportert og Skatteetatens tall stemmer på hver linje
   (`modul -- mva-oversikt --client "<klient>" --id <VAT-id>`; id fra `modul -- perioder --client "<klient>" --aar ÅÅÅÅ --type VAT_GENERAL_INDUSTRY`).
   Da blir 2740 automatisk avstemt i begge månedene.
2. `npm run -s modul -- last-opp --client "<klient>" --id <BALANCE-id> --ref <2740-linjen> --fil <notat.pdf> --bekreft`: det endelige 2740-notatet
   på 2740 (linjen fra `modul -- linjer --client "<klient>" --id <BALANCE-id> --konto 27`).

**Bare i Tripletex-UI:**
1. Opprett og send mva-meldingen (regnskapsføreren, før Del C).
2. Synk med Skatteetaten etter kvitteringen, og igjen hvis tallene ikke er kommet.
3. Opprett betalingen med KID, beløp og forfall, til kundens godkjenning. Godkjenningen gjør kunden.
4. Lås perioden etter at terminen er levert og bankmånedene er lukket. Det finnes ikke API-kall for låsing; sjekklista er `periodeavslutning`.

## Svar

- Del A: tabell Klient · System · Status (levert, ikke levert, til gode, ikke registrert, kunne ikke leses) · Betaling · Neste steg.
  Ikke levert og kunne ikke leses øverst; levert og betalt kan samles på én linje («N klienter levert og betalt»).
- Del C: én linje per punkt: kvittering · beløp og forfall · KID · 2740 · hva som gjenstår (med «ikke gjort» på UI-punktene og det som venter på ja).

## Lever

Lever: `silfer-rapport` (via `modul -- notat-2740`) + `docs/dokumentlagring.md` (kategori `MVA_RAPPORT`, periode `ÅÅÅÅ-T<n>`, samling `Mva ÅÅÅÅ`, oppgave «MVA-innlevering»): det endelige 2740-notatet (PDF). Kvitteringen ligger allerede i Altinn-fanen i Tally og lastes ikke opp på nytt.
Fullfør i Tally: se `tally-gjoremal`. «MVA-innlevering» fullføres når kvitteringen er mottatt og betalingen er opprettet eller tilgodebeløpet registrert. Kommentaren inneholder termin, beløp å betale eller til gode, forfall og hva som gjenstår (synk, fullføring i modulen, låsing).

## Fallgruver

- Registrert midt i året: terminnummeret i Tripletex teller fra registreringsdatoen. Sjekk at du ser på riktig periode.
- Tripletex kan si VAT_APPLICANT selv om Enhetsregisteret sier registrert (Tally `lookup_brreg`). Si det.
- Ikke registrert: sjekk kjøp av tjenester fra utlandet over 2 000 kr i kvartalet (omvendt avgiftsplikt, egen melding med frist 10.5, 31.8, 10.11 og 10.2)
  og § 3-26 (uttak ved oppføring av bygg for salg). § 3-26 vurderes årlig, ikke per termin.
- Skattekontoen kan allerede ha et krav for terminen (`mva status` viser åpne mva-krav). Si det før noen sender, så meldingen ikke leveres to ganger.
- Til gode: Tripletex kan vise «ikke betalt» og en åpen post selv når Skatteetaten har betalt ut. Oppgjøret leses fra 2740 og skattekontoen.
- `fullfor` virker bare uten avvik og åpne linjer; et avslag er «ikke gjort», ikke en feil å omgå.
- Årstermin (frist 10.3 året etter; primærnæring 10.4) hører ikke med i den tomånedlige oversikten.

## Referanser

Kontroller: M2 (2740 nullstilt), M6 (levert og betalt) i `docs/kontrollkatalog.md`. Avstemmingsmodulen: `tripletex-api/docs/avstemmingsmodul.md`.
Naboskills: `mva-kontroll` (før innsending, 2740-notatet), `periodeavslutning` (låsing), `kundeinstruks`, `tally-gjoremal`.
