---
name: "balanseavstemming"
description: "Avstemming av balansekontoer i Tripletex utenom bank og reskontro: saldo per konto mot dokumentasjon (skattetrekkskonto 1950, 2600/2770 mot a-melding, 2740 mot mva, 2940 feriepenger, periodiseringer, lån, mellomregning aksjonær, egenkapital, sovende kontoer), i terminmåneder og per 31.12, med ark klart for avstemmingsmodulen. Lukker Tally-oppgavene «Avstemming balansekontoer» og «Balanseavstemming». Bruk ved «avstem balansen», «balanseavstemming», «avstem balansekontoer», «balansespesifikasjon», «avstem balansekonto <nr>», «mellomregning», «sovende kontoer»."
---

# Balanseavstemming

Én rad per balansekonto med IB, bevegelse, UB, dokumentert saldo, differanse, status og kilde, og et ferdig ark til avstemmingsmodulen.
Bank (19xx) avstemmes i `bankavstemming` og 1500/2400 i `reskontroavstemming`; her brukes bare resultatet derfra som dokumentert saldo.

## Når

- Tally «Avstemming balansekontoer» (16., i terminmåneder: siste måned i hver termin for mva) og «Balanseavstemming» (26.2, hele balansen per 31.12).
- Først: bank lukket for måneden (`bankavstemming`), reskontro avstemt (`reskontroavstemming`), a-melding levert (`a-melding`), i terminmåneder
  også mva levert (`mva-innlevering`). Per 31.12 er `aarsoppgjoer-forberedelse` kjørt; saldobalansen derfra er utgangspunktet.
- Brukeren oppgir klient og periode `ÅÅÅÅ-MM` (standard: siste måned i siste avsluttede termin) eller «31.12 ÅÅÅÅ». Valgfritt: én konto.

## Kundeinstruks

«Regnskapssystem og byrå» (V) · «Bank» (1950, kontoer uten feed) · «Lønn» (direkte trekk eller skattetrekkskonto, feriepengesats) · «Mangelliste»
(konto for manglende bilag) · «Reskontro og balanse» (kontoer avstemt månedlig eller årlig) · «Årsoppgjør» (det som bevisst venter) · «Kjente avvik».

## Steg

Utkast – kalibreres mot første klient. Følg stegene, men si fra om noe ikke stemmer med det verktøyene gir.

### 1. Saldobalanse (ett skript)
Ett `tripletex_run_script`, med D = første dag etter perioden:
- `get_balance_sheet` 1000–2999 og konto for manglende bilag, `dateFrom` 1.1, `dateToExclusive` D, `showAccountsWithoutTransactionsInPeriod: true` → IB, bevegelse, UB.
- Samme kall for de siste 12 månedene → sovende kontoer (A5). `get_accounting_settings` → hvilke kontoer som er reskontro, mva og lønn.
- `get_year_end_status` (år − 1) → fjorårets egenkapital og skatt, brukt som IB-kontroll (S5, S6).
Behold kontoer med UB ≠ 0 eller bevegelse ≠ 0. Kontroller S9 først: går balansen ikke opp, stopp og si at dataene er feil.

### 2. Dokumentert saldo per kontogruppe
Hent i samme skript, eller les resultatet fra naboskillen for samme periode:

| Konto | Dokumentert saldo | Kilde (MCP) |
|---|---|---|
| 19xx | `bankBalance` for måneden (lukket, differanse 0) | `get_bank_reconciliation_periods` / `bankavstemming` |
| 1500 / 2400 | Σ åpne poster per D | `search_open_postings` / `reskontroavstemming` |
| 2740, 2700–2739 | −beløp å betale for levert, ubetalt termin, ellers 0 | `search_ledger_postings` 27xx / `mva-innlevering` |
| 2600 / 2770 | a-meldt minus betalt (`accrued` − betalt) | `get_amelding_status` / `lonnsavstemming` |
| 2940 (2780/2785) | feriepengegrunnlag hittil i år × sats − utbetalt | `search_ledger_postings` 5000–5099 og 2940 |
| 1950 | minst skyldig trekk på 2600 (ikke ved direkte trekk) | `get_balance_sheet` |
| 1700–1799, 2900–2999 | periodiseringsbilag som fortsatt gjelder, ett per post | `search_ledger_postings` |
| 1200–1299 | anleggsregister; årets avskrivning (60xx) bokført | `search_ledger_postings` |
| 13xx / 15xx / 29xx mot aksjonær | låneavtale eller protokoll; debet mot personlig aksjonær er AVVIK | `search_ledger_postings` |
| 2000–2099 | fjorårets UB + protokollførte endringer | `get_year_end_status`, `get_balance_sheet` |
| 2500 / 1570 | fjorårets betalbare skatt − betalt | `search_ledger_postings` |
| 2200–2299 | låneoppgave eller nedbetalingsplan (per 31.12) | dokument fra kunden |
| Konto for manglende bilag (typisk 1370 eller 7799) | 0 | `get_balance_sheet` |

