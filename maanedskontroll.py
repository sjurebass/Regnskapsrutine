"""Månedskontroll for Tripletex-klienter.

    uv run --system-certs --with openpyxl python maanedskontroll.py --periode 2026-08
    uv run --system-certs --with openpyxl python maanedskontroll.py --periode 2026-08 --klient Eksempel
    uv run --system-certs --with openpyxl python maanedskontroll.py --periode 2026-08 --kontroll R1,R2,M1

Skriver «Kontroll ÅÅÅÅ-MM <Klient>.xlsx» i hver kundes årsmappe, én samlet
statusrapport i status/, og en linje i hver logg.md.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import traceback

from tools import config, logg, rapport
from tools.hent import Kontekst
from tools.kontroller import KATALOG, kjor
from tools.modeller import Klient, Periode, Resultat
from tools.profil import les_kjente_avvik, les_profil, merk_kjente
from tools.tripletex import Tripletex, TripletexFeil, fra_miljo


def kjor_klient(api: Tripletex, klient: Klient, periode: Periode, bare: set[str] | None) -> Resultat:
    profil = les_profil(klient.mappe, klient.navn)
    company_id = klient.company_id or profil.company_id
    if not company_id:
        raise TripletexFeil(
            "Mangler company_id. Sett den i klienter.json eller klientprofil.md "
            "(kjør hent-klienter.py for å slå den opp)."
        )
    api.bytt_selskap(company_id)
    kontekst = Kontekst(api, klient, profil, periode)
    resultat = Resultat(klient=klient, periode=periode)
    kjor(kontekst, resultat, bare)
    merk_kjente(resultat.funn, les_kjente_avvik(klient.mappe))

    mappe = os.path.join(klient.mappe, str(periode.aar))
    sti = rapport.skriv_klientrapport(
        resultat,
        kontekst.saldo_perioden(),
        kontekst.saldo_hittil(),
        kontekst.advarsler,
        mappe,
    )
    logg.loggfor(resultat, sti)
    return resultat


def main() -> int:
    p = argparse.ArgumentParser(description="Løpende kontroll av Tripletex-klienter")
    p.add_argument("--periode", help="ÅÅÅÅ-MM, f.eks. 2026-08")
    p.add_argument("--klient", help="Kjør bare klienter som matcher denne teksten")
    p.add_argument("--kontroll", help="Bare disse kontrollene, f.eks. R1,R2,M1")
    p.add_argument("--liste", action="store_true", help="Vis kontrollkatalogen og avslutt")
    args = p.parse_args()

    if args.liste:
        for k in KATALOG:
            krav = f"  (krever {', '.join(k.krever)})" if k.krever else ""
            print(f"{k.id:<4} {k.omraade:<10} {k.navn}{krav}")
        return 0

    if not args.periode:
        p.error("--periode er påkrevd (ÅÅÅÅ-MM)")

    config.last_env()
    periode = Periode.fra_tekst(args.periode)
    bare = {k.strip().upper() for k in args.kontroll.split(",")} if args.kontroll else None

    klienter = config.les_klienter()
    if args.klient:
        nal = args.klient.lower()
        klienter = [k for k in klienter if nal in k.navn.lower()]
    if not klienter:
        print("Ingen klienter å kjøre. Sjekk klienter.json eller --klient.")
        return 1

    try:
        api = fra_miljo()
    except TripletexFeil as e:
        print(e)
        return 1
    resultater: list[Resultat] = []
    start = time.time()
    for i, klient in enumerate(klienter, start=1):
        print(f"[{i}/{len(klienter)}] {klient.navn} … ", end="", flush=True)
        try:
            resultat = kjor_klient(api, klient, periode, bare)
            resultater.append(resultat)
            apne = resultat.aapne_funn
            print(
                f"{resultat.status} ({sum(1 for f in apne if f.alvorlighet == 'rød')} røde, "
                f"{sum(1 for f in apne if f.alvorlighet == 'gul')} gule)"
            )
        except Exception as e:
            print(f"FEIL: {e}")
            traceback.print_exc()
            feilet = Resultat(klient=klient, periode=periode)
            feilet.feil.append(("kjøring", f"{type(e).__name__}: {e}"))
            resultater.append(feilet)

    statussti = rapport.skriv_statusrapport(resultater, periode, config.STATUSMAPPE)
    logg.loggfor_kjoring(resultater, periode, statussti, config.STATUSMAPPE)
    print(
        f"\nFerdig på {time.time() - start:.0f} s, {api.kall_teller} API-kall.\n"
        f"Statusrapport: {statussti}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
