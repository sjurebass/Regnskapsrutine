# Dokumentlagring i Tally

Alle filer byrået lager eller får (rapporter, kontoutskrifter, A07, notater, mangellister) lagres i **klientens dokumentarkiv i Tally**
via Tally-MCP-en. Det finnes ingen kundemapper på PC-en. Claudes scratch-mappe brukes bare mens filen lages, og tømmes etterpå.

Skillene viser hit i stedet for å gjenta fremgangsmåten.

## Før du laster opp

- **Kunden kan se dokumentarkivet.** Et dokument blir synlig for kunden når opplastingen er fullført. Last bare opp det kunden kan se:
  rapporter, avstemminger, kontoutskrifter, mangellister og notater skrevet for kunden. Byråets interne vurderinger hører i
  kundeinstruksen (`kundeinstruks`) eller som internt notat på oppgaven (`add_task_comment`), ikke som dokument.
- Skal et dokument bare være for byrået, arkiver det rett etter opplasting med `organize_document` (`archived: true`). Da forsvinner det
  fra den aktive lista, også for kunden. Si det til brukeren.
- **Opplasting er skriving.** Vis filnavn, klient, kategori, periode og oppgave, og last opp etter ja. Et ja kan dekke alle filene fra én
  kjøring for én klient.
- Personvern: kundens egne data (lønn per ansatt i lønnsavstemmingen, kortholder i mangellisten) kan gå i kundens arkiv. Ikke last opp
  data om andre klienter, og ikke legg personopplysninger i filnavn eller beskrivelser.

## Slik lastes det opp

1. **Steg 0 i hver skill:** sjekk med ToolSearch hvilke Tally-verktøy som finnes: `upload_document`, `start_opplasting`, `fullfor_opplasting`.
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
| Åpne bankposter (Excel), bankavstemmings-PDF, kontoutskrift | `BILAG` | `ÅÅÅÅ-MM` | `Bankavstemming ÅÅÅÅ` | Bankavstemming |
| Mangelliste til kunden (Excel) | `BILAG` | `ÅÅÅÅ-MM` | `Mangelliste ÅÅÅÅ` | Oversendelse mangelliste |
| Mva: 2740-notat, reskontrovurdering, kvittering, betalingsinfo | `MVA_RAPPORT` | `ÅÅÅÅ-T<n>` | `Mva ÅÅÅÅ` | MVA-kontroll / MVA-innlevering |
| Lønnsavstemming (Excel), A07-XML | `LONN` | `ÅÅÅÅ-T<n>` | `Lønn ÅÅÅÅ` | Terminvis lønnsavstemming |
| Årsoppgjørskontroll (PDF), balansespesifikasjon | `ARSOPPGJOR` | `ÅÅÅÅ` | `Årsoppgjør ÅÅÅÅ` | Årsoppgjørsoppgaven |
| Låneavtaler, protokoller, avtaler | `KONTRAKT` | `ÅÅÅÅ` | – | – |
| Brev til kunden eller styret (PDF), annet | `ANNET` | `ÅÅÅÅ-MM` | – | Oppgaven det gjelder |

- Legg dokumentet i samlingen med `organize_document` (`collection`) etter opplasting. Samlingene erstatter årsmappene som lå på PC-en.
- Filnavn: `<Hva> <periode> <Klient>.<endelse>`, for eksempel `Bankavstemming åpne poster 2026-09 Eksempel AS.xlsx`.
- Samme fil for samme periode: last opp ny versjon og arkiver den gamle (`organize_document`, `archived: true`). Slett ikke.

## Tripletex i tillegg

Noe dokumentasjon hører også hjemme i Tripletex: vedlegg på bilag, kontoutskrift på manuell bankavstemming, og vedlegg og kommentarer i
avstemmingsmodulen. Det er skriving som krever CLI eller Tripletex-UI (se skillene). Tally er arkivet; Tripletex får det regnskapet trenger.

## Gamle filer på PC-en

Mappene i `C:\Users\Sjur\Desktop\avstemminger\<Kunde>\` er fra september 2026 og brukes ikke lenger. De kan flyttes til Tally klient for klient
med fremgangsmåten over (ett ja per klient), når Tally-MCP-en har verktøy for å fullføre opplastinger. Slett dem ikke før de er lagret i Tally.
