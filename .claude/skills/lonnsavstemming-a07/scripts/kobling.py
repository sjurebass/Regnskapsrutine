"""Kobler A07-beløp per person mot linjene i lønnsbilaget.

Tripletex fører ikke ansatt på posteringslinjene – teksten er bare
«Lønnsbilag N-ÅÅÅÅ». Koblingen må derfor gjøres ved beløpsmatching: for hver
måned og konto har vi ett mål per person fra A07, og en liste med linjer fra
regnskapet. Vi fordeler linjene på personene slik at hver persons sum treffer
målet innenfor toleransen.

Én person kan ha flere linjer på samme konto (f.eks. fastlønn + etterbetaling),
så dette er en fordeling, ikke en én-til-én-match.
"""

from __future__ import annotations

from collections import defaultdict

MAKS_NODER = 200_000


def fordel(maal: dict[str, float], linjer: list[float], toleranse: float = 0.02):
    """Fordeler linjer på personer. Returnerer {navn: sum} eller None.

    Alle beløp normaliseres til positive tall før matching, slik at kredit- og
    debetkonti behandles likt."""
    if not maal:
        return {}
    if not linjer:
        return None

    navn = sorted(maal, key=lambda n: -abs(maal[n]))
    mål = {n: abs(maal[n]) for n in navn}
    verdier = sorted((abs(v) for v in linjer), reverse=True)

    if abs(sum(verdier) - sum(mål.values())) > toleranse * max(len(navn), 1) + toleranse:
        return None

    tildelt: dict[str, list[float]] = {n: [] for n in navn}
    sum_na: dict[str, float] = {n: 0.0 for n in navn}
    noder = 0

    # Resterende sum fra og med indeks i – brukt til pruning.
    rest_fra = [0.0] * (len(verdier) + 1)
    for i in range(len(verdier) - 1, -1, -1):
        rest_fra[i] = rest_fra[i + 1] + verdier[i]

    def mangler() -> float:
        return sum(max(0.0, mål[n] - sum_na[n]) for n in navn)

    def rek(i: int) -> bool:
        nonlocal noder
        noder += 1
        if noder > MAKS_NODER:
            return False
        if i == len(verdier):
            return all(abs(sum_na[n] - mål[n]) <= toleranse for n in navn)
        if rest_fra[i] + toleranse < mangler():
            return False
        v = verdier[i]
        prøvd: set[float] = set()
        for n in navn:
            if sum_na[n] in prøvd:      # like delsummer gir like greiner
                continue
            prøvd.add(sum_na[n])
            if sum_na[n] + v > mål[n] + toleranse:
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
    # tilbake til opprinnelig fortegn
    return {n: (sum(tildelt[n]) if maal[n] >= 0 else -sum(tildelt[n])) for n in navn}


class Personkobling:
    """Cacher fordelingen per (måned, konto)."""

    def __init__(self, ledger, er_lonnsbilag):
        self.ledger = ledger
        self.er_lonnsbilag = er_lonnsbilag
        self._cache: dict[tuple[str, int], dict | None] = {}

    def _linjer(self, maaned: str, konto: int) -> list[float]:
        return [
            p["beloep"] for p in self.ledger.aktive
            if p["konto"] == konto and p["dato"][:7] == maaned and self.er_lonnsbilag(p)
        ]

    def fordeling(self, maaned: str, konto: int, maal: dict[str, float]):
        nokkel = (maaned, konto)
        if nokkel not in self._cache:
            self._cache[nokkel] = fordel(maal, self._linjer(maaned, konto))
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
