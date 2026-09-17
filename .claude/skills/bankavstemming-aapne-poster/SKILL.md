---
name: bankavstemming-aapne-poster
description: >
  Henter ut åpne (uavstemte) poster fra Tripletex «Automatisk bankavstemming»
  konto for konto og måned for måned, og lager en ferdig Excel-rapport med
  Silfer-header som kan sendes til kunden for å skaffe dokumentasjon. Bruk denne
  skillen når brukeren vil ha en liste over åpne/uavstemte bankposter, «åpne
  poster på bankkonto», «uavstemte poster», poster som «mangler bilag» eller
  «mangler dokumentasjon», en «bankavstemmingsliste til kunden», eller vil
  gjennomgå bankkontoer per måned i Tripletex. Trigger også når brukeren limer
  inn rå uttrekk fra bankavstemmingssiden og vil ha det satt opp som en pen
  liste/rapport, eller ber Claude i Chrome lese av avstemmingssiden. Klient-
  uavhengig – fungerer på tvers av alle klienter. Excel er standard leveranse.
---

# Åpne poster i bankavstemming → Excel-rapport

## Hva skillen gjør
1. **Henter** åpne (uavstemte) poster fra Tripletex «Automatisk bankavstemming»,
   konto for konto og måned for måned (via Claude i Chrome), ELLER tar imot rå
   uttrekk brukeren allerede har.
2. **Strukturerer** postene til `data.json` (skjema nedenfor).
3. **Genererer** en Excel-rapport med Silfer-header: én filtrerbar postliste + et
   sammendrag, klar til å sende kunden.

Hele hensikten er at kunden skal kunne finne dokumentasjon/bilag for hver post.

## Når IKKE å bruke
Ikke bruk hovedbok-/posteringssøk (f.eks. Tripletex-MCP `search_ledger_postings`)
for å finne åpne poster – der ser du bare **bokførte og allerede avstemte** poster,
ikke avstemmingsstatusen. De åpne postene finnes kun i bankavstemmingssiden.

---

## Steg 1 – Skaff postene

Du har to veier. Velg ut fra hva brukeren gir deg.

### Vei A – Brukeren limer inn uttrekk
Hvis brukeren allerede har rådataene (fra Claude i Chrome eller manuelt), hopp
rett til **Steg 2**. Behold radene ordrett, og hold styr på konto, måned og side
(Tripletex-side vs. bankside).

### Vei B – Les av via Claude i Chrome (RASK metode)
Les `references/chrome-uttrekk.md` – den har den raske oppskriften. Kort fortalt:
- Last alle Chrome-verktøy i ETT ToolSearch-kall (inkl. `browser_batch`).
- Bytt inn i klienten (åpnes i ny fane) → les `contextId` fra fanens URL.
- Finn `accountId` per konto **én gang** (klikk hver konto i velgeren, les
  accountId fra tab-context-URL) og cache dem. **Hopp over skattetrekk (typ. 1950).**
- Naviger direkte via URL (`contextId`+`accountId`+`period`) og hent **alle måneder
  for en konto i ett `browser_batch`** (navigate → wait 2s → JS-uttrekk per måned).
  Ingen screenshots, ingen måneds-fane-klikking.
- `[]` = ingen åpne poster. `side:"TX"` = Tripletex-side, `side:"BANK"` = Bankside.
- Alltid **lesemodus** – aldri matche/lukke/endre/slette.

Kritisk: broen blokkerer URL-/id-output – les contextId/accountId fra tab-context,
og la JS returnere kun radtekst. Er du usikker på kontoliste/periode, spør kort.

---

## Steg 2 – Strukturer til data.json

Bygg denne strukturen. Poster kan oppgis **strukturert** eller som **rå-strenger**
(`generer_excel.py` tolker rå-strenger selv – minustegn −, mellomrom-tusenskille,
komma-desimal og «| Detaljer:»).

```json
{
  "selskap": "Klient AS",
  "orgnr": "",
  "aar": "2026",
  "periode": "Januar–Juni 2026",
  "dato": "",
  "kontoer": [
    {
      "nummer": "1920",
      "navn": "Driftskonto 3606 18 91212",
      "merknad": "",
      "maaneder": [
        { "maaned": "Juni", "poster": [
            { "raw": "2026-06-08 5 060,50 Oase ... | Detaljer: Fylt på", "kilde": "Bankside" },
            { "dato": "2026-06-01", "tekst": "Dintero AS", "belop": -2712.50, "kilde": "Tripletex-side" }
        ]},
        { "maaned": "Januar", "status": "Avstemt og lukket", "poster": [] }
      ]
    },
    { "nummer": "1930", "navn": "Kort Olle", "maaneder": [] }
  ]
}
```

