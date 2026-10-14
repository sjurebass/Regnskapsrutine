# Regnskapsrutine

Byråets felles Claude-skills for løpende regnskap: Tripletex som regnskapssystem, Tally som praksissystem og Missive for e-post.
Klon repoet, åpne mappa i Claude Code, og si for eksempel «bankavstemming for <klient>» eller «hvem mangler mva for t5».

Repoet inneholder skills, indekser og referanser – aldri regnskap eller kundedata. Klientreglene ligger i kundeinstruksen i Tally,
filene i klientens dokumentarkiv i Tally ([docs/dokumentlagring.md](docs/dokumentlagring.md)), og utkast til kunden i Missive.
Reglene Claude følger står i [CLAUDE.md](CLAUDE.md); malen alle skills følger i [docs/skill-mal.md](docs/skill-mal.md). Alt går via MCP-koblingene.

## Skills

| Skill | Si for eksempel | Tally-oppgave | Leser | Skriver | Krever utover MCP |
|---|---|---|---|---|---|
| [`tally-gjoremal`](.claude/skills/tally-gjoremal/SKILL.md) | «se fristlisten», «fullfør oppgaven», «før timer for i dag» | alle (eier «fullfør»-mønsteret) | Tally, Missive-kalender | Tally (oppgaver, timer, rutiner) | – |
| [`kundeinstruks`](.claude/skills/kundeinstruks/SKILL.md) | «hva vet vi om <klient>», «husk for <klient> at …» | – | Tally | Tally (kundeinstruks) | – |
| [`leverandorindeks`](.claude/skills/leverandorindeks/SKILL.md) | «er <leverandør> mva-registrert», «vurder leverandøren» | – | `data/leverandorer.json`, Brreg | `data/leverandorer.json` | Filsystem (Claude Code) |
| [`silfer-rapport`](.claude/skills/silfer-rapport/SKILL.md) | brukes av de andre skillene; «lag Silfer-pdf» | – | spec.json | xlsx/pdf i scratch | `uv`, Edge |
| [`bilagsforing`](.claude/skills/bilagsforing/SKILL.md) | «bilagsføring på <klient>», «før bilagene i mottaket» | Bilagsbehandling | Tripletex, Tally | Tripletex (bilag, vedlegg, match), Tally | Føring: Tripletex-UI |
| [`bilagskontroll`](.claude/skills/bilagskontroll/SKILL.md) | «kontroll av bilag for <måned>», «bilag uten vedlegg» | Kontroll av bilag | Tripletex, Tally | Tally-dokument (Excel), Tally | Rettinger: Tripletex-UI |
| [`bankavstemming`](.claude/skills/bankavstemming/SKILL.md) | «bankavstemming for <klient>», «hvilke klienter har bankkontoer som ikke er lukket» | Bankavstamming | Tripletex, Tally | Tally-dokument (Excel), Tally | Match og lukking: Tripletex-UI |
| [`reskontroavstemming`](.claude/skills/reskontroavstemming/SKILL.md) | «avstem reskontro for <klient>», «forfalte fakturaer» | Avstemming kundereskontro, Avstemming leverandørreskontro | Tripletex, Brreg, Tally | Tally-dokument (Excel, kontoutskrift-PDF), Tally | Utligning og modul: Tripletex-UI |
| [`balanseavstemming`](.claude/skills/balanseavstemming/SKILL.md) | «avstem balansen», «balansespesifikasjon» | Avstemming balansekontoer, Balanseavstemming | Tripletex, Tally | Tally-dokument (Excel), Tally | Avstemmingsmodulen: Tripletex-UI |
| [`periodeavslutning`](.claude/skills/periodeavslutning/SKILL.md) | «ferdigstill perioderegnskapet», «er <måned> klar til å lukkes» | Ferdigstillelse perioderegnskap, Lukking av regnskapsperiode | Tripletex, Tally | Tally (månedsrapport-utkast) | Periodelås: Tripletex-UI |
| [`mva-kontroll`](.claude/skills/mva-kontroll/SKILL.md) | «mva-kontroll for <klient> t<n>», «klar til å sende mva» | MVA-kontroll | Tripletex, Tally, `docs/fradragsregler-kort.md` | Tally-dokument (2740-notat), Tally | Rettinger og modul: Tripletex-UI |
| [`mva-innlevering`](.claude/skills/mva-innlevering/SKILL.md) | «hvem mangler mva for t<n>», «sendt og synkronisert» | MVA-innlevering | Tripletex, Tally (Altinn) | Tally | Opprett, send, lås: regnskapsfører med ID-porten |
| [`lonnskjoring`](.claude/skills/lonnskjoring/SKILL.md) | «kjør lønn for <måned>», «legg inn lønnsendringen» | Innsamling lønnsgrunnlag, Kjør lønn, Send lønnsslipper, Feriepengeberegning | Tripletex, Missive, Tally | Tripletex (lønnsutkast, arbeidsforhold), Tally | Fullføring av kjøringen: Tripletex-UI |
| [`a-melding`](.claude/skills/a-melding/SKILL.md) | «er a-meldingen sendt», «hvem mangler a-melding» | A-melding | Tripletex, Tally | Tripletex (send etter ja), Tally | – |
| [`lonnsavstemming`](.claude/skills/lonnsavstemming/SKILL.md) | «lønnsavstemming termin <n> for <klient>», «årsavslutning lønn» | Avstemming av AGA og forskuddstrekk, Årsavslutning lønn | Tally (A07 via Altinn), Tripletex | Tally-dokument (Excel), Tally | `uv` · modul: Tripletex-UI |
| [`aarsoppgjoer-forberedelse`](.claude/skills/aarsoppgjoer-forberedelse/SKILL.md) | «forbered årsoppgjøret», «hva mangler før årsoppgjøret» | Forberedelse | Tripletex, Tally | Tally (årsoppgjørsstatus, dokument), Missive-utkast | – |
| [`aksjonaerregister`](.claude/skills/aksjonaerregister/SKILL.md) | «aksjonærregister for <klient>», «RF-1086» | RF-1086 | Tripletex, Brreg, Tally | Tally-dokument (sjekkliste), Tally | Levering: regnskapsfører i Altinn |
| [`aarsoppgjoer-kontroll`](.claude/skills/aarsoppgjoer-kontroll/SKILL.md) | «kontroller årsoppgjøret» + filer | Skattemelding, Årsregnskap | Opplastede filer, Brreg | Tally-dokument (PDF) | `uv` |
| [`kvalitetskontroll`](.claude/skills/kvalitetskontroll/SKILL.md) | «kvalitetskontroll av <klient>» | kvalitetsgjennomgang i Tally | Tally, Tripletex | Tally (kvalitetsgjennomgang) | Attestering: oppdragsansvarlig |

