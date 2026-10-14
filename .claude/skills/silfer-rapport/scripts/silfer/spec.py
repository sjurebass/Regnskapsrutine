"""Lesing og validering av spec.json. Feil meldes med sti («seksjoner[1].tabell.kolonner[3].type: …») så specen kan rettes i ett forsøk.

`valider()` fyller standardverdier, gjør om posisjonsrader til dict-rader, tvinger celleverdier til kolonnetypen og
maskerer personopplysninger i tekst (`dokument.personvern.redact`, standard på). Resultatet merkes `_validert`.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from . import tema
from .filer import os_sti
from .tekst import i_dag, parse_amount, redact, til_dato


class SpecFeil(ValueError):
    pass


def last(sti_eller_dict) -> dict:
    """Leser spec fra fil (utf-8, også med BOM) eller kopierer et dict."""
    if isinstance(sti_eller_dict, dict):
        return copy.deepcopy(sti_eller_dict)
    sti = Path(sti_eller_dict)
    try:
        with open(os_sti(sti), encoding="utf-8-sig") as f:
            return json.loads(f.read())
    except FileNotFoundError:
        raise SpecFeil(f"Fant ikke spec-filen: {sti}") from None
    except UnicodeDecodeError:
        raise SpecFeil(f"{sti}: ikke UTF-8. Skriv spec-filen med Write-verktøyet eller Python (PowerShell «>» gir UTF-16).") from None
    except json.JSONDecodeError as e:
        raise SpecFeil(f"{sti}: ugyldig JSON på linje {e.lineno}, kolonne {e.colno}: {e.msg}") from None


_ARK_ULOVLIG = re.compile(r"[\[\]:*?/\\]")
_TALLTYPER = ("belop", "antall", "heltall", "prosent")
_INNHOLD = ("tabell", "kontroller", "sammendrag")


class _Ctx:
    def __init__(self, redact_paa: bool):
        self.redact_paa = redact_paa
        self.antall = 0

    def mask(self, tekst, paa: bool | None = None):
        if not (self.redact_paa if paa is None else paa):
            return tekst
        ny, n = redact(tekst)
        self.antall += n
        return ny


def _str(v, sti, *, paakrevd=False):
    if v is None or v == "":
        if paakrevd:
            raise SpecFeil(f"{sti}: mangler (påkrevd tekst)")
        return None
    if not isinstance(v, (str, int, float)):
        raise SpecFeil(f"{sti}: skal være tekst, fikk {type(v).__name__}")
    return str(v)


def _bool(v, sti, standard=False):
    if v is None:
        return standard
    if not isinstance(v, bool):
        raise SpecFeil(f"{sti}: skal være true/false")
    return v


def _tall(v, sti):
    if v is None or v == "":
        return None
    if isinstance(v, bool):
        raise SpecFeil(f"{sti}: skal være et tall, fikk true/false")
    if isinstance(v, (int, float)):
        return v
    if isinstance(v, str) and re.fullmatch(r"\s*[−\-]?[\d  .]*\d(?:,\d+)?\s*", v):
        return parse_amount(v)
    raise SpecFeil(f"{sti}: skal være et tall, fikk «{v}»")


def _verdi(v, kol, sti, ctx: _Ctx):
    """Tvinger én celleverdi til kolonnetypen."""
    t = kol["type"]
    if v is None or v == "":
        return None
    if t == "tekst":
        if isinstance(v, (dict, list)):
            raise SpecFeil(f"{sti}: skal være tekst")
        return ctx.mask(str(v), kol.get("redact"))
    if t == "heltall":
        if isinstance(v, bool):
            raise SpecFeil(f"{sti}: skal være heltall")
        if isinstance(v, int):
            return v
        if isinstance(v, float) and v.is_integer():
            return int(v)
        if isinstance(v, str):
            return int(v) if v.strip().isdigit() else v
        raise SpecFeil(f"{sti}: skal være heltall, fikk «{v}»")
    if t in ("belop", "antall", "prosent"):
        return _tall(v, sti)
    if t == "dato":
        d = til_dato(v)
        if isinstance(d, str):
            raise SpecFeil(f"{sti}: ugyldig dato «{v}» (bruk ÅÅÅÅ-MM-DD eller dd.mm.åååå)")
        return d
    if t == "status":
        s = str(v).strip().upper()
        if s not in tema.STATUSER:
            raise SpecFeil(f"{sti}: ukjent status «{v}» (gyldige: {', '.join(tema.STATUSER)})")
        return s
    raise SpecFeil(f"{sti}: ukjent type {t}")


def _kolonner(liste, sti, *, ekstra=()) -> list[dict]:
    if not isinstance(liste, list) or not liste:
        raise SpecFeil(f"{sti}: skal være en ikke-tom liste")
    ut, sett = [], set()
    for i, k in enumerate(liste):
        ks = f"{sti}[{i}]"
        if isinstance(k, str):
            k = {"id": k}
        if not isinstance(k, dict):
            raise SpecFeil(f"{ks}: skal være et objekt eller en id")
        ukjent = set(k) - {"id", "tekst", "type", "bredde", "just", "vis", "lopende", "redact", *ekstra}
        if ukjent:
            raise SpecFeil(f"{ks}: ukjente felt {sorted(ukjent)}")
        kid = _str(k.get("id"), f"{ks}.id", paakrevd=True)
        if kid in sett:
            raise SpecFeil(f"{ks}.id: «{kid}» brukt to ganger")
        sett.add(kid)
        typ = k.get("type") or ("belop" if k.get("lopende") else "tekst")
        if typ not in tema.TYPER:
            raise SpecFeil(f"{ks}.type: ukjent type «{typ}» (gyldige: {', '.join(tema.TYPER)})")
        just = k.get("just") or tema.STANDARD_JUST[typ]
        if just not in ("l", "r", "c"):
            raise SpecFeil(f"{ks}.just: skal være l, r eller c")
        vis = k.get("vis") or "begge"
        if vis not in ("begge", "excel", "pdf"):
            raise SpecFeil(f"{ks}.vis: skal være begge, excel eller pdf")
        bredde = k.get("bredde", tema.STANDARD_BREDDE[typ])
        if not isinstance(bredde, (int, float)) or bredde <= 0:
            raise SpecFeil(f"{ks}.bredde: skal være et positivt tall")
        ny = {"id": kid, "tekst": _str(k.get("tekst"), f"{ks}.tekst") or kid.capitalize(), "type": typ,
              "bredde": bredde, "just": just, "vis": vis, "redact": k.get("redact"), "lopende": None}
        if ny["redact"] is not None:
            _bool(ny["redact"], f"{ks}.redact")
        for e in ekstra:
            if e in k:
                ny[e] = k[e]
        if k.get("lopende") is not None:
            lop = k["lopende"]
            if not isinstance(lop, dict):
                raise SpecFeil(f"{ks}.lopende: skal være {{start, pluss, minus}}")
            ukjent = set(lop) - {"start", "pluss", "minus"}
            if ukjent:
                raise SpecFeil(f"{ks}.lopende: ukjente felt {sorted(ukjent)}")
            ny["lopende"] = {"start": _tall(lop.get("start", 0), f"{ks}.lopende.start") or 0,
                             "pluss": lop.get("pluss"), "minus": lop.get("minus")}
            if not (lop.get("pluss") or lop.get("minus")):
                raise SpecFeil(f"{ks}.lopende: oppgi pluss og/eller minus (kolonne-id)")
        ut.append(ny)
    return ut


def _rader(rader, kolonner, sti, ctx: _Ctx, *, tillat=("_fet",)) -> list[dict]:
    if rader is None:
        return []
    if not isinstance(rader, list):
        raise SpecFeil(f"{sti}: skal være en liste")
    kart = {k["id"]: k for k in kolonner}
    ut = []
    for i, r in enumerate(rader):
        rs = f"{sti}[{i}]"
        if isinstance(r, list):
            if len(r) != len(kolonner):
                raise SpecFeil(f"{rs}: {len(r)} verdier, men {len(kolonner)} kolonner")
            r = dict(zip(kart, r))
        if not isinstance(r, dict):
            raise SpecFeil(f"{rs}: skal være et objekt eller en liste")
        ukjent = set(r) - set(kart) - set(tillat)
        if ukjent:
            raise SpecFeil(f"{rs}: ukjent kolonne {sorted(ukjent)} (kolonnene er {list(kart)})")
        ny = {kid: _verdi(r.get(kid), kart[kid], f"{rs}.{kid}", ctx) for kid in kart if kid in r}
        if "_fet" in r:
            ny["_fet"] = _bool(r["_fet"], f"{rs}._fet")
        ut.append(ny)
    return ut


def _etikett_kol(kolonner, onsket, sti):
    ids = [k["id"] for k in kolonner]
    if onsket:
        if onsket not in ids:
            raise SpecFeil(f"{sti}: ukjent kolonne «{onsket}»")
        return onsket
    begge = [k for k in kolonner if k["vis"] == "begge"]
    for k in begge:
        if k["id"] == "tekst":
            return k["id"]
    for k in begge:
        if k["type"] == "tekst":
            return k["id"]
    return begge[0]["id"] if begge else ids[0]


def _sum(s, kolonner, sti, *, sammendrag=False):
    if s is None:
        return None
    if not isinstance(s, dict):
        raise SpecFeil(f"{sti}: skal være et objekt")
    ukjent = set(s) - {"etikett", "kolonner", "tell", "tell_kol", "etikett_kol", "skal_vaere", "skal_vaere_kol"}
    if ukjent:
        raise SpecFeil(f"{sti}: ukjente felt {sorted(ukjent)}")
    kart = {k["id"]: k for k in kolonner}
    kol = s.get("kolonner") or []
    for i, kid in enumerate(kol):
        if kid not in kart:
            raise SpecFeil(f"{sti}.kolonner[{i}]: ukjent kolonne «{kid}»")
        if kart[kid]["type"] not in _TALLTYPER:
            raise SpecFeil(f"{sti}.kolonner[{i}]: «{kid}» er ikke en tallkolonne")
    for felt in ("tell", "tell_kol", "skal_vaere_kol"):
        if s.get(felt) and s[felt] not in kart:
            raise SpecFeil(f"{sti}.{felt}: ukjent kolonne «{s[felt]}»")
    ny = {"etikett": _str(s.get("etikett"), f"{sti}.etikett") or ("Totalt" if sammendrag else "Sum"),
          "kolonner": list(kol), "tell": s.get("tell"), "tell_kol": s.get("tell_kol"),
          "etikett_kol": _etikett_kol(kolonner, s.get("etikett_kol"), f"{sti}.etikett_kol"),
          "skal_vaere": _tall(s.get("skal_vaere"), f"{sti}.skal_vaere"),
          "skal_vaere_kol": s.get("skal_vaere_kol") or (kol[0] if kol else None)}
    if ny["skal_vaere"] is not None and not ny["skal_vaere_kol"]:
        raise SpecFeil(f"{sti}.skal_vaere: krever minst én kolonne i sum.kolonner")
    return ny


def _flagg(d, sti, ny):
    for f in ("liten", "filter", "frys", "zebra", "uthev_avvik"):
        ny[f] = _bool(d.get(f), f"{sti}.{f}")
    return ny


def _tabell(t, sti, ctx: _Ctx) -> dict:
    if not isinstance(t, dict):
        raise SpecFeil(f"{sti}: skal være et objekt")
    ukjent = set(t) - {"kolonner", "rader", "ib", "ub", "sum", "kontrollsum", "etikett_kol",
                       "liten", "filter", "frys", "zebra", "uthev_avvik"}
    if ukjent:
        raise SpecFeil(f"{sti}: ukjente felt {sorted(ukjent)}")
    kolonner = _kolonner(t.get("kolonner"), f"{sti}.kolonner")
    kart = {k["id"]: k for k in kolonner}
    lopende = [k for k in kolonner if k["lopende"]]
    if len(lopende) > 1:
        raise SpecFeil(f"{sti}.kolonner: bare én kolonne kan ha «lopende»")
    for k in lopende:
        for felt in ("pluss", "minus"):
            ref = k["lopende"][felt]
            if ref and (ref not in kart or kart[ref]["type"] not in _TALLTYPER):
                raise SpecFeil(f"{sti}.kolonner[{kolonner.index(k)}].lopende.{felt}: «{ref}» er ikke en tallkolonne i tabellen")
    ny = {"kolonner": kolonner, "rader": _rader(t.get("rader"), kolonner, f"{sti}.rader", ctx),
          "etikett_kol": _etikett_kol(kolonner, t.get("etikett_kol"), f"{sti}.etikett_kol")}
    for felt in ("ib", "ub"):
        v = t.get(felt)
        if v is None:
            ny[felt] = None
            continue
        if not isinstance(v, dict):
            raise SpecFeil(f"{sti}.{felt}: skal være et objekt med celler")
        celler = {k: x for k, x in v.items() if k != "verdi"}
        ny[felt] = _rader([celler], kolonner, f"{sti}.{felt}", ctx)[0]
        ny[felt]["verdi"] = _tall(v.get("verdi"), f"{sti}.{felt}.verdi")
    if lopende and ny["ib"] is None:
        ny["ib"] = {ny["etikett_kol"]: "Inngående saldo", "verdi": None}
    ny["sum"] = _sum(t.get("sum"), kolonner, f"{sti}.sum")
    ks = t.get("kontrollsum")
    if ks is not None:
        if not lopende:
            raise SpecFeil(f"{sti}.kontrollsum: krever en kolonne med «lopende»")
        if not isinstance(ks, dict):
            raise SpecFeil(f"{sti}.kontrollsum: skal være {{tekst, tekst_avvik}}")
        ukjent = set(ks) - {"tekst", "tekst_avvik"}
        if ukjent:
            raise SpecFeil(f"{sti}.kontrollsum: ukjente felt {sorted(ukjent)}")
        ny["kontrollsum"] = {"tekst": ctx.mask(_str(ks.get("tekst"), f"{sti}.kontrollsum.tekst")),
                             "tekst_avvik": ctx.mask(_str(ks.get("tekst_avvik"), f"{sti}.kontrollsum.tekst_avvik"))}
    else:
        ny["kontrollsum"] = None
    return _flagg(t, sti, ny)


def _kontroller(k, sti, ctx: _Ctx) -> dict:
    if not isinstance(k, dict):
        raise SpecFeil(f"{sti}: skal være et objekt")
    ukjent = set(k) - {"etiketter", "rader", "antall_avvik", "liten"}
    if ukjent:
        raise SpecFeil(f"{sti}: ukjente felt {sorted(ukjent)}")
    et = k.get("etiketter") or {}
    rader = []
    for i, r in enumerate(k.get("rader") or []):
        rs = f"{sti}.rader[{i}]"
        if not isinstance(r, dict):
            raise SpecFeil(f"{rs}: skal være et objekt")
        ukjent = set(r) - {"navn", "beregning", "a", "b", "toleranse", "forklart", "kommentar", "antall"}
        if ukjent:
            raise SpecFeil(f"{rs}: ukjente felt {sorted(ukjent)}")
        rader.append({"navn": ctx.mask(_str(r.get("navn"), f"{rs}.navn", paakrevd=True)),
                      "beregning": ctx.mask(_str(r.get("beregning"), f"{rs}.beregning")),
                      "a": _tall(r.get("a"), f"{rs}.a"), "b": _tall(r.get("b"), f"{rs}.b"),
                      "toleranse": _tall(r.get("toleranse", 1), f"{rs}.toleranse") or 0,
                      "forklart": _bool(r.get("forklart"), f"{rs}.forklart"),
                      "kommentar": ctx.mask(_str(r.get("kommentar"), f"{rs}.kommentar")),
                      "antall": _bool(r.get("antall"), f"{rs}.antall")})
    if not rader:
        raise SpecFeil(f"{sti}.rader: minst én kontroll")
    return {"etiketter": {"a": _str(et.get("a"), f"{sti}.etiketter.a") or "Beregnet",
                          "b": _str(et.get("b"), f"{sti}.etiketter.b") or "Regnskap"},
            "rader": rader, "antall_avvik": _bool(k.get("antall_avvik"), f"{sti}.antall_avvik", True),
            "liten": _bool(k.get("liten"), f"{sti}.liten")}


def _sammendrag(s, sti, ctx: _Ctx) -> dict:
    if not isinstance(s, dict):
        raise SpecFeil(f"{sti}: skal være et objekt")
    ukjent = set(s) - {"av", "gruppe", "kolonner", "rader", "sum", "liten", "filter", "frys", "zebra", "uthev_avvik"}
    if ukjent:
        raise SpecFeil(f"{sti}: ukjente felt {sorted(ukjent)}")
    kolonner = _kolonner(s.get("kolonner"), f"{sti}.kolonner", ekstra=("tell", "summer"))
    for i, k in enumerate(kolonner):
        if k.get("tell") and k.get("summer"):
            raise SpecFeil(f"{sti}.kolonner[{i}]: enten «tell» eller «summer», ikke begge")
        if k.get("tell") and k["type"] not in ("antall", "heltall"):
            k["type"] = "antall"
    gruppe = _str(s.get("gruppe"), f"{sti}.gruppe", paakrevd=True)
    if gruppe not in [k["id"] for k in kolonner]:
        raise SpecFeil(f"{sti}.gruppe: «{gruppe}» er ikke en kolonne i sammendraget")
    beregnet = {k["id"] for k in kolonner if k.get("tell") or k.get("summer")}
    rader = _rader(s.get("rader"), [k for k in kolonner if k["id"] not in beregnet], f"{sti}.rader", ctx)
    ny = {"av": _str(s.get("av"), f"{sti}.av", paakrevd=True), "gruppe": gruppe, "kolonner": kolonner, "rader": rader,
          "etikett_kol": _etikett_kol(kolonner, None, f"{sti}"),
          "sum": _sum(s.get("sum"), kolonner, f"{sti}.sum", sammendrag=True)}
    return _flagg(s, sti, ny)


def _dokument(d) -> dict:
    if not isinstance(d, dict):
        raise SpecFeil("dokument: mangler (objekt med hva, klient, periode …)")
    ukjent = set(d) - {"hva", "tittel", "klient", "orgnr", "under", "periode", "periode_tekst", "utarbeidet",
                       "utarbeidet_av", "bunntekst", "sidetall", "personvern"}
    if ukjent:
        raise SpecFeil(f"dokument: ukjente felt {sorted(ukjent)}")
    hva = _str(d.get("hva"), "dokument.hva", paakrevd=True)
    under = d.get("under") or []
    if isinstance(under, str):
        under = [under]
    if not isinstance(under, list):
        raise SpecFeil("dokument.under: skal være en liste med tekst")
    pv = d.get("personvern") or {}
    if not isinstance(pv, dict):
        raise SpecFeil("dokument.personvern: skal være {\"redact\": true|false}")
    utarbeidet = _str(d.get("utarbeidet"), "dokument.utarbeidet") or i_dag()
    if not re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", utarbeidet):
        d_ = til_dato(utarbeidet)
        if isinstance(d_, str):
            raise SpecFeil("dokument.utarbeidet: bruk dd.mm.åååå")
        utarbeidet = d_.strftime("%d.%m.%Y")
    return {"hva": hva, "tittel": _str(d.get("tittel"), "dokument.tittel") or hva,
            "klient": _str(d.get("klient"), "dokument.klient", paakrevd=True),
            "orgnr": _str(d.get("orgnr"), "dokument.orgnr"),
            "under": [_str(x, f"dokument.under[{i}]") for i, x in enumerate(under) if x],
            "periode": _str(d.get("periode"), "dokument.periode", paakrevd=True),
            "periode_tekst": _str(d.get("periode_tekst"), "dokument.periode_tekst"),
            "utarbeidet": utarbeidet, "utarbeidet_av": _str(d.get("utarbeidet_av"), "dokument.utarbeidet_av"),
            "bunntekst": _str(d.get("bunntekst"), "dokument.bunntekst") or f"{tema.FORFATTER} · {hva} · {utarbeidet}",
            "sidetall": _bool(d.get("sidetall"), "dokument.sidetall", True),
            "personvern": {"redact": _bool(pv.get("redact"), "dokument.personvern.redact", True)}}


def valider(spec: dict) -> dict:
    """Validerer og normaliserer. Kaster SpecFeil med sti til første feil."""
    if not isinstance(spec, dict):
        raise SpecFeil("spec: skal være et JSON-objekt")
    if spec.get("_validert"):
        return spec
    ukjent = set(spec) - {"versjon", "dokument", "seksjoner", "$schema", "_kommentar"}
    if ukjent:
        raise SpecFeil(f"spec: ukjente felt {sorted(ukjent)} (gyldige: versjon, dokument, seksjoner)")
    if spec.get("versjon", 1) != 1:
        raise SpecFeil("versjon: bare 1 støttes")
    dok = _dokument(spec.get("dokument"))
    ctx = _Ctx(dok["personvern"]["redact"])
    seksjoner = spec.get("seksjoner")
    if not isinstance(seksjoner, list) or not seksjoner:
        raise SpecFeil("seksjoner: skal være en ikke-tom liste")
    ut, ider = [], set()
    for i, s in enumerate(seksjoner):
        ss = f"seksjoner[{i}]"
        if not isinstance(s, dict):
            raise SpecFeil(f"{ss}: skal være et objekt")
        ukjent = set(s) - {"id", "ark", "sideskift", "overskrift", "nivaa", "bar", "tekst", "boks", "punkter",
                           "merknad", *_INNHOLD}
        if ukjent:
            raise SpecFeil(f"{ss}: ukjente felt {sorted(ukjent)}")
        sid = _str(s.get("id"), f"{ss}.id") or f"s{i + 1}"
        if sid in ider:
            raise SpecFeil(f"{ss}.id: «{sid}» brukt to ganger")
        ider.add(sid)
        ark = _str(s.get("ark"), f"{ss}.ark") or "Rapport"
        if len(ark) > 31 or _ARK_ULOVLIG.search(ark):
            raise SpecFeil(f"{ss}.ark: «{ark}» – maks 31 tegn og ingen av []:*?/\\")
        nivaa = s.get("nivaa", 2)
        if nivaa not in (2, 3):
            raise SpecFeil(f"{ss}.nivaa: 2 eller 3")
        innhold = [k for k in _INNHOLD if s.get(k) is not None]
        if len(innhold) > 1:
            raise SpecFeil(f"{ss}: bare én av tabell, kontroller og sammendrag per seksjon")
        boks = s.get("boks")
        if boks is not None:
            if not isinstance(boks, dict) or boks.get("type", "konkl") not in ("konkl", "varsel"):
                raise SpecFeil(f"{ss}.boks: skal være {{\"type\": \"konkl\"|\"varsel\", \"tekst\": …}}")
            boks = {"type": boks.get("type", "konkl"), "tekst": ctx.mask(_str(boks.get("tekst"), f"{ss}.boks.tekst", paakrevd=True))}
        punkter = s.get("punkter") or []
        if not isinstance(punkter, list):
            raise SpecFeil(f"{ss}.punkter: skal være en liste med tekst")
        ny = {"id": sid, "ark": ark, "sideskift": _bool(s.get("sideskift"), f"{ss}.sideskift"),
              "overskrift": _str(s.get("overskrift"), f"{ss}.overskrift"), "nivaa": nivaa,
              "bar": _bool(s.get("bar"), f"{ss}.bar", None),
              "tekst": ctx.mask(_str(s.get("tekst"), f"{ss}.tekst")), "boks": boks,
              "punkter": [ctx.mask(_str(p, f"{ss}.punkter[{j}]", paakrevd=True)) for j, p in enumerate(punkter)],
              "merknad": ctx.mask(_str(s.get("merknad"), f"{ss}.merknad")),
              "tabell": None, "kontroller": None, "sammendrag": None}
        if s.get("tabell") is not None:
            ny["tabell"] = _tabell(s["tabell"], f"{ss}.tabell", ctx)
        elif s.get("kontroller") is not None:
            ny["kontroller"] = _kontroller(s["kontroller"], f"{ss}.kontroller", ctx)
        elif s.get("sammendrag") is not None:
            ny["sammendrag"] = _sammendrag(s["sammendrag"], f"{ss}.sammendrag", ctx)
        if not any(ny[k] for k in ("overskrift", "tekst", "boks", "punkter", "merknad", *_INNHOLD)):
            raise SpecFeil(f"{ss}: tom seksjon")
        ut.append(ny)
    # kryssreferanser: sammendrag.av
    tabeller = {s["id"]: s for s in ut if s["tabell"]}
    for i, s in enumerate(ut):
        sm = s["sammendrag"]
        if not sm:
            continue
        ss = f"seksjoner[{i}].sammendrag"
        if sm["av"] not in tabeller:
            raise SpecFeil(f"{ss}.av: fant ingen seksjon med id «{sm['av']}» og tabell")
        kilde = {k["id"]: k for k in tabeller[sm["av"]]["tabell"]["kolonner"]}
        if sm["gruppe"] not in kilde:
            raise SpecFeil(f"{ss}.gruppe: «{sm['gruppe']}» finnes ikke i tabellen «{sm['av']}»")
        if kilde[sm["gruppe"]]["vis"] == "pdf":
            raise SpecFeil(f"{ss}.gruppe: «{sm['gruppe']}» må vises i Excel (vis: begge)")
        for j, k in enumerate(sm["kolonner"]):
            ref = k.get("summer") or (k.get("tell") if isinstance(k.get("tell"), str) else None)
            if ref and ref not in kilde:
                raise SpecFeil(f"{ss}.kolonner[{j}]: «{ref}» finnes ikke i tabellen «{sm['av']}»")
            if k.get("summer") and kilde[ref]["type"] not in _TALLTYPER:
                raise SpecFeil(f"{ss}.kolonner[{j}].summer: «{ref}» er ikke en tallkolonne")
    return {"versjon": 1, "dokument": dok, "seksjoner": ut, "_validert": True, "_redigert": ctx.antall}
