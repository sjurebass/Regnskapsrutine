"""
parse_maestro_xlsx.py – Parser for Maestro "Publisering"-XLSX

Maestro-filen har én rad per regnskapspost med kolonner:
  Tema | ID | Gruppe | Beskrivelse | I år | I fjor

"I år"   = inneværende år (f.eks. 2025)
"I fjor" = forrige år (f.eks. 2024 = IB 2025)

Brukes slik:
    python parse_maestro_xlsx.py <sti/til/maestro.xlsx>

Skriver JSON til stdout i samme format som haiku-agenten (steg 2B i SKILL.md):
{
  "selskap": "...",
  "partsnummer": "...",
  "ib_2025": {...},
  "midl_forskjeller_ib": {...},
  "sum_midl_forskjeller_ib": ...,
  "perm_forskjeller": {...},
  "ib_egenkapital": ...,
  "underskudd_fremfoering_ib": 0,
  "skatt_2025": {...},
  "merknad": ""
}
"""

import sys, json
import openpyxl

# Mapping Maestro-ID → vår kontokode (for ib_2025-dict)
MAESTRO_BALANSE_ID_MAP = {
    # Omløpsmidler
    "1000": "1000", "1100": "1100", "1200": "1200", "1230": "1230",
    "1300": "1300", "1320": "1320", "1340": "1340", "1360": "1360",
    "1500": "1500", "1530": "1530", "1570": "1570",
    "1800": "1800", "1920": "1920", "1930": "1930",
    # Egenkapital
    "2000": "2000", "2020": "2020", "2030": "2030",
    "2050": "2050", "2080": "2080",
    # Gjeld
    "2400": "2400", "2500": "2500", "2510": "2510",
    "2600": "2600", "2700": "2700", "2740": "2740",
    "2770": "2770", "2800": "2800", "2900": "2900",
}

MAESTRO_SUM_ID_MAP = {
    "balanseverdiForOmloepsmiddel-SUM": "sum_omloepsmidler",
    "anleggsmiddel-SUM": "sum_anleggsmidler",
    "Eiendeler-COMP": "sum_eiendeler",
    "egenkapital-SUM": "sum_egenkapital",
    "kortsiktigGjeld-SUM": "sum_kortsiktig_gjeld",
    "langsiktigGjeld-SUM": "sum_langsiktig_gjeld",
    "Gjeld-SUM": "sum_gjeld",
    "EKGjeld-COMP": "sum_gjeld_og_egenkapital",
}

def safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None

