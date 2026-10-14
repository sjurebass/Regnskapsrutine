# Kontoutskrift per motpart (R13)

Steg 7 i `SKILL.md`. På forespørsel, og automatisk for kunder med poster forfalt over 30 dager.
Mønster: `.claude/skills/silfer-rapport/scripts/eksempler/kontoutskrift_reskontro.json`. Alle kall med `--client "<klient>"`; D = første dag etter perioden.

1. IB og UB uavhengig av bevegelsene. Kunde: `npm run -s api -- GET /balanceSheet dateFrom=ÅÅÅÅ-01-01 dateTo=<D> accountNumberFrom=1500 accountNumberTo=1500 customerId=<id> fields=balanceIn,balanceOut`.
   Leverandør (`/balanceSheet` har ikke leverandørfilter): Σ åpne poster (`/ledger/posting/openPost` på 2400 med `supplierId=<id>`) per 1.1 = IB og per D = UB.
2. Bevegelser (leverandør: 2400 og `supplierId`), sortert på dato i skriptet:
   `npm run -s api -- GET /ledger/posting dateFrom=ÅÅÅÅ-01-01 dateTo=<D> accountNumberFrom=1500 accountNumberTo=1500 customerId=<id> fields=date,voucher(number,year),description,amount,invoiceNumber,termOfPayment --sider --ut <mappe>/bevegelser.json`
3. Bevegelser: Dato · Bilag · Tekst · Forfall · Fakturert · Innbetalt (leverandør: Betalt) · Saldo, fra «Inngående saldo» med løpende saldo til «Utgående saldo».
   Fakturarader (kreditnota negativ) er Fakturert, alle andre Innbetalt. Leverandør: fortegn snudd, så gjelden vises positiv.
4. «Åpne poster per <siste dag>»: Dato · Forfall · Fakt.nr. · Tekst · Beløp, med «Sum åpne poster» lik utgående saldo.
5. Kontrollinje: «Kontrollert: inngående saldo X + fakturert Y − innbetalt Z = utgående saldo W, som stemmer».
   **Stemmer ikke summen med uavhengig UB, lages ikke PDF-en.** Rapporter differansen som R13.

Filnavn: `Kontoutskrift kundereskontro <kundenr.> ÅÅÅÅ-MM <Klient>.pdf` (leverandør tilsvarende; nummer, ikke navn).
Kontoutskrift til en privatperson lages bare når brukeren ber om den.
