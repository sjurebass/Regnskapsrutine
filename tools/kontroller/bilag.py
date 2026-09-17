"""D – bilag og bokføringskvalitet."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from ..hent import Kontekst, saldo_map, ub
from ..modeller import GUL, INFO, ROD, Funn, Kontroll

OMRAADE = "Bilag"

# Bilagstyper der dokumentasjon normalt skal finnes.
KREVER_DOKUMENTASJON = ("innkommende", "inngående", "leverandør", "utgående", "faktura", "diverse", "manuelt")


def _dato(verdi) -> date | None:
    if not verdi:
        return None
    try:
        return datetime.fromisoformat(str(verdi)[:10]).date()
    except ValueError:
        return None


def _bilagsbelop(k: Kontekst) -> dict[int, float]:
    """Debetsum per bilag i perioden."""
    ut: dict[int, float] = defaultdict(float)
    for p in k.posteringer():
        bilag = (p.get("voucher") or {}).get("id")
        belop = float(p.get("amount") or 0)
        if bilag is not None and belop > 0:
            ut[bilag] += belop
    return ut


def d1_bilag_uten_vedlegg(k: Kontekst) -> list[Funn]:
    belop_per_bilag = _bilagsbelop(k)
    per_type: dict[str, list[dict]] = defaultdict(list)
    for b in k.bilag():
        if b.get("document") or b.get("attachment"):
            continue
        navn = ((b.get("voucherType") or {}).get("name") or "Ukjent bilagstype").strip()
        per_type[navn].append(b)
    funn = []
    for navn, bilag in sorted(per_type.items(), key=lambda x: -len(x[1])):
        sum_belop = sum(belop_per_bilag.get(b.get("id"), 0.0) for b in bilag)
        viktig = any(ord in navn.lower() for ord in KREVER_DOKUMENTASJON)
        eksempler = ", ".join(
            f"{b.get('number')} ({str(b.get('date'))[:10]})"
            for b in sorted(bilag, key=lambda x: -belop_per_bilag.get(x.get("id"), 0.0))[:8]
        )
        funn.append(
            Funn(
                kontroll="D1",
                omraade=OMRAADE,
                tittel=f"{len(bilag)} bilag uten vedlegg – {navn}",
                alvorlighet=(GUL if viktig else INFO),
                belop=sum_belop,
                detalj=f"Bilag: {eksempler}" + (" …" if len(bilag) > 8 else ""),
                referanse=f"uten vedlegg {navn}",
            )
        )
    return funn


def d2_observasjonskonti(k: Kontekst) -> list[Funn]:
    saldi = saldo_map(k.saldo_hittil())
    funn = []
    for nummer in k.profil.konto("observasjon"):
        saldo = round(ub(saldi, [nummer]), 2)
        if abs(saldo) < 1:
            continue
        navn = ((saldi.get(nummer) or {}).get("account") or {}).get("name") or ""
        funn.append(
            Funn(
                kontroll="D2",
                omraade=OMRAADE,
                tittel=f"Saldo på observasjonskonto {nummer} {navn}",
                alvorlighet=ROD,
                belop=saldo,
                konto=str(nummer),
                detalj=(
                    f"Saldo {saldo:,.2f} per {k.periode.til.strftime('%d.%m.%Y')}. "
                    "Kontoen skal tømmes før perioden lukkes."
                ).replace(",", " "),
                referanse=f"observasjon {nummer}",
            )
        )
    return funn


def d3_feil_periode(k: Kontekst) -> list[Funn]:
    """Posteringer der bilagsdato ligger langt fra bokføringsdato."""
    sene = []
    for p in k.posteringer():
        bilag = p.get("voucher") or {}
        bilagsdato = _dato(bilag.get("date"))
        posteringsdato = _dato(p.get("date"))
        if not bilagsdato or not posteringsdato:
            continue
        dager = (posteringsdato - bilagsdato).days
        if dager > 45:
            sene.append((dager, p, bilagsdato, posteringsdato))
    if not sene:
        return []
    sene.sort(key=lambda x: -x[0])
    sum_belop = sum(abs(float(p.get("amount") or 0)) for _, p, _, _ in sene) / 2
    detalj = "; ".join(
        f"bilag {(p.get('voucher') or {}).get('number')} datert "
        f"{bd.strftime('%d.%m.%y')} ført {pd.strftime('%d.%m.%y')} "
        f"({(p.get('description') or '')[:30]})"
        for dager, p, bd, pd in sene[:8]
    )
    return [
        Funn(
            kontroll="D3",
            omraade=OMRAADE,
            tittel=f"{len(sene)} posteringer med over 45 dagers avstand mellom bilagsdato og føring",
            alvorlighet=GUL,
            belop=sum_belop,
            detalj=detalj,
            referanse="sen føring",
        )
    ]


def d4_periodelasing(k: Kontekst) -> list[Funn]:
    forrige = k.periode.forrige()
    funn = []
    for p in k.regnskapsperioder():
        slutt = _dato(p.get("end"))
        if slutt != forrige.til:
            continue
        if not p.get("isClosed"):
            funn.append(
                Funn(
                    kontroll="D4",
                    omraade=OMRAADE,
                    tittel=f"{forrige.navn} er ikke låst",
                    alvorlighet=INFO,
                    detalj=(
                        "Perioden er ferdig, men står åpen i Tripletex. Låsing hindrer at "
                        "kunden fører bilag tilbake i tid etter at avstemmingen er gjort."
                    ),
                    referanse=f"ulåst {forrige}",
                )
            )
    return funn


def d5_runde_belop(k: Kontekst) -> list[Funn]:
    grense = max(k.profil.grense(), 10000.0)
    treff = []
    for p in k.posteringer():
        belop = float(p.get("amount") or 0)
        if abs(belop) < grense:
            continue
        if abs(belop) % 1000 != 0:
            continue
        konto = p.get("account") or {}
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        if nummer < 3000:
            continue  # balansekonti: runde beløp er normalt
        if p.get("systemGenerated"):
            continue
        treff.append(p)
    if not treff:
        return []
    detalj = "; ".join(
        f"{str(p.get('date'))[:10]} {(p.get('account') or {}).get('number')} "
        f"{float(p.get('amount') or 0):,.0f} {(p.get('description') or '')[:30]}".replace(",", " ")
        for p in sorted(treff, key=lambda x: -abs(float(x.get("amount") or 0)))[:8]
    )
    return [
        Funn(
            kontroll="D5",
            omraade=OMRAADE,
            tittel=f"{len(treff)} manuelle posteringer på runde tusen over {grense:,.0f}".replace(",", " "),
            alvorlighet=INFO,
            belop=sum(float(p.get("amount") or 0) for p in treff),
            detalj=detalj + "  → typisk skjønnsposter, sjekk at de er dokumentert",
            referanse="runde beløp",
        )
    ]


def d6_ubehandlede_bilag(k: Kontekst) -> list[Funn]:
    funn = []
    for hent, navn, kontroll_ref in (
        (k.bilagsmottak, "bilagsmottaket", "bilagsmottak"),
        (k.ikke_bokforte_bilag, "ikke bokført", "ikke bokført"),
    ):
        try:
            bilag = hent()
        except Exception as e:  # endepunktet finnes ikke på alle lisenser
            k.advarsler.append(f"D6 {navn}: {e}")
            continue
        if not bilag:
            continue
        datoer = [d for d in (_dato(b.get("date")) for b in bilag) if d]
        eldste = min(datoer) if datoer else None
        gamle = [d for d in datoer if (k.periode.til - d).days > 30]
        funn.append(
            Funn(
                kontroll="D6",
                omraade=OMRAADE,
                tittel=f"{len(bilag)} bilag ligger i {navn}",
                alvorlighet=GUL if gamle else INFO,
                detalj=(
                    (f"Eldste datert {eldste.strftime('%d.%m.%Y')}. " if eldste else "")
                    + (f"{len(gamle)} er eldre enn 30 dager." if gamle else "")
                ),
                referanse=kontroll_ref,
            )
        )
    return funn


KONTROLLER = [
    Kontroll("D1", "Bilag uten vedlegg", OMRAADE, d1_bilag_uten_vedlegg),
    Kontroll("D2", "Observasjonskonti", OMRAADE, d2_observasjonskonti),
    Kontroll("D3", "Bilagsdato mot føringsdato", OMRAADE, d3_feil_periode),
    Kontroll("D4", "Periodelåsing", OMRAADE, d4_periodelasing),
    Kontroll("D5", "Runde manuelle beløp", OMRAADE, d5_runde_belop),
    Kontroll("D6", "Ubehandlede bilag", OMRAADE, d6_ubehandlede_bilag),
]
