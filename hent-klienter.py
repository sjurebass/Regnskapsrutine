"""Slår opp klientene i Tripletex og oppdaterer klienter.json.

    uv run --system-certs python hent-klienter.py

Matcher Tripletex-selskapene mot mappene som allerede ligger her, og beholder
«aktiv»-valget fra forrige kjøring. Klienter som ikke matcher noen mappe blir
lagt inn med aktiv=false, så ingenting kjøres før du har bestemt deg.
"""

from __future__ import annotations

import difflib
import json
import os
import sys

from tools import config
from tools.tripletex import TripletexFeil, fra_miljo


def normaliser(navn: str) -> str:
    base = navn.split("(")[0]
    return "".join(c for c in base.lower() if c.isalnum())


def main() -> int:
    config.last_env()
    try:
        api = fra_miljo("0")
    except TripletexFeil as e:
        print(e)
        return 1
    try:
        selskaper = api.liste(
            "/company/>withLoginAccess",
            fields="id,name,organizationNumber,customerCompanyId,endDate",
        )
    except TripletexFeil as e:
        print(f"Kom ikke til klientlisten: {e}")
        print("Sjekk tokens i .env, og at employee token er laget i regnskapsførerselskapet.")
        return 1

    mapper = config.klientmapper()
    mappe_indeks = {normaliser(m): m for m in mapper}

    tidligere: dict[str, dict] = {}
    if os.path.exists(config.KLIENTFIL):
        with open(config.KLIENTFIL, encoding="utf-8") as f:
            for rad in json.load(f).get("klienter", []):
                tidligere[normaliser(rad["navn"])] = rad

    rader = []
    brukte_mapper = set()
    for s in selskaper:
        navn = s.get("name") or ""
        nokkel = normaliser(navn)
        mappe = mappe_indeks.get(nokkel)
        if not mappe:
            nær = difflib.get_close_matches(nokkel, list(mappe_indeks), n=1, cutoff=0.85)
            mappe = mappe_indeks[nær[0]] if nær else None
        if mappe:
            brukte_mapper.add(mappe)
        forrige = tidligere.get(nokkel, {})
        rader.append(
            {
                "navn": mappe or navn,
                "mappe": mappe or navn,
                "company_id": str(s.get("id")),
                "orgnr": s.get("organizationNumber"),
                "aktiv": bool(forrige.get("aktiv", False)),
                "tripletex_navn": navn,
            }
        )

    # mapper uten treff i Tripletex tas med, så de ikke forsvinner i stillhet
    for mappe in mapper:
        if mappe in brukte_mapper:
            continue
        forrige = tidligere.get(normaliser(mappe), {})
        rader.append(
            {
                "navn": mappe,
                "mappe": mappe,
                "company_id": forrige.get("company_id") or config.mappenavn_til_nummer(mappe),
                "orgnr": forrige.get("orgnr"),
                "aktiv": bool(forrige.get("aktiv", False)),
                "tripletex_navn": None,
                "merknad": "fant ingen match i Tripletex – sjekk company_id manuelt",
            }
        )

    rader.sort(key=lambda r: r["navn"].lower())
    config.skriv_klienter(
        rader,
        "aktiv=true betyr at klienten er med i den løpende månedskontrollen.",
    )
    print(f"Skrev {config.KLIENTFIL} med {len(rader)} klienter.\n")
    for r in rader:
        merke = "aktiv" if r["aktiv"] else "  -  "
        advarsel = "  ← " + r["merknad"] if r.get("merknad") else ""
        print(f"[{merke}] {r['navn']:<40} company_id={r['company_id'] or '?':<8}{advarsel}")
    print("\nSett aktiv=true på de klientene rutinen skal gjelde for.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