Felt-regler:
- `orgnr`, `dato`, `periode`, `merknad`, `status` er valgfrie. `dato` er
  rapportdato (standard = i dag). Ikke slå opp org.nr eller andre eksterne kilder
  med mindre brukeren ber om det.
- `kilde`: `"Tripletex-side"` (bokført, ikke sett i bank) eller `"Bankside"` (i
  bank, mangler bilag). `"left"/"right"/"Tripletex"/"Bank"` godtas også.
- **Standard: kun BANKSIDE-poster tas med.** Tripletex-side (ofte timing) filtreres
  bort automatisk – det er bankside-postene kunden må skaffe bilag for. Vil du ha
  med begge, sett `"inkluder_tripletex_side": true` i data.json.
- Kontoer uten åpne poster tas med som tom `maaneder`-liste (eller måneder med
  tom `poster`) – de vises i sammendraget med 0.
- Ta med **alle** poster, også identiske dubletter (mange × samme beløp er ekte).
- **«Fylt på» (kortpåfyll) og bank-/kortgebyr filtreres automatisk bort** av
  generatoren – disse krever ingen dokumentasjon fra kunden. Ta dem gjerne med i
  `data.json`; skriptet utelater dem selv og rapporterer hvor mange. (Reglene
  ligger i `IRRELEVANT_MØNSTRE` i `generer_excel.py` hvis de skal justeres.)
- **Tekst-kolonnen renses automatisk** for råstrenger (`"raw"`): generatoren
  fjerner betalingstype-prefiks (Visa/Giro…), valutakurs-støy, bilag-/faktura-/
  referansehaler og lange arkivnr, trekker ut utenlandsk valutabeløp som suffiks,
  og pen-setter store bokstaver. Eks: «VisaVALUTAKURS: 11,0353 – EUR 126,50
  GOOGLE:WORKSPACE E, 0546976…» → «Google Workspace 126,50 EUR». Vil du overstyre,
  send `"tekst"` eksplisitt (da renses den ikke). Logikken ligger i `clean_tekst`
  / `ACRONYMER` i `generer_excel.py`.

Regn ikke summer manuelt – Excel-arket beregner dem via formler.

---

## Steg 3 – Generer Excel-rapporten

```bash
python scripts/generer_excel.py <data.json> <output.xlsx>
```

Deretter **må** formlene beregnes og kontrolleres for feil (bruk xlsx-skillets
recalc, eller LibreOffice):
```bash
python /mnt/skills/public/xlsx/scripts/recalc.py <output.xlsx> 60
```
Skal returnere `"status": "success"` med `total_errors: 0`. Fiks ev. feil og kjør
på nytt.

Rapporten får to faner, begge med Silfer-header (logo øverst):
- **Sammendrag** – per konto: antall åpne poster + sum beløp (COUNTIF/SUMIF), med
  totalrad.
- **Åpne poster** – filtrerbar tabell (autofilter, frosne titler) med kolonnene
  Konto · Kontonavn · Måned · Dato · Tekst · Beløp · Kilde · **Dokumentasjon** ·
  **Status**. De to siste er tomme for kunden. Negative beløp i rødt; ekte datoer.

Filnavn-forslag: `Aapne_poster_bankavstemming_<Klient>_<år>.xlsx`.

Legg filen i utdatamappen og del den med brukeren. Gi en kort oppsummering
(antall poster per konto, totalsum, og evt. kontoer uten poster). Ikke lim inn
hele listen i chatten – Excel-arket er leveransen.

---

## Tips
- Vil brukeren heller ha PDF eller annen branding, tilpass etter forespørsel –
  standard er Excel med Silfer-logo.
- «Fylt på»-poster er interne kortpåfyll; de er egentlig selvforklarende, men tas
  med. Foreslå gjerne å markere/skille dem ut hvis kunden lett forveksler dem.
- Nyttig å legge til nedtrekksvalg i Status-kolonnen (f.eks. «Mangler bilag /
  Mottatt / Avklart») hvis brukeren ønsker det.
