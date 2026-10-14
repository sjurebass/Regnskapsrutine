"""
parse_xml.py – Parser for Skatteetatens skattemeldingOgNaeringsspesifikasjonRequest (v3)

Brukes slik:
    python parse_xml.py <sti/til/skattemelding.xml>

Skriver et JSON-objekt til stdout med alle relevante tall for IB/UB-kontroll
og skatteberegningskontroll.

Versjon 3 legger til:
- Egenkapitalavstemming (inngaaende + utgaaende EK)
- Permanente forskjeller (listet per post)
- Midlertidige forskjeller IB (bugfix: ForrigeInntektsaar med dobbel 'r')
- Fremførbart underskudd (allerede støttet, nå eksportert som UB)
"""

import sys, json, base64, re
import xml.etree.ElementTree as ET

# Kontotypekoder → lesbare norske navn
KONTO_NAVN = {
    # Eiendeler (1xxx)
    "1000": "Immaterielle eiendeler",
    "1100": "Tomter, bygninger og annen fast eiendom",
    "1200": "Maskiner og anlegg",
    "1230": "Driftsløsøre, inventar o.l.",
    "1300": "Investering i datterselskap",
    "1320": "Investering i tilknyttet selskap",
    "1340": "Investering i aksjer og andeler",
    "1360": "Obligasjoner og andre fordringer",
    "1500": "Kundefordringer",
    "1530": "Andre kortsiktige fordringer",
    "1570": "Andre fordringer",
    "1800": "Aksjer og andeler",
    "1920": "Bankinnskudd",
    "1930": "Kontanter og lignende",
    # Egenkapital (20xx)
    "2000": "Aksjekapital",
    "2020": "Egne aksjer",
    "2030": "Overkurs",
    "2050": "Annen egenkapital",
    "2080": "Udekket tap",
    # Gjeld (24xx–29xx)
    "2400": "Leverandørgjeld",
    "2500": "Betalbar skatt",
    "2510": "Skyldig merverdiavgift",
    "2600": "Skattetrekk og andre trekk",
    "2700": "Skyldig arbeidsgiveravgift og feriepenger",
    "2740": "Skyldig arbeidsgiveravgift",
    "2770": "Skyldig lønn",
    "2800": "Annen kortsiktig gjeld",
    "2900": "Langsiktig gjeld",
}

def finn_tekst(element, *tags):
    """Naviger ned i XML-treet og returner tekstinnhold (None hvis ikke funnet)."""
    current = element
    for tag in tags:
        found = None
        for child in current:
            local = child.tag.split('}')[-1] if '}' in child.tag else child.tag
            if local == tag:
                found = child
                break
        if found is None:
            return None
        current = found
    return current.text

def hent_beloep(element):
    """Henter første numeriske beløp fra et element (prøver ulike nøstingsdybder)."""
    for path in [
        ['beloep', 'beloepSomHeltall'],
        ['beloepSomHeltall'],
        ['beloep', 'beloep'],
        ['beloep', 'beloep', 'beloep'],
        ['beloep'],
    ]:
        val = finn_tekst(element, *path)
        if val is not None:
            try:
                return float(val)
            except ValueError:
                pass
    return None

def strip_ns(tag):
    return tag.split('}')[-1] if '}' in tag else tag

def parse_wrapper(xml_path):
    """Parser wrapper-XML og returnerer de to dekodet sub-XML-ene som ET-trær."""
    with open(xml_path, 'r', encoding='utf-8') as f:
        raw = f.read()

    # Hent typer og base64-innhold
    types    = re.findall(r'<type>(.*?)</type>', raw)
    contents = re.findall(r'<content>(.*?)</content>', raw, re.DOTALL)

    inntektsaar = re.search(r'<inntektsaar>(\d{4})</inntektsaar>', raw)
    inntektsaar = inntektsaar.group(1) if inntektsaar else "ukjent"

    docs = {}
    for doc_type, b64 in zip(types, contents):
        decoded_xml = base64.b64decode(b64.strip()).decode('utf-8')
        docs[doc_type] = ET.fromstring(decoded_xml)

    return docs, inntektsaar

