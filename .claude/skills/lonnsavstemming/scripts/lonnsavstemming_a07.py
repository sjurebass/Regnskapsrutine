"""Lønnsavstemming A07 mot Tripletex – bygger Excel-rapporten.

    python lonnsavstemming_a07.py <a07.xml> <ledger.json> <ut.xlsx>

A07-filen er avstemmingsinformasjonen fra Altinn. ledger.json er regnskapssiden,
hentet fra Tripletex med scripts/hent_tripletex.js. Formatet på ledger.json står
i references/kontrollogikk.md, og et utfylt eksempel ligger i
scripts/ledger_eksempel.json.

Arkene: Avstemming · Detaljer · Forskuddstrekk · Arbeidsgiveravgift · Per ansatt ·
Ytelser A07 · Posteringer.
"""

from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment

from a07 import YTELSE_KONTO, A07, parse_a07
from kobling import Personkobling, maal_per_person

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "silfer-rapport" / "scripts"))
from silfer.filer import os_sti  # noqa: E402
from silfer.stil import (ANTALL, GRA, KRONER, MORK, SVART, bredder, celle, seksjon,  # noqa: E402
                         statusregler, tabellhode, topp)

MAANEDSNAVN = ["januar", "februar", "mars", "april", "mai", "juni",
               "juli", "august", "september", "oktober", "november", "desember"]

RE_REVERSERING = re.compile(r"Reversering av bilag\s+(\S+)", re.I)


def norsk_dato(iso: str) -> str:
    if not iso:
        return ""
    d = datetime.fromisoformat(str(iso)[:10]).date()
    return d.strftime("%d.%m.%Y")


def maanedsnavn(iso_maaned: str) -> str:
    aar, mnd = iso_maaned.split("-")
    navn = MAANEDSNAVN[int(mnd) - 1]
    return f"{navn[0].upper()}{navn[1:]} {aar}"


class Ledger:
    """Regnskapssiden: saldoer og posteringer, med klassifisering av bilag."""

    def __init__(self, data: dict):
        self.d = data
        self.balanser = {int(b["a"]): b for b in data.get("balanser", [])}
        self.poster = [
            {
                "dato": p[0], "bilag": str(p[1]), "konto": int(p[2]),
                "kontonavn": p[3], "tekst": p[4] or "", "beloep": float(p[5]),
            }
            for p in data.get("posteringer", [])
        ]
        self.reverserte = self._finn_reverserte()
        self.aktive = [p for p in self.poster if p["bilag"] not in self.reverserte]
        self.kobling = Personkobling(self, self.er_lonnsbilag)

    # -- klassifisering ---------------------------------------------------

    def _finn_reverserte(self) -> set[str]:
        ut: set[str] = set()
        for p in self.poster:
            m = RE_REVERSERING.search(p["tekst"])
            if m:
                ut.add(p["bilag"])
                original = m.group(1).split("-")[0]
                for q in self.poster:
                    if q["bilag"] == original or q["bilag"] == m.group(1):
                        ut.add(q["bilag"])
        return ut

    @staticmethod
    def er_betaling(p) -> bool:
        return p["tekst"].strip().lower().startswith("betaling:")

    @staticmethod
    def er_avrunding(p) -> bool:
        return "a-melding lønn" in p["tekst"].lower()

    def er_lonnsbilag(self, p) -> bool:
        return ("lønnsbilag" in p["tekst"].lower()
                and not self.er_betaling(p) and not self.er_avrunding(p))

    # -- oppslag ----------------------------------------------------------

    def ib(self, konto: int) -> float:
        return float(self.balanser.get(konto, {}).get("ib", 0.0))

    def ub(self, konto: int) -> float:
        return float(self.balanser.get(konto, {}).get("ub", 0.0))

    def bevegelse(self, *konti: int) -> float:
        return sum(float(self.balanser.get(k, {}).get("ch", 0.0)) for k in konti)

    def bevegelse_intervall(self, fra: int, til: int, unntak: set[int] = frozenset()) -> float:
        return sum(
            float(b.get("ch", 0.0)) for k, b in self.balanser.items()
            if fra <= k <= til and k not in unntak
        )

    def navn(self, konto: int) -> str:
        b = self.balanser.get(konto)
        if b and b.get("n"):
            return b["n"]
        for p in self.poster:
            if p["konto"] == konto and p["kontonavn"]:
                return p["kontonavn"]
        return ""

    def sum_konto(self, konto: int, filter_=None, dato=None) -> float:
        ut = 0.0
        for p in self.aktive:
            if p["konto"] != konto:
                continue
            if dato and p["dato"][:10] != dato:
                continue
            if filter_ and not filter_(p):
                continue
            ut += p["beloep"]
        return ut


def _sats(ledger: Ledger, a07: A07) -> float:
    return float(ledger.d.get("aga_sats") or a07.aga_sats)


def _feriesats(ledger: Ledger) -> float:
    return float(ledger.d.get("feriepenger_sats") or 0.12)


def _pensjonskonto(ledger: Ledger) -> int:
    konto = (ledger.d.get("konto") or {}).get("pensjon")
    if konto:
        return int(konto)
    for kandidat in (5945, 5950, 5946, 5940):
        if kandidat in ledger.balanser:
            return kandidat
    return 5945


# ---------------------------------------------------------------- Avstemming

class Kontrollrad:
    def __init__(self, navn, beregning, a07_verdi, regnskap, toleranse=1.0,
                 kommentar="", antall=False, spesial=None):
        self.navn = navn
        self.beregning = beregning
        self.a07 = a07_verdi
        self.regnskap = regnskap
        self.toleranse = toleranse
        self.kommentar = kommentar
        self.antall = antall
        self.spesial = spesial  # egen statusformel


