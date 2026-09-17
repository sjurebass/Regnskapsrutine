"""M – merverdiavgift."""

from __future__ import annotations

from collections import defaultdict
from datetime import date

from ..hent import Kontekst, bevegelse, saldo_map, ub
from ..modeller import GUL, INFO, ROD, Funn, Kontroll, Periode

OMRAADE = "Mva"

# Konti der inngående mva normalt ikke er fradragsberettiget.
TYPISK_UTEN_FRADRAG = [7350, 7355, 7360, 7400, 7420, 7500, 7770, 7790]


def _mvakonti(k: Kontekst) -> list[int]:
    numre = set()
    for gruppe in ("mva_utgaaende", "mva_inngaaende", "mva_oppgjor"):
        numre.update(k.profil.konto(gruppe))
    for konto in k.kontoer():
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        if 2700 <= nummer <= 2749:
            numre.add(nummer)
    return sorted(numre)


def _terminmaaneder(termin: int) -> tuple[int, int]:
    return termin * 2 - 1, termin * 2


# Innleveringsfrist for mva-melding per termin (dag, måned, årsforskyvning).
MVA_FRISTER = {
    1: (10, 4, 0),
    2: (10, 6, 0),
    3: (31, 8, 0),
    4: (10, 10, 0),
    5: (10, 12, 0),
    6: (10, 2, 1),
}


def _frist(aar: int, termin: int) -> date:
    dag, maaned, forskyvning = MVA_FRISTER[termin]
    return date(aar + forskyvning, maaned, dag)


def m1_mva_mot_melding(k: Kontekst) -> list[Funn]:
    """Bokført mva for terminen mot innlevert mva-melding."""
    funn = []
    konti = _mvakonti(k)
    for status in k.mva_status():
        termin = int(status.get("term") or 0)
        if not termin:
            continue
        fra_mnd, til_mnd = _terminmaaneder(termin)
        if til_mnd > k.periode.maaned:
            continue
        if str(status.get("deliveryStatus") or "").upper() not in (
            "DELIVERED",
            "LEVERT",
            "APPROVED",
            "COMPLETED",
        ):
            continue  # ikke levert ennå – fanges av M6
        fra = Periode(k.periode.aar, fra_mnd).fra
        til = Periode(k.periode.aar, til_mnd).til
        saldi = saldo_map(k.saldobalanse(fra, til))
        bokfort = -bevegelse(saldi, konti)  # positivt = skyldig
        meldt = status.get("altinnPaymentAmount")
        if meldt is None:
            continue
        differanse = round(bokfort - float(meldt), 2)
        if abs(differanse) >= 1:
            funn.append(
                Funn(
                    kontroll="M1",
                    omraade=OMRAADE,
                    tittel=f"Bokført mva avviker fra mva-meldingen for termin {termin}",
                    alvorlighet=ROD,
                    belop=differanse,
                    detalj=(
                        f"Bokført {bokfort:,.2f} mot melding {float(meldt):,.2f} for "
                        f"{fra.strftime('%d.%m')}–{til.strftime('%d.%m.%Y')}."
                    ).replace(",", " "),
                    referanse=f"mva termin {termin}",
                )
            )
    return funn


def m2_oppgjorskonto(k: Kontekst) -> list[Funn]:
    """Oppgjørskonto skal stå i null for terminer som er levert og betalt."""
    saldi = saldo_map(k.saldo_hittil())
    konti = k.profil.konto("mva_oppgjor")
    saldo = round(ub(saldi, konti), 2)
    if abs(saldo) < 1:
        return []
    betalte = [
        str(s.get("term"))
        for s in k.mva_status()
        if str(s.get("paymentStatus") or "").upper() in ("PAID", "BETALT", "COMPLETED")
    ]
    return [
        Funn(
            kontroll="M2",
            omraade=OMRAADE,
            tittel="Restsaldo på mva-oppgjørskonto",
            alvorlighet=GUL,
            belop=saldo,
            konto=", ".join(str(n) for n in konti),
            detalj=(
                f"Saldo {saldo:,.2f} per {k.periode.til.strftime('%d.%m.%Y')}. "
                + (f"Betalte terminer: {', '.join(betalte)}. " if betalte else "")
                + "Kontoen skal normalt nullstilles når terminen er betalt."
            ).replace(",", " "),
            referanse="oppgjørskonto",
        )
    ]


