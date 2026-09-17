# avstemminger

Løpende regnskapskontroll av Tripletex-klientene, med én mappe per kunde (navn som i
Tripletex) og én undermappe per år.

## Komme i gang

Se [SETUP.md](SETUP.md) – tokens, klientliste, profiler og første kjøring.
Bakgrunnen og hele kontrollkatalogen står i [RUTINE-FORSLAG.md](RUTINE-FORSLAG.md).

```bash
uv run --system-certs python maanedskontroll.py --periode 2026-08
```

## Hva som ligger her

| | |
|---|---|
| `maanedskontroll.py` | kjører katalogen på alle aktive klienter og skriver rapportene |
| `sjekk-tilgang.py` | diagnose: virker tokenet, svarer endepunktene? |
| `hent-klienter.py` | henter klientlisten fra Tripletex og oppdaterer `klienter.json` |
| `synk-kunderegister.py` | synker `klienter.json` mot kunderegisteret (`Kundeoversikt*.xlsx` på skrivebordet) |
| `lag-klientfiler.py` | oppretter `klientprofil.md` og `kjente-avvik.md` for nye kunder |
| `selvtest.py` | kjører katalogen mot testdata med kjent fasit, uten API |
| `klienter.json` | hvilke klienter rutinen gjelder for (`aktiv: true`) |
| `tools/` | API-klient, datauthenting, kontroller, rapporter |
| `status/` | samlet statusrapport per måned + kjøringshistorikk |
| `mal/` | Silfer-logo og eksempelrapport |

## Per kunde

| | |
|---|---|
| `logg.md` | historikk – hver kjøring legger til en linje |
| `klientprofil.md` | hvilke kontroller som gjelder, kontonumre, vesentlighetsgrense |
| `kjente-avvik.md` | avvik som er vurdert og skal rapporteres som «kjent» |
| `<år>/` | rapporter, A07-filer og dokumentasjon |

## Skills – de andre rapportene

Ligger i `.claude/skills/` og følger med repoet. Klon, åpne mappa i Claude Code,
og skillene er tilgjengelige – be om «lønnsavstemming termin 3» eller «åpne
bankposter», så kjøres de.

| Skill | Gjør | Status |
|---|---|---|
| `lonnsavstemming-a07` | terminavstemming av lønn mot A07 fra Altinn → Excel + PDF | **kun instruksjoner** – se under |
| `bankavstemming-aapne-poster` | åpne bankposter per konto → Excel til kunden | komplett |
| `aarsoppgjoer-kontroll` | kvalitetssikring av årsregnskap og skattemelding → PDF | komplett |

**Merk om `lonnsavstemming-a07`:** skillen beskriver syv Excel-ark, PDF-mal og full
kontrollogikk, men skriptene den viser til (`scripts/lonnsavstemming_a07.py`,
`lag_pdf.py`, `hent_tripletex.js`, `references/kontrollogikk.md`) finnes ikke.
SKILL.md har derfor et avsnitt «Skriptet mangler?» som ber Claude bygge det på
nytt hver gang. Det virker, men gir ikke nødvendigvis identisk resultat fra gang
til gang – og det er nettopp det en kollega trenger. Skriptene bør skrives én gang
og legges i skillen.

Månedskontrollen erstatter ikke disse. Den fanger opp det løpende, og flagger når
en A07-avstemming mangler for terminen.

## Hva som bevisst ikke ligger i git

Repoet inneholder verktøyet, ikke regnskapet. `.gitignore` utelater alt som
standard og slipper inn verktøyfilene én for én, slik at en ny kundemappe havner
utenfor uten at noen må huske å oppdatere noe.

Utenfor git: alle kundemapper (`klientprofil.md` med kontonumre, `logg.md`,
A07-filer, rapporter), `status/`, `klienter.json` med kundenavn, og `.env` med
tokens. `klienter.eksempel.json` viser formatet.

Skal du dele repoet med en kollega, kan det gjøres som det står – men sjekk
`git status` før du legger til noe nytt.

## Grenser

Verktøyet leser fra Tripletex. Det bokfører ikke, sender ingenting inn til Altinn,
betaler ingenting og sender ingen e-post. Alle funn er forslag til deg.

Opprettet 10.09.2026 fra Tripletex-klientlisten. Kontrollrutine lagt til 17.09.2026.
