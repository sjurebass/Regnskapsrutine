"""R – kunde- og leverandørreskontro."""

from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime

from ..hent import Kontekst, navn_av, saldo_map
from ..modeller import GUL, INFO, ROD, Funn, Kontroll

OMRAADE = "Reskontro"


def _dato(verdi) -> date | None:
    if not verdi:
        return None
    try:
        return datetime.fromisoformat(str(verdi)[:10]).date()
    except ValueError:
        return None


def _apne_per_type(k: Kontekst, ledger_type: str) -> list[dict]:
    ut = []
    for rad in k.apne_poster():
        konto = rad.get("account") or {}
        if (konto.get("ledgerType") or "").upper() == ledger_type:
            ut.append(rad)
    return ut


def _reskontroavstemming(k: Kontekst, ledger_type: str, kontroll: str, navn: str) -> list[Funn]:
    saldi = saldo_map(k.saldo_hittil())
    funn = []
    for rad in _apne_per_type(k, ledger_type):
        konto = rad.get("account") or {}
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        sum_apne = sum(float(p.get("amount") or 0) for p in rad.get("postings") or [])
        ub = float((saldi.get(nummer) or {}).get("closingBalance") or 0)
        differanse = round(ub - sum_apne, 2)
        if abs(differanse) >= 1:
            funn.append(
                Funn(
                    kontroll=kontroll,
                    omraade=OMRAADE,
                    tittel=f"{navn} stemmer ikke mot konto {nummer}",
                    alvorlighet=ROD,
                    belop=differanse,
                    konto=str(nummer),
                    detalj=(
                        f"Sum åpne poster {sum_apne:,.2f} mot hovedbok {ub:,.2f} "
                        f"per {k.periode.til.strftime('%d.%m.%Y')}. Differansen skyldes "
                        "som regel direkteposteringer på reskontrokontoen."
                    ).replace(",", " "),
                    referanse=f"konto {nummer} reskontro",
                )
            )
    return funn


def r1_kundereskontro(k: Kontekst) -> list[Funn]:
    return _reskontroavstemming(k, "CUSTOMER", "R1", "Kundereskontro")


def r2_leverandorreskontro(k: Kontekst) -> list[Funn]:
    return _reskontroavstemming(k, "SUPPLIER", "R2", "Leverandørreskontro")


def _saldo_per_motpart(rader: list[dict], felt: str) -> dict[str, tuple[str, float, int]]:
    ut: dict[str, tuple[str, float, int]] = {}
    sum_per: dict[str, float] = defaultdict(float)
    antall: dict[str, int] = defaultdict(int)
    navn: dict[str, str] = {}
    for rad in rader:
        for p in rad.get("postings") or []:
            motpart = p.get(felt) or {}
            nokkel = str(motpart.get("id") or "ukjent")
            sum_per[nokkel] += float(p.get("amount") or 0)
            antall[nokkel] += 1
            navn[nokkel] = navn_av(motpart) or "Uten reskontro"
    for nokkel, belop in sum_per.items():
        ut[nokkel] = (navn[nokkel], belop, antall[nokkel])
    return ut


def r3_feil_fortegn(k: Kontekst) -> list[Funn]:
    grense = k.profil.grense()
    funn = []
    kunder = _saldo_per_motpart(_apne_per_type(k, "CUSTOMER"), "customer")
    for _, (navn, belop, antall) in sorted(kunder.items(), key=lambda x: x[1][1]):
        if belop < -grense:
            funn.append(
                Funn(
                    kontroll="R3",
                    omraade=OMRAADE,
                    tittel=f"Kunde med kreditsaldo: {navn}",
                    alvorlighet=GUL,
                    belop=belop,
                    detalj=(
                        f"{antall} åpne poster gir kreditsaldo. Typisk uidentifisert "
                        "innbetaling, dobbeltbetaling eller kreditnota som ikke er koblet."
                    ),
                    referanse=f"kunde {navn}",
                )
            )
    lev = _saldo_per_motpart(_apne_per_type(k, "SUPPLIER"), "supplier")
    for _, (navn, belop, antall) in sorted(lev.items(), key=lambda x: -x[1][1]):
        if belop > grense:
            funn.append(
                Funn(
                    kontroll="R3",
                    omraade=OMRAADE,
                    tittel=f"Leverandør med debetsaldo: {navn}",
                    alvorlighet=GUL,
                    belop=belop,
                    detalj=(
                        f"{antall} åpne poster gir debetsaldo. Typisk forskuddsbetaling, "
                        "dobbeltbetaling eller kreditnota som ikke er koblet."
                    ),
                    referanse=f"leverandør {navn}",
                )
            )
    return funn


