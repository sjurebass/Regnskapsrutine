"""E – eier og nærstående."""

from __future__ import annotations

import re

from ..hent import Kontekst, bevegelse, saldo_map, ub
from ..modeller import GUL, INFO, ROD, Funn, Kontroll

OMRAADE = "Eier"

# Ord som ofte følger med private uttak. Treff er en påminnelse, ikke en konklusjon.
PRIVATORD = [
    "vinmonopol", "apotek", "ferie", "hotell", "reise", "restaurant", "kino",
    "gave", "klær", "sport", "treningssenter", "sats", "elixia", "barnehage",
    "sfo", "tannlege", "lege", "privat", "møbler", "interiør", "hage",
]


def e1_mellomregning(k: Kontekst) -> list[Funn]:
    saldi = saldo_map(k.saldo_hittil())
    funn = []
    for nummer in k.profil.konto("mellomregning"):
        rad = saldi.get(nummer)
        if not rad:
            continue
        saldo = round(float(rad.get("closingBalance") or 0), 2)
        endring = round(float(rad.get("sumAmount") or 0), 2)
        navn = (rad.get("account") or {}).get("name") or ""
        if abs(saldo) < 1 and abs(endring) < 1:
            continue
        # Positiv saldo = selskapet har en fordring på eier eller ansatt
        if saldo > 0:
            eierkonto = nummer in (2910, 2911, 2920, 1570)
            forklaring = (
                "Lån til aksjonær behandles skattemessig som utbytte – avklar om det "
                "finnes reell låneavtale med sikkerhet og markedsrente, eller om beløpet "
                "skal utbyttebeskattes."
                if eierkonto
                else "Fordring på ansatt eller nærstående. Sjekk at den er reell, "
                "dokumentert og skal stå i balansen."
            )
            funn.append(
                Funn(
                    kontroll="E1",
                    omraade=OMRAADE,
                    tittel=f"Selskapet har en fordring på {nummer} {navn}",
                    alvorlighet=ROD if eierkonto else GUL,
                    belop=saldo,
                    konto=str(nummer),
                    detalj=(
                        f"Saldo {saldo:,.2f} per {k.periode.til.strftime('%d.%m.%Y')} "
                        f"(endret {endring:+,.2f} hittil i år). " + forklaring
                    ).replace(",", " "),
                    referanse=f"mellomregning {nummer}",
                )
            )
        elif abs(endring) >= k.profil.grense():
            funn.append(
                Funn(
                    kontroll="E1",
                    omraade=OMRAADE,
                    tittel=f"Stor bevegelse på mellomregning {nummer} {navn}",
                    alvorlighet=INFO,
                    belop=endring,
                    konto=str(nummer),
                    detalj=(
                        f"Saldo {saldo:,.2f}, endret {endring:+,.2f} hittil i år."
                    ).replace(",", " "),
                    referanse=f"mellomregning bevegelse {nummer}",
                )
            )
    return funn


def e2_private_uttak(k: Kontekst) -> list[Funn]:
    monster = re.compile("|".join(PRIVATORD), re.I)
    treff = []
    for p in k.posteringer():
        konto = p.get("account") or {}
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        if not 4000 <= nummer <= 7999:
            continue
        tekst = " ".join(
            filter(
                None,
                [p.get("description") or "", (p.get("supplier") or {}).get("name") or ""],
            )
        )
        if monster.search(tekst):
            treff.append((nummer, konto.get("name") or "", tekst, float(p.get("amount") or 0)))
    if not treff:
        return []
    return [
        Funn(
            kontroll="E2",
            omraade=OMRAADE,
            tittel=f"{len(treff)} kostnader med privat preg – til vurdering",
            alvorlighet=INFO,
            belop=sum(b for _, _, _, b in treff),
            detalj="; ".join(
                f"{n} {navn}: {tekst[:40]} {b:,.0f}".replace(",", " ")
                for n, navn, tekst, b in sorted(treff, key=lambda x: -abs(x[3]))[:10]
            ),
            referanse="privat preg",
        )
    ]


KONTROLLER = [
    Kontroll("E1", "Mellomregning eier", OMRAADE, e1_mellomregning),
    Kontroll("E2", "Kostnader med privat preg", OMRAADE, e2_private_uttak),
]
