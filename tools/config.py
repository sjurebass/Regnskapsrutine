"""Oppsett: .env, klientliste og stier."""

from __future__ import annotations

import json
import os
import re

from .modeller import Klient

ROT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLIENTFIL = os.path.join(ROT, "klienter.json")
STATUSMAPPE = os.path.join(ROT, "status")


def last_env() -> None:
    """Leser .env i prosjektroten inn i miljøvariablene."""
    sti = os.path.join(ROT, ".env")
    if not os.path.exists(sti):
        return
    with open(sti, encoding="utf-8") as f:
        for linje in f:
            linje = linje.strip()
            if not linje or linje.startswith("#") or "=" not in linje:
                continue
            navn, _, verdi = linje.partition("=")
            os.environ.setdefault(navn.strip(), verdi.strip().strip('"').strip("'"))


def les_klienter(bare_aktive: bool = True) -> list[Klient]:
    if not os.path.exists(KLIENTFIL):
        raise SystemExit(
            f"Fant ikke {KLIENTFIL}. Kjør «uv run python hent-klienter.py» for å lage den."
        )
    with open(KLIENTFIL, encoding="utf-8") as f:
        data = json.load(f)
    ut = []
    for rad in data.get("klienter", []):
        if bare_aktive and not rad.get("aktiv", True):
            continue
        mappe = rad.get("mappe") or rad["navn"]
        ut.append(
            Klient(
                navn=rad["navn"],
                mappe=os.path.join(ROT, mappe),
                company_id=str(rad["company_id"]) if rad.get("company_id") else None,
                aktiv=bool(rad.get("aktiv", True)),
            )
        )
    return ut


def skriv_klienter(klienter: list[dict], kommentar: str = "") -> None:
    with open(KLIENTFIL, "w", encoding="utf-8") as f:
        json.dump(
            {"kommentar": kommentar, "klienter": klienter}, f, ensure_ascii=False, indent=2
        )
        f.write("\n")


def mappenavn_til_nummer(navn: str) -> str | None:
    """«Eksempel AS (123)» -> «123».

    NB: dette er klientnummeret regnskapskontoret ser i klientlisten, IKKE
    selskapets companyId. De to er helt forskjellige tall, og bare companyId
    virker mot API-et. Bruk hent-klienter.py for å få riktig id.
    """
    m = re.search(r"\((\d+)\)\s*$", navn)
    return m.group(1) if m else None


def klientmapper() -> list[str]:
    ut = []
    for navn in sorted(os.listdir(ROT)):
        sti = os.path.join(ROT, navn)
        if os.path.isdir(sti) and not navn.startswith((".", "_")) and navn not in (
            "tools",
            "status",
            "mal",
            "__pycache__",
        ):
            ut.append(navn)
    return ut
