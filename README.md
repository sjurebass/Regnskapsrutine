# Regnskapsrutine

Byråets felles Claude-skills for løpende regnskap: Tripletex som regnskapssystem, Tally som praksissystem og Missive for e-post.
Klon repoet, åpne mappa i Claude Code, og si for eksempel «bankavstemming for <klient>» eller «hvem mangler mva for t5».

Repoet inneholder skills, indekser og referanser – aldri regnskap eller kundedata. Klientreglene ligger i kundeinstruksen i Tally,
filene i klientens dokumentarkiv i Tally ([docs/dokumentlagring.md](docs/dokumentlagring.md)), og utkast til kunden i Missive.
Reglene Claude følger står i [CLAUDE.md](CLAUDE.md); malen alle skills følger i [docs/skill-mal.md](docs/skill-mal.md). Tripletex nås via byråets egen API-kobling
([tripletex-api/](tripletex-api/README.md)), Tally og Missive via MCP.

## Skills

| Skill | Si for eksempel | Tally-oppgave | Leser | Skriver | Bare i Tripletex-UI |
|---|---|---|---|---|---|
| [`tally-gjoremal`](.claude/skills/tally-gjoremal/SKILL.md) | «se fristlisten», «fullfør oppgaven», «før timer for i dag» | alle (eier «fullfør»-mønsteret) | Tally, Missive-kalender | Tally (oppgaver, timer, rutiner) | – |
| [`kundeinstruks`](.claude/skills/kundeinstruks/SKILL.md) | «hva vet vi om <klient>», «husk for <klient> at …» | – | Tally | Tally (kundeinstruks) | – |
| [`leverandorindeks`](.claude/skills/leverandorindeks/SKILL.md) | «er <leverandør> mva-registrert», «vurder leverandøren» | – | `data/leverandorer.json`, Brreg | `data/leverandorer.json` | – |
| [`silfer-rapport`](.claude/skills/silfer-rapport/SKILL.md) | brukes av de andre skillene; «lag Silfer-pdf» | – | spec.json | xlsx/pdf i scratch | – (`uv`, Edge) |
| [`bilagsforing`](.claude/skills/bilagsforing/SKILL.md) | «bilagsføring på <klient>», «før bilagene i mottaket» | Bilagsbehandling | Tripletex, Tally | Tripletex (bilag, vedlegg, match), Tally | – |
| [`bilagskontroll`](.claude/skills/bilagskontroll/SKILL.md) | «kontroll av bilag for <måned>», «bilag uten vedlegg» | Kontroll av bilag | Tripletex, Tally | Tally-dokument (Excel), Tally | rettinger på bank- og OCR-bilag |
| [`bankavstemming`](.claude/skills/bankavstemming/SKILL.md) | «bankavstemming for <klient>», «hvilke klienter har bankkontoer som ikke er lukket» | Bankavstamming | Tripletex, Tally | Tally-dokument (Excel), Tally | lukke avstemmingen |
| [`reskontroavstemming`](.claude/skills/reskontroavstemming/SKILL.md) | «avstem reskontro for <klient>», «forfalte fakturaer» | Avstemming kundereskontro, Avstemming leverandørreskontro | Tripletex, Brreg, Tally | Tally-dokument (Excel, kontoutskrift-PDF), Tally | – |
| [`balanseavstemming`](.claude/skills/balanseavstemming/SKILL.md) | «avstem balansen», «balansespesifikasjon» | Avstemming balansekontoer, Balanseavstemming | Tripletex, Tally | Tally-dokument (Excel), Tally | – |
| [`periodeavslutning`](.claude/skills/periodeavslutning/SKILL.md) | «ferdigstill perioderegnskapet», «er <måned> klar til å lukkes» | Ferdigstillelse perioderegnskap, Lukking av regnskapsperiode | Tripletex, Tally | Tally (månedsrapport-utkast) | periodelås |
| [`mva-kontroll`](.claude/skills/mva-kontroll/SKILL.md) | «mva-kontroll for <klient> t<n>», «klar til å sende mva» | MVA-kontroll | Tripletex, Tally, `docs/fradragsregler-kort.md` | Tally-dokument (2740-notat), Tally | – |
| [`mva-innlevering`](.claude/skills/mva-innlevering/SKILL.md) | «hvem mangler mva for t<n>», «sendt og synkronisert» | MVA-innlevering | Tripletex, Tally (Altinn) | Tally | opprette, sende og synke meldingen (ID-porten), låse perioden |
| [`lonnskjoring`](.claude/skills/lonnskjoring/SKILL.md) | «kjør lønn for <måned>», «legg inn lønnsendringen» | Innsamling lønnsgrunnlag, Kjør lønn, Send lønnsslipper, Feriepengeberegning | Tripletex, Missive, Tally | Tripletex (lønnsutkast, arbeidsforhold), Tally | fullføre kjøringen (utkast og skattekort via Tripletex-MCP) |
| [`a-melding`](.claude/skills/a-melding/SKILL.md) | «er a-meldingen sendt», «hvem mangler a-melding» | A-melding | Tripletex, Tally | Tripletex (send etter ja), Tally | meldinger med historiske kjøringer |
| [`lonnsavstemming`](.claude/skills/lonnsavstemming/SKILL.md) | «lønnsavstemming termin <n> for <klient>», «årsavslutning lønn» | Avstemming av AGA og forskuddstrekk, Årsavslutning lønn | Tally (A07 via Altinn), Tripletex | Tally-dokument (Excel), Tally | – |
| [`aarsoppgjoer-forberedelse`](.claude/skills/aarsoppgjoer-forberedelse/SKILL.md) | «forbered årsoppgjøret», «hva mangler før årsoppgjøret» | Forberedelse | Tripletex, Tally | Tally (årsoppgjørsstatus, dokument), Missive-utkast | – |
| [`aksjonaerregister`](.claude/skills/aksjonaerregister/SKILL.md) | «aksjonærregister for <klient>», «RF-1086» | RF-1086 | Tripletex, Brreg, Tally | Tally-dokument (sjekkliste), Tally | levering i Altinn |
| [`aarsoppgjoer-kontroll`](.claude/skills/aarsoppgjoer-kontroll/SKILL.md) | «kontroller årsoppgjøret» + filer | Skattemelding, Årsregnskap | Opplastede filer, Brreg | Tally-dokument (PDF) | `uv` |
| [`kvalitetskontroll`](.claude/skills/kvalitetskontroll/SKILL.md) | «kvalitetskontroll av <klient>» | kvalitetsgjennomgang i Tally | Tally, Tripletex | Tally (kvalitetsgjennomgang) | – (attestering: oppdragsansvarlig) |

