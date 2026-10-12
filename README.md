# Regnskapsrutine

Byråets felles Claude-skills for løpende regnskap: Tripletex som regnskapssystem, Tally som praksissystem og Missive for e-post.
Klon repoet, åpne mappa i Claude Code, og si for eksempel «kjør mangelliste» eller «hvem mangler mva for t5».

Repoet inneholder skills, indekser og referanser – aldri regnskap eller kundedata. Klientreglene ligger i kundeinstruksen i Tally,
filene i klientens dokumentarkiv i Tally ([docs/dokumentlagring.md](docs/dokumentlagring.md)), og utkast til kunden i Missive. Reglene Claude følger står i [CLAUDE.md](CLAUDE.md).

## Skills

| Skill | Si for eksempel | Tally-oppgave | Leser fra | Skriver til | Krever utover MCP | Status |
|---|---|---|---|---|---|---|
| [`mangelliste`](.claude/skills/mangelliste/SKILL.md) | «kjør mangelliste» | Oversendelse mangelliste | Tally, Tripletex, Missive (Fiken/PO via Chrome) | Missive-utkast, Tally | – | I bruk |
| [`bilagsforing`](.claude/skills/bilagsforing/SKILL.md) | «bilagsføring på <klient>» | Bilagsbehandling | Tripletex, Tally | Tripletex (bilag, match), Tally | Føring: CLI eller Tripletex-UI | Ny |
| [`bankavstemming`](.claude/skills/bankavstemming/SKILL.md) | «bankavstemming for <klient>», «hvilke klienter har åpne bankkontoer» | Bankavstemming | Tripletex | Tally-dokument (Excel) | Matching/lukking: CLI eller UI. Excel: `uv` | Ny |
| [`mva-termin`](.claude/skills/mva-termin/SKILL.md) | «hvem mangler mva for t5», «avstem mva for <klient>» | MVA-kontroll, MVA-innlevering | Tripletex, Tally (Altinn) | Avstemmingsmodulen, Tally | Del B/C: CLI eller UI | Omskrevet |
| [`lonn`](.claude/skills/lonn/SKILL.md) | «lag lønnsutkast», «legg inn lønnsendringen», «er a-meldingen sendt» | Lønnsforslag, Kjør lønn, A-melding | Tripletex, Missive, Tally | Tripletex (lønnskjøring, arbeidsforhold), Tally | – | Ny |
| [`lonnsavstemming-a07`](.claude/skills/lonnsavstemming-a07/SKILL.md) | «lønnsavstemming termin 4 for <klient>» | Terminvis lønnsavstemming | A07-XML, Tripletex | Tally-dokument (Excel, A07) | `uv` | Oppdatert |
| [`tally-gjoremal`](.claude/skills/tally-gjoremal/SKILL.md) | «se fristlisten», «før timer for i dag» | alle | Tally, Missive-kalender | Tally | – | Ny |
| [`kundeinstruks`](.claude/skills/kundeinstruks/SKILL.md) | «hent kundeinstruks for <klient>», «husk for <klient> at …» | – | Tally | Tally (kundeinstruks) | – | Ny |
| [`leverandorindeks`](.claude/skills/leverandorindeks/SKILL.md) | «er <leverandør> mva-registrert», «vurder leverandøren» | – | `data/leverandorer.json`, Brreg | `data/leverandorer.json` | Filsystem (Claude Code) | Ny |
| [`aarsoppgjoer-kontroll`](.claude/skills/aarsoppgjoer-kontroll/SKILL.md) | «kontroller årsoppgjøret» + filer | Årsoppgjør | Opplastede filer, Brreg | Tally-dokument (PDF) | `uv` | Oppdatert |

«CLI» er Sjurs egen Tripletex-kobling (`C:\Users\Sjur\Tripletex API`). Skillene merker stegene som trenger den med
**Krever CLI (Sjur) eller Tripletex-UI:**. Uten CLI gir Claude en ferdig liste å gjøre i Tripletex.

## Indekser

