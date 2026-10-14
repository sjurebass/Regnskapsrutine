"""Filnavn etter standarden i docs/dokumentlagring.md: «<Hva> <periode> <Klient>.<endelse>»."""

from __future__ import annotations

import re

_ULOVLIG = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
MAKS = 120


def filnavn(hva: str, periode: str, klient: str, ext: str) -> str:
    """'Bankavstemming åpne poster', '2026-09', 'Eksempel AS', 'xlsx' → 'Bankavstemming åpne poster 2026-09 Eksempel AS.xlsx'."""
    deler = [str(x).strip() for x in (hva, periode, klient) if x is not None and str(x).strip()]
    navn = " ".join(deler)
    navn = _ULOVLIG.sub("-", navn)
    navn = re.sub(r"\s+", " ", navn).strip(" .")
    if len(navn) > MAKS:
        navn = navn[:MAKS].rstrip(" .")
    return f"{navn}.{ext.lstrip('.')}"


_LANG = "\\\\?\\"          # \\?\  (Windows: utvidet sti uten 260-tegnsgrensen)


def os_sti(sti) -> str:
    """Sti klar for filsystemet. Windows uten «lange stier» stopper ved 260 tegn, og Claudes scratch-mapper er
    ofte over 240 tegn – da brukes den utvidede formen (gjelder open, mkdir, replace og kopiering)."""
    import os

    s = str(sti)
    if s.startswith(_LANG):
        return s
    s = os.path.abspath(s)
    if os.name == "nt" and len(s) >= 240:
        s = _LANG + "UNC\\" + s[2:] if s.startswith("\\\\") else _LANG + s
    return s


def lag_mappe(sti) -> None:
    import os

    os.makedirs(os_sti(sti), exist_ok=True)