Skriving i Tripletex gjør Claude med API-koblingen etter ja (**Skriving (etter ja):** i skillene, med `--bekreft`). Det API-et ikke kan, står i
kolonnen over og er merket **Bare i Tripletex-UI:** med en nummerert liste. Oppgaven «Oversendelse mangelliste» har ingen felles skill; fullfør den med `tally-gjoremal`.

`balanseavstemming`, `periodeavslutning`, `aarsoppgjoer-forberedelse`, `aksjonaerregister` og `kvalitetskontroll` er utkast: stegene kalibreres
første gang de kjøres på en klient.

## Indekser

| Indeks | Hvor | Brukes til |
|---|---|---|
| Skillindeksen | Denne fila | Hvilken skill gjør hva; hver trigger står i én skill |
| Klientindeksen | Kundeinstruksen i Tally, fast mal (skillen `kundeinstruks`) | System, bank, mva, lønn, bilagsregler, reskontro og balanse, kjente avvik, årsoppgjør per klient |
| Leverandørindeksen | [`data/leverandorer.json`](data/leverandorer.json) (skillen `leverandorindeks`) | Mva-behandling og Brreg-fakta per leverandør, felles for alle klienter |
| Tripletex-endepunktindeksen | [`tripletex-api/`](tripletex-api/README.md) | Om et Tripletex-kall finnes, parametere og fallgruver |
| Kontrollkatalogen | [`docs/kontrollkatalog.md`](docs/kontrollkatalog.md) | Alle kontroller med ID, skill, API-kall og grunnlag |
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

1. **Connectorer** i Claude (claude.ai → Innstillinger → Connectors): Tally MCP og Missive. Tripletex-connectoren
   (tripletex-mcp-iota.vercel.app) trengs bare for lønnsutkast og skattekort i `lonnskjoring`.
2. **Claude Code** (desktop-appen eller terminalen). Klon repoet og åpne mappa:
   ```bash
   git clone https://github.com/sjurebass/Regnskapsrutine.git
   ```
3. **Node** (versjon 20.6 eller nyere) for API-koblingen. Ingen `npm install` trengs.
4. **Din egen Tripletex-nøkkel** (aldri del den): kjør i repo-mappa og lim inn nøkkelen når du blir spurt. Den lagres i
   `tripletex-api/.env`, som aldri committes.
   ```powershell
   npm run set-token
   ```
   Sjekk at den virker – du skal se klientene du har tilgang til:
   ```powershell
   npm run -s klienter
   ```
5. **uv** for `silfer-rapport` og skriptene (ingen admin-rettigheter trengs). Bak bedriftsproxy: sett `UV_SYSTEM_CERTS=1`.
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
   PDF lages med Microsoft Edge, som finnes på alle maskinene.

Skillene bruker felles filer (`silfer-rapport`, `docs/`, `data/`), så last inn hele repoet, ikke enkeltmapper.

## Senere

- Oppgaver uten skill: Oversendelse mangelliste, Generalforsamling, Betalinger, kundens egne oppgaver (Laste opp manglende bilag,
  Oversende lønnsgrunnlag, Godkjenning av lønn) og onboarding.
- Retningen er en komplett regnskapsfører: skillene er byggeklosser med en lesedel og en ja-liste, og funn i samme format.
  Neste steg er løpende bokføring per banktransaksjon, kontinuerlige kontroller med funn som avvik i Tally, og én dagsliste per regnskapsfører.
- [`docs/maskinporten.md`](docs/maskinporten.md) – bakgrunn for Maskinporten-integrasjonen. Den er nå i bruk via Tally (A07, kvitteringer og brev).