def parse_skattemelding(tree):
    """Trekker ut skattetall fra skattemeldingUpersonlig."""
    def find(tag):
        for el in tree.iter():
            if strip_ns(el.tag) == tag:
                return el
        return None

    result = {
        "partsnummer": None,
        "inntektsaar": None,
        "skattepliktig_inntekt": None,
        "underskudd_til_fremfoering": 0,
    }

    pnr = find('partsnummer')
    if pnr is not None and pnr.text:
        result["partsnummer"] = pnr.text.strip()

    aar = find('inntektsaar')
    if aar is not None and aar.text:
        result["inntektsaar"] = aar.text.strip()

    # Skattepliktig inntekt = samletInntekt
    for el in tree.iter():
        if strip_ns(el.tag) == 'samletInntekt':
            v = hent_beloep(el)
            if v is not None:
                result["skattepliktig_inntekt"] = v
            break

    # Fremførbart underskudd (UB 2024 = IB 2025)
    for el in tree.iter():
        if strip_ns(el.tag) == 'underskuddTilFremfoering':
            v = hent_beloep(el)
            result["underskudd_til_fremfoering"] = v if v is not None else 0
            break

    return result

def parse_naeringsspesifikasjon(tree):
    """Trekker ut balanse, midl. forskjeller, permanente forskjeller og
    egenkapitalavstemming fra naeringsspesifikasjon."""

    result = {
        "partsnummer": None,
        "inntektsaar": None,
        "kontaktperson": None,
        "balanse_ub": {},           # typekode -> beløp
        "balanse_ub_summer": {},    # navngitte summer
        "midlertidige_forskjeller": [],
        "sum_midlertidige_forskjeller_ub": 0.0,
        "sum_midlertidige_forskjeller_ib": 0.0,
        "permanente_forskjeller": [],   # NYTT: liste med {id, type, beloep}
        "egenkapitalavstemming": {      # NYTT
            "inngaaende_ek": None,      # IB 2024 (= IB 2023 UB)
            "utgaaende_ek": None,       # UB 2024 (= IB 2025)
            "sum_tillegg": None,
            "sum_fradrag": None,
            "endringer": [],            # liste med {type, beloep}
        },
    }

    # Basisfelt
    for el in tree.iter():
        tag = strip_ns(el.tag)
        if tag == 'partsreferanse' and el.text:
            result["partsnummer"] = el.text.strip()
        elif tag == 'inntektsaar' and el.text:
            result["inntektsaar"] = el.text.strip()
        elif tag == 'navn' and el.text and result["kontaktperson"] is None:
            result["kontaktperson"] = el.text.strip()

    # --- Balanse: summer ---
    for el in tree.iter():
        tag = strip_ns(el.tag)
        if tag == 'sumBalanseverdiForOmloepsmiddel':
            result["balanse_ub_summer"]["sum_omloepsmidler"] = hent_beloep(el)
        elif tag == 'sumBalanseverdiForAnleggsmiddel':
            result["balanse_ub_summer"]["sum_anleggsmidler"] = hent_beloep(el)
        elif tag == 'sumBalanseverdiForEiendel':
            result["balanse_ub_summer"]["sum_eiendeler"] = hent_beloep(el)
        elif tag == 'sumKortsiktigGjeld':
            result["balanse_ub_summer"]["sum_kortsiktig_gjeld"] = hent_beloep(el)
        elif tag == 'sumLangsiktigGjeld':
            result["balanse_ub_summer"]["sum_langsiktig_gjeld"] = hent_beloep(el)
        elif tag == 'sumGjeld':
            result["balanse_ub_summer"]["sum_gjeld"] = hent_beloep(el)
        elif tag == 'sumEgenkapital':
            result["balanse_ub_summer"]["sum_egenkapital"] = hent_beloep(el)
        elif tag == 'sumGjeldOgEgenkapital':
            result["balanse_ub_summer"]["sum_gjeld_og_egenkapital"] = hent_beloep(el)

    # Individuelle balanseverdier (eiendeler)
    for el in tree.iter():
        if strip_ns(el.tag) == 'balanseverdi':
            id_el = None
            beloep_el = None
            for child in el:
                ctag = strip_ns(child.tag)
                if ctag == 'id':
                    id_el = child.text.strip() if child.text else None
                elif ctag == 'beloep':
                    beloep_el = child
            if id_el and beloep_el is not None:
                v = hent_beloep(beloep_el)
                if v is not None:
                    result["balanse_ub"][id_el] = v

    # Individuelle gjeld/egenkapital-poster
    for el in tree.iter():
        tag = strip_ns(el.tag)
        if tag in ('gjeld', 'kapital'):
            id_el = None
            beloep_el = None
            for child in el:
                ctag = strip_ns(child.tag)
                if ctag == 'id':
                    id_el = child.text.strip() if child.text else None
                elif ctag == 'beloep':
                    beloep_el = child
            if id_el and beloep_el is not None:
                v = hent_beloep(beloep_el)
                if v is not None:
                    result["balanse_ub"][id_el] = v

    # --- Midlertidige forskjeller ---
    # BUGFIX v3: korrekt tag-navn er 'ForrigeInntektsaar' (dobbel 'r')
    sum_forskj_ub = 0.0
    sum_forskj_ib = 0.0
    for el in tree.iter():
        if strip_ns(el.tag) == 'midlertidigForskjell':
            forskj = {
                "id": None, "type": None,
                "regn_ub": None, "skatt_ub": None,
                "regn_ib": None, "skatt_ib": None,
                "forskjell_ub": None, "forskjell_ib": None
            }
            for child in el:
                ctag = strip_ns(child.tag)
                if ctag == 'id':
                    forskj["id"] = child.text
                elif ctag == 'midlertidigForskjellstype':
                    for sub in child:
                        if strip_ns(sub.tag) == 'midlertidigForskjellstype':
                            forskj["type"] = sub.text
                elif ctag == 'regnskapsmessigVerdi':
                    forskj["regn_ub"] = hent_beloep(child)
                elif ctag == 'skattemessigVerdi':
                    forskj["skatt_ub"] = hent_beloep(child)
                elif ctag == 'regnskapsmessigVerdiForrigeInntektsaar':   # FIKSET: dobbel 'r'
                    forskj["regn_ib"] = hent_beloep(child)
                elif ctag == 'skattemessigVerdiForrigeInntektsaar':      # FIKSET: dobbel 'r'
                    forskj["skatt_ib"] = hent_beloep(child)

            if forskj["regn_ub"] is not None and forskj["skatt_ub"] is not None:
                forskj["forskjell_ub"] = round(forskj["regn_ub"] - forskj["skatt_ub"], 2)
                sum_forskj_ub += forskj["forskjell_ub"]
            if forskj["regn_ib"] is not None and forskj["skatt_ib"] is not None:
                forskj["forskjell_ib"] = round(forskj["regn_ib"] - forskj["skatt_ib"], 2)
                sum_forskj_ib += forskj["forskjell_ib"]

            result["midlertidige_forskjeller"].append(forskj)

    result["sum_midlertidige_forskjeller_ub"] = round(sum_forskj_ub, 2)
    result["sum_midlertidige_forskjeller_ib"] = round(sum_forskj_ib, 2)

    # --- Permanente forskjeller (NYTT) ---
    for el in tree.iter():
        if strip_ns(el.tag) == 'permanentForskjell':
            pf = {"id": None, "type": None, "beloep": None}
            for child in el:
                ctag = strip_ns(child.tag)
                if ctag == 'id':
                    pf["id"] = child.text
                elif ctag == 'permanentForskjellstype':
                    for sub in child:
                        if strip_ns(sub.tag) == 'permanentForskjellstype':
                            pf["type"] = sub.text
                elif ctag == 'beloep':
                    pf["beloep"] = hent_beloep(child)
            result["permanente_forskjeller"].append(pf)

    # --- Egenkapitalavstemming (NYTT) ---
    for el in tree.iter():
        if strip_ns(el.tag) == 'egenkapitalavstemming':
            ek = result["egenkapitalavstemming"]
            for child in el:
                ctag = strip_ns(child.tag)
                if ctag == 'inngaaendeEgenkapital':
                    ek["inngaaende_ek"] = hent_beloep(child)
                elif ctag == 'utgaaendeEgenkapital':
                    ek["utgaaende_ek"] = hent_beloep(child)
                elif ctag == 'sumTilleggIEgenkapital':
                    ek["sum_tillegg"] = hent_beloep(child)
                elif ctag == 'sumFradragIEgenkapital':
                    ek["sum_fradrag"] = hent_beloep(child)
                elif ctag == 'egenkapitalendring':
                    endring = {"type": None, "beloep": None}
                    for sub in child:
                        sctag = strip_ns(sub.tag)
                        if sctag == 'egenkapitalendringstype':
                            for subsub in sub:
                                if strip_ns(subsub.tag) == 'egenkapitalendringstype':
                                    endring["type"] = subsub.text
                        elif sctag == 'beloep':
                            endring["beloep"] = hent_beloep(sub)
                    if endring["type"]:
                        ek["endringer"].append(endring)
            break  # bare én egenkapitalavstemming

    return result