def parse_maestro_xlsx(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)

    # Finn "Publisering"-arket (eller første ark)
    ws = None
    for name in wb.sheetnames:
        if 'publisering' in name.lower() or ws is None:
            ws = wb[name]

    # Les alle rader inn i en dict: {(tema, id): (i_aar, i_fjor)}
    rows = {}
    selskap = None
    header_funnet = False

    for row in ws.iter_rows(values_only=True):
        if not any(v is not None for v in row):
            continue

        # Første rad: selskapsnavn
        if selskap is None and row[0] and isinstance(row[0], str) and 'Navn:' in row[0]:
            # "Navn: Dyktig Consulting AS.  Tid: ..."
            tekst = str(row[0])
            if 'Navn:' in tekst:
                selskap = tekst.split('Navn:')[1].split('.')[0].strip()
            continue

        # Overskriftsrad
        if row[0] == 'Tema' and row[1] == 'ID':
            header_funnet = True
            continue

        if not header_funnet:
            continue

        tema = row[0]
        id_  = row[1]
        i_aar   = safe_float(row[4])  # kolonne E = "I år"
        i_fjor  = safe_float(row[5])  # kolonne F = "I fjor"

        if tema and id_:
            # Lagre også rå streng-verdi for tekstfelt (f.eks. orgnr, navn)
            rows[(str(tema), str(id_))] = (i_aar, i_fjor, row[4], row[5])

    # ── Hent selskapsinfo ──────────────────────────────────────────────
    orgnr = None
    for (tema, id_), (i_aar, i_fjor, raw_aar, raw_fjor) in rows.items():
        if id_ == 'KlientOrgnr':
            # Orgnr er en streng, ikke tall
            orgnr_raw = raw_aar
            if orgnr_raw:
                orgnr = str(orgnr_raw).strip().replace(' ', '').replace('\xa0', '')
        if id_ == 'KlientNavn' and selskap is None:
            selskap = str(raw_aar).strip() if raw_aar else None

    # ── Balanse IB (= "I fjor" fra Maestro) ───────────────────────────
    ib_2025 = {}

    for (tema, id_), (i_aar, i_fjor, raw_aar, raw_fjor) in rows.items():
        if 'Balanse' not in tema and 'balanse' not in tema.lower():
            continue

        # Individuelle kontoer (numerisk ID)
        if id_ in MAESTRO_BALANSE_ID_MAP:
            vaar_kode = MAESTRO_BALANSE_ID_MAP[id_]
            if i_fjor is not None:
                ib_2025[vaar_kode] = i_fjor

        # Summer
        elif id_ in MAESTRO_SUM_ID_MAP:
            vaar_kode = MAESTRO_SUM_ID_MAP[id_]
            if i_fjor is not None:
                ib_2025[vaar_kode] = i_fjor

    # ── Midlertidige forskjeller (ikke i standard Maestro-export) ─────
    # Maestro Publisering har ikke midlertidige forskjeller direkte.
    # Returnerer tom dict; XML-parseren bruker sine egne verdier.
    midl_ib = {}
    sum_midl_ib = None  # Ikke tilgjengelig i standard Maestro-export

    # ── Permanente forskjeller ─────────────────────────────────────────
    perm_forskjeller = {}
    for (tema, id_), (i_aar, i_fjor, raw_aar, raw_fjor) in rows.items():
        if 'Permanente' in tema or 'permanente' in tema.lower():
            if id_.endswith('-COMP') or id_.endswith('-SUM'):
                continue
            if i_aar is not None:
                perm_forskjeller[id_] = i_aar

    # ── Egenkapital IB (= "I fjor" fra Maestro) ───────────────────────
    ib_egenkapital = None
    for (tema, id_), (i_aar, i_fjor, raw_aar, raw_fjor) in rows.items():
        if id_ == 'InngaaendeEK-COMP':
            # I Maestro-Egenkapital-arket: "I år" = inngående EK for inneværende år
            ib_egenkapital = i_aar
            break

    if ib_egenkapital is None:
        # Fallback: sum egenkapital "I fjor"
        ib_egenkapital = ib_2025.get("sum_egenkapital")

    # ── Skattedata (I år = 2025) ───────────────────────────────────────
    skattepliktig = None
    betalbar_skatt = None
    permanente_forskjeller_sum = None

    for (tema, id_), (i_aar, i_fjor, raw_aar, raw_fjor) in rows.items():
        if id_ == 'NaeringInntUnder':
            skattepliktig = i_aar
        elif id_ == 'OverskuddSkatt':
            if skattepliktig is None:
                skattepliktig = i_aar
        elif id_ == 'BetalbarSkattResultatUtenKildeskatt':
            betalbar_skatt = i_aar
        elif id_ == 'PermanenteForskjeller':
            permanente_forskjeller_sum = i_aar

    return {
        "selskap": selskap or "Ukjent AS",
        "partsnummer": orgnr,
        "ib_2025": ib_2025,
        "midl_forskjeller_ib": midl_ib,
        "sum_midl_forskjeller_ib": sum_midl_ib,
        "perm_forskjeller": perm_forskjeller,
        "ib_egenkapital": ib_egenkapital,
        "underskudd_fremfoering_ib": 0.0,  # Maestro-export har ikke dette direkte
        "skatt_2025": {
            "skattepliktig_inntekt": skattepliktig,
            "mid_forskjeller_ub": None,  # Ikke tilgjengelig i standard export
            "oppgitt_betalbar_skatt": betalbar_skatt,
            "oppgitt_endring_utsatt_skatt": None,
            "oppgitt_total_skattekostnad": None,
        },
        "merknad": "Lest fra Maestro Publisering-XLSX. Midlertidige forskjeller IB ikke tilgjengelig i dette formatet."
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Bruk: python parse_maestro_xlsx.py <sti/til/maestro.xlsx>", file=sys.stderr)
        sys.exit(1)
    data = parse_maestro_xlsx(sys.argv[1])
    print(json.dumps(data, ensure_ascii=False, indent=2))
