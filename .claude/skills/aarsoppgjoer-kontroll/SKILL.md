---
name: "aarsoppgjoer-kontroll"
description: "Kvalitetssikring av årsoppgjør for norske AS: årsregnskapskontroll (noter, notehenvisninger, matematikk, Brreg-rollesjekk) og skattemeldingskontroll (IB/UB, midlertidige forskjeller, egenkapital, fremført underskudd, permanente forskjeller, skatteberegning) parallelt, med krysskontroll og Silfer-PDF. Bruk ved «sjekk årsregnskapet», «kontroller årsoppgjøret», «kvalitetssikre regnskap», «sjekk skattemeldingen», «IB-kontroll», «betalbar skatt», «notekobling», eller opplasting av PDF-årsregnskap, XML-skattemelding eller XLSX fra Maestro, Skatteetaten eller kontoplan. Bare AS (22 %)."
---

# Årsoppgjør-kontroll – samlet kvalitetssikring (v3)

## Oversikt

Dette skillen slår sammen tre kontroller i én arbeidsflyt:

1. **Årsregnskapskontroll**: noter, notehenvisninger, noterekkefølge, matematikk, brreg-rollesjekk
2. **Skattemeldingskontroll**: IB/UB-balanse, midlertidige forskjeller, egenkapitalavstemming,
   fremf. underskudd, permanente forskjeller, skatteberegning
3. **Kontoplansjekk** (kun når kontoplan er lastet opp): utsatt skattekonflikt,
   ikke-fradragsberettigede kostnader vs. skattemeldingen
4. **Krysskontroll** (kun når både årsregnskap og skattemelding foreligger): skattekostnad,
   sum egenkapital og avskrivninger krysssjekkes mellom de to dokumentene

Når alle filtyper er lastet opp, kjøres alle kontroller **parallelt** – total tid ca. 20–35 sek.

---

## Steg 0 – Identifiser hvilke dokumenter som er lastet opp

| Filtype | Rolle |
|---------|-------|
| `.pdf` (årsregnskap med noter/balanse/resultat) | Årsregnskapskontroll |
| `.xml` (skattemelding fra Altinn/Skatteetaten 2024) | Skattemeldingskontroll – UB 2024 |
| `.xlsx` – **Maestro Publisering** (`Tema\|ID\|Gruppe\|Beskrivelse\|I år\|I fjor`) | IB 2025 kilde A |
| `.xlsx` – **Skatteetaten** (3 ark: Oppsummering / Skattemelding / Næringsspesifikasjon) | IB 2025 kilde B |
| `.xlsx` – **Kontoplan** (`Kontonr\|Kontobetegnelse\|...\|Saldo 2024\|...\|MidForsRef\|PermanentRef`) | IB 2025 kilde C + kvalitetskontroll |
| `.zip` (fra Maestro – inneholder XML og/eller XLSX) | Pakk ut – behandle innhold |

**Gjenkjenn XLSX-format:**
- Maestro: ark med kolonner `Tema, ID, Gruppe, Beskrivelse, I år, I fjor`
- Skatteetaten: 3 arknavn «Oppsummering», «Skattemelding», «Næringsspesifikasjon»
- Kontoplan: kolonne `Kontonr` i rad 4 (eller lignende) + kolonne `MidForsRef`

**Sett flag:**
- `HAR_AARSREGNSKAP = True` hvis PDF med noter/balanse/resultat er lastet opp
- `HAR_SKATTEMELDING = True` hvis XML (2024) er lastet opp
- `HAR_IB_2025 = True` hvis XLSX (Maestro eller Skatteetaten) er lastet opp
- `HAR_KONTOPLAN = True` hvis kontoplan-XLSX er lastet opp

> **Merk:** Kontoplan kan brukes som IB 2025-kilde (via `MidForsRef`-summering) og/eller som
> selvstendig kvalitetskontroll. Den er alltid nyttig hvis den er tilgjengelig.

---

## Scenario A – Kun årsregnskap (PDF)
Gå til **Del I** nedenfor (Steg 1 → 1.5 → 2 → 3).

## Scenario B – Kun skattemelding (XML + XLSX/kontoplan)
Gå til **Del II** nedenfor (Steg 1 → 2A/2B/2C → 3 → 4).
Kjør også **Del II – Steg 2D** (kontoplansjekk) hvis `HAR_KONTOPLAN = True`.

## Scenario C – Begge → Parallell kjøring ⚡
**I én og samme melding**, spawn:
- Del I Steg 2: 3 haiku-agenter for årsregnskapet
- Del II Steg 1: kjør Python-parsing av XML som Bash-kommando
- Del II Steg 2A/2B/2C: kjør Python-parsing av XLSX som Bash-kommando
- Del II Steg 2D: kjør kontoplanparser hvis kontoplan er lastet opp

Deretter (når alt er ferdig): krysskontroll (Del III) + generer begge PDF-rapporter.

---

# Del I – Årsregnskapskontroll

## Del I – Steg 1: Les PDF

Bruk `Read`-verktøyet for å lese PDF-filen. Legg innholdet i konteksten.

## Del I – Steg 1.5: Brreg-rollesjekk

Fanger opp at feil person er oppført som styreleder eller daglig leder – vanlig ved kopiering
fra maler eller ved endringer i roller i løpet av året.

1. **Finn org.nr** fra PDF-en (typisk forsiden eller bunntekst). Fjern mellomrom.
2. **Kall brreg-APIet:**
```bash
curl -s -H "Accept: application/json" \
  "https://data.brreg.no/enhetsregisteret/api/enheter/[ORGNR_UTEN_MELLOMROM]/roller"
```
3. **Ekstraher aktive roller** (ignorer der `fratraadt` eller `avregistrert` er `true`):
   - `DAGL` = Daglig leder
   - `LEDE` = Styrets leder
   - `MEDL` = Styremedlem
   - `NEST` = Nestleder
