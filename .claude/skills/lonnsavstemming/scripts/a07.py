"""Parser for A07 «Avstemmingsinformasjon a-melding» (XML fra Altinn).

Leser innsendinger, arbeidsgiveravgiftsgrunnlag, inntektsmottakere med ytelser
per opptjeningsperiode, forskuddstrekk og betalingsinformasjon.

Gjeldende innsending: en melding er ERSTATTET hvis en annen melding oppgir den i
`erstatterMeldingsId`. Alt annet er gjeldende og SUMMERES – også meldinger med
status MAA_KONTROLLERES. (Verifisert mot ferdige avstemminger; statusfeltet alene
avgjør ikke.)
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from collections import defaultdict
from dataclasses import dataclass, field

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


def _t(e) -> str:
    return e.tag.split("}")[-1]


def _tekst(rot, sti: str, standard=None):
    e = rot.find(sti)
    return e.text.strip() if e is not None and e.text else standard


def _tall(rot, sti: str, standard: float = 0.0) -> float:
    v = _tekst(rot, sti)
    try:
        return float(v)
    except (TypeError, ValueError):
        return standard


@dataclass
class Innsending:
    maaned: str
    meldings_id: str
    status: str
    levert: str
    antall: int
    aga: float
    trekk: float
    erstatter: str | None = None
    erstattet_av: str | None = None
    trekk_per_dato: list[tuple[str, float]] = field(default_factory=list)
    kid_aga: str | None = None
    kid_trekk: str | None = None
    kontonummer: str | None = None

    @property
    def gjeldende(self) -> bool:
        return self.erstattet_av is None

    @property
    def merknad(self) -> str:
        if not self.gjeldende:
            return "erstattet"
        return f"gjeldende; erstatter {self.erstatter}" if self.erstatter else "gjeldende"


@dataclass
class Ytelse:
    maaned: str
    beskrivelse: str
    fordel: str
    aga_pliktig: bool
    trekkpliktig: bool
    beloep: float
    # Ytelser uten opptjeningsperiode plasseres i en måned av fordelingsrutinen.
    # Flagget gjør at de kan fordeles på nytt når pensjonsgrunnlaget er kjent.
    uten_periode: bool = False


@dataclass
class Person:
    fnr: str
    navn: str
    ansattnummer: str | None
    ytelser: list[Ytelse] = field(default_factory=list)
    forskuddstrekk: float = 0.0

    def aga_grunnlag(self, maaned: str | None = None) -> float:
        return sum(
            y.beloep for y in self.ytelser
            if y.aga_pliktig and (maaned is None or y.maaned == maaned)
        )


@dataclass
class A07:
    orgnr: str
    navn: str
    fom: str
    tom: str
    avstemt: str
    innsendinger: list[Innsending]
    personer: list[Person]
    grunnlag_loenn: float
    grunnlag_pensjon: float
    fradrag_sone: float
    aga_sats: float
    sone: str
    sum_aga: float
    trekk_per_dato: list[tuple[str, float]]
    kid_aga: str | None
    kid_trekk: str | None
    kontonummer: str | None

    # -- avledet ----------------------------------------------------------

    @property
    def maaneder(self) -> list[str]:
        return sorted({i.maaned for i in self.innsendinger})

    def gjeldende(self, maaned: str | None = None) -> list[Innsending]:
        return [
            i for i in self.innsendinger
            if i.gjeldende and (maaned is None or i.maaned == maaned)
        ]

    def aga_innrapportert(self, maaned: str | None = None) -> float:
        return sum(i.aga for i in self.gjeldende(maaned))

    def trekk_innrapportert(self, maaned: str | None = None) -> float:
        return sum(i.trekk for i in self.gjeldende(maaned))

    def trekk_per_loennsdato(self) -> dict[str, float]:
        ut: dict[str, float] = defaultdict(float)
        for i in self.gjeldende():
            for dato, beloep in i.trekk_per_dato:
                ut[dato] += beloep
        return dict(sorted(ut.items()))

    def ytelser_per_maaned_konto(self, konto_override: dict[str, int] | None = None):
        """{(maaned, konto): beløp} for alle ytelser."""
        override = konto_override or {}
        ut: dict[tuple[str, int], float] = defaultdict(float)
        for p in self.personer:
            for y in p.ytelser:
                konto = override.get(y.beskrivelse) or YTELSE_KONTO.get(y.beskrivelse, 5260)
                ut[(y.maaned, konto)] += y.beloep
        return dict(ut)

    def ytelser_per_person(self, konto_override: dict[str, int] | None = None):
        """{(navn, maaned, konto): beløp}."""
        override = konto_override or {}
        ut: dict[tuple[str, str, int], float] = defaultdict(float)
        for p in self.personer:
            for y in p.ytelser:
                konto = override.get(y.beskrivelse) or YTELSE_KONTO.get(y.beskrivelse, 5260)
                ut[(p.navn, y.maaned, konto)] += y.beloep
        return dict(ut)

    def grunnlag_per_maaned(self) -> dict[str, float]:
        ut: dict[str, float] = defaultdict(float)
        for p in self.personer:
            for y in p.ytelser:
                if y.aga_pliktig:
                    ut[y.maaned] += y.beloep
        return dict(sorted(ut.items()))

    def utbetalte_feriepenger(self) -> float:
        return sum(
            y.beloep for p in self.personer for y in p.ytelser
            if y.beskrivelse == "feriepenger"
        )


def _maaned_av(inntekt) -> str:
    """Opptjeningsperiodens måned. Mangler perioden (typisk feriepenger til
    sluttede), returneres tom streng og kaller fordeler den selv."""
    start = _tekst(inntekt, "{*}startdatoOpptjeningsperiode")
    if start:
        return start[:7]
    slutt = _tekst(inntekt, "{*}sluttdatoOpptjeningsperiode")
    return slutt[:7] if slutt else ""


def parse_a07(sti: str) -> A07:
    rot = ET.parse(sti).getroot()
    mottatt = rot.find("{*}mottatt")
    if mottatt is None:
        mottatt = rot

    opplysningspliktig = mottatt.find("{*}opplysningspliktig")
    orgnr = _tekst(opplysningspliktig, "{*}norskIdentifikator", "")
    navn = _tekst(opplysningspliktig, "{*}navn", "")

    innsendinger: list[Innsending] = []
    for e in opplysningspliktig.findall("{*}innsendinger"):
        total = e.find("{*}mottattAvgiftOgTrekkTotalt")
        betaling = e.find("{*}innbetalingsinformasjon")
        trekk_dato: list[tuple[str, float]] = []
        trekk_sum = 0.0
        if total is not None:
            for td in total.findall("{*}sumForskuddstrekkPerLoennsutbetalingsdato"):
                dato = _tekst(td, "{*}loennsutbetalingsdato", "")
                beloep = _tall(td, "{*}beloep")
                trekk_dato.append((dato, beloep))
                trekk_sum += beloep
        innsendinger.append(
            Innsending(
                maaned=_tekst(e, "{*}kalendermaaned", ""),
                meldings_id=_tekst(e, "{*}meldingsId", ""),
                status=_tekst(e, "{*}status", ""),
                levert=(_tekst(e, "{*}leveringstidspunkt", "") or "").replace("T", " ")[:16],
                antall=int(_tall(e, "{*}antallInntektsmottakere")),
                aga=_tall(total, "{*}sumArbeidsgiveravgift") if total is not None else 0.0,
                trekk=trekk_sum,
                erstatter=_tekst(e, "{*}erstatterMeldingsId"),
                trekk_per_dato=trekk_dato,
                kid_aga=_tekst(betaling, "{*}kidForArbeidsgiveravgift") if betaling is not None else None,
                kid_trekk=_tekst(betaling, "{*}kidForForskuddstrekk") if betaling is not None else None,
                kontonummer=_tekst(betaling, "{*}kontonummer") if betaling is not None else None,
            )
        )

    # marker erstattede
    etter_id = {i.meldings_id: i for i in innsendinger}
    for i in innsendinger:
        if i.erstatter and i.erstatter in etter_id:
            etter_id[i.erstatter].erstattet_av = i.meldings_id

    oppgave = mottatt.find("{*}oppgave")
    personer: list[Person] = []
    grunnlag_loenn = grunnlag_pensjon = fradrag = 0.0
    aga_sats = 14.1
    sone = ""
    for virksomhet in oppgave.findall("{*}virksomhet"):
        aga = virksomhet.find("{*}arbeidsgiveravgift")
        if aga is not None:
            for node, felt in (
                ("{*}loennOgGodtgjoerelse", "loenn"),
                ("{*}tilskuddOgPremieTilPensjon", "pensjon"),
                ("{*}fradragIGrunnlagetForSone", "fradrag"),
            ):
                for e in aga.findall(node):
                    if felt == "fradrag":
                        fradrag += _tall(e, "{*}avgiftsfradragBeloep")
                    elif felt == "loenn":
                        grunnlag_loenn += _tall(e, "{*}avgiftsgrunnlagBeloep")
                        aga_sats = _tall(e, "{*}prosentsatsForAvgiftsberegning", aga_sats)
                        sone = _tekst(e, "{*}sone", sone) or sone
                    else:
                        grunnlag_pensjon += _tall(e, "{*}avgiftsgrunnlagBeloep")

        for im in virksomhet.findall("{*}inntektsmottaker"):
            ident = im.find("{*}identifiserendeInformasjon")
            person = Person(
                fnr=_tekst(im, "{*}norskIdentifikator", ""),
                navn=_tekst(ident, "{*}navn", "") if ident is not None else "",
                ansattnummer=_tekst(ident, "{*}ansattnummer") if ident is not None else None,
            )
            for inntekt in im.findall("{*}inntekt"):
                loenn = inntekt.find("{*}loennsinntekt")
                person.ytelser.append(
                    Ytelse(
                        maaned=_maaned_av(inntekt),
                        beskrivelse=(_tekst(loenn, "{*}beskrivelse", "annet") if loenn is not None else "annet"),
                        fordel=_tekst(inntekt, "{*}fordel", ""),
                        aga_pliktig=(_tekst(inntekt, "{*}utloeserArbeidsgiveravgift", "false") == "true"),
                        trekkpliktig=(_tekst(inntekt, "{*}inngaarIGrunnlagForTrekk", "false") == "true"),
                        beloep=_tall(inntekt, "{*}beloep"),
                        uten_periode=not _tekst(inntekt, "{*}startdatoOpptjeningsperiode"),
                    )
                )
            for ft in im.findall("{*}forskuddstrekk"):
                person.forskuddstrekk += _tall(ft, "{*}beloep")
            personer.append(person)

    betaling = oppgave.find("{*}betalingsinformasjon")
    trekk_per_dato: list[tuple[str, float]] = []
    if betaling is not None:
        for td in betaling.findall("{*}sumForskuddstrekkPerLoennsutbetalingsdato"):
            trekk_per_dato.append(
                (_tekst(td, "{*}loennsutbetalingsdato", ""), _tall(td, "{*}beloep"))
            )

    gjeldende = [i for i in innsendinger if i.gjeldende]
    kid_aga = next((i.kid_aga for i in gjeldende if i.kid_aga), None)
    kid_trekk = next((i.kid_trekk for i in gjeldende if i.kid_trekk), None)
    kontonummer = next((i.kontonummer for i in gjeldende if i.kontonummer), None)

    a07 = A07(
        orgnr=orgnr,
        navn=navn,
        fom=_tekst(mottatt, "{*}fomKalendermaaned", ""),
        tom=_tekst(mottatt, "{*}tomKalendermaaned", ""),
        avstemt=(_tekst(mottatt, "{*}avstemmingstidspunkt", "") or "")[:10],
        innsendinger=innsendinger,
        personer=personer,
        grunnlag_loenn=grunnlag_loenn,
        grunnlag_pensjon=grunnlag_pensjon,
        fradrag_sone=fradrag,
        aga_sats=aga_sats,
        sone=sone,
        sum_aga=_tall(betaling, "{*}sumArbeidsgiveravgift") if betaling is not None else 0.0,
        trekk_per_dato=trekk_per_dato,
        kid_aga=kid_aga,
        kid_trekk=kid_trekk,
        kontonummer=kontonummer,
    )
    _fordel_ytelser_uten_periode(a07)
    return a07


def _fordel_ytelser_uten_periode(a07: A07, pensjon_per_maaned=None) -> None:
    """Ytelser uten opptjeningsperiode (typisk feriepenger til sluttede) legges i
    den måneden der grunnlaget mangler omtrent dette beløpet.

    Vi regner ut hvor mye grunnlag måneden mangler for å forklare innrapportert
    AGA – innrapportert / sats − (ytelser + pensjon) – og velger måneden der
    avviket fra ytelsen er minst. Pensjonsgrunnlaget må være med; uten det
    havner beløpet lett i feil måned."""
    uten = [(p, y) for p in a07.personer for y in p.ytelser if not y.maaned]
    if not uten:
        return
    maaneder = a07.maaneder or [a07.fom]
    pensjon = pensjon_per_maaned or {}
    sats = a07.aga_sats / 100 or 0.141
    for _, y in uten:
        grunnlag_naa = a07.grunnlag_per_maaned()
        beste, beste_avvik = maaneder[0], None
        for m in maaneder:
            mangler = (a07.aga_innrapportert(m) / sats
                       - grunnlag_naa.get(m, 0.0) - pensjon.get(m, 0.0))
            avvik = abs(mangler - (y.beloep if y.aga_pliktig else 0.0))
            if beste_avvik is None or avvik < beste_avvik:
                beste, beste_avvik = m, avvik
        y.maaned = beste


def fordel_paa_nytt(a07: A07, pensjon_per_maaned) -> None:
    """Kjøres på nytt når pensjonsgrunnlaget per måned er kjent fra regnskapet."""
    for p in a07.personer:
        for y in p.ytelser:
            if getattr(y, "uten_periode", False):
                y.maaned = ""
    _fordel_ytelser_uten_periode(a07, pensjon_per_maaned)
