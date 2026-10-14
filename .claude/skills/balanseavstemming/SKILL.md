---
name: "balanseavstemming"
description: "Avstemming av balansekontoer i Tripletex utenom bank og reskontro: saldo per konto mot dokumentasjon (skattetrekkskonto 1950, 2600/2770 mot a-melding, 2740 mot mva, 2940 feriepenger, periodiseringer, lån, mellomregning aksjonær, egenkapital, sovende kontoer), i terminmåneder og per 31.12, med ark klart for avstemmingsmodulen. Lukker Tally-oppgavene «Avstemming balansekontoer» og «Balanseavstemming». Bruk ved «avstem balansen», «balanseavstemming», «avstem balansekontoer», «balansespesifikasjon», «avstem balansekonto <nr>», «mellomregning», «sovende kontoer»."
---

# Balanseavstemming

Én rad per balansekonto med IB, bevegelse, UB, dokumentert saldo, avstemmingsposter, differanse, status og kilde, og et ferdig ark til avstemmingsmodulen.
Metoden (oppstilling, kategori, alder, eskalering) står i `docs/avstemmingsmetodikk.md`. Bank (19xx) avstemmes i `bankavstemming` og 1500/2400 i
`reskontroavstemming`; her brukes bare resultatet derfra som dokumentert saldo.

## Når

- Tally «Avstemming balansekontoer» (16., i terminmåneder: siste måned i hver termin for mva; nivå 3 i `periodeavslutning`) og «Balanseavstemming» (26.2, hele balansen per 31.12).
- Først: bank lukket for måneden (`bankavstemming`), reskontro avstemt (`reskontroavstemming`), a-melding levert (`a-melding`), i terminmåneder
  også mva levert (`mva-innlevering`). Per 31.12 er `aarsoppgjoer-forberedelse` kjørt; saldobalansen derfra er utgangspunktet.
- Brukeren oppgir klient og periode `ÅÅÅÅ-MM` (standard: siste måned i siste avsluttede termin) eller «31.12 ÅÅÅÅ». Valgfritt: én konto.

## Kundeinstruks

«Regnskapssystem og byrå» (V) · «Bank» (1950, kontoer uten feed) · «Lønn» (direkte trekk eller skattetrekkskonto, feriepengesats) · «Mangelliste»
(konto for manglende bilag) · «Reskontro og balanse» (kontoer avstemt månedlig eller årlig, konsernselskaper) · «Årsoppgjør» (det som bevisst venter) · «Kjente avvik».

## Steg

Utkast – kalibreres mot første klient. Følg stegene, men si fra om noe ikke stemmer med det verktøyene gir.

Lesing: `npm run -s api -- GET <sti> <parametre> "fields=…" --client "<klient>"`. D = første dag etter perioden (`dateTo` og `date` er eksklusive).
Posteringer: `/ledger/posting dateFrom=ÅÅÅÅ-01-01 dateTo=D accountNumberFrom=<fra> accountNumberTo=<til> "fields=date,amount,account(number),voucher(number,year),description"`
med `--sider --ut %TEMP%\rr\balanse-ÅÅÅÅ-MM\<konto>.json`. Bare sammendraget vises.

### 1. Saldobalanse og port
- `npm run -s status -- --client "<klient>" --maaned ÅÅÅÅ-MM --json` → bank lukket, reskontro mot UB, a-melding, observasjonskonti og mva i én port.
- `/balanceSheet dateFrom=ÅÅÅÅ-01-01 dateTo=D accountNumberFrom=1000 accountNumberTo=8999 includeActiveAccountsWithoutMovements=true`
  med `"fields=account(id,number,name),balanceIn,balanceChange,balanceOut"` → IB, bevegelse, UB. Resultatkontoene brukes bare til S9 (udisponert resultat).
- Samme kall på 1000–2999 med `dateFrom` = D − 12 måneder → sovende kontoer (A5). Samme for år − 1 på 2000–2099 og 2500/1570 → IB-kontroll (S5, S6).
- `/ledger/account isBalanceAccount=true "fields=id,number,name,ledgerType,isBankAccount" --sider` → hvilke kontoer som er reskontro og bank.
Behold kontoer med UB ≠ 0 eller bevegelse ≠ 0. Kontroller S9 først: går balansen ikke opp, stopp og si at dataene er feil.

### 2. Dokumentert saldo per kontogruppe
Les resultatet fra naboskillen for samme periode der det finnes, ellers kallet i tabellen (felt for `/asset` og `/claimsAndPayments`: `references/kontroller.md`):

