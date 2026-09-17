"""P – bransjeavhengige kontroller. Kjøres bare der profilen slår dem på."""

from __future__ import annotations

from collections import defaultdict

from ..hent import Kontekst, navn_av, saldo_map, ub
from ..modeller import GUL, INFO, ROD, Funn, Kontroll

OMRAADE = "Bransje"


def p1_ufakturerte_timer(k: Kontekst) -> list[Funn]:
    per_prosjekt: dict[str, dict] = defaultdict(lambda: {"timer": 0.0, "verdi": 0.0, "navn": ""})
    for t in k.timeregistreringer():
        if t.get("invoice"):
            continue
        fakturerbare = float(t.get("chargeableHours") or 0)
        if fakturerbare <= 0:
            continue
        prosjekt = t.get("project") or {}
        nokkel = str(prosjekt.get("id") or "uten prosjekt")
        rad = per_prosjekt[nokkel]
        rad["timer"] += fakturerbare
        rad["verdi"] += fakturerbare * float(t.get("hourlyRate") or 0)
        rad["navn"] = prosjekt.get("name") or "Uten prosjekt"
    funn = []
    for _, rad in sorted(per_prosjekt.items(), key=lambda x: -x[1]["verdi"]):
        if rad["timer"] < 5:
            continue
        funn.append(
            Funn(
                kontroll="P1",
                omraade=OMRAADE,
                tittel=f"Ufakturerte timer: {rad['navn']}",
                alvorlighet=GUL if rad["verdi"] >= k.profil.grense() else INFO,
                belop=rad["verdi"],
                detalj=(
                    f"{rad['timer']:.1f} fakturerbare timer hittil i år uten faktura "
                    f"(anslått verdi {rad['verdi']:,.0f})."
                ).replace(",", " "),
                referanse=f"ufakturert {rad['navn']}",
            )
        )
    return funn[:12]


def p2_prosjektmargin(k: Kontekst) -> list[Funn]:
    """Inntekt mot kostnad per prosjekt, regnet fra posteringene hittil i år."""
    per_prosjekt: dict[str, dict] = defaultdict(lambda: {"inntekt": 0.0, "kostnad": 0.0, "navn": ""})
    for p in k.posteringer_hittil():
        prosjekt = p.get("project") or {}
        if not prosjekt.get("id"):
            continue
        konto = p.get("account") or {}
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        belop = float(p.get("amount") or 0)
        rad = per_prosjekt[str(prosjekt["id"])]
        rad["navn"] = prosjekt.get("name") or prosjekt.get("number") or "?"
        if 3000 <= nummer <= 3999:
            rad["inntekt"] -= belop  # inntekt er kredit
        elif 4000 <= nummer <= 7999:
            rad["kostnad"] += belop
    funn = []
    for _, rad in per_prosjekt.items():
        dekning = rad["inntekt"] - rad["kostnad"]
        if rad["inntekt"] <= 0 and rad["kostnad"] <= 0:
            continue
        if dekning >= 0 and (rad["inntekt"] == 0 or dekning / max(rad["inntekt"], 1) > 0.1):
            continue
        funn.append(
            Funn(
                kontroll="P2",
                omraade=OMRAADE,
                tittel=f"Svak margin på prosjekt {rad['navn']}",
                alvorlighet=GUL if dekning < 0 else INFO,
                belop=dekning,
                detalj=(
                    f"Inntekt {rad['inntekt']:,.0f}, kostnad {rad['kostnad']:,.0f}, "
                    f"dekningsbidrag {dekning:,.0f} hittil i år."
                ).replace(",", " "),
                referanse=f"margin {rad['navn']}",
            )
        )
    funn.sort(key=lambda f: f.belop or 0)
    return funn[:10]


def p3_varelager(k: Kontekst) -> list[Funn]:
    saldi = saldo_map(k.saldo_hittil())
    bokfort = round(ub(saldi, k.profil.konto("varelager")), 2)
    funn = []
    try:
        tellinger = [t for t in k.varetellinger() if t.get("isCompleted")]
    except Exception as e:
        k.advarsler.append(f"P3 varetelling: {e}")
        tellinger = []
    if not tellinger:
        if abs(bokfort) >= 1:
            funn.append(
                Funn(
                    kontroll="P3",
                    omraade=OMRAADE,
                    tittel="Ingen fullført varetelling registrert",
                    alvorlighet=INFO,
                    belop=bokfort,
                    konto=", ".join(str(n) for n in k.profil.konto("varelager")),
                    detalj=f"Bokført lager {bokfort:,.0f} uten telling å måle mot.".replace(",", " "),
                    referanse="ingen telling",
                )
            )
        return funn
    siste = max(tellinger, key=lambda t: str(t.get("date") or ""))
    lagerverdi = float(siste.get("warehouseValue") or 0)
    differanse = round(bokfort - lagerverdi, 2)
    if abs(differanse) >= max(k.profil.grense(), 1.0):
        funn.append(
            Funn(
                kontroll="P3",
                omraade=OMRAADE,
                tittel="Bokført lager avviker fra siste telling",
                alvorlighet=GUL,
                belop=differanse,
                detalj=(
                    f"Bokført {bokfort:,.0f} mot telling {lagerverdi:,.0f} "
                    f"({str(siste.get('date'))[:10]})."
                ).replace(",", " "),
                referanse="lagerdifferanse",
            )
        )
    return funn


def p4_leieinntekter(k: Kontekst) -> list[Funn]:
    """Leieinntekt måned for måned – hull tyder på manglende fakturering."""
    per_maaned: dict[int, float] = defaultdict(float)
    for p in k.posteringer_hittil():
        konto = p.get("account") or {}
        try:
            nummer = int(konto.get("number"))
        except (TypeError, ValueError):
            continue
        if not 3600 <= nummer <= 3699:
            continue
        dato = str(p.get("date") or "")
        if len(dato) < 7:
            continue
        per_maaned[int(dato[5:7])] -= float(p.get("amount") or 0)
    if not per_maaned:
        return []
    maaneder = [per_maaned.get(m, 0.0) for m in range(1, k.periode.maaned + 1)]
    snitt = sum(maaneder) / len(maaneder)
    if snitt <= 0:
        return []
    denne = per_maaned.get(k.periode.maaned, 0.0)
    if denne >= snitt * 0.8:
        return []
    return [
        Funn(
            kontroll="P4",
            omraade=OMRAADE,
            tittel="Leieinntekten er lavere enn vanlig denne måneden",
            alvorlighet=GUL,
            belop=denne - snitt,
            detalj=(
                f"{denne:,.0f} i {k.periode.navn} mot et snitt på {snitt:,.0f} hittil i år. "
                "Sjekk om all leie er fakturert."
            ).replace(",", " "),
            referanse="leieinntekt",
        )
    ]


KONTROLLER = [
    Kontroll("P1", "Ufakturerte timer", OMRAADE, p1_ufakturerte_timer, ("prosjekt",)),
    Kontroll("P2", "Prosjektmargin", OMRAADE, p2_prosjektmargin, ("prosjekt",)),
    Kontroll("P3", "Varelager mot telling", OMRAADE, p3_varelager, ("varelager",)),
    Kontroll("P4", "Leieinntekter", OMRAADE, p4_leieinntekter, ("utleie",)),
]
