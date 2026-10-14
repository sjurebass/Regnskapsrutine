"""Silfer-rapport: én spec.json → Silfer-Excel (.xlsx), -PDF (.pdf via Edge/Chrome) eller -HTML.

    from silfer import bygg
    bygg("spec.json", "ut/Rapport 2026-09 Eksempel AS.xlsx")

Tunge moduler (openpyxl, pypdf) importeres først når de trengs, slik at `silfer.stil` og `silfer.tekst`
kan brukes med bare de pakkene de selv krever.
"""

from __future__ import annotations

from pathlib import Path

from .filer import filnavn, lag_mappe, os_sti
from .tekst import clean_tekst, dato_no, esc, hel, kr, redact

__all__ = ["bygg", "filnavn", "clean_tekst", "redact", "kr", "hel", "dato_no", "esc", "FORMATER"]

FORMATER = ("xlsx", "pdf", "html")


def bygg(spec, ut, *, format: str | None = None, behold_html: bool = False) -> Path:
    """Bygger én fil. `spec` er en sti, et dict eller en allerede validert spec. Formatet tas fra endelsen på `ut`."""
    from .spec import last, valider

    s = spec if isinstance(spec, dict) and spec.get("_validert") else valider(last(spec))
    ut = Path(ut)
    fmt = (format or ut.suffix.lstrip(".")).lower()
    if fmt not in FORMATER:
        raise ValueError(f"Ukjent format «{fmt}» – bruk xlsx, pdf eller html.")
    lag_mappe(ut.parent)
    if fmt == "xlsx":
        from .excel import bygg_excel
        return bygg_excel(s, ut)
    if fmt == "pdf":
        from .pdf import bygg_pdf
        return bygg_pdf(s, ut, behold_html=behold_html)
    from .html import render
    with open(os_sti(ut), "w", encoding="utf-8") as f:
        f.write(render(s))
    return ut
