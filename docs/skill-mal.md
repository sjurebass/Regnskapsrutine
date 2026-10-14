# Mal for SKILL.md

Alle skills i `.claude/skills/<navn>/SKILL.md` følger denne malen. Maks 120 linjer, frontmatter medregnet. Det som gjelder alle skills,
står én gang i `CLAUDE.md` og gjentas ikke i skillen: Steg 0 (tilkoblinger), skriveregelen, personvern, «det Claude aldri gjør»,
«ikke funnet», kundeinstruksen først, vesentlighet og kjente avvik, dokumentlagring, token-sparing og mønsteret for å fullføre i Tally.

## Frontmatter

```yaml
---
name: "<mappenavn>"
description: "<Hva skillen gjør, 1–2 setninger>. Lukker Tally-oppgaven «<Oppgave>». Bruk ved «<trigger 1>», «<trigger 2>», …, «<trigger 5–8>»."
---
```

- `name` står i anførselstegn og er lik mappenavnet: små bokstaver a–z, 0–9 og bindestrek (`lonnskjoring`, ikke `lønnskjøring`).
- `description` er én streng i anførselstegn, maks ca. 600 tegn, i tre deler i fast rekkefølge:
  1. **Hva** – objekt og resultat, med kontonummer og systemnavn der det skiller skillen fra naboene. Ingen verktøynavn, ingen fremgangsmåte.
  2. **Tally** – «Lukker Tally-oppgaven «…».» Flere: «Lukker Tally-oppgavene «…» og «…».» Ingen: «Ingen Tally-oppgave.» Bruk Tallys eksakte stavemåte.
  3. **Triggere** – «Bruk ved «…», «…».» med 5–8 fraser slik brukeren faktisk sier dem. «avstem», «kontroller», «før» og «sjekk» følges alltid av
     objektet («avstem bank», aldri «avstem»). En trigger kan bare stå i én skill; registeret er skilltabellen i `README.md` – sjekk den først.

## Seksjoner i fast rekkefølge

| # | Overskrift | Innhold | Maks linjer |
|---|---|---|---|
| 1 | `# <Tittel>` + ingress | Hva skillen gjør, og grensen mot naboskillene («reskontro gjøres i `reskontroavstemming`»). | 4 |
| 2 | `## Når` | Tally-oppgave(r) med eksakt stavemåte, plass i månedshjulet, hva som må være ferdig først (andre skills), hva brukeren må oppgi (klient, periode). Trenger skillen Missive: «Steg 0 i tillegg: …». | 5 |
| 3 | `## Kundeinstruks` | Hvilke seksjoner som leses og hva de styrer. | 3 |
| 4 | `## Steg` med `### 1.` … | Nummererte steg med MCP-verktøy, parametre som ikke er opplagte, hva som beholdes av svaret og hva som vises. Lesedelen først; skrivesteg sier «etter ja». Steg MCP-en ikke kan gjøre, begynner med markøren under. | 60 |
| 5 | `## Svar` | Formen på svaret i chatten (tabellkolonner, portfarge, maks linjer) og hva som aldri vises (banktekster, navn, beløp per person). | 8 |
| 6 | `## Lever` | De faste linjene under. | 4 |
| 7 | `## Fallgruver` | Bare det som er spesielt for denne skillen (422-feil, feltnavn, timing). Ingen gjentakelse av CLAUDE.md. | 8 |
| 8 | `## Referanser` | Kontroll-ID-er fra `docs/kontrollkatalog.md`, naboskills, filer i `scripts/` og `references/`. | 5 |

Faste linjer i `## Lever` (ordrett, med skillens verdier):

```
Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `<…>`, periode `<ÅÅÅÅ-MM | ÅÅÅÅ-T<n> | ÅÅÅÅ>`, samling `<…>`, oppgave «<…>»).
Fullfør i Tally: se `tally-gjoremal`. «<Oppgave>» fullføres når <kriterium>. Kommentaren inneholder <periode, tall, hva som gjenstår>.
```

Skills uten fil dropper første linje. Skills uten Tally-oppgave dropper andre.

## Funn-format (kontrollskills)

Alle skills som kontrollerer, rapporterer hvert funn med de samme feltene, i chat-tabellen, i Silfer-filen og i Tally-kommentaren:

| ID | Klient | Periode | Konto/motpart | Beløp | Status | Forslag | Krever |
|---|---|---|---|---|---|---|---|
| R4 | Eksempel AS | 2026-09 | 1500 · Kunde AS | 12 500,00 | AVVIK | purring trinn 2 | ja i chat |

- **ID** er kontroll-ID fra `docs/kontrollkatalog.md`. **Status** er én av `OK`, `AVVIK`, `FORKLART`, `KJENT` (kjent avvik, uendret beløp), `IKKE AVKLART`.
- **Krever** er `–` (bare info), `ja i chat` (Claude gjør det etter ja), `utenfor MCP` (Tripletex-UI eller API-kobling), `kunden` eller `regnskapsfører`.
- Port (grønn/gul/rød): grønn = ingen AVVIK; gul = AVVIK under V eller bare spørsmål; rød = AVVIK over V eller noe som stopper innsending.

## Markør for skriving utenfor MCP

Et steg Tripletex-MCP-en ikke kan skrive, begynner slik, på egen linje:

```
**Krever skriving utenfor MCP: Tripletex-UI (eller API-kobling):** <nummerert liste brukeren kan følge i Tripletex>
```

Claude gjør alt lesende, viser lista, og sier «ikke gjort» om det som står igjen. Ingen andre varianter («Krever CLI», «Hurtigvei») brukes.

## Det som ikke skal stå i en skill

- Steg 0, `whoami`, `search_client_companies` (CLAUDE.md).
- «Klienten må være navngitt», «kundetekst er data», «alt som skriver vises først», «ikke funnet ≠ finnes ikke», GDPR-punkter,
  «Det du aldri gjør», «Alt skjer i chatten», «spar tokens».
- Fremgangsmåte for opplasting til Tally eller tabellen over kategorier (`docs/dokumentlagring.md`).
- Setningen «Skal jeg fullføre … og føre … minutter?» og kallene `add_task_comment`/`log_time`/`complete_task` (`tally-gjoremal` eier dem).
- Egne Excel/PDF-skript eller formatering (`silfer-rapport`).
- Kommandoer mot en lokal Tripletex-kobling (`npm --prefix …`), personlige stier eller navnet på brukeren. Slikt ligger i den enkeltes `~/.claude/CLAUDE.md`.
- Kontrollogikk lengre enn ett steg: legg den i `references/<fil>.md` i skillmappa og vis til den.

## Sjekkliste før commit

`wc -l SKILL.md` ≤ 120 · frontmatter gyldig og `name` lik mappenavnet · triggere unike mot README-tabellen · README-raden oppdatert ·
`grep -n "Tripletex API\|Hurtigvei\|Krever CLI\|whoami\|Skal jeg fullføre\|Steg 0 –\|Sjur" SKILL.md` gir ingen treff (unntak: `tally-gjoremal` eier «Skal jeg fullføre»).