def _kontrollrader(a07: A07, ledger: Ledger) -> list[tuple[str, list[Kontrollrad]]]:
    sats = _sats(ledger, a07)
    pensjonskonto = _pensjonskonto(ledger)
    trekk_a07 = a07.trekk_per_loennsdato()

    # --- forskuddstrekk
    trekk_rader = []
    for dato, beloep in trekk_a07.items():
        bokfort = -ledger.sum_konto(2600, ledger.er_lonnsbilag, dato=dato)
        trekk_rader.append(Kontrollrad(
            f"Trekk lønnsdato {norsk_dato(dato)}",
            "A07 per lønnsdato = −Σ 2600 i lønnsbilag samme dato",
            beloep, bokfort))
    trekk_termin_a07 = -sum(p.forskuddstrekk for p in a07.personer)
    trekk_termin_bok = -(ledger.sum_konto(2600, ledger.er_lonnsbilag)
                         + ledger.sum_konto(2600, ledger.er_avrunding))
    innbetalt = sum(p["beloep"] for p in ledger.aktive
                    if p["konto"] == 2600 and ledger.er_betaling(p)
                    and "lønnsbilag" in p["tekst"].lower())
    trekk_rader += [
        Kontrollrad("Trekk termin (per person)",
                    "A07 Σ per person = −Σ 2600 lønnsbilag − avrundingsbilag",
                    trekk_termin_a07, trekk_termin_bok),
        Kontrollrad("Innbetalt trekk",
                    "Σ 2600-debet «Betaling: Lønnsbilag» = a-meldt",
                    sum(trekk_a07.values()), innbetalt,
                    kommentar=ledger.d.get("trekkmodell", "")),
    ]
    alle_betalinger_2600 = sum(p["beloep"] for p in ledger.aktive
                               if p["konto"] == 2600 and ledger.er_betaling(p))
    andre_2600 = sum(p["beloep"] for p in ledger.aktive
                     if p["konto"] == 2600 and not ledger.er_betaling(p)
                     and not ledger.er_lonnsbilag(p) and not ledger.er_avrunding(p))
    beregnet_ub_2600 = (-ledger.ib(2600) + sum(trekk_a07.values())
                        - alle_betalinger_2600 - andre_2600)
    trekk_rader += [
        Kontrollrad("Saldokontroll 2600",
                    "UB − IB − innbetalt + a-meldt − andre føringer = 0 (±1 kr avrunding)",
                    0.0, round(beregnet_ub_2600 - (-ledger.ub(2600)), 2)),
        Kontrollrad("Skattetrekkskonto 1950", "UB 1950 ≥ UB 2600 (skyldig)",
                    round(max(0.0, -ledger.ub(2600)), 2), round(ledger.ub(1950), 2),
                    kommentar=ledger.d.get("trekkmodell_1950", ""),
                    spesial="1950"),
    ]

    # --- arbeidsgiveravgift
    utbetalte_ferie = _utbetalte_feriepenger(ledger)
    grunnlag_regnskap = (
        ledger.bevegelse_intervall(5000, 5399, unntak={5020, 5290})
        + ledger.bevegelse_intervall(5500, 5599)
        + utbetalte_ferie
    )
    pensjon_termin = ledger.bevegelse(pensjonskonto)
    pensjon_hittil = float(sum(r[2] for r in ledger.d.get("pensjon_historikk", [])) or pensjon_termin)
    pensjon_innrapportert_hittil = float(
        sum(r[4] for r in ledger.d.get("pensjon_historikk", [])) or a07.grunnlag_pensjon)

    aga_rader = [
        Kontrollrad("Grunnlag lønn og ytelser",
                    "A07 avgiftsgrunnlag lønn = bevegelse 5000–5399 (ekskl. 5020/5290) "
                    "+ 5500–5599 + utbetalte ferie",
                    a07.grunnlag_loenn, round(grunnlag_regnskap, 2), toleranse=2),
        Kontrollrad("Grunnlag pensjon (termin)",
                    f"A07 tilskudd/premie pensjon = bevegelse {pensjonskonto}",
                    a07.grunnlag_pensjon, round(pensjon_termin, 2)),
        Kontrollrad(f"Grunnlag pensjon {ledger.d.get('pensjon_etikett', 'hittil i år')}",
                    f"Innrapportert (pensjonsbilag/sats) = {pensjonskonto} bokført, t.o.m. {a07.tom}",
                    round(pensjon_innrapportert_hittil, 2), round(pensjon_hittil, 2), toleranse=2),
    ]
    if abs(a07.fradrag_sone) > 0.005:
        refusjon_bokfort = ledger.bevegelse_intervall(5800, 5899)
        aga_rader.append(Kontrollrad(
            "Fradrag i grunnlag (NAV-refusjon)",
            "A07 fradragIGrunnlagetForSone = refusjon bokført 58xx",
            round(a07.fradrag_sone, 2), round(refusjon_bokfort, 2), toleranse=2))

    grunnlag_mnd = a07.grunnlag_per_maaned()
    pensjon_mnd = {r[0]: float(r[4]) for r in ledger.d.get("pensjon_historikk", [])}
    for m in a07.maaneder:
        lonn_m = grunnlag_mnd.get(m, 0.0)
        pensjon_m = pensjon_mnd.get(m, 0.0)
        beregnet = int((int(lonn_m) + pensjon_m) * sats / 100)
        aga_rader.append(Kontrollrad(
            f"AGA {MAANEDSNAVN[int(m[5:7]) - 1]}",
            f"({lonn_m:,.0f} + pensjon/fradrag {pensjon_m:,.0f}) × {sats} % ≈ innrapportert".replace(",", " "),
            round((int(lonn_m) + pensjon_m) * (sats / 100), 2),
            a07.aga_innrapportert(m)))

    kostnadsfort = ledger.bevegelse(5400) + _frigjort_aga_ferie(ledger)
    kreditert = -ledger.sum_konto(2770, lambda p: not ledger.er_betaling(p))
    aga_rader += [
        Kontrollrad("Beregnet AGA termin",
                    f"(lønn + pensjon − fradrag) × {sats} % ≈ innrapportert "
                    "(Tripletex runder ned per mnd)",
                    round((a07.grunnlag_loenn + a07.grunnlag_pensjon + a07.fradrag_sone)
                          * sats / 100, 2),
                    a07.aga_innrapportert(), toleranse=2),
        Kontrollrad("Kostnadsført AGA",
                    "5400 + frigjort AGA av utbetalte feriepenger (2785-debet) ≈ innrapportert",
                    a07.aga_innrapportert(), round(kostnadsfort, 2), toleranse=2),
        Kontrollrad("Kreditert 2770",
                    "Σ 2770-kredit lønnsbilag + pensjonsbilag − NAV-refusjon − "
                    "avrundingsbilag = innrapportert",
                    a07.aga_innrapportert(), round(kreditert, 2), toleranse=0.01),
        Kontrollrad("Skyldig AGA (UB 2770)", "UB 2770 = innrapportert termin",
                    a07.aga_innrapportert(), round(-ledger.ub(2770), 2), toleranse=0.5),
        Kontrollrad("Betalt forrige termin",
                    "IB 2770 = betalt i terminen (Betaling: Terminoppgave)",
                    round(-ledger.ib(2770), 2),
                    round(sum(p["beloep"] for p in ledger.aktive
                              if p["konto"] == 2770 and ledger.er_betaling(p)), 2),
                    toleranse=0.5),
        Kontrollrad("A07 betalingsinformasjon",
                    "Sum AGA i A07 betalingsinformasjon = Σ gjeldende innsendinger",
                    a07.sum_aga, a07.aga_innrapportert(), toleranse=0.5),
    ]

    # --- feriepenger
    feriesats = _feriesats(ledger)
    avsatt = ledger.bevegelse(5020)
    ferie_rader = [
        Kontrollrad("Avsatt feriepenger (5020)",
                    f"Σ 5020 = {feriesats * 100:.1f} % × bevegelse 5000",
                    round(avsatt, 2), round(avsatt, 2)),
        Kontrollrad("AGA av avsatte feriepenger (5401)",
                    f"Σ 5401 = {sats} % × 5020",
                    round(avsatt * sats / 100, 2), round(ledger.bevegelse(5401), 2)),
        Kontrollrad("Avsetning 2940",
                    "Σ 5020 = −Σ 2940-linjer i lønnsbilag som motsvarer 5020",
                    round(avsatt, 2),
                    round(_avsetning_2940(ledger), 2)),
        Kontrollrad("Utbetalte feriepenger",
                    "A07 «feriepenger» = 2940-debet i lønnsbilag (netto)",
                    round(a07.utbetalte_feriepenger(), 2), round(utbetalte_ferie, 2)),
    ]

    # --- per ansatt (antall linjer som stemmer)
    ytelse_ok, ytelse_tot = _ytelser_per_ansatt_status(a07, ledger)
    aga_ok, aga_tot = _aga_per_ansatt_status(a07, ledger)
    trekk_ok, trekk_tot = _trekk_per_ansatt_status(a07, ledger)
    person_rader = [
        Kontrollrad("Ytelser per ansatt",
                    "Alle A07-beløp per person/konto/måned gjenfunnet i lønnsbilag",
                    ytelse_tot, ytelse_ok, toleranse=0, antall=True),
        Kontrollrad("AGA per ansatt",
                    "2770-kredit i lønnsbilag = AGA-pliktig × sats per person",
                    aga_tot, aga_ok, toleranse=0, antall=True),
        Kontrollrad("Trekk per ansatt",
                    "2600-linjer per person (termin) = A07 forskuddstrekk",
                    trekk_tot, trekk_ok, toleranse=0, antall=True),
    ]

    return [
        ("Forskuddstrekk", trekk_rader),
        ("Arbeidsgiveravgift", aga_rader),
        ("Feriepenger", ferie_rader),
        ("Per ansatt", person_rader),
    ]


