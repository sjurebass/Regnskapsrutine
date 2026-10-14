---
name: "silfer-rapport"
description: "Lager Silfer-Excel og Silfer-PDF for alle skills fra én spec.json: logo, byråets farger, tabeller med sum, løpende saldo, kontrollsum, resultat- og balanseoppstilling, statuskolonner og sidetall, med filnavn etter dokumentlagringsstandarden. Ingen Tally-oppgave. Bruk ved «lag Silfer-excel», «lag Silfer-pdf», «silfer-rapport», «rapport i byråets format», «eksporter tabellen til excel», «lag pdf av rapporten»."
---

# Silfer-rapport

Rapportgeneratoren for hele repoet: én spec.json blir til Excel (.xlsx), PDF (Edge/Chrome headless) og HTML i Silfer-stil.
Den kallende skillen eier innholdet (tall, vurderinger, kontroller) og skriver specen; ingen skill har egen styling, logo eller fonter.
Unntak til fase 2: `aarsoppgjoer-kontroll` lager sine to PDF-er med reportlab, men bruker logoen herfra.

## Når

- En skill sier «Lever: `silfer-rapport`», eller brukeren vil ha en tabell eller rapport som fil i byråets format.
- Klient og periode kommer fra den kallende skillen. Filen lages i scratch og lagres så i Tally etter `docs/dokumentlagring.md`.

## Kundeinstruks

Leses ikke her – den kallende skillen har lest den. Denne skillen henter ingen data fra Tripletex eller Tally.

## Steg

### 1. Skriv spec.json

Skriv filen med Write-verktøyet eller Python (UTF-8). Minste form:

```json
{"versjon": 1,
 "dokument": {"hva": "Kontoutskrift kundereskontro", "klient": "Eksempel AS", "orgnr": "123 456 789", "periode": "2026-09"},
 "seksjoner": [{"overskrift": "Åpne poster per 30.09.2026",
   "tabell": {"kolonner": [{"id": "dato", "tekst": "Dato", "type": "dato"}, {"id": "tekst", "tekst": "Tekst"},
                           {"id": "belop", "tekst": "Beløp", "type": "belop"}],
              "rader": [{"dato": "2026-09-10", "tekst": "Faktura 2026-0097", "belop": 4200.00}],
              "sum": {"etikett": "Sum åpne poster", "kolonner": ["belop"], "skal_vaere": 4200.00}}}]}
```

- `dokument`: `hva` (filnavn og bunntekst), `tittel`, `klient`, `orgnr`, `under[]`, `periode` (`ÅÅÅÅ-MM` | `ÅÅÅÅ-T<n>` | `ÅÅÅÅ`),
  `periode_tekst`, `utarbeidet`, `utarbeidet_av` (initialer), `bunntekst`, `sidetall`, `personvern.redact`.
- `seksjoner[]`: `ark` (Excel-fane), `overskrift`, `nivaa`, `tekst`, `sideskift`, én av `tabell` | `kontroller` | `sammendrag` | `oppstilling`,
  `boks` (`konkl` grønn | `varsel` oransje), `punkter[]`, `merknad`.
- Kolonnetyper: `tekst`, `heltall`, `dato`, `belop`, `antall`, `prosent`, `status`. `vis`: `begge` | `excel` | `pdf`.
- Status er en lukket mengde: OK, AVVIK, FORKLART, PERIODISERT, FEIL, MANGLER, MERKNAD, KJENT, IKKE AKTUELT, IKKE AVKLART.
- Avledede tall regnes ut av generatoren, aldri for hånd: `sum` (med `tell` og `skal_vaere` → OK/AVVIK), `lopende` (løpende saldo
  fra IB), `ib`/`ub`, `kontrollsum` (IB + pluss − minus = UB → «Kontrollert: …» i grønn boks, ellers avvik i oransje),
  `sammendrag` (COUNTIF/SUMIF over en annen seksjon), `kontroller` (A − B med toleranse og status) og `oppstilling` (grupper med
  sumlinje, resultatlinjer som ± andre linjer, avvik kr og % per rad, kontrollinje med `skal_vaere`). En bro er en `tabell` med `lopende` og `kontrollsum`.
  Excel får formler, PDF får de samme tallene beregnet.
