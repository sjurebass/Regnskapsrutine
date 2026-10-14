---
name: "tally-gjoremal"
description: "Frister, oppgaver og timer i Tally: fristliste og prioritering, mønsteret for å fullføre en oppgave med notat og timer (alle skills viser hit), gjentakende gjøremål, kunderutiner, masseplanlegging og timeføring. Lukker enhver Tally-oppgave, også «Oversendelse mangelliste» som ikke har egen skill. Bruk ved «se fristlisten», «hva haster», «fullfør oppgaven», «lag et gjøremål hver mandag», «sett kunderutine», «før timer for i dag», «legg inn kurs», «fyll opp timelisten»."
---

# Tally – gjøremål, frister og timer

Det daglige arbeidet i Tally som ikke hører til én bestemt avstemming: hva som haster, hvordan en oppgave fullføres, gjentakende gjøremål,
rutinene som styrer fristene, og timeføring. Alle andre skills fullfører oppgaver etter mønsteret i steg 2 her.

## Når

- Fristlisten om morgenen, timer på slutten av dagen, og hver gang en annen skill er ferdig og oppgaven skal fullføres.
- «Oversendelse mangelliste» har ingen felles skill og fullføres herfra.
- Steg 0 i tillegg: Missive (kalenderen) for timeføring.

## Kundeinstruks

Leses ikke direkte. Skillen for oppgaven leser det den trenger. Kunderutinene (lønnsdato, bilagsfrist, termin for mva) ligger i Tally (steg 4).

## Steg

### 1. Fristlisten

1. `list_deadlines` (standard: forfalt + neste 30 dager; `days_ahead` ved behov). `list_tasks` med `assignee: "meg"` for egne oppgaver.
2. Prioriter: lovpålagte frister som er forfalt (a-melding, mva, skattetrekk, aksjonærregister) → lønn før lønnsdato → bilag og mangelliste
   før avstemmingene som avhenger av dem → oppgaver uten ansvarlig → det som kan vente.
3. Sjekk fagsystemet før du sier at noe ikke er gjort. A-meldingen kan være sendt selv om oppgaven er åpen: se `a-melding`.

### 2. Fullfør en oppgave

Dette er det eneste stedet mønsteret står; `CLAUDE.md` og alle skills peker hit. Det gjelder også «Oversendelse mangelliste».

1. Foreslå tidsbruk og spør: «Skal jeg fullføre <oppgave> for <klient> og føre <X> minutter?» Brukeren kan rette tiden.
2. Ved ja, i samme steg:
   - `add_task_comment`: det skillens `## Lever` sier (periode, hva som ble gjort, hva som gjenstår). Én til tre korte linjer, bare for byrået.
   - `log_time` med `client_id`, `task_id`, dato for når arbeidet ble gjort, minutter og en `idempotency_key` (ny UUID per føring).
   - `complete_task`. Gjentakende oppgaver får neste forekomst automatisk; si det.
3. Fullfør bare forekomsten for perioden som faktisk er gjort. Fullfører du oktober-oppgaven for bankavstemming, ser oktober avstemt ut.
4. Nekter Tally å la agenten fullføre oppgavetypen, bruk `be_om_avklaring` i stedet.
5. Er oppgaven ikke aktuell, bruk `mark_task_not_applicable` med begrunnelse og `versjon` fra `get_task`. Det lager også neste forekomst.

### 3. Gjentakende gjøremål

- Eget gjøremål: `opprett_eget_gjoremaal` med RRULE, for eksempel `RRULE:FREQ=WEEKLY;BYDAY=MO` (hver mandag) eller
  `RRULE:FREQ=MONTHLY;BYMONTHDAY=5` (den 5.). Velg helligdagsregel (neste eller forrige virkedag); klokkeslett og fremgangsmåte i beskrivelsen.
- Tally lager én forekomst om gangen. Sjekk `list_egne_gjoremaal` først, så det ikke blir duplikater.
- Maloppgaver (fra tjenestemalen, f.eks. månedlig «Bilagsbehandling») kan ikke slås av per klient via MCP. Skal en klient ha en annen
  frekvens, lag eget gjøremål og be brukeren slå av malen på klientkortet i Tally.

### 4. Kunderutiner som styrer frister