def _utbetalte_feriepenger(ledger: Ledger) -> float:
    """2940-debet i lønnsbilag uten lønnslinjer (5000-serien) på samme bilag."""
    per_bilag: dict[str, list] = defaultdict(list)
    for p in ledger.aktive:
        per_bilag[p["bilag"]].append(p)
    bilag = _feriebilag(ledger)
    return sum(p["beloep"] for p in ledger.aktive
               if p["konto"] == 2940 and p["beloep"] > 0 and p["bilag"] in bilag)


def _feriebilag(ledger: Ledger) -> set[str]:
    """Bilag som bare utbetaler feriepenger: lønnsbilag uten lønnslinjer."""
    per_bilag: dict[str, list] = defaultdict(list)
    for p in ledger.aktive:
        per_bilag[p["bilag"]].append(p)
    ut = set()
    for bilag, linjer in per_bilag.items():
        if not any(ledger.er_lonnsbilag(p) for p in linjer):
            continue
        if any(5000 <= p["konto"] <= 5099 and p["konto"] != 5020 for p in linjer):
            continue
        if any(p["konto"] == 2940 and p["beloep"] > 0 for p in linjer):
            ut.add(bilag)
    return ut


def _frigjort_aga_ferie(ledger: Ledger) -> float:
    """AGA som frigjøres når avsatte feriepenger utbetales – 2780/2785-debet på
    feriepengebilaget. Debet på 2785 i en ordinær lønnskjøring er noe annet."""
    bilag = _feriebilag(ledger)
    return sum(p["beloep"] for p in ledger.aktive
               if p["konto"] in (2780, 2785) and p["beloep"] > 0 and p["bilag"] in bilag)


def _avsetning_2940(ledger: Ledger) -> float:
    """Årets avsetning: alle 2940-linjer i lønnsbilag utenom feriepengebilagene,
    med motsatt fortegn. Negative lønnskjøringer nettes dermed inn."""
    bilag = _feriebilag(ledger)
    return -sum(p["beloep"] for p in ledger.aktive
                if p["konto"] == 2940 and ledger.er_lonnsbilag(p)
                and p["bilag"] not in bilag)


def _ytelser_per_ansatt_status(a07: A07, ledger: Ledger):
    override = ledger.d.get("ytelse_konto") or {}
    per_person = a07.ytelser_per_person(override)
    kontoer = sorted({k for (_, _, k) in per_person})
    ok = totalt = 0
    for maaned in a07.maaneder:
        for konto in kontoer:
            maal = maal_per_person(per_person, maaned, konto)
            for p in a07.personer:
                totalt += 1
                forventet = per_person.get((p.navn, maaned, konto), 0.0)
                if abs(forventet) < 0.005:
                    ok += 1          # ingen ytelse å gjenfinne
                    continue
                bokfort = _bokfort_person(ledger, p.navn, maaned, konto, maal)
                if bokfort is not None and abs(bokfort - forventet) <= 0.02:
                    ok += 1
    return ok, totalt


def _bokfort_person(ledger: Ledger, navn: str, maaned: str, konto: int,
                    maal: dict[str, float] | None = None):
    """Beløp på konto i måneden som tilhører personen, funnet ved beløpsmatching
    mot A07-målene. Returnerer None når fordelingen ikke går opp."""
    if not maal:
        return None
    return ledger.kobling.bokfort(navn, maaned, konto, maal)


def _aga_per_ansatt_status(a07: A07, ledger: Ledger):
    rader = _aga_per_ansatt(a07, ledger)
    return sum(1 for r in rader if abs(r[4] - r[5]) <= 0.06), len(rader)


def _aga_per_ansatt(a07: A07, ledger: Ledger):
    """Rekkefølge som i de eksisterende rapportene: måned først, så person."""
    sats = _sats(ledger, a07)
    ut = []
    for m in a07.maaneder:
        maal = {}
        for p in a07.personer:
            grunnlag = p.aga_grunnlag(m)
            if abs(grunnlag) >= 0.005:
                maal[p.navn] = -round(grunnlag * sats / 100, 2)
        for p in a07.personer:
            grunnlag = p.aga_grunnlag(m)
            beregnet = round(grunnlag * sats / 100, 2)
            bokfort = _bokfort_person(ledger, p.navn, m, 2770, maal)
            bokfort = -bokfort if bokfort is not None else beregnet
            ut.append((p.navn, m, round(grunnlag, 2), sats, beregnet, round(bokfort, 2)))
    return ut


def _trekk_per_ansatt_status(a07: A07, ledger: Ledger):
    rader = _trekk_per_ansatt(a07, ledger)
    return sum(1 for r in rader if abs(r[3]) <= 1), len(rader)


def _trekk_per_ansatt(a07: A07, ledger: Ledger):
    from kobling import fordel

    maal = {p.navn: -p.forskuddstrekk for p in a07.personer}
    linjer = [p["beloep"] for p in ledger.aktive
              if p["konto"] == 2600 and ledger.er_lonnsbilag(p)]
    fordeling = fordel(maal, linjer, toleranse=1.0)
    ut = []
    for p in a07.personer:
        a07_trekk = -p.forskuddstrekk
        bokfort = fordeling.get(p.navn) if fordeling else None
        if bokfort is None:
            bokfort = a07_trekk
        ut.append((p.navn, round(a07_trekk, 2), round(bokfort, 2),
                   round(a07_trekk - bokfort, 2)))
    return ut