- Fullt skjema: `references/spec.md`. Eksempler i `scripts/eksempler/`; `kontoutskrift_reskontro.json` er referanseutseendet.

### 2. Bygg

```bash
uv run --with openpyxl --with pillow --with pypdf python .claude/skills/silfer-rapport/scripts/rapport.py "<spec.json>" --mappe "<scratch>" --format xlsx,pdf
```

- Filnavn: «<Hva> <periode> <Klient>.xlsx» og «….pdf». `--behold-html` skriver også HTML-en PDF-en er laget fra.
- Feil i specen meldes med sti (`seksjoner[1].tabell.rader[3].belop: …`). Rett specen og kjør igjen.
- Exit 2: verken Edge eller Chrome finnes. HTML-en er skrevet i stedet; si «PDF ikke laget» og at den kan skrives ut fra nettleseren.
- Fra et skript: `sys.path.insert(0, "<repo>/.claude/skills/silfer-rapport/scripts")`, så `from silfer import bygg; bygg(spec, ut)`.

### 3. Sjekk

LibreOffice finnes ikke på maskinene; formlene beregnes når filen åpnes i Excel – derfor sjekk.py.

```bash
uv run --with openpyxl --with pypdf python .claude/skills/silfer-rapport/scripts/sjekk.py "<fil.xlsx>" "<fil.pdf>"
```

xlsx: feilverdier, semikolon og norske funksjonsnavn i formler, referanser til ark og rader som ikke finnes, logo i hvert ark.
pdf: «Side n av N» på hver side, tittel og logo på side 1, `/Author` = Silfer AS. Exit 1 betyr at filen ikke skal leveres.
`--sjekk` på `rapport.py` gjør det samme rett etter byggingen.

### 4. Forhåndsvis (valgfritt)

Åpne HTML-filen (`--behold-html`) i nettleserpanelet. Den er laget med samme motor og CSS som PDF-en.

## Svar

- Filnavn, ark og sider, resultatet av sjekk.py og antall felt maskert av personvernfilteret.
- Ikke lim inn tabellen eller banktekster i chatten – filen er leveransen.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori, periode, samling og oppgave gir den kallende skillen).

## Fallgruver

- Ny formatering hører hjemme i specen eller i `scripts/silfer/`, aldri i den kallende skillen.
- `personvern.redact` (standard på) maskerer kontonummer, IBAN, 11-sifrede nummer, e-post og telefon i tekst til «[skjult]».
  Navn maskeres ikke: bruk initialer eller «ansatt 1» i specen. Kundenavn er greit i reskontrodokumentasjon.
- Tekst som starter med `=`, `+`, `-` eller `@` skrives alltid som tekst i Excel (ingen formelinjeksjon fra banktekster).
- PowerShell `>` skriver UTF-16 – lag spec-filer med Write-verktøyet eller Python. Sett stier i anførselstegn (mellomrom, æøå).
- Uten `--with pillow` mangler logoen i Excel; uten `--with pypdf` mangler sidetall og metadata i PDF-en.

## Referanser

- `references/spec.md` (skjema og regler) · `scripts/eksempler/` (fiktive: bankavstemming, kontoutskrift_reskontro, notat_2740, kontrollrapport, regnskapsrapport).
- `scripts/rapport.py`, `scripts/sjekk.py`, `scripts/silfer/` (tema, tekst, filer, spec, modell, excel, html, pdf, stil).
- Brukes av `bankavstemming` og `regnskapsrapport` (`scripts/lag_spec.py`) og `lonnsavstemming` (`silfer.stil`, kompat-skall som ikke skal endres).
- Utviklerverktøy: `scripts/test_stil_kompat.py`, `scripts/sammenlign_stil.py` (regresjon ved endringer i stilen).