| Indeks | Hvor | Brukes til |
|---|---|---|
| Skillindeksen | Denne fila | Hvilken skill gjør hva |
| Klientindeksen | Kundeinstruksen i Tally, fast mal (skillen `kundeinstruks`) | System, bank, mva, lønn, bilagsregler, kjente avvik per klient |
| Leverandørindeksen | [`data/leverandorer.json`](data/leverandorer.json) (skillen `leverandorindeks`) | Mva-behandling og Brreg-fakta per leverandør, felles for alle klienter |
| Tripletex-endepunktindeksen | [`tripletex-api/`](tripletex-api/README.md) | Om et Tripletex-kall finnes, parametere og fallgruver |
| Kontrollkatalogen | [`docs/kontrollkatalog.md`](docs/kontrollkatalog.md) | Alle løpende kontroller, hvilken skill og hvilket MCP-verktøy |
| Dokumentarkivet | Tally, per klient: kategori, periode og samling ([`docs/dokumentlagring.md`](docs/dokumentlagring.md)) | Hvor rapporter, kontoutskrifter, A07 og notater lagres |

## Månedshjulet

| Når | Hva | Skill | Tally-oppgave |
|---|---|---|---|
| 1.–5. | Mangelliste for forrige måned, så bilag som kan føres mot bank | `mangelliste`, `bilagsforing` | Oversendelse mangelliste, Bilagsbehandling |
| 5. | A-melding for forrige måned levert? Stripe-, Dintero- og andre oppgjørsbilag | `lonn`, `bilagsforing` | A-melding |
| Lønnsdato − 2 virkedager | Lønnsutkast | `lonn` | Kjør lønn |
| Lønnsdato | Lønnsslipper (regnskapsfører fullfører kjøringen) | `lonn` | Send lønnsslipper |
| 10. i partallsmåneder (31.8 for mai–juni) | Mva: hvem mangler, kontroll før innsending, etterarbeid | `mva-termin` | MVA-kontroll, MVA-innlevering |
| 15. i oddetallsmåneder | Skattetrekk og arbeidsgiveravgift forfaller | `lonn` (status), `lonnsavstemming-a07` | Terminvis lønnsavstemming |
| Løpende | Bankavstemming, fristliste, timer | `bankavstemming`, `tally-gjoremal` | Bankavstemming |
| Årlig | Årsoppgjør, aksjonærregister (31.1), skattemelding (31.5), årsregnskap (31.7) | `aarsoppgjoer-kontroll`, `mva-termin --aarlig` | Årsoppgjørsløpet |

Frister som faller på en helg eller helligdag, flyttes til neste virkedag.

## Oppsett for kollegaer

1. **Connectorer** i Claude (claude.ai → Innstillinger → Connectors): Tally MCP, Tripletex (tripletex-mcp-iota.vercel.app) og Missive.
   Claude in Chrome trengs bare for Fiken- og PowerOffice-klienter i `mangelliste`.
2. **Claude Code** (desktop-appen eller terminalen). Klon repoet og åpne mappa:
   ```bash
   git clone https://github.com/sjurebass/Regnskapsrutine.git
   ```
3. **uv** for Excel- og PDF-skriptene (ingen admin-rettigheter trengs). Bak bedriftsproxy: sett `UV_SYSTEM_CERTS=1`.
   ```powershell
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```
4. **Node** (for `tripletex-api/finn.js`) er valgfritt.

Skillene kan også lastes inn som enkeltmapper i Claude Desktop (Innstillinger → Skills), men `leverandorindeks` og `tripletex-api/` krever repoet.

## Annet

- [`docs/maskinporten.md`](docs/maskinporten.md) – vurdering av Maskinporten for A07 og brev fra det offentlige. Tilgangspakker må være på plass
  for alle klienter før 31.12.2026.
- Den første Python-månedskontrollen (september 2026) ligger i git-taggen `v1-python`.

## Grenser

Claude leser fritt, men alt som skriver, vises først og krever ja. Claude sender aldri e-post, mva-melding eller (uten ja) a-melding, godkjenner aldri
lønn eller betaling, låser aldri perioder og sletter aldri permanent.