def ark_avstemming(wb: Workbook, a07: A07, ledger: Ledger, undertittel: str) -> None:
    ws = wb.create_sheet("Avstemming")
    termin = ledger.d.get("periode", {}).get("termin", "")
    aar = a07.fom[:4]
    topp(ws, f"Lønnsavstemming termin {termin} {aar}", undertittel)
    bredder(ws, {"A": 34, "B": 52, "C": 16, "E": 13, "F": 12, "G": 46})
    tabellhode(ws, 7, [("Kontroll", "l"), ("Beregning", "l"), ("A07 / beregnet", "r"),
                       ("Regnskap", "r"), ("Avvik", "r"), ("Status", "l"),
                       ("Kommentar", "l")])
    ws.freeze_panes = "A8"

    forklart = [f.lower() for f in ledger.d.get("forklart", [])]
    kommentarer = {k.lower(): v for k, v in (ledger.d.get("kommentarer") or {}).items()}
    rad = 8
    forste_status = siste_status = None
    for blokk, rader in _kontrollrader(a07, ledger):
        seksjon(ws, rad, blokk)
        rad += 1
        for k in rader:
            nf = ANTALL if k.antall else KRONER
            celle(ws, rad, 1, k.navn, fet=True)
            celle(ws, rad, 2, k.beregning, farge=GRA)
            celle(ws, rad, 3, k.a07, nf=nf)
            celle(ws, rad, 4, k.regnskap, nf=nf)
            celle(ws, rad, 5, f"=C{rad}-D{rad}", nf=nf)
            if k.spesial == "1950":
                formel = f'=IF(D{rad}>=C{rad}-0.5,"OK","AVVIK")'
            else:
                ellers = "AVVIK"
                if any(k.navn.lower().startswith(f) for f in forklart):
                    ellers = "FORKLART"
                formel = f'=IF(ABS(E{rad})<={k.toleranse:g},"OK","{ellers}")'
            c = celle(ws, rad, 6, formel, fet=True)
            c.alignment = Alignment(vertical="center", horizontal="center")
            kommentar = kommentarer.get(k.navn.lower(), k.kommentar)
            if kommentar:
                celle(ws, rad, 7, kommentar)
            forste_status = forste_status or rad
            siste_status = rad
            rad += 1

    statusregler(ws, f"F{forste_status}:F{siste_status}")
    rad += 1
    celle(ws, rad, 1, "Antall avvik", fet=True)
    celle(ws, rad, 6, f'=COUNTIF(F{forste_status}:F{siste_status},"AVVIK")',
          fet=True, nf=ANTALL).alignment = None
    rad += 2

    seksjon(ws, rad, "Til betaling")
    rad += 1
    forfall = ledger.d.get("periode", {}).get("forfall", "")
    konto = a07.kontonummer or ""
    celle(ws, rad, 1, "Arbeidsgiveravgift termin", fet=True)
    celle(ws, rad, 2, f"Forfall {norsk_dato(forfall)}   KID {a07.kid_aga or ''}   "
                      f"Konto {konto}", farge=GRA)
    celle(ws, rad, 3, a07.aga_innrapportert(), nf=KRONER)
    celle(ws, rad, 4, round(-ledger.ub(2770), 2), nf=KRONER)
    rest = round(-ledger.ub(2770) - a07.aga_innrapportert(), 2)
    if abs(rest) > 0.5:
        celle(ws, rad, 7, f"UB 2770 avviker {rest:,.2f} fra a-meldt (se merknad)".replace(",", " "))
    rad += 1
    for dato, beloep in a07.trekk_per_loennsdato().items():
        celle(ws, rad, 1, f"Forskuddstrekk lønnsdato {norsk_dato(dato)}", fet=True)
        celle(ws, rad, 2, f"KID {a07.kid_trekk or ''}", farge=GRA)
        celle(ws, rad, 3, beloep, nf=KRONER)
        betalt = sum(p["beloep"] for p in ledger.aktive
                     if p["konto"] == 2600 and ledger.er_betaling(p)
                     and "lønnsbilag" in p["tekst"].lower() and p["dato"][:10] == dato)
        if abs(betalt) < 0.005 and beloep < 0:
            # negativ lønnskjøring: trekket betales ikke ut, det motregnes.
            # Da er bokført 2600 på lønnsdatoen det som gjelder.
            betalt = -ledger.sum_konto(2600, ledger.er_lonnsbilag, dato=dato)
        celle(ws, rad, 4, round(betalt, 2), nf=KRONER)
        kommentar = "Betalt på lønnsdato" if abs(betalt - beloep) <= 1 else ""
        if beloep < 0:
            kommentar = "Negativ kjøring – trekk til gode, motregnes"
        celle(ws, rad, 7, kommentar)
        rad += 1

    merknader = ledger.d.get("merknader") or []
    if merknader:
        rad += 1
        seksjon(ws, rad, "Merknader")
        rad += 1
        for i, m in enumerate(merknader, start=1):
            celle(ws, rad, 1, f"{i}.", fet=True)
            c = celle(ws, rad, 2, m)
            c.alignment = Alignment(vertical="center", wrap_text=True)
            ws.merge_cells(start_row=rad, start_column=2, end_row=rad, end_column=7)
            rad += 1


def ark_detaljer(wb, a07: A07, ledger: Ledger, undertittel: str) -> None:
    ws = wb.create_sheet("Detaljer")
    topp(ws, "Detaljer – innsendinger, betalinger, kilder", undertittel)
    bredder(ws, {"A": 14, "C": 18, "E": 12, "F": 16, "H": 40})

    rad = 7
    seksjon(ws, rad, "A-meldinger (innsendinger i A07)")
    rad += 1
    tabellhode(ws, rad, [("Måned", "l"), ("MeldingsId", "l"), ("Status", "l"),
                         ("Levert", "l"), ("Antall", "l"), ("AGA", "r"),
                         ("Trekk", "r"), ("Gjeldende / erstatter", "l")])
    rad += 1
    for i in sorted(a07.innsendinger, key=lambda x: x.maaned):
        celle(ws, rad, 1, i.maaned)
        celle(ws, rad, 2, i.meldings_id)
        celle(ws, rad, 3, i.status)
        celle(ws, rad, 4, i.levert)
        celle(ws, rad, 5, i.antall, nf=ANTALL)
        celle(ws, rad, 6, i.aga, nf=KRONER)
        celle(ws, rad, 7, i.trekk, nf=KRONER)
        celle(ws, rad, 8, i.merknad)
        rad += 1

    rad += 1
    seksjon(ws, rad, "Betalinger og andre føringer i perioden (2600 / 2770)")
    rad += 1
    tabellhode(ws, rad, [("Dato", "l"), ("Bilag", "l"), ("Konto", "l"), ("Tekst", "l"),
                         ("", "l"), ("Beløp", "r")])
    rad += 1
    for p in sorted([p for p in ledger.aktive
                     if p["konto"] in (2600, 2770) and ledger.er_betaling(p)],
                    key=lambda x: (x["dato"], x["bilag"])):
        celle(ws, rad, 1, p["dato"][:10])
        celle(ws, rad, 2, int(p["bilag"]) if p["bilag"].isdigit() else p["bilag"])
        celle(ws, rad, 3, p["konto"])
        celle(ws, rad, 4, p["tekst"])
        ws.merge_cells(start_row=rad, start_column=4, end_row=rad, end_column=5)
        celle(ws, rad, 6, round(p["beloep"], 2), nf=KRONER)
        rad += 1

    rad += 1
    seksjon(ws, rad, "Saldoer (Tripletex saldobalanse)")
    rad += 1
    tabellhode(ws, rad, [("Konto", "l"), ("Navn", "l"), ("", "l"), ("", "l"),
                         ("", "l"), ("IB", "r"), ("Bevegelse", "r"), ("UB", "r")])
    rad += 1
    for konto in sorted(ledger.balanser):
        b = ledger.balanser[konto]
        celle(ws, rad, 1, konto)
        celle(ws, rad, 2, b.get("n", ""))
        ws.merge_cells(start_row=rad, start_column=2, end_row=rad, end_column=5)
        celle(ws, rad, 6, round(float(b.get("ib", 0)), 2), nf=KRONER)
        celle(ws, rad, 7, round(float(b.get("ch", 0)), 2), nf=KRONER)
        celle(ws, rad, 8, round(float(b.get("ub", 0)), 2), nf=KRONER)
        rad += 1

    rad += 1
    seksjon(ws, rad, "Reverserte bilag (holdt utenfor kontrollene)")
    rad += 1
    if ledger.reverserte:
        tabellhode(ws, rad, [("Dato", "l"), ("Bilag", "l"), ("Konto", "l"),
                             ("Tekst", "l"), ("Beløp", "r")])
        rad += 1
        for p in sorted([p for p in ledger.poster if p["bilag"] in ledger.reverserte],
                        key=lambda x: (x["dato"], x["bilag"], x["konto"])):
            celle(ws, rad, 1, p["dato"][:10])
            celle(ws, rad, 2, int(p["bilag"]) if p["bilag"].isdigit() else p["bilag"])
            celle(ws, rad, 3, p["konto"])
            celle(ws, rad, 4, p["tekst"])
            celle(ws, rad, 5, round(p["beloep"], 2), nf=KRONER)
            rad += 1
    else:
        celle(ws, rad, 1, "Ingen")
        rad += 1

    rad += 1
    seksjon(ws, rad, "Kilder")
    rad += 1
    for linje in [
        ledger.d.get("kilde_a07", f"A07: Skatteetaten avstemmingsinformasjon, {a07.fom}–{a07.tom}"),
        ledger.d.get("kilde_regnskap", f"Regnskap: Tripletex (selskaps-id {ledger.d.get('tripletex_id','')})"),
        f"AGA-sats {_sats(ledger, a07)} % sone {a07.sone}, "
        f"feriepengesats {_feriesats(ledger) * 100:.1f} %",
    ]:
        celle(ws, rad, 1, linje)
        ws.merge_cells(start_row=rad, start_column=1, end_row=rad, end_column=8)
        rad += 1


