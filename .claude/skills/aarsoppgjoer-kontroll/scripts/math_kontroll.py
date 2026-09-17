#!/usr/bin/env python3
"""
Matematisk kontroll av årsregnskap for norske små foretak.

Leser regnskap_data.json og kjører alle tallkontroller,
og skriver resultater til math_resultater.json.

Bruk: python math_kontroll.py <inn-fil.json> <ut-fil.json>

Støtter automatisk deteksjon av årstallsfeltet (beloep_2024, beloep_2025 osv.)
"""

import json
import sys


def kr(tall):
    """Formater tall som norsk kronerbeløp."""
    if tall is None:
        return "?"
    return f"{tall:,.0f}".replace(",", " ")


def sjekk(navn, beregnet, oppgitt, beregning_str):
    """Returner ett kontrollresultat."""
    if oppgitt is None:
        return {
            "kontroll": navn,
            "beregning": beregning_str,
            "resultat": f"Beregnet: {kr(beregnet)} (oppgitt: mangler)",
            "status": "MERKNAD",
        }
    diff = beregnet - oppgitt
    if diff == 0:
        return {
            "kontroll": navn,
            "beregning": beregning_str,
            "resultat": kr(oppgitt),
            "status": "OK",
        }
    elif abs(diff) <= 1:
        return {
            "kontroll": navn,
            "beregning": beregning_str,
            "resultat": f"Beregnet: {kr(beregnet)}, oppgitt: {kr(oppgitt)} — {abs(diff)} krone avrundingsfeil",
            "status": "MERKNAD",
        }
    else:
        return {
            "kontroll": navn,
            "beregning": beregning_str,
            "resultat": f"FEIL: beregnet {kr(beregnet)}, oppgitt {kr(oppgitt)}, differanse {kr(diff)}",
            "status": "FEIL",
        }


def hent(data, *nøkler, standard=None):
    """Hent nestet verdi trygt."""
    for nøkkel in nøkler:
        if not isinstance(data, dict):
            return standard
        data = data.get(nøkkel, standard)
        if data is None:
            return standard
    return data


def finn_aarsbeloep_felt(linjer):
    """
    Auto-detekter årstallsfeltet (beloep_2024, beloep_2025 osv.) fra linjene.
    Returnerer feltnavnet for inneværende år (høyeste årstall funnet).
    """
    kandidater = set()
    for linje in linjer:
        for key in linje.keys():
            if key.startswith("beloep_") and key[7:].isdigit():
                kandidater.add(key)
    if not kandidater:
        return "beloep_2025"  # fallback
    # Velg høyeste årstall (inneværende år)
    return max(kandidater, key=lambda k: int(k[7:]))


