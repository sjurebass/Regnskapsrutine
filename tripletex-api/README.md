# Tripletex API-koblingen

Kommandolinjeverktøy mot Tripletex API v2 for byråets klienter. Skillene i `.claude/skills/` bruker det til lesing, uttrekk og – etter ja fra
brukeren – skriving. Alt kjøres fra **repo-rota**:

```bash
npm run -s <kommando> -- <argumenter>
```

`-s` gir ren utskrift (uten npm-støy). Kildekoden ligger i `tripletex-api/src/`, nøkkelen i `tripletex-api/.env` (git-ignorert, per person).
Ingen npm-avhengigheter.

## Oppsett (én gang per person)

1. **Node.js 20.6 eller nyere**: `node --version`. Installer fra nodejs.org om den mangler.
2. **Nøkkel**: du trenger din egen Tripletex API-nøkkel (som regel et JWT refresh token som starter med `tlxr_`). Den får du av den som
   administrerer byråets Tripletex-integrasjon. Nøkkelen gir tilgang til klientene som er delegert til deg.
3. **Legg inn nøkkelen** (skjult inntasting, havner bare i `tripletex-api/.env`):
   ```bash
   npm run set-token
   ```
   Kjør den direkte i en terminal. Nøkkelen vises aldri, heller ikke deler av den. Lim den aldri inn i chat.
4. **Sjekk nøkkelen** (ingen nettverkskall): `npm run token` – viser nøkkeltype og utløp.
5. **Røyktest**: `npm run -s klienter` – lister klientene nøkkelen har tilgang til.

Valgfritt:
- `uv` (Python) for `bankavstemming --excel` og andre Silfer-Excel-rapporter.
- Microsoft Edge eller Google Chrome for PDF-notatene i `modul` (notat-2740, reskontro-vurdering).
- `pdftotext` (Poppler, følger med Git for Windows) for tekst fra PDF i `bilag hent` og `dokument`.

Flere byråer: har du tilgang via flere byråer, legg inn én nøkkel per byrå med `npm run set-token -- <navn>` (blir `TRIPLETEX_TOKEN_<NAVN>`).
Klientlistene slås sammen, og hvert kall går automatisk via riktig nøkkel. Se `tripletex-api/.env.example` for alle innstillinger.

## Kommandoer

Klient angis alltid med `--client "<navn|org.nr.|id>"` (en unik del av navnet holder) eller `--alle`. Verktøyet velger aldri klient selv.
Uten `--ut` skrives filer til `%TEMP%\rr\<kommando>-<periode>` – aldri inne i repoet. Kall går alltid ett om gangen (tokenfornyingen tåler
ikke parallelle kall).

### Oppsett og oppslag

| Kommando | Bruk | Utdata |
|---|---|---|
| `set-token [navn]` | legger inn `TRIPLETEX_TOKEN` (eller `TRIPLETEX_TOKEN_<NAVN>`, `employee`, `consumer`) i `tripletex-api/.env` | «lagret» |
| `token` | nøkkeltype og utløp (ingen nettverk) | tekst |
| `klienter [--sok <tekst>] [--json]` | klientene nøkkelen har tilgang til | tabell eller JSON `[{id, navn, orgnr, konto}]` |
| `finn -- <ord>` / `finn -- --sti /sti [METODE]` | offline endepunktindeks | tekst |
| `probe -- --client <k>` | lesetilgang per område (bare status, ingen data) | tekst |
| `connect` | test av nøklene og whoAmI per klient (alle klienter) | tekst |

### Generisk API

```bash
npm run -s api -- <METODE> </sti> [nøkkel=verdi …] [body='<json>'] (--client <k> | --client <k> --client <k2> | --alle) [--sider] [--ut <fil>] [--bekreft]
```

- GET: svaret som JSON, maskert. `--sider` henter alle sider (`{antall, values}`). Flere klienter / `--alle`: JSON-liste `[{klient, ok, data|feil}]`.
- `--ut <fil>`: lagrer svaret til fil – binært for PDF og dokumentinnhold, ellers maskert JSON – og skriver bare sti og størrelse.
  Binære svar uten `--ut` skrives aldri ut.
