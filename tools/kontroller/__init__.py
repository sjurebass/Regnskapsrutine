"""Kontrollkatalogen – registeret alle kjøringer går gjennom."""

from __future__ import annotations

import traceback

from ..hent import Kontekst
from ..modeller import Funn, Kontroll, Resultat
from . import analyse, bank, bilag, bransje, eier, lonn, mva, reskontro

MODULER = [bank, reskontro, mva, lonn, bilag, eier, analyse, bransje]

KATALOG: list[Kontroll] = [k for modul in MODULER for k in modul.KONTROLLER]
ETTER_ID: dict[str, Kontroll] = {k.id: k for k in KATALOG}


def aktuelle(profil, bare: set[str] | None = None) -> list[Kontroll]:
    """Kontrollene som skal kjøres for denne klienten."""
    ut = []
    for kontroll in KATALOG:
        if bare and kontroll.id not in bare:
            continue
        if kontroll.id in profil.deaktiverte_kontroller:
            continue
        if any(not profil.har(flagg) for flagg in kontroll.krever):
            continue
        ut.append(kontroll)
    return ut


def kjor(kontekst: Kontekst, resultat: Resultat, bare: set[str] | None = None) -> Resultat:
    profil = kontekst.profil
    for kontroll in KATALOG:
        if bare and kontroll.id not in bare:
            continue
        if kontroll.id in profil.deaktiverte_kontroller:
            resultat.hoppet_over.append((kontroll.id, "slått av i klientprofil"))
            continue
        manglende = [flagg for flagg in kontroll.krever if not profil.har(flagg)]
        if manglende:
            resultat.hoppet_over.append((kontroll.id, f"krever {', '.join(manglende)}"))
            continue
        try:
            funn = kontroll.funksjon(kontekst) or []
            for f in funn:
                if not f.omraade:
                    f.omraade = kontroll.omraade
            resultat.funn.extend(funn)
            resultat.kjorte.append(kontroll.id)
        except Exception as e:  # én kontroll skal ikke velte hele kjøringen
            resultat.feil.append((kontroll.id, f"{type(e).__name__}: {e}"))
            traceback.print_exc()
    resultat.funn.sort(key=lambda f: f.sorteringsnokkel())
    return resultat
