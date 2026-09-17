# Oppsett

## 1. Tripletex-tilgang

Tripletex' API krever to nøkler:

- **Consumer token** – knyttet til integrasjonen, ikke til deg. Bestilles fra Tripletex.
  Ta kontakt med Tripletex support og be om consumer token for en egen integrasjon
  til regnskapskontoret. Be samtidig om tilgang til testmiljøet
  (`https://api-test.tripletex.tech/v2`), så kan alt prøves uten å røre produksjon.
- **Employee token** – knyttet til din bruker i regnskapsførerselskapet. Lages inne i
  Tripletex under API-tilgang på din egen bruker, med consumer-tokenet som mottaker.

Ett employee token er nok for alle klientene du har tilgang til. Klientbytte skjer ved
å sette `companyId` i kallet, ikke ved å lage nye nøkler per klient.

Menyplasseringen i Tripletex endrer seg mellom versjoner – finner du den ikke, spør
support om «API-tilgang / employee token for regnskapsfører».

Når du har nøklene:

```bash
cp .env.example .env
```

Fyll inn `TRIPLETEX_CONSUMER_TOKEN` og `TRIPLETEX_EMPLOYEE_TOKEN` i `.env`.
`.env` er i `.gitignore` og skal ikke deles.

## 2. Verifiser tilgangen

```bash
uv run --system-certs python sjekk-tilgang.py
```

Skriver ut hvem tokenet tilhører og hvilke klientselskaper det når. Deretter:

```bash
uv run --system-certs python sjekk-tilgang.py --klient Eksempel --periode 2026-08
```

Denne går gjennom hvert endepunkt kontrollene bruker og sier hvilke som svarer.
Endepunkter som ikke er med i klientens lisens (prosjekt, lager, lønn) vil vise
FEIL – det er forventet, og de kontrollene hoppes over automatisk.

## 3. Koble klientlisten mot Tripletex

Klientlisten holdes i `klienter.json` og fylles fra to kilder.

**Kunderegisteret** (`Kundeoversikt*.xlsx` på skrivebordet) gir navn,
system, regnskapskontor og bankkontoer:

```bash
uv run --system-certs python synk-kunderegister.py
```

Med `--aktiver "Eksempel,Annen Kunde"` settes de som matcher aktive og resten inaktive.
Bankkontoene legges samtidig inn som notat i `klientprofil.md` for de aktive.

**Tripletex** gir riktig `company_id`, som er det kjøringen faktisk trenger:

```bash
uv run --system-certs python hent-klienter.py
```

Ingen klient kjøres før `aktiv: true` er satt. Bare Tripletex-klienter kan kjøres –
Fiken og PowerOffice merkes automatisk som ikke støttet.

## 4. Klientprofiler

```bash
uv run --system-certs python lag-klientfiler.py
```

Oppretter `klientprofil.md` og `kjente-avvik.md` i hver kundemappe (rører ikke
filer som finnes fra før). Gå gjennom profilene og bekreft feltene merket `?`:
mva-plikt, lønn, prosjekt, varelager, utleie og vesentlighetsgrense. Det er disse
som avgjør hvilke kontroller som kjøres.

## 5. Kjør

```bash
uv run --system-certs python maanedskontroll.py --periode 2026-08
```

eller på Windows:

```bash
kjor.cmd --periode 2026-08
```

Nyttige varianter:

| Kommando | Gjør |
|---|---|
| `--liste` | viser hele kontrollkatalogen |
| `--klient Eksempel` | kjører bare klienter som matcher teksten |
| `--kontroll R1,R2,M1` | kjører bare disse kontrollene |

Resultatet blir `Kontroll ÅÅÅÅ-MM <Klient>.xlsx` i hver kundes årsmappe, én samlet
`status/ÅÅÅÅ-MM Statusrapport alle klienter.xlsx`, og en ny linje i hver `logg.md`.

## Feilsøking

**`--system-certs`** trengs fordi uv ellers ikke stoler på rot-sertifikatet i
Windows' sertifikatlager. Python selv bruker Windows-lageret, så selve API-kallene
går fint uten flagget.

**Sertifikatfeil mot tripletex.no**: rot-sertifikatet fra bedriftsproxyen må ligge
i Windows' sertifikatlager.

**401 midt i en kjøring**: session token har utløpt. Verktøyet henter nytt token
automatisk én gang; skjer det ofte, sjekk at employee token ikke har utløpsdato
som nærmer seg.

**En kontroll feiler**: kjøringen fortsetter, og feilen havner i arket
«Sammendrag» under Kjøringsnotater. Kjør `sjekk-tilgang.py` på klienten for å se
hvilket endepunkt som svarte dårlig.

**Rapporten er låst**: har du filen åpen i Excel, lagres den med klokkeslett i
navnet i stedet for at kjøringen ryker.

## Selvtest

```bash
uv run --system-certs python selvtest.py
```

Kjører hele katalogen mot et konstruert datasett med kjent fasit, uten API.
Skal ende med «mangler: -» og ingen feil. Kjør den etter endringer i kontrollene.