| Konto | Dokumentert saldo | Kilde (API) |
|---|---|---|
| 19xx | bankens sluttsaldo for måneden (lukket, differanse 0) | `npm run -s bankavstemming -- --client "<klient>" --til ÅÅÅÅ-MM` (`status.json`) / `bankavstemming` |
| 1500 / 2400 | Σ åpne poster per D | `/ledger/posting/openPost date=D` per konto / `reskontroavstemming` |
| 2740, 2700–2739 | −beløp å betale for levert, ubetalt termin, ellers 0 | `npm run -s mva -- status --client "<klient>" --aar ÅÅÅÅ --termin N --json`, `/ledger/posting` 27xx / `mva-innlevering` |
| 2600 / 2770 | ubetalt trekk og arbeidsgiveravgift (påløpt − betalt) | `npm run -s amelding -- status --client "<klient>" --maned ÅÅÅÅ-MM --json` / `lonnsavstemming` |
| 2940 (2780/2785) | feriepengegrunnlag hittil i år × sats − utbetalt | `/ledger/posting` 5000–5099, 2940 og 2780–2785 |
| 1950 | minst skyldig trekk på 2600 (ikke ved direkte trekk) | `/balanceSheet` (steg 1) |
| 1700–1799, 2900–2999 | periodiseringsbilag som fortsatt gjelder, ett per post | `/ledger/posting` |
| 1200–1299 | anleggsregisteret = UB; årets avskrivning (60xx) bokført | `/asset`, `/asset/balanceAccountsSum`, `/ledger/posting` 6000–6099 |
| 13xx / 15xx / 29xx mot aksjonær | låneavtale eller protokoll; debet mot personlig aksjonær er AVVIK | `/ledger/posting` |
| 13xx / 15xx / 22xx / 24xx / 29xx mot konsernselskap | motpartens saldo med motsatt fortegn (S13); begge selskapene navngitt av brukeren | `/balanceSheet` hos begge klientene, ellers saldobekreftelse via kunden |
| 2000–2099 | fjorårets UB + protokollførte endringer | `/balanceSheet` år − 1 og i år |
| 2500 / 1570 | fjorårets betalbare skatt − betalt | `/ledger/posting` 2500/1570, `/claimsAndPayments year=ÅÅÅÅ` |
| 2200–2299 | låneoppgave eller nedbetalingsplan (per 31.12) | dokument fra kunden |
| Konto for manglende bilag (typisk 1370 eller 7799) | 0 | `status` (observasjonskonti) |

### 3. Oppstilling og status per konto
- Oppstilling: UB ± avstemmingsposter = dokumentert saldo. Det som står igjen, er uforklart differanse (S10). Hver post får kategori
  (1 tidsforskjell, 2 krever føring, 3 må undersøkes) og alder (0–30, 31–60, 61–90, over 90 dager per S) med eskalering over V/2 og V (S11),
  og kontoen trend mot forrige periodes fil i Tally (S12). Eksempler per kontogruppe: `references/kontroller.md`.
- OK: differanse under 1 kr og kilden finnes. FORKLART: bare kategori 1. KJENT: kjent avvik, samme beløp. AVVIK: kategori 2 eller 3, eller uforklart
  differanse (over V gir rød port). IKKE AVKLART: ingen dokumentasjon (S1).
- Kontrollene S1–S3, S5–S13, B2–B4, R1, R2, M2, L2, L3, A4, A5, D2 og E1 med utslag og grunnlag: `references/kontroller.md`.
- Sovende kontoer (A5, unntatt egenkapital, langsiktig lån og depositum): foreslå IGNORED i modulen; settes bare etter ja.
- Det kundeinstruksen sier venter til årsoppgjøret, flagges ikke i månedene. Varige svar om en konto tilbys lagret i kundeinstruksen.

### 4. Rettinger (etter ja)
Poster i kategori 2 føres helst med `periodisering` (`bilag manuell` med føringskontroll). Enkeltbilag ellers:
**Skriving (etter ja):** `npm run -s api -- POST /ledger/voucher body='<bilag>' --client "<klient>"` – først uten `--bekreft` (viser bilaget), så med `--bekreft`.
1. Ompostering fra observasjonskonti, bare med bilaget for akkurat den transaksjonen.
2. Avskrivning, reversering av periodisering eller avsetning: bilag med konto, beløp og dato fra forslagslista.
Vis forslagene nummerert med konto, beløp og bilag før ja, ett ja per bilag, og si «ikke gjort» om det som står igjen.

