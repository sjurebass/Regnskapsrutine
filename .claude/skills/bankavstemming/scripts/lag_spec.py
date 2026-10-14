"""Bankavstemming: data.json → spec → Silfer-Excel (og PDF) med åpne bankposter til kunden.

    uv run --with openpyxl --with pillow --with pypdf python .claude/skills/bankavstemming/scripts/lag_spec.py \\
        <data.json> --mappe <scratch> [--format xlsx,pdf] [--spec-ut <spec.json>]

data.json har samme form som før (SKILL.md steg 5): selskap, orgnr, aar, periode, dato, kontoer[].maaneder[].poster[].
Poster kan være strukturerte ({dato, tekst, belop, kilde}) eller råstrenger ({raw, kilde}); råstrenger renses.
Bankreglene ligger her: bare bankside-poster (med mindre "inkluder_tripletex_side": true), «Fylt på» og gebyr utelates.
Stil, logo og filformat kommer fra silfer-rapport. Skriver antall og sum per konto, så steg 3 kan avstemmes uten å åpne filen.
"""

from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "silfer-rapport" / "scripts"))
from silfer import bygg, filnavn  # noqa: E402
from silfer.filer import lag_mappe, os_sti  # noqa: E402
from silfer.spec import SpecFeil, valider  # noqa: E402
from silfer.tekst import clean_tekst, kr, parse_raw  # noqa: E402

MND = ["Januar", "Februar", "Mars", "April", "Mai", "Juni", "Juli", "August",
       "September", "Oktober", "November", "Desember"]

# Poster som IKKE krever dokumentasjon fra kunden – filtreres bort fra rapporten.
# «Fylt på» = interne kortpåfyll fra driftskontoen; gebyr = bank-/kortgebyr.
IRRELEVANT_MØNSTRE = ["fylt på", "fyll på", "gebyr"]


def er_irrelevant(tekst):
    t = (tekst or "").lower()
    return any(m in t for m in IRRELEVANT_MØNSTRE)


def normalize_kilde(k):
    if not k:
        return ""
    s = str(k).strip().lower()
    if s.startswith("bank") or s == "right" or "kontoutskrift" in s:
        return "Bankside"
    if s.startswith("tripletex") or s == "left" or "bokf" in s:
        return "Tripletex-side"
    return str(k)


def norm_post(p):
    """Return dict with dato/tekst/belop/kilde, accepting structured or raw."""
    kilde = normalize_kilde(p.get("kilde", ""))
    if "raw" in p and "belop" not in p:
        parsed = parse_raw(p["raw"])
        if not parsed:
            raise ValueError(f"Kunne ikke tolke rad: {p['raw']!r}")
        dato, belop, tekst = parsed
        # rens råstrengen til lesbar tekst; behold original for filtrering
        return {"dato": dato, "tekst": clean_tekst(tekst), "_match": tekst,
                "belop": round(belop, 2), "kilde": kilde}
    return {"dato": p["dato"], "tekst": p["tekst"], "_match": p["tekst"],
            "belop": round(float(p["belop"]), 2), "kilde": kilde}


def month_sort_key(name):
    n = name.strip().split("–")[0].split("-")[0].strip().capitalize()
    return MND.index(n) if n in MND else 99


def _konto(nr: str):
    return int(nr) if nr.isdigit() else nr