def beregn_skatt(skattepliktig_inntekt, mid_forskj_ub, mid_forskj_ib,
                 underskudd_ib=0, skattesats=0.22):
    """Beregner betalbar skatt og utsatt skatt."""
    # Betalbar skatt
    grunnlag = skattepliktig_inntekt - underskudd_ib
    if grunnlag > 0:
        betalbar_skatt = round(grunnlag * skattesats)
        underskudd_ub = 0
    else:
        betalbar_skatt = 0
        underskudd_ub = -grunnlag

    # Utsatt skatt / skattefordel
    utsatt_skatt_ub = round(mid_forskj_ub * skattesats) if mid_forskj_ub > 0 else 0
    utsatt_skattefordel_ub = round(-mid_forskj_ub * skattesats) if mid_forskj_ub < 0 else 0

    utsatt_skatt_ib = round(mid_forskj_ib * skattesats) if mid_forskj_ib > 0 else 0
    utsatt_skattefordel_ib = round(-mid_forskj_ib * skattesats) if mid_forskj_ib < 0 else 0

    endring_utsatt_skatt = (utsatt_skatt_ub - utsatt_skattefordel_ub) - \
                           (utsatt_skatt_ib - utsatt_skattefordel_ib)

    return {
        "betalbar_skatt": betalbar_skatt,
        "underskudd_ub": underskudd_ub,
        "utsatt_skatt_ub": utsatt_skatt_ub,
        "utsatt_skattefordel_ub": utsatt_skattefordel_ub,
        "utsatt_skatt_ib": utsatt_skatt_ib,
        "utsatt_skattefordel_ib": utsatt_skattefordel_ib,
        "endring_utsatt_skatt": endring_utsatt_skatt,
        "total_skattekostnad": betalbar_skatt + endring_utsatt_skatt,
    }

