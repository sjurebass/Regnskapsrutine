"""Oppretter klientprofil.md og kjente-avvik.md for hver kundemappe.

    uv run python lag-klientfiler.py

Rører ikke filer som allerede finnes. Kjør den igjen når du får en ny kunde.
"""

from __future__ import annotations

import os
import sys

from tools import config

PROFILMAL = """# Klientprofil – {navn}

Styrer hvilke kontroller som kjøres på denne klienten. Felt merket `?` må
bekreftes – til det er gjort brukes standardverdien i parentes.

| Felt | Verdi |
|---|---|
| company_id | {company_id} |
| orgnr | {orgnr} |
| mva_pliktig | {mva} |
| lonn | {lonn} |
| prosjekt | {prosjekt} |
| varelager | {varelager} |
| anleggsmidler | {anleggsmidler} |
| utleie | {utleie} |
| vesentlighet | 5000 |
| vesentlighet_prosent | 0.5 |
| avvik_prosent | 30 |
| deaktiverte_kontroller | - |

Kontonumre overstyres bare hvis klienten avviker fra standard kontoplan.
Tom eller `-` betyr at standarden brukes.

| Felt | Verdi |
|---|---|
| konto_kunde | - |
| konto_leverandor | - |
| konto_forskuddstrekk | - |
| konto_skyldig_aga | - |
| konto_feriepenger | - |
| konto_skyldig_lonn | - |
| konto_mva_utgaaende | - |
| konto_mva_inngaaende | - |
| konto_mva_oppgjor | - |
| konto_mellomregning | - |
| konto_observasjon | - |
| konto_varelager | - |
| konto_avskrivning | - |

## Notater

{notater}
"""

AVVIKSMAL = """# Kjente avvik – {navn}

Avvik som er vurdert og skal rapporteres som «kjent» i stedet for å dukke opp
som nytt hver måned. Nøkkelen står i kolonnen «Nøkkel» i kontrollrapporten –
kopier den hit sammen med forklaringen.

Sett en dato i «Gyldig til» når avviket skal opp til ny vurdering. Tom dato
betyr at det gjelder til noen fjerner linjen. Endrer beløpet seg, får avviket
ny nøkkel og dukker opp på nytt – det er meningen.

| Nøkkel | Kontroll | Forklaring | Gyldig til |
|---|---|---|---|
"""

STANDARD = {
    "mva": "? (ja)",
    "lonn": "? (nei)",
    "prosjekt": "? (nei)",
    "varelager": "? (nei)",
    "anleggsmidler": "? (ja)",
    "utleie": "? (nei)",
}


def main() -> int:
    laget = 0
    for mappenavn in config.klientmapper():
        mappe = os.path.join(config.ROT, mappenavn)
        felt = dict(STANDARD)

        profilsti = os.path.join(mappe, "klientprofil.md")
        if not os.path.exists(profilsti):
            with open(profilsti, "w", encoding="utf-8") as f:
                f.write(
                    PROFILMAL.format(
                        navn=mappenavn,
                        company_id=config.mappenavn_til_nummer(mappenavn) or "?",
                        orgnr="?",
                        notater=(
                            "Fyll inn særegenheter: hvem som fører bilag, faste "
                            "periodiseringer, avtaler som påvirker kontrollene."
                        ),
                        **felt,
                    )
                )
            laget += 1
            print(f"opprettet {mappenavn}/klientprofil.md")

        avvikssti = os.path.join(mappe, "kjente-avvik.md")
        if not os.path.exists(avvikssti):
            with open(avvikssti, "w", encoding="utf-8") as f:
                f.write(AVVIKSMAL.format(navn=mappenavn))
            laget += 1
            print(f"opprettet {mappenavn}/kjente-avvik.md")

    os.makedirs(config.STATUSMAPPE, exist_ok=True)
    print(f"\n{laget} filer opprettet.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
