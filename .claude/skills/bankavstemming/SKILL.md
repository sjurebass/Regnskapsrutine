---
name: "bankavstemming"
description: "Bankavstemming for Tripletex-klienter: status per bankkonto og måned (lukket, åpen, ikke startet), umatchede bankposter som mangler bilag mot det som er internt arbeid, og Silfer-Excel med åpne poster til kunden. Lukker Tally-oppgaven «Bankavstamming» (Tallys stavemåte). Bruk ved «bankavstemming», «avstem bank», «avstem bankkontoene», «åpne bankposter», «uavstemte bankposter», «hvilke klienter har bankkontoer som ikke er lukket», «lag excel med åpne bankposter», «kontoutskrift mangler»."
---

# Bankavstemming

Viser hvor langt bankavstemmingen har kommet for én eller flere Tripletex-klienter, skiller det kunden må levere fra det byrået gjør selv,
og lager en Silfer-Excel med åpne poster til kunden. Dokumenter i bilagsmottaket føres med `bilagsforing`; 1500/2400 avstemmes i `reskontroavstemming`.

## Når

- Tally-oppgaven «Bankavstamming», den 15. i måneden. `bilagsforing` bør være kjørt først, så mottaket er tomt for det som har bankmotpost.
- Brukeren oppgir klient, eller ber om «alle». Periode: januar til og med forrige måned i samme år, hvis ikke annet er sagt.

## Kundeinstruks

«Bank» (kontoer, bankfeed ja/nei, kontoer uten integrasjon), «Mangelliste» (konto for manglende bilag) og «Kjente avvik».

## Steg

### 1. Hent status (ett skript)

Finn klientene med `search_client_companies` (navngitt, eller alle) og les alle i ett `tripletex_run_script` (feltnavn: `tlx.help('<verktøy>')`).

```js
const KLIENTER = ['<navn 1>', '<navn 2>'], AAR = 2026, TIL = '2026-09';   // TIL = til og med
const ut = {};
for (const navn of KLIENTER) {
  try {
    const per = await tlx.get_bank_reconciliation_periods({ companyName: navn, year: AAR });
    const kontoer = {};   // per konto og periode (ÅÅÅÅ-MM): status, bankBalance, ledgerBalance, difference – sjekk formen i første kall
    // For hver konto og åpen måned til og med TIL:
    //   const u = await tlx.get_unmatched_bank_transactions({ companyName: navn, accountNumber: '<konto>', date: '<ÅÅÅÅ-MM>-15' });
    //   antall og sum for u.unmatched, u.unmatchedPostings og u.awaitingApproval; bare for u.unmatched: postedDate, amountCurrency, description
    ut[navn] = kontoer;
  } catch (e) { ut[navn] = { feil: e.message }; }
}
return ut;
```

Ett skript tåler 200 kall og 2 minutter; mange klienter deles i flere kjøringer. Rader som feiler på rate limit mangler: si det og kjør dem på nytt.
Trengs mange enkeltlinjer vurdert, kan én lesende agent per klient gjøre steg 2 og returnere oversiktslinjen og `data.json`.

### 2. Klassifiser per konto og måned

- **Bare bankside-poster går til kunden.** En linje som bare finnes på banksiden, mangler i regnskapet. Poster på Tripletex-siden er internt, ofte timing.
- Umatchet er ikke manglende: sammenlign `unmatched` med `unmatchedPostings` og `awaitingApproval` (samme beløp og dato) før noe kalles en mangel.
- `not_started` er ikke avstemt. En lukket periode kan ha umatchede linjer, og null differanse beviser ikke samsvar med kontoutskriften.
- Konto uten bankfeed (manuell avstemming, typisk Pareto, Cultura, Folio, sparekonto): det er kontoutskriften som mangler, ikke enkeltposter.

| Funn | Hvor |
|---|---|
| Bankside-linje uten motpost i `unmatchedPostings` eller `awaitingApproval` | **Fra kunden** (mangler bilag) |
| Linje med motpost i den andre listen · forslag i `awaitingApproval` | Internt: match · godkjenn forslaget |
| Konto uten bankfeed, måned etter siste lukkede med bevegelse | **Fra kunden**: kontoutskrift |
| Åpen måned uten umatchede linjer · konto med bevegelse og `not_started` | Internt: kan lukkes · avstemming ikke opprettet |
| Skattetrekkskonto (typisk 1950), negativ saldo, statisk saldo, «Fylt på», bank- og kortgebyr | Internt |
| Kjent avvik i kundeinstruksen med samme beløp | «Kjent, uendret» |
| Dokumenter i bilagsmottaket (`get_voucher_inbox_count`) som kan høre til åpne linjer | Internt: `bilagsforing` først |

### 3. Excel til kunden