- POST/PUT/DELETE: uten `--bekreft` vises metode, sti, parametre og body (tørrkjøring), og ingenting sendes. Skrivende kall går bare mot én klient.
- Bruk alltid `fields=` med bare feltene oppgaven trenger.

### Fagkommandoer

| Kommando | Lese/skrive | Utdata |
|---|---|---|
| `bankavstemming -- --til ÅÅÅÅ-MM [--fra ÅÅÅÅ-MM] (--client <k> \| --alle) [--ut <mappe>] [--excel]` | lese | `status.json` per konto (`kontoId`) og måned: avstemming (`avstemmingId`), lukket, åpen, bevegelse, UB, bankens sluttsaldo (`bankSaldo`) og `differanse`, `bank[]` umatchede bankposter (med `id` der kontoutskriften har den), `tx` umatchede posteringer, `forslag` ikke godkjente matcher; `<Klient>.data.json` (formatet `lag_spec.py` leser); oversikt `.md`. `--excel` kjører `.claude/skills/bankavstemming/scripts/lag_spec.py` |
| `bilag -- hent --client <k> --til ÅÅÅÅ-MM [--fra ÅÅÅÅ-MM] [--ut <mappe>]` | lese | `forslag.json`, `bank.json` (med transaksjons-id), `historikk.tsv`, `leverandorer.tsv`, `docs/<id>.pdf + .txt` |
| `bilag -- før --client <k> --plan <plan.json> [--bare <id,…>] [--bekreft]` | skrive | avansert bilag → vedlegg → bekreft vedlegg → lukk 2400 → bankmatch → slett mottakskopi; logg `<plan>.resultat.json` |
| `lonn -- hent --client <k> --aar ÅÅÅÅ --termin 1–6 [--a07 <a07.json>] [--ut <mappe>]` | lese | `<ut>/ledger.json` for `lonnsavstemming_a07.py` |
| `lonn -- datoer (--client <k> \| --alle) --fra ÅÅÅÅ-MM --til ÅÅÅÅ-MM [--json]` | lese | `[{klient, maaned, dato, antall_slipper}]` |
| `amelding -- status (--client <k> \| --alle) --maned ÅÅÅÅ-MM [--json]` | lese | per klient: gruppe (ikke sendt / venter / godkjent / avvist / endret etter innsending / kunne ikke leses), forklaring, påløpt og ubetalt trekk/AGA/finansskatt, termin |
| `amelding -- oversikt (--client <k> \| --alle) --ar ÅÅÅÅ [--json]` | lese | status per måned |
| `amelding -- send --client <k> --maned ÅÅÅÅ-MM [--kun-arbeidsforhold] [--bilagsdato ÅÅÅÅ-MM-DD] [--bekreft]` | skrive | meldingsnummer, antall arbeidsforhold, om bilag ble laget |
| `pensjon -- --client <k> --ar ÅÅÅÅ [--konto 5945]` | lese | pensjon mot a-melding og A07 per termin |
| `mva -- "<klient>" --aar ÅÅÅÅ --termin N --json [--gjenbruk] [--aarlig]` | lese | kontroller før innsending (port, punkter, `tilVurdering` ≤ 10) |
| `mva -- status (--client <k> \| --alle) --aar ÅÅÅÅ --termin N [--json]` | lese | registrering, terminlengde, levert, betalt, rest, forfall, KID, saldo 2740, åpne mva-krav på skattekontoen |
| `modul -- perioder\|linjer\|vedlegg\|mva-oversikt\|kontroll-utkast --client <k> …` | lese | avstemmingsmodulen; `kontroll-utkast --aar --termin` gir utkast mot hovedbok, status, KID og forfall |
| `modul -- notat-2740 --client <k> --aar --termin [--forklaring-MM "beløp\|tekst"] [--ut]` | lese (lager PDF) | Silfer-PDF |
| `modul -- reskontro-vurdering --client <k> --dato ÅÅÅÅ-MM-DD [--vurderinger <json>] [--json] [--ut]` | lese (lager PDF) | Silfer-PDF; med `--json` også `<ut>/reskontro-vurdering.json` (poster per konto og motpart, kategorisert) og sammendrag på konsollen |
| `modul -- utlign\|lukk --client <k> … [--bekreft]` | skrive | lukker poster som går i null (én konto, én motpart, sum 0) |
| `modul -- last-opp\|sett-status\|fullfor\|laas-opp --client <k> … [--bekreft]` | skrive | avstemmingsmodulen |
| `modul -- bankpdf --client <k> --konto 1920 --maaned ÅÅÅÅ-MM [--ut]` | lese (eksport) | Tripletex' bankavstemmings-PDF |
| `leverandor -- finn\|vis\|liste\|oppslag\|vurder\|importer\|oppdater … [--json]` | lese; `vurder`/`oppslag`/`importer`/`oppdater` skriver til `data/leverandorer.json` | felles leverandørindeks (Enhetsregisteret + byråets vurderinger) |
| `status -- (--client <k> \| --alle) --maaned ÅÅÅÅ-MM [--json]` / `--aar ÅÅÅÅ` | lese | port per klient: bilagsmottak, ikke bokførte bilag, bank lukket per konto, reskontro 1500/2400 mot saldo, a-melding, observasjonskonti (1370/1960/7799), perioder lukket, mva for siste termin; `--aar` gir hele året |
| `dokument -- --client <k> (--bilag <nr-år\|id> \| --faktura <id>) [--ut <mappe>]` | lese | `<ut>/<id>.pdf` + maskert `<id>.txt` |