def bygg_rapport_data(xml_path):
    """Hovedfunksjon – returnerer dict klar for IB/UB-kontroll og skatteberegning."""
    docs, inntektsaar = parse_wrapper(xml_path)

    skatt_data = {}
    naering_data = {}

    if 'skattemeldingUpersonlig' in docs:
        skatt_data = parse_skattemelding(docs['skattemeldingUpersonlig'])
    if 'naeringsspesifikasjon' in docs:
        naering_data = parse_naeringsspesifikasjon(docs['naeringsspesifikasjon'])

    # Slå sammen partsnummer / inntektsår
    partsnummer = skatt_data.get("partsnummer") or naering_data.get("partsnummer")
    aar = skatt_data.get("inntektsaar") or inntektsaar

    skattepliktig = skatt_data.get("skattepliktig_inntekt") or 0
    underskudd_ib = skatt_data.get("underskudd_til_fremfoering") or 0
    mid_ub = naering_data.get("sum_midlertidige_forskjeller_ub") or 0
    mid_ib = naering_data.get("sum_midlertidige_forskjeller_ib") or 0

    beregnet_skatt = beregn_skatt(skattepliktig, mid_ub, mid_ib, underskudd_ib)

    # Bygg lesbar balanseliste
    balanse_linjer = []
    for kode, beloep in sorted(naering_data.get("balanse_ub", {}).items()):
        navn = KONTO_NAVN.get(kode, f"Konto {kode}")
        balanse_linjer.append({"kode": kode, "navn": navn, "ub": beloep})

    # Legg til summer
    for noekkelnavn, label in [
        ("sum_omloepsmidler",       "Sum omløpsmidler"),
        ("sum_anleggsmidler",       "Sum anleggsmidler"),
        ("sum_eiendeler",           "Sum eiendeler"),
        ("sum_egenkapital",         "Sum egenkapital"),
        ("sum_kortsiktig_gjeld",    "Sum kortsiktig gjeld"),
        ("sum_langsiktig_gjeld",    "Sum langsiktig gjeld"),
        ("sum_gjeld",               "Sum gjeld"),
        ("sum_gjeld_og_egenkapital","Sum gjeld og egenkapital"),
    ]:
        v = naering_data.get("balanse_ub_summer", {}).get(noekkelnavn)
        if v is not None:
            balanse_linjer.append({"kode": noekkelnavn, "navn": label, "ub": v, "er_sum": True})

    # Egenkapitalavstemming UB verdier for IB-kontroll
    ek_avstemming = naering_data.get("egenkapitalavstemming", {})

    return {
        "partsnummer": partsnummer,
        "inntektsaar": aar,
        "kontaktperson": naering_data.get("kontaktperson"),
        "balanse_ub": naering_data.get("balanse_ub", {}),
        "balanse_summer_ub": naering_data.get("balanse_ub_summer", {}),
        "balanse_linjer": balanse_linjer,

        # Midlertidige forskjeller
        "midlertidige_forskjeller": naering_data.get("midlertidige_forskjeller", []),
        "sum_midlertidige_forskjeller_ub": mid_ub,   # UB 2024 = IB 2025
        "sum_midlertidige_forskjeller_ib": mid_ib,   # IB 2024

        # Permanente forskjeller (NYTT) – listert per post, ingen IB/UB å sammenligne
        "permanente_forskjeller_2024": naering_data.get("permanente_forskjeller", []),

        # Egenkapitalavstemming (NYTT)
        "egenkapitalavstemming_ub": {
            "inngaaende_ek": ek_avstemming.get("inngaaende_ek"),   # IB 2024 (til info)
            "utgaaende_ek": ek_avstemming.get("utgaaende_ek"),      # UB 2024 = IB 2025
            "sum_tillegg": ek_avstemming.get("sum_tillegg"),
            "sum_fradrag": ek_avstemming.get("sum_fradrag"),
            "endringer": ek_avstemming.get("endringer", []),
        },

        # Fremførbart underskudd (NYTT eksplisitt felt)
        "underskudd_til_fremfoering_ub": underskudd_ib,  # UB 2024 = IB 2025

        # Skatteberegning
        "skattepliktig_inntekt": skattepliktig,
        "underskudd_ib": underskudd_ib,
        "beregnet_skatt": beregnet_skatt,
    }