def lag_spec(data: dict) -> tuple[dict, dict]:
    """data.json → (spec, oppsummering)."""
    selskap = data.get("selskap", "Ukjent klient")
    aar = str(data.get("aar", ""))
    # Standard: ta KUN med bankside-poster (i bank, mangler bilag). Tripletex-side (bokført, ikke sett i bank – ofte
    # timing) tas bare med når data.json sier "inkluder_tripletex_side": true.
    kun_bankside = not data.get("inkluder_tripletex_side", False)
    kontoer, rader, utelatt, utelatt_tx, siste_mnd = [], [], 0, 0, -1
    for k in data["kontoer"]:
        nummer = str(k["nummer"])
        maaneder = sorted(k.get("maaneder", []), key=lambda m: month_sort_key(m["maaned"]))
        n, s = 0, 0.0
        for m in maaneder:
            siste_mnd = max(siste_mnd, month_sort_key(m["maaned"]) if month_sort_key(m["maaned"]) < 99 else -1)
            for p in m.get("poster", []):
                np_ = norm_post(p)
                if kun_bankside and np_["kilde"] == "Tripletex-side":
                    utelatt_tx += 1
                    continue
                if er_irrelevant(np_.get("_match", np_["tekst"])):
                    utelatt += 1
                    continue
                rader.append({"konto": _konto(nummer), "kontonavn": k.get("navn", ""), "maaned": m["maaned"],
                              "dato": np_["dato"], "tekst": np_["tekst"], "belop": np_["belop"], "kilde": np_["kilde"]})
                n += 1
                s += np_["belop"]
        kontoer.append({"nummer": nummer, "navn": k.get("navn", ""), "antall": n, "sum": round(s, 2),
                        "merknad": k.get("merknad", "") or ("Ingen åpne poster" if n == 0 else "")})

    tx_note = ("Kun bankside-poster er tatt med (i bank, mangler bilag). " if kun_bankside
               else "Både bank- og Tripletex-side er tatt med. ")
    note = ("Kilde: Automatisk bankavstemming i Tripletex. Åpne (uavstemte) poster "
            + (data.get("periode", "") or aar) + ". " + tx_note
            + "Konto for skattetrekk (typ. 1950) er holdt utenfor. «Fylt på» (kortpåfyll) og bank-/kortgebyr er "
              "utelatt – disse krever ingen dokumentasjon.")
    periode = f"{aar}-{siste_mnd + 1:02d}" if aar and siste_mnd >= 0 else (aar or datetime.date.today().strftime("%Y-%m"))
    spec = {
        "versjon": 1,
        "dokument": {"hva": "Bankavstemming åpne poster", "tittel": f"Åpne poster i bankavstemming {aar}".strip(),
                     "klient": selskap, "orgnr": (data.get("orgnr") or "").strip() or None, "periode": periode,
                     "periode_tekst": data.get("periode") or aar or None,
                     "utarbeidet": (data.get("dato") or "").strip() or None,
                     "utarbeidet_av": data.get("utarbeidet_av")},
        "seksjoner": [
            {"id": "sammendrag", "ark": "Sammendrag", "overskrift": "Sammendrag – åpne poster per konto",
             "sammendrag": {
                 "av": "poster", "gruppe": "konto",
                 "kolonner": [{"id": "konto", "tekst": "Konto", "type": "heltall", "bredde": 8},
                              {"id": "navn", "tekst": "Kontonavn", "type": "tekst", "bredde": 24},
                              {"id": "antall", "tekst": "Åpne poster", "type": "antall", "tell": "tekst", "bredde": 13},
                              {"id": "sum", "tekst": "Sum beløp (kr)", "type": "belop", "summer": "belop", "bredde": 15},
                              {"id": "merknad", "tekst": "Merknad", "type": "tekst", "bredde": 52}],
                 "rader": [{"konto": _konto(k["nummer"]), "navn": k["navn"], "merknad": k["merknad"]} for k in kontoer],
                 "sum": {"etikett": "Totalt", "kolonner": ["antall", "sum"]}, "zebra": True},
             "merknad": note},
            {"id": "poster", "ark": "Åpne poster", "sideskift": True,
             "overskrift": f"Åpne poster i bankavstemming {aar}".strip(),
             "tabell": {
                 "kolonner": [{"id": "konto", "tekst": "Konto", "type": "heltall", "bredde": 8},
                              {"id": "kontonavn", "tekst": "Kontonavn", "type": "tekst", "bredde": 24},
                              {"id": "maaned", "tekst": "Måned", "type": "tekst", "bredde": 10},
                              {"id": "dato", "tekst": "Dato", "type": "dato", "bredde": 12},
                              {"id": "tekst", "tekst": "Tekst", "type": "tekst", "bredde": 34},
                              {"id": "belop", "tekst": "Beløp (kr)", "type": "belop", "bredde": 13},
                              {"id": "kilde", "tekst": "Kilde", "type": "tekst", "bredde": 14},
                              {"id": "dokumentasjon", "tekst": "Dokumentasjon", "type": "tekst", "bredde": 26, "vis": "excel"},
                              {"id": "status", "tekst": "Status", "type": "status", "bredde": 14, "vis": "excel"}],
                 "rader": rader,
                 "sum": {"etikett": "Sum åpne poster", "kolonner": ["belop"], "tell": "tekst"},
                 "filter": True, "frys": True, "zebra": True}},
        ],
    }
    spec["dokument"] = {k: v for k, v in spec["dokument"].items() if v is not None}
    return spec, {"kontoer": kontoer, "utelatt": utelatt, "utelatt_tx": utelatt_tx, "antall": len(rader)}


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="Bankavstemming: data.json → Silfer-Excel/-PDF med åpne poster.")
    ap.add_argument("data", help="data.json (se SKILL.md steg 5)")
    ap.add_argument("--mappe", required=True, help="mappen filene skrives til (scratch)")
    ap.add_argument("--format", default="xlsx", help="xlsx, pdf eller xlsx,pdf (standard xlsx)")
    ap.add_argument("--spec-ut", help="skriv også specen til denne filen")
    a = ap.parse_args(argv)

    with open(os_sti(a.data), encoding="utf-8-sig") as f:
        data = json.load(f)
    try:
        spec, opp = lag_spec(data)
        spec = valider(spec)
    except (SpecFeil, ValueError, KeyError) as e:
        print(f"Feil i data.json: {e}")
        return 1
    if a.spec_ut:
        with open(os_sti(a.spec_ut), "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in spec.items() if not k.startswith("_")}, f, ensure_ascii=False, indent=1,
                      default=str)
    lag_mappe(a.mappe)
    dok = spec["dokument"]
    kode = 0
    for fmt in [x.strip().lower() for x in a.format.split(",") if x.strip()]:
        ut = Path(a.mappe) / filnavn(dok["hva"], dok["periode"], dok["klient"], fmt)
        try:
            bygg(spec, ut)
            print(f"Laget {ut}")
        except Exception as e:  # noqa: BLE001
            print(f"Ikke laget ({fmt}): {e}")
            kode = 2 if "Edge" in str(e) else 1
    for k in opp["kontoer"]:
        print(f"  {k['nummer']} {k['navn']}: {k['antall']} poster, sum {kr(k['sum'])} kr")
    print(f"  Totalt {opp['antall']} poster · {opp['utelatt']} utelatt (Fylt på / gebyr) · "
          f"{opp['utelatt_tx']} Tripletex-side utelatt")
    if spec.get("_redigert"):
        print(f"  Personvern: {spec['_redigert']} felt maskert som [skjult].")
    return kode


if __name__ == "__main__":
    sys.exit(main())
