"""Skriver historikk til logg.md i kundemappen og status/historikk.md."""

from __future__ import annotations

import os
from datetime import date

from .modeller import GUL, INFO, ROD, Resultat

HODE = "| Dato | Modus | År | Fil |\n|---|---|---|---|\n"


def _sikre_logg(sti: str, tittel: str) -> None:
    if os.path.exists(sti):
        return
    with open(sti, "w", encoding="utf-8") as f:
        f.write(f"# {tittel}\n\n{HODE}")


def loggfor(resultat: Resultat, rapportsti: str) -> None:
    sti = os.path.join(resultat.klient.mappe, "logg.md")
    _sikre_logg(sti, f"{resultat.klient.navn} – avstemminger")
    apne = resultat.aapne_funn
    rod = sum(1 for f in apne if f.alvorlighet == ROD)
    gul = sum(1 for f in apne if f.alvorlighet == GUL)
    kjent = sum(1 for f in resultat.funn if f.kjent)
    if resultat.feil:
        oppsummering = f"Månedskontroll {resultat.periode} – kjøringsfeil i {len(resultat.feil)} kontroller"
    elif rod or gul:
        oppsummering = (
            f"Månedskontroll {resultat.periode} – {rod} røde, {gul} gule"
            + (f", {kjent} kvittert" if kjent else "")
        )
    else:
        oppsummering = f"Månedskontroll {resultat.periode} – ingen avvik"
    relativ = os.path.relpath(rapportsti, resultat.klient.mappe).replace(os.sep, "/")
    linje = (
        f"| {date.today().strftime('%d.%m.%Y')} | {oppsummering} | "
        f"{resultat.periode.aar} | {relativ} |\n"
    )
    with open(sti, "a", encoding="utf-8") as f:
        f.write(linje)


def loggfor_kjoring(resultater: list[Resultat], periode, statussti: str, mappe: str) -> None:
    sti = os.path.join(mappe, "historikk.md")
    if not os.path.exists(sti):
        with open(sti, "w", encoding="utf-8") as f:
            f.write("# Kjøringshistorikk – månedskontroll\n\n")
            f.write("| Dato | Periode | Klienter | Rød | Gul | Rapport |\n|---|---|---|---|---|---|\n")
    rod = sum(1 for r in resultater for f in r.aapne_funn if f.alvorlighet == ROD)
    gul = sum(1 for r in resultater for f in r.aapne_funn if f.alvorlighet == GUL)
    with open(sti, "a", encoding="utf-8") as f:
        f.write(
            f"| {date.today().strftime('%d.%m.%Y')} | {periode} | {len(resultater)} | "
            f"{rod} | {gul} | {os.path.basename(statussti)} |\n"
        )