For klienter med noe under «Fra kunden»: skriv `data.json` i scratch (Write-verktøyet, UTF-8) og kjør generatoren fra repo-rota.

```json
{ "selskap": "<Klient AS>", "orgnr": "<org.nr.>", "aar": "2026", "periode": "Januar–September 2026", "kontoer": [
    { "nummer": "1920", "navn": "Driftskonto", "maaneder": [ { "maaned": "September", "poster": [
        { "dato": "2026-09-03", "tekst": "<banktekst>", "belop": -347.08, "kilde": "Bankside" } ] } ] },
    { "nummer": "1931", "navn": "Kort", "merknad": "Ingen bankfeed – send kontoutskrift for januar–juli 2026.", "maaneder": [] } ] }
```

```
uv run --with openpyxl --with pillow --with pypdf python .claude/skills/bankavstemming/scripts/lag_spec.py <scratch>/data.json --mappe <scratch> [--format xlsx,pdf]
uv run --with openpyxl --with pypdf python .claude/skills/silfer-rapport/scripts/sjekk.py "<scratch>/Bankavstemming åpne poster ÅÅÅÅ-MM <Klient>.xlsx"
```

- Filnavnet følger standarden: `Bankavstemming åpne poster ÅÅÅÅ-MM <Klient>.xlsx` (siste måned i perioden). `--format xlsx,pdf` gir samme liste som PDF.
- Skriptet fjerner «Fylt på» og gebyrer, renser bankteksten (kortnummer, «VISA VARE», kurs, referanser) og legger utenlandsk beløp bak.
  Gi `"tekst"` i stedet for `"raw"` hvis teksten ikke skal renses. Kontoer uten poster tas med som tom liste og vises med 0.
- Faner: «Sammendrag» (antall og sum per konto, merknad) og «Åpne poster» (filtrerbar; Dokumentasjon og Status er tomme for kunden).
- Skriptet skriver antall og sum per konto; de skal stemme med steg 2. `sjekk.py` skal være grønn før filen lagres.

### 4. Skriving i Tripletex (etter ja, per klient)

**Krever skriving utenfor MCP: Tripletex-UI (eller API-kobling):**
1. Match bankpost mot postering (manuell match). Det går også når posteringen ligger i forrige måned.
2. Godkjenn forslagene under «Forslag» i bankavstemmingen.
3. Lukk måneder med differanse 0. Les avstemmingen før og etter.
4. Manuell avstemming (uten bankfeed): før kontoutskriften som ett bankbilag per måned, datert siste dag, én linje per bankpost mot reskontro,
   gebyr (7770) eller renter (8050). Opprett avstemmingen med utgående saldo, lukk ved differanse 0. Uten kontoutskrift og saldo 0: avstem mot 0.
5. 422 når en tidligere måned opprettes: en senere måned er allerede godkjent. Åpne den senere, avstem den tidlige, lukk den senere igjen.
6. Vedlegg: kontoutskrift og Tripletex' bankavstemmings-PDF på bankavstemmingen.
7. Avstemmingsmodulen: 19xx med bevegelse får bankavstemmings-PDF og kontoutskrift som vedlegg, så status «avstemt» (blir ikke automatisk).

## Svar

Én tabell over alle klientene, uten banktekster og navn (én klient: funn-formatet i `docs/skill-mal.md`, ID B1–B5):

| Klient | Fra kunden | Internt |
|---|---|---|
| Eksempel AS | 1920: 6 poster uten bilag; 1931: kontoutskrift jan–jul | 1920 jan–feb: kan lukkes; 1950: skattetrekkskonto ikke lukket |

Klienter som ikke kunne leses, står som egen gruppe med grunn. Si aldri «ingenting å etterlyse» for en konto som ikke er lest.
Etter Excel: antall poster per konto, totalsum og lenken til dokumentet i Tally. Lista limes ikke inn i chatten.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `BILAG`, periode `ÅÅÅÅ-MM`, samling `Bankavstemming ÅÅÅÅ`, oppgave «Bankavstamming»).
Fullfør i Tally: se `tally-gjoremal`. «Bankavstamming» fullføres når alle måneder i perioden er lukket, eller det som gjenstår er etterlyst. Kommentaren inneholder periode, kontoer som er lukket og hva som gjenstår.

## Fallgruver

- Hovedbokssøk finner ikke åpne bankposter; hovedboken viser bare det som er bokført. Bruk `get_unmatched_bank_transactions`.
- Fjern aldri identiske rader. Mange like beløp er ekte.

## Referanser

- `docs/kontrollkatalog.md`: B1–B5. Naboskills: `bilagsforing`, `reskontroavstemming`, `balanseavstemming` (19xx dokumentert saldo), `silfer-rapport`.
- `scripts/lag_spec.py`: bygger spec fra `data.json` og kaller `silfer-rapport`. Logo og stil ligger i `silfer-rapport`.