4. **Finn signatur** i årsregnskapet (typisk nederst på balansesiden).
5. **Sammenlign** – bygg `rollesjekk`-liste:
   - `"OK"` hvis samsvar, `"FEIL"` hvis avvik → legg til i `maa_rettes`
   - `"MERKNAD"` med tekst «Kunne ikke hente data fra Brønnøysundregistrene» ved feil

## Del I – Steg 2: Spawn 3 haiku-subagenter UMIDDELBART i SAMME melding

Spawn alle tre med `model: "haiku"`, `subagent_type: "general-purpose"`.
Inkluder hele PDF-teksten direkte. Erstatt `[PDF_TEKST]`, `[SELSKAP]`, `[AAR]`.

---

### Subagent A – Obligatoriske noter

```
Du er en norsk regnskapskontrollør. Her er teksten fra årsregnskapet for [SELSKAP] [AAR]:

---
[PDF_TEKST]
---

Kontroller obligatoriske noter for norsk lite AS (NRS 8).

Returner KUN gyldig JSON:
{
  "funn_noter": [
    {"krav": "§ 7-35 – Regnskapsprinsipper", "status": "OK", "plassering": "Note X / avsnitt"}
  ],
  "kritiske_feil": [
    {"post": "Note X – tittel", "funn": "Hva er galt", "rettelse": "Hva må gjøres"}
  ]
}

Sjekk disse kravene:
- § 7-35: Regnskapsprinsipper til stede?
- § 7-38: Lønnskostnader spesifisert (lønn, aga, pensjon, ytelser)? Sum = lønnskostnad i RR?
  Pensjonsordningens art trenger IKKE oppgis for små foretak – ikke flagg dette.
  UNNTAK: Hvis lønnskostnader i RR er under 11 000 kr, er det tilstrekkelig med en note
  som opplyser at selskapet ikke har ansatte. Full spesifikasjon (lønn, aga, pensjon)
  er da IKKE påkrevd. Sett status "OK" hvis slik note finnes.
- § 7-39: Anleggsmiddelnote med bevegelsesanalyse for INNEVÆRENDE år?
  Er IB akkumulerte avskrivninger oppgitt?
  VIKTIG: § 7-39 gjelder kun varige driftsmidler og immaterielle eiendeler (poster som
  avskrives). Finansielle anleggsmidler (langsiktige fordringer, investeringer i aksjer,
  obligasjoner) faller IKKE inn under § 7-39. Hvis selskapet kun har finansielle
  anleggsmidler, sett status "IKKE AKTUELT".
- § 7-40: Fordringer med forfall > 1 år, gjeld med forfall > 5 år, pantesikret gjeld,
  garantier. Sjekk om selskapet har vesentlige langsiktige fordringer eller gjeld –
  hvis ja, skal det opplyses om forfallstid og betingelser. Flagg som MERKNAD hvis
  vesentlige poster mangler forklaring.
- § 7-42: Eier selskapet egne aksjer? Opplysningsplikt gjelder KUN dersom selskapet
  faktisk eier egne aksjer. Negativ bekreftelse («eier ikke egne aksjer») er IKKE
  påkrevd for små foretak. Flagg kun hvis selskapet faktisk eier egne aksjer og
  mangler note om dette.
- § 7-43: Antall ansatte (gjennomsnittlige årsverk) oppgitt?
  UNNTAK: Hvis lønnskostnader i RR er under 11 000 kr og noten opplyser at selskapet
  ikke har ansatte, er eksplisitt oppgivelse av antall årsverk IKKE påkrevd.
  Sett status "OK" eller "IKKE AKTUELT" i slike tilfeller.
- § 7-44: Revisorhonorar – IKKE SJEKK. Flagg aldri manglende revisorhonorar som innholdsmangel.
- § 7-45: Godtgjørelse til DL/styre – OPPHEVET 2021. Flagg ALDRI manglende DL-lønn, styrehonorar
  eller revisorhonorar som innholdsmangel.
  UNNTAK – notetittel: Hvis notetittelen sier f.eks. «Lønnskostnader og ytelser, godtgjørelser til
  daglig leder, styret og revisor» men noten KUN inneholder lønnskostnadstabell, skal dette flagges
  som BØR RETTES: noteoverskriften bør forenkles til kun å beskrive faktisk innhold (f.eks.
  «Lønnskostnader»). Dette er et presisjonsspørsmål for notetittelen, ikke et krav om mer innhold.
- NRS 8 (2025): Note om virksomhetens art og lokalisering?

Gyldige statuser: "OK", "FEIL", "MANGLER", "MERKNAD", "IKKE AKTUELT"
```

---

### Subagent B – Notehenvisninger og rekkefølge

