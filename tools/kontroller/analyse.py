"""A – drift, rimelighet og balanseopprydding."""

from __future__ import annotations

from collections import defaultdict

from ..hent import Kontekst, bevegelse, saldo_map, ub
from ..modeller import GUL, INFO, ROD, Funn, Kontroll

OMRAADE = "Analyse"


def _resultatkonti(saldi: dict[int, dict]) -> dict[int, dict]:
    return {n: r for n, r in saldi.items() if 3000 <= n <= 8999}


def omsetning_hittil(k: Kontekst) -> float:
    """Sum inntekt (kontoklasse 3) hittil i år, brukt som vesentlighetsgrunnlag."""
    saldi = saldo_map(k.saldo_hittil())
    return abs(sum(float(r.get("sumAmount") or 0) for n, r in saldi.items() if 3000 <= n <= 3999))


def _sammenlign(k: Kontekst, naa: dict, foer: dict, kontroll: str, etikett: str) -> list[Funn]:
    grense = k.profil.grense(omsetning_hittil(k))
    funn = []
    for nummer, rad in sorted(_resultatkonti(naa).items()):
        belop_naa = float(rad.get("sumAmount") or 0)
        belop_foer = float((foer.get(nummer) or {}).get("sumAmount") or 0)
        endring = belop_naa - belop_foer
        if abs(endring) < grense:
            continue
        if belop_foer == 0:
            prosent = None
        else:
            prosent = abs(endring) / abs(belop_foer) * 100
            if prosent < k.profil.avvik_prosent:
                continue
        navn = (rad.get("account") or {}).get("name") or ""
        funn.append(
            Funn(
                kontroll=kontroll,
                omraade=OMRAADE,
                tittel=f"{nummer} {navn}: {etikett}",
                alvorlighet=INFO,
                belop=endring,
                konto=str(nummer),
                detalj=(
                    f"{belop_naa:,.0f} mot {belop_foer:,.0f}"
                    + (f" ({prosent:.0f} % endring)" if prosent is not None else " (ingen sammenligning)")
                ).replace(",", " "),
                referanse=f"{kontroll} konto {nummer}",
            )
        )
    funn.sort(key=lambda f: -abs(f.belop or 0))
    return funn[:15]


def a1_mot_forrige_maaned(k: Kontekst) -> list[Funn]:
    return _sammenlign(
        k,
        saldo_map(k.saldo_perioden()),
        saldo_map(k.saldo_forrige_maaned()),
        "A1",
        f"avvik mot {k.periode.forrige().navn}",
    )


def a2_mot_ifjor(k: Kontekst) -> list[Funn]:
    return _sammenlign(
        k,
        saldo_map(k.saldo_perioden()),
        saldo_map(k.saldo_samme_maaned_ifjor()),
        "A2",
        f"avvik mot {k.periode.forrige_aar().navn}",
    )


def a3_manglende_faste_kostnader(k: Kontekst) -> list[Funn]:
    """Konti som har hatt kostnad hver av de tre foregående månedene, men ikke nå."""
    per_konto_maaned: dict[int, set[int]] = defaultdict(set)
    navn: dict[int, str] = {}
    belop: dict[tuple[int, int], float] = defaultdict(float)
    for p in k.posteringer_hittil():
        konto = p.get("account") or {}
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        if not 4000 <= nummer <= 7999:
            continue
        dato = str(p.get("date") or "")
        if len(dato) < 7:
            continue
        mnd = int(dato[5:7])
        per_konto_maaned[nummer].add(mnd)
        navn[nummer] = konto.get("name") or ""
        belop[(nummer, mnd)] += float(p.get("amount") or 0)

    naa = k.periode.maaned
    tidligere = [naa - 3, naa - 2, naa - 1]
    if min(tidligere) < 1:
        return []
    funn = []
    for nummer, maaneder in sorted(per_konto_maaned.items()):
        if naa in maaneder:
            continue
        if not all(m in maaneder for m in tidligere):
            continue
        snitt = sum(belop[(nummer, m)] for m in tidligere) / 3
        if abs(snitt) < k.profil.grense() / 5:
            continue
        funn.append(
            Funn(
                kontroll="A3",
                omraade=OMRAADE,
                tittel=f"Fast kostnad mangler: {nummer} {navn[nummer]}",
                alvorlighet=GUL,
                belop=snitt,
                konto=str(nummer),
                detalj=(
                    f"Kontoen har hatt bevegelse hver måned de tre foregående månedene "
                    f"(snitt {snitt:,.0f}), men ingenting i {k.periode.navn}. "
                    "Mangler faktura, eller er den ført et annet sted?"
                ).replace(",", " "),
                referanse=f"mangler konto {nummer}",
            )
        )
    return funn


