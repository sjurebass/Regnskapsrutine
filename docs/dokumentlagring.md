# Dokumentlagring i Tally

Alle filer byrået lager eller får (rapporter, kontoutskrifter, notater, mangellister) lagres i **klientens dokumentarkiv i Tally**
via Tally-MCP-en. Det som kommer fra Altinn (A07, kvitteringer, brev fra Skatteetaten og andre etater), ligger allerede i Tally via
byråets Maskinporten-tilgang (Altinn-fanen på klientkortet). Det lastes aldri ned eller opp på nytt; vis til meldingen i kommentaren. Det finnes ingen kundemapper på PC-en. Claudes scratch-mappe brukes bare mens filen lages, og tømmes etterpå.

Skillene viser hit i stedet for å gjenta fremgangsmåten.

## Før du laster opp

- **Kunden kan se dokumentarkivet.** Et dokument blir synlig for kunden når opplastingen er fullført. Last bare opp det kunden kan se:
  rapporter, avstemminger, kontoutskrifter, mangellister og notater skrevet for kunden. Byråets interne vurderinger hører i
  kundeinstruksen (`kundeinstruks`) eller som internt notat på oppgaven (`add_task_comment`), ikke som dokument.
- Skal et dokument bare være for byrået, arkiver det rett etter opplasting med `organize_document` (`archived: true`). Da forsvinner det
  fra den aktive lista, også for kunden. Si det til brukeren.
- **Opplasting er skriving.** Vis filnavn, klient, kategori, periode og oppgave, og last opp etter ja. Et ja kan dekke alle filene fra én
  kjøring for én klient.
- Personvern: kundens egne data (kortholder i mangellisten) kan gå i kundens arkiv. Ikke last opp
  data om andre klienter, og ikke legg personopplysninger i filnavn eller beskrivelser.

## Slik lastes det opp

1. **Før første opplasting i en økt:** sjekk med ToolSearch hvilke Tally-verktøy som finnes: `upload_document`, `start_opplasting`, `fullfor_opplasting`.
2. **Filer under 3 MB:** `upload_document`.
3. **Filer fra 3 til 25 MB:** `start_opplasting` (klient, filnavn, MIME-type, nøyaktig størrelse i byte, kategori, periode, oppgave) →
   send bytene uendret med HTTP PUT til `upload_url` med nøyaktig de headerne svaret gir → `fullfor_opplasting` med `ticket`.
   `upload_url` gir skrivetilgang; vis den aldri i chatten.
   ```bash
   curl -sS -X PUT --data-binary "@<fil>" -H "Content-Type: <mime>" <øvrige headere fra svaret> "<upload_url>"
   ```
4. **Kontroller** med `list_documents` (klient eller oppgave) at dokumentet ligger der, og gi brukeren lenken.
5. **Slett filen fra scratch** når den er lagret.

**Mangler verktøyet for å fullføre** (`upload_document` for små filer, `fullfor_opplasting` for store): start ikke en opplasting som ikke kan
fullføres. Si «ikke lagret i Tally», del filen i chatten med SendUserFile, og be brukeren dra den inn på oppgaven i Tally. Skriv aldri noe
som kan leses som at filen er lagret.

## Kategori, periode og samling