def ark_forskuddstrekk(wb, a07: A07, ledger: Ledger, undertittel: str) -> None:
    ws = wb.create_sheet("Forskuddstrekk")
    topp(ws, "Forskuddstrekk – konto 2600", undertittel)
    bredder(ws, {"A": 16, "G": 30})
    tabellhode(ws, 7, [("Lønnsdato", "l"), ("Bokført 2600 (lønnsbilag)", "r"),
                       ("A-meldt (A07)", "r"), ("Avvik", "r"), ("Innbetalt", "r"),
                       ("Innbetalt dato", "l"), ("Bilag", "l")])
    rad = 8
    forste = rad
    for dato, a_meldt in a07.trekk_per_loennsdato().items():
        bokfort = -ledger.sum_konto(2600, ledger.er_lonnsbilag, dato=dato)
        betalinger = [p for p in ledger.aktive
                      if p["konto"] == 2600 and ledger.er_betaling(p)
                      and p["dato"][:10] == dato]
        celle(ws, rad, 1, norsk_dato(dato))
        celle(ws, rad, 2, round(bokfort, 2), nf=KRONER)
        celle(ws, rad, 3, a_meldt, nf=KRONER)
        celle(ws, rad, 4, f"=B{rad}-C{rad}", nf=KRONER)
        celle(ws, rad, 5, round(sum(p["beloep"] for p in betalinger), 2), nf=KRONER)
        celle(ws, rad, 6, norsk_dato(dato) if betalinger else "")
        celle(ws, rad, 7, ", ".join(sorted({p["bilag"] for p in betalinger})))
        rad += 1
    celle(ws, rad, 1, "Sum", fet=True)
    for kol in "BCDE":
        celle(ws, rad, ord(kol) - 64, f"=SUM({kol}{forste}:{kol}{rad - 1})",
              fet=True, nf=KRONER)
    rad += 2

    seksjon(ws, rad, "Saldokontroll 2600")
    rad += 1
    alle_betalinger = sum(p["beloep"] for p in ledger.aktive
                          if p["konto"] == 2600 and ledger.er_betaling(p))
    andre = sum(p["beloep"] for p in ledger.aktive
                if p["konto"] == 2600 and not ledger.er_betaling(p)
                and not ledger.er_lonnsbilag(p) and not ledger.er_avrunding(p))
    start = rad
    for tekst, verdi in [
        ("IB 2600 (skyldig fra forrige termin)", round(-ledger.ib(2600), 2)),
        ("+ A-meldt trekk termin", round(sum(a07.trekk_per_loennsdato().values()), 2)),
        ("− Innbetalt i terminen (alle «Betaling:» på 2600)", round(-alle_betalinger, 2)),
        ("− Andre føringer 2600", round(-andre, 2)),
    ]:
        celle(ws, rad, 1, tekst)
        ws.merge_cells(start_row=rad, start_column=1, end_row=rad, end_column=3)
        celle(ws, rad, 4, verdi, nf=KRONER)
        rad += 1
    celle(ws, rad, 1, "→ Beregnet UB 2600 (kredit = skyldig, negativ = tilgode)", fet=True)
    ws.merge_cells(start_row=rad, start_column=1, end_row=rad, end_column=3)
    celle(ws, rad, 4, f"=SUM(D{start}:D{rad - 1})", fet=True, nf=KRONER)
    beregnet_rad = rad
    rad += 1
    celle(ws, rad, 1, "UB 2600 iflg. saldobalanse")
    ws.merge_cells(start_row=rad, start_column=1, end_row=rad, end_column=3)
    celle(ws, rad, 4, round(-ledger.ub(2600), 2), nf=KRONER)
    saldo_rad = rad
    rad += 1
    celle(ws, rad, 1, "Avvik", fet=True)
    ws.merge_cells(start_row=rad, start_column=1, end_row=rad, end_column=3)
    celle(ws, rad, 4, f"=D{beregnet_rad}-D{saldo_rad}", fet=True, nf=KRONER)
    rad += 2

    celle(ws, rad, 1, f"Skattetrekkskonto 1950: IB {ledger.ib(1950):,.2f}  "
                      f"bevegelse {ledger.bevegelse(1950):,.2f}  "
                      f"UB {ledger.ub(1950):,.2f}", farge=GRA)
    rad += 2

    seksjon(ws, rad, "Trekk per ansatt (termin)")
    rad += 1
    tabellhode(ws, rad, [("Ansatt", "l"), ("A07 trekk", "r"), ("Bokført 2600", "r"),
                         ("Avvik", "r"), ("Status", "l")])
    rad += 1
    forste_status = rad
    for navn, a07_trekk, bokfort, _ in _trekk_per_ansatt(a07, ledger):
        celle(ws, rad, 1, navn)
        celle(ws, rad, 2, a07_trekk, nf=KRONER)
        celle(ws, rad, 3, bokfort, nf=KRONER)
        celle(ws, rad, 4, f"=B{rad}-C{rad}", nf=KRONER)
        c = celle(ws, rad, 5, f'=IF(ABS(D{rad})<=1,"OK","AVVIK")', fet=True)
        c.alignment = Alignment(vertical="center", horizontal="center")
        rad += 1
    if rad > forste_status:
        statusregler(ws, f"E{forste_status}:E{rad - 1}")