Leverandørvurderinger: `--av agent` (standard) eller regnskapsførerens initialer (`--av AB`). En vurdering gjort av en regnskapsfører
overskrives ikke av andre uten `--tving`.

## Finne riktig kall

Før en Tripletex-oppgave som ingen kommando dekker – og alltid før du sier at noe ikke går:

1. `npm run -s finn -- <ord>` (norsk eller engelsk, æøå valgfritt). Gir oppskrifter (kall, påkrevde parametere, `fields=`, fallgruver),
   områder og enkeltkall. Prøv 2–3 synonymer ved svake treff.
2. `npm run -s finn -- --sti /sti [METODE]` gir alle parametere, enum-verdier og skrivbare body-felt fra spec.
3. Test med et **lesende** kall: `npm run -s api -- GET /sti … --client "klient"`.
   403 = mangler tilgang eller modul hos klienten, ikke at kallet mangler. 404 på stien = feil sti. Les `validationMessages` på 422/403 –
   ofte en forretningsregel.
4. Først når 1–3 er gjort, kan du si at noe ikke er tilgjengelig. Si hva du søkte etter, og si **«ikke funnet»**, aldri «finnes ikke».

## Skriving

- Alle skrivende handlinger (føre bilag, matche bank, lukke poster, laste opp, sende a-melding, POST/PUT/DELETE i `api`) er tørrkjøring uten
  `--bekreft`. Tørrkjøringen viser hva som ville skjedd.
- `--bekreft` legges bare til **etter et eksplisitt ja fra brukeren** for akkurat den klienten og handlingen. Ett ja gjelder ikke senere handlinger.
- Bare i Tripletex-UI (ikke i API-et med nøkkel): periodelås, innsending og synk av mva-meldingen, godkjenning og fullføring av lønn,
  betalinger, registrering av pensjon og alt under `/tsk/salaryv2/*` (krever innlogging i nettleser).

## Personvern

- Personopplysninger (fødsels-/D-nummer, kontonummer, e-post, telefon, navn og adresse på personer) maskeres i all utskrift
  (`src/privacy.js`): `redact()` på feltnavn og `redactText()` på fritekst. Omgå aldri maskeringen i egne skript.
- `--umaskert` i `api` virker bare når brukeren selv har satt miljøvariabelen `TRIPLETEX_UMASKERT=1`. Claude bruker den aldri.
- Hent bare det oppgaven krever: alltid `fields=`, og unngå personendepunktene (`/employee`, `/salary`, `/contact`, `/timesheet`,
  `/travelExpense`) med mindre oppgaven faktisk krever dem.