```
Du er en norsk regnskapskontrollør. Her er teksten fra årsregnskapet for [SELSKAP] [AAR]:

---
[PDF_TEKST]
---

Kontroller notehenvisninger og noterekkefølge.

Returner KUN gyldig JSON:
{
  "funn_koblinger": [
    {"oppstilling": "Resultatregnskap", "post": "Lønnskostnad", "note": "Note 1", "status": "OK"}
  ],
  "funn_rekkefolge": [
    {"note": "Note 1 – Lønnskostnader", "tilhorende": "Lønnskostnad (resultat)", "status": "OK"}
  ],
  "kritiske_feil": [
    {"post": "...", "funn": "...", "rettelse": "..."}
  ]
}

Regler for notekobling:
HOVEDREGEL: Enhver post i resultatregnskapet eller balansen som gjenfinnes
  (brukes/spesifiseres) i en note, SKAL ha notehenvisning til den noten.
  Gå gjennom hver note og sjekk: finnes det en post i RR eller balansen som
  inneholder tallet som noten utdyper? Hvis ja → posten skal ha notereferanse.
  Eksempler:
  - Lønnskostnad → lønnskostnadsnoten
  - Skattekostnad → skattenoten
  - Årsresultat / udekket tap → egenkapitalnoten
  - Aksjekapital → aksjonærnoten
  - Betalbar skatt → skattenoten
  - Bankinnskudd → note om bundne midler
  - Anleggsmidler → anleggsmiddelnoten
  Hvis skattekostnad-linjen mangler helt i RR (selv ved kr 0), flagg dette:
  linjen bør vises med notehenvisning til skattenoten.
EGENKAPITALLINJER SPESIELT: Alle EK-linjer i balansen som gjenfinnes i
  egenkapitalnoten skal ha notehenvisning til EK-noten. Dette gjelder bl.a.:
  - Aksjekapital → aksjonærnoten (eller EK-noten hvis den viser aksjekapital)
  - Overkursfond → EK-noten
  - Annen innskutt egenkapital → EK-noten
  - Annen egenkapital / udekket tap → EK-noten
  Bare «Sum egenkapital»-linjen er unntatt (sum-linje).
  Sjekk HVER enkelt EK-linje — dette er en vanlig mangel.
DISPONERINGER I RESULTATREGNSKAPET: Alle disponeringslinjer nederst i RR
  (f.eks. «Overført til/fra annen egenkapital», «Avsatt til utbytte»,
  «Overført til/fra overkursfond», «Overført til/fra annen innskutt EK»)
  gjenfinnes i EK-noten og skal ha notehenvisning til EK-noten.
  Sjekk HVER enkelt disponeringslinje — dette er en vanlig mangel.
TRENGER IKKE notekobling: sum-linjer, leverandørgjeld, skyldig off. avgifter,
  andre kortsiktige fordringer, annen kortsiktig gjeld
SPESIALREGEL: Annen driftskostnad kan ha notekobling til lønnskostnadsnoten dersom
  noten også inneholder poster som reisekostnader, bilgodtgjørelse e.l. Dette er KORREKT.

TOMME UNDEROVERSKRIFTER: Sjekk om balansen inneholder underoverskrifter
  (f.eks. «Immaterielle eiendeler», «Varige driftsmidler», «Finansielle
  anleggsmidler», «Fordringer», «Investeringer») som IKKE har noen poster
  med beløp under seg. Hvis en underoverskrift vises uten tilhørende poster,
  flagg som MERKNAD i kritiske_feil med anbefaling om å skjule tomme grupper
  i regnskapssystemet. Dette er et presentasjonsproblem, ikke regnskapsfaglig feil.

Regler for rekkefølge (§ 7-1a):
- Plasseringen bestemmes av FØRSTE forekomst av notehenvisningen i oppstillingene
- Resultatnoter (første referanse i resultat) kommer før rene balansenoter
- Innen resultat: noter i samme rekkefølge som postene i resultatregnskapet
- Innen balanse: noter i samme rekkefølge som postene i balansen
- VIKTIG UNNTAK: Dersom egenkapitalnoten er referert fra resultatregnskapet
  (f.eks. årsresultat), er det KORREKT at den har lavere nummer enn aksjonærnoten.
- Sjekk for duplikate notenumre

Gyldige statuser: "OK", "FEIL", "MANGLER", "MERKNAD"
```

---

### Subagent C – Matematisk kontroll + nøkkeltall for krysskontroll

```
Du er en norsk regnskapskontrollør. Her er teksten fra årsregnskapet for [SELSKAP] [AAR]:

---
[PDF_TEKST]
---

Ekstraher alle nøkkeltall og gjør matematisk kontroll. Kjør beregningene i Python inline.

Kontroller:
1. Sum driftsinntekter
2. Sum driftskostnader
3. Driftsresultat = Sum driftsinntekter − Sum driftskostnader
4. Resultat av finansposter = Finansinntekter − Finanskostnader
5. Resultat før skattekostnad = Driftsresultat + Resultat av finansposter
6. Årsresultat = Resultat før skatt − Skattekostnad
7. Sum eiendeler = Sum anleggsmidler + Sum omløpsmidler
8. Sum egenkapital og gjeld = Sum egenkapital + Sum gjeld
9. Balansen går opp: Sum eiendeler = Sum egenkapital og gjeld
10. Notesum lønnskostnader vs. lønnskostnad i resultatregnskapet
11. Note skattekostnad (betalbar + endring utsatt) vs. resultatregnskap
12. Egenkapitalnote sluttsaldo vs. balanse sum egenkapital
13. Avskrivninger i anleggsmiddelnote vs. resultatregnskap (hvis begge steder)

Returner KUN gyldig JSON:
{
  "matematikk": [
    {"kontroll": "Sum driftsinntekter", "beregning": "A + B = C", "resultat": "C", "status": "OK"}
  ],
  "merknad": "Eventuelle avrundingsbemerkninger",
  "nokkel": {
    "skattekostnad": null,
    "sum_egenkapital": null,
    "avskrivninger": null,
    "resultat_for_skatt": null
  }
}

Status-regler:
- "OK" hvis beregnet = oppgitt, ELLER differansen er ≤ 1 krone (avrunding er akseptabelt)
- "FEIL" hvis differansen er > 1 krone

For "nokkel"-feltet, hent fra regnskapet (null hvis ikke funnet):
- skattekostnad: total skattekostnad (betalbar + endring utsatt) fra resultatregnskapet
- sum_egenkapital: sum egenkapital fra balansen (UB)
- avskrivninger: avskrivninger fra resultatregnskapet
- resultat_for_skatt: resultat før skattekostnad fra resultatregnskapet
```