| Dokument | Kategori | Periode | Samling | Knytt til oppgave |
|---|---|---|---|---|
| Åpne bankposter (Excel), bankavstemmings-PDF, kontoutskrift | `BILAG` | `ÅÅÅÅ-MM` | `Bankavstemming ÅÅÅÅ` | Bankavstamming |
| Kontoutskrifter per 31.12 (fra kunden) | `BILAG` | `ÅÅÅÅ-12` | `Bankavstemming ÅÅÅÅ` | Bankavstamming |
| Mangelliste til kunden (Excel) | `BILAG` | `ÅÅÅÅ-MM` | `Mangelliste ÅÅÅÅ` | Oversendelse mangelliste |
| Reskontroavstemming (Excel) | `BILAG` | `ÅÅÅÅ-MM` | `Reskontro ÅÅÅÅ` | Avstemming kundereskontro / Avstemming leverandørreskontro |
| Kontoutskrift kundereskontro / leverandørreskontro per motpart (PDF, til kunden) | `BILAG` | `ÅÅÅÅ-MM` | `Reskontro ÅÅÅÅ` | Gjennomgang kunde- og leverandørreskontro |
| Bilagskontroll (Excel, byråintern – arkiveres rett etter opplasting) | `BILAG` | `ÅÅÅÅ-MM` | `Bilagskontroll ÅÅÅÅ` | Kontroll av bilag |
| Balanseavstemming per måned (Excel) | `BILAG` | `ÅÅÅÅ-MM` | `Balanseavstemming ÅÅÅÅ` | Avstemming balansekontoer |
| Mva: 2740-notat, reskontrovurdering, betalingsinfo | `MVA_RAPPORT` | `ÅÅÅÅ-T<n>` | `Mva ÅÅÅÅ` | MVA-kontroll / MVA-innlevering |
| Lønnsavstemming (Excel) | `LONN` | `ÅÅÅÅ-T<n>` (år: `ÅÅÅÅ`) | `Lønn ÅÅÅÅ` | Avstemming av AGA og forskuddstrekk / Årsavslutning lønn |
| Perioderapport (PDF, bare når kunden vil ha fil) | `ANNET` | `ÅÅÅÅ-MM` | `Perioderapporter ÅÅÅÅ` | Ferdigstillelse perioderegnskap |
| Årsoppgjør forberedelse – sjekkliste (Excel); årsoppgaver, lagerliste, kasseoppgjør 31.12 fra kunden | `ARSOPPGJOR` | `ÅÅÅÅ` | `Årsoppgjør ÅÅÅÅ` | Forberedelse |
| Balanseavstemming 31.12 (Excel) og balansespesifikasjon (PDF) | `ARSOPPGJOR` | `ÅÅÅÅ` | `Årsoppgjør ÅÅÅÅ` | Balanseavstemming |
| RF-1086 sjekkliste (Excel, pseudonymisert) | `ARSOPPGJOR` | `ÅÅÅÅ` | `Årsoppgjør ÅÅÅÅ` | RF-1086 |
| Årsoppgjørskontroll (PDF) | `ARSOPPGJOR` | `ÅÅÅÅ` | `Årsoppgjør ÅÅÅÅ` | Skattemelding / Årsregnskap |
| Låneavtaler, protokoller, aksjeeierbok, avtaler | `KONTRAKT` | `ÅÅÅÅ` | – | – |
| Oppdragskontroll (PDF, byråintern – internt arkiv eller arkiveres straks) | `ANNET` | `ÅÅÅÅ` | – | – (kvalitetsgjennomgangen i Tally) |
| Brev til kunden eller styret (PDF), annet | `ANNET` | `ÅÅÅÅ-MM` | – | Oppgaven det gjelder |

- Legg dokumentet i samlingen med `organize_document` (`collection`) etter opplasting. Samlingene erstatter årsmappene som lå på PC-en.
- Filnavn: `<Hva> <periode> <Klient>.<endelse>`, for eksempel `Bankavstemming åpne poster 2026-09 Eksempel AS.xlsx`.
- Samme fil for samme periode: last opp ny versjon og arkiver den gamle (`organize_document`, `archived: true`). Slett ikke.
- Claude kan ikke legge ved filer i Missive-utkast. E-posten til kunden viser til dokumentet i Tally.

## Tripletex i tillegg

Noe dokumentasjon hører også hjemme i Tripletex: vedlegg på bilag, kontoutskrift på manuell bankavstemming, og vedlegg og kommentarer i
avstemmingsmodulen. Det er skriving utenfor MCP: Tripletex-UI eller API-kobling (se markøren i skillene). Tally er arkivet; Tripletex får det regnskapet trenger.
