"""Løser en validert spec én gang for begge formatene.

Hver tabell blir en liste med rader (IB, data, sum, UB, kontroll), og hver avledet celle får både den beregnede
verdien (brukes i HTML/PDF og i utskriften fra lag_spec) og en formeloppskrift (brukes av Excel). Slik kan ikke tallene
i Excel og PDF gli fra hverandre.

Formeloppskrifter (tupler, løses til cellereferanser i excel.py):
    ("lopende",)                       forrige saldo + pluss − minus i samme rad
    ("sum", kol) / ("tell", kol)       SUM / COUNTA over datarader
    ("ub_lopende",)                    saldo i siste datarad
    ("lik", kol, skal)                 IF(ABS(kol−skal)<0.005;"OK";"AVVIK")
    ("kontroll_diff",)                 IB + ΣSUM(pluss) − SUM(minus) − UB
    ("kontroll_status", kol)           IF(ABS(kol)<0.005;"OK";"AVVIK")
    ("countif", av, gruppe) / ("sumif", av, gruppe, summer)   over tabellen i seksjonen «av»
    ("avvik", a, b) / ("kstatus", kol, toleranse, ellers) / ("antall_avvik", kol)
    ("pst", a, b)                      IF(b=0;"";(a−b)/ABS(b)*100) i samme rad (oppstilling)
    ("gsum", kol, i0, i1)              SUM over radene i0..i1 (indekser i Tabell.rader)
    ("ledd", kol, [(±1, ref)])         ±celle i en sum-/resultatrad («rad», i) eller ±SUM over en gruppe («omr», i0, i1)
    ("lik_alle", [kol], skal)          IF(AND(ABS(kol−skal)<0.005, …);"OK";"AVVIK")
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .tekst import kr

EPS = 0.005


@dataclass
class Celle:
    verdi: Any = None
    type: str | None = None        # overstyrer kolonnetypen (f.eks. «status» eller «antall» i en sumrad)
    formel: tuple | None = None    # Excel-oppskrift
    fet: bool | None = None        # None = som raden
    dempet: bool = False           # grå tekst
    innrykk: int = 0               # innrykk i etikettkolonnen (kontolinjer i en oppstilling)


@dataclass
class Rad:
    art: str                       # ib | data | tom | sum | ub | kontroll | antall_avvik | gruppe | resultat
    celler: dict[str, Celle] = field(default_factory=dict)
    fet: bool = False
    vis: str = "begge"             # «excel»: bare i Excel
    luft_for: bool = False         # Excel: én tom rad før denne


@dataclass
class Tabell:
    kolonner: list[dict]
    rader: list[Rad]
    etikett_kol: str
    kilde: str = "tabell"          # tabell | kontroller | sammendrag | oppstilling
    lopende: dict | None = None
    av: str | None = None
    gruppe: str | None = None
    liten: bool = False
    filter: bool = False
    frys: bool = False
    zebra: bool = False
    uthev_avvik: bool = False
    kontrollsum: "Boks | None" = None

    def data(self) -> list[Rad]:
        return [r for r in self.rader if r.art in ("data", "tom")]


@dataclass
class Boks:
    type: str                      # konkl | varsel
    tekst: str


@dataclass
class Seksjon:
    id: str
    ark: str
    sideskift: bool
    overskrift: str | None
    nivaa: int
    bar: bool | None
    tekst: str | None
    tabell: Tabell | None
    bokser: list[Boks]
    punkter: list[str]
    merknad: str | None


def _n(x) -> float:
    return float(x) if isinstance(x, (int, float)) else 0.0


def _rund(x: float) -> float:
    return round(x + 0.0, 2) + 0.0


def _forste_ledige(kolonner, celler, unntatt=()) -> str | None:
    for k in kolonner:
        if k["vis"] == "begge" and k["id"] not in celler and k["id"] not in unntatt:
            return k["id"]
    return None


def _tabell(t: dict) -> Tabell:
    kolonner = t["kolonner"]
    lop = next((k for k in kolonner if k["lopende"]), None)
    et = t["etikett_kol"]
    rader: list[Rad] = []
    start = 0.0
    if lop:
        start = _n(t["ib"].get("verdi") if t["ib"] and t["ib"].get("verdi") is not None else lop["lopende"]["start"])
    if t["ib"] is not None:
        celler = {k: Celle(v) for k, v in t["ib"].items() if k not in ("verdi", "_fet")}
        if lop:
            celler[lop["id"]] = Celle(_rund(start))
        rader.append(Rad("ib", celler, fet=True))
    saldo = start
    pluss = lop["lopende"]["pluss"] if lop else None
    minus = lop["lopende"]["minus"] if lop else None
    for r in t["rader"]:
        celler = {k: Celle(v) for k, v in r.items() if k != "_fet" and v is not None}
        if lop:
            saldo = saldo + (_n(r.get(pluss)) if pluss else 0) - (_n(r.get(minus)) if minus else 0)
            celler[lop["id"]] = Celle(_rund(saldo), formel=("lopende",))
        rader.append(Rad("data", celler, fet=bool(r.get("_fet"))))
    data = t["rader"]
    if not data:
        rader.append(Rad("tom", {et: Celle("Ingen poster i perioden")}))
    s = t["sum"]
    if s:
        n = len(data)
        celler = {s["etikett_kol"]: Celle(s["etikett"].replace("{n}", str(n)))}
        for kid in s["kolonner"]:
            celler[kid] = Celle(_rund(sum(_n(r.get(kid)) for r in data)), formel=("sum", kid))
        if s["tell"]:
            tell_kol = s["tell_kol"] or _forste_ledige(kolonner, celler)
            antall = sum(1 for r in data if r.get(s["tell"]) not in (None, ""))
            if tell_kol:
                celler[tell_kol] = Celle(antall, type="antall", formel=("tell", s["tell"]))
        if s["skal_vaere"] is not None:
            faktisk = celler[s["skal_vaere_kol"]].verdi
            status = "OK" if abs(faktisk - s["skal_vaere"]) < EPS else "AVVIK"
            plass = _forste_ledige(kolonner, celler)
            if plass:
                celler[plass] = Celle(status, type="status", formel=("lik", s["skal_vaere_kol"], s["skal_vaere"]))
            else:
                celler[s["etikett_kol"]].verdi += f" – {status}"
        rader.append(Rad("sum", celler, fet=True, luft_for=t["filter"]))
    ub_verdi = None
    if t["ub"] is not None:
        celler = {k: Celle(v) for k, v in t["ub"].items() if k not in ("verdi", "_fet")}
        if lop:
            if t["ub"].get("verdi") is not None:
                ub_verdi = _rund(_n(t["ub"]["verdi"]))
                celler[lop["id"]] = Celle(ub_verdi)
            else:
                ub_verdi = _rund(saldo)
                celler[lop["id"]] = Celle(ub_verdi, formel=("ub_lopende",))
        rader.append(Rad("ub", celler, fet=True, luft_for=t["filter"] and not s))
    tabell = Tabell(kolonner, rader, et, lopende=lop, liten=t["liten"], filter=t["filter"], frys=t["frys"],
                    zebra=t["zebra"], uthev_avvik=t["uthev_avvik"])
    if t["kontrollsum"] is not None and lop:
        sum_p = _rund(sum(_n(r.get(pluss)) for r in data)) if pluss else 0.0
        sum_m = _rund(sum(_n(r.get(minus)) for r in data)) if minus else 0.0
        ub = ub_verdi if ub_verdi is not None else _rund(saldo)
        beregnet = _rund(start + sum_p - sum_m)
        diff = _rund(beregnet - ub)
        ok = abs(diff) < EPS
        kart = {k["id"]: k for k in kolonner}
        celler = {et: Celle("Kontroll: inngående saldo"
                            + (f" + {kart[pluss]['tekst'].lower()}" if pluss else "")
                            + (f" − {kart[minus]['tekst'].lower()}" if minus else "")
                            + " − utgående saldo"),
                  lop["id"]: Celle(diff, formel=("kontroll_diff",))}
        plass = _forste_ledige(kolonner, celler) or next(
            (k["id"] for k in kolonner if k["id"] not in celler), None)
        if plass:
            celler[plass] = Celle("OK" if ok else "AVVIK", type="status", formel=("kontroll_status", lop["id"]))
        rader.append(Rad("kontroll", celler, fet=True, vis="excel"))
        verdier = {"ib": kr(start), "pluss": kr(sum_p), "minus": kr(sum_m), "ub": kr(ub),
                   "diff": kr(diff), "beregnet": kr(beregnet)}
        p_navn = kart[pluss]["tekst"].lower() if pluss else ""
        m_navn = kart[minus]["tekst"].lower() if minus else ""
        ledd = (f" + {p_navn} {{pluss}}" if pluss else "") + (f" − {m_navn} {{minus}}" if minus else "")
        if ok:
            mal = t["kontrollsum"]["tekst"] or ("**Kontrollert:** inngående saldo {ib}" + ledd + " = utgående saldo {ub}.")
            tabell.kontrollsum = Boks("konkl", _fyll(mal, verdier))
        else:
            mal = t["kontrollsum"]["tekst_avvik"] or (
                "**Avvik:** inngående saldo {ib}" + ledd + " gir {beregnet}, men utgående saldo er {ub}"
                " (differanse {diff}).")
            tabell.kontrollsum = Boks("varsel", _fyll(mal, verdier))
    return tabell


def _fyll(mal: str, verdier: dict) -> str:
    ut = mal
    for k, v in verdier.items():
        ut = ut.replace("{" + k + "}", v)
    return ut


KONTROLL_KOLONNER = [
    ("navn", "Kontroll", "tekst", 34, "l"), ("beregning", "Beregning", "tekst", 52, "l"),
    ("a", None, "belop", 16, "r"), ("b", None, "belop", 16, "r"), ("avvik", "Avvik", "belop", 13, "r"),
    ("status", "Status", "status", 12, "c"), ("kommentar", "Kommentar", "tekst", 46, "l"),
]


def _kontroller(k: dict) -> Tabell:
    kolonner = []
    for kid, tekst, typ, bredde, just in KONTROLL_KOLONNER:
        tekst = tekst or k["etiketter"][kid]
        kolonner.append({"id": kid, "tekst": tekst, "type": typ, "bredde": bredde, "just": just, "vis": "begge",
                         "redact": None, "lopende": None})
    rader = []
    for r in k["rader"]:
        typ = "antall" if r["antall"] else None
        avvik = None if r["a"] is None or r["b"] is None else _rund(r["a"] - r["b"])
        ellers = "FORKLART" if r["forklart"] else "AVVIK"
        status = None if avvik is None else ("OK" if abs(avvik) <= r["toleranse"] else ellers)
        celler = {"navn": Celle(r["navn"], fet=True), "beregning": Celle(r["beregning"], dempet=True),
                  "a": Celle(r["a"], type=typ), "b": Celle(r["b"], type=typ),
                  "avvik": Celle(avvik, type=typ, formel=("avvik", "a", "b") if avvik is not None else None),
                  "status": Celle(status, formel=("kstatus", "avvik", r["toleranse"], ellers) if status else None),
                  "kommentar": Celle(r["kommentar"])}
        rader.append(Rad("data", {k_: c for k_, c in celler.items() if c.verdi is not None}))
    if k["antall_avvik"]:
        n = sum(1 for r in rader if r.celler.get("status") and r.celler["status"].verdi == "AVVIK")
        rader.append(Rad("antall_avvik", {"navn": Celle("Antall avvik"),
                                          "status": Celle(n, type="antall", formel=("antall_avvik", "status"))},
                         fet=True, luft_for=True))
    return Tabell(kolonner, rader, "navn", kilde="kontroller", liten=k["liten"], uthev_avvik=True)


def _sammendrag(sm: dict, kilder: dict[str, dict]) -> Tabell:
    kilde = kilder[sm["av"]]["tabell"]["rader"]
    g = sm["gruppe"]
    kolonner = sm["kolonner"]
    rader = []
    for r in sm["rader"]:
        celler = {k: Celle(v) for k, v in r.items() if k != "_fet" and v is not None}
        nokkel = r.get(g)
        treff = [x for x in kilde if x.get(g) == nokkel]
        for k in kolonner:
            if k.get("tell"):
                celler[k["id"]] = Celle(len(treff), formel=("countif", sm["av"], g))
            elif k.get("summer"):
                celler[k["id"]] = Celle(_rund(sum(_n(x.get(k["summer"])) for x in treff)),
                                        formel=("sumif", sm["av"], g, k["summer"]))
        rader.append(Rad("data", celler, fet=bool(r.get("_fet"))))
    if not rader:
        rader.append(Rad("tom", {sm["etikett_kol"]: Celle("Ingen rader")}))
    s = sm["sum"]
    if s:
        celler = {s["etikett_kol"]: Celle(s["etikett"].replace("{n}", str(len(sm["rader"]))))}
        for kid in s["kolonner"]:
            celler[kid] = Celle(_rund(sum(_n(r.celler[kid].verdi) for r in rader if kid in r.celler)),
                                formel=("sum", kid))
        rader.append(Rad("sum", celler, fet=True, luft_for=sm["filter"]))
    return Tabell(kolonner, rader, sm["etikett_kol"], kilde="sammendrag", av=sm["av"], gruppe=g,
                  liten=sm["liten"], filter=sm["filter"], frys=sm["frys"], zebra=sm["zebra"],
                  uthev_avvik=sm["uthev_avvik"])


def _oppstilling(o: dict) -> Tabell:
    """Grupper (overskrift, kontolinjer, sumlinje) og resultatlinjer (± tidligere linjer), med avvik per rad."""
    kolonner = o["kolonner"]
    et = o["etikett_kol"]
    verdi = o["verdi"]
    avvik = [k for k in kolonner if k.get("avvik")]
    status_kol = next((k["id"] for k in kolonner if k["type"] == "status" and k["vis"] == "begge"), None)
    rader: list[Rad] = []
    total: dict[str, tuple] = {}      # linje-id → (formelreferanse | None, {kol: verdi})

    def legg_avvik(celler: dict) -> None:
        for k in avvik:
            a, b = k["avvik"]
            va = _n(celler[a].verdi) if a in celler else 0.0
            vb = _n(celler[b].verdi) if b in celler else 0.0
            if k["type"] == "prosent":
                v = None if abs(vb) < EPS else round((va - vb) / abs(vb) * 100, 1)
                celler[k["id"]] = Celle(v, formel=("pst", a, b))
            else:
                celler[k["id"]] = Celle(_rund(va - vb), formel=("avvik", a, b))

    for l in o["linjer"]:
        celler_ekstra = {k: Celle(v) for k, v in l["celler"].items() if v is not None}
        if l["resultat"] is None:
            if l["gruppe"]:
                rader.append(Rad("gruppe", {et: Celle(l["gruppe"])}, fet=True, luft_for=l["luft"]))
            i0 = len(rader)
            for r in l["rader"]:
                celler = {k: Celle(v) for k, v in r.items() if k != "_fet" and v is not None}
                if l["innrykk"] and et in celler:
                    celler[et].innrykk = 1
                legg_avvik(celler)
                rader.append(Rad("data", celler, fet=bool(r.get("_fet"))))
            i1 = len(rader) - 1
            summer = {kid: _rund(sum(_n(r.get(kid)) for r in l["rader"])) for kid in verdi}
            if l["sum"]:
                celler = {et: Celle(l["sum"]), **celler_ekstra}
                for kid in verdi:
                    celler[kid] = Celle(summer[kid], formel=("gsum", kid, i0, i1) if l["rader"] else None)
                legg_avvik(celler)
                rader.append(Rad("sum", celler, fet=True, luft_for=l["luft"] and not l["gruppe"]))
                ref = ("rad", len(rader) - 1)
            else:
                ref = ("omr", i0, i1) if l["rader"] else None
            total[l["id"]] = (ref, summer)
            continue
        verdier = {kid: _rund(sum(f * total[lid][1][kid] for f, lid in l["ledd"])) for kid in verdi}
        refs = [(f, total[lid][0]) for f, lid in l["ledd"] if total[lid][0] is not None]
        celler = {et: Celle(l["resultat"]), **celler_ekstra}
        for kid in verdi:
            celler[kid] = Celle(verdier[kid], formel=("ledd", kid, refs) if refs else None)
        legg_avvik(celler)
        if l["skal_vaere"] is not None and status_kol and status_kol not in celler:
            ok = all(abs(verdier[kid] - l["skal_vaere"]) < EPS for kid in verdi)
            celler[status_kol] = Celle("OK" if ok else "AVVIK", type="status",
                                       formel=("lik_alle", verdi, l["skal_vaere"]))
        rader.append(Rad("resultat", celler, fet=True, luft_for=l["luft"]))
        total[l["id"]] = (("rad", len(rader) - 1), verdier)
    return Tabell(kolonner, rader, et, kilde="oppstilling", liten=o["liten"], frys=o["frys"], zebra=o["zebra"],
                  uthev_avvik=o["uthev_avvik"])


def under_deler(dok: dict) -> list[str]:
    """Undertittelen: klient | Org.nr. … | <under …> | Periode … | Utarbeidet … [| Utarbeidet av …]."""
    deler = [dok["klient"]]
    if dok["orgnr"]:
        deler.append(f"Org.nr. {dok['orgnr']}")
    deler += dok["under"]
    deler.append(f"Periode {dok['periode_tekst'] or dok['periode']}")
    deler.append(f"Utarbeidet {dok['utarbeidet']}")
    if dok["utarbeidet_av"]:
        deler.append(f"Utarbeidet av {dok['utarbeidet_av']}")
    return deler


def los(spec: dict) -> list[Seksjon]:
    """Validert spec → seksjoner med ferdig beregnede tabeller."""
    kilder = {s["id"]: s for s in spec["seksjoner"] if s["tabell"]}
    ut = []
    for s in spec["seksjoner"]:
        tabell, bokser = None, []
        if s["tabell"]:
            tabell = _tabell(s["tabell"])
            if tabell.kontrollsum:
                bokser.append(tabell.kontrollsum)
        elif s["kontroller"]:
            tabell = _kontroller(s["kontroller"])
        elif s["sammendrag"]:
            tabell = _sammendrag(s["sammendrag"], kilder)
        elif s.get("oppstilling"):
            tabell = _oppstilling(s["oppstilling"])
        if s["boks"]:
            bokser.append(Boks(s["boks"]["type"], s["boks"]["tekst"]))
        ut.append(Seksjon(s["id"], s["ark"], s["sideskift"], s["overskrift"], s["nivaa"], s["bar"], s["tekst"],
                          tabell, bokser, s["punkter"], s["merknad"]))
    return ut


def avvik_i(tabell: Tabell, rad: Rad) -> bool:
    """Har raden en statuscelle med AVVIK/FEIL/MANGLER?"""
    for kid, c in rad.celler.items():
        typ = c.type or next((k["type"] for k in tabell.kolonner if k["id"] == kid), None)
        if typ == "status" and c.verdi in ("AVVIK", "FEIL", "MANGLER"):
            return True
    return False
