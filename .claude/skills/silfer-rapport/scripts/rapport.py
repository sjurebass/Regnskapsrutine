"""Silfer-rapport: spec.json → Excel og/eller PDF i Silfer-stil.

    uv run --with openpyxl --with pillow --with pypdf python .claude/skills/silfer-rapport/scripts/rapport.py \\
        <spec.json> --mappe <mappe> [--format xlsx,pdf] [--behold-html] [--sjekk]

Filnavnet følger standarden «<Hva> <periode> <Klient>.<endelse>» (docs/dokumentlagring.md).
Exit 0 = ferdig, 1 = feil i spec eller bygging (eller sjekk), 2 = ingen nettleser for PDF (HTML er skrevet i stedet).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from silfer import FORMATER, bygg, filnavn  # noqa: E402
from silfer.filer import lag_mappe  # noqa: E402
from silfer.spec import SpecFeil, last, valider  # noqa: E402


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Bygger Silfer-Excel/-PDF fra spec.json.")
    ap.add_argument("spec", help="spec.json (UTF-8)")
    ap.add_argument("--mappe", required=True, help="mappen filene skrives til (scratch)")
    ap.add_argument("--format", default="xlsx,pdf", help="kommaseparert: xlsx, pdf, html (standard xlsx,pdf)")
    ap.add_argument("--behold-html", action="store_true", help="skriv også .html ved siden av PDF-en (forhåndsvisning)")
    ap.add_argument("--sjekk", action="store_true", help="kjør sjekk.py på filene etterpå")
    a = ap.parse_args(argv)

    formater = [f.strip().lower().lstrip(".") for f in a.format.split(",") if f.strip()]
    ukjent = [f for f in formater if f not in FORMATER]
    if ukjent or not formater:
        print(f"Ukjent format: {', '.join(ukjent) or '(tomt)'} – bruk xlsx, pdf og/eller html.")
        return 1
    try:
        spec = valider(last(a.spec))
    except SpecFeil as e:
        print(f"Feil i spec: {e}")
        return 1

    dok = spec["dokument"]
    mappe = Path(a.mappe)
    lag_mappe(mappe)
    laget, kode = [], 0
    for fmt in formater:
        ut = mappe / filnavn(dok["hva"], dok["periode"], dok["klient"], fmt)
        try:
            bygg(spec, ut, behold_html=a.behold_html)
            laget.append(ut)
            print(f"Laget {ut}")
            if fmt == "pdf" and a.behold_html:
                print(f"Laget {ut.with_suffix('.html')}")
        except PermissionError:
            print(f"Kunne ikke skrive {ut} – er filen åpen i Excel eller en PDF-leser? Lukk den og kjør på nytt.")
            kode = 1
        except Exception as e:  # noqa: BLE001
            from silfer.pdf import NettleserMangler
            if isinstance(e, NettleserMangler):
                print(f"PDF ikke laget – fant verken Edge eller Chrome. Åpne HTML-filen i nettleseren og skriv ut til PDF: {e.html_fil}")
                kode = max(kode, 2)
            else:
                raise
    if spec.get("_redigert"):
        print(f"Personvern: {spec['_redigert']} felt maskert som [skjult].")
    if a.sjekk and laget:
        import sjekk
        kode = max(kode, sjekk.main([str(p) for p in laget if p.suffix.lower() in (".xlsx", ".pdf")]))
    return kode


if __name__ == "__main__":
    sys.exit(main())
