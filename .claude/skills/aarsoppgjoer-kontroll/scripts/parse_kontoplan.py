"""
parse_kontoplan.py – Parser og kvalitetskontroll for kontoplan/saldobalanse XLSX

Leser en kontoplan-XLSX med kolonner:
  Kontonr | Kontobetegnelse | Fortegn | ... | Saldo 2024 | ... |
  ResBalRef | PermanentRef | MidForsRef | EKRef | ...

Funksjoner:
  1. Summerer Saldo 2024 per MidForsRef → IB 2025 per midlertidig-forskjell-typekode
  2. Kontroll: Utsatt skattefordel (1070) vs. utsatt skatteforpliktelse (2120/2121)
  3. Kontroll: Kontoer med ikke-fradragsberettigede kostnader (PermanentRef != '' og Saldo != 0)

Brukes slik:
    python parse_kontoplan.py <sti/til/kontoplan.xlsx>
    python parse_kontoplan.py <sti/til/kontoplan.xlsx> --xml-perm <sti/til/xml_data.json>

Skriver JSON til stdout:
{
  "selskap": "BOOKIS AS",
  "ib_2025_midl": {"101": 7685639.92, "140": 94098.75, "141": 292575.92},
  "quality_checks": {
    "utsatt_skatt_konflikt": {
      "ok": true,
      "kto_1070": 0.0, "kto_2120": 0.0, "kto_2121": 0.0,
      "melding": "Utsatt skattefordel og -forpliktelse er konsistente"
    },
    "ikke_fradragsberettiget": {
      "ok": false,
      "kontoer": [
        {"kontonr": "7791", "navn": "...", "saldo_2024": 965.99, "permanent_ref": "0610"}
      ],
      "sum_per_ref": {"0610": 3688.33},
      "total": 3688.33,
      "melding": "3 688 kr på ikke-fradragsberettigede kontoer uten tilsvarende permanent forskjell"
    }
  }
}
"""

import sys, json, re
from collections import defaultdict
import openpyxl


def safe_float(val):
    if val is None:
        return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def finn_header_rad(ws):
    """Finn raden som inneholder 'Kontonr' i første kolonne (0-indeksert radnummer)."""
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if row[0] is not None and str(row[0]).strip().lower() in ('kontonr', 'konto nr', 'konto'):
            return i, list(row)
    raise ValueError(
        "Fant ikke kolonneoverskrift 'Kontonr' i kontoplan. "
        "Sjekk at filen er en kontoplan-XLSX med riktig format."
    )


def finn_kol(headers, *alternativ):
    """Returner indeks for første treff (case-insensitive) blant alternativ."""
    headers_lower = [str(h).strip().lower() if h else '' for h in headers]
    for alt in alternativ:
        alt_l = alt.lower()
        for i, h in enumerate(headers_lower):
            if h == alt_l or alt_l in h:
                return i
    return None