---

## Del I – Steg 3: Samle funn og generer årsregnskapsrapport

Kombiner til `<scratch>/rapport_aarsregnskap.json`:

```json
{
  "selskap": "Selskapsnavn AS",
  "orgnr": "xxx xxx xxx",
  "aar": "2024",
  "dato": "DD.MM.ÅÅÅÅ",
  "maa_rettes": [],
  "obligatoriske": [],
  "notehenvisninger": [],
  "noterekkefølge": [],
  "matematikk": [],
  "matematikk_merknad": "",
  "rollesjekk": [
    {"rolle": "Styreleder", "brreg": "Ola Nordmann", "regnskap": "Ola Nordmann", "status": "OK"}
  ],
  "nokkel": {
    "skattekostnad": null,
    "sum_egenkapital": null,
    "avskrivninger": null
  }
}
```

- `maa_rettes` = `kritiske_feil` fra A + B + rollesjekk-avvik (deduplisert)
- `rollesjekk` = resultater fra Steg 1.5

Generer PDF (SKILL_BASE_DIR = mappen der dette SKILL.md-filen ligger):

```bash
uv run --with reportlab python <SKILL_BASE_DIR>/scripts/generer_rapport_aarsregnskap.py \
    <scratch>/Gjennomgang_[Selskap]_[aar].pdf \
    <scratch>/rapport_aarsregnskap.json
```

---

# Del II – Skattemeldingskontroll

## Del II – Steg 1: Parse XML (Python, ~1 sek)

```bash
uv run --with openpyxl python <SKILL_BASE_DIR>/scripts/parse_xml.py "<sti/til/2024_skattemelding.xml>" > <scratch>/xml_data.json
```

Scriptet håndterer automatisk:
- **Wrapper-format** (base64-innpakkede underdokumenter fra Altinn/Maestro)
- **Direkte format** (separate Skattemelding.xml + Naeringsspesifikasjon.xml fra ZIP):

```bash
uv run --with openpyxl python <SKILL_BASE_DIR>/scripts/parse_xml.py "<Skattemelding.xml>" --naering "<Naeringsspesifikasjon.xml>" > <scratch>/xml_data.json
```

## Del II – Steg 2A: Parse Maestro XLSX (kun Maestro-format)

Gjenkjenn: arket inneholder kolonnene `Tema, ID, Gruppe, Beskrivelse, I år, I fjor`.

```bash
uv run --with openpyxl python <SKILL_BASE_DIR>/scripts/parse_maestro_xlsx.py "<sti/til/maestro_2025.xlsx>" > <scratch>/pdf_data.json
```

«I fjor»-kolonnen = UB 2024 = IB 2025.

## Del II – Steg 2B: Parse Skatteetaten XLSX (3-arks format)

Gjenkjenn: tre arknavn «Oppsummering», «Skattemelding», «Næringsspesifikasjon».

```bash
uv run --with openpyxl python <SKILL_BASE_DIR>/scripts/parse_skatteetaten_xlsx.py "<sti/til/skattemelding_2025.xlsx>" > <scratch>/pdf_data.json
```

Returnerer midlertidige forskjeller IB per 3-sifret typekode (101, 140, 141 osv.) fra
«RM i fjor»-kolonnen i Næringsspesifikasjon-arket. Individuelle balansekontoer er ikke
tilgjengelig – balanse-IB-kontrollen vil da kjøre på typekode-nivå.

## Del II – Steg 2C: Les PDF med haiku-agent (kun hvis ingen XLSX)

Spawn én haiku-agent (`model: "haiku"`) med hele PDF-teksten og kontoerliste fra XML-data.

```
Du er norsk regnskapsfører. Her er teksten fra utkast til skattemelding/næringsoppgave 2025:

---
[PDF_TEKST]
---

Jeg trenger IB (inngående balanse) for 2025 for følgende poster:
[LISTE_FRA_XML]

I tillegg, hent:
- Skattepliktig inntekt 2025
- Sum midlertidige forskjeller UB 2025 (netto sum)
- Per midlertidig forskjell IB 2025: {id/type → IB-verdi}
- Betalbar skatt 2025, endring utsatt skatt 2025, total skattekostnad 2025
- Permanente forskjeller 2025: {id/type → beløp}
- Inngående egenkapital 2025 fra egenkapitalavstemmingen
- Fremførbart underskudd IB 2025

Returner KUN gyldig JSON:
{
  "selskap": "...", "partsnummer": "...",
  "ib_2025": {"1500": 0.0, ...},
  "midl_forskjeller_ib": {}, "sum_midl_forskjeller_ib": 0.0,
  "perm_forskjeller": {}, "ib_egenkapital": 0.0,
  "underskudd_fremfoering_ib": 0.0,
  "skatt_2025": {
    "skattepliktig_inntekt": null, "mid_forskjeller_ub": null,
    "oppgitt_betalbar_skatt": null, "oppgitt_endring_utsatt_skatt": null,
    "oppgitt_total_skattekostnad": null
  },
  "merknad": ""
}
```

## Del II – Steg 2D: Kontoplansjekk (kjøres alltid når HAR_KONTOPLAN = True)

```bash
uv run --with openpyxl python <SKILL_BASE_DIR>/scripts/parse_kontoplan.py "<sti/til/kontoplan.xlsx>" > <scratch>/kontoplan_data.json
```

Kontoplanparser kjører to kvalitetskontroller og returnerer IB 2025 per MidForsRef-typekode:

**Kontroll 1 – Utsatt skattekonflikt:** Sjekker at kto 1070 (utsatt skattefordel) og
kto 2120/2121 (utsatt skatteforpliktelse) IKKE begge er beløpssatt. Nettostørrelse
skal kun stå på én side.