def m3_rimelighet_sats(k: Kontekst) -> list[Funn]:
    """Bokført mva mot sats ganger grunnlag, per mva-kode."""
    per_kode: dict[str, dict] = defaultdict(lambda: {"grunnlag": 0.0, "mva": 0.0, "pst": 0.0})
    for p in k.posteringer_hittil():
        vat = p.get("vatType") or {}
        pst = vat.get("percentage")
        if not pst:
            continue
        netto = float(p.get("amount") or 0)
        brutto = p.get("amountGross")
        if brutto is None:
            continue
        rad = per_kode[f"{vat.get('number') or ''} {vat.get('name') or ''}".strip()]
        rad["grunnlag"] += netto
        rad["mva"] += float(brutto) - netto
        rad["pst"] = float(pst)
    funn = []
    for kode, rad in sorted(per_kode.items()):
        if abs(rad["grunnlag"]) < 1000:
            continue
        forventet = rad["grunnlag"] * rad["pst"] / 100
        avvik = round(rad["mva"] - forventet, 2)
        if abs(forventet) > 0 and abs(avvik) > max(100.0, abs(forventet) * 0.01):
            funn.append(
                Funn(
                    kontroll="M3",
                    omraade=OMRAADE,
                    tittel=f"Mva-beløp stemmer ikke med satsen på kode {kode}",
                    alvorlighet=GUL,
                    belop=avvik,
                    detalj=(
                        f"Grunnlag {rad['grunnlag']:,.0f} × {rad['pst']:.0f} % gir "
                        f"{forventet:,.0f}, bokført {rad['mva']:,.0f} hittil i år."
                    ).replace(",", " "),
                    referanse=f"sats {kode}",
                )
            )
    return funn


def m4_mvakode_mot_konto(k: Kontekst) -> list[Funn]:
    """Posteringer med annen mva-kode enn kontoens standard, og fradrag på
    konti der fradrag normalt ikke gis."""
    konto_std = {}
    for konto in k.kontoer():
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        std = (konto.get("vatType") or {}).get("number")
        if std:
            konto_std[nummer] = str(std)

    avvikende: dict[tuple, dict] = defaultdict(lambda: {"antall": 0, "belop": 0.0})
    fradrag_uten_rett: dict[int, dict] = defaultdict(lambda: {"antall": 0, "mva": 0.0, "navn": ""})
    for p in k.posteringer():
        konto = p.get("account") or {}
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        vat = p.get("vatType") or {}
        kode = str(vat.get("number") or "")
        std = konto_std.get(nummer)
        if std and kode and kode != std:
            rad = avvikende[(nummer, konto.get("name") or "", kode, std)]
            rad["antall"] += 1
            rad["belop"] += float(p.get("amount") or 0)
        if nummer in TYPISK_UTEN_FRADRAG and vat.get("percentage"):
            brutto = p.get("amountGross")
            mva = float(brutto) - float(p.get("amount") or 0) if brutto is not None else 0.0
            rad = fradrag_uten_rett[nummer]
            rad["antall"] += 1
            rad["mva"] += mva
            rad["navn"] = konto.get("name") or ""

    funn = []
    for (nummer, navn, kode, std), rad in sorted(avvikende.items()):
        if abs(rad["belop"]) < k.profil.grense():
            continue
        funn.append(
            Funn(
                kontroll="M4",
                omraade=OMRAADE,
                tittel=f"Avvikende mva-kode på {nummer} {navn}",
                alvorlighet=GUL,
                belop=rad["belop"],
                konto=str(nummer),
                detalj=(
                    f"{rad['antall']} posteringer med kode {kode}, kontoens standard er {std}."
                ),
                referanse=f"mvakode {nummer} {kode}",
            )
        )
    for nummer, rad in sorted(fradrag_uten_rett.items()):
        funn.append(
            Funn(
                kontroll="M4",
                omraade=OMRAADE,
                tittel=f"Mva fradragsført på {nummer} {rad['navn']}",
                alvorlighet=GUL,
                belop=rad["mva"],
                konto=str(nummer),
                detalj=(
                    f"{rad['antall']} posteringer. Kontotypen gir normalt ikke fradragsrett – "
                    "sjekk om kodene er riktige."
                ),
                referanse=f"fradrag {nummer}",
            )
        )
    return funn