- Kommandoer på tvers av klienter skriver bare antall, summer og status til konsollen. Store uttrekk går til fil (`--ut`); bare sammendrag i chat.
- Filene i `%TEMP%\rr\` og mva-arbeidsmappa inneholder kundedata – slett dem når jobben er ferdig. Ingenting med kundedata skal i repoet.

## Fallgruver

- Kall må gå sekvensielt per prosess – tokenfornyingen tåler ikke parallelle kall.
- Til-datoer er eksklusive (`dateTo`, `/balanceSheet`, `/ledger/posting/openPost?date=`). `fullResultSize` er ikke et pålitelig totalantall –
  bla til en side gir færre enn `count` (`--sider` gjør det).
- `/balanceSheet` kan utelate kontoer uten IB, bevegelse og UB – manglende konto betyr saldo 0.
- `/voucherInbox/inboxFiltered` og `/incomingInvoice` gir 403 med nøkkel, `/voucherInbox/sendToArchive` gir 500. `sendToLedger` er `true` som standard.
- A-melding og pensjon bruker interne kall (`/salary/tskinternal/*`). `amelding send` er ikke testet med nøkkel og kan kreve ID-porten-innlogging;
  ha Tripletex-UI som reserve. Interne kall kan endres uten varsel – test lesende først.
- Mva: `/vatReturns/>vatTerm` og `/vatReturns/status/list` teller terminer fra første rad i `/vatTermSizeSettings`; `/vatReturns/status` og
  `vatTermAmount` bruker kalendernummer.
- `/claimsAndPayments` (skattekontoen) er et internt kall og kan gi 401/403 for enkelte klienter – vises som «kunne ikke leses».
- Byråkall (avstemmingsmodulen, companyId 0) gjøres bare i `modul` og `pensjon`, på en fast liste med stier, og krever at brukeren har tilgang
  til byråets avstemmingsmodul.

## Endepunktindeksen

Søkbar indeks over Tripletex API v2: alle kall gruppert per fagområde, oppgaveoppskrifter med påkrevde parametere, `fields=` og fallgruver,
og en oversikt over byråets avstemmingsmodul (interne kall). Bare lokale filer – ingen kall mot Tripletex og ingen nøkkel.

| Fil | Innhold |
|---|---|
| `docs/api-v2-oppgaver.md` | Oppgaveoppskrifter per område, fallgruver og «ikke i API v2» |
| `docs/api-v2-oversikt.md` | Alle kall gruppert per tag med beskrivelse og nøkkelord |
| `docs/avstemmingsmodul.md` | Avstemmingsmodulen (lønn, A07, mva, balanse): interne kall, referenceId-er og arbeidsflyt |
| `docs/api-v2-indeks.json` | Maskinlesbar indeks som `finn.js` bruker |
| `docs/openapi.json` | Offentlig spec, brukes av `--sti` |
| `docs/indeks/*.json` | Kildene: nøkkelord, oppgaver og fallgruver per område. Rett her og bygg på nytt |

```bash
npm run -s bygg-indeks                 # bygger api-v2-indeks.json, -oversikt.md og -oppgaver.md fra docs/indeks/
npm run -s bygg-indeks -- --hent-spec  # henter openapi.json på nytt og viser nye og fjernede kall
```

Nye kall i spec må få oppgave og nøkkelord i `docs/indeks/`. Ingen kundenavn eller ekte id-er i kildene; bruk `<kunde-id>`, «en klient».

## Filer

| Sti | Innhold |
|---|---|
| `src/tripletex.js`, `src/auth.js` | klient, klientliste, nøkler og sesjoner |
| `src/privacy.js` | maskering av personopplysninger |
| `src/valg.js` | felles valg: `--client`/`--alle`, standard utmappe, én klient om gangen |
| `src/cli.js` | `api`, `token`, `connect` |
| `src/klienter.js`, `src/status.js`, `src/dokument.js` | `klienter`, `status`, `dokument` |
| `src/bankavstemming.js`, `src/bilag.js`, `src/lonn.js`, `src/amelding.js`, `src/pensjon.js`, `src/modul.js`, `src/leverandor.js`, `src/probe.js` | fagkommandoene |
| `src/mva.js`, `src/mva/` | mva-kontrollen (`mva/kontroller/`), `mva status` (`mva/status.js`) og PDF-notatene (`mva/notater.js`) |
| `finn.js`, `build-index.js`, `docs/` | endepunktindeksen |
| `.env.example` | mal for `tripletex-api/.env` |
