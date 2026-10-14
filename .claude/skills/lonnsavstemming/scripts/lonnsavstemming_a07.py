"""Lønnsavstemming A07 mot Tripletex – bygger Excel-rapporten.

    python lonnsavstemming_a07.py <a07.json> <ledger.json> <ut.xlsx>

a07.json er svaret fra Tally `hent_amelding_rapport` (A07 fra Skatteetaten via
Altinn, uten personopplysninger). ledger.json er regnskapssiden, hentet fra
Tripletex med scripts/hent_tripletex.js. Formatene står i
references/kontrollogikk.md; utfylte eksempler ligger i
scripts/a07_tally_eksempel.json og scripts/ledger_eksempel.json.

Arkene: Avstemming · Detaljer · Forskuddstrekk · Arbeidsgiveravgift ·
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

from a07 import IKKE_OPPGITT, A07, les_a07, summer

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "silfer-rapport" / "scripts"))
from silfer.filer import os_sti  # noqa: E402
from silfer.stil import (ANTALL, GRA, KRONER, MORK, SVART, bredder, celle, seksjon,  # noqa: E402
                         statusregler, tabellhode, topp)

MAANEDSNAVN = ["januar", "februar", "mars", "april", "mai", "juni",
               "juli", "august", "september", "oktober", "november", "desember"]

RE_REVERSERING = re.compile(r"Reversering av bilag\s+(\S+)", re.I)

YTELSE_TOLERANSE = 1.0
INGEN_AMELDING = "Ingen a-melding for måneden i A07"
IKKE_OPPGITT_KOMMENTAR = "Beløpet er ikke oppgitt i A07 – kontroller i Altinn"


def norsk_dato(iso: str) -> str:
    if not iso:
        return ""
    d = datetime.fromisoformat(str(iso)[:10]).date()
    return d.strftime("%d.%m.%Y")


def maanedsnavn(iso_maaned: str) -> str:
    aar, mnd = iso_maaned.split("-")
    navn = MAANEDSNAVN[int(mnd) - 1]
    return f"{navn[0].upper()}{navn[1:]} {aar}"


def kort_maaned(iso_maaned: str) -> str:
    return MAANEDSNAVN[int(iso_maaned[5:7]) - 1]


def verdi(v: float | None, desimaler: int = 2):
    """Tall eller «ikke oppgitt». None blir aldri 0."""
    return IKKE_OPPGITT if v is None else round(v, desimaler)


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
        """«Betaling: …», og i direkte-modellen linjen «Lønnsbilag N-ÅÅÅÅ. Overføring
        skattetrekk» i selve lønnsbilaget (samme bilag og dato som trekket)."""
        t = p["tekst"].strip().lower()
        return (t.startswith("betaling:") or "overføring skattetrekk" in t
                or "overforing skattetrekk" in t)

    @staticmethod
    def er_avrunding(p) -> bool:
        return "a-melding lønn" in p["tekst"].lower()

    def er_lonnsbilag(self, p) -> bool:
        return ("lønnsbilag" in p["tekst"].lower()
                and not self.er_betaling(p) and not self.er_avrunding(p))

    def er_aga_postering(self, p) -> bool:
        """2770 i lønnsbilag og pensjonsbilag: alt utenom betalinger og avrundingsbilag."""
        return not self.er_betaling(p) and not self.er_avrunding(p)

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

    def sum_konto(self, konto: int, filter_=None, dato=None, maaned=None) -> float:
        ut = 0.0
        for p in self.aktive:
            if p["konto"] != konto:
                continue
            if dato and p["dato"][:10] != dato:
                continue
            if maaned and p["dato"][:7] != maaned:
                continue
            if filter_ and not filter_(p):
                continue
            ut += p["beloep"]
        return ut


def _sats(ledger: Ledger, a07: A07) -> float:
    """AGA-sats i prosent: ledger.json først, så A07."""
    if ledger.d.get("aga_sats"):
        return float(ledger.d["aga_sats"])
    if a07.sats is not None:
        return round(a07.sats * 100, 4)
    return 14.1


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


def _forfall(a07: A07, ledger: Ledger) -> str:
    """Forfall fra A07; er den null, 15. i måneden etter terminen (ledger.json)."""
    return a07.forfall or ledger.d.get("periode", {}).get("forfall", "")


def _maaneder(a07: A07, ledger: Ledger) -> list[str]:
    """Månedene i A07 pluss måneder med lønnsbilag på 2600/2770 i regnskapet."""
    ut = set(a07.maaneder)
    ut |= {p["dato"][:7] for p in ledger.aktive
           if p["konto"] in (2600, 2770) and ledger.er_lonnsbilag(p)}
    return sorted(m for m in ut if m)


def _mangler(a07: A07, m: str) -> str:
    return INGEN_AMELDING if a07.per_maaned is not None and not a07.har_maaned(m) else ""


def _innbetalt_trekk(ledger: Ledger, maaned: str | None = None) -> list[dict]:
    """2600-debet «Betaling: Lønnsbilag» eller «Overføring skattetrekk» (direkte-modellen),
    eventuelt i én måned."""
    return [p for p in ledger.aktive
            if p["konto"] == 2600 and ledger.er_betaling(p)
            and "lønnsbilag" in p["tekst"].lower()
            and (maaned is None or p["dato"][:7] == maaned)]


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
    maaneder = _maaneder(a07, ledger)
    trekk_termin = a07.trekk_innrapportert()

    # --- forskuddstrekk
    trekk_rader = []
    for m in maaneder:
        bokfort = -ledger.sum_konto(2600, ledger.er_lonnsbilag, maaned=m)
        trekk_rader.append(Kontrollrad(
            f"Trekk {kort_maaned(m)}",
            "A07 per måned = −Σ 2600 i lønnsbilag samme måned",
            a07.trekk_innrapportert(m), round(bokfort, 2), kommentar=_mangler(a07, m)))
    trekk_termin_bok = -(ledger.sum_konto(2600, ledger.er_lonnsbilag)
                         + ledger.sum_konto(2600, ledger.er_avrunding))
    innbetalt = sum(p["beloep"] for p in _innbetalt_trekk(ledger))
    trekk_rader += [
        Kontrollrad("Trekk termin",
                    "A07 totalt = −Σ 2600 lønnsbilag − avrundingsbilag",
                    trekk_termin, round(trekk_termin_bok, 2)),
        Kontrollrad("Innbetalt trekk",
                    "Σ 2600-debet «Betaling: Lønnsbilag» og «Overføring skattetrekk» = a-meldt",
                    trekk_termin, round(innbetalt, 2),
                    kommentar=ledger.d.get("trekkmodell", "")),
    ]
    alle_betalinger_2600 = sum(p["beloep"] for p in ledger.aktive
                               if p["konto"] == 2600 and ledger.er_betaling(p))
    andre_2600 = sum(p["beloep"] for p in ledger.aktive
                     if p["konto"] == 2600 and not ledger.er_betaling(p)
                     and not ledger.er_lonnsbilag(p) and not ledger.er_avrunding(p))
    if trekk_termin is None:
        saldo_rest = None
    else:
        beregnet_ub_2600 = (-ledger.ib(2600) + trekk_termin
                            - alle_betalinger_2600 - andre_2600)
        saldo_rest = round(beregnet_ub_2600 - (-ledger.ub(2600)), 2)
    trekk_rader += [
        Kontrollrad("Saldokontroll 2600",
                    "UB − IB − innbetalt + a-meldt − andre føringer = 0 (±1 kr avrunding)",
                    0.0, saldo_rest),
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
    historikk = ledger.d.get("pensjon_historikk", [])
    pensjon_hittil = float(sum(r[2] for r in historikk) or pensjon_termin)
    pensjon_innrapportert_hittil = (float(sum(r[4] for r in historikk))
                                    if historikk and sum(r[4] for r in historikk)
                                    else a07.grunnlag_pensjon)

    aga_rader = [
        Kontrollrad("Grunnlag lønn og ytelser",
                    "A07 avgiftsgrunnlag lønn = bevegelse 5000–5399 (ekskl. 5020/5290) "
                    "+ 5500–5599 + utbetalte ferie",
                    a07.grunnlag_loenn, round(grunnlag_regnskap, 2), toleranse=2),
        Kontrollrad("Grunnlag pensjon (termin)",
                    f"A07 avgiftsgrunnlag pensjon = bevegelse {pensjonskonto}",
                    a07.grunnlag_pensjon, round(pensjon_termin, 2)),
        Kontrollrad(f"Grunnlag pensjon {ledger.d.get('pensjon_etikett', 'hittil i år')}",
                    f"Innrapportert (pensjonsbilag/sats) = {pensjonskonto} bokført, t.o.m. {a07.tom}",
                    None if pensjon_innrapportert_hittil is None else round(pensjon_innrapportert_hittil, 2),
                    round(pensjon_hittil, 2), toleranse=2),
    ]
    if a07.grunnlag_fradrag is None or abs(a07.grunnlag_fradrag) > 0.005:
        refusjon_bokfort = ledger.bevegelse_intervall(5800, 5899)
        aga_rader.append(Kontrollrad(
            "Fradrag i grunnlag (NAV-refusjon)",
            "A07 fradrag i grunnlaget = refusjon bokført 58xx",
            a07.grunnlag_fradrag, round(refusjon_bokfort, 2), toleranse=2))

    for m in maaneder:
        bokfort = -ledger.sum_konto(2770, ledger.er_aga_postering, maaned=m)
        aga_rader.append(Kontrollrad(
            f"AGA {kort_maaned(m)}",
            "A07 per måned = −Σ 2770 i lønnsbilag + pensjonsbilag samme måned "
            "(uten avrundingsbilag; 0–1 kr er normalt)",
            a07.aga_innrapportert(m), round(bokfort, 2), kommentar=_mangler(a07, m)))

    aga_termin = a07.aga_innrapportert()
    beregnet = a07.beregnet_aga(sats / 100)
    ukjente = ", ".join(sorted({g.type for g in a07.ukjente_grunnlag}))
    kostnadsfort = ledger.bevegelse(5400) + _frigjort_aga_ferie(ledger)
    kreditert = -ledger.sum_konto(2770, lambda p: not ledger.er_betaling(p))
    aga_rader += [
        Kontrollrad("Beregnet AGA termin",
                    "Σ avgiftsgrunnlag × sats i A07 (lønn + pensjon − fradrag) ≈ innrapportert "
                    "(Tripletex runder ned per mnd)",
                    None if beregnet is None else round(beregnet, 2),
                    aga_termin, toleranse=max(2, len(maaneder)),
                    kommentar=f"Ukjent type holdt utenfor: {ukjente}" if ukjente else ""),
        Kontrollrad("Kostnadsført AGA",
                    "5400 + frigjort AGA av utbetalte feriepenger (2785-debet) ≈ innrapportert",
                    aga_termin, round(kostnadsfort, 2), toleranse=2),
        Kontrollrad("Kreditert 2770",
                    "Σ 2770-kredit lønnsbilag + pensjonsbilag − NAV-refusjon − "
                    "avrundingsbilag = innrapportert",
                    aga_termin, round(kreditert, 2), toleranse=0.01),
        Kontrollrad("Skyldig AGA (UB 2770)", "UB 2770 = innrapportert termin",
                    aga_termin, round(-ledger.ub(2770), 2), toleranse=0.5),
        Kontrollrad("Betalt forrige termin",
                    "IB 2770 = betalt i terminen (Betaling: Terminoppgave)",
                    round(-ledger.ib(2770), 2),
                    round(sum(p["beloep"] for p in ledger.aktive
                              if p["konto"] == 2770 and ledger.er_betaling(p)), 2),
                    toleranse=0.5),
        Kontrollrad("A07 totalt mot innsendinger",
                    "AGA totalt i A07 = Σ gjeldende innsendinger",
                    a07.aga_totalt, a07.aga_innsendinger(), toleranse=0.5),
    ]

    # --- feriepenger
    feriesats = _feriesats(ledger)
    avsatt = ledger.bevegelse(5020)
    ferie_a07 = a07.utbetalte_feriepenger()
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
                    "A07 ytelser «feriepenger» (perioden) = 2940-debet i lønnsbilag (netto)",
                    None if ferie_a07 is None else round(ferie_a07, 2), round(utbetalte_ferie, 2)),
    ]

    # --- ytelser per konto (antall som stemmer)
    grupper = _ytelsesgrupper(a07, ledger)
    ok = sum(1 for _, _, a, r in grupper
             if a is not None and abs(a - r) <= YTELSE_TOLERANSE)
    ytelse_rader = [
        Kontrollrad("Ytelser per konto",
                    "A07 per ytelse for perioden = konto i regnskapet (se «Ytelser A07»)",
                    len(grupper) if a07.ytelser is not None else None, ok,
                    toleranse=0, antall=True),
    ]

    return [
        ("Forskuddstrekk", trekk_rader),
        ("Arbeidsgiveravgift", aga_rader),
        ("Feriepenger", ferie_rader),
        ("Ytelser", ytelse_rader),
    ]


def _utbetalte_feriepenger(ledger: Ledger) -> float:
    """2940-debet i lønnsbilag uten lønnslinjer (5000-serien) på samme bilag."""
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


def _bokfort_ytelse(ledger: Ledger, konto: int) -> float:
    """Regnskapet for en ytelseskonto i perioden. 2940: utbetalte feriepenger.
    5000–5999: bare lønnsbilag. Andre konti (reise 71xx): alle posteringer."""
    if konto == 2940:
        return _utbetalte_feriepenger(ledger)
    # Trekkpliktig del av reise- og bilgodtgjørelse (5500–5599) føres via reiseregning, ikke lønnsbilag: ta med alle posteringer.
    if 5000 <= konto <= 5999 and not 5500 <= konto <= 5599:
        return ledger.sum_konto(konto, ledger.er_lonnsbilag)
    return ledger.sum_konto(konto)


def _ytelsesgrupper(a07: A07, ledger: Ledger):
    """[(konto, ytelser, A07-sum, regnskap)] for perioden, sortert på konto."""
    override = ledger.d.get("ytelse_konto") or {}
    return [(konto, typer, summer(y.beloep for y in typer), round(_bokfort_ytelse(ledger, konto), 2))
            for konto, typer in a07.ytelser_per_konto(override).items()]


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
            ellers = "AVVIK"
            if any(k.navn.lower().startswith(f) for f in forklart):
                ellers = "FORKLART"
            celle(ws, rad, 1, k.navn, fet=True)
            celle(ws, rad, 2, k.beregning, farge=GRA)
            celle(ws, rad, 3, verdi(k.a07, 0 if k.antall else 2), nf=nf)
            celle(ws, rad, 4, verdi(k.regnskap, 0 if k.antall else 2), nf=nf)
            kommentar = kommentarer.get(k.navn.lower(), k.kommentar)
            if k.a07 is None or k.regnskap is None:
                # null i A07 er ikke null kroner: ingen avviksformel, og raden må forklares.
                celle(ws, rad, 5, None, nf=nf)
                c = celle(ws, rad, 6, ellers, fet=True)
                kommentar = kommentar or IKKE_OPPGITT_KOMMENTAR
            else:
                celle(ws, rad, 5, f"=C{rad}-D{rad}", nf=nf)
                if k.spesial == "1950":
                    formel = f'=IF(D{rad}>=C{rad}-0.5,"OK","AVVIK")'
                else:
                    formel = f'=IF(ABS(E{rad})<={k.toleranse:g},"OK","{ellers}")'
                c = celle(ws, rad, 6, formel, fet=True)
            c.alignment = Alignment(vertical="center", horizontal="center")
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
    forfall = _forfall(a07, ledger)
    konto = a07.kontonummer or ""
    aga = a07.aga_innrapportert()
    celle(ws, rad, 1, "Arbeidsgiveravgift termin", fet=True)
    celle(ws, rad, 2, f"Forfall {norsk_dato(forfall)}   KID {a07.kid_aga or IKKE_OPPGITT}   "
                      f"Konto {konto}", farge=GRA)
    celle(ws, rad, 3, verdi(aga), nf=KRONER)
    celle(ws, rad, 4, round(-ledger.ub(2770), 2), nf=KRONER)
    if aga is None:
        celle(ws, rad, 7, IKKE_OPPGITT_KOMMENTAR)
    else:
        rest = round(-ledger.ub(2770) - aga, 2)
        if abs(rest) > 0.5:
            celle(ws, rad, 7, f"UB 2770 avviker {rest:,.2f} fra a-meldt (se merknad)".replace(",", " "))
    rad += 1
    for m in _maaneder(a07, ledger):
        beloep = a07.trekk_innrapportert(m)
        celle(ws, rad, 1, f"Forskuddstrekk {maanedsnavn(m).lower()}", fet=True)
        celle(ws, rad, 2, f"KID {a07.kid_for(m, 'trekk') or a07.kid_trekk or IKKE_OPPGITT}", farge=GRA)
        celle(ws, rad, 3, verdi(beloep), nf=KRONER)
        betalt = sum(p["beloep"] for p in _innbetalt_trekk(ledger, m))
        if abs(betalt) < 0.005 and beloep is not None and beloep < 0:
            # negativ lønnskjøring: trekket betales ikke ut, det motregnes.
            # Da er bokført 2600 i måneden det som gjelder.
            betalt = -ledger.sum_konto(2600, ledger.er_lonnsbilag, maaned=m)
        celle(ws, rad, 4, round(betalt, 2), nf=KRONER)
        if beloep is None:
            kommentar = IKKE_OPPGITT_KOMMENTAR
        elif beloep < 0:
            kommentar = "Negativ kjøring – trekk til gode, motregnes"
        else:
            kommentar = "Betalt på lønnsdato" if abs(betalt - beloep) <= 1 else _mangler(a07, m)
        celle(ws, rad, 7, kommentar)
        rad += 1
    finansskatt = a07.finansskatt_innrapportert()
    if finansskatt is None or abs(finansskatt) > 0.005:
        celle(ws, rad, 1, "Finansskatt på lønn termin", fet=True)
        celle(ws, rad, 2, f"Forfall {norsk_dato(forfall)}   KID {a07.kid_finansskatt or IKKE_OPPGITT}",
              farge=GRA)
        celle(ws, rad, 3, verdi(finansskatt), nf=KRONER)
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
    bredder(ws, {"A": 14, "B": 14, "C": 18, "D": 17, "E": 12, "F": 16, "G": 14, "H": 16,
                 "I": 24, "J": 24})

    rad = 7
    seksjon(ws, rad, "A-meldinger (innsendinger i A07)")
    rad += 1
    tabellhode(ws, rad, [("Måned", "l"), ("Status", "l"), ("Kildesystem", "l"),
                         ("Levert", "l"), ("Mottakere", "r"), ("AGA", "r"),
                         ("Trekk", "r"), ("Gjeldende", "l"), ("KID AGA", "l"),
                         ("KID trekk", "l")])
    rad += 1
    for i in sorted(a07.innsendinger, key=lambda x: (x.maaned, x.levert)):
        celle(ws, rad, 1, i.maaned)
        celle(ws, rad, 2, i.status)
        celle(ws, rad, 3, i.kildesystem)
        celle(ws, rad, 4, i.levert)
        celle(ws, rad, 5, i.antall_mottakere if i.antall_mottakere is not None else IKKE_OPPGITT,
              nf=ANTALL)
        celle(ws, rad, 6, verdi(i.aga), nf=KRONER)
        celle(ws, rad, 7, verdi(i.trekk), nf=KRONER)
        celle(ws, rad, 8, i.merknad)
        celle(ws, rad, 9, i.kid_aga or "")
        celle(ws, rad, 10, i.kid_trekk or "")
        rad += 1
    if not a07.innsendinger:
        celle(ws, rad, 1, "Ingen innsendinger i A07")
        rad += 1
    finansskatt = a07.finansskatt_innrapportert()
    if finansskatt is None or abs(finansskatt) > 0.005:
        celle(ws, rad, 1, f"Finansskatt på lønn i perioden: "
                          f"{IKKE_OPPGITT if finansskatt is None else f'{finansskatt:,.0f} kr'.replace(',', ' ')}",
              farge=GRA)
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
    linjer = [
        ledger.d.get("kilde_a07",
                     f"A07: Skatteetaten avstemmingsinformasjon via Tally (Altinn), {a07.fom}–{a07.tom}"),
        ledger.d.get("kilde_regnskap", f"Regnskap: Tripletex (selskaps-id {ledger.d.get('tripletex_id','')})"),
        f"AGA-sats {_sats(ledger, a07)} % sone {a07.sone}, "
        f"feriepengesats {_feriesats(ledger) * 100:.1f} %",
    ]
    if a07.avstemt:
        linjer.append(f"A07 hentet fra Tally {norsk_dato(a07.avstemt)}. Ingen personopplysninger; "
                      "ytelsene gjelder hele perioden.")
    if a07.ukjente_grunnlag:
        linjer.append("Ukjent type i avgiftsgrunnlaget (holdt utenfor beregnet AGA): " + ", ".join(
            f"{g.type} {IKKE_OPPGITT if g.grunnlag is None else f'{g.grunnlag:,.0f}'.replace(',', ' ')}"
            for g in a07.ukjente_grunnlag))
    if a07.merknad:
        linjer.append(f"Tally: {a07.merknad}")
    for linje in linjer:
        celle(ws, rad, 1, linje)
        ws.merge_cells(start_row=rad, start_column=1, end_row=rad, end_column=10)
        rad += 1


def ark_forskuddstrekk(wb, a07: A07, ledger: Ledger, undertittel: str) -> None:
    ws = wb.create_sheet("Forskuddstrekk")
    topp(ws, "Forskuddstrekk – konto 2600", undertittel)
    bredder(ws, {"A": 16, "B": 22, "C": 16, "F": 16, "G": 30})
    tabellhode(ws, 7, [("Måned", "l"), ("Bokført 2600 (lønnsbilag)", "r"),
                       ("A-meldt (A07)", "r"), ("Avvik", "r"), ("Innbetalt", "r"),
                       ("Innbetalt dato", "l"), ("Bilag", "l")])
    rad = 8
    forste = rad
    mangler_a07 = False
    for m in _maaneder(a07, ledger):
        a_meldt = a07.trekk_innrapportert(m)
        bokfort = -ledger.sum_konto(2600, ledger.er_lonnsbilag, maaned=m)
        betalinger = _innbetalt_trekk(ledger, m)
        celle(ws, rad, 1, maanedsnavn(m))
        celle(ws, rad, 2, round(bokfort, 2), nf=KRONER)
        celle(ws, rad, 3, verdi(a_meldt), nf=KRONER)
        if a_meldt is None:
            mangler_a07 = True
            celle(ws, rad, 4, None, nf=KRONER)
        else:
            celle(ws, rad, 4, f"=B{rad}-C{rad}", nf=KRONER)
        celle(ws, rad, 5, round(sum(p["beloep"] for p in betalinger), 2), nf=KRONER)
        celle(ws, rad, 6, ", ".join(sorted({norsk_dato(p["dato"]) for p in betalinger})))
        celle(ws, rad, 7, ", ".join(sorted({p["bilag"] for p in betalinger})))
        rad += 1
    celle(ws, rad, 1, "Sum", fet=True)
    for kol in "BCDE":
        if mangler_a07 and kol in "CD":
            celle(ws, rad, ord(kol) - 64, IKKE_OPPGITT, fet=True, nf=KRONER)
        else:
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
    trekk_termin = a07.trekk_innrapportert()
    start = rad
    for tekst, v in [
        ("IB 2600 (skyldig fra forrige termin)", round(-ledger.ib(2600), 2)),
        ("+ A-meldt trekk termin", verdi(trekk_termin)),
        ("− Innbetalt i terminen («Betaling:» og «Overføring skattetrekk» på 2600)",
         round(-alle_betalinger, 2)),
        ("− Andre føringer 2600", round(-andre, 2)),
    ]:
        celle(ws, rad, 1, tekst)
        ws.merge_cells(start_row=rad, start_column=1, end_row=rad, end_column=3)
        celle(ws, rad, 4, v, nf=KRONER)
        rad += 1
    celle(ws, rad, 1, "→ Beregnet UB 2600 (kredit = skyldig, negativ = tilgode)", fet=True)
    ws.merge_cells(start_row=rad, start_column=1, end_row=rad, end_column=3)
    if trekk_termin is None:
        celle(ws, rad, 4, IKKE_OPPGITT, fet=True, nf=KRONER)
    else:
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
    if trekk_termin is None:
        celle(ws, rad, 4, IKKE_OPPGITT, fet=True, nf=KRONER)
    else:
        celle(ws, rad, 4, f"=D{beregnet_rad}-D{saldo_rad}", fet=True, nf=KRONER)
    rad += 2

    celle(ws, rad, 1, f"Skattetrekkskonto 1950: IB {ledger.ib(1950):,.2f}  "
                      f"bevegelse {ledger.bevegelse(1950):,.2f}  "
                      f"UB {ledger.ub(1950):,.2f}", farge=GRA)
    rad += 1
    celle(ws, rad, 1, "A07 fra Tally gir trekk per måned, ikke per lønnsdato eller per person.",
          farge=GRA)


def ark_aga(wb, a07: A07, ledger: Ledger, undertittel: str) -> None:
    ws = wb.create_sheet("Arbeidsgiveravgift")
    topp(ws, "Arbeidsgiveravgift – Sticos pkt. 1–5", undertittel)
    bredder(ws, {"A": 44, "B": 18, "C": 16, "D": 18, "E": 14, "F": 12, "G": 30})
    sats = _sats(ledger, a07)
    pensjonskonto = _pensjonskonto(ledger)
    aga_termin = a07.aga_innrapportert()

    rad = 7
    seksjon(ws, rad, "1. AGA per måned – A07 mot 2770-kredit")
    rad += 1
    tabellhode(ws, rad, [("Måned", "l"), ("Innrapportert (A07)", "r"),
                         ("2770 lønnsbilag", "r"), ("2770 pensjon og annet", "r"),
                         ("Sum bokført", "r"), ("Avvik", "r"), ("Kommentar", "l")])
    rad += 1
    start = rad
    mangler_a07 = False
    for m in _maaneder(a07, ledger):
        a_meldt = a07.aga_innrapportert(m)
        lonn = -ledger.sum_konto(2770, ledger.er_lonnsbilag, maaned=m)
        annet = -ledger.sum_konto(
            2770, lambda p: ledger.er_aga_postering(p) and not ledger.er_lonnsbilag(p), maaned=m)
        celle(ws, rad, 1, maanedsnavn(m))
        celle(ws, rad, 2, verdi(a_meldt), nf=KRONER)
        celle(ws, rad, 3, round(lonn, 2), nf=KRONER)
        celle(ws, rad, 4, round(annet, 2), nf=KRONER)
        celle(ws, rad, 5, f"=C{rad}+D{rad}", nf=KRONER)
        if a_meldt is None:
            mangler_a07 = True
            celle(ws, rad, 6, None, nf=KRONER)
            celle(ws, rad, 7, IKKE_OPPGITT_KOMMENTAR, farge=GRA)
        else:
            celle(ws, rad, 6, f"=B{rad}-E{rad}", nf=KRONER)
            celle(ws, rad, 7, _mangler(a07, m) or "Tripletex runder ned per måned (0–1 kr)", farge=GRA)
        rad += 1
    celle(ws, rad, 1, "Sum termin", fet=True)
    for kol in "BCDEF":
        if mangler_a07 and kol in "BF":
            celle(ws, rad, ord(kol) - 64, IKKE_OPPGITT, fet=True, nf=KRONER)
        else:
            celle(ws, rad, ord(kol) - 64, f"=SUM({kol}{start}:{kol}{rad - 1})",
                  fet=True, nf=KRONER)
    rad += 2

    celle(ws, rad, 1, "Avgiftsgrunnlag i A07 (hele perioden)", fet=True)
    rad += 1
    tabellhode(ws, rad, [("Type", "l"), ("Virksomhet", "l"), ("Sone", "l"),
                         ("Beregningskode", "l"), ("Grunnlag", "r"), ("Sats", "r"),
                         ("Beregnet AGA", "r")])
    rad += 1
    start = rad
    beregnet_ok = True
    for g in a07.avgiftsgrunnlag or []:
        celle(ws, rad, 1, g.type)
        celle(ws, rad, 2, g.virksomhet)
        celle(ws, rad, 3, g.sone)
        celle(ws, rad, 4, g.beregningskode)
        celle(ws, rad, 5, verdi(g.grunnlag), nf=KRONER)
        g_sats = g.sats if g.sats is not None else sats / 100
        celle(ws, rad, 6, g_sats, nf="0.0%")
        if g.art == "ukjent":
            celle(ws, rad, 7, "holdt utenfor", farge=GRA)
        elif g.grunnlag is None:
            beregnet_ok = False
            celle(ws, rad, 7, IKKE_OPPGITT, nf=KRONER)
        elif g.art == "fradrag":
            celle(ws, rad, 7, f"=-ABS(E{rad})*F{rad}", nf=KRONER)
        else:
            celle(ws, rad, 7, f"=E{rad}*F{rad}", nf=KRONER)
        rad += 1
    if a07.avgiftsgrunnlag is None:
        beregnet_ok = False
        celle(ws, rad, 1, f"Avgiftsgrunnlag: {IKKE_OPPGITT}")
        rad += 1
    celle(ws, rad, 1, "Sum beregnet AGA", fet=True)
    if beregnet_ok and rad > start:
        celle(ws, rad, 7, f"=SUM(G{start}:G{rad - 1})", fet=True, nf=KRONER)
    else:
        celle(ws, rad, 7, IKKE_OPPGITT if not beregnet_ok else 0, fet=True, nf=KRONER)
    sum_beregnet = rad
    rad += 1
    celle(ws, rad, 1, "Innrapportert termin (A07)")
    celle(ws, rad, 7, verdi(aga_termin), nf=KRONER)
    innrapportert_rad = rad
    rad += 1
    celle(ws, rad, 1, "Avvik (Tripletex runder ned per måned)", fet=True)
    if beregnet_ok and aga_termin is not None:
        celle(ws, rad, 7, f"=G{sum_beregnet}-G{innrapportert_rad}", fet=True, nf=KRONER)
    else:
        celle(ws, rad, 7, IKKE_OPPGITT, fet=True, nf=KRONER)
    rad += 1
    celle(ws, rad, 1, "A07 fra Tally gir grunnlaget for hele perioden; AGA per måned kontrolleres mot 2770.",
          farge=GRA)
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
    a07_grunnlag = summer([a07.grunnlag_loenn, a07.grunnlag_pensjon, a07.grunnlag_fradrag])
    celle(ws, rad, 2, verdi(a07_grunnlag), fet=True, nf=KRONER)
    a07_rad = rad
    rad += 1
    celle(ws, rad, 1, "Differanse")
    if a07_grunnlag is None:
        celle(ws, rad, 2, IKKE_OPPGITT, nf=KRONER)
    else:
        celle(ws, rad, 2, f"=B{sum_rad}-B{a07_rad}", nf=KRONER)
    diff_rad = rad
    rad += 1
    hist = ledger.d.get("pensjon_historikk") or []
    if hist:
        pensjon_periodisering = round(
            sum(float(r[2]) for r in hist) - sum(float(r[4]) for r in hist), 2)
    elif a07.grunnlag_pensjon is not None:
        pensjon_periodisering = round(ledger.bevegelse(pensjonskonto) - a07.grunnlag_pensjon, 2)
    else:
        pensjon_periodisering = 0.0
    utenfor = round(sum(
        ledger.bevegelse(k) - sum(p["beloep"] for p in ledger.aktive
                                  if p["konto"] == k and ledger.er_lonnsbilag(p))
        for k in konti), 2)
    forklaringer = [
        ("(1) Pensjon periodisering (regnskap − innrapportert i terminen)", pensjon_periodisering),
        ("(2) Bevegelse på lønnskonti utenfor lønnsbilag", utenfor),
    ]
    forste_forklaring = rad
    for tekst, v in forklaringer:
        celle(ws, rad, 1, tekst)
        celle(ws, rad, 2, v, nf=KRONER)
        rad += 1
    celle(ws, rad, 1, "(3) Avrunding grunnlag (lønn per måned, pensjon per bilag)")
    avrunding_rad = rad
    if a07_grunnlag is None:
        celle(ws, rad, 2, IKKE_OPPGITT, nf=KRONER)
    else:
        celle(ws, rad, 2,
              f"=ROUND(B{diff_rad}-SUM(B{forste_forklaring}:B{rad - 1}),2)", nf=KRONER)
    rad += 1
    celle(ws, rad, 1, "Uforklart differanse", fet=True)
    if a07_grunnlag is None:
        celle(ws, rad, 2, IKKE_OPPGITT, fet=True, nf=KRONER)
    else:
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
    kostnadsfort = ledger.bevegelse(5400) + frigjort
    for tekst, v, fet in [
        ("5400 Arbeidsgiveravgift (bevegelse)", round(ledger.bevegelse(5400), 2), False),
        ("+ Frigjort AGA av utbetalte feriepenger (2785-debet mot 5400)", round(frigjort, 2), False),
        ("→ Kostnadsført", round(kostnadsfort, 2), True),
        ("Innrapportert A07", verdi(aga_termin), False),
        ("Avvik (øre-avrunding)",
         IKKE_OPPGITT if aga_termin is None else round(kostnadsfort - aga_termin, 2), True),
    ]:
        celle(ws, rad, 1, tekst, fet=fet)
        celle(ws, rad, 2, v, fet=fet, nf=KRONER)
        rad += 1
    rad += 1

    seksjon(ws, rad, "4. Skyldig AGA – konto 2770")
    rad += 1
    betalt = sum(p["beloep"] for p in ledger.aktive
                 if p["konto"] == 2770 and ledger.er_betaling(p))
    kreditert = -ledger.sum_konto(2770, ledger.er_aga_postering)
    avrunding = -ledger.sum_konto(2770, ledger.er_avrunding)
    andre = 0.0
    for tekst, v, fet in [
        ("IB 2770", round(-ledger.ib(2770), 2), False),
        ("− Betalt i terminen (Betaling: Terminoppgave)", round(-betalt, 2), False),
        ("+ Kreditert lønnsbilag + pensjonsbilag − NAV-refusjon", round(kreditert, 2), False),
        ("− Avrundingsbilag (A-melding lønn)", round(avrunding, 2), False),
        ("− Andre føringer 2770", andre, False),
        ("→ Beregnet UB", round(-ledger.ib(2770) - betalt + kreditert + avrunding, 2), True),
        ("UB 2770 saldobalanse", round(-ledger.ub(2770), 2), False),
        ("Innrapportert termin (A07)", verdi(aga_termin), False),
        ("UB − innrapportert (restsaldo)",
         IKKE_OPPGITT if aga_termin is None else round(-ledger.ub(2770) - aga_termin, 2), True),
    ]:
        celle(ws, rad, 1, tekst, fet=fet)
        celle(ws, rad, 2, v, fet=fet, nf=KRONER)
        rad += 1
    rad += 1

    seksjon(ws, rad, "5. Innbetaling")
    rad += 1
    forfall = _forfall(a07, ledger)
    belop = IKKE_OPPGITT if aga_termin is None else f"{aga_termin:,.0f} kr".replace(",", " ")
    celle(ws, rad, 1, f"Skyldig AGA termin {ledger.d.get('periode', {}).get('termin', '')}: "
                      f"{belop} – forfall {norsk_dato(forfall)} – "
                      f"KID {a07.kid_aga or IKKE_OPPGITT} – konto {a07.kontonummer or ''}",
          farge=GRA)
    ws.merge_cells(start_row=rad, start_column=1, end_row=rad, end_column=7)
    rad += 1
    for p in sorted([p for p in ledger.aktive
                     if p["konto"] == 2770 and ledger.er_betaling(p)],
                    key=lambda x: x["dato"]):
        celle(ws, rad, 1, f"Betalt {norsk_dato(p['dato'])} bilag {p['bilag']}: {p['tekst']}")
        celle(ws, rad, 2, round(p["beloep"], 2), nf=KRONER)
        rad += 1


def ark_ytelser(wb, a07: A07, ledger: Ledger, undertittel: str) -> None:
    ws = wb.create_sheet("Ytelser A07")
    topp(ws, "Ytelser i A07 for perioden – mot konto", undertittel)
    bredder(ws, {"A": 44, "B": 12, "C": 10, "D": 16, "E": 16, "F": 14, "G": 12})
    tabellhode(ws, 7, [("Ytelse (A07)", "l"), ("AGA-pliktig", "l"), ("Konto", "l"),
                       ("A07", "r"), ("Regnskap", "r"), ("Avvik", "r"), ("Status", "l")])
    rad = 8
    forste = rad

    def status(r: int, a07_verdi) -> None:
        if a07_verdi is None:
            celle(ws, r, 6, None, nf=KRONER)
            c = celle(ws, r, 7, "AVVIK", fet=True)
        else:
            celle(ws, r, 6, f"=D{r}-E{r}", nf=KRONER)
            c = celle(ws, r, 7, f'=IF(ABS(F{r})<={YTELSE_TOLERANSE:g},"OK","AVVIK")', fet=True)
        c.alignment = Alignment(vertical="center", horizontal="center")

    def ytelsesrad(r: int, y, konto: int) -> None:
        navn = y.beskrivelse[0].upper() + y.beskrivelse[1:]
        celle(ws, r, 1, f"{navn} ({y.fordel})" if y.fordel else navn)
        celle(ws, r, 2, IKKE_OPPGITT if y.aga_pliktig is None else ("ja" if y.aga_pliktig else "nei"))
        celle(ws, r, 3, str(konto))
        celle(ws, r, 4, verdi(y.beloep), nf=KRONER)

    for konto, typer, a07_sum, regnskap in _ytelsesgrupper(a07, ledger):
        if len(typer) == 1:
            ytelsesrad(rad, typer[0], konto)
            celle(ws, rad, 5, regnskap, nf=KRONER)
            status(rad, a07_sum)
            rad += 1
            continue
        start = rad
        for y in typer:
            ytelsesrad(rad, y, konto)
            rad += 1
        celle(ws, rad, 1, f"Sum konto {konto}", fet=True)
        if a07_sum is None:
            celle(ws, rad, 4, IKKE_OPPGITT, fet=True, nf=KRONER)
        else:
            celle(ws, rad, 4, f"=SUM(D{start}:D{rad - 1})", fet=True, nf=KRONER)
        celle(ws, rad, 5, regnskap, fet=True, nf=KRONER)
        status(rad, a07_sum)
        rad += 1
    if a07.ytelser is None:
        celle(ws, rad, 1, f"Lønn og ytelser: {IKKE_OPPGITT}")
        rad += 1
    elif not a07.ytelser:
        celle(ws, rad, 1, "Ingen ytelser i A07")
        rad += 1
    if rad > forste:
        statusregler(ws, f"G{forste}:G{rad - 1}")

    rad += 1
    sum_pliktig = a07.sum_aga_pliktige_ytelser()
    celle(ws, rad, 1, "Sum AGA-pliktige ytelser (A07)", fet=True)
    if sum_pliktig is None:
        celle(ws, rad, 4, IKKE_OPPGITT, fet=True, nf=KRONER)
    else:
        celle(ws, rad, 4, f'=SUMIF(B{forste}:B{rad - 2},"ja",D{forste}:D{rad - 2})',
              fet=True, nf=KRONER)
    pliktig_rad = rad
    rad += 1
    celle(ws, rad, 1, "Avgiftsgrunnlag lønn (A07)")
    celle(ws, rad, 4, verdi(a07.grunnlag_loenn), nf=KRONER)
    grunnlag_rad = rad
    rad += 1
    celle(ws, rad, 1, "Differanse (fradrag i grunnlaget eller avrunding)")
    if sum_pliktig is None or a07.grunnlag_loenn is None:
        celle(ws, rad, 4, IKKE_OPPGITT, nf=KRONER)
    else:
        celle(ws, rad, 4, f"=D{pliktig_rad}-D{grunnlag_rad}", nf=KRONER)
    rad += 2
    for linje in [
        "Ytelsene gjelder hele perioden. A07 fra Tally har ingen fordeling per måned eller per person.",
        "Regnskap: 5000–5999 i lønnsbilag, 2940 = utbetalte feriepenger, andre konti (reise) = alle posteringer.",
        "Konto styres av ytelse_konto i ledger.json der klienten avviker fra standard.",
    ]:
        celle(ws, rad, 1, linje, farge=GRA, ramme=False)
        rad += 1


def ark_posteringer(wb, ledger: Ledger, undertittel: str) -> None:
    ws = wb.create_sheet("Posteringer")
    topp(ws, "Posteringer i perioden", undertittel)
    bredder(ws, {"A": 12, "B": 9, "C": 8, "D": 30, "E": 60, "F": 14})
    tabellhode(ws, 7, [("Dato", "l"), ("Bilag", "l"), ("Konto", "l"),
                       ("Kontonavn", "l"), ("Tekst", "l"), ("Beløp", "r")])
    ws.freeze_panes = "A8"
    rad = 8
    for p in sorted(ledger.poster, key=lambda x: (x["dato"], x["bilag"], x["konto"])):
        celle(ws, rad, 1, p["dato"][:10], ramme=False)
        celle(ws, rad, 2, int(p["bilag"]) if p["bilag"].isdigit() else p["bilag"], ramme=False)
        celle(ws, rad, 3, p["konto"], ramme=False)
        celle(ws, rad, 4, p["kontonavn"], ramme=False)
        celle(ws, rad, 5, p["tekst"], ramme=False)
        celle(ws, rad, 6, round(p["beloep"], 2), nf=KRONER, ramme=False)
        rad += 1


def bygg(a07_sti: str, ledger_sti: str, ut_sti: str) -> str:
    a07 = les_a07(a07_sti)
    with open(ledger_sti, encoding="utf-8") as f:
        ledger = Ledger(json.load(f))

    periode = ledger.d.get("periode", {})
    termin = periode.get("termin", "")
    spenn = (f"{kort_maaned(a07.fom)}–{kort_maaned(a07.tom)} {a07.fom[:4]}"
             if a07.fom and a07.tom else "")
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
    ark_ytelser(wb, a07, ledger, undertittel)
    ark_posteringer(wb, ledger, undertittel)
    wb.save(ut_sti)
    return ut_sti


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    # os_sti: Claudes scratch-mapper kan gi stier over Windows' grense på 260 tegn.
    bygg(*(os_sti(a) for a in sys.argv[1:4]))
    print(sys.argv[3])