def m5_fradrag_uten_bilag(k: Kontekst) -> list[Funn]:

    uten_dok = set()
    for b in k.bilag():
        har = bool(b.get("document") or b.get("attachment"))
        if not har:
            uten_dok.add(b.get("id"))
    if not uten_dok:
        return []
    sum_mva = 0.0
    antall = 0
    eksempler = []
    for p in k.posteringer():
        bilag = p.get("voucher") or {}
        if bilag.get("id") not in uten_dok:
            continue
        vat = p.get("vatType") or {}
        if not vat.get("percentage"):
            continue
        brutto = p.get("amountGross")
        if brutto is None:
            continue
        mva = float(brutto) - float(p.get("amount") or 0)
        if mva <= 0:
            continue
        sum_mva += mva
        antall += 1
        if len(eksempler) < 8:
            eksempler.append(
                f"bilag {bilag.get('number')} {str(p.get('date'))[:10]} "
                f"{(p.get('description') or '')[:35]} mva {mva:,.0f}".replace(",", " ")
            )
    if not antall:
        return []
    return [
        Funn(
            kontroll="M5",
            omraade=OMRAADE,
            tittel=f"Mva fradragsført på {antall} bilag uten dokumentasjon",
            alvorlighet=ROD,
            belop=sum_mva,
            detalj="; ".join(eksempler),
            referanse="fradrag uten bilag",
        )
    ]


def m6_levert_og_betalt(k: Kontekst) -> list[Funn]:
    """Terminer med passert frist skal være levert, og betalt hvis de har forfalt."""
    idag = date.today()
    funn = []
    for status in k.mva_status():
        termin = int(status.get("term") or 0)
        if not termin:
            continue
        _, til_mnd = _terminmaaneder(termin)
        if til_mnd > k.periode.maaned:
            continue
        if _frist(k.periode.aar, termin) >= idag:
            continue  # fristen har ikke gått ut ennå
        levering = str(status.get("deliveryStatus") or "").upper()
        betaling = str(status.get("paymentStatus") or "").upper()
        if levering not in ("DELIVERED", "LEVERT", "APPROVED", "COMPLETED"):
            funn.append(
                Funn(
                    kontroll="M6",
                    omraade=OMRAADE,
                    tittel=f"Mva-melding termin {termin} ser ikke ut til å være levert",
                    alvorlighet=ROD,
                    belop=status.get("altinnPaymentAmount"),
                    detalj=f"Status i Tripletex: {levering or 'ukjent'}.",
                    referanse=f"levering termin {termin}",
                )
            )
        elif betaling not in ("PAID", "BETALT", "COMPLETED", "NOT_APPLICABLE"):
            funn.append(
                Funn(
                    kontroll="M6",
                    omraade=OMRAADE,
                    tittel=f"Mva termin {termin} er levert, men ikke registrert betalt",
                    alvorlighet=GUL,
                    belop=status.get("altinnPaymentAmount"),
                    detalj=f"Betalingsstatus: {betaling or 'ukjent'}.",
                    referanse=f"betaling termin {termin}",
                )
            )
    return funn


KONTROLLER = [
    Kontroll("M1", "Mva-konti mot mva-melding", OMRAADE, m1_mva_mot_melding, ("mva_pliktig",)),
    Kontroll("M2", "Oppgjørskonto nullstilt", OMRAADE, m2_oppgjorskonto, ("mva_pliktig",)),
    Kontroll("M3", "Rimelighetskontroll mva-sats", OMRAADE, m3_rimelighet_sats, ("mva_pliktig",)),
    Kontroll("M4", "Mva-kode mot konto", OMRAADE, m4_mvakode_mot_konto, ("mva_pliktig",)),
    Kontroll("M5", "Fradragsført mva uten bilag", OMRAADE, m5_fradrag_uten_bilag, ("mva_pliktig",)),
    Kontroll("M6", "Mva-melding levert og betalt", OMRAADE, m6_levert_og_betalt, ("mva_pliktig",)),
]