### 3. Status per konto
- OK: differanse under 1 kr og kilden finnes. FORKLART: kjent årsak (betalt etter D, periodisering). KJENT: kjent avvik, samme beløp.
  AVVIK: 1 kr eller mer uten forklaring (over V gir rød port). IKKE AVKLART: ingen dokumentasjon (S1).
- Kontrollene S1–S3, S5–S9, B2–B4, R1, R2, M2, L2, L3, A4, A5, D2 og E1 med utslag og grunnlag: `references/kontroller.md`.
- Sovende kontoer (A5, unntatt egenkapital, langsiktig lån og depositum): foreslå IGNORED i modulen; settes bare etter ja.
- Det kundeinstruksen sier venter til årsoppgjøret, flagges ikke i månedene. Varige svar om en konto tilbys lagret i kundeinstruksen.

### 4. Rettinger (etter ja)
**Krever skriving utenfor MCP: Tripletex-UI (eller API-kobling):**
1. Ompostering fra observasjonskonti, bare med bilaget for akkurat den transaksjonen.
2. Avskrivning, reversering av periodisering eller avsetning: bilag med konto, beløp og dato fra forslagslista.
Vis forslagene nummerert med konto, beløp og bilag før ja, og si «ikke gjort» om det som står igjen.

### 5. Avstemmingsmodulen (etter ja)
**Krever skriving utenfor MCP: Tripletex-UI (eller API-kobling):**
1. Åpne balanseavstemmingen for måneden (per 31.12 også årsavstemmingen).
2. Per konto i arket «Modul»: dokumentert saldo, status (RECONCILED, eller IGNORED etter ja), vedlegg og én setning i kommentaren.
3. Fullfør avstemmingen når alle linjer har status.

### 6. Fil og årsoppgjørsfase
- Spec til `silfer-rapport`: «Sammendrag» (Konto · Navn · IB · Bevegelse · UB · Dokumentert saldo · Differanse · Status · Kilde · Merknad, antall per status, port),
  ark per konto ved behov, «Modul» (Konto · accountId · Status · Dokumentert saldo · Vedlegg · Kommentar) og «Tiltak» (nummerert, med Krever).
- Filnavn `Balanseavstemming ÅÅÅÅ-MM <Klient>.xlsx`; per 31.12 `Balanseavstemming ÅÅÅÅ <Klient>.xlsx` og PDF `Balansespesifikasjon ÅÅÅÅ <Klient>.pdf`.
- Per 31.12, etter ja: Tally `update_arsoppgjor` fase `balanseavstemming` med status og kort notat.

## Svar

- Port (grønn/gul/rød) og antall OK · FORKLART · KJENT · AVVIK · IKKE AVKLART. Maks 10 linjer.
- AVVIK og IKKE AVKLART i funn-formatet: ID · Klient · Periode · Konto · Beløp · Status · Forslag · Krever.
- Til slutt det som står igjen utenfor MCP (rettinger, modulen).
- Mellomregning vises som «aksjonær 1 (rolle)». Aldri navn eller lønn per person.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `BILAG`, periode `ÅÅÅÅ-MM`, samling `Balanseavstemming ÅÅÅÅ`, oppgave «Avstemming balansekontoer»; per 31.12 kategori `ARSOPPGJOR`, periode `ÅÅÅÅ`, samling `Årsoppgjør ÅÅÅÅ`, oppgave «Balanseavstemming»).
Fullfør i Tally: se `tally-gjoremal`. «Avstemming balansekontoer» fullføres når alle kontoer over V er OK, FORKLART eller KJENT og arket «Modul» er levert; «Balanseavstemming» når alle kontoer er dokumentert per 31.12 og fasen er oppdatert. Kommentaren inneholder periode, antall kontoer, AVVIK-listen og hva som gjenstår i modulen.

## Fallgruver

- Modulen avstemmer balansen per måned: én termin gir to avstemminger, og årsavstemmingen per 31.12 er en egen periode.
- 19xx blir aldri automatisk avstemt i modulen, selv med lukket bank og differanse 0. Det blir heller aldri 2700–2739.
- 2740 blir automatisk avstemt først når mva-avstemmingen er fullført; 2600/2610/2770/2771 først når lønnsavstemmingen er fullført.
- En konto er «avstemt» først når dokumentasjonen er lastet opp i modulen.
- Anleggsregisteret og skattekontoen kan ikke leses i MCP-en. Bruk avskrivningsbilagene og brev i Tally `list_altinn_innboks`, eller be kunden om tallene.
- `get_balance_sheet` har eksklusiv sluttdato: D er første dag etter perioden. Bare Tripletex-klienter.

## Referanser

- `references/kontroller.md`: S1–S3, S5–S9, B2–B4, R1, R2, M2, L2, L3, A4, A5, D2, E1. Katalog: `docs/kontrollkatalog.md`.
- Naboskills: `bankavstemming`, `reskontroavstemming`, `mva-innlevering`, `a-melding`, `lonnsavstemming`, `aarsoppgjoer-forberedelse`, `periodeavslutning`.
- Avstemmingsmodulen: `tripletex-api/docs/avstemmingsmodul.md` (Balanse).