**Kontroll 2 – Ikke-fradragsberettigede kostnader:** Finner alle kontoer der
`PermanentRef` er utfylt og `Saldo 2024` ≠ 0. Disse representerer kostnader som
ikke gir skattemessig fradrag og skal legges til som permanente forskjeller i
skattemeldingen. Sjekker at summen er reflektert.

**Vis resultater umiddelbart i chat** (ikke vent på PDF):

```python
import json
kp = json.loads(open('<scratch>/kontoplan_data.json').read())
qc = kp.get('quality_checks', {})

utsatt = qc.get('utsatt_skatt_konflikt', {})
ikon = "✅" if utsatt.get('ok') else "❌"
print(f"\n{ikon} Utsatt skattekonflikt: {utsatt.get('melding', '')}")

iff = qc.get('ikke_fradragsberettiget', {})
ikon = "✅" if iff.get('ok') else "❌"
print(f"\n{ikon} Ikke-fradragsberettiget: {iff.get('melding', '')}")
if not iff.get('ok'):
    for kto in iff.get('kontoer', []):
        print(f"   • Kto {kto['kontonr']} {kto['navn']}: {kto['saldo_2024']:,.2f} kr")
```

Når IB-kilde er Skatteetaten XLSX (midl. forskjeller som 3-sifret typekode), bruk
`ib_2025_midl` fra kontoplan som sikrere IB-kilde og sammenlign:

```python
xml_data = json.loads(open('<scratch>/xml_data.json').read())
kp_midl = kp.get('ib_2025_midl', {})

print("\n── IB-kontroll midlertidige forskjeller (kontoplan vs. XML UB) ──")
for mf in xml_data.get('midlertidige_forskjeller', []):
    type_id = mf['id']
    kode = type_id.replace('type', '').lstrip('0') if 'type' in type_id else type_id
    ub_xml = mf.get('forskjell_ub')
    ib_kp  = kp_midl.get(kode)
    if ub_xml is not None and ib_kp is not None:
        diff = round(float(ib_kp) - float(ub_xml), 2)
        ok = abs(diff) <= 10.0  # ±10 kr toleranse for avrunding/MVA
        ikon = "✅" if ok else "❌"
        print(f"  {ikon} Typekode {kode}: UB(XML)={ub_xml:,.2f} | IB(Kontoplan)={ib_kp:,.2f} | diff={diff:+,.2f}")
```

## Del II – Steg 3: Sammenlign og beregn (Python inline)