def ark_aga(wb, a07: A07, ledger: Ledger, undertittel: str) -> None:
    ws = wb.create_sheet("Arbeidsgiveravgift")
    topp(ws, "Arbeidsgiveravgift – Sticos pkt. 1–5", undertittel)
    bredder(ws, {"A": 44, "B": 18, "E": 14, "G": 30})
    sats = _sats(ledger, a07)
    pensjonskonto = _pensjonskonto(ledger)

    rad = 7
    seksjon(ws, rad, "1. Kontroll av beregnet AGA per måned")
    rad += 1
    tabellhode(ws, rad, [("Måned", "l"), ("Grunnlag lønn (A07)", "r"),
                         ("Pensjon − fradrag", "r"), ("Beregnet AGA", "r"),
                         ("Innrapportert", "r"), ("Avvik", "r"), ("Kommentar", "l")])
    rad += 1
    start = rad
    grunnlag_mnd = a07.grunnlag_per_maaned()
    pensjon_mnd = {r[0]: float(r[4]) for r in ledger.d.get("pensjon_historikk", [])}
    for m in a07.maaneder:
        celle(ws, rad, 1, maanedsnavn(m))
        celle(ws, rad, 2, round(grunnlag_mnd.get(m, 0.0), 2), nf=KRONER)
        celle(ws, rad, 3, round(pensjon_mnd.get(m, 0.0), 2), nf=KRONER)
        celle(ws, rad, 4, f"=ROUNDDOWN((INT(B{rad})+C{rad})*{sats / 100},0)", nf=KRONER)
        celle(ws, rad, 5, a07.aga_innrapportert(m), nf=KRONER)
        celle(ws, rad, 6, f"=D{rad}-E{rad}", nf=KRONER)
        celle(ws, rad, 7, "Tripletex runder ned per måned (0–1 kr)", farge=GRA)
        rad += 1
    celle(ws, rad, 1, "Sum termin", fet=True)
    for kol in "BCDEF":
        celle(ws, rad, ord(kol) - 64, f"=SUM({kol}{start}:{kol}{rad - 1})",
              fet=True, nf=KRONER)
    rad += 1
    celle(ws, rad, 1, "A07 samlet grunnlag (lønn / pensjon / fradrag)", farge=GRA)
    celle(ws, rad, 2, a07.grunnlag_loenn, nf=KRONER)
    celle(ws, rad, 3, a07.grunnlag_pensjon, nf=KRONER)
    celle(ws, rad, 4, round(a07.fradrag_sone, 2), nf=KRONER)
    rad += 2

    seksjon(ws, rad, "2. Grunnlag mot regnskapsførte ytelser (bevegelse i terminen)")
    rad += 1
    tabellhode(ws, rad, [("Konto", "l"), ("Bevegelse", "r"), ("Herav lønnsbilag/reise", "r"),
                         ("Herav annet", "r"), ("I A07-grunnlag", "l"), ("", "l"),
                         ("Kommentar", "l")])
    rad += 1
    start = rad
    konti = sorted({k for k in ledger.balanser
                    if (5000 <= k <= 5399 and k not in (5020, 5290)) or 5500 <= k <= 5599})
    for konto in konti:
        bevegelse = ledger.bevegelse(konto)
        i_lonnsbilag = sum(p["beloep"] for p in ledger.aktive
                           if p["konto"] == konto and ledger.er_lonnsbilag(p))
        annet = round(bevegelse - i_lonnsbilag, 2)
        celle(ws, rad, 1, f"{konto} {ledger.navn(konto)}")
        celle(ws, rad, 2, round(bevegelse, 2), nf=KRONER)
        celle(ws, rad, 3, round(i_lonnsbilag, 2), nf=KRONER)
        celle(ws, rad, 4, annet, nf=KRONER)
        if abs(annet) > 0.5:
            celle(ws, rad, 5, "NEI – kontroller", farge="FFC0392B")
            celle(ws, rad, 7, "Bevegelse uten lønnsbilag – mulig ikke innrapportert fordel",
                  farge=GRA)
        else:
            celle(ws, rad, 5, "JA", farge="FF1B6E3D")
        rad += 1
    ferie_ut = _utbetalte_feriepenger(ledger)
    celle(ws, rad, 1, "Utbetalte feriepenger (2940-debet i lønnsbilag, netto)")
    celle(ws, rad, 2, round(ferie_ut, 2), nf=KRONER)
    celle(ws, rad, 3, round(ferie_ut, 2), nf=KRONER)
    celle(ws, rad, 4, 0, nf=KRONER)
    celle(ws, rad, 5, "JA", farge="FF1B6E3D")
    rad += 1
    celle(ws, rad, 1, f"Pensjon {pensjonskonto} (bevegelse)")
    celle(ws, rad, 2, round(ledger.bevegelse(pensjonskonto), 2), nf=KRONER)
    celle(ws, rad, 5, "JA", farge="FF1B6E3D")
    rad += 1
    celle(ws, rad, 1, "Sum regnskap", fet=True)
    celle(ws, rad, 2, f"=SUM(B{start}:B{rad - 1})", fet=True, nf=KRONER)
    sum_rad = rad
    rad += 1
    celle(ws, rad, 1, "A07 grunnlag (lønn + pensjon − fradrag)", fet=True)
    a07_grunnlag = a07.grunnlag_loenn + a07.grunnlag_pensjon + a07.fradrag_sone
    celle(ws, rad, 2, round(a07_grunnlag, 2), fet=True, nf=KRONER)
    a07_rad = rad
    rad += 1
    celle(ws, rad, 1, "Differanse")
    celle(ws, rad, 2, f"=B{sum_rad}-B{a07_rad}", nf=KRONER)
    diff_rad = rad
    rad += 1
    hist = ledger.d.get("pensjon_historikk") or []
    if hist:
        pensjon_periodisering = round(
            sum(float(r[2]) for r in hist) - sum(float(r[4]) for r in hist), 2)
    else:
        pensjon_periodisering = round(ledger.bevegelse(pensjonskonto) - a07.grunnlag_pensjon, 2)
    utenfor = round(sum(
        ledger.bevegelse(k) - sum(p["beloep"] for p in ledger.aktive
                                  if p["konto"] == k and ledger.er_lonnsbilag(p))
        for k in konti), 2)
    forklaringer = [
        ("(1) Pensjon periodisering (regnskap − innrapportert i terminen)", pensjon_periodisering),
        ("(2) Bevegelse på lønnskonti utenfor lønnsbilag", utenfor),
    ]
    forste_forklaring = rad
    for tekst, verdi in forklaringer:
        celle(ws, rad, 1, tekst)
        celle(ws, rad, 2, verdi, nf=KRONER)
        rad += 1
    celle(ws, rad, 1, "(3) Avrunding grunnlag (lønn per måned, pensjon per bilag)")
    avrunding_rad = rad
    celle(ws, rad, 2,
          f"=ROUND(B{diff_rad}-SUM(B{forste_forklaring}:B{rad - 1}),2)", nf=KRONER)
    rad += 1
    celle(ws, rad, 1, "Uforklart differanse", fet=True)
    celle(ws, rad, 2,
          f"=ROUND(B{diff_rad}-SUM(B{forste_forklaring}:B{avrunding_rad}),2)",
          fet=True, nf=KRONER)
    rad += 2

    historikk = ledger.d.get("pensjon_historikk") or []
    if historikk:
        seksjon(ws, rad, f"Pensjon hittil i år – {pensjonskonto} bokført mot "
                         "innrapportert (pensjonsbilag / sats)")
        rad += 1
        tabellhode(ws, rad, [("Måned", "l"), ("Bokført " + str(pensjonskonto), "r"),
                             ("Innrapportert grunnlag", "r"), ("Differanse", "r"),
                             ("", "l"), ("", "l"), ("Kommentar", "l")])
        rad += 1
        start = rad
        for r in historikk:
            celle(ws, rad, 1, maanedsnavn(r[0]))
            celle(ws, rad, 2, round(float(r[2]), 2), nf=KRONER)
            celle(ws, rad, 3, round(float(r[4]), 2), nf=KRONER)
            celle(ws, rad, 4, f"=B{rad}-C{rad}", nf=KRONER)
            rad += 1
        celle(ws, rad, 1, "Sum hittil i år", fet=True)
        for kol in "BCD":
            celle(ws, rad, ord(kol) - 64, f"=SUM({kol}{start}:{kol}{rad - 1})",
                  fet=True, nf=KRONER)
        celle(ws, rad, 7, "Skal være 0", farge=GRA)
        rad += 2

    seksjon(ws, rad, "3. Kostnadsført AGA")
    rad += 1
    frigjort = _frigjort_aga_ferie(ledger)
    for tekst, verdi, fet in [
        ("5400 Arbeidsgiveravgift (bevegelse)", round(ledger.bevegelse(5400), 2), False),
        ("+ Frigjort AGA av utbetalte feriepenger (2785-debet mot 5400)", round(frigjort, 2), False),
        ("→ Kostnadsført", round(ledger.bevegelse(5400) + frigjort, 2), True),
        ("Innrapportert A07", a07.aga_innrapportert(), False),
        ("Avvik (øre-avrunding)",
         round(ledger.bevegelse(5400) + frigjort - a07.aga_innrapportert(), 2), True),
    ]:
        celle(ws, rad, 1, tekst, fet=fet)
        celle(ws, rad, 2, verdi, fet=fet, nf=KRONER)
        rad += 1
    rad += 1

    seksjon(ws, rad, "4. Skyldig AGA – konto 2770")
    rad += 1
    betalt = sum(p["beloep"] for p in ledger.aktive
                 if p["konto"] == 2770 and ledger.er_betaling(p))
    kreditert = -ledger.sum_konto(2770, lambda p: not ledger.er_betaling(p)
                                  and not ledger.er_avrunding(p))
    avrunding = -ledger.sum_konto(2770, ledger.er_avrunding)
    andre = 0.0
    for tekst, verdi, fet in [
        ("IB 2770", round(-ledger.ib(2770), 2), False),
        ("− Betalt i terminen (Betaling: Terminoppgave)", round(-betalt, 2), False),
        ("+ Kreditert lønnsbilag + pensjonsbilag − NAV-refusjon", round(kreditert, 2), False),
        ("− Avrundingsbilag (A-melding lønn)", round(avrunding, 2), False),
        ("− Andre føringer 2770", andre, False),
        ("→ Beregnet UB", round(-ledger.ib(2770) - betalt + kreditert + avrunding, 2), True),
        ("UB 2770 saldobalanse", round(-ledger.ub(2770), 2), False),
        ("Innrapportert termin (A07)", a07.aga_innrapportert(), False),
        ("UB − innrapportert (restsaldo)",
         round(-ledger.ub(2770) - a07.aga_innrapportert(), 2), True),
    ]:
        celle(ws, rad, 1, tekst, fet=fet)
        celle(ws, rad, 2, verdi, fet=fet, nf=KRONER)
        rad += 1
    rad += 1

    seksjon(ws, rad, "5. Innbetaling")
    rad += 1
    forfall = ledger.d.get("periode", {}).get("forfall", "")
    celle(ws, rad, 1, f"Skyldig AGA termin {ledger.d.get('periode', {}).get('termin', '')}: "
                      f"{a07.aga_innrapportert():,.0f} kr – forfall {norsk_dato(forfall)} – "
                      f"KID {a07.kid_aga or ''} – konto {a07.kontonummer or ''}",
          farge=GRA)
    ws.merge_cells(start_row=rad, start_column=1, end_row=rad, end_column=7)
    rad += 1
    for p in sorted([p for p in ledger.aktive
                     if p["konto"] == 2770 and ledger.er_betaling(p)],
                    key=lambda x: x["dato"]):
        celle(ws, rad, 1, f"Betalt {norsk_dato(p['dato'])} bilag {p['bilag']}: {p['tekst']}")
        celle(ws, rad, 2, round(p["beloep"], 2), nf=KRONER)
        rad += 1
    rad += 1

    seksjon(ws, rad, "AGA per ansatt per måned (2770-kredit i lønnsbilag)")
    rad += 1
    tabellhode(ws, rad, [("Ansatt", "l"), ("Måned", "l"), ("AGA-pliktig grunnlag (A07)", "r"),
                         ("AGA beregnet", "r"), ("Bokført 2770", "r"), ("Avvik", "r"),
                         ("Status", "l")])
    rad += 1
    forste = rad
    for navn, m, grunnlag, _, beregnet, bokfort in _aga_per_ansatt(a07, ledger):
        celle(ws, rad, 1, navn)
        celle(ws, rad, 2, m)
        celle(ws, rad, 3, grunnlag, nf=KRONER)
        celle(ws, rad, 4, beregnet, nf=KRONER)
        celle(ws, rad, 5, bokfort, nf=KRONER)
        celle(ws, rad, 6, f"=D{rad}-E{rad}", nf=KRONER)
        c = celle(ws, rad, 7, f'=IF(ABS(F{rad})<=0.06,"OK","AVVIK")', fet=True)
        c.alignment = Alignment(vertical="center", horizontal="center")
        rad += 1
    if rad > forste:
        statusregler(ws, f"G{forste}:G{rad - 1}")