- `hent_kunderutiner` viser rutinespørsmålene per tjeneste (lønnsdato, bilagsfrist, termin for mva) med verdi og status satt/mangler/ugyldig.
- `sett_kunderutine` endrer svarene. Forhåndsvisningen viser hvilke automatiske oppgaver som flyttes (gammel → ny frist).
- Lønnsdato og standardfristene for lønnsoppgavene: se `lonnskjoring` (steg 4, lønnsdatoer inn i Tally).
- Mangler et svar som bare kunden kan gi: be om det med `send_message` der verktøyet finnes (krever bekreftelse), ellers som Missive-utkast.

### 5. Masseplanlegging

`planlegg_oppgaver` lager en plan uten å endre noe (opprett mange oppgaver, omfordel fra én ansatt, eller legg inn årsoppgjørsløpet).
Vis tabellen, og kall `utfor_plan` med samme argumenter og `plan_token` først etter ja. Planen gjelder i 30 minutter.

### 6. Før timer

1. Finn hva som er gjort: arbeidet i denne chatten; i Claude Desktop dagens økter (`list_sessions` / `get_session`, ellers spør brukeren);
   møter fra Missive-kalenderen (`get_calendar_events`; Tally har ingen kalender); allerede førte timer (`list_time_entries` for dagen).
2. Lag en forslagstabell: dato · klient · oppgave · minutter · fakturerbar · beskrivelse.
3. Ved ja: `log_time` per linje med ny `idempotency_key`. Timene lagres som utkast; brukeren sender timelisten fra Tally.

- Klientarbeid føres på klientens oppgave for perioden. `log_time` krever klient eller oppgave.
- Internt og ikke-fakturerbart føres på «Intern administrasjon». Finnes den ikke, opprett en byråintern oppgave (etter ja).
- Kurs og fagforum: `submit_course_entry` for etterutdanningen **og** timer på en egen intern oppgave med kursets navn.
- Standard tidsbruk: 30 minutter for løpende bilagsbehandling, 10 minutter per a-melding. Spør når du ikke vet; ikke anta 60.
- Fastprisklienter: vanlig føring. Bare ekstraarbeid får beskrivelsen «Ikke inkludert i fastpris – faktureres i tillegg».
- Dagsmål 7,5 timer. Ber brukeren om å «fylle opp», fyll differansen med intern tid og si hvor mye. Dater timene til dagen arbeidet ble gjort.
- Klienter som ikke finnes i Tally: før som intern tid med klientnavnet i beskrivelsen, og si at klienten mangler i Tally.

### 7. Dokumenter

- Se hva som ligger på en klient eller oppgave: `list_documents` (`client_id` eller `task_id`, `search`), og `get_document` for lenke.
- Rydd: `organize_document` legger i samling eller arkiverer (`archived: true` skjuler også for kunden). `delete_document` har forhåndsvisning.
- Opplasting, kategorier og samlinger: `docs/dokumentlagring.md`.

## Svar

- Fristlisten: frist · klient · oppgave · status · neste steg (hvilken skill). Spør hvilke klienter du skal starte på.
- Timer: forslagstabellen i steg 6. Etter føring: sum per dag og hva som gjenstår til dagsmålet.
- Etter fullføring: én linje per oppgave med minutter, og om neste forekomst er laget.

## Lever

Fullfør i Tally: mønsteret i steg 2. «Oversendelse mangelliste» fullføres når utkastet er sendt, eller det ikke er noe å etterlyse. Kommentaren inneholder periode og hva som ble etterlyst (eller at det ikke var noe).

## Fallgruver

- Bruk id-er fra leseverktøyene (`list_clients`, `list_tasks`, `list_deadlines`, `get_task`) når du skriver.
- Tally-MCP-en kan ikke endre eller slette timeføringer, endre estimater eller slå av maloppgaver per klient. Si hvilken føring eller
  innstilling som må endres, og hvor i Tally.
- Fullfør aldri en oppgave der arbeidet ikke er gjort. Timelisten sendes av brukeren, aldri av Claude.

## Referanser

- `docs/kontrollkatalog.md`: D4 periodelåsing hører til `periodeavslutning`.
- Skillene `lonnskjoring` (lønnsdatoer), `a-melding` (status), `kundeinstruks` (klientregler); `docs/dokumentlagring.md` (arkivet).