### 5. Avstemmingsmodulen (etter ja)
Lesing: `npm run -s modul -- perioder --client "<klient>" --aar ÅÅÅÅ --type BALANCE --json` → id for måneden; `modul -- linjer --id <id>` → `accountId`, saldo, status.
**Stopp:** kontoen har differanse under 1 kr etter oppstillingen (S10) – ellers settes ikke RECONCILED: vis oppstillingen og let etter årsaken.
**Stopp:** ingen post i kategori 3 over V står uten beslutning (S11) – ellers settes ikke RECONCILED og `fullfor` kjøres ikke: vis posten med `Krever: oppdragsansvarlig`.
**Skriving (etter ja):** `npm run -s modul -- <kommando> --client "<klient>" --id <id> … --bekreft`, hver først uten `--bekreft`:
1. `sett-status --konto <accountId> --status RECONCILED --dokumentert <beløp>` per konto i arket «Modul» (IGNORED bare etter eget ja).
2. `last-opp --ref <accountId> --fil <sti>` per konto (kontoutskrift, låneoppgave, beregning); kontroller med `modul -- vedlegg --id <id>`.
3. `fullfor` når alle linjer har status og differanse 0.
**Bare i Tripletex-UI:**
1. Kommentar på linjen: én setning med årsaken (`modul` skriver ikke kommentarer).
2. Årsavstemmingen per 31.12 (ANNUAL_BALANCE): `modul` dekker bare de månedlige avstemmingene.

### 6. Fil og årsoppgjørsfase
- Spec til `silfer-rapport`: «Sammendrag» (Konto · Navn · IB · Bevegelse · UB · Dokumentert saldo · Differanse · Status · Kilde · Merknad, antall per status, port,
  utført av og dato), «Poster» (Konto · Dato · Beløp · Kategori · Alder · Forslag · Krever), «Modul» (Konto · accountId · Status · Dokumentert saldo ·
  Vedlegg · Kommentar) og «Tiltak» (nummerert, med Krever).
- Filnavn `Balanseavstemming ÅÅÅÅ-MM <Klient>.xlsx`; per 31.12 `Balanseavstemming ÅÅÅÅ <Klient>.xlsx` og PDF `Balansespesifikasjon ÅÅÅÅ <Klient>.pdf`.
- Per 31.12, etter ja: Tally `update_arsoppgjor` fase `balanseavstemming` med status og kort notat.

## Svar

- Port (grønn/gul/rød) og antall OK · FORKLART · KJENT · AVVIK · IKKE AVKLART, og avstemmingsposter per kategori og aldersgruppe. Maks 10 linjer.
- AVVIK og IKKE AVKLART i funn-formatet: ID · Klient · Periode · Konto · Beløp · Status · Forslag (kategori og alder først) · Krever.
- Til slutt det som står igjen: skriving som venter på ja (rettinger, modulen) og det som bare kan gjøres i Tripletex-UI.
- Mellomregning vises som «aksjonær 1 (rolle)». Aldri navn eller lønn per person.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `BILAG`, periode `ÅÅÅÅ-MM`, samling `Balanseavstemming ÅÅÅÅ`, oppgave «Avstemming balansekontoer»; per 31.12 kategori `ARSOPPGJOR`, periode `ÅÅÅÅ`, samling `Årsoppgjør ÅÅÅÅ`, oppgave «Balanseavstemming»).
Fullfør i Tally: se `tally-gjoremal`. «Avstemming balansekontoer» fullføres når alle kontoer over V er OK, FORKLART eller KJENT, ingen stopp står åpen og arket «Modul» er levert; «Balanseavstemming» når alle kontoer er dokumentert per 31.12 og fasen er oppdatert. Kommentaren inneholder periode, antall kontoer, AVVIK-listen, poster per kategori og hva som gjenstår i modulen.

## Fallgruver

- Modulen avstemmer balansen per måned: én termin gir to avstemminger, og årsavstemmingen per 31.12 er en egen periode.
- 19xx og 2700–2739 blir aldri automatisk avstemt i modulen; 2740 først når mva-avstemmingen er fullført, 2600/2610/2770/2771 når lønnsavstemmingen er fullført.
- En konto er «avstemt» først når dokumentasjonen er lastet opp i modulen. `sett-status` setter ikke RECONCILED med differanse. Mer: `references/kontroller.md`.
- `/claimsAndPayments` virker bare når klienten har Altinn-systembruker, og gir av og til 500 (prøv igjen). 403 eller tomt: Tally `list_altinn_innboks` eller kunden.
- `/asset` har ingen dato: avstem registeret mot UB og forklar tilganger og avgang etter D. Bare Tripletex-klienter.

## Referanser

- `references/kontroller.md`: S1–S3, S5–S13, B2–B4, R1, R2, M2, L2, L3, A4, A5, D2, E1. Katalog: `docs/kontrollkatalog.md`. Metode: `docs/avstemmingsmetodikk.md`.
- Naboskills: `bankavstemming`, `reskontroavstemming`, `periodisering`, `mva-innlevering`, `a-melding`, `lonnsavstemming`, `aarsoppgjoer-forberedelse`, `periodeavslutning`.
- Avstemmingsmodulen: `tripletex-api/docs/avstemmingsmodul.md` (Balanse).
