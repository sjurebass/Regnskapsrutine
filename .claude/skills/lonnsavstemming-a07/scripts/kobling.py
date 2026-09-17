"""Kobler A07-beløp per person mot linjene i lønnsbilaget.

Tripletex fører ikke ansatt på posteringslinjene – teksten er bare
«Lønnsbilag N-ÅÅÅÅ». Koblingen må derfor gjøres ved beløpsmatching: for hver
måned og konto har vi ett mål per person fra A07, og en liste med linjer fra
regnskapet. Vi fordeler linjene på personene slik at hver persons sum treffer
målet innenfor toleransen.

Én person kan ha flere linjer på samme konto – fastlønn pluss etterbetaling, og
i negative lønnskjøringer en positiv og en negativ linje som netter seg. Derfor
må fortegnet på linjene beholdes; det er ikke en ren delsum-oppgave.
"""

from __future__ import annotations

from collections import defaultdict

MAKS_NODER = 300_000


def fordel(maal: dict[str, float], linjer: list[float], toleranse: float = 0.02):
    """Fordeler linjer på personer. Returnerer {navn: sum} eller None.

    Målene er som regel enten alle positive (kostnadskonti) eller alle negative
    (2600/2770). Vi snur hele bildet når de er negative, slik at søket alltid
    jobber med positive mål – men beholder fortegnet på hver enkelt linje."""
    if not maal:
        return {}
    if not linjer:
        return None

    negativ = sum(maal.values()) < 0
    tegn = -1.0 if negativ else 1.0
    mål = {n: maal[n] * tegn for n in maal}
    verdier = sorted((v * tegn for v in linjer), key=lambda x: (-abs(x), x))

    if abs(sum(verdier) - sum(mål.values())) > toleranse * (len(mål) + 1):
        return None

    navn = sorted(mål, key=lambda n: -abs(mål[n]))
    tildelt: dict[str, list[float]] = {n: [] for n in navn}
    sum_na: dict[str, float] = {n: 0.0 for n in navn}
    # Hvor mye positivt, og hvor mye negativt, som gjenstår fra og med indeks i.
    # Det positive brukes til å se om målene i det hele tatt kan nås; det
    # negative til å la en person få en for stor linje som en senere negativ
    # linje trekker ned igjen (negative lønnskjøringer).
    rest_positiv = [0.0] * (len(verdier) + 1)
    rest_negativ = [0.0] * (len(verdier) + 1)
    for i in range(len(verdier) - 1, -1, -1):
        rest_positiv[i] = rest_positiv[i + 1] + max(0.0, verdier[i])
        rest_negativ[i] = rest_negativ[i + 1] + min(0.0, verdier[i])
    noder = 0

    def mangler() -> float:
        return sum(max(0.0, mål[n] - sum_na[n]) for n in navn)

    def rek(i: int) -> bool:
        nonlocal noder
        noder += 1
        if noder > MAKS_NODER:
            return False
        if i == len(verdier):
            return all(abs(sum_na[n] - mål[n]) <= toleranse for n in navn)
        if rest_positiv[i] + toleranse < mangler():
            return False
        v = verdier[i]
        # To personer er utskiftbare bare når BÅDE delsummen og målet er likt.
        # Dedupliserer man på delsummen alene, mister man løsninger der flere
        # står på null med ulike mål.
        prøvd: set[tuple[float, float]] = set()
        for n in navn:
            nokkel = (sum_na[n], mål[n])
            if nokkel in prøvd:
                continue
            prøvd.add(nokkel)
            # En positiv linje kan ta personen over målet bare hvis det finnes
            # nok negativt igjen til å trekke henne ned. En negativ linje kan
            # alltid legges til.
            if v > 0 and sum_na[n] + v + rest_negativ[i + 1] > mål[n] + toleranse:
                continue
            sum_na[n] += v
            tildelt[n].append(v)
            if rek(i + 1):
                return True
            sum_na[n] -= v
            tildelt[n].pop()
        return False

    if not rek(0):
        return None
    return {n: sum(tildelt[n]) * tegn for n in navn}


class Personkobling:
    """Cacher fordelingen per (måned, konto)."""

    def __init__(self, ledger, er_lonnsbilag):
        self.ledger = ledger
        self.er_lonnsbilag = er_lonnsbilag
        self._cache: dict[tuple[str, int], dict | None] = {}

    def _linjer(self, maaned: str, konto: int, fortegn: float = 0.0) -> list[float]:
        ut = [
            p["beloep"] for p in self.ledger.aktive
            if p["konto"] == konto and p["dato"][:7] == maaned and self.er_lonnsbilag(p)
        ]
        # 2940 blander avsetning (kredit) og utbetaling (debet). Er målet en
        # utbetaling, er avsetningslinjene irrelevante – og motsatt.
        if konto == 2940 and fortegn:
            ut = [v for v in ut if v * fortegn > 0]
        return ut

    def fordeling(self, maaned: str, konto: int, maal: dict[str, float]):
        nokkel = (maaned, konto)
        if nokkel not in self._cache:
            sum_maal = sum(maal.values())
            fortegn = 1.0 if sum_maal > 0 else (-1.0 if sum_maal < 0 else 0.0)
            self._cache[nokkel] = fordel(maal, self._linjer(maaned, konto, fortegn))
        return self._cache[nokkel]

    def bokfort(self, navn: str, maaned: str, konto: int, maal: dict[str, float]):
        f = self.fordeling(maaned, konto, maal)
        if f is None:
            return None
        return f.get(navn)


def maal_per_person(ytelser_per_person: dict, maaned: str, konto: int) -> dict[str, float]:
    ut: dict[str, float] = defaultdict(float)
    for (navn, m, k), beloep in ytelser_per_person.items():
        if m == maaned and k == konto:
            ut[navn] += beloep
    return dict(ut)