```python
import json, datetime, sys
sys.path.insert(0, '<SKILL_BASE_DIR>/scripts')
from parse_xml import beregn_skatt, KONTO_NAVN

xml_data = json.loads(open('<scratch>/xml_data.json').read())
pdf_data = json.loads(open('<scratch>/pdf_data.json').read())

# Hvis kontoplan er tilgjengelig og pdf_data mangler ib_2025 (Skatteetaten XLSX format),
# bruk kontoplan-IB for midlertidige forskjeller
try:
    kp_data  = json.loads(open('<scratch>/kontoplan_data.json').read())
    kp_midl  = kp_data.get('ib_2025_midl', {})
except FileNotFoundError:
    kp_midl = {}

TOLER = 1.0

def diff_ok(ub, ib):
    if ib is None: return None, False
    d = round(float(ib) - float(ub), 2)
    return d, abs(d) <= TOLER

# Del 1: Balanse IB/UB
# Inkluder kun poster der IB er funnet – poster uten IB-match kan ikke kontrolleres
ib_kontroll = []
pdf_ib = pdf_data.get("ib_2025", {})
for linje in xml_data["balanse_linjer"]:
    kode = linje["kode"]
    ib_val = pdf_ib.get(kode)
    if ib_val is None:
        continue  # Hopp over poster uten IB-match (sum-linjer, manglende kontoer)
    diff, ok = diff_ok(linje["ub"], ib_val)
    ib_kontroll.append({
        "kode": kode, "navn": linje["navn"],
        "ub_2024": linje["ub"], "ib_2025": ib_val,
        "diff": diff, "ok": ok, "er_sum": linje.get("er_sum", False)
    })

# Del 2: Midlertidige forskjeller
# Bruk kontoplan-IB hvis tilgjengelig (typekode → saldo), ellers pdf_data
midl_kontroll = []
pdf_midl = pdf_data.get("midl_forskjeller_ib", {})
for mf in xml_data.get("midlertidige_forskjeller", []):
    type_id = mf.get("id", "")
    # Prøv kontoplan-IB først (mer pålitelig), deretter pdf_data
    kode_kp = type_id.replace('type', '').lstrip('0') if 'type' in type_id else type_id
    ib_f = kp_midl.get(kode_kp) or kp_midl.get(type_id) or \
           pdf_midl.get(type_id) or pdf_midl.get(kode_kp)
    ub_f = mf.get("forskjell_ub")
    TOLER_MIDL = 10.0  # Typekode-summering kan ha ±10 kr avrunding/MVA
    diff, ok = (None, True) if ub_f is None else \
               ((round(float(ib_f) - float(ub_f), 2), abs(float(ib_f or 0) - float(ub_f or 0)) <= TOLER_MIDL)
                if ib_f is not None else (None, False))
    midl_kontroll.append({
        "type": mf.get("type") or type_id,
        "ub_forskjell": ub_f, "ib_forskjell": ib_f,
        "diff": diff, "ok": ok, "har_ib": ub_f is not None,
        "kilde": "kontoplan" if kp_midl.get(kode_kp) else "xlsx",
    })

sum_midl_ub_xml = xml_data.get("sum_midlertidige_forskjeller_ub", 0)
sum_midl_ib_pdf = pdf_data.get("sum_midl_forskjeller_ib")
sum_midl_diff, sum_midl_ok = diff_ok(sum_midl_ub_xml, sum_midl_ib_pdf)

# Del 3: Egenkapitalavstemming
ek_xml = xml_data.get("egenkapitalavstemming_ub", {})
ek_diff, ek_ok = diff_ok(ek_xml.get("utgaaende_ek"), pdf_data.get("ib_egenkapital"))

# Del 4: Fremførbart underskudd
und_ub = xml_data.get("underskudd_til_fremfoering_ub", 0)
und_ib = pdf_data.get("underskudd_fremfoering_ib")
und_diff, und_ok = diff_ok(und_ub, und_ib if und_ib is not None else 0)

# Del 5: Permanente forskjeller – krysskontroll mot kontoplan
# Hvis kontoplan er tilgjengelig: sjekk at ikke-fradragsberettigede summer finnes i XML
kontoplan_perm_avvik = []
try:
    kp_data = json.loads(open('<scratch>/kontoplan_data.json').read())
    iff = kp_data.get('quality_checks', {}).get('ikke_fradragsberettiget', {})
    if not iff.get('ok') and iff.get('total', 0) > 1.0:
        xml_perm_total = sum(
            abs(p.get('beloep', 0) or 0)
            for p in xml_data.get('permanente_forskjeller_2024', [])
        )
        forventet = iff['total']
        if abs(xml_perm_total - forventet) > 10.0:
            kontoplan_perm_avvik.append({
                "melding": (
                    f"Kontoplan: {forventet:,.2f} kr ikke-fradragsberettigede kostnader "
                    f"er IKKE reflektert i skattemeldingen som permanente forskjeller. "
                    f"Underskuddet er overvurdert med tilsvarende beløp."
                ),
                "kontoplan_sum": forventet,
                "xml_perm_sum": xml_perm_total,
            })
except (FileNotFoundError, KeyError):
    pass

# Del 6: Skatteberegning
skatt_2025 = pdf_data.get("skatt_2025", {})
ski = skatt_2025.get("skattepliktig_inntekt") or 0
mid_ub_2025 = skatt_2025.get("mid_forskjeller_ub") or sum_midl_ib_pdf or 0
mid_ib_2025 = xml_data["sum_midlertidige_forskjeller_ub"]
beregnet = beregn_skatt(ski, mid_ub_2025, mid_ib_2025)

def skatt_rad(post, bv, ov):
    d, ok = diff_ok(bv, ov)
    return {"post": post, "beregnet": bv, "oppgitt": ov, "diff": d, "ok": ok}

rapport = {
    "selskap": pdf_data.get("selskap", "Ukjent AS"), "aar": "2025",
    "dato": datetime.date.today().strftime("%d.%m.%Y"),
    "partsnummer_xml": xml_data.get("partsnummer", ""),
    "ib_kontroll": ib_kontroll,
    "midl_kontroll": midl_kontroll,
    "sum_midl_ub_xml": sum_midl_ub_xml, "sum_midl_ib_pdf": sum_midl_ib_pdf,
    "sum_midl_ok": sum_midl_ok,
    "ek_kontroll": {
        "utgaaende_ek_xml": ek_xml.get("utgaaende_ek"),
        "ib_ek_pdf": pdf_data.get("ib_egenkapital"), "ok": ek_ok
    },
    "ek_endringer_xml": ek_xml.get("endringer", []),
    "und_kontroll": {"ub_xml": und_ub, "ib_pdf": und_ib, "ok": und_ok},
    "permanente_forskjeller_2024": xml_data.get("permanente_forskjeller_2024", []),
    "permanente_forskjeller_2025": [
        {"id": k, "type": k, "beloep": v}
        for k, v in (pdf_data.get("perm_forskjeller") or {}).items()
    ],
    "kontoplan_perm_avvik": kontoplan_perm_avvik,
    "skatt_rader": [
        skatt_rad("Betalbar skatt", beregnet["betalbar_skatt"],
                  skatt_2025.get("oppgitt_betalbar_skatt")),
        skatt_rad("Endring utsatt skatt", beregnet["endring_utsatt_skatt"],
                  skatt_2025.get("oppgitt_endring_utsatt_skatt")),
        skatt_rad("Total skattekostnad", beregnet["total_skattekostnad"],
                  skatt_2025.get("oppgitt_total_skattekostnad")),
    ],
    "skatt_grunnlag": {
        "skattepliktig_inntekt": ski, "mid_forskjeller_ib": mid_ib_2025,
        "mid_forskjeller_ub": mid_ub_2025
    },
    "beregnet_skatt": beregnet,
    "_nokkel": {
        "skattekostnad": beregnet.get("total_skattekostnad"),
        "sum_egenkapital_ub": ek_xml.get("utgaaende_ek"),
        "avskrivninger": pdf_data.get("_skattemessig_avskrivning"),
    }
}

with open('<scratch>/rapport_skattemelding.json', 'w') as f:
    json.dump(rapport, f, ensure_ascii=False, indent=2)
print("Skattemeldingsdata klar")
```

## Del II – Steg 4: Generer skattemeldingsrapport (PDF)

```bash
uv run --with reportlab python <SKILL_BASE_DIR>/scripts/generer_rapport_skattemelding.py \
    <scratch>/rapport_skattemelding.json \
    <scratch>/Skattemeldingskontroll_[Selskap]_2025.pdf
```

---

# Del III – Krysskontroll (kun Scenario C: begge dokumenter)

Når både `<scratch>/rapport_aarsregnskap.json` og `<scratch>/rapport_skattemelding.json` foreligger,
kjør denne Python-blokken for å kryssjekke nøkkeltall mellom de to dokumentene:

```python
import json

ar  = json.loads(open('<scratch>/rapport_aarsregnskap.json').read())
skm = json.loads(open('<scratch>/rapport_skattemelding.json').read())

TOLER = 1.0
kryss = []

def diff_ok(a, b, navn):
    if a is None or b is None:
        kryss.append({"kontroll": navn, "aarsregnskap": a, "skattemelding": b,
                      "diff": None, "ok": None, "merknad": "Ikke funnet i ett av dokumentene"})
        return
    d = round(float(b) - float(a), 2)
    ok = abs(d) <= TOLER
    kryss.append({"kontroll": navn, "aarsregnskap": a, "skattemelding": b,
                  "diff": d, "ok": ok, "merknad": "" if ok else f"Avvik: {d:+.0f} kr"})

# 1. Skattekostnad: årsregnskap vs. beregnet fra skattemeldingen
diff_ok(
    ar.get("nokkel", {}).get("skattekostnad"),
    skm["beregnet_skatt"].get("total_skattekostnad"),
    "Skattekostnad (årsregnskap vs. skattemelding)"
)

# 2. Sum egenkapital UB: årsregnskap vs. utgående EK i skattemeldingen
diff_ok(
    ar.get("nokkel", {}).get("sum_egenkapital"),
    skm["ek_kontroll"].get("utgaaende_ek_xml"),
    "Sum egenkapital UB (årsregnskap vs. skattemelding)"
)

# 3. Avskrivninger: årsregnskap vs. skattemessige avskrivninger fra Skatteetaten XLSX
av_ar  = ar.get("nokkel", {}).get("avskrivninger")
av_skm = skm.get("_nokkel", {}).get("avskrivninger")
if av_ar is not None or av_skm is not None:
    diff_ok(av_ar, av_skm, "Avskrivninger (årsregnskap vs. skattemelding)")

# Lagre krysskontrollresultat
with open('<scratch>/krysskontroll.json', 'w') as f:
    json.dump(kryss, f, ensure_ascii=False, indent=2)

# Vis resultater i chat
print("\n── Krysskontroll ──────────────────────────────────────────────")
for r in kryss:
    ikon = "✅" if r["ok"] is True else ("⚠️" if r["ok"] is None else "❌")
    print(f"{ikon}  {r['kontroll']}")
    print(f"     Årsregnskap:  {r['aarsregnskap']}")
    print(f"     Skattemelding: {r['skattemelding']}")
    if r.get('merknad'):
        print(f"     ⚠ {r['merknad']}")
```

Legg `kryss`-listen inn i oppsummeringen i chatvinduet.

---

## Steg 5 – Vis oppsummering og del filer

### Årsregnskapsoppsummering:
```
## Årsregnskapskontroll [SELSKAP] [AAR]
Kritiske funn: X stk.  |  Brreg-roller: ✅/❌
Obligatoriske noter: X / Y OK  |  Notehenvisninger: X / Y OK  |  Matematikk: X / Y OK
```

### Skattemeldingsoppsummering:
```
## Skattemeldingskontroll [SELSKAP] 2025
| Kontroll                           | Resultat |
|------------------------------------|----------|
| Balanse IB/UB (X/Y poster OK)      | ✅ / ❌  |
| Midlertidige forskjeller IB/UB     | ✅ / ❌  |
| Egenkapitalavstemming IB/UB        | ✅ / ❌  |
| Fremførbart underskudd IB/UB       | ✅ / ❌  |
| Skatteberegning                    | ✅ / ❌  |
Beregning: [f.eks. 880 199 × 22 % = 193 644 kr]
```

### Kontoplanoppsummering (kun hvis HAR_KONTOPLAN = True):
```
## Kontoplansjekk [SELSKAP] 2024
| Kontroll                                      | Resultat |
|-----------------------------------------------|----------|
| Utsatt skattefordel vs. -forpliktelse         | ✅ / ❌  |
| Ikke-fradragsberettigede kostnader            | ✅ / ❌  |
Ikke-fradragsberettiget: [X kr på kto XXXX, YYYY – ikke reflektert i skattemeldingen]
```

### Krysskontrolloppsummering (Scenario C):
```
## Krysskontroll årsregnskap ↔ skattemelding
| Kontroll                                          | Resultat |
|---------------------------------------------------|----------|
| Skattekostnad                                     | ✅ / ❌  |
| Sum egenkapital UB                                | ✅ / ❌  |
| Avskrivninger                                     | ✅ / ❌  |
```

### PDF-sammenslåing (Scenario C – begge dokumenter):

Når **både** årsregnskap og skattemelding er kjørt, slå dem **alltid** sammen til én enkelt PDF
med `pypdf`. Årsregnskap skal komme **først**, skattemelding **etter**:

```python
from pypdf import PdfWriter, PdfReader

writer = PdfWriter()
for pdf_path in [
    "<scratch>/Gjennomgang_[Selskap]_[aar].pdf",
    "<scratch>/Skattemeldingskontroll_[Selskap]_2025.pdf"
]:
    reader = PdfReader(pdf_path)
    for page in reader.pages:
        writer.add_page(page)

samlet_path = "<scratch>/Årsoppgjørskontroll_[Selskap]_2025.pdf"
with open(samlet_path, "wb") as f:
    writer.write(f)
print(f"Samlet rapport: {samlet_path}")
```

Del **kun** den sammenslåtte PDF-en med SendUserFile (ikke de to enkeltrapportene). Sammenslåingen kjøres med `uv run --with pypdf python`.
Brukeren skal ha én fil å forholde seg til.

Hvis **kun ett** dokument er kjørt (Scenario A eller B), del den ene rapporten direkte.

---

## Viktige merknader

