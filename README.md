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

## Skills som hører til

- `lonnsavstemming-a07` – full terminavstemming av lønn mot A07 (leverer hit)
- `bankavstemming-aapne-poster` – åpne bankposter som liste til kunden
- `aarsoppgjoer-kontroll` – kvalitetssikring av årsregnskap og skattemelding

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
