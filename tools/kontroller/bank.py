"""B – bank og likvider."""

from __future__ import annotations

from datetime import date, datetime

from ..hent import Kontekst, saldo_map
from ..modeller import GUL, INFO, ROD, Funn, Kontroll

OMRAADE = "Bank"


def _dato(verdi) -> date | None:
    if not verdi:
        return None
    try:
        return datetime.fromisoformat(str(verdi)[:10]).date()
    except ValueError:
        return None


def _bankkontoer(k: Kontekst) -> list[dict]:
    return [konto for konto in k.kontoer() if konto.get("isBankAccount") and not konto.get("isInactive")]


def _umatchede(k: Kontekst) -> list[tuple[dict, dict]]:
    """(avstemming, transaksjon) for transaksjoner som ikke er matchet."""
    ut = []
    for avst in k.bankavstemminger():
        for t in avst.get("transactions") or []:
            if not t.get("matched"):
                ut.append((avst, t))
    return ut


def b1_apne_bankposter(k: Kontekst) -> list[Funn]:
    grense = k.periode.til.toordinal() - 30
    funn = []
    per_konto: dict[str, list] = {}
    for avst, t in _umatchede(k):
        d = _dato(t.get("postedDate"))
        if d and d.toordinal() <= grense:
            konto = (avst.get("account") or {}).get("number") or "?"
            per_konto.setdefault(str(konto), []).append((d, t))
    for konto, poster in sorted(per_konto.items()):
        sum_belop = sum(float(t.get("amountCurrency") or 0) for _, t in poster)
        eldste = min(d for d, _ in poster)
        detalj = "; ".join(
            f"{d.strftime('%d.%m')} {float(t.get('amountCurrency') or 0):,.0f} "
            f"{(t.get('description') or '')[:40]}".replace(",", " ")
            for d, t in sorted(poster)[:8]
        )
        if len(poster) > 8:
            detalj += f" … (+{len(poster) - 8} til)"
        funn.append(
            Funn(
                kontroll="B1",
                omraade=OMRAADE,
                tittel=f"{len(poster)} uavstemte bankposter eldre enn 30 dager",
                alvorlighet=GUL,
                belop=sum_belop,
                konto=konto,
                detalj=f"Eldste {eldste.strftime('%d.%m.%Y')}. {detalj}",
                referanse=f"konto {konto}",
            )
        )
    return funn


def b2_bank_mot_kontoutdrag(k: Kontekst) -> list[Funn]:
    """Bokført saldo mot bankens saldo ved periodeslutt."""
    saldi = saldo_map(k.saldo_hittil())
    funn = []
    for avst in k.bankavstemminger():
        periode = avst.get("accountingPeriod") or {}
        slutt = _dato(periode.get("end"))
        if slutt != k.periode.til:
            continue
        konto = avst.get("account") or {}
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        bank_saldo = avst.get("bankAccountClosingBalanceCurrency")
        if bank_saldo is None:
            continue
        bokfort = float((saldi.get(nummer) or {}).get("closingBalance") or 0)
        differanse = round(bokfort - float(bank_saldo), 2)
        if abs(differanse) >= 1:
            funn.append(
                Funn(
                    kontroll="B2",
                    omraade=OMRAADE,
                    tittel=f"Bokført saldo avviker fra banken på {nummer} {konto.get('name') or ''}",
                    alvorlighet=ROD,
                    belop=differanse,
                    konto=str(nummer),
                    detalj=(
                        f"Bokført {bokfort:,.2f} mot banken {float(bank_saldo):,.2f} "
                        f"per {k.periode.til.strftime('%d.%m.%Y')}"
                    ).replace(",", " "),
                    referanse=f"konto {nummer} ub",
                )
            )
    return funn


def b3_bankkonti_uten_avstemming(k: Kontekst) -> list[Funn]:
    """Bankkonti som ikke har en avstemming for perioden."""
    avstemte = set()
    for avst in k.bankavstemminger():
        periode = avst.get("accountingPeriod") or {}
        if _dato(periode.get("end")) == k.periode.til:
            nummer = (avst.get("account") or {}).get("number")
            if nummer:
                avstemte.add(str(nummer))
    saldi = saldo_map(k.saldo_hittil())
    funn = []
    for konto in _bankkontoer(k):
        nummer = str(konto.get("number"))
        if nummer in avstemte:
            continue
        try:
            ub = float((saldi.get(int(nummer)) or {}).get("closingBalance") or 0)
        except (TypeError, ValueError):
            ub = 0.0
        funn.append(
            Funn(
                kontroll="B3",
                omraade=OMRAADE,
                tittel=f"Ingen bankavstemming for {nummer} {konto.get('name') or ''}",
                alvorlighet=GUL if abs(ub) > 0 else INFO,
                belop=ub,
                konto=nummer,
                detalj=(
                    "Kontoen er merket som bankkonto, men har ingen avstemming for "
                    f"{k.periode}. Mangler banktilkobling eller er ikke avstemt."
                ),
                referanse=f"konto {nummer} mangler avstemming",
            )
        )
    return funn


def b4_negativ_bank(k: Kontekst) -> list[Funn]:
    saldi = saldo_map(k.saldo_hittil())
    funn = []
    for konto in _bankkontoer(k):
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        ub = float((saldi.get(nummer) or {}).get("closingBalance") or 0)
        if ub < 0:
            funn.append(
                Funn(
                    kontroll="B4",
                    omraade=OMRAADE,
                    tittel=f"Negativ saldo på {nummer} {konto.get('name') or ''}",
                    alvorlighet=ROD if ub < -1000 else GUL,
                    belop=ub,
                    konto=str(nummer),
                    detalj=(
                        "Bankkonto i minus ved periodeslutt. Sjekk om det er kassekreditt, "
                        "feilført betaling eller manglende innbetaling."
                    ),
                    referanse=f"konto {nummer} negativ",
                )
            )
    return funn


def b5_gamle_apne_poster(k: Kontekst) -> list[Funn]:
    grense = k.periode.til.toordinal() - 90
    per_konto: dict[str, list] = {}
    for avst, t in _umatchede(k):
        d = _dato(t.get("postedDate"))
        if d and d.toordinal() <= grense:
            konto = str((avst.get("account") or {}).get("number") or "?")
            per_konto.setdefault(konto, []).append((d, t))
    funn = []
    for konto, poster in sorted(per_konto.items()):
        sum_belop = sum(float(t.get("amountCurrency") or 0) for _, t in poster)
        eldste = min(d for d, _ in poster)
        funn.append(
            Funn(
                kontroll="B5",
                omraade=OMRAADE,
                tittel=f"{len(poster)} bankposter har ligget åpne over 90 dager",
                alvorlighet=ROD,
                belop=sum_belop,
                konto=konto,
                detalj=(
                    f"Eldste {eldste.strftime('%d.%m.%Y')}. Disse bør dokumenteres eller "
                    "føres ut før årsoppgjøret."
                ),
                referanse=f"konto {konto} over 90 dager",
            )
        )
    return funn


KONTROLLER = [
    Kontroll("B1", "Åpne bankposter over 30 dager", OMRAADE, b1_apne_bankposter),
    Kontroll("B2", "Bokført bank mot kontoutdrag", OMRAADE, b2_bank_mot_kontoutdrag),
    Kontroll("B3", "Bankkonti uten avstemming", OMRAADE, b3_bankkonti_uten_avstemming),
    Kontroll("B4", "Negativ bank eller kasse", OMRAADE, b4_negativ_bank),
    Kontroll("B5", "Bankposter åpne over 90 dager", OMRAADE, b5_gamle_apne_poster),
]
