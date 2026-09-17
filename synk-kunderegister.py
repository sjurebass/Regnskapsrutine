"""Synkroniserer klienter.json mot kunderegisteret («Kundeoversikt*.xlsx» på skrivebordet).

    uv run --system-certs python synk-kunderegister.py [--fil <sti>]

Leser kunde, system, regnskapskontor, bankforbindelse og bankkontoene fra
kunderegisteret, og oppdaterer klienter.json uten å røre «aktiv»-valgene.
Bankkontoene legges inn som notat i klientprofil.md for de aktive klientene,
så B3 (bankkonti uten avstemming) kan leses mot noe.

Kjøres på nytt når kunderegisteret endres.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time

from tools import config

STOTTET_SYSTEM = "Tripletex"


def finn_register() -> str | None:
    """Nyeste «Kundeoversikt*.xlsx» på skrivebordet. Overstyres med --fil."""
    import glob

    treff = glob.glob(os.path.join(os.path.expanduser("~"), "Desktop", "Kundeoversikt*.xlsx"))
    treff = [t for t in treff if not os.path.basename(t).startswith("~$")]
    return max(treff, key=os.path.getmtime) if treff else None


def normaliser(navn: str) -> str:
    base = str(navn).split("(")[0]
    return "".join(c for c in base.lower() if c.isalnum())


def les_register(sti: str) -> list[dict]:
    import openpyxl

    wb = openpyxl.load_workbook(sti, data_only=True)
    ws = wb["Kundeoversikt"]
    kunder: list[dict] = []
    naavaerende: dict | None = None
    i_bankblokk = False
    for rad in ws.iter_rows(values_only=True):
        if not rad or rad[0] is None:
            continue
        forste = str(rad[0]).strip()
        if forste in ("Kundeoversikt", "Kunde") or forste.startswith("Klikk"):
            continue
        if forste.startswith("Bankkontoer"):
            i_bankblokk = True
            continue
        if forste.startswith("Konto "):
            if naavaerende is None or not i_bankblokk:
                continue
            felt = [str(x).strip() for x in rad[1:7] if x is not None and str(x).strip()]
            if felt:
                naavaerende["bankkontoer"].append(" – ".join(felt))
            continue
        i_bankblokk = False
        naavaerende = {
            "navn": forste,
            "system": (str(rad[1]).strip() if len(rad) > 1 and rad[1] else ""),
            "regnskapskontor": (str(rad[2]).strip() if len(rad) > 2 and rad[2] else ""),
            "orgnr": (str(rad[3]).strip() if len(rad) > 3 and rad[3] else ""),
            "banktilgang": (str(rad[4]).strip() if len(rad) > 4 and rad[4] else ""),
            "bankforbindelse": (str(rad[6]).strip() if len(rad) > 6 and rad[6] else ""),
            "status": (str(rad[11]).strip() if len(rad) > 11 and rad[11] else ""),
            "bankkontoer": [],
        }
        kunder.append(naavaerende)
    return kunder


MAA_BYTTES: list[str] = []


def skriv_trygt(sti: str, tekst: str) -> None:
    """Windows låser filer sporadisk under virusskanning – skriv ved siden av og bytt.

    Går det fortsatt ikke, blir «.new»-filen liggende og navnet rapportert til
    slutt, så ingenting går tapt.
    """
    midlertidig = sti + ".new"
    with open(midlertidig, "w", encoding="utf-8") as f:
        f.write(tekst)
    for _ in range(4):
        try:
            os.replace(midlertidig, sti)
            return
        except PermissionError:
            time.sleep(1.0)
    MAA_BYTTES.append(sti)


def oppdater_profilnotat(mappe: str, kunde: dict) -> bool:
    sti = os.path.join(mappe, "klientprofil.md")
    if not os.path.exists(sti):
        return False
    with open(sti, encoding="utf-8") as f:
        tekst = f.read()
    merke = "<!-- kunderegister -->"
    linjer = [
        merke,
        f"Fra kunderegisteret: system {kunde['system'] or '?'}, "
        f"regnskapskontor {kunde['regnskapskontor'] or '?'}, "
        f"bankforbindelse {kunde['bankforbindelse'] or '?'}, "
        f"banktilgang {kunde['banktilgang'] or '?'}.",
    ]
    if kunde["bankkontoer"]:
        linjer.append("")
        linjer.append("Bankkontoer:")
        linjer.extend(f"- {b}" for b in kunde["bankkontoer"])
    if kunde["banktilgang"].lower() == "nei":
        linjer.append("")
        linjer.append(
            "Uten banktilgang vil B1/B3 gi mange treff. Vurder å senke støyen i "
            "`deaktiverte_kontroller` til tilgangen er på plass."
        )
    blokk = "\n".join(linjer)
    if merke in tekst:
        start = tekst.index(merke)
        tekst = tekst[:start].rstrip() + "\n\n" + blokk + "\n"
    else:
        tekst = tekst.rstrip() + "\n\n" + blokk + "\n"
    skriv_trygt(sti, tekst)
    return True


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--fil", default=None, help="Sti til kunderegisteret (xlsx)")
    p.add_argument(
        "--aktiver",
        help="Kommaliste med navnebiter som skal settes aktiv, f.eks. «Eksempel,Annen Kunde». "
        "Klienter som ikke matcher blir satt inaktive.",
    )
    args = p.parse_args()
    fil = args.fil or finn_register()
    if not fil or not os.path.exists(fil):
        print("Fant ingen «Kundeoversikt*.xlsx» på skrivebordet. Oppgi den med --fil.")
        return 1

    kunder = les_register(fil)
    print(f"Leste {len(kunder)} kunder fra kunderegisteret\n")

    valgte = (
        [b.strip().lower() for b in args.aktiver.split(",") if b.strip()] if args.aktiver else None
    )

    tidligere: dict[str, dict] = {}
    if os.path.exists(config.KLIENTFIL):
        with open(config.KLIENTFIL, encoding="utf-8") as f:
            for rad in json.load(f).get("klienter", []):
                tidligere[normaliser(rad["navn"])] = rad

    mapper = {normaliser(m): m for m in config.klientmapper()}
    rader = []
    for kunde in kunder:
        nokkel = normaliser(kunde["navn"])
        forrige = tidligere.get(nokkel, {})
        mappe = mapper.get(nokkel) or forrige.get("mappe") or kunde["navn"]
        stottet = kunde["system"] == STOTTET_SYSTEM
        if valgte is None:
            onsket = bool(forrige.get("aktiv", False))
        else:
            onsket = any(bit in kunde["navn"].lower() or bit in mappe.lower() for bit in valgte)
        rad = {
            "navn": mappe,
            "mappe": mappe,
            "system": kunde["system"],
            "regnskapskontor": kunde["regnskapskontor"],
            "company_id": forrige.get("company_id") or config.mappenavn_til_nummer(mappe),
            "aktiv": onsket and stottet,
        }
        if not stottet:
            rad["merknad"] = f"{kunde['system']} – månedskontrollen støtter foreløpig bare Tripletex"
        elif not rad["company_id"]:
            rad["merknad"] = "company_id hentes med hent-klienter.py"
        rader.append(rad)

    # klienter som finnes i klienter.json men ikke i registeret
    kjente = {normaliser(r["navn"]) for r in rader}
    for nokkel, forrige in tidligere.items():
        if nokkel not in kjente:
            forrige.setdefault("merknad", "står ikke i kunderegisteret – sjekk om den er avsluttet")
            rader.append(forrige)

    rader.sort(key=lambda r: (r.get("system") != STOTTET_SYSTEM, r["navn"].lower()))
    skriv_trygt(
        config.KLIENTFIL,
        json.dumps(
            {
                "kommentar": (
                    "Synkronisert mot kunderegisteret. aktiv=true betyr at "
                    "klienten er med i den løpende månedskontrollen. Bare Tripletex-klienter "
                    "kan kjøres."
                ),
                "klienter": rader,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
    )

    aktive = [r for r in rader if r["aktiv"]]
    for rad in rader:
        merke = "aktiv" if rad["aktiv"] else "  -  "
        print(f"[{merke}] {rad['navn']:<48} {rad.get('system',''):<12} {rad.get('merknad','')}")

    print(f"\n{len(aktive)} aktive av {len(rader)}.")
    register = {normaliser(k["navn"]): k for k in kunder}
    for rad in aktive:
        kunde = register.get(normaliser(rad["navn"]))
        if kunde and oppdater_profilnotat(os.path.join(config.ROT, rad["mappe"]), kunde):
            print(f"  oppdaterte notat i {rad['mappe']}/klientprofil.md")

    if MAA_BYTTES:
        print("\nDisse filene var låst. Innholdet ligger klart som «.new» – bytt dem inn:")
        for sti in MAA_BYTTES:
            print(f"  move /Y \"{sti}.new\" \"{sti}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