«Krever utover MCP» er skriving Tripletex-MCP-en ikke har. Skillene merker stegene med **Krever skriving utenfor MCP: Tripletex-UI (eller API-kobling):**
og gir en nummerert liste å gjøre i Tripletex. Oppgaven «Oversendelse mangelliste» har ingen felles skill; fullfør den med `tally-gjoremal`.

`balanseavstemming`, `periodeavslutning`, `aarsoppgjoer-forberedelse`, `aksjonaerregister` og `kvalitetskontroll` er utkast: stegene kalibreres
første gang de kjøres på en klient.

## Indekser

| Indeks | Hvor | Brukes til |
|---|---|---|
| Skillindeksen | Denne fila | Hvilken skill gjør hva; hver trigger står i én skill |
| Klientindeksen | Kundeinstruksen i Tally, fast mal (skillen `kundeinstruks`) | System, bank, mva, lønn, bilagsregler, reskontro og balanse, kjente avvik, årsoppgjør per klient |
| Leverandørindeksen | [`data/leverandorer.json`](data/leverandorer.json) (skillen `leverandorindeks`) | Mva-behandling og Brreg-fakta per leverandør, felles for alle klienter |
| Tripletex-endepunktindeksen | [`tripletex-api/`](tripletex-api/README.md) | Om et Tripletex-kall finnes, parametere og fallgruver |
| Kontrollkatalogen | [`docs/kontrollkatalog.md`](docs/kontrollkatalog.md) | Alle kontroller med ID, skill, MCP-verktøy og grunnlag |
| Fradragsreglene | [`docs/fradragsregler-kort.md`](docs/fradragsregler-kort.md) (full versjon: [`docs/fradragsregler.md`](docs/fradragsregler.md)) | Vurdering av inngående mva i `bilagskontroll` og `mva-kontroll` |
| Dokumentarkivet | Tally, per klient: kategori, periode og samling ([`docs/dokumentlagring.md`](docs/dokumentlagring.md)) | Hvor rapporter, kontoutskrifter, A07 og notater lagres |

