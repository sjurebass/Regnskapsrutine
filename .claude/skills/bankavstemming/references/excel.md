# Excel med åpne bankposter til kunden

Steg 3 i `SKILL.md`. For klienter med noe under «Fra kunden» har `npm run -s bankavstemming` skrevet `<mappe>/<Klient>.data.json`
(postene som `raw`, som skriptet renser). Rett den ved behov (Write, UTF-8). `--excel` i steg 1 kjører `lag_spec.py` for alle;
`sjekk.py` kjøres likevel per fil.

## Formatet

```json
{ "selskap": "<Klient AS>", "orgnr": "<org.nr.>", "aar": "2026", "periode": "Januar–September 2026", "kontoer": [
    { "nummer": "1920", "navn": "Driftskonto", "maaneder": [ { "maaned": "September", "poster": [
        { "dato": "2026-09-03", "tekst": "<banktekst>", "belop": -347.08, "kilde": "Bankside" } ] } ] },
    { "nummer": "1931", "navn": "Kort", "merknad": "Ingen bankfeed – send kontoutskrift for januar–juli 2026.", "maaneder": [] } ] }
```

## Kommandoer

```
uv run --with openpyxl --with pillow --with pypdf python .claude/skills/bankavstemming/scripts/lag_spec.py "<mappe>/<Klient>.data.json" --mappe <mappe> [--format xlsx,pdf]
uv run --with openpyxl --with pypdf python .claude/skills/silfer-rapport/scripts/sjekk.py "<mappe>/Bankavstemming åpne poster ÅÅÅÅ-MM <Klient>.xlsx"
```

## Regler

- Filnavnet følger standarden: `Bankavstemming åpne poster ÅÅÅÅ-MM <Klient>.xlsx` (siste måned i perioden). `--format xlsx,pdf` gir samme liste som PDF.
- Bare poster som venter på kunden (kategori 2, «Fra kunden» i steg 2) tas med. Kategori og alder står i chat-tabellen og Tally-kommentaren, ikke i kundens fil.
- Skriptet fjerner «Fylt på» og gebyrer, renser bankteksten (kortnummer, «VISA VARE», kurs, referanser) og legger utenlandsk beløp bak.
  Gi `"tekst"` i stedet for `"raw"` hvis teksten ikke skal renses. Kontoer uten poster tas med som tom liste og vises med 0.
- Faner: «Sammendrag» (antall og sum per konto, merknad) og «Åpne poster» (filtrerbar; Dokumentasjon og Status er tomme for kunden).
- Skriptet skriver antall og sum per konto; de skal stemme med steg 2. `sjekk.py` skal være grønn før filen lagres.