def _alder(poster: list[dict], til: date) -> dict[str, float]:
    bøtter = {"0-30": 0.0, "31-60": 0.0, "61-90": 0.0, "over 90": 0.0, "ikke forfalt": 0.0}
    for p in poster:
        forfall = _dato(p.get("termOfPayment")) or _dato(p.get("date"))
        belop = float(p.get("amount") or 0)
        if forfall is None or forfall >= til:
            bøtter["ikke forfalt"] += belop
            continue
        dager = (til - forfall).days
        if dager <= 30:
            bøtter["0-30"] += belop
        elif dager <= 60:
            bøtter["31-60"] += belop
        elif dager <= 90:
            bøtter["61-90"] += belop
        else:
            bøtter["over 90"] += belop
    return bøtter


def r4_alder_kundefordringer(k: Kontekst) -> list[Funn]:
    funn = []
    for rad in _apne_per_type(k, "CUSTOMER"):
        poster = rad.get("postings") or []
        if not poster:
            continue
        bøtter = _alder(poster, k.periode.til)
        oversikt = "  ".join(f"{navn}: {belop:,.0f}".replace(",", " ") for navn, belop in bøtter.items())
        funn.append(
            Funn(
                kontroll="R4",
                omraade=OMRAADE,
                tittel="Aldersfordeling kundefordringer",
                alvorlighet=INFO,
                belop=sum(bøtter.values()),
                konto=str((rad.get("account") or {}).get("number") or ""),
                detalj=oversikt,
                referanse="aldersfordeling",
            )
        )
        gamle = [
            p
            for p in poster
            if (_dato(p.get("termOfPayment")) or _dato(p.get("date")))
            and (k.periode.til - (_dato(p.get("termOfPayment")) or _dato(p.get("date")))).days > 90
            and float(p.get("amount") or 0) > 0
        ]
        if gamle:
            sum_gamle = sum(float(p.get("amount") or 0) for p in gamle)
            detalj = "; ".join(
                f"{navn_av(p.get('customer'))} {float(p.get('amount') or 0):,.0f} "
                f"(faktura {p.get('invoiceNumber') or '-'}, forfall "
                f"{(_dato(p.get('termOfPayment')) or _dato(p.get('date'))).strftime('%d.%m.%y')})".replace(",", " ")
                for p in sorted(gamle, key=lambda x: -float(x.get("amount") or 0))[:10]
            )
            funn.append(
                Funn(
                    kontroll="R4",
                    omraade=OMRAADE,
                    tittel=f"{len(gamle)} kundefordringer forfalt over 90 dager",
                    alvorlighet=ROD if sum_gamle > k.profil.grense() else GUL,
                    belop=sum_gamle,
                    detalj=detalj + "  → vurder purring, inkasso eller tapsavsetning",
                    referanse="forfalt over 90",
                )
            )
    return funn


def r5_forfalte_leverandorfakturaer(k: Kontekst) -> list[Funn]:
    funn = []
    for rad in _apne_per_type(k, "SUPPLIER"):
        forfalte = []
        for p in rad.get("postings") or []:
            forfall = _dato(p.get("termOfPayment"))
            if forfall and forfall < k.periode.til and float(p.get("amount") or 0) < 0:
                forfalte.append((forfall, p))
        if not forfalte:
            continue
        sum_belop = sum(float(p.get("amount") or 0) for _, p in forfalte)
        detalj = "; ".join(
            f"{navn_av(p.get('supplier'))} {abs(float(p.get('amount') or 0)):,.0f} "
            f"(forfalt {d.strftime('%d.%m.%y')})".replace(",", " ")
            for d, p in sorted(forfalte)[:10]
        )
        if len(forfalte) > 10:
            detalj += f" … (+{len(forfalte) - 10} til)"
        funn.append(
            Funn(
                kontroll="R5",
                omraade=OMRAADE,
                tittel=f"{len(forfalte)} leverandørfakturaer er forfalt og ubetalt",
                alvorlighet=GUL,
                belop=sum_belop,
                konto=str((rad.get("account") or {}).get("number") or ""),
                detalj=detalj,
                referanse="forfalt leverandør",
            )
        )
    return funn


