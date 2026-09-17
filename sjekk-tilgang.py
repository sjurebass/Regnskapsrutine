"""Diagnose: virker tokenet, og svarer endepunktene kontrollene bruker?

    uv run --system-certs python sjekk-tilgang.py --klient Eksempel --periode 2026-08

Kjøres første gang API-tilgangen settes opp, og hver gang en kontroll feiler med
en API-melding. Skriver ut hvilke endepunkter som svarer, hvor mange rader de
gir, og hvilke som ikke er tilgjengelige på klientens lisens.
"""

from __future__ import annotations

import argparse
import sys

from tools import config
from tools.hent import Kontekst
from tools.modeller import Periode
from tools.profil import les_profil
from tools.tripletex import TripletexFeil, fra_miljo


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--klient", help="Tekst som matcher klientnavnet")
    p.add_argument("--periode", default=None, help="ÅÅÅÅ-MM")
    args = p.parse_args()

    config.last_env()
    try:
        api = fra_miljo("0")
    except TripletexFeil as e:
        print(e)
        return 1

    print("1) Session token")
    try:
        meg = api.verdi("/token/session/>whoAmI", fields="*")
        print(f"   OK – {meg}")
    except TripletexFeil as e:
        print(f"   FEIL: {e}")
        return 1

    print("\n2) Klienttilgang")
    try:
        selskaper = api.liste("/company/>withLoginAccess", fields="id,name")
        print(f"   OK – {len(selskaper)} selskaper tilgjengelig")
    except TripletexFeil as e:
        print(f"   FEIL: {e}")
        selskaper = []

    if not args.klient:
        for s in selskaper[:50]:
            print(f"   {s.get('id'):<10} {s.get('name')}")
        print("\nKjør med --klient <navn> for å teste endepunktene på én klient.")
        return 0

    klienter = [k for k in config.les_klienter(bare_aktive=False) if args.klient.lower() in k.navn.lower()]
    if not klienter:
        print(f"Fant ingen klient som matcher «{args.klient}» i klienter.json")
        return 1
    klient = klienter[0]
    profil = les_profil(klient.mappe, klient.navn)
    company_id = klient.company_id or profil.company_id
    if not company_id:
        print(f"{klient.navn} mangler company_id.")
        return 1
    api.bytt_selskap(company_id)

    periode = Periode.fra_tekst(args.periode) if args.periode else Periode(2026, 1)
    k = Kontekst(api, klient, profil, periode)
    print(f"\n3) Endepunkter for {klient.navn} (companyId {company_id}), periode {periode}")
    prover = [
        ("kontoplan", k.kontoer),
        ("saldobalanse hittil", k.saldo_hittil),
        ("saldobalanse måned", k.saldo_perioden),
        ("posteringer måned", k.posteringer),
        ("åpne poster", k.apne_poster),
        ("bilag", k.bilag),
        ("regnskapsperioder", k.regnskapsperioder),
        ("bankavstemminger", k.bankavstemminger),
        ("leverandørfakturaer", k.leverandorfakturaer),
        ("mva-status", k.mva_status),
        ("lønnsslipper", k.lonnsslipper),
        ("bilagsmottak", k.bilagsmottak),
        ("ikke bokførte bilag", k.ikke_bokforte_bilag),
        ("anleggsmidler", k.anleggsmidler),
        ("timeregistreringer", k.timeregistreringer),
        ("varetellinger", k.varetellinger),
    ]
    for navn, funksjon in prover:
        try:
            data = funksjon()
            print(f"   OK    {navn:<24} {len(data)} rader")
        except Exception as e:
            print(f"   FEIL  {navn:<24} {str(e)[:120]}")

    if k.advarsler:
        print("\nAdvarsler underveis:")
        for a in k.advarsler:
            print(f"   {a[:160]}")
    print(f"\n{api.kall_teller} API-kall totalt.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