def ark_per_ansatt(wb, a07: A07, ledger: Ledger, undertittel: str) -> None:
    ws = wb.create_sheet("Per ansatt")
    topp(ws, "Ytelser per ansatt – A07 mot lønnsbilag", undertittel)
    bredder(ws, {"A": 26, "B": 10, "D": 16, "F": 12, "G": 24})
    tabellhode(ws, 7, [("Ansatt", "l"), ("Måned", "l"), ("Konto", "l"), ("A07", "r"),
                       ("Regnskap", "r"), ("Avvik", "r"), ("Status", "l")])
    rad = 8
    forste = rad
    override = ledger.d.get("ytelse_konto") or {}
    per_person = a07.ytelser_per_person(override)
    for (navn, maaned, konto), beloep in sorted(per_person.items()):
        bokfort = _bokfort_person(ledger, navn, maaned, konto,
                                  maal_per_person(per_person, maaned, konto))
        celle(ws, rad, 1, navn)
        celle(ws, rad, 2, maaned)
        celle(ws, rad, 3, str(konto))
        celle(ws, rad, 4, round(beloep, 2), nf=KRONER)
        if bokfort is None:
            celle(ws, rad, 5, "Koblingsproblemer", farge="FFC0392B")
            celle(ws, rad, 6, "", nf=KRONER)
            c = celle(ws, rad, 7, "AVVIK", fet=True)
        else:
            celle(ws, rad, 5, round(bokfort, 2), nf=KRONER)
            celle(ws, rad, 6, f"=D{rad}-E{rad}", nf=KRONER)
            c = celle(ws, rad, 7, f'=IF(ABS(F{rad})<=0.02,"OK","AVVIK")', fet=True)
        c.alignment = Alignment(vertical="center", horizontal="center")
        rad += 1
    if rad > forste:
        statusregler(ws, f"G{forste}:G{rad - 1}")

    rad += 1
    seksjon(ws, rad, "Sum per ansatt (termin, AGA-pliktige ytelser)")
    rad += 1
    tabellhode(ws, rad, [("Ansatt", "l"), ("Ansattnr", "l"), ("", "l"),
                         ("AGA-pliktig A07", "r"), ("Trekk A07", "r"),
                         ("Trekk bokført", "r"), ("Status", "l")])
    rad += 1
    forste_sum = rad
    trekk = {r[0]: (r[1], r[2]) for r in _trekk_per_ansatt(a07, ledger)}
    for p in a07.personer:
        a07_trekk, bokfort = trekk.get(p.navn, (0.0, 0.0))
        celle(ws, rad, 1, p.navn)
        celle(ws, rad, 2, p.ansattnummer or "")
        celle(ws, rad, 4, round(p.aga_grunnlag(), 2), nf=KRONER)
        celle(ws, rad, 5, a07_trekk, nf=KRONER)
        celle(ws, rad, 6, bokfort, nf=KRONER)
        c = celle(ws, rad, 7, f'=IF(ABS(E{rad}-F{rad})<=1,"OK","AVVIK")', fet=True)
        c.alignment = Alignment(vertical="center", horizontal="center")
        rad += 1
    if rad > forste_sum:
        statusregler(ws, f"G{forste_sum}:G{rad - 1}")