def kontroller(data):
    resultater = []
    merknader = []

    rr = hent(data, "resultatregnskap", standard={})
    summer_rr = hent(rr, "summer", standard={})
    linjer_rr = hent(rr, "linjer", standard=[])

    balanse = hent(data, "balanse", standard={})
    s_eiend = hent(balanse, "summer_eiendeler", standard={})
    s_ekgjeld = hent(balanse, "summer_ek_gjeld", standard={})
    linjer_eiend = hent(balanse, "eiendeler", standard=[])
    linjer_ekgjeld = hent(balanse, "ek_gjeld", standard=[])

    noter = hent(data, "noter", standard=[])

    # Auto-detekter årstallsfelt
    alle_linjer = linjer_rr + linjer_eiend + linjer_ekgjeld
    aarsbeloep = finn_aarsbeloep_felt(alle_linjer)

    # ── Resultatregnskap ──────────────────────────────────────────────

    # Sum driftsinntekter
    driftsinnt = [l for l in linjer_rr if l["post"].lower() in {
        "salgsinntekt", "annen driftsinntekt", "salgsinntekter",
        "andre driftsinntekter", "driftsinntekter",
    }]
    beregnet_sum_di = sum(l.get(aarsbeloep, 0) or 0 for l in driftsinnt)
    oppgitt_sum_di = summer_rr.get("sum_driftsinntekter")
    if oppgitt_sum_di is not None and driftsinnt:
        resultater.append(sjekk(
            "Sum driftsinntekter",
            beregnet_sum_di, oppgitt_sum_di,
            " + ".join(l["post"] for l in driftsinnt)
        ))

    # Driftsresultat
    oppgitt_driftsres = summer_rr.get("driftsresultat")
    if oppgitt_sum_di is not None and summer_rr.get("sum_driftskostnader") is not None:
        beregnet_driftsres = oppgitt_sum_di - summer_rr["sum_driftskostnader"]
        resultater.append(sjekk(
            "Driftsresultat",
            beregnet_driftsres, oppgitt_driftsres,
            "Sum driftsinntekter − Sum driftskostnader"
        ))

    # Resultat før skatt
    oppgitt_res_for_skatt = summer_rr.get("resultat_for_skatt")
    if oppgitt_driftsres is not None and summer_rr.get("resultat_av_finansposter") is not None:
        beregnet_res_for_skatt = oppgitt_driftsres + summer_rr["resultat_av_finansposter"]
        resultater.append(sjekk(
            "Resultat før skattekostnad",
            beregnet_res_for_skatt, oppgitt_res_for_skatt,
            "Driftsresultat + Resultat av finansposter"
        ))

    # Årsresultat
    oppgitt_aarsres = summer_rr.get("aarsresultat")
    if oppgitt_res_for_skatt is not None and summer_rr.get("skattekostnad") is not None:
        beregnet_aarsres = oppgitt_res_for_skatt - summer_rr["skattekostnad"]
        resultater.append(sjekk(
            "Årsresultat",
            beregnet_aarsres, oppgitt_aarsres,
            "Resultat før skatt − Skattekostnad"
        ))

    # ── Balanse ───────────────────────────────────────────────────────

    sum_anl = s_eiend.get("sum_anleggsmidler")
    sum_oml = s_eiend.get("sum_omlopsmidler")
    sum_eiend_oppg = s_eiend.get("sum_eiendeler")

    if sum_anl is not None and sum_oml is not None:
        resultater.append(sjekk(
            "Sum eiendeler",
            sum_anl + sum_oml,
            sum_eiend_oppg,
            "Sum anleggsmidler + Sum omløpsmidler"
        ))

    sum_ek = s_ekgjeld.get("sum_egenkapital")
    sum_gjeld = s_ekgjeld.get("sum_gjeld")
    sum_ekgjeld_oppg = s_ekgjeld.get("sum_ek_gjeld")

    if sum_ek is not None and sum_gjeld is not None:
        resultater.append(sjekk(
            "Sum egenkapital og gjeld",
            sum_ek + sum_gjeld,
            sum_ekgjeld_oppg,
            "Sum egenkapital + Sum gjeld"
        ))

    # Balansen går opp
    if sum_eiend_oppg is not None and sum_ekgjeld_oppg is not None:
        if sum_eiend_oppg == sum_ekgjeld_oppg:
            resultater.append({
                "kontroll": "Balansen går opp (eiendeler = EK + gjeld)",
                "beregning": f"{kr(sum_eiend_oppg)} = {kr(sum_ekgjeld_oppg)}",
                "resultat": "✓",
                "status": "OK",
            })
        else:
            diff = sum_eiend_oppg - sum_ekgjeld_oppg
            resultater.append({
                "kontroll": "Balansen går opp (eiendeler = EK + gjeld)",
                "beregning": f"Eiendeler {kr(sum_eiend_oppg)} vs. EK+gjeld {kr(sum_ekgjeld_oppg)}",
                "resultat": f"FEIL – differanse {kr(diff)}",
                "status": "FEIL",
            })

    # ── Noters interne konsistens ─────────────────────────────────────

    for note in noter:
        nr = note.get("nummer")
        tittel = note.get("tittel", "")
        note_summer = note.get("summer", {})
        if not note_summer:
            continue

        # Lønnskostnadsnote
        if "lønn" in tittel.lower() and "sum" in note_summer:
            note_sum = note_summer["sum"]
            rr_lønn = next(
                (l.get(aarsbeloep) for l in linjer_rr
                 if "lønn" in l["post"].lower()),
                None
            )
            if rr_lønn is not None:
                resultater.append(sjekk(
                    f"Note {nr} ({tittel}) sum vs. resultatregnskap",
                    note_sum, rr_lønn,
                    f"Note-sum {kr(note_sum)} vs. RR lønnskostnad {kr(rr_lønn)}"
                ))

        # Egenkapitalnote
        if "egenkapital" in tittel.lower() and "sluttsaldo" in note_summer:
            note_ek = note_summer["sluttsaldo"]
            if sum_ek is not None:
                resultater.append(sjekk(
                    f"Note {nr} ({tittel}) sluttsaldo vs. balanse sum EK",
                    note_ek, sum_ek,
                    f"Note-sluttsaldo {kr(note_ek)} vs. balanse {kr(sum_ek)}"
                ))

    if not resultater:
        merknader.append(
            "Ikke tilstrekkelig talldata i regnskap_data.json til å gjøre automatisk kontroll."
        )

    return resultater, " ".join(merknader) if merknader else ""


def main():
    if len(sys.argv) < 3:
        print("Bruk: python math_kontroll.py <regnskap_data.json> <math_resultater.json>")
        sys.exit(1)

    inn_fil = sys.argv[1]
    ut_fil = sys.argv[2]

    try:
        with open(inn_fil, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"Finner ikke {inn_fil}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"JSON-feil i {inn_fil}: {e}")
        sys.exit(1)

    resultater, merknad = kontroller(data)

    output = {
        "matematikk": resultater,
        "merknad": merknad,
    }

    with open(ut_fil, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    antall_feil = sum(1 for r in resultater if r["status"] == "FEIL")
    antall_ok = sum(1 for r in resultater if r["status"] == "OK")
    print(f"Matematisk kontroll ferdig: {antall_ok} OK, {antall_feil} feil av {len(resultater)} kontroller")
    print(f"Årstallsfelt brukt: {next((k for l in data.get('resultatregnskap', {}).get('linjer', []) for k in l if k.startswith('beloep_')), 'ikke funnet')}")
    print(f"Resultater skrevet til {ut_fil}")


if __name__ == "__main__":
    main()
