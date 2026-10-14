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

### 1. Hent status (én kommando, bare lesing)

`npm run -s bankavstemming -- --til ÅÅÅÅ-MM [--fra ÅÅÅÅ-MM] (--client "<klient>" | --alle) --ut <mappe>` (`--client` kan gjentas; `--fra` er
januar samme år; `<mappe>` = kort arbeidsmappe, for eksempel `%TEMP%\rr\bank-ÅÅÅÅ-MM`).
- `<mappe>/status.json`: per klient, konto og måned `avstemming` (type), `lukket`, `aapen`, `bev`, `ub`, bankens sluttsaldo og differanse,
  `bank[]` (umatchede bankposter), `tx {antall, sum}` (umatchede posteringer i hovedboken) og `forslag {antall, sum}` (matchforslag som ikke er godkjent),
  pluss `vurdering` (fra kunden / internt). `<mappe>/<Klient>.data.json` for klienter med noe fra kunden, og en oversikt `.md`.
- Konsollen viser bare antall og summer; les `status.json` med et lite skript. Klienter som feiler, står med FEIL: si det og kjør dem på nytt med `--client`.
Trengs mange enkeltlinjer vurdert, kan én lesende agent per klient gjøre steg 2 og returnere oversiktslinjen og eventuelle rettelser i `data.json`.

### 2. Klassifiser per konto og måned

- **Bare bankside-poster går til kunden.** En linje som bare finnes på banksiden, mangler i regnskapet. Poster på Tripletex-siden er internt, ofte timing.
- Umatchet er ikke manglende: sammenlign `bank[]` med `tx` og `forslag` (samme beløp og dato) før noe kalles en mangel. Linjene på hovedbokssiden:
  `npm run -s api -- GET /ledger/posting accountId=<konto-id> dateFrom=ÅÅÅÅ-MM-01 dateTo=<neste mnd>-01 fields=id,date,amount,matched --client "<klient>"`.
- `avstemming: null` med `aapen: true` er ikke startet, altså ikke avstemt. En lukket periode kan ha umatchede linjer, og null differanse
  beviser ikke samsvar med kontoutskriften; sjekk bankens sluttsaldo mot `ub`.
- Konto uten bankfeed (manuell avstemming, typisk Pareto, Cultura, Folio, sparekonto): det er kontoutskriften som mangler, ikke enkeltposter.

| Funn | Hvor |
|---|---|
| Linje i `bank[]` uten motpost blant umatchede posteringer (`tx`) eller forslag (`forslag`) | **Fra kunden** (mangler bilag) |
| Linje med motpost på den andre siden · `forslag.antall` > 0 | Internt: match · godkjenn forslaget |
| Konto uten bankfeed, måned etter siste lukkede med bevegelse | **Fra kunden**: kontoutskrift |
| Åpen måned uten umatchede linjer · konto med bevegelse og `avstemming: null` | Internt: kan lukkes · avstemming ikke opprettet |
| Skattetrekkskonto (typisk 1950), negativ saldo, statisk saldo, «Fylt på», bank- og kortgebyr | Internt |
| Kjent avvik i kundeinstruksen med samme beløp | «Kjent, uendret» |
| Dokumenter i bilagsmottaket (`npm run -s api -- GET /voucherInbox/inboxCount --client "<klient>"`) som kan høre til åpne linjer | Internt: `bilagsforing` først |

### 3. Excel til kunden

For klienter med noe under «Fra kunden» har steg 1 skrevet `<mappe>/<Klient>.data.json` (postene som `raw`, som skriptet renser).
Rett den ved behov (Write, UTF-8). `--excel` i steg 1 kjører `lag_spec.py` for alle; `sjekk.py` kjøres likevel per fil. Formatet:

```json
{ "selskap": "<Klient AS>", "orgnr": "<org.nr.>", "aar": "2026", "periode": "Januar–September 2026", "kontoer": [
    { "nummer": "1920", "navn": "Driftskonto", "maaneder": [ { "maaned": "September", "poster": [
        { "dato": "2026-09-03", "tekst": "<banktekst>", "belop": -347.08, "kilde": "Bankside" } ] } ] },
    { "nummer": "1931", "navn": "Kort", "merknad": "Ingen bankfeed – send kontoutskrift for januar–juli 2026.", "maaneder": [] } ] }
```

```
uv run --with openpyxl --with pillow --with pypdf python .claude/skills/bankavstemming/scripts/lag_spec.py "<mappe>/<Klient>.data.json" --mappe <mappe> [--format xlsx,pdf]
uv run --with openpyxl --with pypdf python .claude/skills/silfer-rapport/scripts/sjekk.py "<mappe>/Bankavstemming åpne poster ÅÅÅÅ-MM <Klient>.xlsx"
```

