"""
parse_skatteetaten_xlsx.py – Parser for Skatteetaten «Skattemelding»-XLSX

Format: 3 ark: Oppsummering / Skattemelding / Næringsspesifikasjon
Kolonne­struktur i Næringsspesifikasjon for midlertidige forskjeller:
  Navn og beskrivelse | RM | SM | RM i fjor | SM i fjor

«RM i fjor» = regnskapsmessig verdi UB 2024 = IB 2025 per type
«SM i fjor» = skattemessig verdi UB 2024

Brukes slik:
    python parse_skatteetaten_xlsx.py <sti/til/skattemelding.xlsx>

Skriver JSON til stdout i samme format som parse_maestro_xlsx.py:
{
  "selskap": "...",
  "partsnummer": null,
  "ib_2025": {},
  "midl_forskjeller_ib": {"101": 7685639.92, ...},
  "sum_midl_forskjeller_ib": null,
  "perm_forskjeller": {},
  "ib_egenkapital": 1301489.80,
  "underskudd_fremfoering_ib": 104506941.0,
  "skatt_2025": {...},
  "merknad": ""
}
"""

import sys, json, re
import openpyxl


def safe_float(val):
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def parse_skatteetaten_xlsx(xlsx_path):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)

    # Krev at alle tre arkene finnes
    sheet_names_lower = [s.lower() for s in wb.sheetnames]
    if not any('oppsummering' in s for s in sheet_names_lower):
        raise ValueError(
            f"Fant ikke 'Oppsummering'-ark. Arknavn: {wb.sheetnames}. "
            "Sjekk at filen er en Skatteetaten-XLSX (ikke Maestro-format)."
        )

    def get_sheet(keyword):
        for name in wb.sheetnames:
            if keyword.lower() in name.lower():
                return wb[name]
        return None

    ws_opps  = get_sheet('oppsummering')
    ws_skatt = get_sheet('skattemelding')
    ws_naer  = get_sheet('næringsspesifikasjon')

    # ── Selskapsinfo fra filnavn (XLSX har ikke orgnr) ──────────────────
    import os
    filnavn = os.path.basename(xlsx_path)
    selskap = None
    # Prøv å hente selskapsnavn fra filnavnet (f.eks. «Skattemelding 2025 for BOOKIS AS.xlsx»)
    m = re.search(r'for\s+(.+?)\.xlsx', filnavn, re.IGNORECASE)
    if m:
        selskap = m.group(1).strip()

    # ── Oppsummering-ark: næringsinntekt + underskudd IB ────────────────
    naerings_inntekt  = None
    underskudd_ib     = None
    skattemessig_res  = None

    if ws_opps:
        for row in ws_opps.iter_rows(values_only=True):
            navn, _, verdi = (row + (None, None, None))[:3]
            if navn is None:
                continue
            navn_l = str(navn).lower()
            if 'næringsinntekt' in navn_l and 'beregnet' not in navn_l:
                if naerings_inntekt is None:
                    naerings_inntekt = safe_float(verdi)
            elif 'underskudd til fremføring per 01.01' in navn_l:
                underskudd_ib = safe_float(verdi)
            elif 'skattemessig resultat' in navn_l:
                skattemessig_res = safe_float(verdi)

    # ── Næringsspesifikasjon-ark ─────────────────────────────────────────
    midl_forskjeller_ib = {}   # type_kode → RM i fjor (IB 2025)
    midl_forskjeller_ub = {}   # type_kode → RM (UB 2025)
    ib_egenkapital       = None
    ub_egenkapital       = None
    skattemessig_avskreiv = None  # Saldoavskrivning + lineær avskrivning sum

    i_midl_seksjon = False  # Vi er inne i midlertidige-forskjeller-seksjonen

    if ws_naer:
        for row in ws_naer.iter_rows(values_only=True):
            # Skipper tomme rader
            if not any(v is not None for v in row):
                continue

            navn = row[0]
            if navn is None:
                continue
            navn_str = str(navn).strip()
            navn_l   = navn_str.lower()

            # Gjenkjenn overskrift for midlertidige forskjeller
            if navn_l == 'navn og beskrivelse' and len(row) >= 5:
                # Sjekk at kolonne 4 og 5 inneholder «RM»/«SM»/«i fjor»
                i_midl_seksjon = True
                continue

            # Hent EK IB/UB fra egenkapitalavstemming
            if 'egenkapital pr 31.12. i fjor' in navn_l or 'egenkapital pr 31.12 i fjor' in navn_l:
                ib_egenkapital = safe_float(row[2])
                continue
            if ('egenkapital pr 31.12.' in navn_l or 'egenkapital pr 31.12 ' in navn_l) \
                    and 'i fjor' not in navn_l:
                ub_egenkapital = safe_float(row[2])
                continue

            # Skattemessig avskrivning (for krysskontroll med årsregnskap)
            if 'tillegg for skattemessig avskrivning' in navn_l:
                skattemessig_avskreiv = safe_float(row[2])
                continue

            # Midlertidige forskjeller: rader med 5 kolonner og typekode i navn
            if i_midl_seksjon and row[1] is None and row[2] is not None or \
               i_midl_seksjon and row[3] is not None:
                # Prøv å hente typekode (3 siffer) fra starten av radnavnet
                m = re.match(r'^(\d{3})\s', navn_str)
                if m:
                    kode = m.group(1)
                    rm_ib   = safe_float(row[3]) if len(row) > 3 else None  # RM i fjor
                    rm_ub   = safe_float(row[1]) if len(row) > 1 else None  # RM (inneværende)
                    if rm_ib is not None:
                        midl_forskjeller_ib[kode] = rm_ib
                    if rm_ub is not None:
                        midl_forskjeller_ub[kode] = rm_ub
                else:
                    # Ikke en midlertidige-forskjell-rad med kode → avslutt seksjon
                    if navn_str not in ('', 'Navn og beskrivelse'):
                        i_midl_seksjon = False

    # ── Skattemelding-ark: fremførbart underskudd ────────────────────────
    if ws_skatt:
        for row in ws_skatt.iter_rows(values_only=True):
            navn, _, verdi = (row + (None, None, None))[:3]
            if navn is None:
                continue
            navn_l = str(navn).lower()
            if 'fremført underskudd fra tidligere år' in navn_l:
                if underskudd_ib is None:
                    underskudd_ib = safe_float(verdi)
            if naerings_inntekt is None and 'næringsinntekt' in navn_l:
                naerings_inntekt = safe_float(verdi)

    # ── Sum midlertidige forskjeller IB ─────────────────────────────────
    # Ikke oppgitt direkte i Skatteetaten-XLSX; beregn fra enkeltposter
    sum_midl_ib = sum(midl_forskjeller_ib.values()) if midl_forskjeller_ib else None

    return {
        "selskap": selskap or "Ukjent AS",
        "partsnummer": None,  # Ikke i XLSX-filen – hentes fra XML
        "ib_2025": {},        # Individuelle kontoer ikke tilgjengelig – bruk kontoplan
        "midl_forskjeller_ib": midl_forskjeller_ib,
        "sum_midl_forskjeller_ib": sum_midl_ib,
        "perm_forskjeller": {},
        "ib_egenkapital": ib_egenkapital,
        "underskudd_fremfoering_ib": underskudd_ib or 0.0,
        "skatt_2025": {
            "skattepliktig_inntekt": naerings_inntekt,
            "mid_forskjeller_ub": sum(midl_forskjeller_ub.values()) if midl_forskjeller_ub else None,
            "oppgitt_betalbar_skatt": None,   # Ikke direkte oppgitt i XLSX
            "oppgitt_endring_utsatt_skatt": None,
            "oppgitt_total_skattekostnad": None,
        },
        "_skattemessig_avskrivning": skattemessig_avskreiv,
        "merknad": (
            "Lest fra Skatteetaten XLSX (3-arks format). "
            "Individuelle balansekontoer ikke tilgjengelig – last opp kontoplan for full IB-kontroll. "
            "Midlertidige forskjeller IB er RM i fjor per type (3-sifret kode)."
        )
    }


if __name__ == "__main__":
    # Claudes scratch-mapper kan gi stier over Windows' grense på 260 tegn – bruk utvidet form.
    import os as _os
    sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "silfer-rapport", "scripts"))
    from silfer.filer import os_sti
    sys.argv[1:] = [a if a.startswith("-") else os_sti(a) for a in sys.argv[1:]]
    if len(sys.argv) < 2:
        print("Bruk: python parse_skatteetaten_xlsx.py <sti/til/skattemelding.xlsx>",
              file=sys.stderr)
        sys.exit(1)
    data = parse_skatteetaten_xlsx(sys.argv[1])
    print(json.dumps(data, ensure_ascii=False, indent=2))