def a4_avskrivninger(k: Kontekst) -> list[Funn]:
    saldi = saldo_map(k.saldo_perioden())
    konti = k.profil.konto("avskrivning")
    i_maaneden = bevegelse(saldi, konti)
    funn = []
    anlegg = []
    try:
        anlegg = [a for a in k.anleggsmidler() if str(a.get("status") or "").upper() != "DISPOSED"]
    except Exception as e:
        k.advarsler.append(f"A4 anleggsmidler: {e}")
    if anlegg and abs(i_maaneden) < 1:
        funn.append(
            Funn(
                kontroll="A4",
                omraade=OMRAADE,
                tittel="Ingen avskrivninger bokført i måneden",
                alvorlighet=GUL,
                belop=None,
                konto=", ".join(str(n) for n in konti),
                detalj=(
                    f"{len(anlegg)} aktive anleggsmidler i registeret, men ingen bevegelse "
                    f"på avskrivningskontoene i {k.periode.navn}."
                ),
                referanse="avskrivning mangler",
            )
        )
    # nyanskaffelser kostnadsført i stedet for aktivert
    grense = max(k.profil.grense(), 15000.0)
    kandidater = []
    for p in k.posteringer():
        konto = p.get("account") or {}
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        if not (6500 <= nummer <= 6599 or 6600 <= nummer <= 6799):
            continue
        belop = float(p.get("amount") or 0)
        if belop >= grense:
            kandidater.append((nummer, konto.get("name") or "", p, belop))
    if kandidater:
        funn.append(
            Funn(
                kontroll="A4",
                omraade=OMRAADE,
                tittel=f"{len(kandidater)} store kjøp ført som kostnad – vurder aktivering",
                alvorlighet=INFO,
                belop=sum(b for _, _, _, b in kandidater),
                detalj="; ".join(
                    f"{n} {navn} {b:,.0f} ({(p.get('description') or '')[:30]})".replace(",", " ")
                    for n, navn, p, b in sorted(kandidater, key=lambda x: -x[3])[:6]
                ),
                referanse="aktivering",
            )
        )
    return funn


def a5_sovende_balansekonti(k: Kontekst) -> list[Funn]:
    naa = saldo_map(k.saldo_hittil())
    ifjor = saldo_map(k.saldo_hittil_ifjor())
    funn = []
    for nummer, rad in sorted(naa.items()):
        if nummer >= 3000:
            continue
        saldo = float(rad.get("closingBalance") or 0)
        if abs(saldo) < k.profil.grense():
            continue
        if abs(float(rad.get("sumAmount") or 0)) >= 1:
            continue
        if abs(float((ifjor.get(nummer) or {}).get("sumAmount") or 0)) >= 1:
            continue
        navn = (rad.get("account") or {}).get("name") or ""
        funn.append(
            Funn(
                kontroll="A5",
                omraade=OMRAADE,
                tittel=f"Ingen bevegelse på {nummer} {navn}",
                alvorlighet=INFO,
                belop=saldo,
                konto=str(nummer),
                detalj=(
                    f"Saldo {saldo:,.0f} uten bevegelse verken i år eller i fjor. "
                    "Kandidat for opprydding eller dokumentasjon."
                ).replace(",", " "),
                referanse=f"sovende {nummer}",
            )
        )
    return funn[:15]


KONTROLLER = [
    Kontroll("A1", "Avvik mot forrige måned", OMRAADE, a1_mot_forrige_maaned),
    Kontroll("A2", "Avvik mot samme måned i fjor", OMRAADE, a2_mot_ifjor),
    Kontroll("A3", "Manglende faste kostnader", OMRAADE, a3_manglende_faste_kostnader),
    Kontroll("A4", "Avskrivninger og aktivering", OMRAADE, a4_avskrivninger, ("anleggsmidler",)),
    Kontroll("A5", "Sovende balansekonti", OMRAADE, a5_sovende_balansekonti),
]
