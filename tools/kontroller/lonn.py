"""L – lønn, skattetrekk og arbeidsgiveravgift.

Den fulle A07-avstemmingen ligger i skillen `lonnsavstemming-a07`; her kjøres
kontrollene som kan gjøres uten A07-filen, pluss en påminnelse om at
terminavstemmingen mangler.
"""

from __future__ import annotations

import os
from calendar import monthrange
from collections import defaultdict
from datetime import date

from ..hent import Kontekst, bevegelse, saldo_map, ub
from ..modeller import GUL, INFO, ROD, Funn, Kontroll, Periode

OMRAADE = "Lønn"


def _forfall(aar: int, termin: int) -> date:
    """Skattetrekk og AGA forfaller den 15. i måneden etter terminslutt."""
    mnd = termin * 2 + 1
    if mnd > 12:
        return date(aar + 1, mnd - 12, 15)
    return date(aar, mnd, 15)


def _ikke_forfalt_bevegelse(k: Kontekst, konti: list[int]) -> float:
    """Sum bevegelse på konti for de terminene som ennå ikke har forfalt.

    Regnes ut fra posteringene hittil i år, så det koster ingen ekstra API-kall.
    """
    maalkonti = set(konti)
    sum_belop = 0.0
    for p in k.posteringer_hittil():
        konto = p.get("account") or {}
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        if nummer not in maalkonti:
            continue
        dato = str(p.get("date") or "")[:10]
        if len(dato) < 7:
            continue
        termin = (int(dato[5:7]) + 1) // 2
        if _forfall(k.periode.aar, termin) <= k.periode.til:
            continue
        sum_belop += float(p.get("amount") or 0)
    return sum_belop


def l1_a07_mangler(k: Kontekst) -> list[Funn]:
    """Er terminen avstemt mot A07? Filnavnkonvensjon fra lonnsavstemming-a07."""
    if k.periode.maaned % 2 != 0:
        return []  # terminen er ikke ferdig
    termin = k.periode.termin
    mappe = os.path.join(k.klient.mappe, str(k.periode.aar))
    if not os.path.isdir(mappe):
        filer = []
    else:
        filer = [f for f in os.listdir(mappe) if f.lower().endswith((".xlsx", ".pdf"))]
    treff = [f for f in filer if f"Termin {termin}" in f and "ønnsavstemming" in f]
    if treff:
        return []
    return [
        Funn(
            kontroll="L1",
            omraade=OMRAADE,
            tittel=f"A07-avstemming mangler for termin {termin}",
            alvorlighet=GUL,
            detalj=(
                f"Fant ingen «Termin {termin} {k.periode.aar} Lønnsavstemming …» i {mappe}. "
                "Kjør skillen lonnsavstemming-a07 med A07-filen fra Altinn."
            ),
            referanse=f"a07 termin {termin}",
        )
    ]


def l2_trekk_og_aga(k: Kontekst) -> list[Funn]:
    saldi = saldo_map(k.saldo_hittil())
    funn = []
    for nokkel, navn, kontroll_navn in (
        ("forskuddstrekk", "Forskuddstrekk", "skyldig forskuddstrekk"),
        ("skyldig_aga", "Arbeidsgiveravgift", "skyldig arbeidsgiveravgift"),
    ):
        konti = k.profil.konto(nokkel)
        faktisk = round(ub(saldi, konti), 2)
        forventet = round(_ikke_forfalt_bevegelse(k, konti), 2)
        differanse = round(faktisk - forventet, 2)
        if abs(differanse) < 1:
            continue
        funn.append(
            Funn(
                kontroll="L2",
                omraade=OMRAADE,
                tittel=f"{navn}: saldo stemmer ikke med terminer som ikke har forfalt",
                alvorlighet=ROD if abs(differanse) > k.profil.grense() else GUL,
                belop=differanse,
                konto=", ".join(str(n) for n in konti),
                detalj=(
                    f"Saldo {faktisk:,.2f} per {k.periode.til.strftime('%d.%m.%Y')}, "
                    f"forventet {forventet:,.2f} ut fra hvilke terminer som er forfalt. "
                    "Differansen er enten ubetalt termin, betaling som ikke er bokført, "
                    "eller rest fra i fjor."
                ).replace(",", " "),
                referanse=kontroll_navn,
            )
        )
    return funn


