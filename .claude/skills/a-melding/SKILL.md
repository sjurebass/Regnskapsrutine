---
name: "a-melding"
description: "A-meldingen i Tripletex: status per klient og måned (ikke sendt, venter, avvist, endret etter innsending), hvilke klienter og måneder som mangler a-melding, innsending etter eksplisitt ja for klient og måned, og skyldig forskuddstrekk og arbeidsgiveravgift med forfall den 15. Lukker Tally-oppgaven «A-melding». Bruk ved «er a-meldingen sendt», «send a-melding», «a-meldingsstatus», «hvem mangler a-melding», «hvilke måneder mangler a-melding», «skyldig forskuddstrekk», «skyldig arbeidsgiveravgift», «hva skal betales 15.»."
---

# A-melding

Status, innsending og skyldig trekk og arbeidsgiveravgift for a-meldingen, for én klient eller alle. Lønnskjøring og rettinger i arbeidsforhold
gjøres i `lonnskjoring`; avstemming mot A07 per termin er `lonnsavstemming`.

## Når

- Tally «A-melding»: frist den 5. for forrige måned. Trekk og AGA betales den 15. annenhver måned (jan, mar, mai, jul, sep, nov) for terminen før.
- Måneden må være sagt (`ÅÅÅÅ-MM`); tidlig i måneden er «denne måneden» tvetydig. Den 5.: spør én gang «forrige måned for alle?» og kjør alle.
- Lønnskjøringen for måneden skal være fullført av regnskapsføreren (`lonnskjoring`) før meldingen sendes.

## Kundeinstruks

«Lønn»: lønn ja/nei, modell (direkte trekk eller skattetrekkskonto 1950) og lønnsdato. «Regnskapssystem og byrå»: lønn i Fiken eller PowerOffice
gir bare Altinn-kvittering (steg 5). En måned uten lønn trenger likevel a-melding så lenge klienten har arbeidsforhold.

## Steg

### 1. Status for alle klienter (ett skript)
Ett `tripletex_run_script` over klientene fra `search_client_companies`: `tlx.get_amelding_status({companyName, month})` i try/catch per klient.
Behold bare status, kort `statusExplanation`, påløpt og ubetalt (`accrued`, `notPaid`) trekk, AGA og finansskatt, og `taxPeriodName`. Ingen ansattdata.
Grupper:
- **Ikke sendt** (`noAmeldingExists`, `ameldingExistsNotSent`, `nonReportedWageinfo`) – L4. Gjelder også måneder uten lønn (L7).
- **Avvist** (`ameldingRejected`) eller **endret etter innsending** – ny melding trengs (L6).
- **Sendt, venter på svar** fra Skatteetaten.
- **Godkjent / alt rapportert.**
- **Kunne ikke leses** (feil, manglende lønnsmodul eller lønnsrolle) – egen gruppe, aldri «ikke sendt».

### 2. Tally-oppgaven i takt (L10)
Tally `list_tasks` (oppgave «A-melding», åpne) mot gruppene:
- Sendt og godkjent i Tripletex, men åpen i Tally → fullfør (Lever).
- Klient uten lønn og uten arbeidsforhold → `mark_task_not_applicable` med `version` fra `get_task`, etter ja. Ett ja kan gjelde flere navngitte klienter.
- Klient med lønn men uten oppgave → varsel.

### 3. Skyldig trekk og AGA (L2, L8)
1. `notPaid` gjelder terminen (`taxPeriodName`, to måneder), med forfall den 15. i måneden etter terminen. Negativ `notPaid` = for mye innbetalt;
   det motregnes eller kreves tilbake (forklares i `lonnsavstemming`).
2. KID og forfall: Tally `hent_amelding_rapport` når A07 for terminen er bestilt (per innsendt a-melding), ellers Altinn-tilbakemeldingen (steg 5).
3. Skattetrekkskonto-modell: `get_balance_sheet` 1950 ≥ 2600 (L8). Direkte modell: trekket betales på lønnsdato og 1950 er ubrukt.
4. Betalingen opprettes av regnskapsføreren i Tripletex og godkjennes av kunden.

### 4. Send (per klient og måned, etter ja)
1. Vis statusen fra steg 1 og hva som sendes: lønnsopplysninger og arbeidsforhold for måneden, og at et bilag for avrunding og AGA-korreksjon
   kan bli laget (bilagsdato er siste dag i måneden med mindre brukeren sier noe annet).
2. Etter eksplisitt ja for akkurat denne klienten og måneden: `send_amelding({companyName, month, confirm: true})`.
3. Stopper verktøyet fordi meldingen ville tatt med historiske lønnskjøringer (kjørt i et annet system), spør om Tripletex skal rapportere dem.
   Bare ved ja: kall på nytt med `includeHistoricalRuns: true`.
4. Rapporter meldingsnummer, antall arbeidsforhold og om det ble laget bilag. Svaret fra Skatteetaten kommer senere (steg 5, eller steg 1 på nytt).
5. Korrigert melding for en tidligere måned (rettet arbeidsforhold i `lonnskjoring`): samme flyt for den måneden. Bare arbeidsforhold
   (`employmentInformationOnly: true`) når brukeren ber om akkurat det.

### 5. Altinn-tilbakemelding (L9)
1. Tally `list_altinn_innboks` per klient (`sender: "Skatteetaten"`, `only_unread`) → tilbakemeldingen på a-meldingen for måneden.
2. Avvist eller med feil: `les_altinn_melding`. Oppsummer feilene uten persondata (feiltype, «ansatt 1», arbeidsforhold), rett i `lonnskjoring`,
   og send på nytt etter nytt ja (steg 4). En avvist melding sendes aldri slik den var.
3. Fiken- og PowerOffice-klienter: kvitteringen her er eneste kilde til status.

## Svar

Tabell: Klient · Måned · Status · Skyldig trekk/AGA (termin) · Forfall · Neste steg. Rekkefølge: ikke sendt → avvist/endret → venter →
kunne ikke leses → godkjent (godkjente kan samles på én linje: «N klienter godkjent»). Summer per klient er greit; aldri navn, beløp per person
eller feiltekst fra Altinn med persondata.

## Lever

Fullfør i Tally: se `tally-gjoremal`. «A-melding» fullføres per klient når meldingen for måneden er sendt og godkjent (eller kvitteringen ligger i Altinn); 10 minutter er standard. Kommentaren inneholder måned, meldingsnummer, antall arbeidsforhold, skyldig trekk/AGA for terminen og forfall.

## Fallgruver

- Tripletex tidsavbrudd mens den venter på svar: utfallet er usikkert. Send aldri på nytt; les `get_amelding_status` og involver brukeren.
- Feil fra Skatteetaten eller Altinn: ingenting er levert, og et nytt forsøk litt senere er greit.
- Alt rapportert for måneden: verktøyet sender ingenting. Si at måneden er levert; ikke prøv andre argumenter.
- `largeFileUploadInProgress: true`: meldingen leveres i bakgrunnen. Vent, ikke send på nytt.
- `includeHistoricalRuns` og `employmentInformationOnly` settes aldri på eget initiativ.
- 403 på en klient betyr manglende lønnsrolle for brukeren, ikke at klienten er uten lønn.

## Referanser

- `docs/kontrollkatalog.md`: L2, L4, L6–L10 (L2 leses også av `balanseavstemming`).
- Skillene `lonnskjoring` (lønnskjøring, arbeidsforhold, rettinger), `lonnsavstemming` (A07 mot regnskapet), `tally-gjoremal` (fullføring, ikke aktuell).