def bygg_rapport_data_direkte(skattemelding_xml, naeringsspesifikasjon_xml):
    """Parser to separate XML-filer (direkte format, ikke wrapper).
    Brukes for 2025-utkast fra Maestro ZIP-eksport.
    Returnerer samme format som bygg_rapport_data().
    """
    skatt_tree   = ET.parse(skattemelding_xml).getroot()
    naering_tree = ET.parse(naeringsspesifikasjon_xml).getroot()

    # Hent inntektsår
    for el in skatt_tree.iter():
        if strip_ns(el.tag) == 'inntektsaar':
            inntektsaar = el.text.strip()
            break
    else:
        inntektsaar = "ukjent"

    skatt_data   = parse_skattemelding(skatt_tree)
    naering_data = parse_naeringsspesifikasjon(naering_tree)

    partsnummer = skatt_data.get("partsnummer") or naering_data.get("partsnummer")
    aar = skatt_data.get("inntektsaar") or inntektsaar

    skattepliktig = skatt_data.get("skattepliktig_inntekt") or 0
    underskudd_ib = skatt_data.get("underskudd_til_fremfoering") or 0
    mid_ub = naering_data.get("sum_midlertidige_forskjeller_ub") or 0
    mid_ib = naering_data.get("sum_midlertidige_forskjeller_ib") or 0

    beregnet_skatt = beregn_skatt(skattepliktig, mid_ub, mid_ib, underskudd_ib)

    balanse_linjer = []
    for kode, beloep in sorted(naering_data.get("balanse_ub", {}).items()):
        navn = KONTO_NAVN.get(kode, f"Konto {kode}")
        balanse_linjer.append({"kode": kode, "navn": navn, "ub": beloep})
    for noekkelnavn, label in [
        ("sum_omloepsmidler", "Sum omløpsmidler"),
        ("sum_anleggsmidler", "Sum anleggsmidler"),
        ("sum_eiendeler", "Sum eiendeler"),
        ("sum_egenkapital", "Sum egenkapital"),
        ("sum_kortsiktig_gjeld", "Sum kortsiktig gjeld"),
        ("sum_langsiktig_gjeld", "Sum langsiktig gjeld"),
        ("sum_gjeld", "Sum gjeld"),
        ("sum_gjeld_og_egenkapital", "Sum gjeld og egenkapital"),
    ]:
        v = naering_data.get("balanse_ub_summer", {}).get(noekkelnavn)
        if v is not None:
            balanse_linjer.append({"kode": noekkelnavn, "navn": label, "ub": v, "er_sum": True})

    ek_avstemming = naering_data.get("egenkapitalavstemming", {})

    return {
        "partsnummer": partsnummer,
        "inntektsaar": aar,
        "kontaktperson": naering_data.get("kontaktperson"),
        "balanse_ub": naering_data.get("balanse_ub", {}),
        "balanse_summer_ub": naering_data.get("balanse_ub_summer", {}),
        "balanse_linjer": balanse_linjer,
        "midlertidige_forskjeller": naering_data.get("midlertidige_forskjeller", []),
        "sum_midlertidige_forskjeller_ub": mid_ub,
        "sum_midlertidige_forskjeller_ib": mid_ib,
        "permanente_forskjeller_2024": naering_data.get("permanente_forskjeller", []),
        "egenkapitalavstemming_ub": {
            "inngaaende_ek": ek_avstemming.get("inngaaende_ek"),
            "utgaaende_ek": ek_avstemming.get("utgaaende_ek"),
            "sum_tillegg": ek_avstemming.get("sum_tillegg"),
            "sum_fradrag": ek_avstemming.get("sum_fradrag"),
            "endringer": ek_avstemming.get("endringer", []),
        },
        "underskudd_til_fremfoering_ub": underskudd_ib,
        "skattepliktig_inntekt": skattepliktig,
        "underskudd_ib": underskudd_ib,
        "beregnet_skatt": beregnet_skatt,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Bruk: python parse_xml.py <sti/til/skattemelding.xml>", file=sys.stderr)
        print("  eller: python parse_xml.py <Skattemelding.xml> <Naeringsspesifikasjon.xml>  (direkte format)", file=sys.stderr)
        sys.exit(1)
    if len(sys.argv) == 3:
        # Direkte format: to separate XML-filer
        data = bygg_rapport_data_direkte(sys.argv[1], sys.argv[2])
    else:
        # Wrapper-format: én fil med base64-kodet innhold
        data = bygg_rapport_data(sys.argv[1])
    print(json.dumps(data, ensure_ascii=False, indent=2))