def l3_feriepenger(k: Kontekst) -> list[Funn]:
    saldi = saldo_map(k.saldo_hittil())
    konti = k.profil.konto("feriepenger")
    avsatt_bevegelse = -round(bevegelse(saldi, konti), 2)  # positivt = avsatt i år
    fra_lonn = round(
        sum(float(p.get("vacationAllowanceAmount") or 0) for p in k.lonnsslipper()), 2
    )
    if fra_lonn == 0 and avsatt_bevegelse == 0:
        return []
    differanse = round(avsatt_bevegelse - fra_lonn, 2)
    if abs(differanse) < max(100.0, abs(fra_lonn) * 0.005):
        return []
    return [
        Funn(
            kontroll="L3",
            omraade=OMRAADE,
            tittel="Feriepengeavsetning stemmer ikke med lønnskjøringene",
            alvorlighet=GUL,
            belop=differanse,
            konto=", ".join(str(n) for n in konti),
            detalj=(
                f"Avsatt i regnskapet {avsatt_bevegelse:,.2f} hittil i år mot "
                f"{fra_lonn:,.2f} fra lønnsslippene. Sjekk sats (10,2 % / 12 %) og "
                "om avsetningen er periodisert riktig."
            ).replace(",", " "),
            referanse="feriepengeavsetning",
        )
    ]


def l4_lonn_kjort(k: Kontekst) -> list[Funn]:
    """Er det kjørt lønn i måneden? Selve a-meldingskontrollen gjøres i A07."""
    i_maaneden = [p for p in k.lonnsslipper() if int(p.get("month") or 0) == k.periode.maaned]
    if i_maaneden:
        return []
    tidligere = [p for p in k.lonnsslipper() if int(p.get("month") or 0) < k.periode.maaned]
    if not tidligere:
        return []
    return [
        Funn(
            kontroll="L4",
            omraade=OMRAADE,
            tittel=f"Ingen lønnskjøring registrert i {k.periode.navn}",
            alvorlighet=GUL,
            detalj=(
                "Det er kjørt lønn tidligere i år, men ikke i denne måneden. "
                "Sjekk om lønn mangler, eller om a-meldingen likevel skal leveres "
                "(frist den 5. i måneden etter)."
            ),
            referanse="lønn mangler",
        )
    ]


def l5_skyldig_lonn(k: Kontekst) -> list[Funn]:
    saldi = saldo_map(k.saldo_hittil())
    konti = k.profil.konto("skyldig_lonn")
    saldo = round(ub(saldi, konti), 2)
    if abs(saldo) < 1:
        return []
    return [
        Funn(
            kontroll="L5",
            omraade=OMRAADE,
            tittel="Skyldig lønn står igjen ved månedsslutt",
            alvorlighet=GUL,
            belop=saldo,
            konto=", ".join(str(n) for n in konti),
            detalj=(
                f"Saldo {saldo:,.2f} per {k.periode.til.strftime('%d.%m.%Y')}. "
                "Normalt skal kontoen være tom etter at lønn er utbetalt."
            ).replace(",", " "),
            referanse="skyldig lønn",
        )
    ]


KONTROLLER = [
    Kontroll("L1", "A07-avstemming utført", OMRAADE, l1_a07_mangler, ("lonn",)),
    Kontroll("L2", "Skyldig trekk og AGA", OMRAADE, l2_trekk_og_aga, ("lonn",)),
    Kontroll("L3", "Feriepengeavsetning", OMRAADE, l3_feriepenger, ("lonn",)),
    Kontroll("L4", "Lønnskjøring i måneden", OMRAADE, l4_lonn_kjort, ("lonn",)),
    Kontroll("L5", "Skyldig lønn nullstilt", OMRAADE, l5_skyldig_lonn, ("lonn",)),
]