def parse_kontoplan(xlsx_path, xml_perm_data=None):
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb[wb.sheetnames[0]]

    # Hent selskapsnavn (typisk rad 2–3 i Maestro/Sticos-eksport)
    selskap = None
    rows_list = list(ws.iter_rows(values_only=True))
    for row in rows_list[:5]:
        if row[0] and isinstance(row[0], str) and len(row[0].strip()) > 3:
            tekst = row[0].strip()
            # Hopp over generiske overskrifter
            if tekst.lower() not in ('kontoplan', 'kontoplan/saldobalanse', 'saldobalanse',
                                      'kontonr', 'konto'):
                selskap = tekst
                break

    # Finn kolonneoverskrifter
    header_idx, headers = finn_header_rad(ws)

    kol_kontonr  = finn_kol(headers, 'Kontonr', 'Konto', 'konto_nr')
    kol_navn     = finn_kol(headers, 'Kontobetegnelse', 'Betegnelse', 'Kontonavn', 'Navn')
    kol_saldo    = finn_kol(headers, 'Saldo 2024', 'Saldo2024', 'UB 2024', 'Saldo')
    kol_perm     = finn_kol(headers, 'PermanentRef', 'Permanent ref', 'Permanent')
    kol_midl     = finn_kol(headers, 'MidForsRef', 'MidFors ref', 'MidFors', 'Midlertidig')

    if kol_kontonr is None or kol_saldo is None:
        raise ValueError(
            f"Fant ikke nødvendige kolonner i kontoplan. Headers: {headers[:10]}"
        )

    # ── Les alle kontoer ───────────────────────────────────────────────
    kontoer = {}  # kontonr → dict
    for row in rows_list[header_idx + 1:]:
        kontonr = row[kol_kontonr] if kol_kontonr < len(row) else None
        if not kontonr:
            continue
        kontonr = str(kontonr).strip()
        if not re.match(r'^\d{4}$', kontonr):
            continue  # Hopp over sum-linjer og andre ikke-kontoer

        navn   = str(row[kol_navn]).strip()   if kol_navn  and kol_navn  < len(row) else ''
        saldo  = safe_float(row[kol_saldo])   if kol_saldo and kol_saldo < len(row) else 0.0
        perm   = str(row[kol_perm]).strip()   if kol_perm  and kol_perm  < len(row) else ''
        midl   = str(row[kol_midl]).strip()   if kol_midl  and kol_midl  < len(row) else ''
        perm   = '' if perm  in ('None', 'nan') else perm
        midl   = '' if midl  in ('None', 'nan') else midl

        kontoer[kontonr] = {
            'kontonr': kontonr,
            'navn': navn,
            'saldo_2024': saldo,
            'permanent_ref': perm,
            'midfors_ref': midl,
        }

    # ── 1. IB 2025 per midlertidig-forskjell-typekode ──────────────────
    ib_2025_midl = defaultdict(float)
    for k, kto in kontoer.items():
        if kto['midfors_ref'] and kto['saldo_2024']:
            ib_2025_midl[kto['midfors_ref']] += kto['saldo_2024']
    ib_2025_midl = {k: round(v, 2) for k, v in sorted(ib_2025_midl.items())}

    # ── 2. Utsatt skattefordel vs. -forpliktelse ───────────────────────
    kto_1070 = abs(kontoer.get('1070', {}).get('saldo_2024', 0.0))
    kto_2120 = abs(kontoer.get('2120', {}).get('saldo_2024', 0.0))
    kto_2121 = abs(kontoer.get('2121', {}).get('saldo_2024', 0.0))
    kto_utsatt = kto_2120 + kto_2121

    # Konflikt: begge sider er non-zero (> 1 kr toleranse)
    utsatt_konflikt = kto_1070 > 1.0 and kto_utsatt > 1.0
    if utsatt_konflikt:
        utsatt_melding = (
            f"KONFLIKT: Kto 1070 = {kto_1070:,.0f} kr OG kto 2120/2121 = {kto_utsatt:,.0f} kr. "
            "Nettostørrelser skal kun stå på én side. "
            "Sjekk om utsatt skattefordel (1070) eller -forpliktelse (2120/2121) er korrekt."
        )
    else:
        utsatt_melding = (
            f"OK – kto 1070 = {kto_1070:,.0f} kr, kto 2120 = {kto_2120:,.0f} kr, "
            f"kto 2121 = {kto_2121:,.0f} kr. Kun én side er beløpssatt."
        )

    utsatt_sjekk = {
        'ok': not utsatt_konflikt,
        'kto_1070': kto_1070,
        'kto_2120': kto_2120,
        'kto_2121': kto_2121,
        'melding': utsatt_melding,
    }

    # ── 3. Ikke-fradragsberettigede kostnader ──────────────────────────
    ikke_fradrag_kontoer = []
    sum_per_ref = defaultdict(float)

    for kontonr, kto in sorted(kontoer.items()):
        perm = kto['permanent_ref']
        saldo = kto['saldo_2024']
        if not perm or abs(saldo) <= 0.01:
            continue
        # Denne kontoen er merket som permanent forskjell og har saldo
        ikke_fradrag_kontoer.append({
            'kontonr': kontonr,
            'navn': kto['navn'],
            'saldo_2024': round(saldo, 2),
            'permanent_ref': perm,
        })
        sum_per_ref[perm] += saldo

    sum_per_ref = {k: round(v, 2) for k, v in sorted(sum_per_ref.items())}
    total_ikke_fradrag = round(sum(sum_per_ref.values()), 2)

    if ikke_fradrag_kontoer:
        kontoer_str = ', '.join(
            f"kto {kto['kontonr']} ({kto['saldo_2024']:,.2f} kr)"
            for kto in ikke_fradrag_kontoer[:5]
        )
        if total_ikke_fradrag > 0.01:
            iff_melding = (
                f"ADVARSEL: Totalt {total_ikke_fradrag:,.2f} kr på kontoer med permanentref "
                f"(ikke-fradragsberettigede kostnader): {kontoer_str}. "
                "Disse skal legges til som permanente forskjeller i skattemeldingen "
                "(øker skattepliktig inntekt / reduserer underskuddet)."
            )
            iff_ok = False
        else:
            iff_melding = "Alle permanentref-kontoer har saldo 0 – OK."
            iff_ok = True
    else:
        iff_melding = "Ingen kontoer med permanentref og saldo – OK."
        iff_ok = True

    ikke_fradrag_sjekk = {
        'ok': iff_ok,
        'kontoer': ikke_fradrag_kontoer,
        'sum_per_ref': sum_per_ref,
        'total': total_ikke_fradrag,
        'melding': iff_melding,
    }

    return {
        'selskap': selskap or 'Ukjent AS',
        'ib_2025_midl': ib_2025_midl,
        'quality_checks': {
            'utsatt_skatt_konflikt': utsatt_sjekk,
            'ikke_fradragsberettiget': ikke_fradrag_sjekk,
        },
    }


if __name__ == '__main__':
    # Claudes scratch-mapper kan gi stier over Windows' grense på 260 tegn – bruk utvidet form.
    import os as _os
    sys.path.insert(0, _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "silfer-rapport", "scripts"))
    from silfer.filer import os_sti
    sys.argv[1:] = [a if a.startswith("-") else os_sti(a) for a in sys.argv[1:]]
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('kontoplan_xlsx')
    parser.add_argument('--xml-perm', dest='xml_perm', default=None,
                        help='Sti til xml_data.json for krysskontroll mot permanent forskjell')
    args = parser.parse_args()
    data = parse_kontoplan(args.kontoplan_xlsx)
    print(json.dumps(data, ensure_ascii=False, indent=2))