## Månedshjulet

| Når | Tally-oppgave | Skill |
|---|---|---|
| 1. i fristmåneden (feb, apr, jun, aug, okt, des) | MVA-innlevering – frister 10.2, 10.4, 10.6, 31.8, 10.10, 10.12 | `mva-innlevering` |
| 5. | A-melding (forrige måned) | `a-melding` |
| 5.–12. | Oversendelse mangelliste | – (`tally-gjoremal` for fullføring) |
| 5.–20. | Bilagsbehandling | `bilagsforing` |
| 10. i oddetallsmåneder (jan, mar, mai, jul, sep, nov) | Avstemming av AGA og forskuddstrekk – betaling forfaller 15. | `lonnsavstemming`, `a-melding` (skyldig beløp) |
| 15. | Bankavstamming · Kontroll av bilag | `bankavstemming`, `bilagskontroll` |
| 16. | Avstemming balansekontoer | `balanseavstemming` |
| 20. | Avstemming kundereskontro · Avstemming leverandørreskontro | `reskontroavstemming` |
| 25. i måneden før mva-fristen | MVA-kontroll | `mva-kontroll` |
| Kundens frist (kunderutine) | Innsamling lønnsgrunnlag | `lonnskjoring` |
| Lønnsdato − 2 virkedager / lønnsdato | Kjør lønn / Send lønnsslipper | `lonnskjoring` |
| Uten frist | Ferdigstillelse perioderegnskap, Lukking av regnskapsperiode | `periodeavslutning` |

Årlig:

| Når | Tally-oppgave | Skill |
|---|---|---|
| 15.1 | Forberedelse | `aarsoppgjoer-forberedelse` |
| 29.1 | RF-1086 · Årsavslutning lønn | `aksjonaerregister`, `lonnsavstemming` (årsmodus) |
| 26.2 | Balanseavstemming | `balanseavstemming` (årsmodus) |
| 31.5 | Skattemelding | `aarsoppgjoer-kontroll` |
| 1.6 | Feriepengeberegning | `lonnskjoring` |
| 30.6 | Årsregnskap · Generalforsamling | `aarsoppgjoer-kontroll` · – |
| Etter risikoklasse | Kvalitetsgjennomgang | `kvalitetskontroll` |

Frister på helg eller helligdag flyttes til neste virkedag. Rekkefølgen i måneden følger avhengighetene:
bilag → bank → reskontro og balanse → mva og lønn → periodeavslutning.

## Oppsett for kollegaer

1. **Connectorer** i Claude (claude.ai → Innstillinger → Connectors): Tally MCP, Tripletex (tripletex-mcp-iota.vercel.app) og Missive.
2. **Claude Code** (desktop-appen eller terminalen). Klon repoet og åpne mappa:
   ```bash
   git clone https://github.com/sjurebass/Regnskapsrutine.git
   ```
3. **uv** for `silfer-rapport` og skriptene (ingen admin-rettigheter trengs). Bak bedriftsproxy: sett `UV_SYSTEM_CERTS=1`.
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   PDF lages med Microsoft Edge, som finnes på alle maskinene.
4. **Node** (for `tripletex-api/finn.js`) er valgfritt.

Skillene bruker felles filer (`silfer-rapport`, `docs/`, `data/`), så last inn hele repoet, ikke enkeltmapper.

## Senere

- Oppgaver uten skill: Oversendelse mangelliste, Generalforsamling, Betalinger, kundens egne oppgaver (Laste opp manglende bilag,
  Oversende lønnsgrunnlag, Godkjenning av lønn) og onboarding.
- Retningen er en komplett regnskapsfører: skillene er byggeklosser med en lesedel og en ja-liste, og funn i samme format.
  Neste steg er løpende bokføring per banktransaksjon, kontinuerlige kontroller med funn som avvik i Tally, og én dagsliste per regnskapsfører.
- [`docs/maskinporten.md`](docs/maskinporten.md) – bakgrunn for Maskinporten-integrasjonen. Den er nå i bruk via Tally (A07, kvitteringer og brev).
