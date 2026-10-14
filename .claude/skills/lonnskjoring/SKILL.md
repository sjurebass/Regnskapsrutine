---
name: "lonnskjoring"
description: "Løpende lønn i Tripletex: innsamling av lønnsgrunnlag og lønnsendringer fra kundens e-post (nytt arbeidsforhold, ny lønn eller stillingsprosent fra dato, etterbetaling), lønnsutkast med faste lønnslinjer (aldri fullført av Claude), lønnsslipper, feriepenger og lønnsdatoer inn i Tally. Lukker Tally-oppgavene «Innsamling lønnsgrunnlag», «Kjør lønn», «Send lønnsslipper» og «Feriepengeberegning». Bruk ved «kjør lønn for <måned>», «lag lønnsutkast», «lønnskjøring», «legg inn lønnsendringen», «se mail om lønn», «send lønnsslipper», «sjekk lønnsdatoene», «feriepengeberegning»."
---

# Lønnskjøring

Den løpende lønnen i Tripletex: lønnsgrunnlag og endringer fra kunden, lønnsutkast, lønnsslipper, feriepenger og lønnsdatoene som styrer
fristene i Tally. Status og innsending av a-meldingen er `a-melding`; avstemming mot A07 per termin og år er `lonnsavstemming`.

## Når

- Tally «Innsamling lønnsgrunnlag» (kundens frist), «Kjør lønn» (lønnsdato − 2 virkedager), «Send lønnsslipper» (lønnsdato), «Feriepengeberegning» (1.6).
- Klient og måned må være sagt. Grunnlaget fra kunden (timer, endringer) må være kommet før utkastet lages.
- Steg 0 i tillegg: Missive-søk når oppgaven gjelder e-post fra kunden.

## Kundeinstruks

«Lønn»: lønnsdato, modell (direkte trekk eller skattetrekkskonto), pensjon og når timegrunnlaget kommer. Styrer utkastet og lønnsdatoene i steg 4.

## Steg

### 1. Innsamling lønnsgrunnlag og lønnsendringer fra e-post
1. Finn e-posten i Missive (`search_conversations`, `get_conversations`). Er noe uklart (er 40 % stillingsprosent eller et engangsbeløp?), spør:
   det rapporteres ulikt i a-meldingen.
2. Les dagens arbeidsforhold, bare feltene som trengs. Den ansatte: `npm run -s api -- GET /employee isInactive=false fields=id,employeeNumber,firstName,lastName
   --client "<klient>"` (navn kommer maskert som initialer). Deretter samme kall mot `/employee/employment employeeId=<id> fields=id,startDate,endDate`
   og `/employee/employment/details employmentId=<id> fields=id,date,employmentType,employmentForm,remunerationType,workingHoursScheme,occupationCode(code),percentageOfFullTimeEquivalent,annualSalary,hourlyWage`.
3. Vis forslaget med initialer: hva endres, og fra hvilken dato.
4. **Skriving (etter ja):** endring fra dato = ny detaljrad, så historikken og a-meldingen blir riktig. Kopier de uendrede feltene fra gjeldende rad:
   `npm run -s api -- POST /employee/employment/details body='{"employment":{"id":<id>},"date":"ÅÅÅÅ-MM-DD",…}' --client "<klient>" --bekreft`
   (først uten `--bekreft`). Nytt arbeidsforhold for en ansatt som finnes: `POST /employee/employment` med `employmentDetails` (form, prosent, lønn,
   yrkeskode fra kontrakten; `GET /employee/employment/occupationCode`). Gjett aldri, spør om det som mangler.
5. Etterbetaling: (ny − gammel månedslønn) × antall måneder, med delvise prosenter der det gjelder. Egen linje på neste kjøring med beskrivelse,
   for eksempel «Etterbetaling lønnsjustering mai–sep». Noen ganger lager Tripletex linjen selv; sjekk utkastet først.
6. Er en tidligere måned rapportert med feil (for eksempel stillingsprosent), trengs korrigert a-melding for den måneden: se `a-melding`.
7. Bekreftelse til kunden som Missive-utkast (punktliste, ingen beløp per person).

### 2. Kjør lønn (utkast)
Unntak: lønnsutkast og skattekort går via Tripletex-MCP-en.
«Lag lønnsutkast» betyr en lønnskjøring som ikke er fullført, med de faste lønnslinjene, klar til at regnskapsføreren ser over og fullfører.
Fullføring bokfører lønnsbilaget og frigir lønnsslippene; det gjør regnskapsføreren på kjøringens side i Tripletex, aldri Claude.
1. `get_salary_run_candidates` for måneden. Vis antall ansatte (ikke navn) og eventuelle sperrer, og få ja på utvalget.
2. Etter ja: `create_salary_run` med `month`, utvalget (`employeeIds`, eller `allSelectable` etter ja) og `voucherDate` = lønnsdato.
   Tripletex fyller fastlønn, godkjente timer, faste tillegg og trekk, godkjente reiser og utlegg, feriepenger i feriepengemåneden og skattetrekk.
3. Les resultatet (`get_salary_run`) og rapporter summer (brutto, skattetrekk, netto), advarsler og lenken til kjøringen.
4. Mangler en forventet linje, ligger den som regel allerede på en annen kjøring for samme måned. Sjekk det før du legger den til manuelt.
5. Justeringer (bonus, etterbetaling, trekk) med `execute_salary_lines` etter ja: lønnsart, antall, sats og beskrivelse «<Måned> <år>».
6. Skattekort: `get_taxcard_status`. Bestilling og henting (`order_taxcards`, `fetch_taxcards`) er skriving og krever ja.