**Parallell kjøring (Scenario C):** Spawn alle 3 haiku-agenter + start XML/XLSX-parsing i samme
melding. Total tid domineres av haiku-agentene (~20 sek), Python-parsingen er instant.

**Brreg-rollesjekk:** Fanger opp feil styreleder/daglig leder før signering – vanlig feil ved
kopiering fra maler. Nettverksfeil gir MERKNAD, ikke FEIL.

**Krysskontroll:** Skattekostnad og sum EK er de viktigste. Avvik her er alvorlig og betyr
at de to dokumentene ikke er konsistente – typisk at skattemeldingen ikke er oppdatert etter
siste endring i årsregnskapet, eller omvendt.

**IB 2025-kilder (prioritetsrekkefølge for midlertidige forskjeller):**
1. **Kontoplan XLSX** (`Saldo 2024` summert per `MidForsRef`) – mest pålitelig, matches mot
   typekoder direkte og unngår samlekonti-problemet
2. **Skatteetaten XLSX** («RM i fjor»-kolonne) – god kilde for midlertidige forskjeller per type
3. **Maestro XLSX** («I fjor»-kolonnen) – god for individuelle balansekontoer
4. **PDF + haiku-agent** – fallback når ingen XLSX er tilgjengelig

**Samlekonti-problemet:** Skatteetaten bruker 3-sifrede typekoder (101, 140, 141 osv.) som
aggregerer mange individuelle kontoer. Kontoplanens `MidForsRef`-kolonne er den nøyaktige
koblingen mellom individuelle 4-sifrede kontoer og disse typekodene.

**Kontoplansjekk – ikke-fradragsberettiget:** Kontoer med PermanentRef ≠ '' og Saldo 2024 ≠ 0
representerer kostnader uten skattemessig fradrag. Disse skal legges til som permanente
forskjeller i skattemeldingen. Manglende permanente forskjeller betyr at underskuddet er
overvurdert med tilsvarende beløp.

**Kontoplansjekk – utsatt skatt:** Kto 1070 (utsatt skattefordel) og 2120/2121 (utsatt
skatteforpliktelse) skal aldri begge være beløpssatt. Nettostørrelse bokføres kun på den
siden som er aktuell – hvis selskapet har fremf. underskudd, skal det typisk ikke være
beløp på verken 1070 eller 2120/2121 (underskuddet er fordelen, men bokføres kun ved
aktivering som er sjelden for typiske SMBer).

**Skattemeldingen (Del II):**
- Skattesats 22 % for alle AS
- Midlertidige forskjeller IB 2025 = UB 2024 fra XML-parseren
- Avrundingstoleranse ±1 krone (±10 kr for typekode-summering fra kontoplan)
- Maestro ZIP inneholder gjerne både Skattemelding.xml og Publisering.xlsx

**Obligatoriske noter – fallgruver:**
- § 7-38: Pensjonstype trenger IKKE oppgis for små foretak.
  Lønnskostnader under 11 000 kr: note om «ingen ansatte» er tilstrekkelig, full spesifikasjon ikke påkrevd.
- § 7-43: Lønnskostnader under 11 000 kr + note om «ingen ansatte» → antall årsverk ikke påkrevd.
- § 7-39: Gjelder kun varige driftsmidler/immaterielle, ikke finansielle anleggsmidler
- § 7-42: Egne aksjer – opplysningsplikt KUN hvis selskapet faktisk eier egne aksjer.
  Negativ bekreftelse er IKKE påkrevd. Ikke flagg manglende «eier ikke egne aksjer».
- § 7-44 / § 7-45: ALDRI flagg manglende revisorhonorar, DL-godtgjørelse eller styrehonorar som innholdsmangel.
  MEN: Hvis notetittelen eksplisitt lover informasjon som ikke finnes i noten (f.eks. tittelen sier
  «godtgjørelser til daglig leder, styret og revisor» men noten kun inneholder lønnskostnadstabell),
  skal dette flagges som BØR RETTES – noteoverskriften bør forenkles slik at den kun beskriver
  det faktiske innholdet (f.eks. «Lønnskostnader»). Dette er et tittelspørsmål, ikke et innholdskrav.
- Avrundingsforskjell ±1 kr i balansen: ikke flagg
- Tomme underoverskrifter (Maestro): MERKNAD, ikke kritisk feil
- Disponeringer i RR (overføringer, utbytte): skal ha notehenvisning til EK-noten
- EK-linjer i balansen (overkursfond, annen innskutt EK, udekket tap): skal ha notekobling
- Notehenvisning fra driftsresultat til virksomhetens art: korrekt praksis, ikke flagg

---

## Arbeidsmappe, levering og Tally

- `<scratch>` er Claudes scratch-mappe for økten. Alle mellomfiler (JSON) og rapportene lages der, aldri i kundemapper på disk.
- `<SKILL_BASE_DIR>` er mappen denne filen ligger i. Skriptene finner fonter og logo selv.
- Lever den samlede PDF-en med SendUserFile. Last den opp i Tally på årsoppgjørsoppgaven (`upload_document`, kategori ARSOPPGJOR,
  periode «<år>») etter ja; er den over 3 MB, bruk `start_opplasting`.
- Ting som bevisst venter til årsoppgjøret står i kundeinstruksens seksjon «Årsoppgjør» (skillen `kundeinstruks`). Les den før kontrollen,
  og ikke flagg det som allerede er avklart der.
- Fullfør i Tally: foreslå tidsbruk og spør «Skal jeg fullføre <oppgave> for <klient> og føre <X> minutter?». Ved ja: `add_task_comment`
  (hva som er kontrollert, antall «må rettes»), `log_time`, `complete_task`.
- Slett mellomfilene i scratch når rapporten er levert.
