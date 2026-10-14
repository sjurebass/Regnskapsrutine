"""regnskap.json (fra `npm run -s regnskap`) → Silfer-spec → Excel/PDF: resultat, balanse, nøkkeltall, avvik og bro.

    uv run --with openpyxl --with pillow --with pypdf python .claude/skills/regnskapsrapport/scripts/lag_spec.py \\
        <mappe>/regnskap.json --mappe <mappe> [--avvik <mappe>/avvik.json] [--bare-grupper] [--bare-avvik]
        [--format xlsx,pdf] [--av <initialer>] [--forelopig "<grunn>"] [--maks-avvik 10]

Tallene hentes bare fra regnskap.json. Summer, resultatlinjer og avvik blir formler i Excel (silfer-rapport «oppstilling»).
Flagg (references/oppstilling.md): AVVIK = |avvik| ≥ V; MERKNAD = |avvik %| ≥ terskel (budsjett 10, i fjor 15, forrige 20) og |avvik| ≥ V/2.
Kontroller: N1 (balansen går opp med årets resultat), N2 (vesentlige avvik), N3/N4 (bro), N5 (nøkkeltall), N6 (fullstendig
oppstilling), N8 (uventet fortegn).

avvik.json (fra avviksanalyse; alt er valgfritt):
  { "avvik": [ { "id": "5000" | "driftsresultat", "mot": "ifjor", "type": "lønnsdrevet", "driver": "…", "utsikt": "vedvarende",
                 "tiltak": "ingen", "status": "FORKLART" | "KJENT" | "AVVIK" | "IKKE AVKLART", "krever": "–" } ],
    "bro": { "linje": "driftsresultat", "mot": "ifjor",
             "drivere": [ { "tekst": "Salgsinntekt, høyere volum", "type": "volumdrevet", "belop": 43500 }, … ] } }
  `id` er rad-id i regnskap.json (kontonummer som tekst, eller gruppe-/sum-id). Start og slutt i broen hentes fra regnskap.json.
  Driverne har samme fortegn som linjen: for resultatlinjer effekten på resultatet, for en kostnadslinje økt kostnad som pluss.

Exit 0 = filene er laget, 1 = feil, 2 = PDF ikke laget (ingen nettleser), 3 = stopp (N1 AVVIK eller broen går ikke opp / diverse ≥ 20 %).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / ".claude" / "skills" / "silfer-rapport" / "scripts"))

from silfer import bygg, filnavn  # noqa: E402
from silfer.filer import lag_mappe, os_sti  # noqa: E402
from silfer.spec import SpecFeil, valider  # noqa: E402
from silfer.tekst import kr  # noqa: E402

TERSKEL = {"forrige": 20, "ifjor": 15, "budsjett": 10}
CMPS = ("forrige", "ifjor", "budsjett")
# Resultatlinjene i regnskap.js (RESULTAT/BALANSE) – samme oppskrift, så Excel får formler.
LEDD = {
    "sumDriftskostnader": ["varekostnad", "lonnskostnad", "avskrivning", "annenDriftskostnad"],
    "driftsresultat": ["driftsinntekter", "-sumDriftskostnader"],
    "resultatForSkatt": ["driftsresultat", "finansinntekter", "-finanskostnader"],
    "aarsresultat": ["resultatForSkatt", "-skattekostnad", "-andreResultatposter"],
    "resultatEtterDisponeringer": ["aarsresultat", "-disponeringer"],
    "sumEiendeler": ["anleggsmidler", "omlopsmidler"],
    "sumGjeld": ["langsiktigGjeld", "kortsiktigGjeld"],
    "sumEgenkapitalOgGjeld": ["egenkapital", "sumGjeld"],
}
LUFT_FOR = {"sumDriftskostnader", "resultatForSkatt", "aarsresultat", "sumEiendeler", "sumGjeld"}
# Kontoer der motsatt fortegn er normalt (N8 hopper over dem).
KONTRA = [(1580, 1589), (2010, 2019), (2080, 2089), (3080, 3099), (5800, 5899)]
KORT = ["jan", "feb", "mar", "apr", "mai", "jun", "jul", "aug", "sep", "okt", "nov", "des"]


def kort_tekst(k: dict) -> str:
    """Kort kolonneoverskrift: «Sep 2026», «Jan–sep 2026», «2026», «Budsjett»."""
    if k["id"] == "budsjett":
        return "Budsjett"
    y1, m1 = int(k["fra"][:4]), int(k["fra"][5:7])
    y2, m2 = int(k["til"][:4]), int(k["til"][5:7])
    if (y1, m1) == (y2, m2):
        return f"{KORT[m1 - 1].capitalize()} {y1}"
    if y1 == y2 and m1 == 1 and m2 == 12:
        return str(y1)
    if y1 == y2:
        return f"{KORT[m1 - 1].capitalize()}–{KORT[m2 - 1]} {y1}"
    return f"{KORT[m1 - 1].capitalize()} {y1}–{KORT[m2 - 1]} {y2}"


def dato_no(iso: str | None) -> str:
    return f"{iso[8:10]}.{iso[5:7]}.{iso[:4]}" if iso else ""


def orgnr_no(s: str) -> str:
    s = "".join(ch for ch in str(s or "") if ch.isdigit())
    return f"{s[:3]} {s[3:6]} {s[6:]}" if len(s) == 9 else s


def flagg(avvik: dict | None, cmp: str, v: float) -> str | None:
    """AVVIK/MERKNAD/None for én sammenligning."""
    if not avvik:
        return None
    a = abs(avvik.get("kr") or 0)
    p = avvik.get("pst")
    if a >= v and a >= 0.005:
        return "AVVIK"
    if p is not None and abs(p) >= TERSKEL[cmp] and a >= v / 2:
        return "MERKNAD"
    return None


def verste(statuser) -> str | None:
    s = [x for x in statuser if x]
    return "AVVIK" if "AVVIK" in s else ("MERKNAD" if s else None)


class Bygger:
    def __init__(self, j: dict, a: argparse.Namespace, avvik: dict):
        self.j, self.a, self.avvik = j, a, avvik
        self.V = float(j["terskler"]["vesentlighet"])
        self.kol = {k["id"]: k for k in j["kolonner"]}
        self.cmps = [c for c in CMPS if c in self.kol and self.kol[c]["status"] == "ok"]
        self.funn: list[dict] = []
        self.stopp: list[str] = []
        self.rader = {("resultat", r["id"]): r for r in j["resultat"]["rader"]}
        self.rader.update({("balanse", r["id"]): r for r in j["balanse"]["rader"]})

    # ── felles ────────────────────────────────────────────────────────────
    def nytt_funn(self, id_, status, forslag, *, konto=None, linje="", mot="", denne=None, verdi=None, belop=None,
                  pst=None, retning="", krever="–"):
        self.funn.append({"id": id_, "klient": self.j["klient"], "periode": self.j["periode"], "konto": konto, "linje": linje,
                          "mot": mot, "denne": denne, "verdi": verdi, "belop": belop, "pst": pst, "retning": retning,
                          "status": status, "forslag": forslag, "krever": krever})

    def verdikolonner(self, del_: str) -> list[str]:
        return ["denne"] + [c for c in self.cmps if not (del_ == "balanse" and c == "budsjett")]

    def kolonner(self, del_: str) -> list[dict]:
        kol = [{"id": "konto", "tekst": "Konto", "type": "heltall", "bredde": 7},
               {"id": "tekst", "tekst": "Linje", "bredde": 34}]
        kol.append({"id": "denne", "tekst": kort_tekst(self.kol["denne"]) if del_ == "resultat"
                    else dato_no(self.kol["denne"]["balansedato"]), "type": "belop"})
        for c in self.verdikolonner(del_)[1:]:
            tekst = kort_tekst(self.kol[c]) if del_ == "resultat" else dato_no(self.kol[c]["balansedato"])
            kol.append({"id": c, "tekst": tekst, "type": "belop"})
            kol.append({"id": f"avvik_{c}", "tekst": "Avvik" if del_ == "resultat" else "Endring", "type": "belop",
                        "avvik": ["denne", c]})
            if del_ == "resultat":
                kol.append({"id": f"pst_{c}", "tekst": "%", "type": "prosent", "bredde": 8, "avvik": ["denne", c]})
        kol.append({"id": "status", "tekst": "Flagg" if del_ == "resultat" else "Kontroll", "type": "status", "bredde": 11})
        return kol

    def status_rad(self, r: dict, del_: str) -> str | None:
        if del_ != "resultat" or (r["nivaa"] == "konto" and r.get("konto") is None):
            return None
        return verste(flagg(r.get("avvik", {}).get(c), c, self.V) for c in self.cmps)

    def verdier(self, r: dict, del_: str) -> dict:
        return {c: r.get(c) for c in self.verdikolonner(del_) if r.get(c) is not None}

    # ── oppstilling ───────────────────────────────────────────────────────
    def oppstilling(self, del_: str) -> dict:
        linjer, ider, gruppe = [], set(), None
        for r in self.j[del_]["rader"]:
            st = self.status_rad(r, del_)
            if r["nivaa"] == "gruppe":
                gruppe = {"id": r["id"], "_tekst": r["tekst"], "_status": st, "_rad": r, "rader": []}
                linjer.append(gruppe)
                ider.add(r["id"])
            elif r["nivaa"] == "konto":
                rad = {"tekst": r["tekst"], **self.verdier(r, del_)}
                if r.get("konto") is not None:
                    rad["konto"] = r["konto"]
                if st:
                    rad["status"] = st
                if gruppe is not None:
                    gruppe["rader"].append(rad)
            else:
                gruppe = None
                ledd = LEDD.get(r["id"])
                celler = {"status": st} if st else {}
                if ledd is None:
                    print(f"merk: ukjent sumlinje «{r['id']}» – skrevet som tall uten formel")
                    linjer.append({"id": r["id"], "rader": [{"tekst": r["tekst"], **self.verdier(r, del_)}], "innrykk": False})
                else:
                    brukt = [x for x in ledd if x.lstrip("-") in ider]
                    linjer.append({"id": r["id"], "resultat": r["tekst"], "ledd": brukt, "celler": celler,
                                   "luft": r["id"] in LUFT_FOR})
                ider.add(r["id"])
        ut = []
        for l in linjer:
            if "_tekst" not in l:
                if l.get("resultat") is not None and not l["ledd"]:
                    l = {"id": l["id"], "sum": l["resultat"], "rader": []}
                ut.append({k: v for k, v in l.items() if not (k == "celler" and not v)})
                continue
            tekst, st, r = l["_tekst"], l["_status"], l["_rad"]
            celler = {"status": st} if st else {}
            if self.a.bare_grupper or not l["rader"]:
                rad = {"tekst": tekst, **self.verdier(r, del_)}
                if st:
                    rad["status"] = st
                ut.append({"id": l["id"], "rader": [rad], "innrykk": False})
            else:
                ny = {"id": l["id"], "gruppe": tekst, "rader": l["rader"], "sum": f"Sum {tekst[0].lower()}{tekst[1:]}"}
                if celler:
                    ny["celler"] = celler
                ut.append(ny)
        if del_ == "balanse" and {"sumEiendeler", "sumEgenkapitalOgGjeld"} <= ider:
            ut.append({"id": "kontroll", "resultat": "Kontroll: eiendeler − egenkapital og gjeld",
                       "ledd": ["sumEiendeler", "-sumEgenkapitalOgGjeld"], "skal_vaere": 0, "luft": True})
        return {"kolonner": self.kolonner(del_), "linjer": ut, "frys": True, "liten": len(self.cmps) > 1}

    # ── kontroller ────────────────────────────────────────────────────────
    def kontroll_n6(self) -> None:
        """Sum kontoer = gruppe, og resultatlinjene = oppskriften (samme tall som regnskap.json)."""
        avvik = []
        for del_ in ("resultat", "balanse"):
            rr = self.j[del_]["rader"]
            verdi = {r["id"]: r for r in rr if r["nivaa"] != "konto"}
            for c in self.verdikolonner(del_):
                for g in (r for r in rr if r["nivaa"] == "gruppe"):
                    s = sum((x.get(c) or 0) for x in rr if x["nivaa"] == "konto" and x["gruppe"] == g["id"])
                    if abs(s - (g.get(c) or 0)) > 0.01:
                        avvik.append(f"{g['tekst']} ({c}): kontoer {kr(s)} ≠ gruppe {kr(g.get(c))}")
                for sid, ledd in LEDD.items():
                    if sid not in verdi:
                        continue
                    s = sum((-1 if x.startswith("-") else 1) * (verdi.get(x.lstrip("-"), {}).get(c) or 0) for x in ledd)
                    if abs(s - (verdi[sid].get(c) or 0)) > 0.01:
                        avvik.append(f"{verdi[sid]['tekst']} ({c}): {kr(s)} ≠ {kr(verdi[sid].get(c))}")
        kres = self.j["kontroll"]["resultat"]
        if not kres["ok"]:
            avvik.append(f"resultat ≠ −Σ 3000–8999 (differanse {kr(kres['differanse'])})")
        andre = self.rader.get(("resultat", "andreResultatposter"))
        if avvik:
            self.nytt_funn("N6", "AVVIK", "Oppstillingen går ikke opp: " + "; ".join(avvik[:3]), krever="regnskapsfører")
        elif andre and abs(andre.get("denne") or 0) >= 0.005:
            self.nytt_funn("N6", "MERKNAD", "Saldo på andre resultatposter (8500–8799) – skal normalt være tom; omklassifiser.",
                           linje=andre["tekst"], belop=andre.get("denne"), krever="regnskapsfører")
        else:
            self.nytt_funn("N6", "OK", "Alle kontoer med saldo ligger i en gruppe; summene stemmer med saldobalansen.")

    def kontroll_n1(self) -> None:
        kb = self.j["kontroll"]["balanse"]
        if not kb["ok"]:
            self.nytt_funn("N1", "AVVIK", f"Balansen går ikke opp med årets resultat: rest {kr(kb['rest'])}. Avstem i balanseavstemming (S9).",
                           belop=kb["rest"], krever="regnskapsfører")
            self.stopp.append(f"N1: balansen går ikke opp (rest {kr(kb['rest'])})")
        elif not kb.get("tidligereAarDisponert", True):
            mnd = int(str(kb["balansedato"])[5:7])
            if mnd <= 6:
                self.nytt_funn("N1", "FORKLART", "Fjorårets resultat er ikke disponert ennå (årsoppgjøret ikke bokført).",
                               linje="Udisponert resultat tidligere år", belop=kb["udisponertTidligereAar"])
            else:
                self.nytt_funn("N1", "MERKNAD", "Resultat fra tidligere år er ikke disponert – sjekk disponeringen (88xx–89xx mot 20xx).",
                               linje="Udisponert resultat tidligere år", belop=kb["udisponertTidligereAar"], krever="regnskapsfører")
        else:
            self.nytt_funn("N1", "OK", "Sum eiendeler = sum egenkapital og gjeld med årets resultat hittil.")

    def kontroll_n8(self) -> None:
        for del_ in ("resultat", "balanse"):
            for r in self.j[del_]["rader"]:
                k = r.get("konto")
                if r["nivaa"] != "konto" or k is None or any(a <= k <= b for a, b in KONTRA):
                    continue
                d = r.get("denne") or 0
                if d < 0 and abs(d) >= self.V / 10:
                    art = {"inntekt": "inntekt i debet", "kostnad": "kostnad i kredit", "eiendel": "eiendel i kredit",
                           "egenkapital": "egenkapital i debet", "gjeld": "gjeld i debet"}.get(r["art"], "motsatt fortegn")
                    self.nytt_funn("N8", "MERKNAD", f"Uventet fortegn ({art}) – undersøk føringen.", konto=k, linje=r["tekst"],
                                   denne=d, belop=d, krever="regnskapsfører")

    def nokkeltall(self) -> dict:
        inntekt = abs((self.rader.get(("resultat", "driftsinntekter")) or {}).get("denne") or 0)
        rader = []
        for n in self.j["nokkeltall"]:
            pst = n["enhet"] == "pst"
            meningslos = n["id"] in ("bruttomargin", "driftsmargin", "lonnAvInntekt") and inntekt < self.V
            rad = {"navn": n["tekst"] + (" (%)" if pst and "%" not in n["tekst"] else ""), "formel": n["formel"]}
            if meningslos:
                rad["normal"] = "driftsinntekter under V"
                rad["status"] = "IKKE AKTUELT"
                rader.append(rad)
                continue
            for c in ["denne", *self.cmps]:
                if n.get(c) is not None:
                    rad[c] = n[c]
            d = n.get("denne")
            endr = [abs(x) for x in (n.get("endring") or {}).values() if x is not None]
            st, normal = "OK", ""
            if n["id"] in ("bruttomargin", "lonnAvInntekt"):
                normal = "endring < 5 pp"
                st = "MERKNAD" if any(x >= 5 for x in endr) else "OK"
            elif n["id"] == "driftsmargin":
                normal = "≥ 0 og endring < 5 pp"
                st = "MERKNAD" if (d is not None and d < 0) or any(x >= 5 for x in endr) else "OK"
            elif n["id"] == "likviditetsgrad1":
                normal = "≥ 1,0"
                st = "IKKE AVKLART" if d is None else ("AVVIK" if d < 0.5 else ("MERKNAD" if d < 1 else "OK"))
            elif n["id"] == "egenkapitalandel":
                normal = "≥ 10 %"
                st = "IKKE AVKLART" if d is None else ("AVVIK" if d < 0 else ("MERKNAD" if d < 10 else "OK"))
            rad["normal"], rad["status"] = normal, st
            rader.append(rad)
            if st in ("MERKNAD", "AVVIK"):
                self.nytt_funn("N5", st, f"{n['tekst']} utenfor normalområdet ({normal}).", linje=n["tekst"], pst=None,
                               krever="regnskapsfører" if st == "AVVIK" else "–")
        kol = [{"id": "navn", "tekst": "Nøkkeltall", "bredde": 26}, {"id": "formel", "tekst": "Beregning", "bredde": 42},
               {"id": "denne", "tekst": kort_tekst(self.kol["denne"]), "type": "belop", "bredde": 11}]
        kol += [{"id": c, "tekst": kort_tekst(self.kol[c]), "type": "belop", "bredde": 11} for c in self.cmps]
        kol += [{"id": "normal", "tekst": "Normalområde", "bredde": 18}, {"id": "status", "tekst": "Status", "type": "status", "bredde": 12}]
        return {"kolonner": kol, "rader": rader}

    def vesentlige_avvik(self) -> None:
        forklart = {(x.get("id"), x.get("mot")): x for x in self.avvik.get("avvik", [])}
        kandidater = []
        for r in self.j["resultat"]["rader"]:
            if r["nivaa"] != "konto" or r.get("konto") is None:
                continue
            for c in self.cmps:
                av = (r.get("avvik") or {}).get(c)
                st = flagg(av, c, self.V)
                if st:
                    kandidater.append((abs(av["kr"]), r, c, av, st))
        for x in self.avvik.get("avvik", []):       # forklarte linjer som ikke er kontolinjer (f.eks. driftsresultat)
            r = self.rader.get(("resultat", str(x.get("id"))))
            c = x.get("mot")
            if r and r["nivaa"] != "konto" and c in self.cmps and (r.get("avvik") or {}).get(c):
                av = r["avvik"][c]
                kandidater.append((abs(av["kr"]), r, c, av, flagg(av, c, self.V) or "MERKNAD"))
        kandidater.sort(key=lambda t: -t[0])
        sett, unike = set(), []
        for t in kandidater:                        # én linje per konto: største avvik; forklarte sammenligninger beholdes
            nokkel = (str(t[1]["id"]), t[2] if (str(t[1]["id"]), t[2]) in forklart else None)
            if nokkel in sett or (nokkel[1] is None and (nokkel[0], None) in sett):
                continue
            sett.add(nokkel)
            unike.append(t)
        kandidater = unike
        vist = kandidater[: self.a.maks_avvik]
        for _, r, c, av, st in vist:
            f = forklart.get((str(r["id"]), c))
            if f:
                st = (f.get("status") or "FORKLART").upper()
                forslag = " ".join(x for x in [f"{f.get('type', '').capitalize()}:" if f.get("type") else "",
                                                f.get("driver", ""), f"Utsikt: {f['utsikt']}." if f.get("utsikt") else "",
                                                f"Tiltak: {f['tiltak']}." if f.get("tiltak") else ""] if x)
                krever = f.get("krever", "–")
            else:
                forslag, krever = self.forslag(r, c, st)
            self.nytt_funn("N2", st, forslag, konto=r.get("konto"), linje=r["tekst"], mot=kort_tekst(self.kol[c]),
                           denne=r.get("denne"), verdi=r.get(c), belop=av["kr"], pst=av.get("pst"),
                           retning={True: "gunstig", False: "ugunstig"}.get(av.get("gunstig"), ""), krever=krever)
        if len(kandidater) > len(vist):
            self.nytt_funn("N2", "MERKNAD", f"{len(kandidater) - len(vist)} flere flaggede linjer under de {len(vist)} største – se Resultat-arket.")

    def forslag(self, r: dict, c: str, st: str) -> tuple[str, str]:
        k, d, v = r.get("konto") or 0, r.get("denne") or 0, r.get(c) or 0
        if 6500 <= k <= 6599 and d >= 30000:
            return "Vurder aktivering (kostpris ≥ 30 000 kr og levetid ≥ 3 år) – A4.", "regnskapsfører"
        if abs(v) < 0.005:
            return "Ny i perioden: engangs, ny avtale eller periodisering? Forklar i avviksanalyse.", "regnskapsfører"
        if abs(d) < 0.005:
            return "Mangler i perioden: fast kostnad eller inntekt uteblitt (A3), eller periodisering? Forklar i avviksanalyse.", "regnskapsfører"
        if st == "AVVIK":
            return "Forklar i avviksanalyse (driver, utsikt, tiltak).", "regnskapsfører"
        return "Følg med neste periode.", "–"

    # ── bro ───────────────────────────────────────────────────────────────
    def bro(self) -> dict | None:
        b = self.avvik.get("bro")
        if not b:
            return None
        lid, mot = str(b.get("linje")), b.get("mot")
        r = self.rader.get(("resultat", lid)) or self.rader.get(("balanse", lid))
        if not r or mot not in self.kol or r.get(mot) is None:
            raise SystemExit(f"Feil i avvik.json: bro.linje «{lid}» eller bro.mot «{mot}» finnes ikke i regnskap.json.")
        start, slutt = float(r[mot]), float(r["denne"])
        drivere = b.get("drivere") or []
        sum_d = round(sum(float(x["belop"]) for x in drivere), 2)
        diff = round(start + sum_d - slutt, 2)
        endring = slutt - start
        diverse = abs(sum(float(x["belop"]) for x in drivere if str(x.get("type", "")).lower() == "diverse"))
        andel = 0.0 if abs(endring) < 0.005 else diverse / abs(endring) * 100
        n3 = abs(diff) < 0.005
        n4 = andel < 20
        self.nytt_funn("N3", "OK" if n3 else "AVVIK",
                       "Broen går opp." if n3 else f"Broen går ikke opp: start + drivere − slutt = {kr(diff)}. Dekomponer videre.",
                       linje=r["tekst"], mot=kort_tekst(self.kol[mot]), belop=None if n3 else diff,
                       krever="–" if n3 else "regnskapsfører")
        self.nytt_funn("N4", "OK" if n4 else "AVVIK", f"«Diverse» er {round(andel)} % av avviket (grense 20 %).",
                       linje=r["tekst"], belop=diverse or None, krever="–" if n4 else "regnskapsfører")
        if not n3:
            self.stopp.append(f"N3: broen går ikke opp (differanse {kr(diff)})")
        if not n4:
            self.stopp.append(f"N4: «diverse» er {round(andel)} % av avviket")
        fra, til = kort_tekst(self.kol[mot]), kort_tekst(self.kol["denne"])
        return {"id": "bro", "ark": "Bro", "overskrift": f"Bro: {r['tekst'].lower()} {fra} → {til}",
                "tabell": {"kolonner": [{"id": "tekst", "tekst": "Driver", "bredde": 44}, {"id": "type", "tekst": "Type", "bredde": 16},
                                        {"id": "belop", "tekst": "Beløp", "type": "belop"},
                                        {"id": "kum", "tekst": "Kumulativt", "lopende": {"pluss": "belop"}}],
                           "ib": {"tekst": f"{r['tekst']} {fra}", "verdi": start},
                           "rader": [{"tekst": x["tekst"], "type": x.get("type", ""), "belop": x["belop"]} for x in drivere],
                           "ub": {"tekst": f"{r['tekst']} {til}", "verdi": slutt},
                           "kontrollsum": {"tekst": f"**Broen går opp:** {fra} {{ib}} + drivere {{pluss}} = {til} {{ub}}.",
                                           "tekst_avvik": f"**Broen går ikke opp:** {fra} {{ib}} + drivere {{pluss}} gir {{beregnet}}, "
                                                          f"men {til} er {{ub}} (differanse {{diff}})."}},
                "merknad": f"«Diverse» er {kr(diverse, 0)} kr av et samlet avvik på {kr(abs(endring), 0)} kr ({round(andel)} %). "
                           "Driverne har samme fortegn som linjen."}

    # ── spec ──────────────────────────────────────────────────────────────
    def funn_seksjon(self, tittel: str, bare_avvik: bool) -> dict:
        kol = [{"id": "id", "tekst": "ID", "bredde": 5}, {"id": "klient", "tekst": "Klient", "vis": "excel"},
               {"id": "periode", "tekst": "Periode", "vis": "excel", "bredde": 10},
               {"id": "konto", "tekst": "Konto", "type": "heltall", "bredde": 7}, {"id": "linje", "tekst": "Linje", "bredde": 24},
               {"id": "mot", "tekst": "Mot", "bredde": 10}, {"id": "denne", "tekst": "Denne", "type": "belop", "vis": "excel"},
               {"id": "verdi", "tekst": "Sammenligning", "type": "belop", "vis": "excel"},
               {"id": "belop", "tekst": "Beløp", "type": "belop"}, {"id": "pst", "tekst": "%", "type": "prosent", "bredde": 8},
               {"id": "retning", "tekst": "Retning", "bredde": 10}, {"id": "status", "tekst": "Status", "type": "status", "bredde": 12},
               {"id": "forslag", "tekst": "Forslag", "bredde": 48}, {"id": "krever", "tekst": "Krever", "bredde": 14}]
        ids = ("N2", "N3", "N4") if bare_avvik else None
        rader = [{k: v for k, v in f.items() if v not in (None, "")} for f in self.funn if ids is None or f["id"] in ids]
        return {"id": "funn", "ark": "Avvik", "overskrift": tittel, "sideskift": not bare_avvik,
                "tabell": {"kolonner": kol, "rader": rader, "uthev_avvik": True, "liten": True},
                "merknad": f"V = {kr(self.V, 0)} kr ({self.j['terskler'].get('vesentlighetKilde', '')}). AVVIK = |avvik| ≥ V. "
                           "MERKNAD = |avvik %| over terskelen (budsjett 10, i fjor 15, forrige periode 20) og |avvik| ≥ V/2."}

    def spec(self) -> dict:
        j, a = self.j, self.a
        mot = " og ".join(kort_tekst(self.kol[c]) for c in self.cmps)
        ptekst = j["periodeTekst"][0].upper() + j["periodeTekst"][1:]
        periode_tekst = f"{ptekst}" + (f", sammenlignet med {mot}" if mot else "")
        if a.forelopig:
            periode_tekst += f" – foreløpig: {a.forelopig}"
        hva = "Avviksanalyse" if a.bare_avvik else ("Regnskapsrapport hittil i år" if j.get("hittil") else "Regnskapsrapport")
        dok = {"hva": hva, "tittel": f"{hva} {j['periodeTekst']}", "klient": j["klient"], "orgnr": orgnr_no(j.get("orgnr")),
               "periode": j["periode"], "periode_tekst": periode_tekst}
        if a.av:
            dok["utarbeidet_av"] = a.av
        self.kontroll_n1()
        self.kontroll_n6()
        self.kontroll_n8()
        seksjoner = []
        bro = self.bro()
        if a.bare_avvik:
            self.vesentlige_avvik()
            seksjoner.append(self.funn_seksjon(f"Avvik {j['periodeTekst']}", True))
        else:
            merk = [j.get("fortegn", ""), *j.get("merknader", [])]
            seksjoner.append({"id": "resultat", "ark": "Resultat", "overskrift": f"Resultatregnskap {j['periodeTekst']}",
                              "oppstilling": self.oppstilling("resultat"),
                              "merknad": " ".join(m for m in merk if m)
                              + " Flagg: AVVIK = |avvik| ≥ V; MERKNAD = over terskel-% og ≥ V/2."})
            seksjoner.append({"id": "balanse", "ark": "Balanse", "sideskift": True,
                              "overskrift": f"Balanse per {dato_no(self.kol['denne']['balansedato'])}",
                              "oppstilling": self.oppstilling("balanse"),
                              "merknad": "Egenkapital og gjeld vises positive. Årets resultat er ikke overført til egenkapitalen før "
                                         "årsoppgjøret og står som egen linje under egenkapitalen."})
            seksjoner.append({"id": "nokkeltall", "ark": "Nøkkeltall", "overskrift": "Nøkkeltall", "tabell": self.nokkeltall(),
                              "merknad": "Margin og lønnsandel vurderes mot klientens egen historikk. Egenkapitalandel og "
                                         "likviditetsgrad er per balansedagen."})
            self.vesentlige_avvik()
            seksjoner.append(self.funn_seksjon("Kontroller og vesentlige avvik", False))
        if bro:
            seksjoner.append(bro)
        return {"versjon": 1, "dokument": dok, "seksjoner": seksjoner}

    def hovedtall(self) -> list[str]:
        ut = []
        for del_, rid, navn in (("resultat", "driftsinntekter", "Driftsinntekter"), ("resultat", "driftsresultat", "Driftsresultat"),
                                ("resultat", "aarsresultat", "Periodens resultat"), ("balanse", "sumEiendeler", "Sum eiendeler"),
                                ("balanse", "egenkapital", "Egenkapital")):
            r = self.rader.get((del_, rid))
            if not r:
                continue
            deler = [f"{navn}: {kr(r.get('denne'), 0)}"]
            for c in self.verdikolonner(del_)[1:]:
                av = (r.get("avvik") or {}).get(c) or {}
                p = av.get("pst")
                deler.append(f"{c} {kr(r.get(c), 0)} ({kr(av.get('kr'), 0)}{'' if p is None else f', {kr(p, 1)} %'})")
            ut.append(" · ".join(deler))
        bank = sum((r.get("denne") or 0) for r in self.j["balanse"]["rader"]
                   if r["nivaa"] == "konto" and isinstance(r.get("konto"), int) and 1900 <= r["konto"] <= 1999)
        ut.append(f"Bank og kontanter (19xx): {kr(bank, 0)}")
        return ut


def main(argv=None) -> int:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description="regnskap.json → Silfer-rapport (resultat, balanse, nøkkeltall, avvik, bro).")
    ap.add_argument("regnskap", help="regnskap.json fra npm run -s regnskap")
    ap.add_argument("--mappe", required=True, help="mappen filene skrives til (kort arbeidsmappe)")
    ap.add_argument("--avvik", help="avvik.json fra avviksanalyse (forklaringer og bro)")
    ap.add_argument("--bare-grupper", action="store_true", help="én linje per gruppe (kortversjon)")
    ap.add_argument("--bare-avvik", action="store_true", help="bare avvik og bro («Avviksanalyse …»)")
    ap.add_argument("--format", default="xlsx,pdf", help="xlsx, pdf og/eller html (standard xlsx,pdf)")
    ap.add_argument("--av", help="initialer for «Utarbeidet av»")
    ap.add_argument("--forelopig", help="grunn til at tallene er foreløpige (står i periodeteksten)")
    ap.add_argument("--maks-avvik", type=int, default=10, help="maks antall vesentlige avvik i lista (standard 10)")
    a = ap.parse_args(argv)
    try:
        with open(os_sti(a.regnskap), encoding="utf-8-sig") as f:
            j = json.load(f)
        avvik = {}
        if a.avvik:
            with open(os_sti(a.avvik), encoding="utf-8-sig") as f:
                avvik = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"Kunne ikke lese inndata: {e}")
        return 1
    if j.get("kommando") != "regnskap" or j.get("versjon") != 1:
        print("Inndata er ikke regnskap.json versjon 1 fra `npm run -s regnskap`.")
        return 1
    b = Bygger(j, a, avvik)
    try:
        spec = b.spec()
    except SystemExit as e:
        print(e)
        return 1
    for linje in b.hovedtall():
        print(linje)
    for f in b.funn:
        if f["id"] in ("N1", "N3", "N4", "N6") or f["status"] in ("AVVIK",):
            konto = f" {f['konto']}" if f.get("konto") else ""
            print(f"{f['id']}{konto} {f['status']}: {f['forslag']}")
    n2 = [f for f in b.funn if f["id"] == "N2"]
    print(f"Vesentlige avvik (N2): {len(n2)} linjer · N5: {sum(1 for f in b.funn if f['id'] == 'N5')} · "
          f"N8: {sum(1 for f in b.funn if f['id'] == 'N8')}")
    if b.stopp:
        print("STOPP – ingen fil laget: " + "; ".join(b.stopp))
        return 3
    try:
        spec = valider(spec)
    except SpecFeil as e:
        print(f"Feil i spec: {e}")
        return 1
    mappe = Path(a.mappe)
    lag_mappe(mappe)
    with open(os_sti(mappe / "spec-regnskapsrapport.json"), "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in spec.items() if not k.startswith("_")}, f, ensure_ascii=False, indent=1, default=str)
    kode = 0
    for fmt in [x.strip() for x in a.format.split(",") if x.strip()]:
        ut = mappe / filnavn(spec["dokument"]["hva"], spec["dokument"]["periode"], spec["dokument"]["klient"], fmt)
        try:
            bygg(spec, ut)
            print(f"Laget {ut}")
        except Exception as e:  # noqa: BLE001
            from silfer.pdf import NettleserMangler
            if isinstance(e, NettleserMangler):
                print(f"PDF ikke laget – fant verken Edge eller Chrome: {e.html_fil}")
                kode = 2
            else:
                raise
    if spec.get("_redigert"):
        print(f"Personvern: {spec['_redigert']} felt maskert som [skjult].")
    return kode


if __name__ == "__main__":
    sys.exit(main())