### 3. Send lønnsslipper
1. På lønnsdato: `npm run -s api -- GET /salary/payslip yearFrom=ÅÅÅÅ yearTo=<år+1> monthFrom=M monthTo=<M+1> fields=id,date,grossAmount,amount,transaction(id)
   --client "<klient>"` (`yearTo` og `monthTo` er eksklusive). Fullført = lønnsbilaget finnes (samme kall mot `/ledger/voucher dateFrom=<lønnsdato>
   dateTo=<dagen etter> fields=id,number,voucherType(name)`). Et utkast har ikke bilag. Bare summer, aldri per person.
2. Fullført: slippene blir tilgjengelige for de ansatte på slippdatoen. Claude sender ingen slipper selv; oppgavene kan fullføres (Lever).
3. Ikke fullført: si det, gi lenken til kjøringen, og la «Kjør lønn» og «Send lønnsslipper» stå åpne.
4. Deretter a-meldingen for måneden: `a-melding`.

**Bare i Tripletex-UI:**
1. Fullføre (godkjenne) lønnskjøringen – regnskapsføreren.
2. Ny ansatt med personalia (fødselsnummer, kontonummer) – regnskapsføreren eller kunden.
3. Betaling av nettolønn og trekk – opprettes av regnskapsføreren, godkjennes av kunden.

### 4. Lønnsdatoer inn i Tally
1. Finn lønnsdatoen per klient fra kjøringene de siste månedene: `npm run -s lonn -- datoer --alle --fra ÅÅÅÅ-MM --til ÅÅÅÅ-MM --json`
   (`[{klient, maaned, dato, antall_slipper}]`), ellers fra kundeinstruksen.
2. Sammenlign med Tally `hent_kunderutiner` (rutinesvaret for lønnsdato) og fristene på lønnsoppgavene.
3. Standard: «Kjør lønn» to virkedager før lønnsdato, «Send lønnsslipper» på lønnsdato, fredag før når lønnsdatoen faller i helgen.
4. Etter ja: `sett_kunderutine` (forhåndsvisningen viser hvilke oppgaver som flyttes), eller fristen på én oppgave. Ett ja per klient.
5. Flagg avvik: klienter med lønnsoppgaver i Tally men ingen lønn i Tripletex, og klienter med lønn men uten oppgaver.

### 5. Feriepenger i juni («Feriepengeberegning»)
1. Kjøringen i feriepengemåneden (oftest juni) tar med feriepengene og ferietrekket selv; utkastet lages som i steg 2.
2. Før utkastet: les 2940 og 2785 (`npm run -s api -- GET /balanceSheet dateFrom=ÅÅÅÅ-01-01 dateTo=<dagen etter> accountNumberFrom=2785
   accountNumberTo=2940 fields=account(number),balanceIn,balanceChange,balanceOut --client "<klient>"`). Utbetalingen skal svare til fjorårets
   avsetning (IB 2940); differanse forklares (sluttede ansatte, endret sats, feil grunnlag).
3. Vis summer (utbetalte feriepenger, ferietrekk) og avviket mot 2940. Avsetningen for året kontrolleres i `lonnsavstemming` (L3).

## Svar

- Summer (brutto, skattetrekk, netto), antall ansatte, advarsler og lenken til kjøringen. Endringer vises med initialer og virkningsdato.
- Lønnsdatoer: tabell klient · lønnsdato · frist «Kjør lønn» · frist «Send lønnsslipper» · avvik.
- Aldri navn, fødselsnummer, kontonummer eller lønn per person.

## Lever

Fullfør i Tally: se `tally-gjoremal`. «Innsamling lønnsgrunnlag» fullføres når grunnlaget og endringene er lagt inn; «Kjør lønn» og «Send lønnsslipper» først når regnskapsføreren har fullført kjøringen; «Feriepengeberegning» når feriepengekjøringen er fullført og avviket mot 2940 er forklart. Kommentaren inneholder måned, antall ansatte, summene og hva regnskapsføreren må gjøre i Tripletex.

## Fallgruver

- En endring fra en dato skrives aldri i den gjeldende detaljraden, men som ny rad med `date`. Rader som allerede er a-meldt, kan ikke endres i samme rad.
- `annualSalary` er årslønn ved 100 %: 80 % stilling med 480 000 i året gir `annualSalary` 600 000.
- Ugyldig dato (for eksempel 31.09): si det og bruk siste dag i måneden.
- Fastlønn, timer, reiser, utlegg og faste tillegg tas av første kjøring i måneden. Timer kommer bare med når timelisten er godkjent.
- Manglende skattekort gir 50 % trekk og en advarsel på kjøringen.
- Mange ansatte deles i flere kjøringer (Tripletex har en grense per lønnsbilag); svaret sier det.

## Referanser

- Skillene `a-melding` (status, innsending, korrigert melding), `lonnsavstemming` (A07, feriepengeavsetning), `tally-gjoremal` (kunderutiner, fullføring), `kundeinstruks` («Lønn»).
- `docs/kontrollkatalog.md`: L3 og L5 kontrolleres i `lonnsavstemming`.