def r6_dublettfakturaer(k: Kontekst) -> list[Funn]:
    fakturaer = k.leverandorfakturaer()
    grupper: dict[tuple, list[dict]] = defaultdict(list)
    for f in fakturaer:
        if f.get("isCreditNote"):
            continue
        lev = (f.get("supplier") or {}).get("id")
        belop = round(float(f.get("amount") or 0), 2)
        nummer = (f.get("invoiceNumber") or "").strip()
        if lev is None or belop == 0:
            continue
        grupper[(lev, belop, nummer)].append(f)
    funn = []
    for (lev, belop, nummer), gruppe in grupper.items():
        if len(gruppe) < 2:
            continue
        levnavn = navn_av(gruppe[0].get("supplier"))
        datoer = ", ".join(sorted({str(g.get("invoiceDate") or "")[:10] for g in gruppe}))
        bilag = ", ".join(str((g.get("voucher") or {}).get("number") or "-") for g in gruppe)
        funn.append(
            Funn(
                kontroll="R6",
                omraade=OMRAADE,
                tittel=f"Mulig dobbeltføring: {levnavn} {belop:,.0f}".replace(",", " "),
                alvorlighet=ROD if abs(belop) > k.profil.grense() else GUL,
                belop=belop * (len(gruppe) - 1),
                detalj=(
                    f"{len(gruppe)} fakturaer med samme leverandør, beløp og fakturanummer "
                    f"{nummer or '(tomt)'}. Datoer: {datoer}. Bilag: {bilag}."
                ),
                referanse=f"dublett {lev} {nummer} {belop}",
            )
        )
    # samme leverandør og beløp innen fem dager, uten likt fakturanummer
    etter_lev: dict[tuple, list[dict]] = defaultdict(list)
    for f in fakturaer:
        if f.get("isCreditNote"):
            continue
        lev = (f.get("supplier") or {}).get("id")
        belop = round(float(f.get("amount") or 0), 2)
        if lev is not None and belop:
            etter_lev[(lev, belop)].append(f)
    for (lev, belop), gruppe in etter_lev.items():
        if len(gruppe) < 2:
            continue
        numre = {(g.get("invoiceNumber") or "").strip() for g in gruppe}
        if len(numre) < 2:
            continue  # allerede fanget over
        gruppe = sorted(gruppe, key=lambda g: str(g.get("invoiceDate") or ""))
        for a, b in zip(gruppe, gruppe[1:]):
            da, db = _dato(a.get("invoiceDate")), _dato(b.get("invoiceDate"))
            if da and db and 0 <= (db - da).days <= 5:
                funn.append(
                    Funn(
                        kontroll="R6",
                        omraade=OMRAADE,
                        tittel=(
                            f"Samme beløp to ganger på kort tid: "
                            f"{navn_av(a.get('supplier'))} {belop:,.0f}"
                        ).replace(",", " "),
                        alvorlighet=GUL,
                        belop=belop,
                        detalj=(
                            f"Faktura {a.get('invoiceNumber')} {da.strftime('%d.%m.%y')} og "
                            f"{b.get('invoiceNumber')} {db.strftime('%d.%m.%y')} har samme beløp. "
                            "Ulike fakturanumre – kan være reell gjentakelse."
                        ),
                        referanse=f"nærdublett {lev} {belop} {da}",
                    )
                )
    return funn


KONTROLLER = [
    Kontroll("R1", "Kundereskontro mot hovedbok", OMRAADE, r1_kundereskontro),
    Kontroll("R2", "Leverandørreskontro mot hovedbok", OMRAADE, r2_leverandorreskontro),
    Kontroll("R3", "Feil fortegn i reskontro", OMRAADE, r3_feil_fortegn),
    Kontroll("R4", "Aldersfordeling kundefordringer", OMRAADE, r4_alder_kundefordringer),
    Kontroll("R5", "Forfalte leverandørfakturaer", OMRAADE, r5_forfalte_leverandorfakturaer),
    Kontroll("R6", "Dublettfakturaer", OMRAADE, r6_dublettfakturaer),
]