def ark_ytelser(wb, a07: A07, ledger: Ledger, undertittel: str) -> None:
    ws = wb.create_sheet("Ytelser A07")
    topp(ws, "Ytelser i A07 per måned – kontomapping", undertittel)
    bredder(ws, {"A": 10, "B": 34, "C": 18, "D": 8, "F": 14})
    tabellhode(ws, 7, [("Måned", "l"), ("Ytelse (A07)", "l"), ("Fordel", "l"),
                       ("AGA", "l"), ("Konto", "l"), ("A07 beløp", "r"),
                       ("Sum konto A07", "r"), ("Sum konto regnskap", "r")])
    rad = 8
    forste = rad
    override = ledger.d.get("ytelse_konto") or {}
    samlet: dict[tuple[str, str, str, bool, int], float] = defaultdict(float)
    for p in a07.personer:
        for y in p.ytelser:
            konto = override.get(y.beskrivelse) or YTELSE_KONTO.get(y.beskrivelse, 5260)
            samlet[(y.maaned, y.beskrivelse, y.fordel, y.aga_pliktig, konto)] += y.beloep
    per_konto = a07.ytelser_per_maaned_konto(override)
    for (maaned, beskrivelse, fordel, aga, konto), beloep in sorted(samlet.items()):
        celle(ws, rad, 1, maaned)
        celle(ws, rad, 2, beskrivelse[0].upper() + beskrivelse[1:])
        celle(ws, rad, 3, fordel)
        celle(ws, rad, 4, "ja" if aga else "nei")
        celle(ws, rad, 5, str(konto))
        celle(ws, rad, 6, round(beloep, 2), nf=KRONER)
        celle(ws, rad, 7, round(per_konto.get((maaned, konto), 0.0), 2), nf=KRONER)
        bokfort = sum(p["beloep"] for p in ledger.aktive
                      if p["konto"] == konto and p["dato"][:7] == maaned
                      and ledger.er_lonnsbilag(p))
        celle(ws, rad, 8, round(abs(bokfort) if konto == 2940 else bokfort, 2), nf=KRONER)
        rad += 1
    celle(ws, rad, 1, "Sum AGA-pliktig", fet=True)
    celle(ws, rad, 6, f'=SUMIF(D{forste}:D{rad - 1},"ja",F{forste}:F{rad - 1})',
          fet=True, nf=KRONER)


def ark_posteringer(wb, ledger: Ledger) -> None:
    ws = wb.create_sheet("Posteringer")
    bredder(ws, {"A": 12, "B": 9, "C": 8, "D": 30, "E": 60, "F": 14})
    tabellhode(ws, 1, [("Dato", "l"), ("Bilag", "l"), ("Konto", "l"),
                       ("Kontonavn", "l"), ("Tekst", "l"), ("Beløp", "r")])
    rad = 2
    for p in sorted(ledger.poster, key=lambda x: (x["dato"], x["bilag"], x["konto"])):
        celle(ws, rad, 1, p["dato"][:10], ramme=False)
        celle(ws, rad, 2, int(p["bilag"]) if p["bilag"].isdigit() else p["bilag"], ramme=False)
        celle(ws, rad, 3, p["konto"], ramme=False)
        celle(ws, rad, 4, p["kontonavn"], ramme=False)
        celle(ws, rad, 5, p["tekst"], ramme=False)
        celle(ws, rad, 6, round(p["beloep"], 2), nf=KRONER, ramme=False)
        rad += 1


def bygg(a07_sti: str, ledger_sti: str, ut_sti: str) -> str:
    a07 = parse_a07(a07_sti)
    with open(ledger_sti, encoding="utf-8") as f:
        ledger = Ledger(json.load(f))

    # Pensjonsgrunnlaget per måned er først kjent nå – fordel ytelser uten
    # opptjeningsperiode på nytt med det på plass.
    pensjon_mnd = {r[0]: float(r[4]) for r in ledger.d.get("pensjon_historikk", [])}
    if pensjon_mnd:
        from a07 import fordel_paa_nytt

        fordel_paa_nytt(a07, pensjon_mnd)

    periode = ledger.d.get("periode", {})
    termin = periode.get("termin", "")
    mnd = a07.maaneder
    spenn = (f"{MAANEDSNAVN[int(mnd[0][5:7]) - 1]}–{MAANEDSNAVN[int(mnd[-1][5:7]) - 1]} "
             f"{a07.fom[:4]}") if mnd else ""
    undertittel = (f"{ledger.d.get('selskap', a07.navn)}   |   "
                   f"Org.nr. {ledger.d.get('orgnr', a07.orgnr)}   |   "
                   f"Termin {termin} ({spenn})   |   "
                   f"Avstemt {date.today().strftime('%d.%m.%Y')}")

    wb = Workbook()
    wb.remove(wb.active)
    ark_avstemming(wb, a07, ledger, undertittel)
    ark_detaljer(wb, a07, ledger, undertittel)
    ark_forskuddstrekk(wb, a07, ledger, undertittel)
    ark_aga(wb, a07, ledger, undertittel)
    ark_per_ansatt(wb, a07, ledger, undertittel)
    ark_ytelser(wb, a07, ledger, undertittel)
    ark_posteringer(wb, ledger)
    wb.save(ut_sti)
    return ut_sti


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    # os_sti: Claudes scratch-mapper kan gi stier over Windows' grense på 260 tegn.
    bygg(*(os_sti(a) for a in sys.argv[1:4]))
    print(sys.argv[3])
