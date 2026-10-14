# Kontroller – balanseavstemming

Utkast – kalibreres mot første klient. ID-ene står også i `docs/kontrollkatalog.md`. V er vesentlighetsgrensen fra kundeinstruksen,
D er første dag etter perioden. Hvert funn rapporteres i funn-formatet (`docs/skill-mal.md`) med status OK, AVVIK, FORKLART, KJENT eller IKKE AVKLART.

Rekkefølge: S9 først (stopper alt), så kontogruppene i den rekkefølgen balansen står, og til slutt S1 over alle kontoer.
Stier er `npm run -s api -- GET <sti> …` (se steg 1 i SKILL.md); kommandoer er `npm run -s <kommando> -- …`.

| ID | Kontroll | Utslag | Data (API) | Grunnlag |
|---|---|---|---|---|
| S9 | Balansen går opp: Σ eiendeler = Σ egenkapital og gjeld inkl. udisponert resultat; IB = fjorårets UB | Avvik → stopp (dataene er feil) | `/balanceSheet` 1000–8999 (i år og år − 1) | bokf.l. § 11 |
| B2 | 19xx: banken lukket for måneden, bankens sluttsaldo = UB | Ikke lukket eller differanse → AVVIK, `bankavstemming` | `bankavstemming` (`status.json`: lukket, sluttsaldo, differanse), `status` | bokf.l. § 11 |
| B3 | 19xx med bevegelse og ingen avstemming startet | AVVIK → `bankavstemming` | `bankavstemming` (`status.json`: avstemming mangler) | GRFS: avstemming ved pliktig rapportering |
| B4 | Negativ bank eller kasse uten kredittramme | AVVIK | `/balanceSheet` | bokf.l. § 11 |
| R1 / R2 | 1500 / 2400 = Σ åpne poster per D | Differanse ≥ 1 kr → AVVIK, `reskontroavstemming` | `/ledger/posting/openPost`, `/balanceSheet`, `status` | bokf.l. § 11; GRFS |
| A4 | 1200–1299: anleggsregisteret = UB, avskrivning bokført for perioden, tilgang ≥ 30 000 kr aktivert (ikke kostnadsført på 65xx), avgang ført | Mangler → AVVIK | `/asset`, `/asset/balanceAccountsSum`, `/ledger/posting` 1200–1299, 6000–6099 og 65xx | rskl. § 5-3; sktl. § 14-40 |
| S8 | 1400–1499 varelager = telling per 31.12 (bare når kundeinstruksen sier varelager) | Mangler telling → kunden | `/balanceSheet`; lagerliste fra kunden | rskl. § 5-2 |
| S3 | 1700–1799 og 2900–2999: hver post har bilag og gjelder fortsatt; forskudd kostnadsføres, avsetninger reverseres; ingen mva på periodiseringsbilag | Post eldre enn 12 måneder uten bevegelse → spørsmål | `/ledger/posting` | rskl. § 4-1 |
| E1 | 13xx/15xx/29xx: saldo mot aksjonær har låneavtale og renter; konsernmellomværende = motpartens saldo | Debet mot personlig aksjonær → AVVIK (spør) | `/ledger/posting` | sktl. § 10-11 (4); asl. § 8-7 |
| S5 | 2000–2099: bevegelse bare med protokoll (utbytte, kapitalendring); 2000 = aksjekapital; IB = fjorårets UB etter disponering | Avvik → AVVIK | `/balanceSheet` (i år og år − 1) | asl. §§ 3-1, 8-1 |
| S7 | 2200–2299 = låneoppgave eller nedbetalingsplan (per 31.12); renter bokført | Avvik → AVVIK | `/balanceSheet`; årsoppgave fra kunden | bokf.l. § 11 |
| S6 | 2500/1570: IB = fjorårets betalbare skatt; bevegelse = betalt forskudds- og restskatt; 0 etter betaling (per 31.12: ny avsetning) | Avvik → AVVIK | `/balanceSheet`, `/ledger/posting`, `/claimsAndPayments` (skattekontoen) | sktbetl. §§ 10-20, 10-21 |
| L2 | 2600/2770 = a-meldt minus betalt; ubetalt beløp forfaller den 15.; 2600 i debet = for mye innbetalt | Differanse → AVVIK eller FORKLART | `amelding status --maned` (påløpt og ubetalt) | sktbetl. § 10-10 |
| S2 | 1950 minst lik skyldig trekk på 2600 (ikke ved direkte trekk; samme som L8) | 1950 lavere → AVVIK | `/balanceSheet` | sktbetl. § 5-12 |
| L3 | 2940 = feriepengegrunnlag hittil i år × sats (fra kundeinstruksen) − utbetalt; 2780/2785 arbeidsgiveravgift av feriepenger | Avvik > 1 % → AVVIK | `/ledger/posting` 5000–5099, 2940, 2785 | ferieloven § 10 |
| M2 | 2740 = −beløp å betale for levert, ubetalt termin, ellers 0; 2700–2739 = 0 etter oppgjørsbilaget | Restsaldo → AVVIK | `mva status` (levert, betalt, saldo 2740), `/ledger/posting` 27xx, Tally `list_altinn_innboks` | mval. § 15-9 |
| D2 | Konto for manglende bilag og andre observasjonskonti (typisk 1370, 7799) = 0 | ≠ 0 → forslag om ompostering | `status` (observasjonskonti), `/balanceSheet` | bokf.l. § 7 |
| A5 | Sovende kontoer: UB ≠ 0 og ingen bevegelse på 12 måneder (unntatt egenkapital, langsiktig lån, depositum) | Liste → vurder, eller IGNORED etter ja | `/balanceSheet` (to perioder) | GRFS: avstemming av balanseposter |
| S1 | Alle kontoer med UB over V har dokumentert saldo og kilde | Mangler kilde → IKKE AVKLART | alle over | GRFS: dokumentert avstemming; bokf.l. § 11 |

## Terskler

- OK når differansen er under 1 kr. AVVIK over V gir rød port; AVVIK under V gir gul.
- Kjent avvik i kundeinstruksen med samme beløp: KJENT. Nytt beløp: nytt funn.
- Det kundeinstruksen sier venter til årsoppgjøret, flagges ikke i månedene, men tas med per 31.12.

## Avstemmingsmodulen (arket «Modul»)

- BALANCE er månedlig (`term` = måned); én termin for mva gir to avstemminger. ANNUAL_BALANCE per 31.12 er egen og gjøres i Tripletex-UI.
- Linjene har ingen egen id; `accountId` er kontoens id hos klienten. Status: NOT_RECONCILED, RECONCILED, IGNORED (og CONTROLLED/REJECTED).
- Kommandoer: `modul perioder|linjer|vedlegg` (lesing), `modul sett-status|last-opp|fullfor` (skriving med `--bekreft`). Kommentarer skrives i UI.
- Automatisk: 2740 etter fullført mva-avstemming; 2600/2610/2770/2771 etter fullført lønnsavstemming. Aldri automatisk: 19xx, 2700–2739.
- Kommentar: én kort setning med årsaken, som en regnskapsfører skriver den. Vedlegg: kontoutskrift, låneoppgave, beregning.