- Filnavnet følger standarden: `Bankavstemming åpne poster ÅÅÅÅ-MM <Klient>.xlsx` (siste måned i perioden). `--format xlsx,pdf` gir samme liste som PDF.
- Skriptet fjerner «Fylt på» og gebyrer, renser bankteksten (kortnummer, «VISA VARE», kurs, referanser) og legger utenlandsk beløp bak.
  Gi `"tekst"` i stedet for `"raw"` hvis teksten ikke skal renses. Kontoer uten poster tas med som tom liste og vises med 0.
- Faner: «Sammendrag» (antall og sum per konto, merknad) og «Åpne poster» (filtrerbar; Dokumentasjon og Status er tomme for kunden).
- Skriptet skriver antall og sum per konto; de skal stemme med steg 2. `sjekk.py` skal være grønn før filen lagres.

### 4. Skriving i Tripletex (etter ja, per klient)

Id-er med `npm run -s api -- GET … --client "<klient>"`: konto `/ledger/account number=<konto> fields=id`, periode `/ledger/accountingPeriod startFrom=ÅÅÅÅ-MM-01 startTo=<neste mnd>-01 fields=id`,
avstemming `/bank/reconciliation accountId=<konto-id> accountingPeriodId=<periode-id> fields=id,isClosed`.

**Skriving (etter ja):**
1. Match bankpost mot postering (også når posteringen ligger i forrige måned; avstemmingen må være åpen). Transaksjons-id fra `bank.json` (`bilag hent`),
   posterings-id fra steg 2: `npm run -s api -- POST /bank/reconciliation/match body='{"bankReconciliation":{"id":<id>},"type":"MANUAL","transactions":[{"id":<tx>}],"postings":[{"id":<postering>}]}' --client "<klient>" --bekreft`
2. Bankavstemmings-PDF (eksport, lesende): `npm run -s modul -- bankpdf --client "<klient>" --konto <19xx> --maaned ÅÅÅÅ-MM --ut <mappe>`.
3. Avstemmingsmodulen, 19xx med bevegelse (BALANCE-id fra `npm run -s modul -- perioder --client "<klient>" --aar ÅÅÅÅ --type BALANCE --json`, `accountId` fra
   `modul -- linjer --client "<klient>" --id <BALANCE-id> --konto 19`): `modul -- last-opp --client "<klient>" --id <BALANCE-id> --ref <accountId> --fil <fil> --bekreft`
   for PDF og kontoutskrift, så `modul -- sett-status --client "<klient>" --id <BALANCE-id> --konto <accountId> --status RECONCILED --dokumentert <saldo> --bekreft`.

**Bare i Tripletex-UI:**
1. Godkjenn forslagene under «Forslag» i bankavstemmingen.
2. Lukk måneder med differanse 0. Les avstemmingen før og etter (steg 1 på nytt).
3. Manuell avstemming (uten bankfeed): før kontoutskriften som ett bankbilag per måned, datert siste dag, én linje per bankpost mot reskontro,
   gebyr (7770) eller renter (8050). Opprett avstemmingen med utgående saldo, lukk ved differanse 0. Uten kontoutskrift og saldo 0: avstem mot 0.
4. 422 når en tidligere måned opprettes: en senere måned er allerede godkjent. Åpne den senere, avstem den tidlige, lukk den senere igjen.
5. Vedlegg på selve bankavstemmingen: kontoutskrift og Tripletex' bankavstemmings-PDF.

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

- Hovedbokssøk finner ikke åpne bankposter; hovedboken viser bare det som er bokført. Bruk `bank[]` i `status.json` (eller `bank.json` fra `bilag hent`).
- `accountId` i `/bank/*`-kall er kontoens interne id, ikke kontonummeret. `dateTo` er eksklusiv. Fjern aldri identiske rader; mange like beløp er ekte.
- Status «avstemt» i avstemmingsmodulen blir ikke satt automatisk; `--dokumentert` er bankens sluttsaldo fra `status.json`.

## Referanser

- `docs/kontrollkatalog.md`: B1–B5. Naboskills: `bilagsforing`, `reskontroavstemming`, `balanseavstemming` (19xx dokumentert saldo), `silfer-rapport`.
- `scripts/lag_spec.py`: bygger spec fra `data.json` og kaller `silfer-rapport`. Logo og stil ligger i `silfer-rapport`.
