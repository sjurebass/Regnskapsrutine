# Klassifisering av åpne bankposter

Metoden står i `docs/avstemmingsmetodikk.md` (kategorier, alder, eskalering, stopp). Her står hvordan feltene i `status.json` blir
oppstilling, kategori og alder for bank. Utkast for oppstillingen – kalibreres første gang en klient har åpne poster.
S = siste dag i måneden som avstemmes; V fra kundeinstruksen.

## Oppstilling per konto og måned

| Linje | Felt i `status.json` |
|---|---|
| Saldo i banken per S | `bankSaldo` (mangler den: konto uten bankfeed – kontoutskriften er kilden) |
| ± i transitt (bokført, ikke i banken) | `tx.sum` (umatchede posteringer i hovedboken) |
| = Justert saldo bank | `bankSaldo + tx.sum` |
| Saldo i hovedboken per S | `ub` |
| ± i banken, ikke bokført | Σ `bank[].belop` (umatchede bankposter) |
| = Justert saldo hovedbok | `ub + Σ bank[].belop` |
| Uforklart differanse | justert bank − justert hovedbok = `tx.sum − differanse − Σ bank[].belop` (`differanse` = `ub − bankSaldo`); skal være 0,00 |

- Summer `tx` og `bank[]` over alle åpne måneder til og med S. Matchforslag (`forslag`) ligger på begge sider og går mot hverandre.
- Går oppstillingen ikke i 0,00, let først etter poster fra lukkede måneder. Kallet gir siste lukkede avstemming som fortsatt har
  umatchede transaksjoner (`value`; `null` = ingen):
  `npm run -s api -- GET /bank/reconciliation/closedWithUnmatchedTransactions accountId=<konto-id> start=ÅÅÅÅ-01-01 fields=id,accountingPeriod(start,end),closedDate --client "<klient>"`.

## Kategori per post

Første rad som passer, gjelder.

| Post | Kategori | Hvor · Krever |
|---|---|---|
| Kjent avvik i kundeinstruksen, samme beløp | KJENT | – |
| Linje i `bank[]` med motpost på den andre siden (samme beløp og dato), eller i `forslag` | Ingen avstemmingspost | Internt: match (skriving 1) eller godkjenn forslaget (UI) |
| Postering i `tx` datert i siste del av måneden, uten bankpost ennå | 1 Tidsforskjell | Internt · – |
| Linje i `bank[]` med dokument i bilagsmottaket | 2 Krever føring | Internt: `bilagsforing` · ja i chat |
| Gebyr, renter, overføring mellom egne kontoer («Fylt på») | 2 Krever føring | Internt: `periodisering` (`bilag manuell`; 7770, 8050, motkonto 19xx) · ja i chat |
| Linje i `bank[]` uten motpost og uten dokument | 2 Krever føring | **Fra kunden**: bilag mangler (Excel) · kunden |
| Postering i `tx` som ikke er gått av ved neste avstemming, eller eldre enn 30 dager | 3 Må undersøkes | Internt · regnskapsfører |
| Bankpost over 60 dager, retur, ukjent innbetaling eller omtvistet beløp | 3 Må undersøkes | regnskapsfører; over V oppdragsansvarlig |
| Konto uten bankfeed der kontoutskriften mangler | IKKE AVKLART | **Fra kunden**: kontoutskrift · kunden |

## Alder og eskalering

- Alder = S − `bank[].dato` (eller posteringsdatoen for `tx`), i aldersgruppene 0–30, 31–60, 61–90 og over 90 dager.
- Enkeltpost over V/2: Krever `regnskapsfører`. Over V: Krever `oppdragsansvarlig`. Over 90 dager: oppdragsansvarlig uansett kategori.
- Funn-format: Forslag begynner med kategori og alder, for eksempel `Kat. 2 · 31–60 · bilag mangler, etterlyst i Excel`.

## Kontroller

| ID | Kontroll | Utslag |
|---|---|---|
| B1 | Åpne bankposter per konto og måned | Poster eldre enn 30 dager |
| B5 | Gamle åpne poster | Over 90 dager → oppdragsansvarlig |
| B6 | Oppstilling: justert saldo bank = justert saldo hovedbok | Uforklart differanse ≠ 0,00 → stopp |
| B7 | Kategori og alder for hver åpen post | Kategori 3 over V → stopp; over V/2 → regnskapsfører |
| B8 | Trend mot forrige måned | Sum over V, antall økt tre måneder på rad, eller samme post tre måneder på rad → prosessavvik |
