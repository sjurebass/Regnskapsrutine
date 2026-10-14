"""Leser A07 «Avstemmingsinformasjon a-melding» fra Tally (JSON).

Tally henter rapporten fra Skatteetaten via Maskinporten/Altinn. Svaret fra
`hent_amelding_rapport(client_id, start_month, end_month)` lagres som a07.json.
Formen står i references/kontrollogikk.md, og et utfylt eksempel ligger i
scripts/a07_tally_eksempel.json.

Rapporten har ingen personopplysninger: summer per måned og for perioden,
ytelser per type for hele perioden, avgiftsgrunnlag og innsendinger med KID.
Erstattede a-meldinger er allerede holdt utenfor månedssummene.

null i kilden betyr at beløpet ikke er oppgitt, ikke null kroner. Slike verdier
blir None her og vises som «ikke oppgitt» i rapporten, aldri som 0.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

IKKE_OPPGITT = "ikke oppgitt"

# Ytelsesbeskrivelse i A07 -> standard konto i norsk kontoplan.
YTELSE_KONTO = {
    "fastloenn": 5000,
    "timeloenn": 5000,
    "overtidsgodtgjoerelse": 5000,
    "uregelmessigeTilleggKnyttetTilArbeidetTid": 5000,
    "uregelmessigeTilleggKnyttetTilIkkeArbeidetTid": 5000,
    "fastTillegg": 5000,
    "helligdagstillegg": 5000,
    "smusstillegg": 5000,
    "bonus": 5001,
    "sluttvederlag": 5001,
    "styrehonorar": 5011,
    "sykepenger": 5030,
    "feriepenger": 2940,
    "bil": 5200,
    "elektroniskKommunikasjon": 5210,
    "rentefordelVedRimeligLaanIArbeidsforhold": 5230,
    "annet": 5260,
    "yrkesbilTjenestligbehovListepris": 5200,
    "yrkesbilTjenestligbehovKilometer": 5200,
    "reiseKost": 5510,
    "reiseKostMedOvernattingPaaHotell": 5510,
    "kostDager": 5510,
    "losji": 5510,
    "trekkpliktigBilgodtgjoerelse": 5510,
    # utenfor avgiftsgrunnlaget
    "kilometergodtgjoerelseBil": 7100,
    "passasjertillegg": 7100,
    "reiseKostMedOvernatting": 7150,
    "reiseKostUtenOvernatting": 7150,
}
STANDARD_KONTO = 5260


# Godtgjørelser som er avgiftsfrie opp til statens sats. Den delen som utløser AGA (over satsen), rapporteres som en egen
# linje med utloeserArbeidsgiveravgift = true og føres som trekkpliktig godtgjørelse på 5510 (kalibrert oktober 2026).
TREKKPLIKTIG_DEL = {"kilometergodtgjoerelseBil", "passasjertillegg", "reiseKostMedOvernatting", "reiseKostUtenOvernatting"}
TREKKPLIKTIG_KONTO = 5510


def konto_for(beskrivelse: str, override: dict | None = None, aga_pliktig: bool | None = None) -> int:
    """Konto for en ytelse: `ytelse_konto` i ledger.json først (nøkkel «<beskrivelse>» eller «<beskrivelse>:aga» for den
    AGA-pliktige delen), så standardmappingen."""
    override = override or {}
    if aga_pliktig and beskrivelse in TREKKPLIKTIG_DEL:
        return int(override.get(f"{beskrivelse}:aga") or TREKKPLIKTIG_KONTO)
    return int(override.get(beskrivelse) or YTELSE_KONTO.get(beskrivelse, STANDARD_KONTO))


def _tall(v) -> float | None:
    """Tall eller None. null og tomt blir None, aldri 0."""
    if v is None or v == "":
        return None
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def summer(verdier) -> float | None:
    """Summen, eller None hvis én av verdiene ikke er oppgitt."""
    ut = 0.0
    for v in verdier:
        if v is None:
            return None
        ut += v
    return ut


def _tekst(v) -> str:
    return "" if v is None else str(v).strip()


@dataclass
class Innsending:
    maaned: str
    status: str
    kildesystem: str
    levert: str
    antall_mottakere: int | None
    erstattet: bool
    trekk: float | None
    aga: float | None
    finansskatt: float | None
    forfall: str | None
    kontonummer: str | None
    kid_trekk: str | None
    kid_aga: str | None
    kid_finansskatt: str | None

    @property
    def gjeldende(self) -> bool:
        return not self.erstattet

    @property
    def merknad(self) -> str:
        return "erstattet" if self.erstattet else "gjeldende"


@dataclass
class Maaned:
    maaned: str
    antall_innsendinger: int | None
    trekk: float | None
    aga: float | None
    finansskatt: float | None


@dataclass
class Ytelse:
    """Én ytelsestype for hele perioden (ikke per måned, ikke per person)."""
    beskrivelse: str
    fordel: str
    aga_pliktig: bool | None
    beloep: float | None


@dataclass
class Avgiftsgrunnlag:
    virksomhet: str
    type: str
    sone: str
    beregningskode: str
    grunnlag: float | None
    sats: float | None  # brøk, 0.141

    @property
    def art(self) -> str:
        """loenn, pensjon, fradrag eller ukjent. Typer med «fradrag» er fradrag i grunnlaget."""
        t = (self.type or "").lower()
        if "fradrag" in t:
            return "fradrag"
        if "pensjon" in t:
            return "pensjon"
        if "loenn" in t or "lønn" in t:
            return "loenn"
        return "ukjent"


@dataclass
class A07:
    orgnr: str                      # første virksomhet i avgiftsgrunnlaget (fallback i overskriften)
    virksomheter: list[str]
    navn: str                       # klient
    fom: str                        # ÅÅÅÅ-MM
    tom: str
    avstemt: str                    # ÅÅÅÅ-MM-DD
    innsendinger: list[Innsending]
    per_maaned: dict[str, Maaned] | None
    ytelser: list[Ytelse] | None
    avgiftsgrunnlag: list[Avgiftsgrunnlag] | None
    trekk_totalt: float | None
    aga_totalt: float | None
    finansskatt_totalt: float | None
    grunnlag_loenn: float | None
    grunnlag_pensjon: float | None
    grunnlag_fradrag: float | None  # negativt: reduserer grunnlaget
    sone: str
    sats: float | None              # brøk, 0.141
    kid_aga: str | None
    kid_trekk: str | None
    kid_finansskatt: str | None
    kontonummer: str | None         # Skatteetatens innbetalingskonto
    forfall: str | None             # forfallsdato fra innsendingene, ofte null
    merknad: str = ""
    ukjente_grunnlag: list[Avgiftsgrunnlag] = field(default_factory=list)

    # -- per måned og totalt ----------------------------------------------

    @property
    def maaneder(self) -> list[str]:
        if self.per_maaned:
            return sorted(self.per_maaned)
        return sorted({i.maaned for i in self.innsendinger if i.maaned})

    def gjeldende(self, maaned: str | None = None) -> list[Innsending]:
        return [i for i in self.innsendinger
                if i.gjeldende and (maaned is None or i.maaned == maaned)]

    def _maanedsverdi(self, felt: str, maaned: str) -> float | None:
        if self.per_maaned is None:
            return None
        m = self.per_maaned.get(maaned)
        if m is None:
            return 0.0          # ingen a-melding for måneden
        return getattr(m, felt)

    def _total(self, totalt: float | None, felt: str) -> float | None:
        if totalt is not None:
            return totalt
        if not self.per_maaned:
            return None
        return summer(getattr(m, felt) for m in self.per_maaned.values())

    def trekk_innrapportert(self, maaned: str | None = None) -> float | None:
        if maaned:
            return self._maanedsverdi("trekk", maaned)
        return self._total(self.trekk_totalt, "trekk")

    def aga_innrapportert(self, maaned: str | None = None) -> float | None:
        if maaned:
            return self._maanedsverdi("aga", maaned)
        return self._total(self.aga_totalt, "aga")

    def finansskatt_innrapportert(self, maaned: str | None = None) -> float | None:
        if maaned:
            return self._maanedsverdi("finansskatt", maaned)
        return self._total(self.finansskatt_totalt, "finansskatt")

    def aga_innsendinger(self) -> float | None:
        """Σ AGA i gjeldende innsendinger (kontroll mot totalen)."""
        return summer(i.aga for i in self.gjeldende())

    def har_maaned(self, maaned: str) -> bool:
        return bool(self.per_maaned) and maaned in self.per_maaned

    def kid_for(self, maaned: str, art: str) -> str | None:
        """KID fra siste gjeldende innsending i måneden. art: trekk, aga eller finansskatt."""
        for i in sorted(self.gjeldende(maaned), key=lambda x: x.levert, reverse=True):
            v = getattr(i, f"kid_{art}")
            if v:
                return v
        return None

    # -- avgiftsgrunnlag --------------------------------------------------

    def beregnet_aga(self, standard_sats: float) -> float | None:
        """Σ grunnlag × sats per rad (lønn + pensjon − fradrag). Ukjente typer holdes utenfor."""
        if self.avgiftsgrunnlag is None:
            return None
        ut = 0.0
        for g in self.avgiftsgrunnlag:
            if g.art == "ukjent":
                continue
            if g.grunnlag is None:
                return None
            sats = g.sats if g.sats is not None else standard_sats
            if g.art == "fradrag":
                ut -= abs(g.grunnlag) * sats
            else:
                ut += g.grunnlag * sats
        return ut

    # -- ytelser for perioden ---------------------------------------------

    def ytelser_per_konto(self, override: dict | None = None) -> dict[int, list[Ytelse]]:
        ut: dict[int, list[Ytelse]] = {}
        for y in self.ytelser or []:
            ut.setdefault(konto_for(y.beskrivelse, override, y.aga_pliktig), []).append(y)
        return dict(sorted(ut.items()))

    def utbetalte_feriepenger(self) -> float | None:
        """Ytelser med «feriepenger» i beskrivelsen."""
        if self.ytelser is None:
            return None
        return summer(y.beloep for y in self.ytelser if "feriepenger" in y.beskrivelse.lower())

    def sum_aga_pliktige_ytelser(self) -> float | None:
        if self.ytelser is None:
            return None
        if any(y.aga_pliktig is None for y in self.ytelser):
            return None
        return summer(y.beloep for y in self.ytelser if y.aga_pliktig)


def _grunnlag(rader: list[Avgiftsgrunnlag] | None, art: str) -> float | None:
    if rader is None:
        return None
    verdi = summer(g.grunnlag for g in rader if g.art == art)
    if verdi is None:
        return None
    return -abs(verdi) if art == "fradrag" else verdi


def _les_innsending(e: dict) -> Innsending:
    kid = e.get("kid") or {}
    antall = e.get("antallInntektsmottakere")
    return Innsending(
        maaned=_tekst(e.get("kalendermaaned")),
        status=_tekst(e.get("status")),
        kildesystem=_tekst(e.get("kildesystem")),
        levert=_tekst(e.get("leveringstidspunkt")).replace("T", " ")[:16],
        antall_mottakere=int(antall) if antall is not None else None,
        erstattet=bool(e.get("erstattet")),
        trekk=_tall(e.get("forskuddstrekk")),
        aga=_tall(e.get("arbeidsgiveravgift")),
        finansskatt=_tall(e.get("finansskattLoenn")),
        forfall=_tekst(e.get("forfallsdato"))[:10] or None,
        kontonummer=_tekst(e.get("kontonummer")) or None,
        kid_trekk=_tekst(kid.get("forskuddstrekk")) or None,
        kid_aga=_tekst(kid.get("arbeidsgiveravgift")) or None,
        kid_finansskatt=_tekst(kid.get("finansskattLoenn")) or None,
    )


def _siste(innsendinger: list[Innsending], felt: str) -> str | None:
    """Verdien fra siste gjeldende innsending som har feltet (siste måned, sist levert)."""
    for i in sorted(innsendinger, key=lambda x: (x.maaned, x.levert), reverse=True):
        if i.gjeldende and getattr(i, felt):
            return getattr(i, felt)
    return None


def les_a07(sti: str) -> A07:
    with open(sti, encoding="utf-8-sig") as f:
        tekst = f.read()
    if tekst.lstrip().startswith("<"):
        raise SystemExit("A07 må være JSON fra Tally (hent_amelding_rapport). XML brukes ikke lenger.")
    d = json.loads(tekst)
    # Et svar pakket i ett ytre felt pakkes ut.
    if isinstance(d, dict) and len(d) == 1 and isinstance(next(iter(d.values())), dict):
        d = next(iter(d.values()))
    if not isinstance(d, dict) or not any(k in d for k in ("totalt", "per_maaned", "innsendinger")):
        raise SystemExit("Fant ingen A07 i fila. Er rapporten bestilt? Se steg 1 i SKILL.md "
                         "(request_amelding_report, så hent_amelding_rapport).")

    innsendinger = [_les_innsending(e) for e in d.get("innsendinger") or []]

    per_maaned = None
    if d.get("per_maaned") is not None:
        per_maaned = {}
        for m in d["per_maaned"]:
            mnd = _tekst(m.get("kalendermaaned"))
            antall = m.get("antallInnsendinger")
            per_maaned[mnd] = Maaned(
                maaned=mnd,
                antall_innsendinger=int(antall) if antall is not None else None,
                trekk=_tall(m.get("forskuddstrekk")),
                aga=_tall(m.get("arbeidsgiveravgift")),
                finansskatt=_tall(m.get("finansskattLoenn")),
            )

    ytelser = None
    if d.get("loenn_og_ytelser") is not None:
        ytelser = []
        for y in d["loenn_og_ytelser"]:
            aga = y.get("utloeserArbeidsgiveravgift")
            ytelser.append(Ytelse(
                beskrivelse=_tekst(y.get("beskrivelse")) or "annet",
                fordel=_tekst(y.get("fordel")),
                aga_pliktig=None if aga is None else bool(aga),
                beloep=_tall(y.get("beloep")),
            ))

    grunnlag = None
    if d.get("avgiftsgrunnlag") is not None:
        grunnlag = []
        for g in d["avgiftsgrunnlag"]:
            sats = _tall(g.get("sats"))
            grunnlag.append(Avgiftsgrunnlag(
                virksomhet=_tekst(g.get("virksomhet")),
                type=_tekst(g.get("type")),
                sone=_tekst(g.get("sone")),
                beregningskode=_tekst(g.get("beregningskode")),
                grunnlag=_tall(g.get("grunnlag")),
                sats=None if sats is None else round(sats / 100, 6),
            ))

    # Sats og sone: lønnsraden med størst grunnlag.
    loenn = sorted((g for g in grunnlag or [] if g.art == "loenn"),
                   key=lambda g: -(g.grunnlag or 0.0))
    hoved = loenn[0] if loenn else (grunnlag[0] if grunnlag else None)

    totalt = d.get("totalt") or {}
    maaneder = re.findall(r"\d{4}-\d{2}", _tekst(d.get("periode")))
    alle_mnd = sorted(per_maaned or {}) or sorted({i.maaned for i in innsendinger if i.maaned})
    fom = maaneder[0] if maaneder else (alle_mnd[0] if alle_mnd else "")
    tom = maaneder[-1] if maaneder else (alle_mnd[-1] if alle_mnd else fom)
    virksomheter = sorted({g.virksomhet for g in grunnlag or [] if g.virksomhet})
    forfall = sorted(i.forfall for i in innsendinger if i.gjeldende and i.forfall)

    return A07(
        orgnr=virksomheter[0] if virksomheter else "",
        virksomheter=virksomheter,
        navn=_tekst(d.get("klient")),
        fom=fom,
        tom=tom,
        avstemt=_tekst(d.get("avstemt"))[:10],
        innsendinger=innsendinger,
        per_maaned=per_maaned,
        ytelser=ytelser,
        avgiftsgrunnlag=grunnlag,
        trekk_totalt=_tall(totalt.get("forskuddstrekk")),
        aga_totalt=_tall(totalt.get("arbeidsgiveravgift")),
        finansskatt_totalt=_tall(totalt.get("finansskattLoenn")),
        grunnlag_loenn=_grunnlag(grunnlag, "loenn"),
        grunnlag_pensjon=_grunnlag(grunnlag, "pensjon"),
        grunnlag_fradrag=_grunnlag(grunnlag, "fradrag"),
        sone=hoved.sone if hoved else "",
        sats=hoved.sats if hoved else None,
        kid_aga=_siste(innsendinger, "kid_aga"),
        kid_trekk=_siste(innsendinger, "kid_trekk"),
        kid_finansskatt=_siste(innsendinger, "kid_finansskatt"),
        kontonummer=_siste(innsendinger, "kontonummer"),
        forfall=forfall[-1] if forfall else None,
        merknad=_tekst(d.get("merknad")),
        ukjente_grunnlag=[g for g in grunnlag or [] if g.art == "ukjent"],
    )
