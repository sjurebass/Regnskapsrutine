"""Utviklerverktøy: viser at `silfer.stil` gir samme Excel som lønnsavstemmingens gamle stil.py.

    git show <rev>:<sti>/stil.py > <scratch>/gammel/stil.py
    uv run --with "openpyxl==3.1.5" --with pillow python .claude/skills/silfer-rapport/scripts/test_stil_kompat.py <scratch>/gammel

Bygger samme arbeidsbok (to ark, alle seks hjelperne med variantene lønnsrapporten bruker) med begge modulene og
sammenligner alle deler i zip-filen unntatt docProps/*. Ingen kundedata. Exit 0 = identisk.
"""

from __future__ import annotations

import datetime as dt
import importlib.util
import os
import sys
import tempfile
from pathlib import Path

HER = Path(__file__).resolve().parent
sys.path.insert(0, str(HER))

from openpyxl import Workbook  # noqa: E402

import sammenlign_stil  # noqa: E402
from silfer import stil as ny  # noqa: E402


def last_gammel(sti: Path):
    fil = sti if sti.suffix == ".py" else (sti / "stil.py" if (sti / "stil.py").exists() else sti / "scripts" / "stil.py")
    spec = importlib.util.spec_from_file_location("gammel_stil", fil)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    if not os.path.exists(mod.LOGO):
        print(f"merk: gammel LOGO ({mod.LOGO}) finnes ikke – bruker silfer-rapport/assets/silfer_logo.png (samme fil)")
        mod.LOGO = ny.LOGO
    return mod, fil


def bygg(m, ut: Path) -> None:
    """Samme kall som lonnsavstemming_a07.py gjør (Avstemming- og Detaljer-arket i miniatyr)."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Avstemming"
    m.topp(ws, "Lønnsavstemming termin 4 2026", "Eksempel AS   |   Org.nr. 123 456 789   |   Termin 4")
    m.bredder(ws, {"A": 34, "B": 52, "C": 16, "E": 13, "F": 12, "G": 46})
    m.tabellhode(ws, 7, [("Kontroll", "l"), ("Beregning", "l"), ("A07 / beregnet", "r"), ("Regnskap", "r"),
                         ("Avvik", "r"), ("Status", "l"), ("Kommentar", "l")])
    ws.freeze_panes = "A8"
    rad = 8
    m.seksjon(ws, rad, "Forskuddstrekk")
    rad += 1
    for navn, a, b, nf, ellers in (("Trekk", 61240.0, 61240.0, m.KRONER, "AVVIK"),
                                   ("AGA-grunnlag", 412300.0, 413900.0, m.KRONER, "FORKLART"),
                                   ("Antall", 7, 7, m.ANTALL, "AVVIK")):
        m.celle(ws, rad, 1, navn, fet=True)
        m.celle(ws, rad, 2, "Beregning", farge=m.GRA)
        m.celle(ws, rad, 3, a, nf=nf)
        m.celle(ws, rad, 4, b, nf=nf)
        m.celle(ws, rad, 5, f"=C{rad}-D{rad}", nf=nf)
        c = m.celle(ws, rad, 6, f'=IF(ABS(E{rad})<=1,"OK","{ellers}")', fet=True)
        from openpyxl.styles import Alignment
        c.alignment = Alignment(vertical="center", horizontal="center")
        m.celle(ws, rad, 7, "Kommentar")
        rad += 1
    m.statusregler(ws, "F9:F11")
    rad += 1
    m.celle(ws, rad, 1, "Antall avvik", fet=True)
    m.celle(ws, rad, 6, '=COUNTIF(F9:F11,"AVVIK")', fet=True, nf=m.ANTALL).alignment = None
    rad += 2
    m.seksjon(ws, rad, "Merknader")
    rad += 1
    m.celle(ws, rad, 1, "1.", fet=True)
    m.celle(ws, rad, 2, "Merknad", ramme=False, str_=8, just="center", farge=m.MORK)
    m.celle(ws, rad, 3, None)
    m.celle(ws, rad, 4, dt.date(2026, 9, 15), farge=m.SVART)

    ws2 = wb.create_sheet("Detaljer")
    m.topp(ws2, "Detaljer – innsendinger, betalinger, kilder", "Eksempel AS")
    m.bredder(ws2, {"A": 14, "C": 18, "E": 12, "F": 16, "H": 40})
    m.seksjon(ws2, 7, "A-meldinger")
    m.tabellhode(ws2, 8, [("Måned", "l"), ("MeldingsId", "l"), ("Antall", "r"), ("AGA", "r")])
    m.celle(ws2, 9, 1, "2026-07")
    m.celle(ws2, 9, 2, "ABC123")
    m.celle(ws2, 9, 3, 7, nf=m.ANTALL)
    m.celle(ws2, 9, 4, 29067.15, nf=m.KRONER)
    m.statusregler(ws2, "B9:B9")
    wb.save(ut)


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    argv = argv if argv is not None else sys.argv[1:]
    if not argv:
        print(__doc__)
        return 1
    gammel, fil = last_gammel(Path(argv[0]))
    print(f"gammel: {fil}")
    feil = 0
    for navn in [n for n in dir(gammel) if n.isupper() and n != "LOGO"]:
        if not hasattr(ny, navn) or getattr(ny, navn) != getattr(gammel, navn):
            print(f"  konstant {navn}: ulik eller mangler")
            feil += 1
    for navn in ("topp", "bredder", "tabellhode", "seksjon", "celle", "statusregler"):
        if not callable(getattr(ny, navn, None)):
            print(f"  funksjon {navn} mangler")
            feil += 1
    with tempfile.TemporaryDirectory(prefix="silfer-kompat-") as t:
        a, b = Path(t) / "gammel.xlsx", Path(t) / "ny.xlsx"
        bygg(gammel, a)
        bygg(ny, b)
        forskjeller = sammenlign_stil.zip_deler(str(a), str(b)) + sammenlign_stil.celler(
            str(a), str(b), bare_verdier=False, fra_rad=1)
    for f in forskjeller:
        print("  " + f)
    feil += len(forskjeller)
    print("identisk: konstanter, sheet-XML, styles.xml, tegninger og bilder (alle deler unntatt docProps)" if not feil
          else f"ULIKT: {feil} forskjell(er)")
    return 0 if not feil else 1


if __name__ == "__main__":
    sys.exit(main())
