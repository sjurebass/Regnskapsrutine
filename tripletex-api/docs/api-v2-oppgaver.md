# Tripletex API v2 – oppgaver og oppskrifter

Spec 2.75.11, bygget 2026-10-12. 454 oppgaver. ✏️ = skrivende (krever bekreftelse).

## MVA / merverdiavgift

### Hente MVA-innstillinger for en klient (er selskapet mva-registrert, hvilke koder er aktivert?)
- **Kall:** `GET /ledger/vatSettings`
- **Nøkkelord:** mva-innstillinger, mva-registrert, er klienten mva-registrert, merverdiavgiftsregisteret, registreringsstatus, aktiverte mva-koder, vat settings, vatsettings
- Ingen påkrevde parametere – kjøres mot valgt klient. GET /ledger/vatSettings?fields=id,version,vatRegistrationStatus,hasVatOutInside,hasVatOutOutside,hasVatOutNoneInside,hasVatOutMedium,hasVatOutLow,hasVatOutExportNone,hasVatInMedium,hasVatInImport,hasVatInHighForeignServices,hasVatInLowForeignServices,hasVatInFish,hasVatOutFish,hasVatInAndOutReverseDuty,hasAdjustmentVat,hasWithdrawalVat,hasDrawbackVat,hasCompensationCodes. vatRegistrationStatus: VAT_NOT_REGISTERED | VAT_APPLICANT | VAT_REGISTERED | VAT_COMPENSATION. has*-flaggene viser hvilke mva-koder som er aktivert (f.eks. hasVatOutMedium = kode 31). Kombiner med GET /vatTermSizeSettings for terminlengde.

### ✏️ Aktivere eller deaktivere mva-koder/omsetningstyper (f.eks. 15 % næringsmidler, import, tjenester fra utlandet, uttak)
- **Kall:** `GET /ledger/vatSettings`, `PUT /ledger/vatSettings`
- **Nøkkelord:** aktivere mva-kode, slå på mva-kode, sla pa mva-kode, middels sats, næringsmiddel, matmoms, lav sats, persontransport, eksport, import, tjenester fra utlandet, snudd avregning, uttak, justering, tilbakeføring, gull, klimakvoter, endre mva-innstillinger
- 1) GET /ledger/vatSettings for å hente hele objektet inkl. id og version. 2) PUT /ledger/vatSettings med hele objektet (id, version, vatRegistrationStatus og alle has*-flagg), der bare ønskede flagg endres – send med eksisterende verdier så ingenting nullstilles. Kobling flagg → kode: hasVatOutInside (salg innenfor mva-loven), hasVatOutNoneInside→5, hasVatOutOutside→6, hasVatOutMedium→31, hasVatOutLow→33, hasVatOutExportNone→52, hasVatInMedium→11, hasVatInImport→14/15/20/21, hasVatInHighForeignServices→86/87, hasVatInLowForeignServices→88/89, hasVatInFish→12, hasVatOutFish→32, hasVatInAndOutReverseDuty→51/91/92, hasAdjustmentVat/hasWithdrawalVat/hasDrawbackVat → justerings-/uttaks-/tilbakeføringskoder, hasCompensationCodes → kompensasjonskoder. Skrivende – bekreft med bruker før PUT.

### ✏️ Endre mva-registreringsstatus (ny registrering i Merverdiavgiftsregisteret, søker, kompensasjon eller avregistrering)
- **Kall:** `GET /ledger/vatSettings`, `PUT /ledger/vatSettings`, `GET /vatTermSizeSettings`, `POST /vatTermSizeSettings`
- **Nøkkelord:** registrere i mva-registeret, mva-registrering, ny mva-registrering, søkt mva-registrering, sokt mva-registrering, avregistrere mva, slettet fra mva-registeret, mva-kompensasjon, kompensasjonsordning, frivillige organisasjoner, vat registration status
- 1) GET /ledger/vatSettings (id, version). 2) PUT /ledger/vatSettings med vatRegistrationStatus = VAT_REGISTERED | VAT_APPLICANT | VAT_COMPENSATION | VAT_NOT_REGISTERED (send hele objektet). 3) Ved ny registrering: GET /vatTermSizeSettings og opprett ev. termin fra registreringsdato: POST /vatTermSizeSettings {reportType:'GENERAL_INDUSTRY', fromDate:'yyyy-MM-dd', termSize:'TWO_MONTHS'}. Ved avregistrering: POST med termSize:'NOT_REGISTERED' fra dato. Endringen styrer hvilke mva-koder som er lovlige på bilag – bekreft alltid med bruker.

### Liste alle mva-koder med sats og fradragsprosent
- **Kall:** `GET /ledger/vatType`
- **Nøkkelord:** mva-koder, liste mva-koder, alle mva-koder, mva-satser, oversikt mva, avgiftskoder, vat types, vat codes, kodeliste
- GET /ledger/vatType?count=1000&sorting=number&fields=id,number,name,displayName,percentage,deductionPercentage,parentType(id,number). number = mva-koden (SAF-T-standardkode, f.eks. '3'), id = intern Tripletex-id som brukes som vatType:{id} på posteringer, produkter og kontoer – de er ikke nødvendigvis like. Legg til shouldIncludeSpecificationTypes=true for å få med spesifikasjonskoder (uttak, justering, tilbakeføring). parentType er satt på relative koder (forholdsmessig fradrag).

### Finne riktig mva-kode (id) for et kodenummer eller en transaksjonstype på en gitt dato
- **Kall:** `GET /ledger/vatType`, `GET /ledger/vatType/{id}`
- **Nøkkelord:** hvilken mva-kode, riktig mva-kode, mva-kode for salg, mva-kode for kjøp, mva-kode for kjop, gyldige mva-koder, mva-kode id, kode 1, kode 3, kode 5, kode 6, kode 31, kode 33, kode 86, satsendring, vattypeid, momskode, kode 81, kode 14
- Slå opp id fra kodenummer: GET /ledger/vatType?number=3&fields=id,number,name,percentage (number tar kommaseparert liste, f.eks. number=1,3,5). Gyldige koder for en transaksjonstype på en dato: typeOfVat=OUTGOING (salg) | INCOMING (kjøp/bilag) | INCOMING_INVOICE (leverandørfaktura) | PROJECT | LEDGER, kombinert med vatDate=yyyy-MM-dd (vatDate virker bare sammen med typeOfVat; default i dag). Én kode: GET /ledger/vatType/{id}. Gjør dette før føring av bilag, oppretting av produkt eller setting av standardkode på konto.

### ✏️ Opprette relativ mva-kode for forholdsmessig fradrag av inngående mva
- **Kall:** `GET /ledger/vatType`, `PUT /ledger/vatType/createRelativeVatType`
- **Nøkkelord:** forholdsmessig fradrag, delvis fradrag, fradragsandel, blandet virksomhet, felleskostnader, relativ mva-kode, relative vat type, fordelingsnøkkel, fordelingsnokkel, fradragsprosent, inngående mva delvis
- 1) Finn basiskoden: GET /ledger/vatType?number=1&fields=id,number,name,percentage (f.eks. fradrag inngående 25 %). 2) PUT /ledger/vatType/createRelativeVatType?name=<maks 8 tegn>&vatTypeId=<id>&percentage=<andel, f.eks. 60>. Alle tre er påkrevde query-parametere, ingen body (action-endepunkt med PUT). Den nye koden oppfører seg som basiskoden, men fradragsgrunnlaget = percentage % av beløpet (vises som deductionPercentage). Brukes ved blandet avgiftspliktig/ikke-avgiftspliktig virksomhet. Skrivende – bekreft først.

### Sjekke status på MVA-meldingen for én termin (levert og betalt?)
- **Kall:** `GET /vatReturns/status`
- **Nøkkelord:** status mva-melding, er mva levert, er mva-meldingen sendt, levert mva, mva betalt, kvittering altinn, mva-termin status, termin 1, termin 2, termin 3, termin 4, termin 5, termin 6, forrige termin, vat return status, momsmelding status, er moms levert
- GET /vatReturns/status?year=2026&term=4&reportType=GENERAL_INDUSTRY&fields=year,term,vatReturns2022Id,voucherNumber,totalAmountVatBasis,altinnPaymentAmount,deliveryStatus(status,time),paymentStatus(status,totalAmount,remainingAmount,paymentDate). Uten year/term returneres forrige termin. term = terminnummer i året og følger terminlengden i /vatTermSizeSettings (tomånedlig 1–6, f.eks. 4 = juli–august; månedlig 1–12; årstermin 1). deliveryStatus.status: NOT_STARTED, NOT_SENT, SENDING, WAITING_FOR_REPLY, RECEIPT_RECEIVED (levert), MANUAL_DELIVERY, DELIVERY_FORBIDDEN, FAILED. paymentStatus.status: NOT_STARTED, NOT_PAID, NO_TAX_TO_PAY, AMOUNT_CREDITED (til gode), PAYMENT_REGISTERED. voucherNumber=0 = terminen er ikke lukket. Ikke hent employee-feltene (personopplysninger).

### Oversikt over alle MVA-terminer i et år (status, grunnlag og betaling)
- **Kall:** `GET /vatReturns/status/list`
- **Nøkkelord:** mva-oversikt, alle terminer, mva hele året, terminoversikt, mva-status liste, mva i år, leverte mva-meldinger, vat status list
- GET /vatReturns/status/list?startDate=2026-01-01&endDate=2027-01-01&reportType=GENERAL_INDUSTRY&fields=year,term,voucherNumber,totalAmountVatBasis,altinnPaymentAmount,deliveryStatus(status),paymentStatus(status,totalAmount,remainingAmount,paymentDate). startDate inkl., endDate eksklusiv; default = inneværende år. Terminer som slutter før 2022-01-01 utelates (status finnes bare for ny mva-melding fra 2022). Bruk reportType=PRIMARY_INDUSTRY for primærnæringsmeldingen.

### MVA-frister og status på tvers av klienter (hvilke meldinger er ikke levert eller ikke betalt?)
- **Kall:** `GET /ledger/vatSettings`, `GET /vatReturns/status/list`, `GET /vatTermSizeSettings`
- **Nøkkelord:** mva-frister, mva frist, ikke levert mva, mangler mva-melding, alle klienter mva, klientoversikt mva, frist 10. april, frist 10. juni, frist 31. august, frist 10. oktober, frist 10. desember, frist 10. februar, oppfølging mva, vat deadlines, frist 10. mars, mva-frist oversikt
- Bare når brukeren eksplisitt ber om alle (eller navngitte) klienter: hent klientlisten dynamisk (npm run connect / connect()), og for hver klient: GET /ledger/vatSettings?fields=vatRegistrationStatus (hopp over VAT_NOT_REGISTERED), GET /vatTermSizeSettings?fields=reportType,fromDate,termSize, deretter GET /vatReturns/status/list for perioden med fields=year,term,deliveryStatus(status),paymentStatus(status,remainingAmount). Flagg deliveryStatus NOT_STARTED/NOT_SENT/FAILED og paymentStatus NOT_PAID. Frister alminnelig tomånedlig termin: 10.4, 10.6, 31.8, 10.10, 10.12, 10.2; årstermin alminnelig næring: 10.3 året etter; primærnæring (årsmelding): 10.4 året etter – bruk reportType=PRIMARY_INDUSTRY for primærnæringsmeldingen. Kun lesing.

### Finne skyldig/ubetalt mva og restbeløp per termin
- **Kall:** `GET /vatReturns/status/list`, `GET /balanceSheet`
- **Nøkkelord:** skyldig mva, ubetalt mva, restbeløp mva, restbelop mva, mva til betaling, mva til gode, tilgodebeløp, betalt mva, skyldig merverdiavgift, oppgjørskonto mva, 2740
- 1) GET /vatReturns/status/list?startDate&endDate&fields=year,term,altinnPaymentAmount,paymentStatus(status,totalAmount,remainingAmount,paymentDate) – filtrer på paymentStatus.status=NOT_PAID eller remainingAmount≠0. altinnPaymentAmount = beløp ifølge Skatteetaten (null før levering). 2) Kontroller mot saldo på oppgjørskonto for mva: GET /balanceSheet?dateFrom=yyyy-MM-dd&dateTo=yyyy-MM-dd&accountNumberFrom=2740&accountNumberTo=2740&fields=account(number,name),balanceIn,balanceChange,balanceOut (dateFrom/dateTo påkrevd, dateTo eksklusiv; kontonummer kan variere – sjekk kontoplanen).

### Hente mva-oppgjørsbilaget for en avsluttet termin
- **Kall:** `GET /vatReturns/status`, `GET /ledger/voucher`, `GET /ledger/posting`
- **Nøkkelord:** mva-oppgjør, mva-oppgjor, oppgjørsbilag, mva-bilag, avsluttet termin, lukket termin, bilagsnummer mva, mva-postering, overføring til oppgjørskonto
- 1) GET /vatReturns/status?year&term&fields=voucherNumber,deliveryStatus(status). voucherNumber=0 betyr at terminen ikke er lukket. 2) GET /ledger/voucher?number=<voucherNumber>&dateFrom=<terminstart>&dateTo=<dato etter lukking>&fields=id,number,date,description,postings(account(number,name),amount) – dateFrom/dateTo er påkrevd og bilagsnummer er bare unike innen året, så velg et datointervall som dekker lukkedatoen. 3) Ev. GET /ledger/posting?dateFrom&dateTo&accountNumberFrom=2700&accountNumberTo=2749&fields=voucher(number),date,account(number),amount for posteringene mot mva-kontoene.

### Avstemme mva-kontoene mot MVA-meldingen for en termin (mva-avstemming)
- **Kall:** `GET /ledger/account`, `GET /balanceSheet`, `GET /vatReturns/status`, `GET /ledger/posting`
- **Nøkkelord:** mva-avstemming, mva avstemming, avstemme mva, avstemming merverdiavgift, utgående mva konto, inngående mva konto, 2700, 2710, 2740, saldobalanse mva, differanse mva, avvik mva, terminavstemming
- 1) Finn mva-kontoene: GET /ledger/account?number=2700,2701,2702,2703,2710,2711,2712,2713,2740&fields=id,number,name (typisk 27xx – sjekk klientens kontoplan). 2) GET /balanceSheet?dateFrom=<terminstart>&dateTo=<dagen etter terminslutt>&accountNumberFrom=2700&accountNumberTo=2749&fields=account(number,name),balanceIn,balanceChange,balanceOut. 3) Sammenlign med GET /vatReturns/status (totalAmountVatBasis, paymentStatus.totalAmount, altinnPaymentAmount). 4) Ved avvik: GET /ledger/posting?dateFrom&dateTo&accountId=<id>&fields=voucher(number),date,description,amount,vatType(number) for å finne posteringer ført etter lukking eller med feil kode. dateTo er alltid eksklusiv.

### Kontrollere mva-grunnlag per kode og finne posteringer med feil mva-kode i en periode
- **Kall:** `GET /ledger/posting`, `GET /ledger/postingByDate`, `GET /ledger/vatType`
- **Nøkkelord:** mva-grunnlag, grunnlag per mva-kode, feil mva-kode, kontroll mva, mva-kontroll, mva-spesifikasjon, posteringer med mva, manglende mva, mva på kostnad, fradrag uten rett, representasjon mva, vat basis
- GET /ledger/posting?dateFrom=yyyy-MM-dd&dateTo=yyyy-MM-dd&count=10000&fields=id,date,voucher(number),account(number,name),vatType(number),amount,amountGross,description (dateFrom/dateTo påkrevd, bla med from/count). Grupper på vatType.number for grunnlag per kode og let etter uventede kombinasjoner: salgskonto 3xxx med kode 0, kostnad med fradrag der fradrag ikke er tillatt (representasjon, personbil), utenlandske tjenester uten 86/87. Store datamengder: GET /ledger/postingByDate?dateFrom&dateTo&from&count (raskere, men fields og changes støttes IKKE – hele PostingDTO returneres; krever tilgang til alle bilag (og lønn hvis lønnstilgangskontroll er på), ellers valideringsfeil). Map kodene med GET /ledger/vatType?fields=id,number,name,percentage.

### Hente strukturerte merknader (standardkommentarer) til MVA-meldingen
- **Kall:** `GET /vatReturns/comment/>all`, `GET /vatReturns/comment`
- **Nøkkelord:** merknad mva-melding, strukturerte merknader, kommentar mva, forklaring avvik, tap på krav, uttak, justering, tilbakeføring, kompensasjon, merknad per mva-kode, vat return comments
- BETA. GET /vatReturns/comment/>all?fields=title,technicalName,description,vatSpecificationType,expectedSign gir alle tilgjengelige merknader (vatSpecificationType: DEFAULT | LOSS_OF_CLAIM | WITHDRAWAL | ADJUSTMENT | REVERSAL | COMPENSATION; expectedSign: ZERO | POSITIVE | NEGATIVE). GET /vatReturns/comment?fields=vatCode,comments(title,technicalName,vatSpecificationType,expectedSign) gir merknadene gruppert per mva-kode – til tross for summary finnes det ingen vatCode-parameter; filtrer på vatCode i svaret. Kun lesing – API v2 har ikke kall for å knytte merknad til en melding; det gjøres i Tripletex. Stien inneholder '>' (skrives bokstavelig, URL-koding til %3E fungerer også).

### Sjekke terminlengde for MVA (tomånedlig, månedlig, årstermin)
- **Kall:** `GET /vatTermSizeSettings`, `GET /vatTermSizeSettings/{id}`
- **Nøkkelord:** terminlengde, hvilken termin, tomånedlig, tomanedlig, månedlig mva, manedlig mva, årstermin, arstermin, terminvis, mva-periode, term size
- GET /vatTermSizeSettings?sorting=fromDate&fields=id,version,reportType,fromDate,termSize. Gjeldende terminlengde = siste rad med fromDate ≤ aktuell dato for riktig reportType (GENERAL_INDUSTRY = alminnelig næring, PRIMARY_INDUSTRY = primærnæring). termSize: ONE_MONTH, TWO_MONTHS (standard), THREE_MONTHS, FOUR_MONTHS, SIX_MONTHS, YEAR (årstermin), NOT_REGISTERED. Terminnummeret i /vatReturns/status følger denne innstillingen. Én rad: GET /vatTermSizeSettings/{id}.

### ✏️ Endre terminlengde (f.eks. bytte til årstermin eller månedlig fra en dato)
- **Kall:** `GET /vatTermSizeSettings`, `POST /vatTermSizeSettings`, `PUT /vatTermSizeSettings/{id}`
- **Nøkkelord:** endre termin, bytte til årstermin, bytte til arstermin, søke årstermin, månedlig termin, manedlig termin, tomånedlig termin, ny terminlengde, endre terminlengde, update term size
- Forutsetter at endringen er godkjent av Skatteetaten (årstermin: omsetning under 1 mill. kr; månedlig: typisk jevnlig mva til gode). Ny periode: POST /vatTermSizeSettings {reportType:'GENERAL_INDUSTRY', fromDate:'2027-01-01', termSize:'YEAR'} – fromDate bør være første dag i en termin/år. Rette eksisterende rad: GET /vatTermSizeSettings for id+version, så PUT /vatTermSizeSettings/{id} med id, version, reportType, fromDate, termSize. Ikke endre bakover for terminer som allerede er levert. Skrivende – bekreft først.

### ✏️ Slette feilregistrert terminlengde-innstilling
- **Kall:** `GET /vatTermSizeSettings`, `DELETE /vatTermSizeSettings/{id}`
- **Nøkkelord:** slette termininnstilling, fjerne terminlengde, feil termin, delete vat term, rette termin
- Finn riktig id med GET /vatTermSizeSettings?fields=id,reportType,fromDate,termSize. DELETE /vatTermSizeSettings/{id}. Kun for feilregistrerte rader uten leverte terminer – sletting kan endre terminberegningen bakover i tid. Krever eksplisitt bekreftelse fra bruker.

### Hente MVA-status og terminer for primærnæring (landbruk, skogbruk, fiske)
- **Kall:** `GET /vatTermSizeSettings`, `GET /vatReturns/status/list`, `GET /vatReturns/status`, `GET /ledger/postingRules`
- **Nøkkelord:** primærnæring, primarnaering, landbruk, jordbruk, bonde, skogbruk, fiske, fiskeri, årstermin primærnæring, primary industry, to mva-meldinger
- Sjekk om klienten har flere næringer: GET /ledger/postingRules?fields=multipleIndustries,defaultBusinessActivityTypeId. Terminlengde: GET /vatTermSizeSettings (reportType=PRIMARY_INDUSTRY, vanligvis termSize=YEAR). Status: GET /vatReturns/status/list?startDate&endDate&reportType=PRIMARY_INDUSTRY eller GET /vatReturns/status?year&term&reportType=PRIMARY_INDUSTRY (reportType er case-insensitiv; default GENERAL_INDUSTRY – glem ikke parameteren, ellers får du alminnelig næring). Frist for årsmelding i primærnæring er 10. april året etter.

### ✏️ Sjekke eller endre standard mva-kode på en konto (mva-låsing)
- **Kall:** `GET /ledger/account`, `GET /ledger/vatType`, `PUT /ledger/account/{id}`
- **Nøkkelord:** mva-kode på konto, mva pa konto, standard mva-kode, låst mva-kode, last mva-kode, vatlocked, lovlige mva-koder, kontoplan mva, konto mva-innstilling, legal vat types
- GET /ledger/account?number=3000&fields=id,version,number,name,vatType(id,number,name),vatLocked,legalVatTypes(number) – legalVatTypes = koder som er tillatt på kontoen. Endre: GET /ledger/vatType?number=3&fields=id for vatType-id, så PUT /ledger/account/{id} med id, version, number, name, vatType:{id}, vatLocked:true/false (vatLocked=true tvinger koden på alle posteringer på kontoen). Skrivende – bekreft før PUT.

### ✏️ Endre mva-kode på produkter (f.eks. næringsmidler til 15 % eller tjenester til 25 %)
- **Kall:** `GET /ledger/vatType`, `GET /product`, `PUT /product/{id}`, `PUT /product/list`
- **Nøkkelord:** mva på produkt, mva pa produkt, produkt mva-kode, endre mva-sats produkt, matmoms, næringsmiddel, 15 %, 25 %, 12 %, priser inkl. mva, priser eks. mva, vare mva
- 1) Kode-id: GET /ledger/vatType?number=31&typeOfVat=OUTGOING&fields=id,number,name,percentage. 2) Finn produktene: GET /product?vatTypeId=<gammel id>&fields=id,version,number,name,vatType(number),priceExcludingVatCurrency,priceIncludingVatCurrency,isRoundPriceIncVat. 3) PUT /product/{id} med id, version, vatType:{id} (ev. PUT /product/list for mange). Vurder om pris ekskl. eller inkl. mva skal holdes fast. Skrivende – bekreft først.

### ✏️ Føre bilag med mva (manuell postering med mva-kode)
- **Kall:** `GET /ledger/account`, `GET /ledger/vatType`, `GET /vatReturns/status`, `POST /ledger/voucher`
- **Nøkkelord:** føre bilag med mva, fore bilag med mva, postering med mva, manuelt bilag mva, inngående mva bilag, fradrag mva, bokføre kvittering, bilag mva-kode, voucher vat
- 1) Konto-id: GET /ledger/account?number=6800,1920&fields=id,number,vatType(number),vatLocked. 2) vatType-id: GET /ledger/vatType?number=1&typeOfVat=INCOMING&vatDate=<bilagsdato>&fields=id,number. 3) Sjekk at terminen er åpen (GET /vatReturns/status → voucherNumber=0). 4) POST /ledger/voucher {date, description, postings:[{row:1, date, account:{id}, amountGross:1250, amountGrossCurrency:1250, vatType:{id}}, {row:2, date, account:{id:<bank/motkonto>}, amountGross:-1250, amountGrossCurrency:-1250}]}. Bare bruttobeløp brukes – Tripletex genererer selv mva-posteringen på 27xx. Sum amountGross = 0, row starter på 1 (row 0 er systemgenerert). Skrivende – bekreft først.

### ✏️ Føre kjøp av tjenester fra utlandet eller import av varer (snudd avregning / omvendt avgiftsplikt)
- **Kall:** `GET /ledger/vatSettings`, `PUT /ledger/vatSettings`, `GET /ledger/vatType`, `POST /ledger/voucher`
- **Nøkkelord:** snudd avregning, omvendt avgiftsplikt, tjenester fra utlandet, kjøp fra utlandet, kjop fra utlandet, import, innførsel, innforsel, innførselsmva, tollmva, tolldeklarasjon, kode 86, kode 87, kode 14, kode 21, reverse charge, utenlandsk leverandør, kode 81, kode 82, kode 83, innførselsmva beregnet selv, speditør, tollfaktura
- 1) Sjekk at kodene er aktivert: GET /ledger/vatSettings (hasVatInHighForeignServices → 86/87, hasVatInLowForeignServices → 88/89, hasVatInImport → 14/15/20/21, hasVatInAndOutReverseDuty → 51/91/92). Aktiver ev. via PUT /ledger/vatSettings (bekreft). 2) GET /ledger/vatType?number=86&typeOfVat=INCOMING&vatDate=<dato>&fields=id,number,name. 3) POST /ledger/voucher med kostnadsposteringen på vatType 86 (med fradrag) eller 87 (uten fradrag) – Tripletex beregner både utgående og inngående mva (netto 0 ved fullt fradrag). Import av varer: mva-registrerte importører beregner normalt innførselsmva selv (SAF-T-kode 81/83 med fradrag, 82/84 uten fradrag, 85 nullsats) på verdien fra tolldeklarasjonen; 14/15 brukes når innførselsmva er betalt til Tolletaten, 20/21 er grunnlagskoder. Tripletex sine kodenummer/navn kan avvike – verifiser med GET /ledger/vatType?number=14,15,20,21,81,82,83,84,85&typeOfVat=INCOMING&vatDate=<dato>&fields=id,number,name,percentage,deductionPercentage. For ikke mva-registrerte kobler hasVatInImport bare kodene 20, 21, 22, 82, 84, 85 og hasVatInHighForeignServices bare kode 87. Skrivende – bekreft først.

### ✏️ Korrigere feil mva-kode på et bokført bilag
- **Kall:** `GET /vatReturns/status`, `GET /ledger/voucher/{id}`, `PUT /ledger/voucher/{id}/:reverse`, `POST /ledger/voucher`, `PUT /supplierInvoice/voucher/{id}/postings`
- **Nøkkelord:** korrigere mva, rette mva-kode, feil mva-kode, endre mva på bilag, tilbakeføre bilag, reversere bilag, motpostere, låst periode, last periode, lukket termin, mva-korreksjon, korrigert mva-melding
- 1) Sjekk terminen: GET /vatReturns/status?year&term (voucherNumber>0 = lukket). Posteringer med isVatReadonly/isAmountVatClosed=true kan ikke endres. 2) GET /ledger/voucher/{id}?fields=id,number,date,postings(id,row,account(number),vatType(number),amountGross,isVatReadonly,isAmountVatClosed). 3) Reverser: PUT /ledger/voucher/{id}/:reverse?date=<dato i åpen termin> (date påkrevd; action-endepunkt), og før nytt bilag med riktig vatType via POST /ledger/voucher. Er terminen levert, føres korreksjonen i neste åpne termin (eller korrigert melding i Tripletex-UI). Leverandørfaktura (BETA): PUT /supplierInvoice/voucher/{id}/postings kan erstatte debetlinjene. Skrivende – bekreft først.

### Kontrollere utgående mva på kundefakturaer i en periode
- **Kall:** `GET /invoice`, `GET /invoice/{id}`, `GET /balanceSheet`
- **Nøkkelord:** utgående mva faktura, utgaende mva faktura, mva på faktura, mva pa faktura, fakturaer mva, salg mva, omsetning mva, beløp eks mva, kreditnota mva, sales vat
- GET /invoice?invoiceDateFrom=yyyy-MM-dd&invoiceDateTo=yyyy-MM-dd&count=1000&fields=id,invoiceNumber,invoiceDate,isCreditNote,amount,amountExcludingVat,customer(name) (begge datoer påkrevd, To eksklusiv). mva = amount − amountExcludingVat. Per linje: GET /invoice/{id}?fields=orderLines(description,vatType(number,percentage),amountExcludingVatCurrency,amountIncludingVatCurrency). Avstem summen mot utgående mva-konto (2700–2703) i GET /balanceSheet. Kunder som er privatpersoner: ikke vis navn (GDPR).

### Kontrollere inngående mva på leverandørfakturaer
- **Kall:** `GET /supplierInvoice`, `GET /ledger/voucher/{id}`
- **Nøkkelord:** inngående mva faktura, inngaende mva faktura, leverandørfaktura mva, leverandorfaktura mva, fradrag inngående mva, kjøp mva, mva-fradrag, utenlandske leverandører, purchase vat
- GET /supplierInvoice?invoiceDateFrom=yyyy-MM-dd&invoiceDateTo=yyyy-MM-dd&fields=id,invoiceNumber,invoiceDate,supplier(name,organizationNumber),amount,amountExcludingVat,isCreditNote,voucher(id,number) (datoer påkrevd). mva = amount − amountExcludingVat. Koder per linje: GET /ledger/voucher/{voucherId}?fields=postings(account(number),vatType(number),amountGross). Let etter utenlandske leverandører uten 86/87, fradrag på kostnader uten fradragsrett (representasjon, personbil, velferd) og fakturaer fra ikke-mva-registrerte leverandører med mva.

### ✏️ Bokføre betaling av mva (oppgjør mot Skatteetaten) og sette opp betalingstype for mva
- **Kall:** `GET /vatReturns/status`, `GET /ledger/paymentTypeOut`, `POST /ledger/paymentTypeOut`, `GET /ledger/account`, `POST /ledger/voucher`
- **Nøkkelord:** betale mva, betaling av mva, mva-betaling, innbetaling skatteetaten, betalt mva, oppgjør mva, oppgjor mva, utbetaling mva til gode, betalingstype mva, utgående betaling, paymenttypeout
- Foretrukket: registrer betalingen i MVA-meldingen i Tripletex (oppdaterer paymentStatus) – v2 har ikke eget kall for dette. Betalingstyper: GET /ledger/paymentTypeOut?fields=id,description,creditAccount(number),showVatReturns,isInactive (BETA); typer med showVatReturns=true vises ved mva-betaling. Ny type: POST /ledger/paymentTypeOut {description, creditAccount:{id:<bank>}, showVatReturns:true}. Manuelt bilag: GET /vatReturns/status for beløp (paymentStatus.totalAmount / altinnPaymentAmount), GET /ledger/account?number=2740,1920 for id-er, POST /ledger/voucher med debet 2740 og kredit bank uten vatType. Et manuelt bilag oppdaterer trolig ikke paymentStatus i mva-modulen. Skrivende – bekreft først.

### Årsavstemming av merverdiavgift (sum terminer mot regnskapet ved årsoppgjøret)
- **Kall:** `GET /vatReturns/status/list`, `GET /balanceSheet`, `GET /ledger/posting`
- **Nøkkelord:** årsavstemming mva, arsavstemming mva, avstemming mva-pliktig omsetning, årsoppgjør mva, arsoppgjor mva, omsetning mot mva-melding, skyldig mva 31.12, mva hele året, revisjon mva, kontroll mva år
- 1) GET /vatReturns/status/list?startDate=<år>-01-01&endDate=<år+1>-01-01&fields=term,totalAmountVatBasis,altinnPaymentAmount,deliveryStatus(status),paymentStatus(status,totalAmount) – alle terminer bør ha RECEIPT_RECEIVED. 2) GET /balanceSheet?dateFrom=<år>-01-01&dateTo=<år+1>-01-01&accountNumberFrom=3000&accountNumberTo=3999 (omsetning) og accountNumberFrom=2700&accountNumberTo=2749 (mva-kontoer). Avstem omsetning mot summen av mva-grunnlag og at skyldig mva pr. 31.12 tilsvarer siste termin. 3) Avvik: GET /ledger/posting?dateFrom&dateTo&accountId=<id>&fields=voucher(number),date,amount,vatType(number).

### Hente posteringsregler som påvirker mva (mva per avdeling, flere næringer)
- **Kall:** `GET /ledger/postingRules`
- **Nøkkelord:** posteringsregler, mva per avdeling, avdeling mva, flere næringer, flere naeringer, næringskode, business activity, posting rules, salg uten mva konto
- GET /ledger/postingRules?fields=vatPerDepartment,multipleIndustries,defaultBusinessActivityTypeId,accountProductSaleNoVat(number,name). vatPerDepartment=true betyr at systemgenererte mva-posteringer splittes per avdeling; multipleIndustries=true betyr at både alminnelig næring og primærnæring (to mva-meldinger) er i bruk. Kun lesing.

### Sjekke Altinn-oppsett for innsending av MVA-meldingen
- **Kall:** `GET /company/settings/altinn`
- **Nøkkelord:** altinn, altinn-id, altinn oppsett, innsending mva, sende mva-melding, levere mva, altinn settings
- GET /company/settings/altinn?fields=altInnId viser om Altinn-ID er satt for klienten. PUT /company/settings/altinn tar Altinn-passord – det skal assistenten aldri fylle inn; be brukeren gjøre det selv i Tripletex. Selve beregning, innsending og gjenåpning av MVA-meldingen finnes ikke i API v2 – gjøres i Tripletex-UI.

### Eksportere SAF-T-fil ved mva-kontroll eller bokettersyn fra Skatteetaten
- **Kall:** `GET /saft/exportSAFT`
- **Nøkkelord:** saf-t, saft, saf-t eksport, mva-kontroll, bokettersyn, kontroll skatteetaten, skatteetaten ber om regnskap, standard audit file, eksportere regnskap, saf-t financial
- BETA. GET /saft/exportSAFT?year=<regnskapsår> (year påkrevd; version=1.2 (default) | 1.3 | 1.4 – angi eksplisitt versjon som Skatteetaten ber om). Gir eksportfil for hele året. Filen inneholder mva-kodene som SAF-T-standardkoder (vatType.number) og kan inneholde personopplysninger (ansatte/privatkunder) – lagre bare lokalt og ikke del videre uten at brukeren ber om det. Kun lesing.

### Mva-avstemming i avstemmingsmodulen (hovedbok mot mva-melding og Skatteetaten per termin)
- **Kall:** `GET /vatReturns/status`, `GET /vatReturns/status/list`, `GET /balanceSheet`
- **Nøkkelord:** mva-avstemming, mva avstemming, avstemme mva, avstemmingsmodul mva, vat reconciliation, mva-melding avstemming, skatteetaten mva, syncwithtaxadmin, 2740 oppgjørskonto, mva termin status
- UDOKUMENTERT – se docs/avstemmingsmodul.md. Byråkontoen (companyId 0): 1) POST /vat/reconciliation/context {customerId, year, term, vatReportType:"GENERAL_INDUSTRY"} → reconciliationId (idempotent). 2) GET /vat/reconciliation/{id}/overview → groups[].lines[] med vatTypeId, basis, ledgerData (hovedbok), reportedData (mva-melding), taxAdminData (Skatteetaten), difference. 3) Status: GET /vat/reconciliation/{id}/status (terminen) og GET /vat/reconciliation/statusList/{id} (alle terminer: deliveryStatus, paymentStatus, totalAmountVatBasis, altinnPaymentAmount – ikke vis employee-navn). 4) Skatteetatens tall: POST /vat/reconciliation/{id}/syncWithTaxAdmin {} krever aktiv ID-porten-innlogging (GET /idporten/loginstatus; API-brukeren har active:false) – ikke testet. 5) Blokkeringer: GET /accountingOffice/reconciliations/{id}/validations. 6) Fullfør: PUT /accountingOffice/reconciliations/{id}/:complete (testet OK på en klient T1–T3 2026 når alle linjer hadde ledgerData = reportedData = taxAdminData; skrivende – bekreft). Reell avstemming først når mva-meldingen for terminen er levert (reportedData null før). Kommentar-referanse trolig vatTypeId – verifiser med «test»-metoden.

**Fallgruver:**
- API v2 har IKKE kall for å opprette, beregne, sende inn, gjenåpne eller laste ned selve MVA-meldingen (spesifikasjonen). Bare status (/vatReturns/status, /vatReturns/status/list), merknader, innstillinger og terminlengde. Innsending gjøres i Tripletex-UI (Tripletex-MCP-connectoren har vatReturnApi_* men skal bare brukes hvis brukeren ber om det).
- vatType.id (intern id) er ikke det samme som vatType.number (mva-koden/SAF-T-koden). Slå alltid opp id med GET /ledger/vatType?number=<kode> før du setter vatType:{id} på posteringer, produkter eller kontoer.
- GET /ledger/vatType: vatDate brukes bare sammen med typeOfVat (OUTGOING | INCOMING | INCOMING_INVOICE | PROJECT | LEDGER); uten typeOfVat ignoreres datoen. number og id tar kommaseparerte lister.
- Standard SAF-T-koder (verifiser mot klienten med GET /ledger/vatType): 0 ingen mva, 1 inngående 25 %, 11 inngående 15 %, 13 inngående 12 %, 12 råfisk inn, 14/15 fradrag innførselsmva betalt til Tolletaten, 20/21/22 grunnlag innførsel, 81/83 innførsel beregnet selv med fradrag (25/15 %), 82/84 uten fradrag, 85 innførsel nullsats, 3 utgående 25 %, 31 utgående 15 %, 32 råfisk ut, 33 utgående 12 %, 5 fritatt innenfor loven, 51 omvendt avgiftsplikt innenlands (gull/klimakvoter), 52 eksport, 6 utenfor mva-loven, 86/87 tjenester fra utlandet 25 % med/uten fradrag, 88/89 lav sats, 91/92 kjøp av gull/klimakvoter med/uten fradrag.
- Mange mva-koder er bare tilgjengelige når tilsvarende has*-flagg er aktivert i /ledger/vatSettings (f.eks. 86/87 krever hasVatInHighForeignServices, 31 krever hasVatOutMedium). Feil 'ugyldig mva-kode' på bilag betyr ofte at koden ikke er aktivert eller ikke er lovlig på kontoen (legalVatTypes/vatLocked).
- PUT /ledger/vatSettings og PUT /vatTermSizeSettings/{id} skal ha id og version fra en fersk GET; send hele objektet så ikke andre flagg nullstilles. Utdatert version gir konflikt-/valideringsfeil – hent på nytt og prøv igjen.
- PUT /ledger/vatType/createRelativeVatType er et action-endepunkt med tre påkrevde query-parametere (name maks 8 tegn, vatTypeId, percentage) og ingen body.
- /vatReturns/status: uten year/term får du FORRIGE termin, ikke inneværende. term er terminnummer i året og avhenger av terminlengden (tomånedlig 1–6). reportType default GENERAL_INDUSTRY – bruk PRIMARY_INDUSTRY for primærnæring.
- /vatReturns/status/list: endDate er eksklusiv; terminer som slutter før 2022-01-01 utelates (ny mva-melding fra 2022). voucherNumber=0 betyr at terminen ikke er lukket; altinnPaymentAmount er null før levering.
- VatDeliveryStatus/VatPaymentStatus inneholder employee (hvem som leverte/betalte) – hent ikke disse feltene (GDPR); bruk fields=deliveryStatus(status,time),paymentStatus(status,totalAmount,remainingAmount,paymentDate).
- /vatReturns/comment og /vatReturns/comment/>all er BETA og bare lesing. Summary for /vatReturns/comment nevner «a given vatCode», men det finnes ingen vatCode-parameter – filtrer i svaret. Stier med '>' skrives bokstavelig (URL-koding %3E fungerer også).
- Bilag i en lukket/levert mva-termin kan ikke endres (isVatReadonly/isAmountVatClosed=true på posteringen). Korriger med reversering (PUT /ledger/voucher/{id}/:reverse?date=… i åpen termin) og nytt bilag, eller i neste termin.
- POST /ledger/voucher: bare bruttobeløp (amountGross/amountGrossCurrency) brukes – Tripletex lager mva-linjene selv. Ikke før mva-kontoene (27xx) manuelt med mva-kode i tillegg, da blir mva dobbelt.
- /balanceSheet, /ledger/posting, /ledger/voucher, /invoice og /supplierInvoice krever datointervall (dateFrom/dateTo eller invoiceDateFrom/invoiceDateTo) og To-datoen er eksklusiv.
- Mva-kontonumre (2700–2749) er vanlig standard men kan avvike i klientens kontoplan – slå opp med GET /ledger/account før avstemming.
- PUT /company/settings/altinn tar Altinn-passord – skal aldri fylles inn av assistenten. Brukeren må gjøre det selv.
- /ledger/paymentTypeOut er BETA. Registrering av mva-betaling mot en termin finnes ikke i v2; manuelt bilag oppdaterer trolig ikke paymentStatus i mva-modulen.
- 403 på /vatReturns/* eller /ledger/vatSettings betyr typisk at tokenet/brukeren mangler tilgang til mva-modulen (eller at klienten ikke er mva-registrert) – ikke at endepunktet mangler.
- Alle skrivende kall (vatSettings, vatTermSizeSettings, createRelativeVatType, konto/produkt-endringer, bilag) krever at brukeren bekrefter først, og klienten må være eksplisitt navngitt.
- GET /ledger/postingByDate støtter ikke fields= eller changes – bruk GET /ledger/posting med fields= når bare noen felt trengs (dataminimering).
- Enum-verdier: termSize = ONE_MONTH | TWO_MONTHS | THREE_MONTHS | FOUR_MONTHS | SIX_MONTHS | YEAR | NOT_REGISTERED; reportType = GENERAL_INDUSTRY | PRIMARY_INDUSTRY; vatRegistrationStatus = VAT_NOT_REGISTERED | VAT_APPLICANT | VAT_REGISTERED | VAT_COMPENSATION. term i /vatReturns/status regnes ut fra gjeldende terminlengde (årstermin: term=1).
- GET /saft/exportSAFT er BETA, krever year, og default version er 1.2 – angi version eksplisitt.
- Avstemmingsmodulen har mva-avstemminger (type VAT_GENERAL_INDUSTRY / VAT_PRIMARY_INDUSTRY; schema VatContextRequest {customerId, year, term, vatReportType}), men spec har ingen mva-context-sti – den udokumenterte POST /vat/reconciliation/context {customerId, year, term, vatReportType:"GENERAL_INDUSTRY"} virker (201, i byråkontoen, testet 2026-09-23; skrivende – bekreft). Status per termin: GET /accountingOffice/reconciliations (udokumentert, byråkontoen – se hovedbok). Udokumentert GET /vat/reconciliation/{id}/overview gir {period, groups[].lines[] med vatTypeId, displayName, basis, ledgerData, reportedData, taxAdminData, difference} (200 når kunden er delegert klient, ellers 403). Avstem selv: GET /vatReturns/status(/list) mot GET /balanceSheet 2700–2749.
- Tilbakeføring av fakturaer fra tidligere terminer (reverseVoucher) datert i ny termin tar med mva-koden og reverserer fradraget i den NYE terminen. Symptom: netto negativt grunnlag på kode 1 og positiv fradragslinje i /vat/reconciliation/{id}/overview. Eksempel klient A T4 2026: 11 fakturaer fra T1–T3 tilbakeført 01.07 = 79 555 i tilbakeført fradrag. Feil i tidligere terminer rettes normalt med ny mva-melding for terminen feilen gjelder – avklar årsaken før T4 leveres. Kontroll: GET /ledger/posting med fields=voucher(number,year,reverseVoucher(number,year)) og vatType(number).

## Bank, avstemming og utbetalinger

### Finne bankkontoene (hovedbokskontoer) til en klient
- **Kall:** `GET /ledger/account`
- **Nøkkelord:** bankkonto, bankkontoer, 1920, 1900, hovedbokskonto bank, kontoplan bank, isbankaccount, account id, kontonummer bank, driftskonto, skattetrekkskonto, sparekonto
- GET /ledger/account?isBankAccount=true&isInactive=false&fields=id,number,name,isBankAccount,requireReconciliation,currency(code),bankName. Bruk 'id' (ikke kontonummeret) som accountId i alle /bank/*-kall. Alternativt number=1920 for én konto. bankAccountNumber/IBAN er kontonummer – ikke ta med i fields med mindre det trengs, og masker ved utskrift.

### Slå opp en bank i bankregisteret (bankId, støttede filformater, autopay)
- **Kall:** `GET /bank`, `GET /bank/{id}`
- **Nøkkelord:** bank, bankid, registernummer, clearingnummer, hvilken bank, filformat, støttede formater, autopay, ztl, bankintegrasjon
- GET /bank?registerNumbers=<de fire første sifrene i bankkontonummeret>&fields=id,name,registerNumbers,bankStatementFileFormatSupport,platform,autoPaySupport eller GET /bank?query=DNB. Filtrer ev. med isBankReconciliationSupport=true / isAutoPaySupported=true / isZtlSupported=true. bankStatementFileFormatSupport viser hvilke fileFormat-verdier banken støtter ved import. GET /bank/{id} for én bank.

### ✏️ Importere kontoutskrift (bankfil) til en bankkonto
- **Kall:** `GET /ledger/account`, `GET /bank`, `POST /bank/statement/import`
- **Nøkkelord:** importere kontoutskrift, laste opp bankfil, import bankfil, kontoutskrift, bank statement import, csv, telepay, dnb csv, nordea csv, danske bank, sbanken, psd2
- 1) accountId fra GET /ledger/account?isBankAccount=true. 2) bankId fra GET /bank?registerNumbers=xxxx (sjekk bankStatementFileFormatSupport). 3) POST /bank/statement/import som multipart/form-data med feltet 'file', og query: bankId*, accountId*, fromDate* (inkl.), toDate* (EKSKL. – bruk dagen etter siste dato), fileFormat* (DNB_CSV|NORDEA_CSV|DANSKE_BANK_CSV|SBANKEN_BEDRIFT_CSV|SBANKEN_PRIVAT_CSV|HAUGESUND_SPAREBANK_CSV|EIKA_TELEPAY|SPAREBANK1_TELEPAY|HANDELSBANKEN_TELEPAY|SPAREBANKEN_VEST_TELEPAY|SPAREBANKEN_SOR_TELEPAY|SPAREBANKEN_OST_TELEPAY|CULTURA_BANK_TELEPAY|LANDKREDITT_TELEPAY|VISMA_ACCOUNT_STATEMENT|VISMA_ACCOUNT_STATEMENT_PSD2|..._PLATFORM_AGNOSTIC|TRANSFERWISE|ZTL|EXTERNAL_PSD2|FOLIO), valgfri externalId. Sjekk først GET /bank/statement?accountId= for overlappende perioder (dobbeltimport). Krever bekreftelse fra bruker.

### Liste importerte kontoutskrifter for en bankkonto med inngående og utgående saldo
- **Kall:** `GET /bank/statement`, `GET /bank/statement/{id}`
- **Nøkkelord:** kontoutskrifter, bankutskrifter, importerte bankfiler, inngående saldo, utgående saldo, saldo bank, hvilke perioder er importert, mangler kontoutskrift
- GET /bank/statement?accountId=<id> (kan være kommaseparert liste)&fields=id,fileName,fromDate,toDate,openingBalanceCurrency,closingBalanceCurrency,bank(name)&count=1000. Sorter på fromDate og se etter hull mellom toDate og neste fromDate for å finne manglende perioder. Kan filtrere på fileFormats. GET /bank/statement/{id} for én utskrift (fields=transactions(id,postedDate,amountCurrency,matched) gir også transaksjonene). Alle felt på BankStatement er skrivebeskyttet – feil kan kun rettes ved å slette og importere på nytt.

### Hente banktransaksjoner fra en kontoutskrift
- **Kall:** `GET /bank/statement`, `GET /bank/statement/transaction`, `GET /bank/statement/transaction/{id}`
- **Nøkkelord:** banktransaksjoner, bankposter, transaksjoner, kontobevegelser, innbetalinger, utbetalinger, bank transactions, transaksjonsliste
- 1) Finn bankStatementId via GET /bank/statement?accountId=. 2) GET /bank/statement/transaction?bankStatementId=<id> (PÅKREVD) &fields=id,postedDate,description,amountCurrency,matched,matchType,paymentId&from=0&count=1000 – bla videre med from ved flere. matched=false = uavstemt. Beskrivelser kan inneholde navn på privatpersoner – masker med redact() ved visning.

### Se detaljer/betalingsreferanse (KID, avsender) for en banktransaksjon
- **Kall:** `GET /bank/statement/transaction/{id}`, `GET /bank/statement/transaction/{id}/details`
- **Nøkkelord:** transaksjonsdetaljer, detaljer banktransaksjon, kid, referanse, remittering, avsender, mottaker, betalingsinfo, hvem har betalt
- GET /bank/statement/transaction/{id}?fields=id,postedDate,description,amountCurrency,paymentId,matched,groupedPostings,sourceVoucher(id,number) og deretter GET /bank/statement/transaction/{id}/details (returnerer et fritt objekt fra bankfilen, f.eks. KID, motpart, kontonummer). Detaljer kan inneholde personopplysninger (navn/kontonummer) – vis kun det som trengs, masker resten.

### ✏️ Slette en feilimportert kontoutskrift
- **Kall:** `GET /bank/statement`, `DELETE /bank/statement/{id}`
- **Nøkkelord:** slette kontoutskrift, feil bankfil, dobbeltimport, importert to ganger, angre import, fjerne bankfil
- Finn riktig id med GET /bank/statement?accountId=&fields=id,fileName,fromDate,toDate. Bekreft med bruker (fil, periode, konto). Hvis transaksjonene er matchet eller avstemmingen er lukket: gjenåpne avstemmingen og slett matcher (DELETE /bank/reconciliation/match/{id}) først. Deretter DELETE /bank/statement/{id}. Irreversibelt.

### Finne bankavstemmingen for en bankkonto og måned
- **Kall:** `GET /ledger/account`, `GET /ledger/accountingPeriod`, `GET /bank/reconciliation`, `GET /bank/reconciliation/{id}`
- **Nøkkelord:** bankavstemming, avstemming for måned, avstemming periode, regnskapsperiode, accounting period, hent avstemming, avstemmingsstatus
- 1) accountId fra GET /ledger/account?isBankAccount=true. 2) accountingPeriodId fra GET /ledger/accountingPeriod?startFrom=2026-08-01&startTo=2026-08-02&fields=id,number,start,end. 3) GET /bank/reconciliation?accountId=<id>&accountingPeriodId=<id>&fields=id,type,isClosed,closedDate,bankAccountClosingBalanceCurrency,account(number,name),accountingPeriod(start,end),approvable,autoPayReconciliation. GET /bank/reconciliation/{id} for én. Tomt resultat = avstemming ikke opprettet for perioden.

### Hente siste bankavstemming eller siste lukkede avstemming for en konto
- **Kall:** `GET /bank/reconciliation/>last`, `GET /bank/reconciliation/>lastClosed`
- **Nøkkelord:** siste avstemming, sist avstemt, siste lukkede avstemming, hvor langt er banken avstemt, avstemt til og med, last reconciliation
- GET "/bank/reconciliation/>last"?accountId=<id>* (sist opprettede) eller GET "/bank/reconciliation/>lastClosed"?accountId=<id>*&after=yyyy-MM-dd (sist lukkede, ev. etter dato). fields=id,isClosed,closedDate,accountingPeriod(start,end),bankAccountClosingBalanceCurrency. Sitér stien i skallet – '>' tolkes ellers som omdirigering.

### Status for bankavstemming på alle bankkontoer (månedskontroll per klient)
- **Kall:** `GET /ledger/account`, `GET /ledger/accountingPeriod`, `GET /bank/reconciliation`, `GET /bank/reconciliation/>lastClosed`
- **Nøkkelord:** avstemmingsstatus, status bankavstemming, hvilke kontoer er avstemt, ikke avstemt, månedskontroll, manedskontroll, periodeavslutning, kontroll bank, oversikt avstemminger
- 1) GET /ledger/account?isBankAccount=true&isInactive=false&fields=id,number,name,requireReconciliation. 2) Periode-id(er) fra GET /ledger/accountingPeriod. 3) GET /bank/reconciliation?accountId=<id1,id2,..>&accountingPeriodId=<id>&fields=id,account(number),accountingPeriod(start),isClosed,closedDate. Kontoer uten treff eller isClosed=false er ikke ferdig avstemt. For 'avstemt til og med' per konto: GET "/bank/reconciliation/>lastClosed"?accountId=.

### ✏️ Opprette bankavstemming for en periode
- **Kall:** `GET /ledger/accountingPeriod`, `GET /bank/reconciliation`, `POST /bank/reconciliation`
- **Nøkkelord:** opprette bankavstemming, ny avstemming, starte avstemming, create reconciliation, automatisk bankavstemming, manuell avstemming
- Sjekk først at den ikke finnes (GET /bank/reconciliation?accountId=&accountingPeriodId=). POST /bank/reconciliation med body {"account":{"id":<kontoId>},"accountingPeriod":{"id":<periodeId>},"type":"AUTOMATIC" (automatisk bankavstemming med importerte transaksjoner) eller "MANUAL","bankAccountClosingBalanceCurrency":<saldo iflg. kontoutskrift>}. Krever bekreftelse.

### ✏️ Registrere/endre saldo iflg. bankutskrift på en avstemming
- **Kall:** `GET /bank/reconciliation/{id}`, `PUT /bank/reconciliation/{id}`
- **Nøkkelord:** saldo iflg bank, utgående saldo, bankens saldo, sluttsaldo, closing balance, oppdatere saldo, saldo kontoutskrift
- GET /bank/reconciliation/{id}?fields=id,version,bankAccountClosingBalanceCurrency,isClosed. PUT /bank/reconciliation/{id} med {"id":..,"version":..,"bankAccountClosingBalanceCurrency":<beløp>}. Må være åpen (isClosed=false). Utgående saldo kan hentes fra GET /bank/statement (closingBalanceCurrency). Krever bekreftelse.

### Kontrollere bankkontoens saldo i hovedboken mot kontoutskriften
- **Kall:** `GET /balanceSheet`, `GET /bank/statement`, `GET /bank/reconciliation/{id}`
- **Nøkkelord:** saldo hovedbok bank, saldo 1920, saldobalanse bank, avstemme saldo, differanse bank, bankdifferanse, saldokontroll, stemmer banken
- 1) Hovedbok: GET /balanceSheet?dateFrom=<periodestart>&dateTo=<dagen etter periodeslutt, EKSKL.>&accountNumberFrom=1920&accountNumberTo=1920&fields=account(number,name),balanceIn,balanceChange,balanceOut. 2) Bank: GET /bank/statement?accountId=&fields=toDate,closingBalanceCurrency (siste utskrift i perioden) eller bankAccountClosingBalanceCurrency på avstemmingen. 3) Differansen forklares av uavstemte transaksjoner/posteringer (se oppgaven om åpne poster).

### Liste åpne (uavstemte) poster på bankkonto – transaksjoner og posteringer uten match
- **Kall:** `GET /bank/reconciliation`, `GET /bank/statement`, `GET /bank/statement/transaction`, `GET /ledger/posting`, `GET /bank/reconciliation/match`
- **Nøkkelord:** åpne poster bank, apne poster, uavstemte poster, uavstemt, umatchet, mangler bilag, mangler dokumentasjon, bankavstemmingsliste, liste til kunden, unmatched, differanse avstemming
- 1) Finn avstemmingen (GET /bank/reconciliation?accountId=&accountingPeriodId=). 2) Banksiden: for hver kontoutskrift i perioden GET /bank/statement/transaction?bankStatementId=&fields=id,postedDate,description,amountCurrency,matched – behold matched=false. 3) Hovedboksiden: GET /ledger/posting?accountId=<bankkonto-id>&dateFrom=&dateTo=(ekskl.)&fields=id,date,description,amount,voucher(number,year),matched – behold matched=false. 4) Kontroll: GET /bank/reconciliation/match?bankReconciliationId=&approved=true viser hva som er avstemt. Lever som tabell per konto/måned; masker personnavn i tekstene. For lukkede perioder med hengende poster: GET /bank/reconciliation/closedWithUnmatchedTransactions?accountId=. Alternativt CSV via PUT /bank/reconciliation/transactions/unmatched:csv?reconciliationId=. Husk at dateTo er ekskl. og at count er 1000 som standard (bla med from).

### Eksportere uavstemte banktransaksjoner til CSV
- **Kall:** `GET /bank/reconciliation`, `PUT /bank/reconciliation/transactions/unmatched:csv`
- **Nøkkelord:** eksport uavstemte, csv uavstemte, last ned uavstemte, unmatched csv, excel åpne poster, liste uavstemte transaksjoner
- 1) Finn avstemmings-id med GET /bank/reconciliation?accountId=&accountingPeriodId=&fields=id. 2) PUT /bank/reconciliation/transactions/unmatched:csv?reconciliationId=<avstemmings-id> – parameteren er ikke merket påkrevd i spec, men må sendes. Svaret er en CSV-fil (text/csv, UTF-8 eller ISO-8859-1), ikke JSON – les som tekst/binær og sjekk tegnsett. Selv om metoden er PUT endrer kallet ingenting. Masker personnavn før deling.

### Finne siste lukkede avstemming som fortsatt har uavstemte transaksjoner
- **Kall:** `GET /bank/reconciliation/closedWithUnmatchedTransactions`
- **Nøkkelord:** lukket med uavstemte, uavstemte i lukket periode, hengende poster, gamle åpne poster, closed with unmatched, etterslep bankavstemming
- GET /bank/reconciliation/closedWithUnmatchedTransactions?accountId=<id>*&start=yyyy-MM-dd&fields=id,accountingPeriod(start,end),closedDate,transactions(id,postedDate,amountCurrency,description,matched). Nyttig i årsoppgjør/kvalitetskontroll for å finne perioder som ble lukket med poster som ikke er avstemt.

### ✏️ Kjøre automatisk matching (forslag) på en bankavstemming
- **Kall:** `PUT /bank/reconciliation/match/:suggest`, `GET /bank/reconciliation/match`
- **Nøkkelord:** automatisk matching, automatch, foreslå matcher, matchforslag, suggest, kjør avstemming, auto avstem, forslag bankavstemming
- PUT /bank/reconciliation/match/:suggest?bankReconciliationId=<id>* – returnerer liste med foreslåtte matcher (type PENDING_SUGGESTION). Se dem med GET /bank/reconciliation/match?bankReconciliationId=<id>&approved=false&fields=id,type,transactions(id,postedDate,amountCurrency,description),postings(id,date,amount,voucher(number)). Oppretter forslag i avstemmingen – be om bekreftelse.

### ✏️ Manuelt matche banktransaksjon(er) mot hovedbokspostering(er)
- **Kall:** `GET /bank/statement/transaction`, `GET /ledger/posting`, `POST /bank/reconciliation/match`
- **Nøkkelord:** manuell match, matche manuelt, koble transaksjon, koble bank mot bilag, avstemme post, en til mange, mange til en, match transaction posting
- 1) Transaksjons-id(er) fra GET /bank/statement/transaction?bankStatementId= (matched=false). 2) Posterings-id(er) på bankkontoen fra GET /ledger/posting?accountId=<bankkonto>&dateFrom=&dateTo=&fields=id,date,amount,description,matched. 3) Sjekk at summene er like. 4) POST /bank/reconciliation/match med {"bankReconciliation":{"id":..},"type":"MANUAL","transactions":[{"id":..}],"postings":[{"id":..}]}. Kun MANUAL og ADJUSTMENT kan settes ved opprettelse. Avstemmingen må være åpen. Krever bekreftelse.

### ✏️ Godkjenne eller avvise matchforslag
- **Kall:** `GET /bank/reconciliation/match`, `GET /bank/reconciliation/match/{id}`, `PUT /bank/reconciliation/match/{id}`, `DELETE /bank/reconciliation/match/{id}`, `POST /bank/reconciliation/match`
- **Nøkkelord:** godkjenne forslag, godkjenn match, avvise forslag, approve suggestion, reject suggestion, bekrefte match, pending suggestion
- Hent forslag: GET /bank/reconciliation/match?bankReconciliationId=<id>&approved=false&fields=id,version,type,transactions(id,postedDate,amountCurrency),postings(id,date,amount) (type PENDING_SUGGESTION). Spec: type kan bare settes til MANUAL eller ADJUSTMENT ved opprettelse; øvrige typer (APPROVED_SUGGESTION, REJECTED_SUGGESTION osv.) er systemsatte og skrivebeskyttet. Sikreste vei for å godkjenne er derfor å slette forslaget (DELETE /bank/reconciliation/match/{id}) og opprette en MANUAL match med samme transactions/postings (POST /bank/reconciliation/match). PUT /bank/reconciliation/match/{id} (id+version) kan brukes til å endre transactions/postings i en match – verifiser resultatet med GET /bank/reconciliation/match/{id}. Avvise = DELETE. Avstemmingen må være åpen. Krever bekreftelse.

### ✏️ Oppheve (slette) en match i bankavstemmingen
- **Kall:** `GET /bank/reconciliation/match`, `DELETE /bank/reconciliation/match/{id}`
- **Nøkkelord:** oppheve match, slette match, fjerne kobling, angre avstemming, feil match, unmatch, løsne transaksjon
- Finn match-id: GET /bank/reconciliation/match?bankReconciliationId=&fields=id,type,transactions(id,amountCurrency,postedDate),postings(id,amount). Avstemmingen må være åpen (gjenåpne med PUT /bank/reconciliation/{id} isClosed=false om nødvendig). DELETE /bank/reconciliation/match/{id}. Transaksjon og postering blir da uavstemte igjen. Krever bekreftelse.

### Telle matcher og nye auto-matcher i en avstemming
- **Kall:** `GET /bank/reconciliation/match/count`, `GET /bank/reconciliation/matches/counter`
- **Nøkkelord:** antall matcher, hvor mange avstemt, telle matcher, nye automatcher, nye forslag, match count, counter, fremdrift avstemming
- GET /bank/reconciliation/match/count?bankReconciliationId=<id>* gir totalt antall matcher (heltall). [BETA] GET /bank/reconciliation/matches/counter?bankReconciliationId=<id>* gir antall auto-matchede og foreslåtte matcher siden avstemmingssiden sist ble åpnet (UI-teller). For fremdrift: sammenlign med antall transaksjoner med matched=false (GET /bank/statement/transaction?bankStatementId=).

### ✏️ Nullstille telleren for nye matcher i bankavstemmingen
- **Kall:** `POST /bank/reconciliation/matches/counter`
- **Nøkkelord:** nullstille teller, reset counter, nullstill varsel, nye matcher sett
- [BETA] POST /bank/reconciliation/matches/counter?bankReconciliationId=<id>* nullstiller telleren slik UI gjør når siden åpnes. Påvirker bare varselet, ikke regnskapet – men er et skrivende kall og krever bekreftelse. Sjelden nødvendig.

### ✏️ Føre bankgebyr, renter eller annen differanse fra bankavstemmingen
- **Kall:** `GET /bank/reconciliation/paymentType`, `GET /ledger/account`, `POST /ledger/voucher`, `GET /ledger/posting`, `POST /bank/reconciliation/match`
- **Nøkkelord:** bankgebyr, gebyr, renteinntekt, rentekostnad, renter, føre differanse, fore differanse, manglende bilag bank, direkteføring, justering, adjustment, 7770, 8050, 8150
- 1) Se tilgjengelige posteringstyper med konti: GET /bank/reconciliation/paymentType?fields=id,description,debitAccount(number,name),creditAccount(number,name). 2) Før bilag: POST /ledger/voucher med date, description og postings (row fra 1, account{id}, amountGross/amountGrossCurrency – kun bruttobeløp brukes, summen må bli 0): f.eks. debet 7770 Bankgebyr og kredit bankkonto (amountGross negativ på bank), eller renteinntekt 8050 mot bank. 3) Hent den nye bankposteringen (GET /ledger/posting?accountId=&dateFrom=&dateTo=) og match den mot banktransaksjonen med POST /bank/reconciliation/match (type MANUAL, eller ADJUSTMENT for justering). Krever bekreftelse før bilag føres.

### Hente betalingstyper for bankavstemmingen
- **Kall:** `GET /bank/reconciliation/paymentType`, `GET /bank/reconciliation/paymentType/{id}`
- **Nøkkelord:** betalingstyper avstemming, posteringstyper, payment types reconciliation, debetkonto, kreditkonto, gebyrtype
- GET /bank/reconciliation/paymentType?description=<tekst>&fields=id,description,debitAccount(number,name),creditAccount(number,name),isInactive,sequence. GET /bank/reconciliation/paymentType/{id} for én. Kun lesing – typene vedlikeholdes i Tripletex-UI.

### ✏️ Lukke (ferdigstille) en bankavstemming
- **Kall:** `GET /bank/reconciliation/{id}`, `PUT /bank/reconciliation/transactions/unmatched:csv`, `PUT /bank/reconciliation/{id}`
- **Nøkkelord:** lukke avstemming, ferdigstille avstemming, godkjenne avstemming, avslutte bankavstemming, close reconciliation, periode ferdig avstemt
- 1) GET /bank/reconciliation/{id}?fields=id,version,isClosed,approvable,bankAccountClosingBalanceCurrency. 2) Kontroller uavstemte (CSV-eksport eller åpne poster-oppgaven) og at saldo stemmer. 3) PUT /bank/reconciliation/{id} med {"id":..,"version":..,"isClosed":true}. approvable=false betyr at avstemmingen ikke kan lukkes ennå. Krever bekreftelse.

### ✏️ Gjenåpne en lukket bankavstemming
- **Kall:** `GET /bank/reconciliation/{id}`, `PUT /bank/reconciliation/{id}`
- **Nøkkelord:** gjenåpne avstemming, gjenapne, åpne lukket avstemming, reopen reconciliation, rette avstemming, endre lukket periode
- GET /bank/reconciliation/{id}?fields=id,version,isClosed. PUT /bank/reconciliation/{id} med {"id":..,"version":..,"isClosed":false}. Nødvendig før matcher kan endres/slettes. Vær obs på at senere perioder kan bygge på denne; lukk igjen etter retting. Krever bekreftelse.

### ✏️ Slette en bankavstemming som er opprettet feil
- **Kall:** `GET /bank/reconciliation`, `DELETE /bank/reconciliation/{id}`
- **Nøkkelord:** slette avstemming, fjerne avstemming, feil avstemming, delete reconciliation, feil periode avstemming
- Finn id med GET /bank/reconciliation?accountId=&accountingPeriodId=&fields=id,isClosed,accountingPeriod(start). Bekreft konto/periode med bruker. Gjenåpne og fjern matcher først om nødvendig. DELETE /bank/reconciliation/{id}. Irreversibelt.

### ✏️ Se eller endre innstillinger for bankavstemming
- **Kall:** `GET /bank/reconciliation/settings`, `POST /bank/reconciliation/settings`, `PUT /bank/reconciliation/settings/{id}`
- **Nøkkelord:** innstillinger bankavstemming, antall per side, avstemmingsoppsett, reconciliation settings, sidestørrelse
- GET /bank/reconciliation/settings?fields=id,version,numberOfMatchesPerPage. Finnes de: PUT /bank/reconciliation/settings/{id} med {"id","version","numberOfMatchesPerPage":"ITEMS_10|ITEMS_50|ITEMS_100|ITEMS_500|ITEMS_1000|ITEMS_5000|ITEMS_10000"}. Finnes de ikke: POST /bank/reconciliation/settings. Påvirker kun visningen. Krever bekreftelse ved endring.

### Liste betalingstyper for utgående betalinger
- **Kall:** `GET /ledger/paymentTypeOut`, `GET /ledger/paymentTypeOut/{id}`
- **Nøkkelord:** utgående betalinger, betalingstyper, utbetalingstyper, hvordan betales leverandørfaktura, betalingsmåte, payment type out, nettbank, autopay, kreditkonto betaling
- [BETA] GET /ledger/paymentTypeOut?isInactive=false&fields=id,description,creditAccount(number,name),showIncomingInvoice,showVatReturns,showWagePayment,showWagePeriodTransaction,requiresSeparateVoucher,sequence,currencyCode. showIncomingInvoice=true = tilgjengelig på leverandørfaktura, showVatReturns = MVA-melding, showWagePayment = lønn. id brukes som paymentType ved leverandørbetaling.

### ✏️ Opprette, endre eller deaktivere betalingstyper for utgående betalinger
- **Kall:** `POST /ledger/paymentTypeOut`, `POST /ledger/paymentTypeOut/list`, `PUT /ledger/paymentTypeOut/{id}`, `PUT /ledger/paymentTypeOut/list`, `DELETE /ledger/paymentTypeOut/{id}`
- **Nøkkelord:** ny betalingstype, opprette utbetalingstype, endre betalingstype, deaktivere betalingstype, slette betalingstype, firmakort betaling, kredittkort, kontant, valutakonto betaling
- [BETA] POST /ledger/paymentTypeOut med {"description":"Firmakort","creditAccount":{"id":<konto-id, f.eks. 1920/2400-konto>},"showIncomingInvoice":true,"showVatReturns":false,"showWagePayment":false,"requiresSeparateVoucher":false,"sequence":n,"currencyCode":"NOK"}. Flere samtidig: POST/PUT /ledger/paymentTypeOut/list (array). Endre: PUT /ledger/paymentTypeOut/{id} med id+version. Foretrekk isInactive=true fremfor DELETE hvis typen er brukt. showWagePayment/showWagePeriodTransaction krever lønnsmodul, isBruttoWageDeduction krever PROVISIONSALARY. Krever bekreftelse.

### ✏️ Registrere betaling av leverandørfaktura
- **Kall:** `GET /ledger/paymentTypeOut`, `GET /supplierInvoice`, `POST /supplierInvoice/{invoiceId}/:addPayment`
- **Nøkkelord:** betale leverandørfaktura, registrere betaling leverandør, leverandørbetaling, leverandorbetaling, betalt faktura, kid, remittering, delbetaling, add payment, utbetaling leverandør
- 1) Finn fakturaen: GET /supplierInvoice?invoiceDateFrom=*&invoiceDateTo=* (ekskl.) &supplierId=/invoiceNumber=/kid= (innkjøp-gruppen). 2) paymentType-id fra GET /ledger/paymentTypeOut?isInactive=false (showIncomingInvoice=true), eller paymentType=0 / useDefaultPaymentType=true for sist brukte type for leverandøren. 3) POST /supplierInvoice/{invoiceId}/:addPayment?paymentType=<id>*&amount=&paymentDate=yyyy-MM-dd&kidOrReceiverReference=&bban=&partialPayment=true (ved delbetaling). Metoden krever oppsett gjort av Tripletex. Krever bekreftelse; betalinger kan gå til bank (autopay). bban = mottakers kontonummer – personopplysning hvis mottaker er privatperson; ikke logg eller vis det.

### ✏️ Registrere innbetaling på kundefaktura (fra bankavstemming)
- **Kall:** `GET /invoice`, `GET /invoice/paymentType`, `PUT /invoice/{id}/:payment`
- **Nøkkelord:** innbetaling kunde, registrere innbetaling, kunde har betalt, betalt kundefaktura, kundereskontro, innbetalingstype, invoice payment, kid innbetaling
- 1) Finn fakturaen: GET /invoice?invoiceDateFrom=*&invoiceDateTo=* (ekskl.) &kid=<KID fra banktransaksjonen> eller &invoiceNumber=, gjerne med status=OUTSTANDING (salg-gruppen); amountOutstanding viser restbeløp. 2) paymentTypeId fra GET /invoice/paymentType?fields=id,description,debitAccount(number). 3) PUT /invoice/{id}/:payment?paymentDate=*&paymentTypeId=*&paidAmount=* (+ paidAmountCurrency for valutafaktura). Innbetalingen gir en postering på bankkontoen som deretter kan matches mot banktransaksjonen (auto-match eller POST /bank/reconciliation/match). Krever bekreftelse.

### Hente posteringer på bankkontoen i en periode (hovedbokssiden av avstemmingen)
- **Kall:** `GET /ledger/account`, `GET /ledger/posting`
- **Nøkkelord:** posteringer bank, hovedbok bank, kontoutskrift hovedbok, bevegelser 1920, bilag på bankkonto, ledger postings bank
- GET /ledger/posting?accountId=<bankkonto-id>&dateFrom=yyyy-MM-dd*&dateTo=yyyy-MM-dd* (EKSKL.)&fields=id,date,description,amount,amountCurrency,voucher(number,year),matched&from=0&count=1000. matched viser om posteringen er avstemt mot bank. Bruk accountNumberFrom/To=1920 hvis id ikke er kjent.

**Fallgruver:**
- accountId i alle /bank/*-kall er hovedbokskontoens interne id (fra GET /ledger/account?isBankAccount=true), IKKE kontonummeret 1920.
- GET /bank/statement/transaction krever bankStatementId – man kan ikke søke transaksjoner direkte på konto/dato; gå via GET /bank/statement?accountId=.
- POST /bank/statement/import er multipart/form-data (felt 'file') med påkrevde query-parametere bankId, accountId, fromDate, toDate og fileFormat (enum). toDate er EKSKLUSIV – bruk dagen etter siste transaksjonsdato. Sjekk overlapp mot eksisterende kontoutskrifter for å unngå dobbeltimport.
- POST /bank/statement/import støtter bare fileFormat-enumen (bankspesifikke CSV/Telepay-formater, VISMA_ACCOUNT_STATEMENT*, EXTERNAL_PSD2, ZTL, TRANSFERWISE, FOLIO) – ikke generisk CAMT.053/MT940. Sjekk bankStatementFileFormatSupport på GET /bank først.
- Stier med '>' (GET /bank/reconciliation/>last og />lastClosed) må siteres i skallet (ellers tolkes '>' som omdirigering) og ev. URL-kodes som %3E i enkelte klienter. Begge krever accountId.
- PUT /bank/reconciliation/transactions/unmatched:csv er et lesekall selv om metoden er PUT, og returnerer CSV (text/csv) – ikke JSON.
- PUT /bank/reconciliation/match/:suggest er et action-endepunkt som oppretter matchforslag (PENDING_SUGGESTION) – regnes som skrivende.
- Ved POST /bank/reconciliation/match kan type kun være MANUAL eller ADJUSTMENT; PENDING_SUGGESTION, APPROVED_SUGGESTION, AUTO_MATCHED, DIRECT_POSTING, AUTOPOSTING_* m.fl. settes av systemet. Godkjente typer (del av avstemmingen): MANUAL, APPROVED_SUGGESTION, DIRECT_POSTING, ADJUSTMENT, AUTO_MATCHED, AUTOPOSTING_APPROVED.
- Lukket avstemming (isClosed=true) må gjenåpnes med PUT /bank/reconciliation/{id} isClosed=false før matcher kan endres/slettes eller kontoutskrifter fjernes. Lukking/gjenåpning skjer via PUT med isClosed – det finnes ingen egen :close-action.
- PUT-kall krever id og gjeldende version (optimistisk låsing); 409/RevisionException betyr at objektet er endret siden det ble hentet – hent på nytt.
- BankReconciliation.type: AUTOMATIC = 'Automatisk bankavstemming' (importerte/PSD2-transaksjoner), MANUAL = manuell avstemming. autoPayReconciliation og approvable er skrivebeskyttet.
- GET /ledger/posting og GET /balanceSheet krever dateFrom og dateTo, og dateTo er EKSKLUSIV. Posteringer har feltet 'matched' (skrivebeskyttet) – bruk det til å finne uavstemte posteringer på bankkontoen.
- Fortegn: på bankkontoen er innskudd positive både i BankTransaction.amountCurrency og Posting.amount (debet), uttak negative – sammenlign summer med samme fortegn ved manuell matching.
- GET /bank/reconciliation/matches/counter og POST (nullstilling) er BETA og gjelder bare UI-varsler om nye matcher. GET /bank/reconciliation/match/query er INTERNAL – ikke bruk.
- Alle /ledger/paymentTypeOut-endepunkter er BETA. showWagePayment/showWagePeriodTransaction krever lønnsmodul og isBruttoWageDeduction krever modulen PROVISIONSALARY – ellers 403/valideringsfeil. Deaktiver (isInactive=true) heller enn å slette brukte typer.
- Det finnes tre ulike sett betalingstyper: /bank/reconciliation/paymentType (posteringstyper i avstemmingen), /ledger/paymentTypeOut (utgående betalinger: leverandør, MVA, lønn, skatt) og /invoice/paymentType (innbetalinger på kundefaktura). Ikke bland id-ene.
- POST /supplierInvoice/{invoiceId}/:addPayment krever oppsett gjort av Tripletex; paymentType=0 eller useDefaultPaymentType=true velger sist brukte type for leverandøren. Betalinger kan sendes til nettbank/autopay – alltid bekreftelse.
- 403 betyr normalt at token/bruker mangler rettighet til bankavstemming/regnskap eller at klienten ikke har modulen (f.eks. bankintegrasjon/autopay). Tomt svar/404 på >last/>lastClosed tyder på at det ikke finnes (lukket) avstemming for kontoen.
- Alle skrivende kall (import, opprette/lukke/gjenåpne/slette avstemming, match/:suggest, opprette/slette matcher, bilag for gebyr, betalingstyper, betalinger) krever eksplisitt bekreftelse fra bruker, og klient må være navngitt.
- GDPR: banktransaksjonstekster og /bank/statement/transaction/{id}/details kan inneholde navn og kontonummer til privatpersoner (Vipps, lønn, utlegg). Bruk minimale fields=, masker med redact() og vis aggregater/initialer i rapporter. Bankkontonummer (bankAccountNumber/IBAN) skal ikke deles.
- Listekall har count=1000 som standard – bla med from/count ved store kontoutskrifter eller mange posteringer.
- Påkrevde id-parametere: GET /bank/statement/transaction (bankStatementId), GET /bank/reconciliation/closedWithUnmatchedTransactions, >last og >lastClosed (accountId), GET /bank/reconciliation/match/count og matches/counter (bankReconciliationId), PUT /bank/reconciliation/match/:suggest (bankReconciliationId). reconciliationId på unmatched:csv er ikke merket påkrevd, men må sendes.
- BankStatement (saldo, datoer, filnavn) og BankReconciliationPaymentType er skrivebeskyttet via API: kontoutskrifter opprettes kun via import og kan bare slettes; avstemmingens betalingstyper kan bare leses.
- En bankavstemming hører til én hovedbokskonto + én regnskapsperiode (månedsperiode fra GET /ledger/accountingPeriod). Finn periode-id med startFrom/startTo (startTo ekskl.).
- GET /bank/statement/transaction/{id}/details returnerer et fritt objekt (ResponseWrapperObject) fra bankfilen – feltene varierer mellom banker og formater.

## Lønn, lønnsavstemminger, pensjon

### ✏️ Lage lønnsutkast / kjøre lønn for en måned med faste lønnslinjer
- **Kall:** `GET /employee`, `GET /employee/employment`, `GET /employee/employment/details`, `GET /salary/payslip`, `GET /salary/type`, `POST /salary/transaction`, `GET /ledger/voucher`
- **Nøkkelord:** lønnsutkast, lonnsutkast, kjøre lønn, kjore lonn, lønnskjøring, lonnskjoring, faste lønnslinjer, månedslønn, lønn for måned, payroll, salary transaction, forskuddstrekk, skattetrekk
- Krever navngitt klient og bekreftelse (brukerens bestilling av utkastet regnes som bekreftelse). 1) Aktive ansatte: GET /employee?fields=id (ikke navn i output). 2) Faste linjer utledes fra historikk: GET /salary/payslip?employeeId=..&yearFrom=..&yearTo=..&monthFrom=..&monthTo=.. (To er EKSKLUSIV) &fields=employee(id),year,month,specifications(salaryType(id,number),rate,count,amount,description). Månedslønn: GET /employee/employment?employeeId=..&fields=id,startDate,endDate → GET /employee/employment/details?employmentId=<id>&fields=date,monthlySalary,hourlyWage,percentageOfFullTimeEquivalent (bruk siste date). Hopp over engangslinjer/korrigeringer. 3) Lønnsart-id: GET /salary/type?fields=id,number,name. 4) POST /salary/transaction?generateTaxDeduction=true med body {date: utbetalingsdato, year, month, isHistorical:false, payslips:[{employee:{id}, specifications:[{salaryType:{id}, rate, count, amount, description:'<Måned> <år>'}]}]}. Ugyldig dato (f.eks. 31.09) → bruk siste dag i måneden. 5) Transaksjonen lagres IKKE-godkjent og uten bilag – verifiser med GET /ledger/voucher?dateFrom=<dato>&dateTo=<dato+1>&fields=id,number,voucherType(name) at det ikke finnes lønnsbilag. Brukeren godkjenner selv i Tripletex → Lønn. Aldri godkjenn, aldri send a-melding. 6) Rapporter pseudonymisert (ansatt 1/2): linjer, skattetrekk, netto; si at linjene er utledet fra historikk.

### Hente lønnsslipper for en måned eller periode
- **Kall:** `GET /salary/payslip`
- **Nøkkelord:** lønnsslipp, lonnsslipp, lønnsslipper, lønn forrige måned, hva ble utbetalt, brutto, netto, lønnshistorikk, payslip, utbetalt lønn, lønn hittil i år
- GET /salary/payslip med yearFrom/yearTo og monthFrom/monthTo – To-parameterne er EKSKLUSIVE (september 2026 = yearFrom=2026&yearTo=2027&monthFrom=9&monthTo=10), eller voucherDateFrom/voucherDateTo (til eksklusiv). Valgfritt employeeId, wageTransactionId (lønnskjøring), activityId, comment. fields=id,year,month,date,grossAmount,amount,vacationAllowanceAmount,employee(id),transaction(id) – ikke navn/fødselsnr. Paginer med from/count. GDPR: vis summer eller «ansatt 1/2», bruk redact() på utskrift.

### Se lønnslinjer på én lønnsslipp eller laste ned lønnsslipp som PDF
- **Kall:** `GET /salary/payslip`, `GET /salary/payslip/{id}`, `GET /salary/payslip/{id}/pdf`
- **Nøkkelord:** lønnsslipp pdf, lonnsslipp pdf, lønnsspesifikasjon, lønnslinjer, lønnsarter på slipp, payslip pdf, skrive ut lønnsslipp, detaljer lønnsslipp
- Finn id via GET /salary/payslip (se oppgaven over). Detaljer: GET /salary/payslip/{id}?fields=id,year,month,grossAmount,amount,vacationAllowanceAmount,specifications(salaryType(number,name),rate,count,amount,description). PDF: GET /salary/payslip/{id}/pdf returnerer binær (application/octet-stream). PDF-en inneholder full persondata – lagre kun lokalt når brukeren ber om det, aldri del/send videre.

### Lage aggregert lønnsoversikt per måned (brutto, netto, feriepenger, antall lønnsslipper)
- **Kall:** `GET /salary/payslip`, `GET /balanceSheet`
- **Nøkkelord:** lønnsoversikt, lonnsoversikt, lønnskostnad per måned, lønnsstatistikk, sum brutto lønn, lønn hittil i år, lønnsrapport, feriepenger per måned, payroll summary
- GET /salary/payslip?yearFrom=<år>&yearTo=<år+1>&monthFrom=1&monthTo=13 (To eksklusiv)&fields=year,month,grossAmount,amount,vacationAllowanceAmount,department(id,name)&count=1000 – summer per måned/avdeling i koden, ikke per person. Sjekk fullResultSize mot antall mottatte rader og paginer med from/count. Avstem mot regnskapet med GET /balanceSheet?dateFrom=<år>-01-01&dateTo=<dag etter periodeslutt>&accountNumberFrom=5000&accountNumberTo=5999&fields=account(number,name),balanceChange. Rapporter kun aggregater.

### Hente en lønnskjøring (lønnsbilag) med alle lønnsslipper og sjekke om den er bokført
- **Kall:** `GET /salary/payslip`, `GET /salary/transaction/{id}`, `GET /ledger/voucher`
- **Nøkkelord:** lønnskjøring, lonnskjoring, lønnsbilag, lonnsbilag, lønnstransaksjon, salary transaction, er lønn bokført, godkjent lønn, lønnsutkast status
- Det finnes ingen liste-/søkeendepunkt for /salary/transaction. Finn id via GET /salary/payslip?yearFrom..&monthFrom..&fields=transaction(id) (eller filtrer payslips med wageTransactionId). Deretter GET /salary/transaction/{id}?fields=id,date,year,month,isHistorical,paySlipsAvailableDate,payslips(id,grossAmount,amount). Bokført? GET /ledger/voucher?dateFrom=<dato>&dateTo=<dato+1>&fields=id,number,description,voucherType(name) – et ikke-godkjent lønnsutkast har ikke bilag.

### ✏️ Slette et lønnsutkast (ikke-godkjent lønnskjøring)
- **Kall:** `GET /salary/transaction/{id}`, `DELETE /salary/transaction/{id}`
- **Nøkkelord:** slette lønnsutkast, slette lonnsutkast, slette lønnskjøring, fjerne lønn, angre lønnskjøring, delete salary transaction, feil lønnskjøring
- Krever eksplisitt bekreftelse. Verifiser først riktig transaksjon: GET /salary/transaction/{id}?fields=id,date,year,month,payslips(id) og at den ikke er godkjent/bokført (ingen lønnsbilag på datoen). DELETE /salary/transaction/{id} → 204. Godkjente/bokførte lønnskjøringer kan normalt ikke slettes via API-et – må tilbakestilles i Tripletex → Lønn (og ev. korrigeres i a-melding).

### ✏️ Laste opp eller fjerne vedlegg på en lønnskjøring
- **Kall:** `POST /salary/transaction/{id}/attachment`, `POST /salary/transaction/{id}/attachment/list`, `PUT /salary/transaction/{id}/deleteAttachment`
- **Nøkkelord:** vedlegg lønn, lønnsvedlegg, laste opp lønnsgrunnlag, timeliste vedlegg, attachment salary, fjerne vedlegg, flytte vedlegg til bilagsmottak
- Opplasting: multipart/form-data med feltet file (én fil) til /attachment, eller flere file-felt til /attachment/list. Fjerne: PUT /salary/transaction/{id}/deleteAttachment; sendToVoucherInbox=true flytter vedlegget til bilagsmottak i stedet for å slette, split=true deler det i ett bilag per side. Skrivende – bekreft først.

### ✏️ Registrere historisk lønn (lønn før åpningsbalanse / bytte av lønnssystem midt i året)
- **Kall:** `GET /employee`, `GET /salary/type`, `POST /salary/transaction`, `POST /ledger/voucher/historical/employee`
- **Nøkkelord:** historisk lønn, historisk lonn, lønn fra tidligere system, systembytte lønn, oppstart midt i året, hittil i år lønn, importere lønn, ishistorical, feriepengegrunnlag fra tidligere
- POST /salary/transaction med isHistorical=true, date, year/month for perioden og payslips med specifications (salaryType{id}, amount, count, rate). Historiske lønnsbilag oppdaterer lønnssystemet (feriepengegrunnlag, sammenstillingsoppgave, hittil i år) med data datert før åpningsbalansen. Send generateTaxDeduction=false (eller utelat) og legg inn faktisk forskuddstrekk som egne linjer med trekk-lønnsart. Finnes ikke den ansatte i Tripletex: POST /ledger/voucher/historical/employee [BETA] oppretter ansatt med mindre streng validering (avdeling ikke påkrevd) – persondata, kun felter som trengs. Skrivende – bekreft.

### Finne lønnsarter (nummer, a-meldingskode, skatte-/AGA-/feriepengeplikt, konto)
- **Kall:** `GET /salary/type`, `GET /salary/type/{id}`
- **Nøkkelord:** lønnsart, lonnsart, lønnsarter, wage type, salary type, a-meldingskode, inntektsbeskrivelse, hvilken konto lønn, fastlønn lønnsart, overtid lønnsart, trekk lønnsart
- GET /salary/type?isInactive=false&fields=id,number,name,ameldingWageCode,isTaxable,isPayrollTaxable,isVacationPayable,isSickPayable,accountNumberDebit(number,name),accountNumberCredit(number,name). number/name/description er «inneholder»-søk (number=10 treffer også 1000/2100 – filtrer eksakt i koden). employeeIds og showInTimesheet kan også filtrere. Lønnsarter kan bare leses via API-et – opprettelse/endring gjøres i Tripletex.

### Hente sammenstillingsoppgave (lønns- og trekkoppgave) for en ansatt og et år
- **Kall:** `GET /employee`, `GET /salary/compilation`, `GET /salary/compilation/pdf`
- **Nøkkelord:** sammenstillingsoppgave, lønns- og trekkoppgave, lonns og trekkoppgave, lønnsoppgave, årsoppgave, arsoppgave, årslønn, trekk hittil i år, salary compilation
- employeeId er påkrevd; year (1900–2100) er valgfri og er som standard FORRIGE år. GET /salary/compilation?employeeId=..&year=..&fields=year,vacationPayBasis,wages(description,amount,taxable),expenses(description,amount),taxDeductions(description,amount),mandatoryTaxDeductions(description,amount). PDF: GET /salary/compilation/pdf?employeeId=..&year=.. (binær). Persondata – vis bare nødvendige summer, pseudonymiser, PDF lagres kun lokalt på forespørsel.

### ✏️ Se eller endre lønnsinnstillinger (beregningsregel og kommune/sone for arbeidsgiveravgift)
- **Kall:** `GET /salary/settings`, `PUT /salary/settings`, `GET /municipality`
- **Nøkkelord:** lønnsinnstillinger, lonnsinnstillinger, beregningsregel aga, sone arbeidsgiveravgift, avgiftssone, kommune aga, aga-sats, hvilken sone, payroll tax zone, salary settings
- GET /salary/settings?fields=payrollTaxCalcMethod,municipality(id,number,name,payrollTaxZone). payrollTaxCalcMethod: AA generelle næringer, BB statsforvaltning/helseforetak, CC unntatte næringer (og foretak i økonomiske vansker), DD jordbruk/skogbruk/fiske, EE kun rapportering av forskuddstrekk, GG godstransport på vei (C2 og JJ finnes også i enum, uten forklaring i spec). Kommune/sone: GET /municipality?includePayrollTaxZones=true&fields=id,number,name,payrollTaxZone. Endring: PUT /salary/settings med {municipality:{id}, payrollTaxCalcMethod} (objektet har ikke id/version). Merk at AGA-kommune også kan settes per arbeidsforhold (employment/details.payrollTaxMunicipalityId). Skrivende – bekreft; påvirker AGA i fremtidige lønnskjøringer.

### Se feriepengeinnstillinger (feriepengesats og feriedager) for et år
- **Kall:** `GET /salary/settings/holiday`
- **Nøkkelord:** feriepengesats, feriepengeprosent, 10,2 prosent, 12 prosent, 5 uker ferie, feriedager, over 60, 6g, ferieinnstillinger, holiday settings
- GET /salary/settings/holiday?fields=id,version,year,days,vacationPayPercentage1,vacationPayPercentage2,isMaxPercentage2Amount6G. vacationPayPercentage1 = ordinær sats (10,2 %, eller 12 % ved 5 ukers ferie), vacationPayPercentage2 = sats for ansatte over 60, isMaxPercentage2Amount6G = tillegget for 60+ begrenses til grunnlag opp til 6G. NB: helligdager/fridager ligger i /timesheet/companyHoliday, ikke her.

### ✏️ Opprette, endre eller slette feriepengeinnstillinger
- **Kall:** `GET /salary/settings/holiday`, `POST /salary/settings/holiday`, `PUT /salary/settings/holiday/{id}`, `POST /salary/settings/holiday/list`, `PUT /salary/settings/holiday/list`, `DELETE /salary/settings/holiday/list`
- **Nøkkelord:** endre feriepengesats, sette feriepengesats, 5 uker ferie, ny feriepengeinnstilling, slette feriepengeinnstilling, feriedager, vacation pay settings
- Opprett: POST /salary/settings/holiday {year, days, vacationPayPercentage1, vacationPayPercentage2, isMaxPercentage2Amount6G}; flere år samtidig: POST /salary/settings/holiday/list med array (uten id/version). Endre: hent id+version med GET, deretter PUT /salary/settings/holiday/{id} eller PUT .../list (array med id+version). Slette: DELETE /salary/settings/holiday/list?ids=1,2 (ingen DELETE på enkelt-id). Skrivende – bekreft; påvirker feriepengeberegningen.

### Se firmaets pensjonsordninger (OTP) og pensjonsleverandør
- **Kall:** `GET /salary/settings/pensionScheme`, `GET /salary/settings/pensionScheme/{id}`, `GET /pension`
- **Nøkkelord:** pensjonsordning, otp, obligatorisk tjenestepensjon, tjenestepensjon, pensjonsleverandør, pensjonsinnretning, avtalenummer pensjon, pensjon a-melding, pension scheme
- GET /salary/settings/pensionScheme?fields=id,version,pensionSchemeId,number,startDate,endDate (number = avtale-/ordningsnummer; filteret number= er eksakt). Slå opp leverandør med GET /pension?query=<navn>&fields=id,displayName,number,fromDate,toDate (spec-summary sier feilaktig «Find countries» – den gir pensjonsinnretninger). pensionSchemeId peker trolig på id i /pension – verifiser. Brukes til å kontrollere at OTP er registrert før a-melding.

### ✏️ Registrere, endre eller avslutte pensjonsordning (OTP)
- **Kall:** `GET /pension`, `POST /salary/settings/pensionScheme`, `POST /salary/settings/pensionScheme/list`, `PUT /salary/settings/pensionScheme/{id}`, `PUT /salary/settings/pensionScheme/list`, `DELETE /salary/settings/pensionScheme/{id}`, `DELETE /salary/settings/pensionScheme/list`
- **Nøkkelord:** registrere otp, ny pensjonsordning, endre pensjonsordning, avslutte pensjonsordning, bytte pensjonsleverandør, pensjonsavtale, slette pensjonsordning
- Finn leverandør med GET /pension?query=... Opprett: POST /salary/settings/pensionScheme {pensionSchemeId, number (avtalenummer), startDate, endDate?}; flere: POST .../list (array). Avslutte/bytte leverandør: PUT /salary/settings/pensionScheme/{id} med endDate (+ version) og opprett ny ordning – foretrekk dette fremfor sletting så historikken bevares. Slette: DELETE /{id} eller DELETE /list?ids=... Skrivende – bekreft.

### Se normalarbeidstid for firmaet (og per ansatt)
- **Kall:** `GET /salary/settings/standardTime/byDate`, `GET /salary/settings/standardTime`, `GET /salary/settings/standardTime/{id}`, `GET /employee/standardTime/byDate`
- **Nøkkelord:** normalarbeidstid, normaltid, arbeidstid, timer per dag, 7,5 timer, 37,5 timer, standard arbeidstid, fleksitid grunnlag, standard time
- Gjeldende for firmaet: GET /salary/settings/standardTime/byDate?date=yyyy-MM-dd (standard i dag)&fields=id,fromDate,hoursPerDay. Historikk: GET /salary/settings/standardTime?fields=id,version,fromDate,hoursPerDay. Avvik for én ansatt: GET /employee/standardTime/byDate?employeeId=..&date=.. (persondata – minimalt med fields).

### ✏️ Registrere ny eller endre normalarbeidstid for firmaet
- **Kall:** `GET /salary/settings/standardTime`, `POST /salary/settings/standardTime`, `PUT /salary/settings/standardTime/{id}`
- **Nøkkelord:** endre normalarbeidstid, ny arbeidstid, kortere arbeidstid, timer per dag, sette normaltid, standard time update
- Ny arbeidstid fra en dato: POST /salary/settings/standardTime {fromDate, hoursPerDay} (f.eks. 7.5). Rette en eksisterende rad: GET for id+version, deretter PUT /salary/settings/standardTime/{id}. Foretrekk ny rad med fromDate fremfor å endre historikk (påvirker timeliste/fleksitid bakover). Skrivende – bekreft.

### ✏️ Avstemme forskuddstrekk for en termin (hovedbok mot a-melding og Skatteetaten)
- **Kall:** `POST /salary/taxDeduction/reconciliation/context`, `GET /salary/taxDeduction/reconciliation/{reconciliationId}/overview`, `GET /salary/taxDeduction/reconciliation/{reconciliationId}/paymentsOverview`, `GET /salary/taxDeduction/reconciliation/{reconciliationId}/balanceAndOwedAmount`, `GET /ledger/posting`
- **Nøkkelord:** avstemme forskuddstrekk, avstemme skattetrekk, forskuddstrekk termin, skattetrekk avstemming, 2600, a07, a-melding mot hovedbok, avvik skattetrekk, tax deduction reconciliation
- 1) POST /salary/taxDeduction/reconciliation/context {customerId, year, term} → value.reconciliationId (oppretter bare en avstemmingskontekst, ingen bilag – men er en POST, så bekreft). 2) GET .../{reconciliationId}/overview: account, startDate/endDate, registeredPayments per måned (ledgerSum, ameldingSum, taxAuthoritiesSum, discrepancy, epochDays) og aggregert avvik. 3) GET .../paymentsOverview: innbetalinger hittil i år (ledgerSum, ameldingSum, paidAmount, restAmount, paymentDate). 4) GET .../balanceAndOwedAmount: saldo vs skyldig trekk. 5) Avvik ≠ 0 → drill ned med GET /ledger/posting?dateFrom&dateTo&accountNumberFrom=2600&accountNumberTo=2600. Rapporter kun aggregater.

### ✏️ Avstemme arbeidsgiveravgift for en termin (per sone)
- **Kall:** `POST /salary/payrollTax/reconciliation/context`, `GET /salary/payrollTax/reconciliation/{reconciliationId}/overview`, `GET /salary/payrollTax/reconciliation/{reconciliationId}/paymentsOverview`, `GET /balanceSheet`
- **Nøkkelord:** avstemme arbeidsgiveravgift, avstemme aga, aga termin, skyldig arbeidsgiveravgift, aga per sone, grunnlag arbeidsgiveravgift, 2770, 5400, a07, payroll tax reconciliation
- 1) POST /salary/payrollTax/reconciliation/context {customerId, year, term} → reconciliationId. 2) GET .../overview: ledgerSum, ameldingSum, taxAuthoritiesSum, discrepancy, ledgerUri og aggregatedZones (zone, displayName, taxPercentage, amountBasisSum, reimbursementSum, pensionSum, payrollTaxSum) – kontroller grunnlag × sats per sone. 3) GET .../paymentsOverview: innbetalt/rest per termin hittil i år. 4) Avvik → GET /balanceSheet?dateFrom&dateTo&accountNumberFrom=2770&accountNumberTo=2789 og 5400–5499.

### ✏️ Avstemme feriepenger (skyldige feriepenger og AGA av feriepenger)
- **Kall:** `POST /salary/holidayAllowance/reconciliation/context`, `GET /salary/holidayAllowance/reconciliation/{reconciliationId}/holidayAllowanceDetails`, `GET /salary/holidayAllowance/reconciliation/{reconciliationId}/holidayAllowanceSummary`
- **Nøkkelord:** avstemme feriepenger, feriepengeavstemming, skyldige feriepenger, 2940, aga av feriepenger, feriepengeliste mot hovedbok, opptjent feriepenger, holiday allowance reconciliation
- 1) POST /salary/holidayAllowance/reconciliation/context {customerId, year, term} → reconciliationId. 2) GET .../holidayAllowanceDetails: outstandingVacationPayGeneralLedger vs outstandingVacationPayHolidayAllowanceReport (skyldige feriepenger hovedbok vs feriepengeliste) og payrollTaxVacationPayGeneralLedger vs payrollTaxVacationPayHolidayAllowanceReport (AGA av feriepenger). 3) GET .../holidayAllowanceSummary: rates og per sats creditPrevYearsByRate, earnedThisYearByRate, earnedAndPaidThisYearByRate, creditThisYearByRate + totaler. Differanse → sjekk konto 2940/2785 i hovedbok.

### ✏️ Avstemme påleggstrekk (utleggstrekk/bidragstrekk) for en termin
- **Kall:** `POST /salary/mandatoryDeduction/reconciliation/context`, `GET /salary/mandatoryDeduction/reconciliation/{reconciliationId}/overview`, `GET /salary/mandatoryDeduction/reconciliation/{reconciliationId}/paymentsOverview`
- **Nøkkelord:** påleggstrekk, paleggstrekk, utleggstrekk, bidragstrekk, trekkpålegg, trekk i lønn, avstemme trekk, mandatory deduction reconciliation
- 1) POST /salary/mandatoryDeduction/reconciliation/context {customerId, year, term} → reconciliationId. 2) GET .../overview: account, ledgerSum, ameldingSum, discrepancy og periodOverviews (epochDays = dager siden 1970-01-01 → måned, ledgerSum, ameldingSum, discrepancy, ledgerUri). 3) GET .../paymentsOverview: innbetalt til kreditor/NAV hittil i år (paidAmount, restAmount). Persondata – ikke vis hvem som har trekk.

### ✏️ Avstemme finansskatt på lønn for en termin
- **Kall:** `POST /salary/financeTax/reconciliation/context`, `GET /salary/financeTax/reconciliation/{reconciliationId}/overview`, `GET /salary/financeTax/reconciliation/{reconciliationId}/paymentsOverview`
- **Nøkkelord:** finansskatt, finansskatt på lønn, finansskatt pa lonn, finansforetak, avstemme finansskatt, finance tax reconciliation
- Kun relevant for finansforetak som betaler finansskatt på lønn (ellers tomt/0). 1) POST /salary/financeTax/reconciliation/context {customerId, year, term} → reconciliationId. 2) GET .../overview: ledgerSum, ameldingSum, taxAuthoritiesSum, discrepancy, financeTaxBasisSum, financeTaxSum, ledgerUri. 3) GET .../paymentsOverview: innbetalinger hittil i år.

### ✏️ Sjekke at skattetrekkskontoen dekker skyldig forskuddstrekk
- **Kall:** `POST /salary/taxDeduction/reconciliation/context`, `GET /salary/taxDeduction/reconciliation/{reconciliationId}/balanceAndOwedAmount`, `GET /balanceSheet`
- **Nøkkelord:** skattetrekkskonto, saldo skattetrekkskonto, dekning skattetrekk, underdekning skattetrekk, skyldig forskuddstrekk, 1950, 2600, bankgaranti
- 1) POST /salary/taxDeduction/reconciliation/context {customerId, year, term} → reconciliationId. 2) GET .../balanceAndOwedAmount: taxDeductionBalance (saldo), taxDeductionOwedAmount (skyldig), taxDeductionAccountNumber/Name. Saldo < skyldig → underdekning; skattetrekksmidler skal stå på egen konto (eller bankgaranti). 3) Kontroll i hovedbok: GET /balanceSheet?dateFrom&dateTo&accountNumberFrom=1950&accountNumberTo=1950 og 2600 (kontonummer kan variere – sjekk kontoplan).

### ✏️ Full lønnsavstemming / A07-avstemming for en termin og hittil i år
- **Kall:** `POST /salary/taxDeduction/reconciliation/context`, `GET /salary/taxDeduction/reconciliation/{reconciliationId}/overview`, `POST /salary/payrollTax/reconciliation/context`, `GET /salary/payrollTax/reconciliation/{reconciliationId}/overview`, `POST /salary/holidayAllowance/reconciliation/context`, `GET /salary/holidayAllowance/reconciliation/{reconciliationId}/holidayAllowanceDetails`, `POST /salary/mandatoryDeduction/reconciliation/context`, `GET /salary/mandatoryDeduction/reconciliation/{reconciliationId}/overview`, `GET /balanceSheet`, `GET /ledger/posting`
- **Nøkkelord:** lønnsavstemming, lonnsavstemming, avstemme lønn, avstem lønnsområdet, a07, a-melding avstemming, terminavstemming lønn, lønn mot hovedbok, årsoppgjør lønn, arsoppgjor lonn
- Opprett kontekst for hver type (taxDeduction, payrollTax, holidayAllowance, mandatoryDeduction, ev. financeTax) med samme {customerId, year, term}; hent overview/paymentsOverview/holidayAllowanceDetails. Supplér med GET /balanceSheet (dateTo eksklusiv; accountNumberFrom/To 2600–2999 og 5000–5999; fields=account(number,name),balanceIn,balanceChange,balanceOut) og GET /ledger/posting?type=WAGE for drill-down. Mot A07 fra Skatteetaten: bruk skillen lonnsavstemming-a07 (Excel/PDF). Rapporter aggregert (per ytelse/konto), aldri navngitte ansatte.

### ✏️ Markere lønnsavstemming som avstemt, be om kontroll eller merke som kontrollert
- **Kall:** `GET /accountingOffice/reconciliations/{reconciliationId}/control`, `PUT /accountingOffice/reconciliations/{reconciliationId}/control/:reconcile`, `PUT /accountingOffice/reconciliations/{reconciliationId}/control/:requestControl`, `PUT /accountingOffice/reconciliations/{reconciliationId}/control/:controlReconciliation`
- **Nøkkelord:** markere avstemt, avstemt, kontrollert, be om kontroll, godkjenne avstemming, avstemmingskontroll, reconcile, request control, regnskapsfører kontroll
- reconciliationId kommer fra context-POST i lønnsavstemmingen. :reconcile markerer som avstemt; :requestControl tar body = array med ansatt-id-er (kontrollører); :controlReconciliation markerer som kontrollert. GET .../control viser historikk (employee, timestamp, type). Regnskapsførerfunksjon – 403 hvis brukeren mangler regnskapskontor-tilgang. Skrivende – bekreft.

### Finne lønnsposteringer og lønnsbilag i hovedboken
- **Kall:** `GET /ledger/posting`, `GET /ledger/voucherType`, `GET /ledger/voucher`
- **Nøkkelord:** lønnsposteringer, lonnsposteringer, lønnsbilag, lonnsbilag, lønn i hovedbok, lønnskostnad, 5000, wage postings, lønnsbilag nummer
- GET /ledger/posting?dateFrom=..&dateTo=.. (begge påkrevd, dateTo eksklusiv)&type=WAGE&fields=id,date,amount,description,account(number,name),voucher(id,number) – ev. accountNumberFrom/To (5000–5999, 2600, 2770). employeeId-filter bare når oppgaven krever det. Lønnsbilag: finn bilagstype-id med GET /ledger/voucherType?name=Lønn, deretter GET /ledger/voucher?dateFrom&dateTo&typeId=..&fields=id,number,date,description.

### Hente saldo på lønnsrelaterte kontoer (skyldig skattetrekk, AGA, feriepenger, lønnskostnad)
- **Kall:** `GET /balanceSheet`
- **Nøkkelord:** saldo skattetrekk, saldo aga, skyldig feriepenger saldo, 2600, 2770, 2780, 2940, lønnskostnad, saldobalanse lønn, balance lønnskontoer
- GET /balanceSheet?dateFrom=yyyy-01-01&dateTo=<dag etter periodeslutt> (eksklusiv)&accountNumberFrom=2600&accountNumberTo=2999&fields=account(number,name),balanceIn,balanceChange,balanceOut. Typisk 2600 forskuddstrekk, 2770 skyldig AGA, 2780/2785 påløpt AGA (feriepenger), 2940 skyldige feriepenger; lønnskostnad 5000–5999 (kjør eget kall). Kontonummer kan avvike – sjekk kontoplanen.

### ✏️ Bokføre betaling av forskuddstrekk/arbeidsgiveravgift eller manuell lønnskorrigering
- **Kall:** `GET /ledger/account`, `POST /ledger/voucher`
- **Nøkkelord:** betale skattetrekk, betale aga, bokføre skattetrekk, bokføre arbeidsgiveravgift, innbetaling skatteetaten, lønnskorrigering, manuell lønnspostering, periodisering lønn, avsetning feriepenger
- Finn konto-id: GET /ledger/account?number=2600&fields=id,number,name (tilsvarende 2770, 1920). POST /ledger/voucher med date, description og postings som balanserer til 0 (f.eks. debet 2600/2770, kredit bank 1920; bruttobeløp, 2 desimaler). Ordinær lønn skal bokføres via lønnskjøringen (salary/transaction), ikke manuelt. Skrivende – bekreft konto, beløp og dato først.

### ✏️ Se eller oppdatere Altinn-oppsett for a-melding
- **Kall:** `GET /company/settings/altinn`, `PUT /company/settings/altinn`
- **Nøkkelord:** altinn, altinn-id, altinn passord, altinn oppsett, a-melding innsending, kan ikke sende a-melding, skattekort altinn
- Lesing: GET /company/settings/altinn?fields=altInnId (hent/vis aldri passord). PUT /company/settings/altinn oppdaterer altInnId og altInnPassword – Claude skal ALDRI skrive inn eller sette passord; be brukeren gjøre endringen selv i Tripletex. Innsending av a-melding og henting av skattekort finnes ikke i det offentlige API-et.

### ✏️ Registrere lønnstillegg (lønnsart) via timelisten for neste lønnskjøring
- **Kall:** `GET /salary/type`, `GET /timesheet/salaryTypeSpecification`, `GET /timesheet/salaryTypeSpecification/{id}`, `POST /timesheet/salaryTypeSpecification`, `PUT /timesheet/salaryTypeSpecification/{id}`, `DELETE /timesheet/salaryTypeSpecification/{id}`
- **Nøkkelord:** lønnstillegg, lonnstillegg, tillegg timeliste, overtid, kveldstillegg, lønnsart timeliste, variable tillegg, salary type specification, registrere tillegg
- [BETA]-endepunkter. Lønnsart-id: GET /salary/type?showInTimesheet=true&fields=id,number,name. Registrer: POST /timesheet/salaryTypeSpecification {employee:{id}, salaryType:{id}, date, count, description} – kun ÉN per ansatt/dato/lønnsart (duplikat gir feil; endre heller eksisterende). Kontroll: GET /timesheet/salaryTypeSpecification?dateFrom&dateTo (til eksklusiv)&employeeId&fields=id,version,date,count,salaryType(number). Endre: PUT /timesheet/salaryTypeSpecification/{id} med id+version. Feil: DELETE /timesheet/salaryTypeSpecification/{id}. Skrivende – bekreft.

### Sjekke arbeidsforhold og lønnsgrunnlag før lønnskjøring (månedslønn, stillingsprosent, skattetrekkskode, AGA-kommune)
- **Kall:** `GET /employee/employment`, `GET /employee/employment/details`
- **Nøkkelord:** arbeidsforhold, månedslønn, manedslonn, årslønn, stillingsprosent, timelønn, skattetrekkskode, hovedarbeidsgiver, lønnsgrunnlag, employment details, aga-kommune, aga sone ansatt, avlønningstype, arbeidsforholdstype
- GET /employee/employment?employeeId=..&fields=id,startDate,endDate,isMainEmployer,taxDeductionCode (loennFraHovedarbeidsgiver|loennFraBiarbeidsgiver|pensjon|…; tom = ikke satt). GET /employee/employment/details?employmentId=<employment.id>&fields=date,monthlySalary,annualSalary,hourlyWage,percentageOfFullTimeEquivalent,remunerationType,employmentType,employmentForm,payrollTaxMunicipalityId(number,name,payrollTaxZone) – flere rader per arbeidsforhold, siste date gjelder. monthlySalary er skrivebeskyttet (endres via annualSalary). Persondata – bruk fields minimalt og vis aggregert/pseudonymisert. Endringer gjøres med PUT /employee/employment/details/{id} (ansatte-gruppen).

### ✏️ Bestille og lese A07 fra Skatteetaten (avstemmingsmodulen, via Altinn-systembruker)
- **Kall:** `GET /salary/taxDeduction/reconciliation/{reconciliationId}/overview`, `GET /salary/payrollTax/reconciliation/{reconciliationId}/overview`
- **Nøkkelord:** a07, bestille a07, hente a07, hent a07, a07 skatteetaten, a07-rapport, amelding reconciliation report, altinn a07, skatteetaten lønn, avstemme mot a07, taxauthority
- UDOKUMENTERT/INTERNT (tskinternal), funnet i UI-koden (altinn-sync-widget), testet OK 2026-09-23 på klient A T4. KALL FRA KLIENTENS KONTEKST: Basic-auth companyId = klient-id fra /company/>withLoginAccess (eksempel: <kunde-id>); contextId = session-companyId fra GET /token/session/>whoAmI?fields=companyId (eksempel: <company-id> – bekreft org.nr. med GET /company/{companyId}). 0) Forutsetning: GET /altinn/systemuser/hasSystemUser?isAgent=false = true i klientkonteksten. 1) Bestill: POST /salary/tskinternal/amelding/reconciliation/reports?contextId=<id> body {year, monthFrom, monthTo} (termin 4 = 7–8) → 204. Asynkront (SSE amelding_reconciliation_report); spør GET .../latest hvert 5. sek til ny id (tok ~10–30 sek). 2) Les: GET /salary/tskinternal/amelding/reconciliation/reports/latest?contextId=<id>&fromYearMonth=2026-07&toYearMonth=2026-08 → {id, reconciliationTimestamp, from, to, details{paymentInformation{sumWithholdingTax,sumPayrollTax,sumFinanceTax}, submissions[] (month, deliveryTimestamp, taxAndWithholdingTotal), businesses[].payrollTax (sone, grunnlag, sats)}} – kun aggregater. Rapporter lagres per foretakskontekst: fra klientkonteksten ses også rapporter hentet i UI. ⚠️ ALDRI bestill fra byråkontoen (companyId 0) med contextId=klient: da hentes BYRÅETS EGEN A07 (Silfer AS, rapport 12595) og contextId ignoreres. Kontroller alltid A07-tall mot ameldingSum før bruk. Bestilling sender forespørsel til Skatteetaten – krever bekreftelse. Relatert: GET /salary/tskinternal/amelding/ameldingStatus?date=&contextId=, GET /salary/reconciliation/{kunde-id}/aggregatedContext?year&term, GET /accountingOffice/reconciliations/permissions/{kunde-id}.

### ✏️ Lønnsavstemming i avstemmingsmodulen – full arbeidsflyt (opprette, A07, kommentere, fullføre)
- **Kall:** `POST /salary/taxDeduction/reconciliation/context`, `POST /salary/payrollTax/reconciliation/context`, `POST /salary/holidayAllowance/reconciliation/context`, `POST /salary/mandatoryDeduction/reconciliation/context`, `POST /salary/financeTax/reconciliation/context`, `GET /salary/taxDeduction/reconciliation/{reconciliationId}/overview`, `GET /salary/payrollTax/reconciliation/{reconciliationId}/overview`, `GET /salary/holidayAllowance/reconciliation/{reconciliationId}/holidayAllowanceDetails`, `GET /accountingOffice/reconciliations/{reconciliationId}/control`
- **Nøkkelord:** lønnsavstemming, avstemmingsmodul lønn, fullføre lønnsavstemming, avstemme lønn termin, skattetrekk avstemming, aga avstemming, feriepenger avstemming, utleggstrekk, finansskatt, a07 avstemming, aggregatedcontext
- Testet OK på klient A termin 4 2026 (alle 5 fullført). Se docs/avstemmingsmodul.md. Byråkontoen (companyId 0). 1) POST context for taxDeduction, payrollTax, holidayAllowance, mandatoryDeduction, financeTax {customerId, year, term}. Oversikt: GET /salary/reconciliation/{kunde-id}/aggregatedContext?year&term&fields=reconciliations(id,type,status). 2) A07 fra KLIENTENS kontekst (oppgaven «Bestille og lese A07»); taxAuthoritiesSum fylles etterpå. 3) Les overview/holidayAllowanceDetails; ledgerSum = hovedbok, ameldingSum = a-melding, taxAuthoritiesSum = A07. 4) Avvik: finn bilaget, kommenter riktig referenceId (feriepenger = kontonummer 2940/2785, trekk = epochDays for måneden). 5) PUT /accountingOffice/reconciliations/{id}/:complete → COMPLETED, låst, PDF i document. 422 nevner referenceId som mangler kommentar. Uten avvik går :complete rett gjennom. Skrivende – krever bekreftelse.

### Se status på a-melding for en måned (levert, avvist, ikke sendt, påløpt/ubetalt trekk og AGA)
- **Kall:** 
- **Nøkkelord:** a-melding status, amelding status, status a-melding, a-melding levert, er a-meldingen sendt, avvist a-melding, tilbakemelding a-melding, ameldingstatus, oversikt a-meldinger
- INTERNT KALL (fra GET /v2/openapi.json?internal=true – ikke i offentlig spec, kan endres uten varsel). Kalles fra KLIENTENS kontekst (Basic-auth companyId = klient-id) – ALDRI fra byråkontoen, da gjelder det byråets egen a-melding. Skript: npm run amelding -- status --client "klient" --maned ÅÅÅÅ-MM (og: oversikt --ar ÅÅÅÅ). Kall: GET /salary/tskinternal/amelding/ameldingStatus?date=ÅÅÅÅ-MM-01&fields=ameldingSummaryStatus,ameldingDetailedStatus,lastAmeldingActionTime,taxPeriodName,taxDeductionAccrued,payrollTaxAccrued,taxDeductionNotPaid,payrollTaxNotPaid (hent aldri ameldingActorEmployee – persondata). ameldingDetailedStatus: noAmeldingExists, ameldingExistsNotSent, ameldingRejected, nonReportedWageinfo m.fl. Liste over a-meldinger: GET /tsk/salaryv2/overview/amessage?startMonth=ÅÅÅÅ-MM&endMonth=ÅÅÅÅ-MM (id, period, date, status, voucherId). Spør alltid hvilken måned – a-meldingen for en måned har frist den 5. i måneden etter.

### ✏️ Sende a-melding for en måned til Skatteetaten
- **Kall:** 
- **Nøkkelord:** send a-melding, sende a-melding, send amelding, levere a-melding, innsending a-melding, a-melding innsending, rapportere lønn skatteetaten, kun arbeidsforhold a-melding, kan ikke sende a-melding
- INTERNT KALL (fra GET /v2/openapi.json?internal=true – ikke i offentlig spec, kan endres uten varsel). Kalles fra KLIENTENS kontekst (Basic-auth companyId = klient-id) – ALDRI fra byråkontoen, da gjelder det byråets egen a-melding. Skript: npm run amelding -- send --client "klient" --maned ÅÅÅÅ-MM [--kun-arbeidsforhold] [--bilagsdato ÅÅÅÅ-MM-DD] --bekreft (uten --bekreft: bare status og hva som ville blitt sendt). Kall: POST /salary/tskinternal/amelding/send body {date:"ÅÅÅÅ-MM-01", voucherDate?, employmentInformationOnly?} → 201 {year, month, kind (WAGE|EMPLOYMENT_ONLY|NOTHING_TO_SEND), ameldingId, ameldingNumber, ameldingWageId, ameldingWageRegisteredNow, employmentCount, voucherCreated, voucherId, voucherNumber, largeFileUploadInProgress}. Registrerer a-meldingen fra månedens lønnskjøringer (og pensjon) hvis det ikke er gjort, og sender. Kan lage bilag (avrunding trekk / AGA-korreksjon) datert voucherDate (standard siste dag i måneden). Avvist forrige gang → sendes som ny innsending; rett feilen først. Krever lønnsmodul og lønnsadmin-rolle. LOVPÅLAGT INNLEVERING SOM IKKE KAN TREKKES TILBAKE: sjekk status først, fortell brukeren hva som sendes, og få eksplisitt ja i chat for den klienten og måneden før --bekreft. IKKE TESTET (2026-09-23). Flyten i Tripletex-UI: opprett a-meldingen først, send etter ID-porten-innlogging hos brukeren. API-tokenet har ingen ID-porten-økt (GET /salary/tskinternal/systemuser/loginstatus = 403), så send-kallet kan feile eller bare registrere – les status etterpå.

### Pensjon (OTP): bokført på 5940–5949 mot pensjon rapportert i a-meldingene og A07, per termin
- **Kall:** `GET /ledger/posting`, `GET /salary/payrollTax/reconciliation/{reconciliationId}/overview`
- **Nøkkelord:** pensjon a-melding, otp a-melding, 5940, pensjon 5940, tilskudd og premie til pensjon, pensjon betalt i perioden, registrere pensjon, pensjonsbilag, avstemme pensjon, obligatorisk tjenestepensjon, rapportert pensjon
- Skript (kun lesing, testet 2026-09-23 på klient C – der er kontoen 5945): npm run pensjon -- --client "klient" --ar ÅÅÅÅ [--konto 5945] → per termin: bokført (per måned), pensjon i a-meldingen, pensjon i A07, avvik. Kilder: 1) GET /ledger/posting?accountNumberFrom=5940&accountNumberTo=5949. 2) A-melding: eksisterende PAYROLL_TAX-avstemminger i byråkontoen (GET /accountingOffice/reconciliations, companyId 0) → GET /salary/payrollTax/reconciliation/{id}/overview → sum aggregatedZones[].pensionSum (null/tom før a-meldingen er sendt). Skriptet oppretter ingen avstemminger. 3) A07: INTERNT GET /salary/tskinternal/amelding/reconciliation/reports/latest?contextId=<whoAmI.companyId>&fromYearMonth&toYearMonth fra klientkonteksten → details.businesses[].payrollTax.pensionContributionsAndPremiums[].basisAmount. Pensjon rapporteres i hele kroner – øreavvik < 1 kr er likt. Pensjonsbilag i lønn (INTERNT GET /tsk/salaryv2/overview/pension) gir 403 med API-token – alle /tsk/salaryv2/* krever nettleserinnlogging. REGISTRERE pensjon (Lønn → Pensjon, /execute/reimbursementMenu#obligatoryPension, JSON-RPC ObligatoryPensionForm.store) finnes ikke i API-et; /execute-sider sender API-tokenet til innlogging (302). Må gjøres i Tripletex-UI (brukeren, eller Claude i Chrome hvis brukeren ber om det).

**Fallgruver:**
- Alle lønnsendepunkter er merket PERSONDATA: bruk alltid fields= minimalt, hent aldri navn/fødselsnr./kontonr. unødig, bruk redact() på utskrift og rapporter aggregert eller som «ansatt 1/2». PDF-er (lønnsslipp, sammenstillingsoppgave) inneholder full persondata – lagre kun lokalt på forespørsel, aldri del.
- Avstemmingsendepunktene ({reconciliationId}/overview, paymentsOverview, holidayAllowanceDetails/Summary, balanceAndOwedAmount) krever en reconciliationId som hentes med POST .../reconciliation/context {customerId, year, term}. Context-POST lager bare en avstemmingskontekst (ingen bilag), men er teknisk et skrivekall.
- customerId i context-body = klientselskapet (Tripletex kaller klienten «customer»), trolig company-id fra GET /token/session/>whoAmI eller GET /company/>withLoginAccess – ikke en kunde fra kundereskontroen. Verifiser med ett testkall første gang. term = terminnummer (normalt 1–6, tomånedlige terminer).
- Avstemming markeres som avstemt/kontrollert via /accountingOffice/reconciliations/{reconciliationId}/control/:reconcile, :requestControl og :controlReconciliation (action-endepunkter med kolon). Krever regnskapskontor-tilgang (403 ellers).
- GET /salary/payslip: yearTo og monthTo er EKSKLUSIVE (én måned = monthFrom=9&monthTo=10, yearFrom=2026&yearTo=2027). voucherDateTo er også eksklusiv.
- Det finnes ingen liste/søk for /salary/transaction – finn transaksjons-id via GET /salary/payslip (fields=transaction(id)).
- POST /salary/transaction lagrer en IKKE-godkjent lønnskjøring uten bilag (lønnsutkast). Godkjenning/bokføring gjøres av brukeren i Tripletex. A-melding kan sendes med npm run amelding -- send, men bare etter eksplisitt ja.
- Det offentlige API-et bruker IKKE ansattes «faste lønnslinjer»: en payslip uten specifications blir tom. Linjene må sendes eksplisitt (utledes fra tidligere lønnsslipper og employment/details) og vises i UI som manuelle tillegg/trekk.
- generateTaxDeduction=true beregner skattetrekk ut fra skattekortet som allerede ligger i Tripletex; spec angir ingen default – send parameteren eksplisitt. Det finnes ikke noe skattekort-endepunkt i det offentlige API-et – brukeren må trykke «Hent skattekort» i Tripletex → Lønn. Tripletex MCP-connectoren (fetch_taxcards/order_taxcards/get_taxcard_status) brukes bare hvis brukeren ber om det.
- A-melding (status, oversikt, innsending) og A07 finnes ikke i den OFFENTLIGE specen, men som interne kall i GET /v2/openapi.json?internal=true (1900+ stier mot 550 offentlige – sjekk den før du sier at noe ikke finnes). Bruk npm run amelding (status/oversikt/send). Innsending er lovpålagt og kan ikke trekkes tilbake – send aldri uten eksplisitt ja for klient og måned.
- Godkjente/bokførte lønnskjøringer kan normalt ikke slettes med DELETE /salary/transaction/{id}; de må tilbakestilles i Tripletex. Slett kun lønnsutkast etter bekreftelse.
- Ugyldige datoer i lønnskjøring (f.eks. 31.09) gir feil – bruk siste dag i måneden.
- GET /salary/type: number/name/description er «inneholder»-filtre, ikke eksakte. Lønnsarter kan kun leses i API-et.
- GET /salary/compilation(/pdf): employeeId er påkrevd og year er som standard FORRIGE år.
- GET /pension har feil summary i specen («Find countries») – den returnerer pensjonsinnretninger (GlobalPension: displayName, number, fromDate, toDate).
- /salary/settings/holiday gjelder feriepengesats og feriedager – helligdager/fridager ligger i /timesheet/companyHoliday. Firmaets normalarbeidstid ligger i /salary/settings/standardTime, per ansatt i /employee/standardTime.
- /list-endepunkter (holiday, pensionScheme) tar arrays: POST uten id/version, PUT med id+version; DELETE .../list bruker ids=1,2,3. Enkeltvis DELETE finnes ikke for holiday.
- PUT /salary/settings: SalarySettings har ikke id/version – send bare municipality{id} og payrollTaxCalcMethod (AA|BB|CC|C2|DD|EE|GG|JJ). Sone/kommune finnes via GET /municipality?includePayrollTaxZones=true.
- PUT /company/settings/altinn tar Altinn-passord – Claude skal aldri skrive inn passord/legitimasjon; brukeren må gjøre det selv.
- Vedlegg til lønnskjøring sendes som multipart/form-data (felt file). deleteAttachment med sendToVoucherInbox=true flytter vedlegget til bilagsmottak i stedet for å slette det.
- 403 på lønnsendepunkter betyr som regel at klienten mangler lønnsmodul eller brukeren mangler lønnsrettigheter – ikke at endepunktet mangler. Finansskatt-avstemming er bare relevant for finansforetak.
- /timesheet/salaryTypeSpecification og /ledger/voucher/historical/employee er [BETA].
- Avstemmingsresponsene: epochDays = antall dager siden 1970-01-01 (konverter til måned: new Date(epochDays*86400000)). I paymentsOverview er payments[].endDate EKSKLUSIV. ledgerUri/uri er lenker til Tripletex-UI, ikke API-kall. For forskuddstrekk er aggregatedDiscrepancy avviket mellom hovedbok og Skatteetaten (ikke a-melding), mens discrepancy per måned er hovedbok mot a-melding.
- PUT på settings-objekter med id (salary/settings/holiday/{id}, pensionScheme/{id}, standardTime/{id}, timesheet/salaryTypeSpecification/{id}) krever gjeldende version – hent med GET først, ellers feiler kallet.
- Liste-endepunktene (payslip, salary/type, pensionScheme, holiday, standardTime) pagineres med from/count – sjekk fullResultSize og hent resten ved behov i stedet for å anta at alt kom med.
- /ledger/posting og /balanceSheet krever dateFrom og dateTo (dateTo EKSKLUSIV). Lønnsposteringer kan filtreres med type=WAGE på /ledger/posting.
- Lønnsavstemming i modulen (testet 2026-09-23): /salary/*/reconciliation/{id}/* = 200 når kunden også er delegert klient for tokenet, 403 ellers, og 500 med en BALANCE-id. taxAuthoritiesSum/aggregatedTaxAuthoritiesSum er null til A07 er hentet fra Skatteetaten. A07 bestilles/leses via interne tskinternal-kall – se oppgaven «Bestille og lese A07». taxAuthoritiesSum i overview-kallene forble null selv etter henting i UI. GET /salary/transaction ga 403; GET /salary/payslip krever yearFrom/yearTo OG monthFrom/monthTo samlet (ellers 422). Context-POST (201) returnerer {year, term, reconciliationId}; oppretter avstemmingen som DRAFT i byråkontoen. Idempotent: ny POST for samme kunde/år/termin gir samme reconciliationId og lager ingen duplikat (testet 2026-09-23). A07 hentet i Tripletex-UI ble IKKE synlig i taxAuthoritiesSum via API, heller ikke etter ny context-POST – avstem mot A07-filen med skillen lonnsavstemming-a07.
- SALARY-avstemming (udokumentert, testet 2026-09-23): POST /salary/reconciliation/context {customerId, year, term} → reconciliationId. GET /salary/reconciliation/{id}/overview gir PLASSHOLDER-/testdata (Group 1…, accountId 1001…) – aldri bruk tallene. GET /salary/reconciliation/{id}/vacationPay gir ekte feriepengetall hittil i år (vacationPayBasis, vacationPayRateAmounts, prevYearOwedVacationPay, prevYearSettledVacationPay). Sjekk alltid om svar fra udokumenterte kall ser ekte ut før de rapporteres.
- Pensjon (OTP) til a-meldingen registreres under Lønn → Pensjon (legacy-side, JSON-RPC ObligatoryPensionForm) – ikke i API-et. Alle /tsk/salaryv2/*-kall og /execute/*-sider krever nettleserinnlogging (403/302 med API-token). Pensjonskostnaden kan være bokført som leverandørfaktura (f.eks. 5945 hos klient C) uten noen kobling til lønn – sammenlign derfor per termin mot pensionSum i AGA-avstemmingen og A07 (npm run pensjon). Testet 2026-09-23: «Registrer pensjon» i lønnsmodulen åpner /execute/reimbursementMenu#obligatoryPension (ingen React-side). Den lagrer via POST https://tripletex.no/JSON-RPC {method:"ObligatoryPensionForm.store"}. JSON-RPC krever cookie-innlogging: med API-token gir kall i klientkontekst NotLoggedInException (bare system.listMethods svarer). Registrering må derfor gjøres i innlogget nettleser (Claude i Chrome ved behov).

## Ansatte, arbeidsforhold, avdelinger, kontakter

### Hente liste over ansatte (aktive, per avdeling, prosjektledere)
- **Kall:** `GET /employee`, `GET /employee/{id}`
- **Nøkkelord:** ansattliste, liste ansatte, hvem er ansatt, ansatte, employee, søk ansatt, sok ansatt, finn ansatt, ansattnummer, aktive ansatte, inaktive ansatte, prosjektledere, ansatte i avdeling, antall ansatte, brukere med tilgang, personalliste, ansattoversikt, vår referanse
- GET /employee med filtre: firstName/lastName (inneholder), employeeNumber (lik), departmentId (liste), isInactive=false, hasSystemAccess=true (kun brukere med innlogging), onlyProjectManagers/assignableProjectManagers=true for prosjektledere, periodStart/periodEnd for ansatte i en periode. GDPR: bruk alltid minimale fields=, f.eks. fields=id,employeeNumber,displayName,department(name) – aldri fødselsnummer, kontonummer, adresse eller telefon med mindre oppgaven krever det; vis initialer/«ansatt 1» i svar. Bruk count/from for paginering. GET /employee/{id} for én ansatt (samme fields-regel). NB: isInactive på /employee ser kun på flagget, ikke på om arbeidsforholdet er aktivt. count er 1000 som standard – bruk from/count ved store lister. Employee har ikke noe skrivbart isInactive-felt: en ansatt blir inaktiv via sluttdato på arbeidsforholdet.

### Søke etter ansatte og eksterne kontakter samlet
- **Kall:** `GET /employee/searchForEmployeesAndContacts`
- **Nøkkelord:** søk person, sok person, ansatte og kontakter, finn bruker, ekstern bruker, kontaktperson ansatt, searchForEmployeesAndContacts, regnskapsfører bruker, lesetilgang
- GET /employee/searchForEmployeesAndContacts?firstName=&lastName=&email= (inneholder). Kontakter er med som standard (includeContacts=true); sett includeContacts=false for kun ansatte. hasSystemAccess=true for brukere med innlogging, excludeReadOnly=true for å utelate lesebrukere. isInactive her kombineres med ansettelsesperioden (i motsetning til GET /employee). GDPR: fields=id,displayName,isContact.

### ✏️ Opprette ny ansatt med arbeidsforhold (nyansatt/onboarding)
- **Kall:** `GET /department`, `GET /employee/employment/occupationCode`, `GET /division`, `POST /employee`, `POST /employee/employment`, `POST /employee/employment/details`
- **Nøkkelord:** ny ansatt, nyansatt, opprette ansatt, registrere ansatt, legge til ansatt, onboarding, ansette, create employee, ny medarbeider, ansettelse, a-melding ny ansatt, arbeidsforhold ny
- 1) GET /department?fields=id,name (avdeling kreves normalt ved opprettelse). 2) POST /employee med firstName, lastName, department{id}, userType (NO_ACCESS hvis ingen innlogging; STANDARD/EXTENDED krever e-post som må bekreftes), samt dateOfBirth/nationalIdentityNumber, adresse og bankAccountNumber når lønn skal kjøres. 3) POST /employee/employment med employee{id}, startDate, division{id} (virksomhet for a-melding, fra GET /division), evt. isMainEmployer/taxDeductionCode. 4) POST /employee/employment/details med employment{id}, date (=startdato), employmentType (ORDINARY), employmentForm (PERMANENT/TEMPORARY), remunerationType (MONTHLY_WAGE/HOURLY_WAGE), workingHoursScheme (NOT_SHIFT), occupationCode{id} (fra GET /employee/employment/occupationCode?nameNO=), percentageOfFullTimeEquivalent, annualSalary eller hourlyWage. Employee-body har også employments-feltet, så arbeidsforhold kan sendes nestet i samme POST. Fødselsdato (dateOfBirth) eller fødselsnummer må normalt være satt på den ansatte for at arbeidsforholdet skal kunne rapporteres i a-meldingen. Unngå NOT_CHOSEN på employmentType/employmentForm/remunerationType/workingHoursScheme – det gir avvik i a-meldingen. Skrivende – krever brukerens bekreftelse. GDPR: personopplysninger behandles kun lokalt, aldri i logger/svar.

### ✏️ Importere mange ansatte på en gang (masseimport / historisk import)
- **Kall:** `POST /employee/list`, `POST /ledger/voucher/historical/employee`, `GET /department`
- **Nøkkelord:** importere ansatte, masseimport, bulk, flere ansatte, overføre ansatte, konvertering, systembytte, historisk import, migrering, employee list, import fra annet system
- POST /employee/list med en liste Employee-objekter (uten id/version), hver med firstName, lastName, department{id}, userType. Ved konvertering fra annet lønnssystem der avdeling mangler: POST /ledger/voucher/historical/employee [BETA] (mindre streng validering, avdeling ikke påkrevd). Kontroller etterpå med GET /employee?fields=id,employeeNumber,displayName. Skrivende – bekreft først. GDPR: ikke lagre importfilen med personopplysninger i scratch/logg.

### Kontrollere at ansatte og arbeidsforhold er komplette før lønnskjøring/a-melding
- **Kall:** `GET /employee`, `GET /employee/employment`, `GET /employee/employment/details`, `GET /division`
- **Nøkkelord:** kontroll ansatte, ansattkontroll, a-melding avvik, avvik a-melding, mangler arbeidsforhold, mangler yrkeskode, mangler virksomhet, stillingsprosent mangler, klargjøre lønn, klargjore lonn, før lønnskjøring, for lonnskjoring, datakvalitet ansatte, aa-registeret, lønnskontroll
- 1) GET /employee?isInactive=false&fields=id,employeeNumber,dateOfBirth,employments(id) – sjekk kun om felt er satt, skriv aldri ut verdier (GDPR). 2) For hver ansatt: GET /employee/employment?employeeId=<id>&fields=id,startDate,endDate,division(id,name),taxDeductionCode,isMainEmployer – flagg arbeidsforhold uten division. 3) GET /employee/employment/details?employmentId=<liste>&fields=employment(id),date,employmentType,employmentForm,remunerationType,workingHoursScheme,occupationCode(code),percentageOfFullTimeEquivalent – flagg manglende yrkeskode, NOT_CHOSEN-verdier eller 0 % stilling. 4) GET /division?fields=id,name,organizationNumber,municipality(name) for å se at virksomhetene har kommune. Rapporter kun aggregert/«ansatt 1, 2» med hva som mangler. Kun lesing.

### ✏️ Oppdatere ansattopplysninger (adresse, bankkonto, avdeling, kategori, brukertype)
- **Kall:** `GET /employee/{id}`, `PUT /employee/{id}`
- **Nøkkelord:** endre ansatt, oppdatere ansatt, ny adresse, nytt kontonummer, bytte avdeling, flytte avdeling, endre e-post, brukertype, gi innlogging, fjerne tilgang, no_access, ansattkategori, update employee, personalia
- Finn id via GET /employee (fields=id,version,displayName). PUT /employee/{id} med kun feltene som skal endres (partial object), f.eks. department{id}, employeeCategory{id}, address{addressLine1,postalCode,city}, bankAccountNumber/iban/bic, userType (STANDARD|EXTENDED|NO_ACCESS). Å sette userType=NO_ACCESS fjerner innlogging. Ta med version fra GET for å unngå versjonskonflikt (409). Det finnes ingen DELETE /employee og intet skrivbart isInactive – ansatte «avsluttes» via sluttdato på arbeidsforholdet. Skrivende – bekreft med brukeren. GDPR: ikke skriv ut nye/gamle verdier for kontonummer, adresse o.l. i svaret; bekreft bare at feltet er oppdatert.

### Hente arbeidsforhold og stillingsdetaljer for en ansatt
- **Kall:** `GET /employee/employment`, `GET /employee/employment/{id}`, `GET /employee/employment/details`, `GET /employee/employment/details/{id}`
- **Nøkkelord:** arbeidsforhold, se arbeidsforhold, stillingsprosent, ansettelsesdato, startdato, sluttdato, lønn ansatt, årslønn, yrkeskode, employment, a-melding kontroll, aa-register, avvik a-melding
- GET /employee/employment?employeeId=<id>&fields=id,startDate,endDate,employmentEndReason,division(name),taxDeductionCode,isMainEmployer. Deretter GET /employee/employment/details?employmentId=<id>&fields=date,employmentType,employmentForm,remunerationType,percentageOfFullTimeEquivalent,occupationCode(code,nameNO). Detaljene er datostyrte (historikk) – nyeste date gjelder. latestSalary på employment gir siste detaljer. GDPR: hent annualSalary/hourlyWage kun når oppgaven krever lønnstall, og vis ikke lønn per navngitt person.

### ✏️ Registrere nytt arbeidsforhold for eksisterende ansatt
- **Kall:** `GET /employee`, `GET /division`, `POST /employee/employment`, `POST /employee/employment/details`
- **Nøkkelord:** nytt arbeidsforhold, opprette arbeidsforhold, ekstra stilling, biarbeidsgiver, hovedarbeidsgiver, gjenansettelse, ansette på nytt, create employment, a-melding arbeidsforhold, skattetrekk kode, trekkode
- Finn employee id (GET /employee, minimale fields). POST /employee/employment med employee{id}, startDate (yyyy-MM-dd), division{id}, evt. employmentId (arbeidsforholds-ID fra tidligere system), isMainEmployer (default true) og taxDeductionCode (default loennFraHovedarbeidsgiver/loennFraBiarbeidsgiver etter isMainEmployer; EMPTY er ulovlig). Følg opp med POST /employee/employment/details (date, employmentType, employmentForm, remunerationType, workingHoursScheme, occupationCode, percentageOfFullTimeEquivalent, annualSalary/hourlyWage). Skrivende – bekreft først.

### ✏️ Avslutte arbeidsforhold når en ansatt slutter
- **Kall:** `GET /employee/employment`, `GET /employee/employment/employmentType/employmentEndReasonType`, `PUT /employee/employment/{id}`, `PUT /employee/{id}`
- **Nøkkelord:** slutte, sluttet, oppsigelse, avslutte arbeidsforhold, sluttdato, sluttårsak, sluttarsak, fratredelse, avgang, permisjon slutt, end employment, a-melding sluttdato, fjerne tilgang ved slutt
- GET /employee/employment?employeeId=&fields=id,version,startDate,endDate. PUT /employee/employment/{id} med endDate og employmentEndReason (EMPLOYMENT_END_EMPLOYEE = arbeidstaker sa opp, EMPLOYMENT_END_EMPLOYER = arbeidsgiver sa opp, EMPLOYMENT_END_EXPIRED = midlertidig utløpt, EMPLOYMENT_END_WRONGLY_REPORTED, EMPLOYMENT_END_SYSTEM_OR_ACCOUNTANT_CHANGE, EMPLOYMENT_END_INTERNAL_CHANGE). Sett isRemoveAccessAtEmploymentEnded=true for automatisk å fjerne innlogging (gjelder alle arbeidsforhold på den ansatte), eller PUT /employee/{id} med userType=NO_ACCESS. Ansatte kan ikke slettes via API (ingen DELETE /employee); de blir inaktive når arbeidsforholdet er avsluttet. Husk at sluttdato skal med i a-meldingen for måneden. Skrivende – bekreft først.

### ✏️ Registrere lønnsendring, ny stillingsprosent eller AGA-kommune på arbeidsforholdet
- **Kall:** `GET /employee/employment/details`, `POST /employee/employment/details`, `PUT /employee/employment/details/{id}`, `GET /municipality`
- **Nøkkelord:** lønnsendring, lonnsendring, lønnsjustering, lønnsøkning, ny lønn, årslønn, timelønn, stillingsprosent, redusert stilling, deltid, endre yrkeskode, arbeidsgiveravgift kommune, aga-sone, skattekommune, employment details, lønnsoppgjør
- Detaljer er datostyrte: for en endring fra en ny dato, POST /employee/employment/details med employment{id}, date (gjelder fra), og nye verdier (annualSalary eller hourlyWage, percentageOfFullTimeEquivalent, occupationCode{id} osv.) – da bevares historikken. Rett en feilregistrering med PUT /employee/employment/details/{id} (id+version fra GET ...?employmentId=). monthlySalary er skrivebeskyttet og beregnes av årslønn. payrollTaxMunicipalityId{id} settes fra GET /municipality?includePayrollTaxZones=true. workingHoursScheme med skift krever shiftDurationHours. Skrivende – bekreft. GDPR: ikke vis lønn per navngitt ansatt i svar.

### Finne riktig yrkeskode (STYRK) til arbeidsforhold
- **Kall:** `GET /employee/employment/occupationCode`, `GET /employee/employment/occupationCode/{id}`
- **Nøkkelord:** yrkeskode, styrk, styrk-08, stillingskode, finne yrkeskode, occupation code, yrke, stillingsbetegnelse, a-melding yrkeskode, feil yrkeskode
- GET /employee/employment/occupationCode?nameNO=<del av yrkesnavn>&fields=id,code,nameNO, eller code=<sifre> for å søke på kode. Bruk id i occupationCode{id} på employment details. GET /employee/employment/occupationCode/{id} for å slå opp en kjent id. Ingen personopplysninger.

### Slå opp kodeverk for arbeidsforhold (type, form, sluttårsak, avlønning, arbeidstid, maritimt)
- **Kall:** `GET /employee/employment/employmentType`, `GET /employee/employment/employmentType/employmentFormType`, `GET /employee/employment/employmentType/employmentEndReasonType`, `GET /employee/employment/employmentType/salaryType`, `GET /employee/employment/employmentType/scheduleType`, `GET /employee/employment/employmentType/maritimeEmploymentType`, `GET /employee/employment/remunerationType`, `GET /employee/employment/workingHoursScheme`
- **Nøkkelord:** kodeverk, kodeliste, arbeidsforholdstype, ansettelsesform, sluttårsak, avlønningstype, arbeidstidsordning, maritimt, skipsregister, fartsområde, skipstype, lønnstype, a-melding koder, employment type
- Listene returnerer kode, nameNO og enum-verdi. I request-body brukes enum-strengene direkte: employmentType ORDINARY|MARITIME|FREELANCE, employmentForm PERMANENT|TEMPORARY|PERMANENT_AND_HIRED_OUT|TEMPORARY_AND_HIRED_OUT|TEMPORARY_ON_CALL, remunerationType MONTHLY_WAGE|HOURLY_WAGE|COMMISION_PERCENTAGE|FEE|PIECEWORK_WAGE, workingHoursScheme NOT_SHIFT|ROUND_THE_CLOCK|SHIFT_365|OFFSHORE_336|CONTINUOUS|OTHER_SHIFT. maritimeEmploymentType krever type=SHIP_REGISTER|SHIP_TYPE|TRADE_AREA. Rene oppslag, ingen persondata.

### ✏️ Registrere permisjon eller permittering på en ansatt
- **Kall:** `GET /employee/employment`, `GET /employee/employment/leaveOfAbsenceType`, `POST /employee/employment/leaveOfAbsence`, `POST /employee/employment/leaveOfAbsence/list`
- **Nøkkelord:** permisjon, permittering, permittere, foreldrepermisjon, fødselspermisjon, pappaperm, mammaperm, utdanningspermisjon, velferdspermisjon, militærtjeneste, ulønnet permisjon, lønnstrekk, a-melding permisjon, leave of absence, furlough, delvis permittert
- Finn employment id (GET /employee/employment?employeeId=&fields=id,startDate). POST /employee/employment/leaveOfAbsence med employment{id}, startDate, endDate, percentage (0-100), isWageDeduction (trekk i lønn), type: LEAVE_OF_ABSENCE, FURLOUGH (permittering), PARENTAL_BENEFITS, MILITARY_SERVICE, EDUCATIONAL, COMPASSIONATE (velferd), OTHER_STATUTORILY_REQUIRED/OTHER_NOT_STATUTORILY_REQUIRED, EDUCATIONAL_STATUTORILY_REQUIRED/EDUCATIONAL_NOT_STATUTORILY_REQUIRED. Flere på en gang: POST .../leaveOfAbsence/list. Kodeliste: GET /employee/employment/leaveOfAbsenceType. Skrivende – bekreft. GDPR: permisjon/fravær er sensitiv – aldri navngi den ansatte i svar/rapport.

### ✏️ Hente, endre eller avslutte permisjoner og permitteringer
- **Kall:** `GET /employee/employment/leaveOfAbsence`, `GET /employee/employment/leaveOfAbsence/{id}`, `PUT /employee/employment/leaveOfAbsence/{id}`
- **Nøkkelord:** hvem har permisjon, permitterte, liste permisjoner, endre permisjon, forlenge permisjon, avslutte permisjon, tilbake fra permisjon, permisjonsprosent, a-melding kontroll permisjon
- GET /employee/employment/leaveOfAbsence?employmentIds=<liste>&date=yyyy-MM-dd (date er standard i dag – sett den for å se andre perioder) og evt. minPercentage/maxPercentage (0-100); fields=id,version,startDate,endDate,percentage,type. Endre/forlenge/avslutte med PUT /employee/employment/leaveOfAbsence/{id} (ny endDate eller percentage). Lesing er ikke skrivende; PUT krever bekreftelse. GDPR: rapporter kun aggregert (antall permitterte), aldri navn.

### ✏️ Registrere eller endre timekost og timesats per ansatt
- **Kall:** `GET /employee/hourlyCostAndRate`, `GET /employee/hourlyCostAndRate/{id}`, `POST /employee/hourlyCostAndRate`, `PUT /employee/hourlyCostAndRate/{id}`
- **Nøkkelord:** timekost, timesats, timepris, kostpris ansatt, internpris, budsjettsats, hourly rate, hourly cost, prosjektkost, etterkalkyle, manglende timesats, fakturerbar sats
- GET /employee/hourlyCostAndRate?employeeId=<id> (NB: uten employeeId returneres token-eierens satser)&fields=id,version,date,rate,budgetRate,hourCostRate. Ny sats fra en dato: POST /employee/hourlyCostAndRate med employee{id}, date, rate (timesats/salgspris), hourCostRate (timekost), budgetRate. Rette eksisterende: PUT /employee/hourlyCostAndRate/{id}. Satsene er datostyrte – ikke overskriv historikk ved prisendring. Prosjekter som mangler sats: GET /project/{id}/actionList/employeesWithMissingHourlyRate (prosjekt-gruppen). Skrivende – bekreft. Ingen DELETE – feilregistreringer rettes med PUT.

### ✏️ Sette eller hente normalarbeidstid per ansatt
- **Kall:** `GET /employee/standardTime`, `GET /employee/standardTime/byDate`, `GET /employee/standardTime/{id}`, `POST /employee/standardTime`, `PUT /employee/standardTime/{id}`, `GET /salary/settings/standardTime`
- **Nøkkelord:** normaltid, normalarbeidstid, timer per dag, arbeidstid ansatt, deltid, heltid, fleksitid, overtid, standard time, 37,5 timer, 7,5 timer, timebank
- GET /employee/standardTime/byDate?employeeId=&date= gir gjeldende normaltid (employeeId standard = token-eier, date standard = i dag). Historikk: GET /employee/standardTime?employeeId=<id> (employeeId er også her token-eier som standard – send alltid eksplisitt). Ny normaltid fra dato: POST /employee/standardTime med employee{id}, fromDate, hoursPerDay (f.eks. 7.5). Rette: PUT /employee/standardTime/{id}. Firmaets standard ligger i GET /salary/settings/standardTime (lønn-gruppen) og gjelder når ansatt ikke har egen. Skrivende for POST/PUT – bekreft. Ingen DELETE – rett med PUT.

### ✏️ Registrere eller oppdatere pårørende for en ansatt
- **Kall:** `GET /employee/nextOfKin`, `GET /employee/nextOfKin/{id}`, `POST /employee/nextOfKin`, `PUT /employee/nextOfKin/{id}`
- **Nøkkelord:** pårørende, parorende, nærmeste pårørende, next of kin, nødkontakt, ektefelle, samboer, kontakt ved ulykke, hms
- GET /employee/nextOfKin?employeeId=<id> (send alltid – standard er token-eier)&fields=id,version,typeOfRelationship (hent navn/telefon kun når det faktisk trengs). POST /employee/nextOfKin med employee{id}, name, phoneNumber, address, typeOfRelationship (SPOUSE|PARTNER|PARENT|CHILD|SIBLING). Endre: PUT /employee/nextOfKin/{id}. GDPR: pårørende er tredjeperson – aldri vis navn/telefon i svar, rapporter eller filer. Skrivende – bekreft.

### ✏️ Opprette, endre og slette ansattkategorier
- **Kall:** `GET /employee/category`, `GET /employee/category/{id}`, `POST /employee/category`, `POST /employee/category/list`, `PUT /employee/category/{id}`, `PUT /employee/category/list`, `DELETE /employee/category/{id}`, `DELETE /employee/category/list`
- **Nøkkelord:** ansattkategori, kategori, gruppere ansatte, employee category, lærling, timelønnede, funksjonærer, slette kategori, ny kategori
- GET /employee/category?query=|name=|number=&fields=id,number,name. Opprette: POST /employee/category (name, number, description) eller POST .../list for flere. Endre: PUT /employee/category/{id} (partial) eller PUT .../list (id+version påkrevd). Slette: DELETE /employee/category/{id} eller DELETE /employee/category/list?ids=1,2. Koble ansatt til kategori via PUT /employee/{id} med employeeCategory{id}. Skrivende – bekreft, særlig sletting.

### Tilgangsgjennomgang: hvilke brukere har innlogging og hvilke rettigheter
- **Kall:** `GET /employee`, `GET /employee/entitlement`, `GET /token/session/>whoAmI`
- **Nøkkelord:** tilgangsgjennomgang, tilgangskontroll, hvem har tilgang, brukere med innlogging, brukeroversikt, rettighetsoversikt, internkontroll tilgang, revisjon tilganger, hvem er jeg, token-eier, whoami
- 1) GET /token/session/>whoAmI?fields=employeeId,company(id,name) for å se hvilken bruker/klient tokenet representerer (sitér stien pga. '>'). 2) GET /employee?hasSystemAccess=true&fields=id,employeeNumber,userType,isProxy – isProxy=true er regnskapsfører-/revisorbyrå. 3) Per bruker: GET /employee/entitlement?employeeId=<id>&fields=entitlementId,name (employeeId må sendes, ellers får du token-eierens). Oppsummer antall brukere per userType og antall rettigheter – ikke navn/e-post. Kun lesing.

### ✏️ Gi eller endre tilganger/rettigheter for en bruker i egen konto
- **Kall:** `GET /employee/entitlement`, `GET /employee/entitlement/{id}`, `PUT /employee/entitlement/:grantEntitlementsByTemplate`, `PUT /employee/{id}`
- **Nøkkelord:** tilgang, rettigheter, gi tilgang, fjerne tilgang, brukerrettigheter, rolle, tilgangsmal, entitlement, full tilgang, regnskapsfører tilgang, revisor tilgang, personalansvarlig, fakturaansvarlig, avdelingsleder, 403, mangler tilgang, tildele rettigheter, rettighetsmal
- Se dagens rettigheter: GET /employee/entitlement?employeeId=<id> (uten employeeId får du token-eierens egne rettigheter)&fields=id,name,entitlementId. Tildel via mal: PUT /employee/entitlement/:grantEntitlementsByTemplate?employeeId=&template= (NONE_PRIVILEGES|ALL_PRIVILEGES|INVOICING_MANAGER|PERSONELL_MANAGER|ACCOUNTANT|AUDITOR|DEPARTMENT_LEADER) – ingen body, query-parametere. [BETA]. Brukeren får bare rettigheter som brukertypen tillater; sett først userType=EXTENDED via PUT /employee/{id} ved behov for full tilgang. NONE_PRIVILEGES fjerner rettigheter. Skrivende og sikkerhetskritisk – bekreft alltid.

### ✏️ Gi regnskapsfører/revisor tilgang til en klientkonto (byrå)
- **Kall:** `GET /company/>withLoginAccess`, `GET /employee/entitlement/client`, `PUT /employee/entitlement/:grantClientEntitlementsByTemplate`
- **Nøkkelord:** klienttilgang, klientkonto, tilgang klient, byrå, regnskapsbyrå, regnskapsfører, revisor, fullmakt, proxy login, standard rettigheter regnskapsfører, agro, klientrettigheter, hvilke klienter
- Kjøres fra byråets konto. Finn klientene brukeren har innlogging til: GET /company/>withLoginAccess (fields=id,name). Se rettigheter i klient: GET /employee/entitlement/client?employeeId=&customerId=<klient-id> [BETA]. Tildel: PUT /employee/entitlement/:grantClientEntitlementsByTemplate?employeeId=&customerId=&template=STANDARD_PRIVILEGES_ACCOUNTANT|STANDARD_PRIVILEGES_AUDITOR|ALL_PRIVILEGES|NONE_PRIVILEGES|AGRO_* &addToExisting=true (legg til i stedet for å erstatte). Alle tre query-parametere er påkrevd. Skrivende og sikkerhetskritisk – bekreft klient og mal eksplisitt.

### ✏️ Endre brukerinnstillinger og språk
- **Kall:** `GET /employee/preferences/>loggedInEmployeePreferences`, `GET /employee/preferences`, `PUT /employee/preferences/{id}`, `PUT /employee/preferences/list`, `PUT /employee/preferences/:changeLanguage`
- **Nøkkelord:** språk, sprak, engelsk, norsk, bytte språk, brukerinnstillinger, preferanser, prosjektfilter, standard lager, ordrelinjeforslag, change language, min profil
- Egen bruker: GET /employee/preferences/>loggedInEmployeePreferences (sitér stien i shell pga. '>'). Andre: GET /employee/preferences?employeeId=. Språk for innlogget bruker: PUT /employee/preferences/:changeLanguage?language=NO|EN (ingen body). Andre felt (filterOnProjectParticipant, filterOnProjectManager, orderLineSuggestions ON|OFF|UNANSWERED, defaultWarehouseId): PUT /employee/preferences/{id} eller PUT .../list (id+version). Skrivende – bekreft.

### Hente avdelinger (avdelingsliste)
- **Kall:** `GET /department`, `GET /department/query`, `GET /department/{id}`
- **Nøkkelord:** avdelinger, avdelingsliste, avdelingsnummer, finn avdeling, søk avdeling, department, kostnadssted, avdelingsleder, inaktive avdelinger
- GET /department?name=&departmentNumber=&departmentManagerId=&isInactive=false&fields=id,departmentNumber,name,isInactive. Fritekst/wildcard: GET /department/query?query=<tekst> (isInactive: true=bare inaktive, false=bare aktive, utelatt=begge). GET /department/{id} for én. Avdeling-id brukes som departmentId i hovedbok, saldobalanse, prosjekt, produkt og reiseregning. Unngå departmentManager(*) med persondata – bruk departmentManager(id,displayName) om nødvendig. Avdelingsregnskap forutsetter at avdelingsmodulen (moduledepartment/moduleDepartmentAccounting) er aktivert i selskapet.

### ✏️ Opprette eller endre avdelinger
- **Kall:** `POST /department`, `POST /department/list`, `PUT /department/{id}`, `PUT /department/list`, `GET /employee`
- **Nøkkelord:** ny avdeling, opprette avdeling, endre avdeling, gi nytt navn avdeling, avdelingsleder, avdelingsnummer, flere avdelinger, department create, avdelingsstruktur, kostnadssted
- POST /department med name, departmentNumber og evt. departmentManager{id} (ansatt-id fra GET /employee?fields=id,displayName). Flere: POST /department/list. Endre navn/nummer/leder: PUT /department/{id} (partial) eller PUT /department/list (id+version påkrevd). Avdelingsmodulen må være aktiv i selskapet for at avdeling skal brukes i regnskapet. Skrivende – bekreft.

### ✏️ Slette eller deaktivere en avdeling
- **Kall:** `GET /department/{id}`, `DELETE /department/{id}`, `PUT /department/{id}`
- **Nøkkelord:** slette avdeling, deaktivere avdeling, inaktiv avdeling, legge ned avdeling, arkivere avdeling, delete department
- Avdelinger som er brukt i posteringer, på ansatte eller prosjekter kan normalt ikke slettes – da PUT /department/{id} med isInactive=true. DELETE /department/{id} kun for ubrukte avdelinger (feil gir 4xx/validering). Hent version via GET /department/{id}?fields=id,version,name. Skrivende og irreversibelt ved sletting – bekreft.

### Hente resultat, saldobalanse og budsjett per avdeling (avdelingsregnskap)
- **Kall:** `GET /department`, `GET /balanceSheet`, `GET /ledger/posting`, `GET /resultbudget/department/{id}`
- **Nøkkelord:** avdelingsregnskap, resultat per avdeling, avdelingsresultat, saldobalanse avdeling, posteringer avdeling, kostnader per avdeling, budsjett avdeling, resultatbudsjett, dimensjon, segment, avdelingsrapport
- 1) GET /department?fields=id,departmentNumber,name. 2) Saldobalanse per avdeling: GET /balanceSheet?dateFrom=&dateTo=(ekskl.)&departmentId= eller departmentIds=1,2 (evt. accountNumberFrom=3000&accountNumberTo=8999 for resultat). 3) Posteringer: GET /ledger/posting?dateFrom=&dateTo=&departmentId=&fields=date,account(number),amount,description,voucher(number). 4) Budsjett: GET /resultbudget/department/{id}?year=. dateTo er eksklusiv i begge rapportene. Kun lesing.

### ✏️ Registrere og vedlikeholde virksomheter/underenheter og koble arbeidsforhold
- **Kall:** `GET /division`, `POST /division`, `POST /division/list`, `PUT /division/{id}`, `PUT /division/list`, `GET /municipality`, `PUT /employee/employment/{id}`
- **Nøkkelord:** virksomhet, underenhet, bedriftsnummer, ny virksomhet, division, a-melding virksomhet, arbeidsforhold mangler virksomhet, aga-sone, kommune, organisasjonsnummer underenhet, flytte ansatte virksomhet
- GET /division?query=&fields=id,name,organizationNumber,startDate,endDate,municipality(name). Opprette: POST /division med name, organizationNumber (underenhetens 9-sifrede nr.), startDate, municipality{id} og municipalityDate (kommune fra GET /municipality, avgjør AGA-sone). Endre: PUT /division/{id} eller PUT /division/list. Koble ansattes arbeidsforhold: PUT /employee/employment/{id} med division{id}. Det finnes ingen DELETE – avslutt med endDate. GET /company/divisions er utgått (deprecated). Skrivende – bekreft.

### Hente kontaktpersoner hos en kunde
- **Kall:** `GET /customer`, `GET /contact`, `GET /contact/{id}`
- **Nøkkelord:** kontaktperson, kontaktpersoner, kundekontakt, hvem er kontakt, fakturakontakt, deres referanse, contact, kontakter kunde, e-post kunde
- Finn kunde-id: GET /customer?customerName=<navn> (eller organizationNumber=<orgnr>)&fields=id,name,organizationNumber. GET /contact?customerId=<id>&fields=id,firstName,lastName,isInactive (legg til email/phone bare hvis oppgaven krever det). Kan også filtreres på firstName/lastName/email/departmentId. GDPR: kontaktpersoner er personer – vis initialer eller rolle i svar, ikke full e-post/telefon.

### ✏️ Opprette, endre eller slette kontaktpersoner
- **Kall:** `POST /contact`, `POST /contact/list`, `PUT /contact/{id}`, `DELETE /contact/list`
- **Nøkkelord:** ny kontaktperson, opprette kontakt, legge til kontakt, endre kontakt, slette kontakt, deaktivere kontakt, oppdatere e-post kontakt, contact create, importere kontakter
- POST /contact med firstName, lastName, email, phoneNumberMobile, customer{id} (og evt. department{id}). Flere: POST /contact/list. Endre: PUT /contact/{id} (partial), sett isInactive=true for å deaktivere i stedet for å slette. Slette: DELETE /contact/list?ids=1,2 [BETA]. Skrivende – bekreft, og sletting er irreversibel. GDPR: ikke logg kontaktdata.

### Se ansattreskontro og åpne poster på en ansatt (utlegg, forskudd, lån)
- **Kall:** `GET /employee`, `GET /ledger/posting/openPost`, `GET /ledger/posting`, `GET /balanceSheet`
- **Nøkkelord:** ansattreskontro, reskontro ansatt, åpne poster ansatt, apne poster, utlegg, skyldig ansatt, forskudd, lån til ansatt, lan til ansatt, mellomværende ansatt, 2910, 1570, tilgode ansatt, employee ledger
- Finn employee id (GET /employee?fields=id,employeeNumber). Åpne poster per dato: GET /ledger/posting/openPost?date=yyyy-MM-dd (til og ekskl.)&employeeId=&fields=date,account(number),amount,description,voucher(number) (evt. accountNumberFrom/To). Bevegelser: GET /ledger/posting?dateFrom=&dateTo=&employeeId=. Saldo: GET /balanceSheet?dateFrom=&dateTo=&employeeId=. Kun lesing. GDPR: i rapport, bruk ansattnummer/«ansatt 1», ikke navn.

### ✏️ Registrere opptjente feriepenger fra tidligere system ved oppstart
- **Kall:** `GET /employee/{id}`, `PUT /employee/{id}`
- **Nøkkelord:** opptjente feriepenger, feriepenger, feriepengegrunnlag, overføre feriepenger, systembytte, konvertering lønn, ekstra ferieuke, holiday allowance, feriepenger i fjor, inngående feriepenger
- Les nåværende: GET /employee/{id}?fields=id,version,holidayAllowanceEarned(*). Oppdater med PUT /employee/{id} og holidayAllowanceEarned{year (opptjeningsår), amount (opptjente feriepenger), basis (grunnlag), amountExtraHolidayWeek (5. ferieuke/60+)}. Kan også sendes ved POST /employee eller /ledger/voucher/historical/employee ved import. Feriepengesatser settes i lønnsinnstillinger (lønn-gruppen). Skrivende – bekreft. GDPR: beløp per ansatt vises ikke navngitt.

### ✏️ Laste opp eller hente dokumenter i ansattarkivet (arbeidskontrakt, attester)
- **Kall:** `GET /documentArchive/employee/{id}`, `POST /documentArchive/employee/{id}`
- **Nøkkelord:** ansattarkiv, personalmappe, arbeidskontrakt, ansettelseskontrakt, last opp kontrakt, dokument ansatt, attest, document archive, vedlegg ansatt
- Hent liste: GET /documentArchive/employee/{employeeId}?periodDateFrom=&periodDateTo=&fields=id,fileName,archiveDate [BETA]. Last opp: POST /documentArchive/employee/{employeeId} som multipart/form-data med feltet file [BETA]. Skrivende ved opplasting – bekreft. GDPR: dokumentene er personopplysninger; ikke les innhold eller lagre filer lokalt uten behov.

**Fallgruver:**
- GDPR: alle /employee*- og /contact-endepunkter er merket PERSONDATA. Bruk alltid minimale fields= (f.eks. id,employeeNumber,displayName), aldri fields=* på ansatte. Aldri vis fødsels-/D-nummer, kontonummer, adresse, telefon, e-post, lønn per person, permisjon/fravær eller pårørende i svar – bruk aggregater, initialer eller «ansatt 1». CLI-et maskerer via src/privacy.js; bruk redact() i egne skript.
- POST /employee krever normalt department{id}; historisk import uten avdeling må gå via POST /ledger/voucher/historical/employee [BETA]. userType STANDARD/EXTENDED krever e-post som brukeren må bekrefte; bruk NO_ACCESS for ansatte uten innlogging.
- Arbeidsforhold (employment) og detaljer (employment/details) er to nivåer: startDate/endDate/sluttårsak/virksomhet ligger på employment, mens stillingsprosent, lønn, yrkeskode og arbeidstidsordning ligger på datostyrte details. Lønnsendring = ny details-rad med ny date, ikke overskriving (bevarer historikk for a-meldingen).
- taxDeductionCode styres av isMainEmployer (true → loennFraHovedarbeidsgiver, false → loennFraBiarbeidsgiver). Verdien EMPTY kan ikke settes. isRemoveAccessAtEmploymentEnded ligger egentlig på Employee og påvirker alle arbeidsforholdene.
- Arbeidsforhold uten division (virksomhet/underenhet) eller uten yrkeskode gir avvik i a-meldingen. Divisions har verken GET /{id} eller DELETE – søk med GET /division?query= og avslutt med endDate. GET /company/divisions er deprecated.
- Kodeverk-endepunktene (employmentType, remunerationType, workingHoursScheme, leaveOfAbsenceType) returnerer id/code/nameNO, men request-body bruker enum-strenger (f.eks. ORDINARY, PERMANENT, MONTHLY_WAGE, NOT_SHIFT, FURLOUGH). GET .../maritimeEmploymentType krever type=SHIP_REGISTER|SHIP_TYPE|TRADE_AREA. Skiftordning krever shiftDurationHours.
- GET /employee/employment/leaveOfAbsence har date som standard i dag – uten date ser du bare permisjoner som er aktive i dag. percentage/minPercentage/maxPercentage må være 0-100.
- isInactive har ulik betydning: på GET /employee matcher den kun flagget, mens på /employee/searchForEmployeesAndContacts kombineres den med ansettelsesperioden. searchForEmployeesAndContacts tar med eksterne kontakter som standard (includeContacts=true).
- Action-endepunkter med kolon (PUT /employee/entitlement/:grantEntitlementsByTemplate, :grantClientEntitlementsByTemplate, PUT /employee/preferences/:changeLanguage) tar query-parametere og ingen body. Entitlement-malene er [BETA], og brukeren får bare rettigheter som userType tillater (STANDARD gir begrenset). :changeLanguage gjelder kun innlogget bruker (token-eier).
- Stier med '>' (GET /employee/preferences/>loggedInEmployeePreferences, GET /company/>withLoginAccess) må siteres i shell, ellers tolkes '>' som omdirigering og det lages en fil.
- PUT /{id} tar et partial object; PUT /list (department, division, employee/category, employee/preferences) krever id og version på hvert objekt. POST skal ikke ha id/version. Ved 409/versjonskonflikt: hent version på nytt.
- DELETE /department/{id} feiler for avdelinger i bruk – sett isInactive=true i stedet. DELETE /contact/list er [BETA]; foretrekk isInactive=true på kontakten. Sletting er irreversibel og krever alltid bekreftelse.
- Timekost/timesats (hourlyCostAndRate) og normaltid (standardTime) er datostyrte – registrer ny rad med date/fromDate ved endring. Ansattens standardTime overstyrer firmaets /salary/settings/standardTime.
- 403 betyr normalt at token-brukeren mangler rettighet (f.eks. personal-/lønnstilgang eller klienttilgang) eller at modulen (avdeling, lønn, prosjekt) ikke er aktiv – ikke at data mangler. Klienttilgang-endepunktene må kjøres fra byråkontoen med customerId = klientens id.
- Flere GET-endepunkter har employeeId som standard lik token-eieren (hourlyCostAndRate, standardTime, standardTime/byDate, nextOfKin, entitlement, entitlement/client). Glemmer du employeeId får du stille og rolig token-brukerens egne data – send alltid employeeId eksplisitt.
- Det finnes ingen DELETE for employee, employment, employment/details, leaveOfAbsence, hourlyCostAndRate, standardTime, nextOfKin eller division. Feil rettes med PUT (id+version), og arbeidsforhold/virksomheter avsluttes med endDate. Employee har heller ikke noe skrivbart isInactive-felt.
- count er 1000 som standard på listeendepunktene; bruk from/count for paginering og sjekk fullResultSize i svaret.
- Enum-verdien NOT_CHOSEN (employmentType, employmentForm, remunerationType, workingHoursScheme) finnes i API-et, men gir avvik i a-meldingen – sett alltid reelle verdier.
- Enkelte områder forutsetter at modul er aktivert i selskapet (f.eks. moduledepartment/moduleDepartmentAccounting for avdeling, moduleEmployeeCategory for ansattkategori, moduleDivisions for virksomheter, moduleHourCost for timekost). Valideringsfeil/403 kan skyldes manglende modul.
- Alle skrivende kall (opprette/endre ansatt, arbeidsforhold, permisjon, tilganger, avdeling, kontakt) krever eksplisitt bekreftelse fra brukeren og at klienten er navngitt.

## Hovedbok, bilag, posteringer, kontoplan, perioder, budsjett, avstemming

### Hente saldobalanse for en periode
- **Kall:** `GET /balanceSheet`
- **Nøkkelord:** saldobalanse, råbalanse, rabalanse, trial balance, saldo, ib, ub, bevegelse, periodetall, hittil i år, balanse, resultat, kontosaldo, saldoliste, resultatrapport, balanserapport, p&l
- GET /balanceSheet med dateFrom (inkl.) og dateTo (EKSKL.) – f.eks. hele 2025: dateFrom=2025-01-01&dateTo=2026-01-01. Avgrens med accountNumberFrom/accountNumberTo (inkl., kontonummer – ikke id), f.eks. 1000–2999 for balanse og 3000–8999 for resultat. Bruk fields=account(number,name),balanceIn,balanceChange,balanceOut. includeActiveAccountsWithoutMovements=true tar med kontoer uten bevegelse. Bla med from/count ved mange kontoer. Standard count er 1000 rader – bla med from ved større kontoplaner. /balanceSheet har ikke supplierId-filter (bruk GET /ledger?supplierId=... for leverandør).

### Lage resultat/saldobalanse per avdeling, prosjekt eller fri dimensjon
- **Kall:** `GET /balanceSheet`, `GET /department`, `GET /project`, `GET /ledger/accountingDimensionValue/search`, `GET /ledger/posting`
- **Nøkkelord:** resultat per avdeling, avdelingsregnskap, prosjektregnskap, resultat per prosjekt, dimensjonsrapport, kostnadssted, segmentrapport, department, project, fri dimensjon
- 1) Finn id: GET /department?fields=id,name,departmentNumber, GET /project?fields=id,number,name eller GET /ledger/accountingDimensionValue/search?dimensionIndex=1. 2) GET /balanceSheet med dateFrom/dateTo (dateTo ekskl.) og departmentId/departmentIds, projectId/projectIds (+ includeSubProjects=true) eller freeDimension1/2/3 (kommaseparerte id-er), accountNumberFrom=3000&accountNumberTo=8999 for resultat. 3) For transaksjonsnivå: GET /ledger/posting med samme filtre (departmentId, projectId, accountingDimensionValue1Id osv.).

### Hente hovedbok/kontospesifikasjon for en konto i en periode
- **Kall:** `GET /ledger/account`, `GET /ledger`
- **Nøkkelord:** hovedbok, kontoutskrift, kontospesifikasjon, general ledger, kontoutdrag, posteringer på konto, saldo konto, ib ub konto, kontokort, hovedboksutskrift
- 1) Slå opp konto-id: GET /ledger/account?number=1920&fields=id,number,name. 2) GET /ledger?dateFrom=...&dateTo=...(ekskl.)&accountId=<id> gir per konto openingBalance, sumAmount, closingBalance og lenker til postings. Bruk fields=account(number,name),openingBalance,sumAmount,closingBalance,postings(date,description,amount,voucher(number,year)). Kan også filtreres på customerId/supplierId/projectId/departmentId/dimensjon. openPostings-parameteren er utgått – bruk /ledger/posting/openPost for åpne poster. Standard count=1000 kontoer; postings-listen kan bli stor – begrens med fields og kortere periode.

### Søke opp posteringer på konto, kunde, leverandør, prosjekt eller avdeling
- **Kall:** `GET /ledger/posting`, `GET /ledger/posting/{id}`, `GET /customer`, `GET /supplier`, `GET /ledger/account`
- **Nøkkelord:** posteringer, transaksjoner, føringer, foringer, søk postering, finn transaksjon, hvilke bilag, leverandørposteringer, kundeposteringer, posting search, debet, kredit, kid, fakturanummer, mva-kode
- GET /ledger/posting krever dateFrom og dateTo (ekskl.). Filtrer med accountId (intern id) eller accountNumberFrom/accountNumberTo (kontonummer), customerId, supplierId, projectId, departmentId, productId, accountingDimensionValue1-3Id, og type (INCOMING_PAYMENT, OUTGOING_INVOICE_CUSTOMER_POSTING, INVOICE_EXPENSE, WAGE m.fl.). Slå opp kunde/leverandør-id via GET /customer?name=... / GET /supplier?name=... (fields=id,name). Minimal fields: id,date,description,amount,amountCurrency,account(number),voucher(id,number,year),customer(name),supplier(name),vatType(number). Unngå employee-felt (GDPR). Bla med from/count; GET /ledger/posting/{id} for én postering. Filtre som ikke finnes: beskrivelse/fritekst, beløp og vatType – filtrer lokalt. Nyttige felt: invoiceNumber, termOfPayment, externalRef (KID), matched, closeGroup(id), freeAccountingDimension1-3(displayName).

### Finne åpne poster i kundereskontro/leverandørreskontro per dato
- **Kall:** `GET /ledger/posting/openPost`, `GET /ledger/openPost`, `GET /customer`, `GET /supplier`
- **Nøkkelord:** åpne poster, apne poster, reskontro, kundereskontro, leverandørreskontro, leverandorreskontro, utestående, utestaende, ubetalt, aldersfordeling, open items, open post, skyldig, reskontrospesifikasjon, reskontroliste, forfalte poster, kid
- GET /ledger/posting/openPost?date=<dagen etter skjæringsdato> (date er ekskl.) gir åpne posteringer. Avgrens med accountNumberFrom/accountNumberTo (f.eks. 1500–1599 kunder, 2400–2499 leverandører), customerId, supplierId eller employeeId. Sett sorted=false for mye raskere svar på store kontoer. fields=id,date,amount,amountCurrency,invoiceNumber,termOfPayment,customer(name),supplier(name),voucher(number,year). GET /ledger/openPost returnerer i stedet LedgerAccount (sum åpne poster per konto: openingBalance/sumAmount/closingBalance + postings) – nyttig for saldo per reskontrokonto, men har ikke accountNumberFrom/To eller sorted. Summer per kunde/leverandør lokalt for reskontrosaldo og aldersfordeling (termOfPayment = forfall). Bare kontoer med isCloseable=true (reskontro-/avstemmingskontoer) har åpne poster. externalRef gir KID.

### ✏️ Lukke/utlikne åpne poster mot hverandre (f.eks. faktura mot innbetaling)
- **Kall:** `GET /ledger/posting/openPost`, `PUT /ledger/posting/:closePostings`
- **Nøkkelord:** lukke poster, utlikne, utligne, motpostere, avstemme reskontro, matche, close postings, åpne poster, apne poster, nullstille reskontro, lukkegruppe
- 1) Finn postene med GET /ledger/posting/openPost (date, customerId/supplierId/employeeId, fields=id,amount,invoiceNumber,date). 2) Kontroller at de gjelder samme kunde/leverandør/ansatt og summerer til 0. 3) Kontoen må ha isCloseable=true. 4) PUT /ledger/posting/:closePostings med JSON-body som array av posting-id-er, f.eks. [123,456]. Skrivende – krever bekreftelse. Resultatet kan sees som closeGroup på postene.

### Se hvilke poster som er lukket mot hverandre (lukkegrupper)
- **Kall:** `GET /ledger/closeGroup`, `GET /ledger/closeGroup/{id}`, `GET /ledger/posting/{id}`
- **Nøkkelord:** lukkegruppe, lukket post, utlignet, utliknet, hva er faktura lukket mot, close group, matched, sporing betaling
- GET /ledger/closeGroup krever dateFrom og dateTo (ekskl.); fields=id,date,postings(id,date,amount,description,voucher(number,year)). For én postering: GET /ledger/posting/{id}?fields=closeGroup(id) og deretter GET /ledger/closeGroup/{id} for å se alle poster i samme lukking.

### Søke opp bilag etter periode, bilagsnummer eller bilagstype
- **Kall:** `GET /ledger/voucher`, `GET /ledger/voucher/{id}`, `GET /ledger/voucherType`
- **Nøkkelord:** finn bilag, søk bilag, sok bilag, bilagsnummer, bilagsliste, bilagsjournal, journal, voucher search, bilag nr, bilagstype, memorial
- GET /ledger/voucher krever dateFrom og dateTo (ekskl.). Filtrer med number (liste), numberFrom (inkl.)/numberTo (ekskl.) og typeId (id fra GET /ledger/voucherType?name=...). Bilagsnummer er per år – kombiner med dato for riktig år. fields=id,number,year,date,description,voucherType(name),postings(row,account(number),amountGross,vatType(number),description). Hent ett bilag med GET /ledger/voucher/{id} (inkl. version før endring). Det finnes ikke fritekst-/beskrivelsesfilter på GET /ledger/voucher – filtrer lokalt. Kladd uten bilagsnummer har tempNumber; bruk />nonPosted for dem.

### Finne bilag via eksternt bilagsnummer (fra import eller integrasjon)
- **Kall:** `GET /ledger/voucher/>externalVoucherNumber`
- **Nøkkelord:** eksternt bilagsnummer, external voucher number, referanse, import-id, integrasjon, duplikatsjekk, finnes bilaget
- GET /ledger/voucher/>externalVoucherNumber?externalVoucherNumber=<nr> (merk '>' i stien). Nyttig for å sjekke duplikater før man oppretter bilag med externalVoucherNumber (maks 70 tegn). fields=id,number,year,date,description.

### Hente bilaget som PDF eller se bilagsbildet/vedlegget
- **Kall:** `GET /ledger/voucher/{voucherId}/pdf`, `GET /ledger/voucher/{id}`, `GET /document/{id}/content`
- **Nøkkelord:** bilag pdf, bilagsbilde, vedlegg, kvittering, dokumentasjon, last ned bilag, voucher pdf, attachment, se bilag
- GET /ledger/voucher/{voucherId}/pdf gir PDF av bilaget (binært svar – lagre til fil). For originalvedlegget: GET /ledger/voucher/{id}?fields=attachment(id,fileName) og deretter GET /document/{id}/content (BETA, download=true) med attachment-id (eller document-id for hoveddokumentet).

### Finne bilag som mangler vedlegg/dokumentasjon
- **Kall:** `GET /ledger/voucher`
- **Nøkkelord:** mangler vedlegg, mangler bilag, mangler dokumentasjon, uten vedlegg, bilag uten dokumentasjon, kontroll dokumentasjon, bokføringsforskriften, bokforingsforskriften
- GET /ledger/voucher med dateFrom/dateTo (ekskl.) og fields=id,number,year,date,description,voucherType(name),attachment(id),document(id). Filtrer lokalt på bilag der både attachment og document er null. Systemgenererte bilag (utgående faktura, lønn) har ofte ikke eget vedlegg – filtrer bort via voucherType. Bla med from/count.

### ✏️ Føre et manuelt bilag (memorialbilag/journalpost)
- **Kall:** `GET /ledger/account`, `GET /ledger/vatType`, `GET /ledger/voucherType`, `POST /ledger/voucher`, `GET /ledger/postingRules`
- **Nøkkelord:** føre bilag, fore bilag, bokføre, bokfore, manuelt bilag, memorial, journalpost, ompostering, korreksjonspostering, journal entry, create voucher, postere, mva-kode, bilagsføring, bilagsforing, journalføring, omkontering
- 1) Slå opp konto-id-er: GET /ledger/account?number=6300,1920&fields=id,number,name,vatType(id),vatLocked,requiresDepartment,requiresProject. 2) MVA-kode: GET /ledger/vatType?number=1&fields=id,number,name (eller typeOfVat). 3) Evt. bilagstype: GET /ledger/voucherType?name=... 4) POST /ledger/voucher med {date, description, voucherType?, postings:[{row:1, date, account:{id}, amountGross, amountGrossCurrency, currency?, vatType:{id}, description, department/project/customer/supplier ved behov}, {row:2, ...motpost}]}. Bruttobeløp (inkl. MVA) med 2 desimaler, debet positivt/kredit negativt, summen av amountGross skal være 0. row starter på 1 (row 0 er systemgenerert – MVA-linjene lages automatisk fra vatType). Poster mot reskontrokonto (1500/2400 o.l.) må ha customer/supplier/employee. sendToLedger har default true = bokføres direkte (krever 'Advanced Voucher'-rettighet); sett sendToLedger=false for å lage et ikke-bokført bilag (kladd) som kan kontrolleres og bokføres senere med :sendToLedger. Fri dimensjon på linjen: freeAccountingDimension1-3:{id}. Skrivende – krever bekreftelse. Sjekk evt. account.legalVatTypes for lovlige MVA-koder på kontoen, og GET /ledger/postingRules for hvilke reskontrokontoer systemet bruker.

### ✏️ Føre bilag i utenlandsk valuta
- **Kall:** `GET /currency`, `GET /currency/{id}/rate`, `POST /ledger/voucher`
- **Nøkkelord:** valuta, valutabilag, eur, usd, utenlandsk faktura, valutakurs, omregning, currency voucher, agio, disagio
- 1) GET /currency?code=EUR&fields=id,code for valuta-id. 2) Evt. sjekk kurs: GET /currency/{id}/rate?date=yyyy-MM-dd. 3) POST /ledger/voucher?convertFromAmountGrossCurrency=true med postings som har currency:{id} og amountGrossCurrency – Tripletex regner da ut amountGross (NOK) med nyeste kurs for posteringsdatoen. Alternativt oppgi både amountGross og amountGrossCurrency selv. Summen i NOK må gå i null. Skrivende – krever bekreftelse.

### ✏️ Periodisere en kostnad eller inntekt over flere måneder
- **Kall:** `GET /ledger/account`, `POST /ledger/voucher`
- **Nøkkelord:** periodisering, periodisere, forskuddsbetalt kostnad, forskuddsbetalt, påløpt, palopt, 1700, 2900, amortisering, fordele kostnad, accrual, amortization, periodiseringskonto
- POST /ledger/voucher der kostnadsposteringen har amortizationAccount:{id} (periodiseringskonto, f.eks. 1700 forskuddsbetalt kostnad – id fra GET /ledger/account?number=1700), amortizationStartDate og amortizationEndDate (alle tre må oppgis). Tripletex fordeler da beløpet månedlig over perioden. Alternativt manuelle periodiseringsbilag per måned med vanlige postinger. Skrivende – krever bekreftelse.

### ✏️ Endre/korrigere et eksisterende bilag
- **Kall:** `GET /ledger/voucher/{id}`, `PUT /ledger/voucher/{id}`, `PUT /ledger/voucher/list`
- **Nøkkelord:** endre bilag, korrigere bilag, rette bilag, feilføring, feilforing, omkontering, endre konto, endre mva-kode, update voucher, oppdatere bilag
- 1) GET /ledger/voucher/{id}?fields=id,version,date,description,postings(id,row,account(id,number),amountGross,amountGrossCurrency,vatType(id),department(id),project(id),customer(id),supplier(id)). 2) PUT /ledger/voucher/{id} (NB: sendToLedger har default true – et ikke-bokført bilag blir bokført ved PUT med mindre du sender sendToLedger=false) med hele bilaget inkl. version og alle manuelle postinger (row>=1). Postinger med row/guiRow 0 slettes og regenereres (MVA/system). 3) Flere bilag samtidig: PUT /ledger/voucher/list. Bilag i lukket periode eller systemgenererte bilag (faktura, lønn) kan ikke endres – bruk reversering + nytt bilag. Skrivende – krever bekreftelse.

### ✏️ Reversere/tilbakeføre et bilag
- **Kall:** `GET /ledger/voucher`, `PUT /ledger/voucher/{id}/:reverse`
- **Nøkkelord:** reversere, reversering, tilbakeføre, tilbakefore, tilbakeføring, kreditere bilag, motbilag, annullere, reverse voucher, angre bilag
- Finn bilags-id (GET /ledger/voucher med number og dateFrom/dateTo). PUT /ledger/voucher/{id}/:reverse?date=yyyy-MM-dd (date påkrevd – reverseringsdato, må ligge i åpen periode). Returnerer det nye reverseringsbilaget. Støtter ikke lønnsbilag (salary transactions). Skrivende – krever bekreftelse.

### ✏️ Slette et bilag
- **Kall:** `GET /ledger/voucher/{id}/options`, `DELETE /ledger/voucher/{id}`
- **Nøkkelord:** slette bilag, fjerne bilag, delete voucher, kan bilaget slettes, slett kladd, feilregistrert bilag
- 1) GET /ledger/voucher/{id}/options?fields=delete(available,reasons) – available=false gir årsakene i reasons. 2) DELETE /ledger/voucher/{id}. Bokførte bilag i lukket periode og systemgenererte bilag kan normalt ikke slettes – reverser i stedet (PUT /ledger/voucher/{id}/:reverse). Sletting er irreversibel – krever eksplisitt bekreftelse.

### ✏️ Finne ikke-bokførte bilag (kladd) og bokføre dem, eller sende tilbake til bilagsmottak
- **Kall:** `GET /ledger/voucher/>nonPosted`, `PUT /ledger/voucher/{id}/:sendToLedger`, `PUT /ledger/voucher/{id}/:sendToInbox`
- **Nøkkelord:** ikke bokført, ikke bokfort, kladd, ubokførte bilag, bokføre kladd, send til hovedbok, send to ledger, avvise bilag, send til innboks, send to inbox, non posted, ikke godkjent
- 1) GET /ledger/voucher/>nonPosted?includeNonApproved=true (påkrevd) med evt. dateFrom/dateTo, fields=id,version,number,tempNumber,date,description. 2) Bokfør: PUT /ledger/voucher/{id}/:sendToLedger?version=<v> (number kan utelates – systemet tildeler bilagsnummer). 3) Avvis/send tilbake: PUT /ledger/voucher/{id}/:sendToInbox?version=<v>&comment=<årsak> (comment brukes bare når attestasjon/godkjenning er aktivert). Krever 'Advanced Voucher'-rettighet. Skrivende – krever bekreftelse. version er valgfri men anbefalt (hindrer at en versjon som er endret i mellomtiden bokføres).

### ✏️ Laste opp vedlegg (kvittering/bilagsbilde) til et bilag eller fjerne vedlegg
- **Kall:** `POST /ledger/voucher/{voucherId}/attachment`, `DELETE /ledger/voucher/{voucherId}/attachment`
- **Nøkkelord:** last opp vedlegg, legge ved kvittering, bilagsbilde, vedlegg, dokumentasjon, attachment, upload, fjerne vedlegg, flytte vedlegg til innboks
- POST /ledger/voucher/{voucherId}/attachment som multipart/form-data med felt 'file' (PDF, PNG, JPEG, TIFF – ikke-PDF konverteres). Har bilaget vedlegg fra før, legges nye sider til på slutten. Fjerne: DELETE /ledger/voucher/{voucherId}/attachment (version; sendToInbox=true flytter vedlegget til bilagsmottak i stedet for å slette, split=true deler per side). Ikke bruk utgått POST /ledger/voucher/{voucherId}/pdf/{fileName}. Skrivende – krever bekreftelse.

### Sjekke bilagsmottaket (antall ubehandlede, liste og e-postadresse)
- **Kall:** `GET /voucherInbox/inboxCount`, `GET /ledger/voucher/>voucherReception`, `GET /voucherInbox/emailAddress`
- **Nøkkelord:** bilagsmottak, innboks, inbox, ubehandlede bilag, hvor mange bilag, epostadresse bilag, e-post til bilagsmottak, skannede bilag, ehf, voucher reception
- GET /voucherInbox/inboxCount gir antall dokumenter i innboksen. GET /ledger/voucher/>voucherReception (dateFrom/dateTo valgfrie, searchText for fritekst) lister bilagene i bilagsmottaket; fields=id,date,description,attachment(id). GET /voucherInbox/emailAddress gir klientens e-postadresse for innsending av fakturaer/kvitteringer.

### ✏️ Laste opp dokumenter til bilagsmottak for å opprette nye bilag
- **Kall:** `POST /ledger/voucher/importDocument`
- **Nøkkelord:** last opp bilag, skanne bilag, importere dokument, sende bilag til tripletex, import document, kvitteringer, fakturaer pdf, dele pdf, bilagsmottak
- POST /ledger/voucher/importDocument som multipart/form-data med 'file' (PDF/PNG/JPEG/TIFF; EHF/XML kun etter avtale med Tripletex) og valgfri 'description'. split=true (query-parameter, default false) lager ett bilag per side. Bilagene havner i bilagsmottaket for videre behandling/tolking. Skrivende – krever bekreftelse.

### ✏️ Importere bilag fra GBAT10-fil
- **Kall:** `POST /ledger/voucher/importGbat10`
- **Nøkkelord:** gbat10, gbat, import bilag, filimport, lønnsfil, lonnsfil, eksternt lønnssystem, import av posteringer, gbat10-fil, lønnsbilag import, lonnsbilag import
- POST /ledger/voucher/importGbat10 som multipart/form-data med 'file', påkrevd form-felt generateVatPostings og valgfritt encoding (filens tegnsett) (true = Tripletex genererer MVA-posteringer ut fra MVA-kodene). Vanlig for import fra eksterne lønns-/fagsystemer. Kontroller importerte bilag med GET /ledger/voucher etterpå. Skrivende – krever bekreftelse.

### ✏️ Registrere åpningsbalanse (IB) ved oppstart i Tripletex
- **Kall:** `GET /ledger/voucher/openingBalance`, `POST /ledger/voucher/openingBalance`, `GET /ledger/voucher/openingBalance/>correctionVoucher`, `DELETE /ledger/voucher/openingBalance`, `GET /ledger/account`
- **Nøkkelord:** åpningsbalanse, apningsbalanse, inngående balanse, ib, oppstart, overgang til tripletex, startbalanse, opening balance, korreksjonsbilag, reskontro ib, konvertering
- 1) Sjekk om det finnes IB: GET /ledger/voucher/openingBalance. 2) POST /ledger/voucher/openingBalance med {voucherDate (1. i en måned, helst 1. januar), balancePostings:[{account:{id}, amount, amountCurrency?, department/project/freeDimension?}], customerPostings:[{customer:{id}, amount, description}], supplierPostings:[...], employeePostings:[...]}. Alle bevegelser før datoen nulles ut i et eget korreksjonsbilag (GET /ledger/voucher/openingBalance/>correctionVoucher). Ubalanse føres automatisk mot en hjelpekonto – kontroller den etterpå med GET /balanceSheet. 3) Feil IB: DELETE /ledger/voucher/openingBalance sletter både IB og korreksjonsbilag. Skrivende – krever bekreftelse.

### ✏️ Importere historiske bilag fra tidligere regnskapssystem
- **Kall:** `POST /ledger/voucher/historical/historical`, `POST /ledger/voucher/historical/{voucherId}/attachment`, `PUT /ledger/voucher/historical/:closePostings`, `POST /ledger/voucher/historical/employee`, `PUT /ledger/voucher/historical/:reverseHistoricalVouchers`
- **Nøkkelord:** historiske bilag, konvertering, migrering, import fra visma, import fra poweroffice, tidligere år, lukkede år, historical, overføre historikk, systembytte
- 1) POST /ledger/voucher/historical/historical?comment=<kildesystem og versjon>&useCustomNumberSeries=... med {date, externalVoucherNumber, description, voucherType?, postings:[{date, account:{id}, currency:{id}, amount, amountCurrency, amountGross, amountGrossCurrency, amountVat, vatType, customer/supplier/employee, invoiceNumber, termOfPayment, closeGroup?}]}. Alle beløpsfelt brukes – MVA-linjer må tas med selv, og amount må summere til 0 på hver enkelt dato. NB: spec-teksten krever amountBasis/amountBasisCurrency, men de feltene finnes ikke i HistoricalPosting-skjemaet – bruk amountGross/amountGrossCurrency/amountVat. closeGroup på posteringen er en fri tekstnøkkel som lukker poster med samme verdi mot hverandre. Kun for lukkede regnskapsår. Krever 'All vouchers' + 'Advanced Voucher'. 2) Vedlegg: POST /ledger/voucher/historical/{voucherId}/attachment (multipart). 3) Lukk historiske åpne poster: PUT /ledger/voucher/historical/:closePostings (BETA, body er en tekststreng med kommaseparerte posting-id-er – query postingIds er utgått; postene må ha samme kunde/leverandør/ansatt og summere til 0). 4) Ansatte fra import: POST /ledger/voucher/historical/employee (BETA – personopplysninger, minimer felt). 5) Angre ALT: PUT /ledger/voucher/historical/:reverseHistoricalVouchers (BETA, sletter alle historiske bilag). Skrivende – krever bekreftelse.

### Hente kontoplanen eller slå opp en konto
- **Kall:** `GET /ledger/account`, `GET /ledger/account/{id}`
- **Nøkkelord:** kontoplan, konto, kontonummer, finn konto, kontoliste, chart of accounts, bankkontoer, balansekontoer, saf-t kode, inaktive kontoer, reskontrokonto, kontotype, kontonavn, lovlige mva-koder
- GET /ledger/account med number (liste, f.eks. number=1920,2400), isBankAccount, isInactive, isBalanceAccount, isApplicableForSupplierInvoice, ledgerType (GENERAL|CUSTOMER|VENDOR|EMPLOYEE|ASSET) eller saftCode. fields=id,number,name,type,vatType(number),vatLocked,isInactive,requireReconciliation,requiresDepartment,requiresProject. Id-en herfra brukes som accountId i alle andre kall. GET /ledger/account/{id} for én konto. GET /ledger/account har ikke navnefilter – hent listen (count default 1000) og filtrer på name lokalt. type (ASSETS, LIABILITIES, OPERATING_REVENUES, OPERATING_EXPENSES m.fl.) og legalVatTypes er skrivebeskyttede, nyttige felt.

### ✏️ Opprette eller endre kontoer i kontoplanen
- **Kall:** `GET /ledger/account`, `POST /ledger/account`, `POST /ledger/account/list`, `PUT /ledger/account/{id}`, `PUT /ledger/account/list`
- **Nøkkelord:** ny konto, opprette konto, endre konto, kontonavn, deaktivere konto, låse mva-kode, lase mva-kode, krev avdeling, krev prosjekt, avstemmingspliktig, update account, create account, underkonto
- Sjekk først at nummeret er ledig: GET /ledger/account?number=... Opprett: POST /ledger/account med {number, name, description?, vatType:{id}?, vatLocked?, isCloseable?, requireReconciliation?, requiresDepartment?, requiresProject?, requiresFreeDimension1-3?, isInactive?, saftCode?, groupingCode?}; flere samtidig med POST /ledger/account/list. Endre: GET for version, deretter PUT /ledger/account/{id} (eller PUT /ledger/account/list). Deaktiver med isInactive=true. ledgerType (GENERAL|CUSTOMER|VENDOR|EMPLOYEE|ASSET) kun med modulen for flere reskontroer. isCloseable=true gjør at poster kan lukkes og åpne poster filtreres på kontoen. saftCode/groupingCode får standardverdi ut fra kontonummer hvis tomme. Skrivende – krever bekreftelse.

### ✏️ Slette kontoer fra kontoplanen
- **Kall:** `GET /ledger/account`, `DELETE /ledger/account/{id}`, `DELETE /ledger/account/list`
- **Nøkkelord:** slette konto, fjerne konto, rydde kontoplan, delete account, ubrukte kontoer
- Finn id med GET /ledger/account?number=...&fields=id,number,name,isPostingsExist. Kontoer med posteringer (isPostingsExist=true) kan ikke slettes – sett isInactive=true via PUT i stedet. DELETE /ledger/account/{id} eller DELETE /ledger/account/list?ids=1,2,3. Irreversibelt – krever eksplisitt bekreftelse.

### ✏️ Opprette og vedlikeholde frie dimensjoner (egendefinerte dimensjoner)
- **Kall:** `GET /ledger/accountingDimensionName`, `GET /ledger/accountingDimensionName/search`, `GET /ledger/accountingDimensionName/{id}`, `POST /ledger/accountingDimensionName`, `PUT /ledger/accountingDimensionName/{id}`, `DELETE /ledger/accountingDimensionName/{id}`
- **Nøkkelord:** fri dimensjon, egendefinert dimensjon, ny dimensjon, kostnadssted, segment, analysedimensjon, deaktivere dimensjon, accounting dimension
- List: GET /ledger/accountingDimensionName?activeOnly=true eller /search (dimensionIndex 1-3, onlyDimensionsWithActiveValues). Opprett: POST /ledger/accountingDimensionName med {dimensionName, description, active:true} – får neste ledige indeks (maks 3 frie dimensjoner). Endre navn/aktiv: PUT /ledger/accountingDimensionName/{id} med version. DELETE /ledger/accountingDimensionName/{id} går bare hvis verdiene ikke er brukt i posteringer – ellers deaktiver/gi nytt navn. Skrivende – krever bekreftelse.

### ✏️ Opprette og vedlikeholde verdier i frie dimensjoner
- **Kall:** `GET /ledger/accountingDimensionValue/search`, `GET /ledger/accountingDimensionValue/{id}`, `POST /ledger/accountingDimensionValue`, `PUT /ledger/accountingDimensionValue/list`, `DELETE /ledger/accountingDimensionValue/{id}`
- **Nøkkelord:** dimensjonsverdi, ny verdi, legge til kostnadssted, verdi fri dimensjon, dimension value, vis i bilagsregistrering, deaktivere verdi
- Søk: GET /ledger/accountingDimensionValue/search?dimensionIndex=1&activeOnly=true (fields=id,number,displayName,active,showInVoucherRegistration). Opprett: POST /ledger/accountingDimensionValue med {dimensionIndex, displayName, number, active:true, showInVoucherRegistration:true, position?}. Oppdater (flere): PUT /ledger/accountingDimensionValue/list med id+version. DELETE /ledger/accountingDimensionValue/{id} kun for verdier som ikke er brukt i posteringer. Verdi-id brukes som freeAccountingDimension1-3 på postinger og som accountingDimensionValue1-3Id/freeDimension1-3 i rapporter. Skrivende – krever bekreftelse.

### Sjekke regnskapsperioder og om en periode er lukket/låst
- **Kall:** `GET /ledger/accountingPeriod`, `GET /ledger/accountingPeriod/{id}`, `GET /ledger/annualAccount`, `GET /ledger/annualAccount/{id}`
- **Nøkkelord:** regnskapsperiode, låst periode, last periode, lukket periode, periodelås, periodelas, månedsavslutning, manedsavslutning, regnskapsår, accounting period, kan jeg føre i perioden
- GET /ledger/accountingPeriod med startFrom/startTo, endFrom/endTo (til-verdier ekskl.) eller numberFrom/numberTo (numberTo ekskl.); count default 1400; fields=id,name,number,start,end,isClosed,checkLedgerLogTime,checkWageLogTime (unngå *EmployeeName-feltene – personopplysning). GET /ledger/annualAccount?yearFrom=2025&yearTo=2026 for regnskapsår (start/end, avvikende regnskapsår). API-et kan bare lese perioder – lukking/låsing gjøres i Tripletex-GUI.

### Hente resultatbudsjett og sammenligne mot regnskap (budsjettavvik)
- **Kall:** `GET /resultbudget/company`, `GET /resultbudget`, `GET /resultbudget/department/{id}`, `GET /resultbudget/project/{id}`, `GET /resultbudget/product/{id}`, `GET /resultbudget/employee/{id}`, `GET /balanceSheet`
- **Nøkkelord:** budsjett, resultatbudsjett, budsjettavvik, budsjett mot regnskap, avvik, avdelingsbudsjett, prosjektbudsjett, result budget, budget vs actual, budsjettoppfølging, budsjettoppfolging, årsbudsjett
- 1) Budsjett: GET /resultbudget/company?year=2025 (year 1900–2100, default inneværende år) (fields=account(number,name),accountingPeriod(number,start),amount), eller per avdeling/prosjekt/produkt/ansatt via /resultbudget/{type}/{id}?year=. GET /resultbudget med departmentIds/projectIds/... eller includeAll*ResultBudgets=true for mange samtidig. 2) Faktisk: GET /balanceSheet med samme periode (dateTo ekskl.) og samme departmentId/projectId. 3) Beregn avvik per konto/periode lokalt. Ansattbudsjett er personrelatert – vis aggregert. Budsjett kan kun leses via API (ingen POST/PUT).

### Slå opp valutakurs og regne om beløp mellom valutaer
- **Kall:** `GET /currency`, `GET /currency/{id}`, `GET /currency/{id}/rate`, `GET /currency/{fromCurrencyID}/exchangeRate`, `GET /currency/{fromCurrencyID}/{toCurrencyID}/exchangeRate`
- **Nøkkelord:** valutakurs, kurs, omregning, eur til nok, usd, exchange rate, dagskurs, norges bank kurs, valuta
- Finn valuta-id: GET /currency?code=EUR&fields=id,code,description. Kurs: GET /currency/{id}/rate?date=yyyy-MM-dd. Omregn til selskapsvaluta: GET /currency/{fromCurrencyID}/exchangeRate?amount=1000&date=... Mellom to valutaer: GET /currency/{fromCurrencyID}/{toCurrencyID}/exchangeRate?amount=&date= (nyeste kurs tilgjengelig på datoen).

### ✏️ Avstemme balansekontoer (årsavstemming) i regnskapsbyrå-modulen
- **Kall:** `POST /balance/reconciliation/annual/context`, `GET /balance/reconciliation/{reconciliationId}/account/{accountId}/vouchers`, `GET /ledger/account`, `GET /balanceSheet`
- **Nøkkelord:** avstemming, årsavstemming, arsavstemming, balanseavstemming, avstemme konto, spesifisere saldo, avstemmingsdokumentasjon, reconciliation, årsoppgjør, arsoppgjor, kontrollere saldo
- 1) POST /balance/reconciliation/annual/context med {customerId (klienten/kunden avstemmingen gjelder), year} → returnerer reconciliationId. 2) Finn konto-id: GET /ledger/account?number=... og saldo: GET /balanceSheet. 3) GET /balance/reconciliation/{reconciliationId}/account/{accountId}/vouchers (fromDate, toDateExclusive, query for fritekst) lister bilagene bak saldoen i avstemmingsperioden (fields=originalId,date,voucherNumber,description,amount,closed,comments,attachments; count default 1000). Opprettelse av kontekst er skrivende (lager avstemmingsobjekt) – bekreft først. Krever regnskapsbyrå-/avstemmingsmodul. Lønnsavstemminger (AGA, forskuddstrekk, feriepenger m.fl.) har egne POST /salary/*/reconciliation/context i lønn-gruppen som også gir reconciliationId. Bankavstemming er noe annet: /bank/reconciliation (bank-gruppen).

### ✏️ Markere avstemming som avstemt, be om kontroll og kontrollere (fire-øyne)
- **Kall:** `PUT /accountingOffice/reconciliations/{reconciliationId}/control/:reconcile`, `PUT /accountingOffice/reconciliations/{reconciliationId}/control/:requestControl`, `PUT /accountingOffice/reconciliations/{reconciliationId}/control/:controlReconciliation`, `GET /accountingOffice/reconciliations/{reconciliationId}/control`
- **Nøkkelord:** marker avstemt, be om kontroll, kontrollere avstemming, godkjenne avstemming, fire øyne, fire oyne, oppdragsansvarlig, kontrollhistorikk, reconcile, request control, controlled
- reconciliationId fra POST /balance/reconciliation/annual/context (eller lønnsavstemmingskontekster i lønn-gruppen). 1) Avstemt: PUT .../control/:reconcile (ingen body eller parametre utover reconciliationId). 2) Be om kontroll: PUT .../control/:requestControl med JSON-body = array av ansatt-id-er som skal kontrollere, f.eks. [101]. 3) Kontrollør markerer: PUT .../control/:controlReconciliation. 4) Historikk: GET .../control (fields=type,timestamp – type RECONCILED|CONTROL_REQUESTED|CONTROLLED; unngå å vise ansattnavn, bruk initialer). Skrivende – krever bekreftelse.

### ✏️ Legge ved avstemmingsdokumentasjon på en balansekonto
- **Kall:** `GET /ledger/account`, `GET /documentArchive/account/{id}`, `POST /documentArchive/account/{id}`
- **Nøkkelord:** dokumentasjon konto, avstemmingsdokumentasjon, legge ved spesifikasjon, dokumentarkiv konto, kontodokumentasjon, document archive, saldospesifikasjon
- Finn konto-id med GET /ledger/account?number=... . Se eksisterende dokumenter: GET /documentArchive/account/{id}?periodDateFrom=...&periodDateTo=...(ekskl.) (BETA). Last opp: POST /documentArchive/account/{id} som multipart/form-data med 'file' (BETA). Skrivende – krever bekreftelse.

### Hente posteringsregler og standardkontoer (kundefordringer, leverandørgjeld, øreavrunding)
- **Kall:** `GET /ledger/postingRules`
- **Nøkkelord:** posteringsregler, standardkontoer, systemkontoer, hvilken konto kundefordringer, leverandørgjeld konto, øreavrunding, oreavrunding, mva per avdeling, posting rules
- GET /ledger/postingRules?fields=accountReceivableCustomersId(number,name),accountDebtVendorsId(number,name),accountDebtEmployeesAndOwnersId(number,name),accountRoundDiffId(number,name),accountSubscriptionAccrual(number,name),accountProductSaleNoVat(number,name),vatPerDepartment,multipleIndustries. Feltene heter *Id men er Account-objekter. Kun lesing. Nyttig før manuelle føringer mot reskontro og for å vite hvilke kontoer systemet bruker automatisk.

### Finne bilagstyper (typeId) for filtrering eller registrering
- **Kall:** `GET /ledger/voucherType`, `GET /ledger/voucherType/{id}`
- **Nøkkelord:** bilagstype, bilagsart, voucher type, typeid, memorial, leverandørfaktura, bankbilag
- GET /ledger/voucherType?name=...&fields=id,name,displayName (uten name gir alle). Id-en brukes som typeId i GET /ledger/voucher og som voucherType:{id} ved POST /ledger/voucher.

### ✏️ Lese eller legge til kommentarer på bilag
- **Kall:** `GET /voucherMessage`, `POST /voucherMessage`
- **Nøkkelord:** kommentar, kommentere bilag, bilagskommentar, notat, melding på bilag, spørsmål om bilag, sporsmal om bilag, voucher message
- GET /voucherMessage?voucherIds=1,2,3 (fields=voucherId,content,sendTime – dropp sender/avsendernavn av personvernhensyn). POST /voucherMessage med {voucherId, content}. BETA-endepunkter. Skrivende (POST) – krever bekreftelse.

### ✏️ Følge opp status på bilag i integrasjoner (f.eks. inkasso)
- **Kall:** `GET /voucherStatus`, `GET /voucherStatus/{id}`, `POST /voucherStatus`
- **Nøkkelord:** bilagsstatus, inkassostatus, oversendt inkasso, debt collection, integrasjonsstatus, voucher status, status inkassosak
- GET /voucherStatus med voucherIds, status (WAITING|DONE|SKIPPED|ERROR|NONE|PROCESSING|RECLAIMED) og type (TRIPLETEX|SUPPLIERINVOICE_EXTERNAL|DEBT_COLLECTION); fields=id,voucher(id,number),type,status,message,timestamp,referenceNumber,externalObjectUrl. POST /voucherStatus med {voucher:{id}, status, message (NONE|ONGOING|NEEDS_APPROVAL|WITHDRAWN|SETTLED), comment, referenceNumber, externalObjectUrl} brukes av integrasjonspartnere. Krever oppsett fra Tripletex (støtter i dag inkasso). Skrivende (POST) – krever bekreftelse.

### Se attestasjons-/godkjenningsstatus på bilag
- **Kall:** `GET /supplierInvoice/forApproval`, `GET /voucherApprovalListElement/{id}`
- **Nøkkelord:** attestasjon, attestere, godkjenning, til godkjenning, venter på godkjenning, attestant, approval, anvisning, leverandørfaktura til godkjenning
- Oversikt over leverandørfakturaer som venter: GET /supplierInvoice/forApproval (innkjøp-gruppen). Detaljer for én godkjenningslinje: GET /voucherApprovalListElement/{id}?fields=voucher(number),status,organisationLevel,actionDate,comment (dropp employee/actionEmployeeName – personopplysninger; bruk initialer ved behov). Godkjenning gjøres via innkjøp-gruppens :approve-endepunkter.

### Eksportere alle posteringer/hovedbok for en periode (dataanalyse, SAF-T)
- **Kall:** `GET /ledger/postingByDate`, `GET /ledger/posting`, `GET /saft/exportSAFT`
- **Nøkkelord:** eksport hovedbok, datauttrekk, alle posteringer, saf-t, saft, revisjon, dataanalyse, excel-uttrekk, transaksjonsliste, export
- Raskest: GET /ledger/postingByDate?dateFrom=...&dateTo=...(ekskl.) med from/count-paging (støtter IKKE fields – svaret er fullt PostingDTO; krever tilgang til alle bilag, og lønnstilgang hvis lønnstilgangskontroll er på, ellers valideringsfeil). Trenger du felter/filtre: GET /ledger/posting med fields=. Formell SAF-T-fil: GET /saft/exportSAFT?year=2025&version=1.3 (year påkrevd; version 1.2 er default, ellers 1.3/1.4; BETA, årsoppgjør-gruppen). Fjern/masker employee-data før lagring (GDPR).

### Avstemme reskontro mot hovedbok (kundefordringer/leverandørgjeld mot sum åpne poster)
- **Kall:** `GET /ledger/postingRules`, `GET /balanceSheet`, `GET /ledger/posting/openPost`, `GET /ledger/openPost`
- **Nøkkelord:** avstemme reskontro, reskontroavstemming, kundereskontro mot hovedbok, leverandørreskontro mot hovedbok, leverandorreskontro mot hovedbok, 1500, 2400, differanse reskontro, saldo kundefordringer, saldo leverandørgjeld, subledger reconciliation, årsoppgjør, arsoppgjor
- 1) Finn reskontrokontoene: GET /ledger/postingRules?fields=accountReceivableCustomersId(id,number),accountDebtVendorsId(id,number),accountDebtEmployeesAndOwnersId(id,number). 2) Hovedbokssaldo per skjæringsdato: GET /balanceSheet?dateFrom=<årets start>&dateTo=<dagen etter skjæringsdato>&accountNumberFrom=1500&accountNumberTo=1599 (tilsvarende 2400–2499) → balanceOut. 3) Åpne poster samme dato: GET /ledger/posting/openPost?date=<dagen etter>&accountNumberFrom=1500&accountNumberTo=1599&sorted=false&fields=amount,customer(id,name),supplier(id,name) – summer lokalt per kunde/leverandør (eller GET /ledger/openPost?accountId=<id> for sum per konto). Bla med from (count default 1000). 4) Differanse skyldes typisk poster ført på reskontrokonto uten kunde/leverandør, eller feil lukking. Ansattreskontro inneholder personopplysninger – vis kun aggregert.

### Kontrollere at bilagsnummerserien er sammenhengende (hull i bilagsjournalen)
- **Kall:** `GET /ledger/voucher`, `GET /ledger/voucherType`
- **Nøkkelord:** hull i nummerserie, bilagsnummerserie, sammenhengende bilagsnummer, manglende bilagsnummer, bilagsjournal, kontroll bilagsnummer, bokføringsforskriften, bokforingsforskriften, revisjon, voucher number gap
- GET /ledger/voucher?dateFrom=2025-01-01&dateTo=2026-01-01&fields=id,number,year,date,voucherType(name)&count=1000 og bla med from til fullResultSize er nådd. Sorter lokalt på number per year og finn hull. Merk: slettede bilag, historiske bilag med egen nummerserie og bilag som ennå ikke er bokført (har bare tempNumber) kan gi naturlige hull – grupper evt. per voucherType.

### Oversikt over avstemmingsmodulen i regnskapsbyrået – alle avstemminger per kunde, termin, type og status
- **Kall:** `GET /accountingOffice/reconciliations/{reconciliationId}/control`, `GET /document/{id}`, `GET /document/{id}/content`, `GET /customer`
- **Nøkkelord:** avstemmingsmodul, avstemmingsmodulen, avstemmingsoversikt, avstemmingsstatus, status avstemming, avstemminger, hvilke avstemminger, byråavstemming, regnskapsbyrå avstemming, accounting office, accountingoffice, reconciliations, balanseavstemming status, mva-avstemming status, lønnsavstemming status, utkast, fullført, draft, completed, avstemmingsrapport, avstemmingsdokument, reconciliationid, finne reconciliationid, dashbord avstemming
- Modulen ligger i BYRÅETS EGEN konto (companyId 0 = Silfer AS via silfer-tokenet), ikke i klientregnskapet. Klientene er kunder der (customer.id i byråkontoen ≠ klientens company-id). 1) UDOKUMENTERT, men virker: GET /accountingOffice/reconciliations?count=1000&fields=id,year,term,type,status,startDate,endDate,modifiable,requiresControl,customer(id,name,organizationNumber),document(id) – lister alle avstemminger. type: BALANCE (per termin), ANNUAL_BALANCE, VAT_GENERAL_INDUSTRY, VAT_PRIMARY_INDUSTRY, PAYROLL_TAX, TAX_DEDUCTION, MANDATORY_DEDUCTION, HOLIDAY_ALLOWANCE, FINANCE_TAX, SALARY. status: DRAFT|COMPLETED|CONTROLLED|ERROR|WARNING. 2) Én: GET /accountingOffice/reconciliations/{id} (også udokumentert). 3) Historikk: GET /accountingOffice/reconciliations/{reconciliationId}/control (type RECONCILED|CONTROL_REQUESTED|CONTROLLED – ikke vis ansattnavn). 4) Ferdig rapport: document.id → GET /document/{id}?fields=id,fileName,mimeType,size og GET /document/{id}/content (PDF, octet-stream). Kan inneholde personopplysninger (lønn) – ikke del ukritisk. 5) GET /accountingOffice/reconciliations/blocklist finnes også (udokumentert). Lokalt: src/tripletex.js blokkerer companyId 0 med vilje – bruk et eget skript med authorization(0,'silfer') og kun GET. Matche mot klient: customer.organizationNumber = klientens org.nr. (npm run connect). Detaljbildene krever i tillegg delegert klienttilgang til kunden (ellers 403) – se fallgruver. Kun lesing.

### ✏️ Kommentere eller legge ved dokumentasjon på en avstemming i avstemmingsmodulen
- **Kall:** `GET /accountingOffice/reconciliations/{reconciliationId}/control`
- **Nøkkelord:** kommentar avstemming, kommentere avstemming, avstemmingskommentar, merknad avstemming, forklare avvik, dokumentasjon avstemming, vedlegg avstemming, laste opp dokumentasjon, reconciliation comment, reconciliation attachment, aoreconciliationcomment, referenceid
- FINN referenceId FØRST med GET /accountingOffice/reconciliations/{id}/validations → [{referenceId, message}] (linjene som må forklares). UDOKUMENTERT, testet 2026-09-23 i byråkontoen (companyId 0, silfer): GET /accountingOffice/reconciliations/{id}/comments?fields=id,createdAt,referenceId,comment og GET .../{id}/attachments?fields=id,referenceId,document(id,fileName,mimeType). Ny kommentar: POST .../{id}/comments med {referenceId, comment (maks 1024 tegn)} → 201. referenceId er PÅKREVD (positivt heltall) og peker på raden kommentaren gjelder: lønnsavstemminger med månedsrader (TAX_DEDUCTION, MANDATORY_DEDUCTION) bruker epochDays for måneden (dager siden 1970-01-01, f.eks. 20635 = 2026-07-01, samme som registeredPayments/periodOverviews.epochDays); balanse/årsbalanse og trolig finansskatt bruker konto-id i klientens kontoplan; HOLIDAY_ALLOWANCE bruker KONTONUMMERET (2940 skyldig feriepenger og 2785 AGA av feriepenger, verifisert mot kommentar skrevet i UI 2026-09-23) – konto-id gir en kommentar som lagres, men ikke vises i UI. Er du i tvil: be brukeren skrive «test» på riktig linje i UI og les referenceId med GET .../comments. Vedlegg: POST /accountingOffice/reconciliations/{id}/attachments?referenceId=<ref> som multipart/form-data med feltet file → 201 (testet med PDF). PAYROLL_TAX bruker konto-id (2770) som referanse. Ikke skriv personopplysninger i kommentaren. Skrivende – krever bekreftelse.

### ✏️ Fullføre en avstemming i avstemmingsmodulen (status COMPLETED + PDF-rapport)
- **Kall:** `GET /accountingOffice/reconciliations/{reconciliationId}/control`, `GET /document/{id}`
- **Nøkkelord:** fullføre avstemming, fullfør, ferdigstille avstemming, complete reconciliation, avslutte avstemming, låse avstemming, avstemmingsrapport pdf, completed
- UDOKUMENTERT, testet 2026-09-23 (feriepenger klient A T4): PUT /accountingOffice/reconciliations/{id}/:complete (ingen body) i byråkontoen. Ved avvik svarer den 422 med validationMessages[].message = JSON {referenceId, message, severity:ERROR} – f.eks. referenceId 2785 «Vennligst forklar avviket i en kommentar». Legg da kommentar på hver referenceId som nevnes (POST .../{id}/comments {referenceId, comment}) og kjør :complete på nytt. OK → 200, status COMPLETED, modifiable=false (låst) og document = PDF-rapport (GET /document/{id}, fileName «Lønn_<klient>_Term<n>_<år>_<tidsstempel>.pdf»). PUT .../control/:reconcile alene endrer ikke status. Ikke-synlige/feilplasserte kommentarer bør slettes før fullføring. Skrivende – krever bekreftelse.

### Månedsavslutning – statussjekk for én klient (bank, bilagsmottak, attestering, mva, perioder, reiseregninger)
- **Kall:** `GET /ledger/account`, `GET /bank/reconciliation`, `GET /bank/reconciliation/>last`, `GET /ledger/voucher/>voucherReception`, `GET /ledger/voucher/>nonPosted`, `GET /supplierInvoice/forApproval`, `GET /vatReturns/status`, `GET /ledger/accountingPeriod`, `GET /travelExpense`, `GET /balanceSheet`
- **Nøkkelord:** månedsavslutning, manedsavslutning, månedsslutt, periodeavslutning, månedskontroll, manedskontroll, sjekkliste, status klient, hva mangler, hva gjenstår, month end, avslutte måned, klientstatus, restanser
- Krever navngitt klient. Kun lesing. 1) Bankkontoer: `GET /ledger/account`?isBankAccount=true&fields=id,number,name. 2) Per konto: `GET /bank/reconciliation/>last`?accountId=..&fields=id,accountingPeriod(start,end),isClosed – flagg kontoer der siste lukkede avstemming er eldre enn forrige måned (åpne poster: se bank-oppgavene). 3) Bilagsmottak: `GET /ledger/voucher/>voucherReception`?fields=id (antall) og `GET /ledger/voucher/>nonPosted`?dateFrom..&dateTo..&fields=id,date,description (kladder). 4) Leverandørfakturaer til attestering: `GET /supplierInvoice/forApproval`?fields=id,invoiceDate,amount. 5) MVA: `GET /vatReturns/status` for inneværende/forrige termin. 6) Perioder: `GET /ledger/accountingPeriod`?startFrom..&fields=number,start,end,isClosed. 7) Reiseregninger ikke bokført: `GET /travelExpense`?state=..&fields=id,state,amount (ingen navn). 8) Saldo-sanity: `GET /balanceSheet` for måneden (dateTo eksklusiv). Lønn: se «Full lønnsavstemming / A07» (lonn). Rapporter som sjekkliste med tall, uten personopplysninger.

### Årsoppgjørskontroll – full sjekkliste for et regnskapsår
- **Kall:** `GET /balanceSheet`, `GET /ledger/posting/openPost`, `GET /asset/balanceAccountsSum`, `GET /asset`, `GET /vatReturns/status/list`, `POST /balance/reconciliation/annual/context`, `GET /balance/reconciliation/{reconciliationId}/account/{accountId}/vouchers`, `GET /ledger/annualAccount`, `GET /ledger/accountingPeriod`, `GET /ledger/voucher/>nonPosted`, `GET /yearEnd/penneo/signingStatus`
- **Nøkkelord:** årsoppgjørskontroll, arsoppgjorskontroll, årsoppgjør, arsoppgjor, årsavslutning, arsavslutning, kontroll før årsoppgjør, year end, 31.12, balansekontroll, avstemme balanse, årsavstemming, arsavstemming, kontrolliste årsoppgjør
- Krever navngitt klient; bruk gjerne skillen aarsoppgjoer-kontroll. 1) Saldobalanse år og fjorår: `GET /balanceSheet`?dateFrom=ÅÅÅÅ-01-01&dateTo=(ÅÅÅÅ+1)-01-01&includeActiveAccountsWithoutMovements=true. 2) Reskontro per 31.12: `GET /ledger/posting/openPost`?date=(ÅÅÅÅ+1)-01-01 (eksklusiv) for kunder/leverandører, summer og avstem mot 1500/2400. 3) Anlegg: `GET /asset/balanceAccountsSum` mot 11xx–12xx i saldobalansen. 4) MVA: `GET /vatReturns/status/list` for året (alle terminer levert/betalt) og avstem 27xx. 5) Lønn: se lønnsavstemming (lonn). 6) Bank: siste avstemming per 31.12 lukket (bank). 7) Balanseavstemming i byråmodulen: `POST /balance/reconciliation/annual/context` → GET .../account/{accountId}/vouchers; markér via accountingOffice/reconciliations (hovedbok). 8) Ikke-bokførte bilag: `GET /ledger/voucher/>nonPosted`. 9) Regnskapsår/perioder: `GET /ledger/annualAccount`, `GET /ledger/accountingPeriod`. 10) Signering: `GET /yearEnd/penneo/signingStatus`. POST-en i punkt 7 lager kun avstemmingskontekst (ikke bilag).

### Resultatregnskap og balanse for en periode med sammenligning mot fjoråret og budsjett (månedsrapport/nøkkeltall)
- **Kall:** `GET /balanceSheet`, `GET /ledger/account`, `GET /resultbudget/company`
- **Nøkkelord:** resultatregnskap, balanseregnskap, resultat og balanse, månedsrapport, manedsrapport, regnskapsrapport, rapport til kunde, sammenligning i fjor, fjorårstall, hittil i år, driftsresultat, nøkkeltall, nokkeltall, likviditetsgrad, egenkapitalandel, dekningsgrad, kontantstrøm, likviditet, p&l, income statement
- Krever navngitt klient. 1) Inneværende periode: `GET /balanceSheet`?dateFrom=..&dateTo=..(eksklusiv)&fields=account(number,name),balanceIn,balanceChange,balanceOut. 2) Samme periode i fjor: nytt kall med datoer −1 år. 3) Budsjett: `GET /resultbudget/company` (kun lesing i v2). 4) Grupper lokalt: 3xxx driftsinntekter, 4xxx varekost, 5xxx lønn, 6–7xxx andre driftskostnader, 8xxx finans/skatt; balanse 1xxx eiendeler, 2xxx EK/gjeld (inntekter og gjeld har negativt fortegn i Tripletex). 5) Nøkkeltall lokalt: likviditetsgrad 1, egenkapitalandel, bruttofortjeneste; kontantstrøm kun indirekte (endring i balanseposter). Tripletex sine ferdige rapport-PDF-er finnes ikke i v2 (se ikkeIApi).

### Finne kunder/leverandører med kreditsaldo, uidentifiserte innbetalinger eller poster med feil fortegn i reskontro
- **Kall:** `GET /ledger/posting/openPost`, `GET /customer`, `GET /supplier`, `GET /ledger/account`
- **Nøkkelord:** kreditsaldo, negativ saldo, feil fortegn, debetsaldo leverandør, kreditsaldo kunde, overbetaling, overbetalt, tilgodehavende, forskuddsbetaling kunde, uidentifisert innbetaling, ukjent innbetaling, innbetaling uten faktura, ikke utlignet, reskontrokontroll
- Krever navngitt klient. Kun lesing. 1) `GET /ledger/posting/openPost`?date=<dag etter skjæringsdato>&accountNumberFrom=1500&accountNumberTo=1599&sorted=false&fields=customer(id),amount,date,voucher(number),description; tilsvarende 2400–2499 med supplier(id). 2) Summer per kunde/leverandør lokalt; flagg kunder med sum < 0 og leverandører med sum > 0, samt innbetalinger som ikke er utlignet mot faktura. 3) Navn: `GET /customer`?id=..&fields=id,name,customerNumber / `GET /supplier` (firmanavn ok; privatpersoner → initialer). 4) Foreslå utligning (hovedbok: «Lukke/utlikne åpne poster») eller tilbakebetaling (egen oppgave) – ikke utfør uten bekreftelse.

### Avstemme mellomregning, aksjonærlån eller konsernmellomværende
- **Kall:** `GET /ledger/account`, `GET /balanceSheet`, `GET /ledger/posting`, `GET /ledger/posting/openPost`, `POST /balance/reconciliation/annual/context`
- **Nøkkelord:** mellomregning, mellomværende, mellomvaerende, aksjonærlån, aksjonaerlan, lån til aksjonær, lån fra aksjonær, konsernmellomværende, konsern, nærstående, lån daglig leder, fordring nærstående, avstemme lån
- Krever navngitt klient. 1) Finn kontoene: `GET /ledger/account`?fields=id,number,name og filtrer lokalt på navn (mellomregning/aksjonær/konsern/lån) – typisk 13xx, 15xx, 22xx, 29xx. 2) IB/UB: `GET /balanceSheet`?dateFrom..&dateTo..&accountNumberFrom=..&accountNumberTo=... 3) Bevegelser: `GET /ledger/posting`?accountId=..&dateFrom..&dateTo..&fields=date,amount,description,voucher(number). 4) Konto med reskontro/dimensjon: `GET /ledger/posting/openPost`. 5) Sammenlign mot motpartens saldo (annen klient i byrået – brukeren må navngi den) eller låneavtale. 6) Dokumenter i balanseavstemmingen (hovedbok: accountingOffice/reconciliations). Personlig aksjonær: ikke vis navn – bruk «aksjonær 1».

### ✏️ Føre avsetninger og påløpte/forskuddsbetalte poster ved periodeslutt, med reversering neste periode
- **Kall:** `GET /ledger/account`, `GET /ledger/vatType`, `POST /ledger/voucher`, `PUT /ledger/voucher/{id}/:reverse`, `POST /ledger/voucher/{voucherId}/attachment`, `GET /ledger/accountingPeriod`
- **Nøkkelord:** påløpt, palopt, påløpte kostnader, avsetning, avsetninger, forskuddsbetalt, forskuddsbetalte kostnader, opptjent inntekt, ikke fakturert inntekt, 2960, 2990, 1700, 1750, reversere neste måned, periodeslutt, accrual
- Skrivende – krever navngitt klient og bekreftelse. 1) Kontoer og mva-kode 0: `GET /ledger/account`?number=..&fields=id,number,vatType(id), `GET /ledger/vatType`?number=0. 2) `POST /ledger/voucher` med date=siste dag i perioden, description «Avsetning/påløpt <tekst> <mnd>», f.eks. debet kostnadskonto / kredit 2960, uten mva. 3) Legg ved grunnlag: `POST /ledger/voucher/{voucherId}/attachment`. 4) Reversering: `PUT /ledger/voucher/{id}/:reverse`?date=<første dag neste periode> (egen bekreftelse). For kostnad fordelt over mange måneder: se «Periodisere en kostnad eller inntekt» (hovedbok). Sjekk først at perioden ikke er låst (`GET /ledger/accountingPeriod`).

### ✏️ Bokføre refusjon av sykepenger/foreldrepenger fra NAV
- **Kall:** `GET /ledger/account`, `GET /ledger/posting`, `POST /ledger/voucher`, `POST /ledger/voucher/{voucherId}/attachment`
- **Nøkkelord:** sykepengerefusjon, refusjon sykepenger, refusjon nav, nav refusjon, sykepenger, foreldrepenger refusjon, 5800, innbetaling fra nav, nav-innbetaling
- Skrivende – krever navngitt klient og bekreftelse. Sykefravær per ansatt er særlig sensitive personopplysninger: vis bare aggregerte beløp, aldri navn/perioder per person. 1) Konto: `GET /ledger/account`?number=5800&fields=id,number,name (evt. 157x hvis selskapet fører refusjonskrav som fordring). 2) Sjekk om innbetalingen allerede er ført: `GET /ledger/posting`?accountNumberFrom=5800&accountNumberTo=5800&dateFrom..&dateTo... 3) `POST /ledger/voucher`: debet bank / kredit 5800 (eller kredit 157x), ingen mva. 4) Vedlegg (utbetalingsmelding): `POST /ledger/voucher/{voucherId}/attachment`. Refusjonskravet til NAV sendes utenfor v2.

### Se endringslogg / revisjonsspor – hvem opprettet eller endret et objekt og når
- **Kall:** `GET /ledger/voucher/{id}`, `GET /customer/{id}`, `GET /supplier/{id}`, `GET /invoice/{id}`, `GET /order/{id}`, `GET /product/{id}`, `GET /ledger/account/{id}`
- **Nøkkelord:** endringslogg, endringshistorikk, revisjonsspor, audit trail, hvem endret, hvem førte, change log, historikk bilag, historikk, changes, sist endret, opprettet av
- Nesten alle objekter i v2 (344 skjemaer) har det skrivebeskyttede feltet changes: legg til fields=id,changes(employeeId,timestamp,changeType) på GET-kallet, f.eks. GET /ledger/voucher/{id}?fields=id,number,changes(employeeId,timestamp,changeType). changeType: CREATE, UPDATE, DELETE, LOCKED, REOPENED. Du får hvem (employeeId) og når, men ikke hvilke felt som ble endret – for det: connector-verktøyet get_change_log eller Tripletex-UI. employeeId er en person – oppgi som «ansatt 1/2» eller initialer, aldri navn.

**Fallgruver:**
- dateTo er EKSKLUSIV i nesten alle søk (/balanceSheet, /ledger, /ledger/posting, /ledger/voucher, /ledger/closeGroup, /ledger/postingByDate): hele 2025 = dateFrom=2025-01-01&dateTo=2026-01-01. date på /ledger/posting/openPost og /ledger/openPost er også 'til og ekskl.'.
- Påkrevde parametre: dateFrom+dateTo på /ledger, /ledger/posting, /ledger/voucher, /balanceSheet, /ledger/closeGroup og /ledger/postingByDate; date på openPost-endepunktene; includeNonApproved på /ledger/voucher/>nonPosted; date på /:reverse.
- accountId/customerId/supplierId osv. er interne id-er, ikke kontonummer/kundenummer. Slå opp med GET /ledger/account?number=... (eller bruk accountNumberFrom/accountNumberTo der det finnes).
- POST /ledger/voucher: kun amountGross/amountGrossCurrency brukes (inkl. MVA), 2 desimaler, summen må bli 0; row starter på 1 (row 0 = systemgenererte linjer som MVA); vatType på linjen gir automatisk MVA-postering; reskontrokontoer (1500/2400 o.l.) krever customer/supplier/employee; kontoer med requiresDepartment/requiresProject/requiresFreeDimension krever dette på linjen.
- POST/PUT /ledger/voucher og PUT /ledger/voucher/list har sendToLedger=true som DEFAULT – bilaget bokføres med en gang (krever 'Advanced Voucher'-rettighet). Send sendToLedger=false for å lage/endre et ikke-bokført bilag; en PUT uten parameteren bokfører en kladd.
- PUT /ledger/voucher/{id}: send med version (optimistisk låsing, ellers 409) og alle manuelle postinger; postinger med guiRow 0 slettes og regenereres. Bilag i lukket periode eller systemgenererte bilag (faktura, lønn) kan ikke endres/slettes – reverser i stedet.
- :reverse støtter ikke lønnsbilag (salary transactions) – de må korrigeres via lønn.
- Action-endepunkter med kolon (/:reverse, /:sendToLedger, /:sendToInbox, /:closePostings, /:reconcile, /:requestControl, /:controlReconciliation, /:reverseHistoricalVouchers) er PUT og tar parametre i query – unntak: /ledger/posting/:closePostings (JSON-array av posting-id-er) og /:requestControl (JSON-array av ansatt-id-er) tar body; /ledger/voucher/historical/:closePostings tar en tekststreng med kommaseparerte id-er i body.
- Stier med '>' er literal del av URL-en: /ledger/voucher/>nonPosted, />externalVoucherNumber, />voucherReception, /ledger/voucher/openingBalance/>correctionVoucher (URL-enkod som %3E om klienten krever det).
- BETA (kan endres uten varsel): /voucherMessage, /ledger/voucher/historical/:closePostings, /ledger/voucher/historical/employee, /ledger/voucher/historical/:reverseHistoricalVouchers, samt /documentArchive/*, /document/{id}/content og /saft/exportSAFT.
- Utgått: POST /ledger/voucher/{voucherId}/pdf/{fileName} (bruk /attachment) og parameteren openPostings på /ledger og /ledger/posting (bruk /ledger/posting/openPost).
- /ledger/postingByDate støtter ikke fields= eller changes, og krever at tokenet har tilgang til alle bilag (og lønn hvis tilgangsstyring for lønn er aktivert) – ellers valideringsfeil.
- /ledger/posting/openPost: sett sorted=false for mye raskere svar på store kontoer (samme poster, bare usortert).
- Filopplasting (/attachment, /importDocument, /importGbat10, historisk attachment, /documentArchive) må sendes som multipart/form-data med feltet 'file'; importGbat10 krever også generateVatPostings.
- Åpningsbalanse: voucherDate må være 1. i en måned (anbefalt 1. januar); alle bevegelser før datoen nulles i et korreksjonsbilag; ubalanse havner på en hjelpekonto; DELETE sletter både IB og korreksjonsbilag.
- Historiske bilag: kun for lukkede år, MVA-linjer må inkluderes manuelt, amount må summere til 0 per dato, krever 'All vouchers' + 'Advanced Voucher'. :reverseHistoricalVouchers sletter ALLE historiske bilag – ekstremt destruktivt.
- Resultatbudsjett, regnskapsperioder og regnskapsår er skrivebeskyttet i API-et – budsjett kan ikke legges inn og perioder kan ikke lukkes/låses via API.
- Kontoer og dimensjonsnavn/-verdier som er brukt i posteringer kan ikke slettes – sett isInactive/active=false i stedet. Maks 3 frie dimensjoner. ledgerType på konto krever modulen for flere reskontroer.
- /voucherStatus krever oppsett fra Tripletex (i dag inkasso). /accountingOffice/reconciliations/* og /balance/reconciliation/* krever regnskapsbyrå-/avstemmingsmodul og kalles i byråets egen konto (companyId 0). Eksisterende reconciliationId finnes med den udokumenterte GET /accountingOffice/reconciliations (se «Oversikt over avstemmingsmodulen») – POST .../context trengs bare for å opprette en ny.
- 403 betyr manglende rettighet for token/bruker (f.eks. 'Advanced Voucher', 'All vouchers', lønnstilgang) eller at modulen ikke er aktiv hos klienten; 422/valideringsfeil betyr brudd på forretningsregel (lukket periode, ubalanse, manglende påkrevd dimensjon/reskontro); 409 betyr utdatert version.
- Bruk alltid fields= og from/count-paging (fullResultSize i svaret) – store klienter har hundretusener av posteringer.
- GDPR: posteringer, lønnsbilag, attestasjonslinjer, kontrollhistorikk og kommentarer kan inneholde ansattdata (employee, sender, actionEmployeeName). Ikke be om disse feltene, og vis kun aggregater/initialer.
- Alle skrivende kall (føre, endre, reversere, slette bilag, lukke poster, IB, import, kontoplanendringer, avstemmingsstatus) krever brukerens bekreftelse og at klienten er eksplisitt valgt.
- count har default 1000 på nesten alle listekall i gruppen (/ledger/accountingPeriod: 1400). Sjekk fullResultSize og bla med from – ellers mister du stille rader ut over 1000.
- GET /ledger/account har ikke navnefilter (bare id, number, isBankAccount, isInactive, isBalanceAccount, isApplicableForSupplierInvoice, ledgerType, saftCode) – filtrer på navn lokalt. GET /ledger/voucher og /ledger/posting har heller ikke fritekst- eller beløpsfilter.
- GET /ledger/openPost returnerer LedgerAccount (summer per konto), mens GET /ledger/posting/openPost returnerer enkeltposteringer. Kun kontoer med isCloseable=true har åpne poster og kan lukkes med :closePostings.
- Historiske bilag: beskrivelsen krever amountBasis/amountBasisCurrency, men feltene finnes ikke i HistoricalPosting-skjemaet – bruk amount, amountCurrency, amountGross, amountGrossCurrency og amountVat.
- /ledger/voucher/{id}/options returnerer bare delete.available + delete.reasons – bruk den før DELETE for å få årsaken i stedet for en feilmelding.
- Avgrensning mot andre grupper: bankavstemming = /bank/reconciliation (bank), lønnsavstemming = /salary/*/reconciliation (lønn), MVA-koder = /ledger/vatType, godkjenning av leverandørfaktura = /supplierInvoice (innkjøp). Denne gruppen dekker balanseavstemming i regnskapsbyrå-modulen.
- I avstemmingsmodulen er customerId/customer.id kundens id i BYRÅETS konto. For klient A var den lik klientens company-id fra /company/>withLoginAccess (<kunde-id>), men match likevel på organisasjonsnummer. Modulen kan ha mange flere kunder enn tokenet har delegert klienttilgang til.
- Avstemmingsmodulen, tilgang (testet 2026-09-23 med silfer-tokenet): liste, /{id}, /{id}/control, /blocklist og dokumentet = 200 for alle kunder. Detaljkallene (GET /balance/reconciliation/{id}/account/{accountId}/vouchers, /salary/*/reconciliation/{id}/*, udokumentert /vat/reconciliation/{id}/overview) = 200 for kunder tokenet OGSÅ har delegert klienttilgang til, men 403 for kunder uten klienttilgang. accountId er kontoens id i KLIENTENS kontoplan (GET /ledger/account hos klienten). Lønnskall med en BALANCE-id gir 500 – bruk en lønns-id (taxDeduction-overview svarte også med en PAYROLL_TAX-id for samme termin). Skrivekallene (context-POST, :reconcile, :requestControl, :controlReconciliation) er ikke testet.
- PUT /accountingOffice/reconciliations/{id}/control/:reconcile (200) logger bare RECONCILED i kontrollhistorikken og endrer ikke status. For COMPLETED: udokumentert PUT .../{id}/:complete (se oppgaven «Fullføre en avstemming»).
- Kommentar med feil referenceId på en avstemming blir lagret (201), men vises ikke i Tripletex-UI. Sjekk referansetypen før POST .../comments (se oppgaven «Kommentere eller legge ved dokumentasjon»). Status kan gå fra DRAFT til ERROR når brukeren åpner avstemmingen i UI og den regnes på nytt med avvik.
- Kart over avstemmingsmodulen: alle interne kall (felles, lønn, A07, mva, balanse, bank) står i docs/avstemmingsmodul.md – hentet fra UI-koden 2026-09-23. Bl.a. GET /accountingOffice/reconciliations/{id}/validations (hva som blokkerer fullføring), periodsOverview, permissions/{kunde-id}, clientOverview/context/{kunde-id}, PUT :complete/:control/:setRequiresControl, og for balanse /balance/reconciliation/{id}/table + :complete/:reopen/:control/:uncontrol.
- contextId fra byråkontoen blir IGNORERT av API-tokenet for klientdata: /ledger/account?contextId=<klient> ga byråets egen konto, og A07-bestilling ga byråets egen A07. Kall klientdata fra klientens kontekst (Basic-auth companyId = kunde-id).
- PUT /ledger/voucher/{id} på bilag med banklinje i en periode med avstemt kontoutskrift gir 422 «Posteringer kan ikke gjøres i en periode der det finnes en avstemt kontoutskrift» – også når bare en annen linje endres (hele bilaget sendes på nytt). Be brukeren endre linjen i UI, eller før et korreksjonsbilag uten banklinje.

## Kunder, ordre, faktura, purring, abonnement/CRM

### Finne en kunde (på navn, org.nr. eller kundenummer)
- **Kall:** `GET /customer`, `GET /customer/{id}`, `GET /supplierCustomer/search`
- **Nøkkelord:** finn kunde, søk kunde, sok kunde, kundeoppslag, kundenummer, org.nr, organisasjonsnummer, kundekort, kunde id, kundeliste, hent kunde, kunder endret siden, inaktive kunder, changedsince, kunde nr
- GET /customer med customerName, organizationNumber (eksakt, 9 siffer uten mellomrom), customerAccountNumber (kundenummer, kommaseparert liste), email/invoiceEmail (eksakt) eller category1Id-3Id. NB: isInactive har default=false, så deaktiverte kunder vises ikke uten isInactive=true. changedSince gir kunder endret etter et tidspunkt (synk/eksport). Bruk fields=id,name,customerNumber,organizationNumber,isInactive,isPrivateIndividual for små svar; count er 1000 som standard – page med from/count. Deretter GET /customer/{id} for detaljer. Usikker på om motparten er kunde eller leverandør: GET /supplierCustomer/search?query=... (kun aktive). GDPR: ikke hent e-post/telefon/adresse for privatpersoner (isPrivateIndividual=true) med mindre oppgaven krever det.

### ✏️ Opprette ny kunde
- **Kall:** `GET /customer`, `POST /customer`, `GET /customer/category`, `GET /country`, `GET /currency`
- **Nøkkelord:** ny kunde, opprette kunde, registrere kunde, legge inn kunde, create customer, kundeoppretting, privatkunde, bedriftskunde
- 1) Sjekk duplikat: GET /customer?organizationNumber=... (og isInactive=true for å fange deaktiverte). 2) POST /customer med minst name; typisk også organizationNumber, isPrivateIndividual, invoiceEmail/email, invoiceSendMethod (EMAIL|EHF|EFAKTURA|AVTALEGIRO|VIPPS|PAPER|MANUAL), emailAttachmentType (LINK|ATTACHMENT), invoicesDueIn + invoicesDueInType (DAYS|MONTHS|RECURRING_DAY_OF_MONTH), language (NO|EN), postalAddress/physicalAddress {addressLine1, postalCode, city, country:{id}} (land-id fra GET /country), category1-3 {id} (GET /customer/category), currency {id} (GET /currency). customerNumber tildeles automatisk hvis utelatt. isSupplier=true gjør den også til leverandør. Skrivende – krever bekreftelse og angitt klient.

### ✏️ Endre kundeopplysninger (e-post, adresse, betalingsfrist, sendemåte/EHF, purreinnstillinger)
- **Kall:** `GET /customer/{id}`, `PUT /customer/{id}`
- **Nøkkelord:** endre kunde, oppdatere kunde, ny fakturaadresse, endre e-post, endre betalingsfrist, bytte til ehf, sendemåte, automatisk purring, kundeinnstillinger, update customer
- Hent kunden med GET /customer/{id}?fields=id,version,<feltene som endres> og send PUT /customer/{id} med id, version og feltene som skal endres (f.eks. invoiceEmail, overdueNoticeEmail, invoiceSendMethod, emailAttachmentType, invoicesDueIn/invoicesDueInType, postalAddress, discountPercentage, singleCustomerInvoice, isAutomaticSoftReminderEnabled / isAutomaticReminderEnabled / isAutomaticNoticeOfDebtCollectionEnabled, isFactoring, accountManager {id}, ledgerAccount {id}). Utdatert version gir konflikt – hent på nytt. EHF krever at kunden har organizationNumber og er registrert som mottaker i Peppol (ELMA).

### ✏️ Importere eller masseoppdatere mange kunder
- **Kall:** `POST /customer/list`, `PUT /customer/list`, `GET /customer`
- **Nøkkelord:** importere kunder, kundeimport, masseoppdatering, bulk, mange kunder, kundeliste excel, oppdatere flere kunder, customer list
- POST /customer/list med en JSON-liste av Customer-objekter (samme felter som POST /customer). For oppdatering: hent id+version med GET /customer?fields=id,version,organizationNumber, og send PUT /customer/list med listen. Begge er BETA. Del opp store importer i mindre bolker og valider org.nr. først for å unngå duplikater.

### ✏️ Deaktivere eller slette kunde
- **Kall:** `PUT /customer/{id}`, `DELETE /customer/{id}`
- **Nøkkelord:** slette kunde, deaktivere kunde, inaktiv kunde, arkivere kunde, fjerne kunde, delete customer, sperre kunde
- Foretrekk deaktivering: PUT /customer/{id} med id, version og isInactive=true. DELETE /customer/{id} (BETA) fungerer normalt bare for kunder uten ordre, fakturaer eller posteringer – ellers feil. Sletting er irreversibel; krever tydelig bekreftelse.

### ✏️ Administrere kunde-/leverandørkategorier
- **Kall:** `GET /customer/category`, `GET /customer/category/{id}`, `POST /customer/category`, `PUT /customer/category/{id}`, `GET /customer`
- **Nøkkelord:** kundekategori, opprette kategori, endre kategori, kategorisere kunder, kundegruppe, segmentere, kategori1
- List eksisterende med GET /customer/category (filtrer name, number, type). Opprett med POST /customer/category {name, number, description, type}. Endre med PUT /customer/category/{id}. Knytt kategori til kunde via PUT /customer/{id} med category1/category2/category3 {id}. Filtrer kunder per kategori med GET /customer?category1Id=...

### ✏️ Kontaktpersoner hos kunde (finne, opprette, endre)
- **Kall:** `GET /contact`, `POST /contact`, `PUT /contact/{id}`, `GET /contact/{id}`
- **Nøkkelord:** kontaktperson, kontakt, kundekontakt, deres referanse, attn, mottaker, contact
- GET /contact?customerId=...&fields=id,firstName,lastName (minimalt – personopplysninger/GDPR, vis initialer i svar). Opprett med POST /contact {firstName, lastName, email, customer:{id}}. Brukes som order.contact eller order.attn på ordre/faktura. Endre med PUT /contact/{id}.

### ✏️ Finne og endre leveringsadresse
- **Kall:** `GET /deliveryAddress`, `GET /deliveryAddress/{id}`, `PUT /deliveryAddress/{id}`, `GET /customer/{id}`
- **Nøkkelord:** leveringsadresse, endre leveringsadresse, fraktadresse, adresse på ordre, leveringssted, delivery address
- Søk med GET /deliveryAddress (addressLine1, postalCode, city, name) eller hent kundens deliveryAddress via GET /customer/{id}?fields=deliveryAddress(*). Endre med PUT /deliveryAddress/{id} (id, version, addressLine1, postalCode, city, country). Det finnes ingen POST – nye leveringsadresser opprettes som del av kunde (POST/PUT /customer) eller ordre (deliveryAddress i POST /order).

### ✏️ Opprette salgsordre med ordrelinjer
- **Kall:** `GET /customer`, `GET /product`, `GET /ledger/vatType`, `POST /order`, `POST /order/orderline`, `POST /order/orderline/list`, `GET /order/orderline/orderLineTemplate`, `POST /order/list`
- **Nøkkelord:** ny ordre, opprette ordre, salgsordre, ordrelinjer, fakturagrunnlag, legge inn varelinjer, create order, ordre med produkter, mange ordre, ordreimport
- 1) Finn customer id (GET /customer) og evt. product id (GET /product?productNumber=...). 2) POST /order med customer {id}, orderDate og deliveryDate (yyyy-MM-dd, påkrevd i praksis), gjerne orderLines inline: [{product:{id}, description, count, unitPriceExcludingVatCurrency, discount, vatType:{id}}]. Ellers legg til linjer etterpå med POST /order/orderline/list (bedre ytelse enn enkeltvis POST /order/orderline) med order {id}. 3) GET /order/orderline/orderLineTemplate?orderId&productId gir forslag til linje (pris/MVA) fra produktet. Valgfritt: invoiceComment, reference, ourContactEmployee, department, project, currency, invoicesDueIn. MVA-kode fra GET /ledger/vatType (f.eks. utgående 25 %). Mange ordre samtidig: POST /order/list (BETA, maks 100 ordre med orderLines per kall).

### Søke opp ordre og se status
- **Kall:** `GET /order`, `GET /order/{id}`, `GET /order/orderline/{id}`
- **Nøkkelord:** finn ordre, ordreliste, åpne ordre, ikke fakturerte ordre, ufakturert, ordrestatus, ordrereferanse, ordrenummer
- GET /order krever orderDateFrom og orderDateTo (To er eksklusiv). Filtrer med customerId (liste), number, deliveryComment, isClosed=false (ordre som fortsatt kan faktureres), isSubscription. fields=id,number,orderDate,deliveryDate,customer(name),isClosed,orderLines(description,count,amountExcludingVatCurrency). Feltet status finnes bare for Logistikk-kunder. Detaljer: GET /order/{id}; enkeltlinje: GET /order/orderline/{id}.

### ✏️ Endre eller slette ordre og ordrelinjer
- **Kall:** `GET /order/{id}`, `PUT /order/{id}`, `PUT /order/orderline/{id}`, `DELETE /order/orderline/{id}`, `DELETE /order/{id}`
- **Nøkkelord:** endre ordre, oppdatere ordre, endre ordrelinje, slette ordrelinje, slette ordre, endre antall, endre pris, rabatt på linje
- Hent ordren med GET /order/{id}?fields=*,orderLines(*). Enkeltlinje: PUT /order/orderline/{id} (BETA) med id, version, count, unitPriceExcludingVatCurrency, discount. Slett linje: DELETE /order/orderline/{id} (BETA). Hele ordren: PUT /order/{id}; med updateLinesAndGroups=true fjernes linjer/grupper som ikke er med i listen – vær forsiktig. DELETE /order/{id} sletter ordre som ikke er fakturert. Fakturerte ordrelinjer kan ikke endres (krediter fakturaen i stedet).

### ✏️ Gruppere ordrelinjer med overskrift og delsum (ordregrupper)
- **Kall:** `GET /order/orderGroup`, `GET /order/orderGroup/{id}`, `POST /order/orderGroup`, `PUT /order/orderGroup`, `DELETE /order/orderGroup/{id}`
- **Nøkkelord:** ordregruppe, delsum, overskrift på faktura, gruppere linjer, seksjon, subtotal
- Opprett med POST /order/orderGroup {order:{id}, title, comment, sortIndex, orderLines:[{id}]} (BETA; bruk orderLines i body, ikke det utgåtte query-parametret orderLineIds). List med GET /order/orderGroup?orderIds=... Endre med PUT /order/orderGroup (id+version i body). Slett med DELETE /order/orderGroup/{id}.

### ✏️ Fakturere en ordre (lage faktura fra ordre)
- **Kall:** `PUT /order/{id}/:invoice`, `GET /invoice/{id}`
- **Nøkkelord:** fakturere, fakturere ordre, lage faktura, opprette faktura fra ordre, ordre til faktura, invoice order, fakturakjøring
- PUT /order/{id}/:invoice?invoiceDate=yyyy-MM-dd (påkrevd, query-parameter). VIKTIG: sendToCustomer er default true – sett sendToCustomer=false hvis fakturaen ikke skal sendes ennå, eller angi sendType (EMAIL|EHF|AVTALEGIRO|EFAKTURA|VIPPS|PAPER|MANUAL) og evt. overrideEmailAddress. createBackorder er kun for pilotkunder. Svaret er Invoice – hent invoiceNumber, kid, amount via GET /invoice/{id}. Selskapet må ha registrert bankkontonummer før faktura kan opprettes. Bokføres automatisk (kundereskontro 1500 / salgsinntekt 3xxx). Skrivende – krever bekreftelse.

### ✏️ Faktura som allerede er betalt (kontantsalg/Vipps/kort) eller a konto-/forskuddsfaktura
- **Kall:** `GET /invoice/paymentType`, `PUT /order/{id}/:invoice`, `POST /invoice`
- **Nøkkelord:** kontantsalg, forhåndsbetalt, forhandsbetalt, betalt ved bestilling, a konto, akonto, forskuddsfaktura, delfaktura, on account, vipps betalt, kortbetaling
- Forhåndsbetalt: finn paymentTypeId med GET /invoice/paymentType, og send både paymentTypeId og paidAmount (i fakturavaluta) på PUT /order/{id}/:invoice eller POST /invoice – begge må angis. Betalingstypens konto må ha samme valuta som fakturaen. To betalinger mulig: paymentTypeIdRestAmount (+ paidAmountAccountCurrencyRest) – restbeløpet beregnes som fakturabeløp minus paidAmount. A konto: PUT /order/{id}/:invoice med createOnAccount=WITH_VAT|WITHOUT_VAT (default NONE), amountOnAccount og onAccountComment. A konto-saldo vises senere i projectInvoiceDetails.onAccountBalanceAmount / order.totalInvoicedOnAccountAmountAbsoluteCurrency. Skrivende – krever bekreftelse.

### ✏️ Samlefaktura – fakturere flere ordre på én faktura
- **Kall:** `GET /order`, `PUT /order/:invoiceMultipleOrders`
- **Nøkkelord:** samlefaktura, flere ordre, slå sammen ordre, sla sammen, én faktura, månedsfaktura, invoice multiple orders
- Finn ordrene med GET /order (customerId, isClosed=false, orderDateFrom/To). PUT /order/:invoiceMultipleOrders?id=1,2,3&invoiceDate=yyyy-MM-dd (BETA; id er kommaseparert liste). Ordrene må ha samme kunde, valuta, forfall, mottaker-e-post, attn og SMS-nummer. sendToCustomer default true – sett false om den ikke skal sendes. Kunden kan også ha singleCustomerInvoice=true.

### ✏️ Opprette faktura direkte (med ordre inline) eller mange fakturaer på en gang
- **Kall:** `POST /invoice`, `POST /invoice/list`, `POST /order`
- **Nøkkelord:** opprette faktura, ny faktura, lage faktura, create invoice, masseutfakturering, fakturaimport, mange fakturaer
- POST /invoice med invoiceDate, invoiceDueDate, customer {id} og orders: [ {id} ] (eksisterende ordre) eller et nytt Order-objekt inline med orderLines. Kun én ordre per faktura. sendToCustomer er default true – sett sendToCustomer=false for å bare opprette. comment = fakturatekst for denne fakturaen. POST /invoice/list (BETA) for inntil 100 fakturaer per kall. Returnerer 201 med Invoice.

### ✏️ Sende eller sende på nytt en faktura (e-post, EHF, eFaktura, papir)
- **Kall:** `PUT /invoice/{id}/:send`, `GET /invoice`
- **Nøkkelord:** sende faktura, send faktura, sende på nytt, ehf, efaktura, e-post faktura, papirfaktura, resend invoice, elektronisk faktura, peppol
- Finn faktura-id med GET /invoice (invoiceDateFrom/To + invoiceNumber). PUT /invoice/{id}/:send?sendType=EMAIL|EHF|AVTALEGIRO|EFAKTURA|VIPPS|PAPER|MANUAL; overrideEmailAddress overstyrer mottaker ved EMAIL. EHF krever org.nr. og Peppol-registrert mottaker; eFaktura/AvtaleGiro/Vipps krever avtaler. Handlingen sender eksternt – krever bekreftelse.

### Søke fakturaer / fakturajournal for en periode
- **Kall:** `GET /invoice`, `GET /invoice/{id}`
- **Nøkkelord:** fakturaliste, fakturajournal, utgående fakturaer, salgsfakturaer, fakturaer i perioden, finn faktura, fakturanummer, kid, faktura på kunde, salgsjournal
- GET /invoice krever invoiceDateFrom og invoiceDateTo (To eksklusiv, f.eks. 2026-01-01 til 2026-02-01 for januar). Filtrer med customerId, invoiceNumber, kid, voucherId, status (ALL|OUTSTANDING|CLOSED). fields=id,invoiceNumber,invoiceDate,invoiceDueDate,customer(name),amount,amountExcludingVat,amountOutstanding,isCreditNote,kid. Bare fakturerte (charged) utgående fakturaer returneres – ikke ordre/utkast. Bruk from/count for paging.

### Liste ubetalte og forfalte kundefakturaer (utestående kundefordringer)
- **Kall:** `GET /invoice`, `GET /ledger/posting/openPost`, `GET /customer`
- **Nøkkelord:** ubetalte fakturaer, forfalte fakturaer, utestående, utestaende, kundefordringer, åpne poster, apne poster, kundereskontro, aldersfordeling, aging, hvem skylder, restanse, innfordring
- Alternativ A (fakturanivå): GET /invoice?invoiceDateFrom=<langt tilbake>&invoiceDateTo=<i morgen>&status=OUTSTANDING&fields=id,invoiceNumber,customer(name),invoiceDueDate,amount,amountOutstanding,amountOutstandingTotal,isCreditNote og filtrer lokalt på amountOutstanding>0 og invoiceDueDate<i dag. OUTSTANDING er ikke det samme som ubetalt (kreditnotaer er med). amountOutstanding er uten purregebyr; amountOutstandingTotal inkluderer siste purring. Alternativ B (reskontro): GET /ledger/posting/openPost?date=<dato, eksklusiv>&accountNumberFrom=1500&accountNumberTo=1599 (evt. customerId, sorted=false for fart) for åpne poster per kunde på en gitt dato. Aldersfordel (0–30, 31–60, 61–90, >90 dager) på forfallsdato.

### Kontoutskrift/reskontro for én kunde
- **Kall:** `GET /customer`, `GET /ledger/posting`, `GET /ledger/posting/openPost`
- **Nøkkelord:** kundereskontro, kontoutskrift, saldo kunde, kundesaldo, kundehistorikk, posteringer kunde, reskontroutskrift, statement
- Finn customerId. Alle bevegelser: GET /ledger/posting?dateFrom&dateTo (begge påkrevd, To eksklusiv)&customerId=...&accountNumberFrom=1500&accountNumberTo=1599&fields=date,voucher(number),description,amount,invoiceNumber,termOfPayment. Kun åpne poster: GET /ledger/posting/openPost?date=<dato, eksklusiv>&customerId=... (parameteren openPostings på /ledger/posting er utgått – ikke bruk den). Summer amount for saldo; inngående saldo = sum av posteringer før dateFrom.

### Sjekke om en faktura er betalt (betalingsstatus og innbetalinger)
- **Kall:** `GET /invoice`, `GET /invoice/{id}`, `GET /reminder`
- **Nøkkelord:** er faktura betalt, betalingsstatus, betalt, delbetalt, innbetalt, restbeløp, restbelop, gjenstående, utestående på faktura, innbetalinger på faktura, payment status
- Finn fakturaen med GET /invoice?invoiceDateFrom&invoiceDateTo&invoiceNumber=... (eller kid=...). Hent GET /invoice/{id}?fields=invoiceNumber,invoiceDueDate,amount,amountCurrency,amountOutstanding,amountOutstandingTotal,sumRemits,isCredited,postings(date,amount,description). amountOutstanding=0 betyr betalt/utlignet (ekskl. purregebyr); amountOutstandingTotal tar med siste purring. isCredited=true betyr at den er kreditert. Purringer: GET /reminder?dateFrom&dateTo&invoiceId=...

### Laste ned faktura som PDF
- **Kall:** `GET /invoice/{invoiceId}/pdf`, `GET /invoice`
- **Nøkkelord:** faktura pdf, last ned faktura, fakturakopi, kopi av faktura, skrive ut faktura, invoice pdf
- Finn id via GET /invoice (invoiceNumber + datoperiode). GET /invoice/{invoiceId}/pdf returnerer binær PDF (application/pdf/octet-stream) – lagre til fil, ikke skriv ut som tekst. download=true (default) gir vedlegg.

### ✏️ Kreditere en faktura (lage kreditnota)
- **Kall:** `GET /invoice`, `PUT /invoice/{id}/:createCreditNote`, `PUT /order/{id}/:invoice`
- **Nøkkelord:** kreditnota, kreditere, kreditere faktura, annullere faktura, tilbakeføre faktura, credit note, feil faktura, reversere faktura
- Full kreditering: PUT /invoice/{id}/:createCreditNote?date=yyyy-MM-dd (påkrevd), comment, sendToCustomer (default true – sett false for ikke å sende), sendType, creditNoteEmail (hvis kundens sendemåte er e-post og feltet er tomt, sendes ikke kreditnotaen). Hele fakturaen nulles ut. Delkreditering: lag ny ordre med negative linjer og fakturer med PUT /order/{id}/:invoice?invoiceIdIfIsCreditNote=<opprinnelig faktura-id>. Krever bekreftelse.

### ✏️ Registrere innbetaling på kundefaktura
- **Kall:** `GET /invoice`, `GET /invoice/paymentType`, `GET /invoice/paymentType/{id}`, `PUT /invoice/{id}/:payment`
- **Nøkkelord:** registrere betaling, innbetaling, betalt faktura, merke som betalt, delbetaling, innbetaling kunde, payment, avstemme innbetaling, kid-innbetaling
- 1) Finn fakturaen: GET /invoice med kid eller invoiceNumber (+ invoiceDateFrom/To). 2) Finn betalingstype: GET /invoice/paymentType?fields=id,description,debitAccount(number) (f.eks. bankkonto 1920). 3) PUT /invoice/{id}/:payment?paymentDate=yyyy-MM-dd&paymentTypeId=..&paidAmount=.. (alle påkrevd). paidAmount er i valutaen til betalingstypens konto; for fakturaer i fremmed valuta må paidAmountCurrency (fakturavaluta) også angis. Delbetaling = lavere beløp. Bokfører innbetalingsbilag automatisk – krever bekreftelse. NB: dersom banktransaksjonen også avstemmes i bankavstemming, unngå dobbel føring.

### ✏️ Sende purring, betalingspåminnelse eller inkassovarsel
- **Kall:** `GET /invoice`, `PUT /invoice/{id}/:createReminder`, `GET /reminder`
- **Nøkkelord:** purring, purre, sende purring, betalingspåminnelse, påminnelse, inkassovarsel, varsel om inkasso, inkasso, purregebyr, forsinkelsesrente, soft reminder, dunning
- Finn forfalte fakturaer (se oppgave om ubetalte fakturaer) og sjekk tidligere purringer med GET /reminder?dateFrom&dateTo&invoiceId=... PUT /invoice/{id}/:createReminder?type=SOFT_REMINDER|REMINDER|NOTICE_OF_DEBT_COLLECTION&date=yyyy-MM-dd (begge påkrevd; enum inneholder også DEBT_COLLECTION, men endepunktet oppgir kun de tre første som støttet). includeCharge=true (purregebyr) og includeInterest=true (forsinkelsesrente) må settes eksplisitt. dispatchType (EMAIL|OWN_PRINTER|SMS|NETS_PRINT|SFTP|API) eller dispatchTypes (kommaseparert); NETS_PRINT kun med NOTICE_OF_DEBT_COLLECTION, SMS/NETS_PRINT må være aktivert; smsNumber må være norsk nummer. email/address/postalCode/city overstyrer mottaker. Sender eksternt – krever bekreftelse.

### Se hvilke purringer som er sendt og laste ned purre-PDF
- **Kall:** `GET /reminder`, `GET /reminder/{id}`, `GET /reminder/{reminderId}/pdf`
- **Nøkkelord:** purringer sendt, purrehistorikk, purreliste, purre pdf, inkassovarsel sendt, reminder list, purregebyr oversikt
- GET /reminder krever dateFrom og dateTo (To eksklusiv); filtrer med invoiceId, customerId, termOfPaymentFrom/To. fields=id,invoiceId,reminderDate,type,charge,interests,totalAmountCurrency,termOfPayment. GET /reminder/{id} for detaljer og GET /reminder/{reminderId}/pdf for PDF (binær).

### Lese fakturamerknad / avtalt betalingsutsettelse på faktura
- **Kall:** `GET /invoice/{id}`, `GET /invoiceRemark/{id}`
- **Nøkkelord:** fakturamerknad, merknad på faktura, betalingsutsettelse, utsatt purring, purrestopp, betalingsavtale, notat faktura, purrepause
- GET /invoice/{id}?fields=id,invoiceNumber,invoiceRemark(id,description,postponeRemindersTo) og evt. GET /invoiceRemark/{id}. Ny merknad kan kun settes via invoiceRemark {description, postponeRemindersTo} i body ved POST /invoice – det finnes ikke eget skrive-endepunkt for invoiceRemark. invoiceRemarks (streng) er utgått.

### ✏️ Sette opp abonnement / repeterende fakturering
- **Kall:** `POST /order`, `PUT /order/{id}/:approveSubscriptionInvoice`, `PUT /order/{id}/:unApproveSubscriptionInvoice`, `GET /order`, `PUT /order/{id}`
- **Nøkkelord:** abonnement, repeterende faktura, gjentakende faktura, fast månedlig faktura, periodisk fakturering, abonnementsfakturering, subscription, løpende avtale, husleiefaktura, serviceavtale
- 1) POST /order med isSubscription=true, subscriptionDuration + subscriptionDurationType (MONTHS|YEAR), subscriptionPeriodsOnInvoice, subscriptionInvoicingTimeInAdvanceOrArrears (ADVANCE|ARREARS), subscriptionInvoicingTime + subscriptionInvoicingTimeType (DAYS|MONTHS), isSubscriptionAutoInvoicing=true for automatisk fakturering, samt orderLines. 2) Godkjenn: PUT /order/{id}/:approveSubscriptionInvoice?invoiceDate=yyyy-MM-dd (påkrevd). 3) Stopp/endre: PUT /order/{id}/:unApproveSubscriptionInvoice, deretter PUT /order/{id}. List abonnement med GET /order?isSubscription=true (orderDateFrom/To påkrevd).

### ✏️ Ordrebekreftelse, pakkseddel og forhåndsvisning av faktura (PDF/e-post)
- **Kall:** `GET /order/orderConfirmation/{orderId}/pdf`, `PUT /order/sendOrderConfirmation/{orderId}`, `GET /order/packingNote/{orderId}/pdf`, `PUT /order/sendPackingNote/{orderId}`, `PUT /order/sendInvoicePreview/{orderId}`
- **Nøkkelord:** ordrebekreftelse, pakkseddel, følgeseddel, folgeseddel, forhåndsvisning faktura, fakturautkast, sende ordrebekreftelse, proforma, order confirmation, packing note
- PDF: GET /order/orderConfirmation/{orderId}/pdf (includeAttachments) og GET /order/packingNote/{orderId}/pdf (type=ALL_ORDER_LINES|STOCK_ITEMS_ONLY). Sende på e-post: PUT /order/sendOrderConfirmation/{orderId}, PUT /order/sendPackingNote/{orderId} eller PUT /order/sendInvoicePreview/{orderId} med email, message, saveAsDefault (lagrer e-posten som standard på kunden). Sending går til kunden – krever bekreftelse.

### ✏️ Legge ved dokument på ordre/faktura
- **Kall:** `PUT /order/{id}/:attach`, `POST /documentArchive/customer/{id}`, `GET /documentArchive/customer/{id}`
- **Nøkkelord:** vedlegg, legge ved, vedlegg faktura, vedlegg ordre, timeliste vedlegg, attach, dokument til kunde, kundearkiv
- PUT /order/{id}/:attach som multipart/form-data med feltet file. addToInvoiceMode=NONE|NEXT|ALL (default NEXT = kun neste faktura; ALL for abonnement) og addToOrderMode=NONE|NEXT|ALL (default NONE) styrer om vedlegget følger faktura/ordrebekreftelse. Dokumenter som bare skal arkiveres på kunden: POST /documentArchive/customer/{id} (BETA), list med GET /documentArchive/customer/{id}.

### ✏️ Plukke/avplukke ordrelinjer (lager/logistikk)
- **Kall:** `PUT /order/orderline/{id}/:pickLine`, `PUT /order/orderline/{id}/:unpickLine`, `GET /order/orderline/{id}`
- **Nøkkelord:** plukke, plukk, plukkliste, avplukke, lagerplukk, levere vare, pick, unpick, lagerlokasjon
- PUT /order/orderline/{id}/:pickLine (valgfritt inventoryId, inventoryLocationId, pickDate – standardlager og dagens dato brukes ellers). Angre med PUT /order/orderline/{id}/:unpickLine. BETA og kun for kunder med Logistikk og aktivert disponibel beholdning – ellers feil/403.

### Se rabattavtaler for kunde eller produkt
- **Kall:** `GET /discountPolicy`, `GET /discountPolicy/{id}`, `GET /customer/{id}`
- **Nøkkelord:** rabatt, kunderabatt, rabattavtale, prisavtale, nettopris, varegrupperabatt, discount
- GET /discountPolicy?customerId=...(evt. productId, productGroupId, query, activeProducts) – BETA og kun Logistikk Basis/grossistintegrasjon. Felter: discountType (CUSTOMER_DISCOUNT|PRODUCT_DISCOUNT|PRODUCT_GROUP_DISCOUNT), percentage, fixedAmount, salesPriceWithDiscount. Generell kunderabatt ligger ellers i customer.discountPercentage (GET /customer/{id}?fields=discountPercentage) og rabatt per linje i orderLine.discount.

### Hente prosjektfakturadetaljer (honorar, timer, utlegg, a konto)
- **Kall:** `GET /invoice/details`, `GET /invoice/details/{id}`, `GET /project/{id}/period/invoiced`, `GET /invoice/{id}`
- **Nøkkelord:** prosjektfaktura, fakturadetaljer prosjekt, honorar, fakturerte timer, viderefakturering, utlegg, fakturert på prosjekt, a konto saldo
- GET /invoice/details krever invoiceDateFrom og invoiceDateTo (To eksklusiv); gir ProjectInvoiceDetails per prosjekt/faktura med feeAmount, markupAmount, amountOrderLinesAndReinvoicing, amountTravelReportsAndExpenses, onAccountBalanceAmount. Per faktura: GET /invoice/{id}?fields=projectInvoiceDetails(*). Fakturert per prosjekt og periode: GET /project/{id}/period/invoiced?dateFrom&dateTo.

### Omsetning/salg per kunde i en periode
- **Kall:** `GET /invoice`, `GET /ledger/posting`
- **Nøkkelord:** omsetning per kunde, salg per kunde, kundeomsetning, salgsrapport, topp kunder, største kunder, fakturert beløp, salgsstatistikk
- Enklest: GET /invoice?invoiceDateFrom&invoiceDateTo&fields=customer(id,name),amountExcludingVat,isCreditNote og summer amountExcludingVat per kunde lokalt (kreditnotaer har negative beløp). Reskontrobasert (inkl. MVA): GET /ledger/posting?dateFrom&dateTo&type=OUTGOING_INVOICE_CUSTOMER_POSTING&fields=amount,customer(id,name). Regnskapsmessig inntekt totalt: GET /ledger/posting?dateFrom&dateTo&accountNumberFrom=3000&accountNumberTo=3999&fields=amount (inntekt er negativ/kredit; kunde er ikke alltid satt på inntektsposteringene). Page med from/count (default 1000).

### Se CRM-prospekter / salgsmuligheter
- **Kall:** `GET /crm/prospect`, `GET /crm/prospect/{id}`
- **Nøkkelord:** prospekt, salgsmulighet, lead, crm, pipeline, potensielle kunder, tapt salg, konkurrent
- GET /crm/prospect med filtre name, description, customerId, salesEmployeeId, isClosed, closedReason, createdDateFrom/To, closedDateFrom/To, competitor, prospectType, projectId, projectOfferId. Detaljer: GET /crm/prospect/{id}. Endepunktene er DEPRECATED og kun lesing – ingen oppretting via API. GDPR: vis ikke navn på selgere (bruk initialer/«ansatt 1»).

### ✏️ Avskrive tap på kundefordring (konstatert tap)
- **Kall:** `GET /invoice`, `GET /invoice/paymentType`, `PUT /invoice/{id}/:payment`, `GET /ledger/account`, `POST /ledger/voucher`, `GET /ledger/posting/openPost`
- **Nøkkelord:** tap på fordringer, tap pa fordringer, konstatert tap, avskrive faktura, avskrive kundefordring, nedskrivning kundefordring, uerholdelig, 7830, bad debt, write off
- Ingen eget avskrivningsendepunkt. 1) Finn fakturaen og amountOutstanding (GET /invoice). 2a) Finnes det en betalingstype mot tapskonto (GET /invoice/paymentType?fields=id,description,debitAccount(number)), kan restbeløpet registreres med PUT /invoice/{id}/:payment (paymentDate, paymentTypeId, paidAmount) – fakturaen blir da utlignet. 2b) Ellers manuelt bilag: POST /ledger/voucher med postering debet tapskonto (f.eks. 7830, finn id via GET /ledger/account?number=7830) og kredit kundefordring 1500 med customer {id} (og evt. MVA-korreksjon for konstatert tap). Kontroller etterpå med GET /ledger/posting/openPost?customerId=...; manuelt bilag utligner ikke nødvendigvis fakturaen i fakturaoversikten. Skrivende – krever bekreftelse; vurder regnskapsmessig/MVA-behandling med ansvarlig regnskapsfører.

### ✏️ Tilbakebetale kreditnota/overbetaling til kunde (refusjon av tilgodehavende)
- **Kall:** `GET /invoice`, `GET /invoice/paymentType`, `PUT /invoice/{id}/:payment`, `POST /ledger/voucher`, `PUT /ledger/posting/:closePostings`
- **Nøkkelord:** tilbakebetale, tilbakebetaling, refusjon kunde, refundere, utbetale kreditnota, betale tilbake, tilgodehavende, overbetaling, kreditnota utbetaling, refund
- Skrivende – krever navngitt klient og bekreftelse. 1) Finn kreditnotaen/fakturaen: `GET /invoice`?invoiceDateFrom..&invoiceDateTo..&customerId=..&fields=id,invoiceNumber,amount,amountOutstanding,isCreditNote. 2) Betalingstype for bankkonto: `GET /invoice/paymentType`?fields=id,description,debitAccount(number). 3a) Kreditnota med negativt utestående: `PUT /invoice/{id}/:payment`?paymentDate=..&paymentTypeId=..&paidAmount=<negativt beløp> – verifiser etterpå med `GET /invoice/{id}` at amountOutstanding = 0. 3b) Overbetaling uten kreditnota: `POST /ledger/voucher` debet 1500 (customer satt) / kredit bankkonto, deretter `PUT /ledger/posting/:closePostings` for å lukke innbetalingen mot tilbakebetalingen. Selve bankoverføringen gjøres i nettbanken – API-et sender ikke penger. Ikke vis kundens kontonummer.

**Fallgruver:**
- Påkrevde datoperioder: GET /invoice og GET /invoice/details (invoiceDateFrom/invoiceDateTo), GET /order (orderDateFrom/orderDateTo), GET /reminder (dateFrom/dateTo), GET /ledger/posting (dateFrom/dateTo), GET /ledger/posting/openPost (date), GET /project/{id}/period/invoiced (dateFrom/dateTo). Til-datoen er EKSKLUSIV (januar = 2026-01-01 til 2026-02-01); format yyyy-MM-dd.
- sendToCustomer er default TRUE på POST /invoice, POST /invoice/list, PUT /order/{id}/:invoice, PUT /order/:invoiceMultipleOrders og PUT /invoice/{id}/:createCreditNote – sett sendToCustomer=false hvis fakturaen/kreditnotaen ikke skal sendes til kunden med en gang.
- Handlingsendepunkter med kolon (PUT /invoice/{id}/:send, :payment, :createCreditNote, :createReminder, PUT /order/{id}/:invoice, :approveSubscriptionInvoice, :attach, PUT /order/:invoiceMultipleOrders) tar parametere som query-parametere, ikke JSON-body (unntak: :attach er multipart med file).
- GET /invoice returnerer bare fakturerte (charged) utgående fakturaer – ikke ordre/fakturautkast. status=OUTSTANDING er ikke det samme som ubetalt (inkluderer kreditnotaer); bruk amountOutstanding > 0.
- Innbetaling: paymentTypeId må komme fra GET /invoice/paymentType (ikke /ledger/paymentTypeOut eller /travelExpense/paymentType). paidAmount er i valutaen til betalingstypens konto; paidAmountCurrency kreves for fakturaer i fremmed valuta. Ved forhåndsbetaling må både paymentTypeId og paidAmount angis.
- Kun én ordre per faktura via POST /invoice; flere ordre krever PUT /order/:invoiceMultipleOrders (BETA) og at ordrene har samme kunde, valuta, forfall, mottaker-e-post, attn og SMS-nummer.
- Faktura kan ikke opprettes før selskapet har registrert bankkontonummer (feilmelding om bankkonto) – sjekk i selskapsoppsettet.
- Purring: type og date er påkrevd; NETS_PRINT kun sammen med NOTICE_OF_DEBT_COLLECTION; SMS og NETS_PRINT må aktiveres i Tripletex først. includeCharge/includeInterest er default false (ingen gebyr/rente).
- Kreditnota via :createCreditNote nuller hele fakturaen. Hvis kundens sendemåte er e-post og creditNoteEmail er tom, blir kreditnotaen ikke sendt. Delkreditering gjøres med ny ordre (negative linjer) + PUT /order/{id}/:invoice?invoiceIdIfIsCreditNote=<id>.
- PUT /order/{id} med updateLinesAndGroups=true sletter ordrelinjer/grupper som ikke er med i listen. Fakturerte ordrelinjer kan ikke endres – krediter i stedet.
- PUT-endepunkter krever id og version i body; utdatert version gir konflikt (409) – hent objektet på nytt først.
- DELETE /customer/{id} er BETA og feiler normalt for kunder med transaksjoner – sett isInactive=true i stedet.
- BETA-endepunkter (customer/list, invoice/list, order/list, invoiceMultipleOrders, orderGroup POST/PUT, orderline PUT/DELETE, pickLine/unpickLine, orderLineTemplate, discountPolicy) kan endre seg. /crm/prospect er DEPRECATED og kun lesing.
- Moduler: discountPolicy krever Logistikk Basis/grossistintegrasjon; pickLine/unpickLine krever Logistikk med disponibel beholdning; eFaktura/AvtaleGiro/Vipps/SMS/Nets-print krever egne avtaler; EHF krever at mottaker har org.nr. og er i Peppol-registeret. 403 betyr som regel manglende modul/tilgang for brukeren/tokenet, ikke feil i kallet.
- Ingen POST for leveringsadresse eller fakturamerknad: deliveryAddress opprettes via kunde/ordre, invoiceRemark settes i body ved POST /invoice. invoiceRemarks (streng) og ehfSendStatus er utgått.
- PDF-endepunkter (/invoice/{invoiceId}/pdf, /reminder/{reminderId}/pdf, /order/orderConfirmation/{orderId}/pdf, /order/packingNote/{orderId}/pdf) returnerer binærdata – lagre som fil.
- Kundefordringer ligger på reskontrokonto 1500 (customer.ledgerAccount kan overstyre); bruk accountNumberFrom/To=1500–1599 med /ledger/posting og /ledger/posting/openPost for kundereskontro.
- GDPR: kunder med isPrivateIndividual=true og kontaktpersoner (/contact) er personopplysninger – bruk fields= minimalt (id,name) og vis ikke e-post, telefon eller adresse i svar.
- Alle skrivende kall (opprette/endre kunde, ordre, faktura, sende, kreditere, registrere betaling, purre) krever eksplisitt bekreftelse fra brukeren og angitt klient før de kjøres.
- Listeendepunkter har count=1000 som standard – page med from/count og sjekk fullResultSize i svaret ved store kunderegistre/fakturavolum.
- GET /customer har isInactive=false som standard: deaktiverte kunder skjules. Send isInactive=true for å finne dem (f.eks. ved duplikatsjekk før ny kunde).
- Invoice.amountOutstanding er utestående uten purregebyr; amountOutstandingTotal inkluderer siste purring og remitteringer. status=OUTSTANDING speiler «utestående»-gruppen i fakturaoversikten og tar med kreditnotaer.
- PUT /invoice/{id}/:payment: paidAmount er i valutaen til betalingstypens konto, mens paidAmount ved forhåndsbetaling på PUT /order/{id}/:invoice og POST /invoice er i fakturavaluta. Ikke bland de to.
- sendType-enum varierer: :send og PUT /order/{id}/:invoice tar EMAIL|EHF|AVTALEGIRO|EFAKTURA|VIPPS|PAPER|MANUAL; :createCreditNote har i tillegg DIRECT og AUTOINVOICE_*/PEPPOL_*-verdier. createReminder bruker dispatchType, ikke sendType.
- Order.status (NEW, PICKED, INVOICED …) brukes bare for Logistikk-kunder; bruk isClosed og om faktura finnes for å vurdere om en ordre er fakturert. createBackorder/createBackorders er pilot-/logistikkfunksjonalitet.
- GET /ledger/posting-parameteren openPostings er utgått – bruk GET /ledger/posting/openPost for åpne poster. orderLineIds/OrderLineIds som query-parameter på /order/orderGroup er også utgått – legg orderLines i body.

## Leverandører, leverandørfaktura, innkjøp, dokumentarkiv

### Finne en leverandør (på navn, org.nr. eller leverandørnummer)
- **Kall:** `GET /supplier`, `GET /supplierCustomer/search`, `GET /supplier/{id}`, `GET /customer/category`
- **Nøkkelord:** finn leverandør, søk leverandør, sok leverandor, leverandørliste, leverandørnummer, org.nr, organisasjonsnummer, supplier search, hvem er leverandøren, leverandørkategori
- GET /supplier har INGEN navnefilter: bruk GET /supplierCustomer/search?query=<navn>&fields=id,name (søker bare AKTIVE kunder og leverandører samlet) eller GET /supplier?organizationNumber=<9 siffer> / supplierNumber=<nr> (eksakt treff). Alternativt hent alle med GET /supplier?fields=id,name,supplierNumber,organizationNumber,isInactive (count er 1000 som standard – paginér med from) og filtrer lokalt; isInactive=true for inaktive. changedSince=<tidspunkt> gir bare endrede (synk). Filtrer på kategori med category1Id/category2Id/category3Id (id fra GET /customer/category). Detaljer: GET /supplier/{id}?fields=... med minimale felter. isCustomer=true betyr at leverandøren også er kunde. Er leverandøren en privatperson (isPrivateIndividual) er navn/adresse/konto personopplysninger – vis ikke.

### ✏️ Opprette ny leverandør (én eller mange)
- **Kall:** `GET /supplier`, `POST /supplier`, `POST /supplier/list`, `GET /customer/category`, `POST /customer/category`, `GET /ledger/account`
- **Nøkkelord:** ny leverandør, opprett leverandør, registrere leverandør, legge inn leverandør, importere leverandører, create supplier, leverandørkort
- 1) Sjekk duplikat: GET /supplier?organizationNumber=<orgnr>&fields=id,name. 2) POST /supplier med minst name; gjerne organizationNumber, email/invoiceEmail, postalAddress{addressLine1,postalCode,city,country{id}}, bankAccountPresentation[{bban|iban,bic}] (feltet bankAccounts er DEPRECATED), currency{id}, language NO|EN, category1{id}. supplierNumber tildeles automatisk om det utelates. ledgerAccount (reskontrokonto, normalt 2400) kan settes via GET /ledger/account?ledgerType=VENDOR. 3) Mange på én gang: POST /supplier/list med array. Kategorier deles med kunder: GET/POST /customer/category. Krever bekreftelse fra bruker.

### ✏️ Endre leverandøropplysninger (bankkonto, adresse, e-post, kategori, valuta)
- **Kall:** `GET /supplier/{id}`, `PUT /supplier/{id}`, `PUT /supplier/list`
- **Nøkkelord:** endre leverandør, oppdatere leverandør, ny bankkonto leverandør, kontonummer leverandør, adresse leverandør, faktura-epost, update supplier, iban, bic, swift
- Hent først GET /supplier/{id}?fields=id,version,<feltene som skal endres> for å få version. PUT /supplier/{id} med id, version og kun feltene som endres. Bankkonto settes i bankAccountPresentation (bban for norske, iban+bic for utenlandske). Flere samtidig: PUT /supplier/list. Kontonummer er sensitivt – vis aldri fullt kontonummer i svar (maskér). Krever bekreftelse.

### ✏️ Deaktivere eller slette leverandør
- **Kall:** `GET /supplier/{id}`, `PUT /supplier/{id}`, `DELETE /supplier/{id}`
- **Nøkkelord:** slette leverandør, deaktivere leverandør, inaktiv leverandør, arkivere leverandør, delete supplier, fjerne leverandør
- DELETE /supplier/{id} virker bare hvis leverandøren ikke har posteringer/bilag; ellers feiler kallet. Da: GET /supplier/{id}?fields=id,version og PUT /supplier/{id} med isInactive=true. Sletting er irreversibel – krever eksplisitt bekreftelse.

### Hente leverandørreskontro, saldo og åpne poster per leverandør
- **Kall:** `GET /ledger/posting/openPost`, `GET /ledger/openPost`, `GET /ledger/posting`, `GET /supplier`, `GET /ledger/account`
- **Nøkkelord:** leverandørreskontro, leverandorreskontro, reskontro, åpne poster, apne poster, leverandørgjeld, utestående leverandør, skyldig, saldo leverandør, kontoutskrift leverandør, aldersfordeling, forfalt, open post, hvor mye har vi kjøpt, innkjøpsvolum, 2400
- Åpne poster per dato: GET /ledger/posting/openPost?date=<dag ETTER skjæringsdato (eksklusiv, påkrevd)>&supplierId=<id> (uten supplierId = alle leverandører; bruk accountNumberFrom=2400&accountNumberTo=2499 for bare leverandørgjeld) og fields=id,date,supplier(id,name),invoiceNumber,termOfPayment,amount,amountCurrency,voucher(number). sorted=false gir raskere svar. Bevegelser/historikk: GET /ledger/posting?dateFrom=&dateTo=(begge påkrevd, dateTo eksklusiv)&supplierId=&fields=date,amount,invoiceNumber,voucher(number). Reskontrokonto: GET /ledger/account?ledgerType=VENDOR. Summer per leverandør lokalt og aldersfordel på termOfPayment (forfall). Leverandørnavn: GET /supplier?id=<liste>&fields=id,name.

### Liste leverandørfakturaer for en periode eller en leverandør
- **Kall:** `GET /supplierInvoice`, `GET /supplier`, `GET /ledger/posting`, `GET /ledger/voucher/>voucherReception`
- **Nøkkelord:** leverandørfakturaer, inngående fakturaer, liste fakturaer, fakturaer fra leverandør, supplier invoices, periode, måned, hente fakturaer, innkjøpsfakturaer
- GET /supplierInvoice krever invoiceDateFrom og invoiceDateTo (To er EKSKLUSIV – bruk dagen etter siste dato). Filtrer med supplierId, invoiceNumber, kid eller voucherId (alle eksakt). Nyttige fields=id,invoiceNumber,invoiceDate,invoiceDueDate,supplier(id,name),amount,amountCurrency,currency(code),outstandingAmount,isCreditNote,voucher(id,number,year). count er 1000 som standard – paginér med from/count. Bilag ført manuelt mot 2400 via /ledger/voucher kan mangle her; kontroller mot GET /ledger/posting?supplierId=&dateFrom=&dateTo= ved avstemming. Fakturaer som fortsatt ligger ubehandlet i bilagsmottaket finnes via GET /ledger/voucher/>voucherReception.

### Lage forfallsliste / betalingsforslag over ubetalte leverandørfakturaer
- **Kall:** `GET /supplierInvoice`, `GET /ledger/posting/openPost`, `GET /supplier`
- **Nøkkelord:** forfallsliste, betalingsforslag, ubetalte fakturaer, ubetalt, hva skal betales, forfaller denne uken, forfalte leverandørfakturaer, utestående leverandørgjeld, likviditet, betalingsliste, unpaid supplier invoices, due date
- 1) GET /supplierInvoice?invoiceDateFrom=<f.eks. 1 år tilbake>&invoiceDateTo=<i morgen>&fields=id,invoiceNumber,invoiceDueDate,supplier(id,name),amountCurrency,currency(code),outstandingAmount,kidOrReceiverReference,isCreditNote og behold rader med outstandingAmount ≠ 0 (outstandingAmount er i fakturavaluta). Sorter på invoiceDueDate og grupper i forfalt / forfaller innen X dager. 2) Kontroll mot hovedbok: GET /ledger/posting/openPost?date=<i morgen>&accountNumberFrom=2400&accountNumberTo=2499&fields=supplier(id,name),invoiceNumber,termOfPayment,amount. Kun lesing – selve betalingen registreres med :addPayment (egen oppgave, krever bekreftelse). Vis ikke kontonumre.

### Kontrollere om en leverandørfaktura allerede er registrert (duplikatsjekk på fakturanummer/KID)
- **Kall:** `GET /supplierInvoice`, `GET /ledger/voucher/>externalVoucherNumber`, `GET /ledger/posting`
- **Nøkkelord:** dobbelfaktura, duplikat, dobbeltregistrert, allerede bokført, fakturanummer, kid, sjekk faktura, betalt to ganger, duplicate invoice
- GET /supplierInvoice?invoiceNumber=<nr>&supplierId=<id>&invoiceDateFrom=<bredt, f.eks. 2 år tilbake>&invoiceDateTo=<i morgen>&fields=id,invoiceNumber,invoiceDate,amount,voucher(number,year). Alternativt kid=<KID>. For importerte bilag: GET /ledger/voucher/>externalVoucherNumber?externalVoucherNumber=. Sjekk evt. også GET /ledger/posting?supplierId=&dateFrom=&dateTo= og se etter samme beløp/invoiceNumber.

### Hente detaljer for én leverandørfaktura (kontering, betalinger, attesteringsstatus, utestående)
- **Kall:** `GET /supplierInvoice/{id}`, `GET /ledger/voucher/{id}`, `GET /voucherApprovalListElement/{id}`
- **Nøkkelord:** vis leverandørfaktura, fakturadetaljer, kontering, hvem har attestert, attesteringsstatus, betalt, utestående beløp, restbeløp, supplier invoice detail
- GET /supplierInvoice/{id}?fields=id,invoiceNumber,invoiceDate,invoiceDueDate,kidOrReceiverReference,amount,amountExcludingVat,currency(code),outstandingAmount,isCreditNote,supplier(id,name),voucher(id,number,year),payments(date,amount),approvalListElements(status,organisationLevel,actionDate),originalInvoiceDocumentId. Konteringslinjer (konto, mva, prosjekt, avdeling): GET /ledger/voucher/{voucher.id}?fields=postings(id,row,account(number,name),vatType(number),amountGross,project(id),department(id)). approvalListElements inneholder ansatte – vis ikke navn, bruk «attestant 1/2». Enkeltsteg i attesteringsflyten: GET /voucherApprovalListElement/{id}?fields=status,organisationLevel,actionDate,comment.

### Laste ned PDF / originalfil av en leverandørfaktura
- **Kall:** `GET /supplierInvoice/{invoiceId}/pdf`, `GET /supplierInvoice/{id}`, `GET /document/{id}`, `GET /document/{id}/content`, `GET /ledger/voucher/{voucherId}/pdf`
- **Nøkkelord:** pdf leverandørfaktura, last ned faktura, originalfaktura, fakturabilde, vedlegg faktura, ehf pdf, download invoice, se faktura
- Enklest: GET /supplierInvoice/{invoiceId}/pdf (binær PDF – lagre til fil, ikke skriv ut). Originaldokument (f.eks. EHF/XML eller skannet fil): hent originalInvoiceDocumentId fra GET /supplierInvoice/{id}, deretter GET /document/{id} (metadata: fileName, mimeType) og GET /document/{id}/content?download=true (BETA). Hele bilaget som PDF: GET /ledger/voucher/{voucherId}/pdf.

### Se leverandørfakturaer som venter på attestering/godkjenning
- **Kall:** `GET /supplierInvoice/forApproval`
- **Nøkkelord:** til attestering, til godkjenning, venter på godkjenning, attesteringskø, ikke attestert, for approval, godkjenningsliste, mine fakturaer til attestering
- GET /supplierInvoice/forApproval?showAll=true&fields=id,invoiceNumber,invoiceDate,invoiceDueDate,supplier(name),amount,currency(code),approvalListElements(status,organisationLevel). Uten showAll vises bare fakturaer der innlogget bruker (API-brukeren) er attestant; employeeId kan settes for en bestemt attestant (bruk kun id). searchText søker i avdeling, prosjekt m.m. Sorter på forfall for å prioritere.

### ✏️ Attestere/godkjenne leverandørfaktura (én eller flere)
- **Kall:** `PUT /supplierInvoice/{invoiceId}/:approve`, `PUT /supplierInvoice/:approve`, `GET /supplierInvoice/forApproval`
- **Nøkkelord:** attestere, godkjenne, godkjenn faktura, attestering, approve invoice, godkjenne leverandørfaktura, overstyre attestering
- Finn id via GET /supplierInvoice/forApproval. Én faktura: PUT /supplierInvoice/{invoiceId}/:approve?comment=<valgfri>. Flere: PUT /supplierInvoice/:approve?invoiceIds=1,2,3. overrideApprovalFlow=true fullfører hele attesteringsflyten uten resterende nivåer og krever rollen firma-attestant. Godkjenning skjer som API-brukeren – krever eksplisitt bekreftelse fra bruker før kall.

### ✏️ Avvise leverandørfaktura
- **Kall:** `PUT /supplierInvoice/{invoiceId}/:reject`, `PUT /supplierInvoice/:reject`
- **Nøkkelord:** avvise faktura, avvis, reject, underkjenne, returnere faktura, feil faktura, ikke godkjent
- PUT /supplierInvoice/{invoiceId}/:reject?comment=<begrunnelse> – comment er PÅKREVD. Flere: PUT /supplierInvoice/:reject?comment=...&invoiceIds=1,2. Krever bekreftelse.

### ✏️ Sende leverandørfaktura til attestant (legge til mottaker i godkjenningsflyt)
- **Kall:** `PUT /supplierInvoice/{invoiceId}/:addRecipient`, `PUT /supplierInvoice/:addRecipient`, `GET /employee`
- **Nøkkelord:** send til attestant, videresende faktura, legg til mottaker, tildele attestant, add recipient, fordele faktura, sende til godkjenning
- Finn ansatt-id: GET /employee?fields=id (filtrer f.eks. på e-post/nummer som brukeren oppgir; hent minst mulig – GDPR, vis ikke navn i svar). Deretter PUT /supplierInvoice/{invoiceId}/:addRecipient?employeeId=<id>&comment=<valgfri>, eller for flere fakturaer PUT /supplierInvoice/:addRecipient?employeeId=&invoiceIds=1,2. Krever bekreftelse.

### ✏️ Endre kontering (konto/mva) på leverandørfaktura og bokføre den
- **Kall:** `PUT /supplierInvoice/voucher/{id}/postings`, `GET /supplierInvoice/{id}`, `GET /ledger/account`, `GET /ledger/vatType`
- **Nøkkelord:** endre kontering, kontere faktura, feil konto, endre mva-kode, konteringslinjer, bokføre leverandørfaktura, debetposteringer, kostnadskonto, fordele kostnad
- BETA. {id} er BILAGS-id (voucher.id), ikke faktura-id – hent den med GET /supplierInvoice/{id}?fields=voucher(id),orderLines. Gyldige kostnadskontoer: GET /ledger/account?isApplicableForSupplierInvoice=true&fields=id,number,name. Inngående mva-koder: GET /ledger/vatType?typeOfVat=INCOMING_INVOICE (eller INCOMING)&vatDate=<fakturadato>&fields=id,number,name. Body er en JSON-ARRAY av OrderLinePosting [{posting:{account{id},vatType{id},amountGross,project{id},department{id}}, orderLine}] – kun debetlinjene. voucherDate endrer bilags- og fakturadato. sendToLedger=true (bokfør) krever oppsett fra Tripletex. Krever bekreftelse.

### ✏️ Endre prosjekt, avdeling eller fri dimensjon på leverandørfaktura
- **Kall:** `PUT /supplierInvoice/{invoiceId}/:changeDimension`, `GET /ledger/voucher/{id}`, `GET /project`, `GET /department`, `GET /ledger/accountingDimensionValue/search`
- **Nøkkelord:** endre prosjekt, endre avdeling, dimensjon, fri dimensjon, kostnadssted, prosjektkostnad, fordele på prosjekt, change dimension
- 1) Finn debetposteringene: GET /ledger/voucher/{voucher.id}?fields=postings(id,row,account(number),amountGross) – bruk bare kostnadslinjene (ikke 2400-linjen). 2) Finn dimensjons-id: GET /project?fields=id,number,name, GET /department?fields=id,name, eller GET /ledger/accountingDimensionValue/search for fri dimensjon. 3) PUT /supplierInvoice/{invoiceId}/:changeDimension?debitPostingIds=<id1,id2>&dimension=PROJECT|DEPARTMENT|EMPLOYEE|PRODUCT|FREE_DIMENSION_1|FREE_DIMENSION_2|FREE_DIMENSION_3&dimensionId=<id>. Alle fire parametere er påkrevd. Krever bekreftelse.

### ✏️ Registrere betaling av leverandørfaktura
- **Kall:** `POST /supplierInvoice/{invoiceId}/:addPayment`, `GET /ledger/paymentTypeOut`, `GET /supplierInvoice/{id}`
- **Nøkkelord:** betale leverandør, registrere betaling, betalt faktura, utbetaling, delbetaling, nettbank, autopay, remittering, add payment, betalingstype
- Merk: dette er POST selv om stien har ':'. Krever oppsett fra Tripletex. Hent betalingstyper: GET /ledger/paymentTypeOut?fields=id,description (BETA). POST /supplierInvoice/{invoiceId}/:addPayment?paymentType=<id> (påkrevd; 0 = sist brukte for leverandøren) eller useDefaultPaymentType=true, samt amount, paymentDate (yyyy-MM-dd), kidOrReceiverReference, bban. partialPayment=true for å tillate flere delbetalinger. Sjekk outstandingAmount etterpå med GET /supplierInvoice/{id}. Kontonummer (bban) skal ikke vises i svar. Dette kan utløse faktisk betaling via bankintegrasjon – krever eksplisitt bekreftelse.

### ✏️ Registrere leverandørfaktura manuelt som bilag (uten EHF)
- **Kall:** `GET /ledger/voucherType`, `GET /supplier`, `GET /ledger/account`, `GET /ledger/vatType`, `POST /ledger/voucher`, `POST /ledger/voucher/{voucherId}/attachment`
- **Nøkkelord:** føre leverandørfaktura, fore leverandorfaktura, bokføre inngående faktura, registrere faktura manuelt, leverandørbilag, kostnadsbilag, manuell kontering, bilag leverandør, postering 2400
- 1) Bilagstype: GET /ledger/voucherType?name=Leverandørfaktura&fields=id,name. 2) Leverandør-id (GET /supplier), kontoer (GET /ledger/account?number=2400,6800&fields=id,number) og inngående mva-kode (GET /ledger/vatType?typeOfVat=INCOMING_INVOICE eller INCOMING). 3) POST /ledger/voucher med date, description, voucherType{id}, vendorInvoiceNumber og postings (row fra 1): kreditlinje konto 2400 med supplier{id}, amountGross negativ (brutto), invoiceNumber, termOfPayment (forfallsdato); debetlinje kostnadskonto med vatType{id} og amountGross positiv (brutto – mva-linjen beregnes). Summen må bli 0, avrund til 2 desimaler. sendToLedger er true som standard og krever rettigheten «Avansert bilag»; sendToLedger=false lagrer uten å bokføre. Utenlandsk valuta: amountGrossCurrency + currency{id}, evt. convertFromAmountGrossCurrency=true. 4) Legg ved faktura: POST /ledger/voucher/{voucherId}/attachment (multipart, felt 'file'). Krever bekreftelse.

### ✏️ Laste opp faktura/kvittering til bilagsmottaket for tolkning
- **Kall:** `POST /ledger/voucher/importDocument`, `GET /voucherInbox/emailAddress`, `GET /voucherInbox/inboxCount`, `POST /documentArchive/reception`
- **Nøkkelord:** bilagsmottak, innboks, inbox, laste opp bilag, skanne faktura, tolke faktura, importere dokument, kvittering, send bilag på e-post, bilagsadresse, import document
- POST /ledger/voucher/importDocument som multipart/form-data med 'file' (PDF, PNG, JPEG, TIFF; EHF/XML bare etter avtale med Tripletex) og valgfri 'description'; split=true lager ett bilag per side. Bilaget havner i bilagsmottaket for tolkning/kontering. Alternativ: GET /voucherInbox/emailAddress gir klientens e-postadresse for bilag. GET /voucherInbox/inboxCount viser antall i innboksen. Rene arkivfiler (ikke bilag): POST /documentArchive/reception (BETA). Krever bekreftelse.

### Se hva som ligger i bilagsmottaket / ikke bokførte bilag
- **Kall:** `GET /ledger/voucher/>voucherReception`, `GET /ledger/voucher/>nonPosted`, `GET /voucherInbox/inboxCount`
- **Nøkkelord:** bilagsmottak, innboks, ubehandlede bilag, ikke bokført, ikke postert, ventende bilag, voucher reception, non posted, hvor mange bilag i innboksen, uposterte
- Antall: GET /voucherInbox/inboxCount. Innhold: GET /ledger/voucher/>voucherReception?dateFrom=&dateTo=(eksklusiv)&searchText=&fields=id,date,description,vendorInvoiceNumber,supplierVoucherType. Ikke-bokførte (registrerte men ikke sendt til hovedbok): GET /ledger/voucher/>nonPosted?includeNonApproved=true (påkrevd param)&dateFrom=&dateTo=.

### ✏️ Sende leverandørbilag tilbake til bilagsmottaket eller reversere feilført leverandørfaktura
- **Kall:** `PUT /ledger/voucher/{id}/:sendToInbox`, `PUT /ledger/voucher/{id}/:reverse`, `GET /ledger/voucher/{id}`
- **Nøkkelord:** tilbake til innboks, send to inbox, angre bokføring, reversere, tilbakeføre, feilført, motbilag, reverse voucher, korrigere leverandørfaktura
- Hent version: GET /ledger/voucher/{id}?fields=id,version,number,date. Tilbake til bilagsmottak for ny kontering: PUT /ledger/voucher/{id}/:sendToInbox?version=<v>&comment=<årsak>. Allerede bokført i låst/rapportert periode: PUT /ledger/voucher/{id}/:reverse?date=<reverseringsdato> (påkrevd) – lager motbilag. Ekte kreditnota fra leverandør registreres som egen leverandørfaktura (isCreditNote). Krever bekreftelse.

### ✏️ Laste opp dokument til dokumentarkivet (leverandør, kunde, prosjekt, produkt, konto, anleggsmiddel, ansatt)
- **Kall:** `POST /documentArchive/supplier/{id}`, `POST /documentArchive/customer/{id}`, `POST /documentArchive/project/{id}`, `POST /documentArchive/product/{id}`, `POST /documentArchive/account/{id}`, `POST /documentArchive/asset/{id}`, `POST /documentArchive/employee/{id}`, `POST /documentArchive/reception`
- **Nøkkelord:** arkivere dokument, laste opp avtale, kontrakt leverandør, dokumentarkiv, arkiv, vedlegg på leverandør, dokumentasjon konto, avstemmingsdokumentasjon, upload document archive
- BETA. Finn id til objektet (GET /supplier, /customer, /project, /product, /ledger/account, /asset). POST /documentArchive/<objekttype>/{id} som multipart/form-data med feltet 'file'. Kontodokumentasjon (f.eks. avstemmingsbilag til årsoppgjør): /documentArchive/account/{kontoens id, ikke kontonummer}. Uten tilknytning: POST /documentArchive/reception. Ansattarkiv inneholder personopplysninger – bruk kun når nødvendig. Krever bekreftelse.

### Hente/liste dokumenter fra dokumentarkivet
- **Kall:** `GET /documentArchive/supplier/{id}`, `GET /documentArchive/customer/{id}`, `GET /documentArchive/project/{id}`, `GET /documentArchive/product/{id}`, `GET /documentArchive/account/{id}`, `GET /documentArchive/asset/{id}`, `GET /documentArchive/employee/{id}`, `GET /document/{id}`, `GET /document/{id}/content`
- **Nøkkelord:** hent arkiv, dokumenter på leverandør, arkiverte dokumenter, finn avtale, dokumentarkiv liste, last ned arkivdokument, dokumentasjon konto
- BETA. GET /documentArchive/<objekttype>/{id}?periodDateFrom=&periodDateTo=(eksklusiv)&fields=id,fileName,mimeType,archiveDate,size. Last ned fil: GET /document/{id}/content?download=true med arkivdokumentets id (verifiser med GET /document/{id} at fileName stemmer) og lagre til fil – ikke skriv binærinnhold ut. Ansattdokumenter: kun ved behov, ikke vis filnavn med personopplysninger.

### ✏️ Endre eller slette et arkivdokument
- **Kall:** `PUT /documentArchive/{id}`, `DELETE /documentArchive/{id}`
- **Nøkkelord:** gi nytt navn dokument, endre arkivdato, slette dokument, fjerne vedlegg arkiv, rydde arkiv, update document archive, delete document
- BETA. PUT /documentArchive/{id} med id, version og fileName/archiveDate/mimeType som skal endres. DELETE /documentArchive/{id} sletter permanent – krever eksplisitt bekreftelse.

### ✏️ Laste opp og hente dokumentasjon på kontrollskjema (f.eks. årsoppgjørskontroller)
- **Kall:** `GET /documentArchive/dynamicControlForm/{id}`, `POST /documentArchive/dynamicControlForm/{id}`, `POST /documentArchive/dynamicControlForm/{id}/list`
- **Nøkkelord:** kontrollskjema, control form, årsoppgjør, arsoppgjor, dokumentasjon kontroll, revisjon, vedlegg kontrollskjema, dynamic control form
- BETA. {id} er kontrollskjemaets id (finnes via årsoppgjørs-/kontrollskjemaendepunktene i gruppen arsoppgjor). Liste: GET /documentArchive/dynamicControlForm/{id}?periodDateFrom=&periodDateTo=. Én fil: POST .../{id} (multipart 'file'); flere filer: POST .../{id}/list (multipart). Opplasting krever bekreftelse.

### Finne innkjøpsordrer (åpne, per leverandør, prosjekt eller med avvik)
- **Kall:** `GET /purchaseOrder`, `GET /purchaseOrder/{id}`, `GET /purchaseOrder/orderline/{id}`
- **Nøkkelord:** innkjøpsordrer, liste innkjøp, åpne bestillinger, ikke mottatt, bestillinger leverandør, purchase orders, po status, innkjøp prosjekt, ordre med avvik
- Krever Logistikk Basic. GET /purchaseOrder?supplierId=&projectId=&number=&isClosed=false&withDeviationOnly=true|false&creationDateFrom=&creationDateTo=&deliveryDateFrom=&deliveryDateTo=(alle datoer INKLUSIVE)&fields=id,number,status,supplier(name),deliveryDate,creationDate,isClosed. Det finnes INGEN status-parameter – filtrer status lokalt. Status-enum: STATUS_OPEN, STATUS_SENT, STATUS_RECEIVING, STATUS_CONFIRMED, STATUS_CONFIRMED_DEVIATION_DETECTED, STATUS_DEVIATION_OPEN, STATUS_DEVIATION_CONFIRMED, STATUS_CLOSED, STATUS_CANCELLED. Linjer: GET /purchaseOrder/{id}?fields=orderLines(id,product(number,name),count,quantityReceived,unitCostCurrency,amountExcludingVatCurrency) eller GET /purchaseOrder/orderline/{id}.

### Finne leverandørens produkter og innkjøpspriser
- **Kall:** `GET /product/supplierProduct`, `GET /supplier`, `GET /product`
- **Nøkkelord:** leverandørprodukt, leverandorprodukt, innkjøpspris, innkjopspris, prisliste leverandør, varenummer leverandør, supplier product, kostpris, hva koster varen hos leverandøren
- GET /product/supplierProduct?vendorId=<leverandør-id>&query=<tekst>&isInactive=false&fields=id,number,name,costExcludingVatCurrency,currency(code),resaleProduct(id,number,name),isMainSupplierProduct. For ett eget produkt: productId=<id>. targetCurrencyId=<id> konverterer prisen. Leverandør-id fra GET /supplier, eget produkt fra GET /product?fields=id,number,name.

### ✏️ Opprette innkjøpsordre med varelinjer
- **Kall:** `GET /supplier`, `GET /product`, `GET /product/supplierProduct`, `POST /purchaseOrder`, `POST /purchaseOrder/orderline`, `POST /purchaseOrder/orderline/list`
- **Nøkkelord:** ny innkjøpsordre, opprette bestilling, bestille fra leverandør, lage po, create purchase order, innkjøp, legge til linjer, leverandørprodukt, innkjøpspris
- Krever Logistikk Basic. 1) Leverandør-id (GET /supplier) og produkter (GET /product?fields=id,number,name eller leverandørens produkter GET /product/supplierProduct?vendorId=<id>). 2) POST /purchaseOrder med supplier{id}, deliveryDate, ourContact{id}, evt. project{id}, department{id}, deliveryAddress, currency, comments. orderLines er read-only på ordren. 3) POST /purchaseOrder/orderline/list med [{purchaseOrder{id}, product{id}, count, unitCostCurrency, discount}] (eller én og én med POST /purchaseOrder/orderline). Pris hentes fra produktets innkjøpspris hvis utelatt. Krever bekreftelse.

### ✏️ Endre, lukke eller slette innkjøpsordre og ordrelinjer, og legge ved filer
- **Kall:** `GET /purchaseOrder/{id}`, `PUT /purchaseOrder/{id}`, `DELETE /purchaseOrder/{id}`, `GET /purchaseOrder/orderline/{id}`, `PUT /purchaseOrder/orderline/{id}`, `PUT /purchaseOrder/orderline/list`, `DELETE /purchaseOrder/orderline/{id}`, `DELETE /purchaseOrder/orderline/list`, `POST /purchaseOrder/{id}/attachment`, `POST /purchaseOrder/{id}/attachment/list`, `DELETE /purchaseOrder/{id}/attachment`
- **Nøkkelord:** endre innkjøpsordre, endre antall, slette innkjøpsordre, kansellere bestilling, lukke ordre, slette linje, vedlegg innkjøpsordre, update purchase order, tilbud leverandør vedlegg
- Krever Logistikk Basic. Hent version først (GET /purchaseOrder/{id}?fields=id,version,status). Ordrehode: PUT /purchaseOrder/{id} (f.eks. deliveryDate, isClosed=true for å lukke). Linjer: PUT /purchaseOrder/orderline/{id} eller /list (count, unitCostCurrency, discount); slett med DELETE /purchaseOrder/orderline/{id} eller DELETE /purchaseOrder/orderline/list (body med linjer). Vedlegg: POST /purchaseOrder/{id}/attachment (multipart 'file') eller /attachment/list; DELETE /purchaseOrder/{id}/attachment fjerner. DELETE /purchaseOrder/{id} sletter hele ordren. Alle krever bekreftelse.

### ✏️ Sende innkjøpsordre til leverandør
- **Kall:** `PUT /purchaseOrder/{id}/:send`, `PUT /purchaseOrder/{id}/:sendByEmail`
- **Nøkkelord:** sende innkjøpsordre, send bestilling, e-post leverandør, send po, ftp, edi, send purchase order, bestillingsbekreftelse
- Krever Logistikk Basic. Standard: PUT /purchaseOrder/{id}/:send?sendType=DEFAULT|EMAIL|FTP (valgfri) – e-post går til receiverEmail på ordren, ellers leverandørens e-post. Tilpasset e-post: PUT /purchaseOrder/{id}/:sendByEmail med body {email, subject, message}. Sjekk lastSentTimestamp/status (STATUS_SENT) etterpå. Sender ekstern melding – krever eksplisitt bekreftelse.

### ✏️ Registrere varemottak på en innkjøpsordre
- **Kall:** `PUT /purchaseOrder/goodsReceipt/{id}/:registerGoodsReceipt`, `GET /purchaseOrder/goodsReceiptLine`, `PUT /purchaseOrder/goodsReceiptLine/{id}`, `PUT /purchaseOrder/goodsReceiptLine/list`, `POST /purchaseOrder/goodsReceiptLine`, `POST /purchaseOrder/goodsReceiptLine/list`, `PUT /purchaseOrder/goodsReceipt/{id}/:confirm`, `PUT /purchaseOrder/goodsReceipt/{id}/:receiveAndConfirm`, `GET /inventory`
- **Nøkkelord:** varemottak, motta varer, registrere mottak, bekrefte varemottak, varer mottatt, delleveranse, restordre, goods receipt, lagerføre, inn på lager
- Krever Logistikk Basic. {id} i disse action-kallene er INNKJØPSORDRENS id. Alt mottatt: PUT /purchaseOrder/goodsReceipt/{poId}/:receiveAndConfirm?receivedDate=yyyy-MM-dd (påkrevd)&inventoryId=<lager, standard hovedlager fra GET /inventory>. Delmottak: 1) PUT /purchaseOrder/goodsReceipt/{poId}/:registerGoodsReceipt?registrationDate= (påkrevd; setter mottatt = bestilt), 2) GET /purchaseOrder/goodsReceiptLine?purchaseOrderId=<poId> og juster quantityReceived med PUT /purchaseOrder/goodsReceiptLine/{id} eller /list, 3) PUT /purchaseOrder/goodsReceipt/{poId}/:confirm?createRestOrder=true for restordre på manko. Nytt produkt som ikke var bestilt: POST /purchaseOrder/goodsReceiptLine(/list). Krever bekreftelse.

### ✏️ Registrere varemottak uten innkjøpsordre
- **Kall:** `POST /purchaseOrder/goodsReceipt`, `POST /purchaseOrder/goodsReceipt/list`, `GET /inventory`, `GET /product`
- **Nøkkelord:** varemottak uten ordre, mottak uten bestilling, direkte varemottak, lagerinngang, goods receipt without purchase order
- Krever Logistikk Basic. POST /purchaseOrder/goodsReceipt med registrationDate, comment og goodsReceiptLines [{product{id}, quantityReceived, inventory{id}, inventoryLocation{id}}]. Flere mottak: POST /purchaseOrder/goodsReceipt/list (bedre ytelse). Produkt-/lager-id fra GET /product og GET /inventory. Krever bekreftelse.

### Hente oversikt over varemottak og mottatte antall
- **Kall:** `GET /purchaseOrder/goodsReceipt`, `GET /purchaseOrder/goodsReceipt/{id}`, `GET /purchaseOrder/goodsReceiptLine`, `GET /purchaseOrder/goodsReceiptLine/{id}`
- **Nøkkelord:** liste varemottak, åpne varemottak, ubekreftede mottak, hva er mottatt, mottatt antall, restantall, goods receipts, varemottak periode
- Krever Logistikk Basic. GET /purchaseOrder/goodsReceipt?receivedDateFrom=&receivedDateTo=(begge inkl.)&status=STATUS_OPEN|STATUS_CONFIRMED&withoutPurchase=true|false&fields=id,registrationDate,status,purchaseOrder(number),comment. For én ordre: GET /purchaseOrder/goodsReceipt/{poId} (id = innkjøpsordre-id). Linjer: GET /purchaseOrder/goodsReceiptLine?purchaseOrderId=<poId>&fields=id,product(number,name),quantityOrdered,quantityReceived,quantityRest,deviation. receivedBy er en ansatt – ikke vis navn.

### ✏️ Korrigere eller slette varemottak og varemottakslinjer
- **Kall:** `PUT /purchaseOrder/goodsReceipt/{id}`, `DELETE /purchaseOrder/goodsReceipt/{id}`, `DELETE /purchaseOrder/goodsReceipt/list`, `PUT /purchaseOrder/goodsReceiptLine/{id}`, `DELETE /purchaseOrder/goodsReceiptLine/{id}`, `DELETE /purchaseOrder/goodsReceiptLine/list`
- **Nøkkelord:** angre varemottak, slette varemottak, korrigere mottak, feil antall mottatt, endre varemottak, delete goods receipt
- Krever Logistikk Basic. PUT /purchaseOrder/goodsReceipt/{id} (her er id VAREMOTTAKETS id) for dato/kommentar/linjer. Slett: DELETE /purchaseOrder/goodsReceipt/{id} eller DELETE /purchaseOrder/goodsReceipt/list?ids=1,2. Linjer: PUT/DELETE /purchaseOrder/goodsReceiptLine/{id}, DELETE /purchaseOrder/goodsReceiptLine/list (body). Bekreftede mottak har påvirket lager – sjekk status først. Krever bekreftelse.

### ✏️ Registrere og behandle avvik ved varemottak (for få, for mange, skadet, retur, restordre)
- **Kall:** `POST /purchaseOrder/deviation`, `POST /purchaseOrder/deviation/list`, `GET /purchaseOrder/deviation`, `GET /purchaseOrder/deviation/{id}`, `PUT /purchaseOrder/deviation/{id}`, `PUT /purchaseOrder/deviation/list`, `DELETE /purchaseOrder/deviation/{id}`, `PUT /purchaseOrder/deviation/{id}/:deliver`, `PUT /purchaseOrder/deviation/{id}/:approve`, `PUT /purchaseOrder/deviation/{id}/:undeliver`
- **Nøkkelord:** avvik, avviksregistrering, manko, for få varer, for mange varer, skadet, defekt, retur til leverandør, restordre, reklamasjon, godkjenne avvik, deviation
- Krever Logistikk Basic. 1) Registrer: POST /purchaseOrder/deviation (eller /list) med purchaseOrderLine{id}, date, cause=CAUSE_DEFECT|CAUSE_TOO_FEW|CAUSE_TOO_MANY|CAUSE_REPLACEMENT, action=ACTION_IGNORE|ACTION_GENERATE_RESTORDER|ACTION_RETURN|ACTION_RETURN_GENERATE_RESTORDER, comment. 2) Send til godkjenning: PUT /purchaseOrder/deviation/{poId}/:deliver. 3) Godkjenn: PUT /purchaseOrder/deviation/{poId}/:approve (tilbake: :undeliver). Action-kallene tar INNKJØPSORDRE-id; GET /purchaseOrder/deviation/{id} tar ORDRELINJE-id; liste: GET /purchaseOrder/deviation?purchaseOrderId= (påkrevd). Endre: PUT /purchaseOrder/deviation/{id} eller /list. Krever bekreftelse.

### ✏️ Koble innkjøpsordre til leverandørfaktura (bilag)
- **Kall:** `POST /purchaseOrder/purchaseOrderIncomingInvoiceRelation`, `POST /purchaseOrder/purchaseOrderIncomingInvoiceRelation/list`, `GET /purchaseOrder/purchaseOrderIncomingInvoiceRelation/{id}`, `PUT /purchaseOrder/purchaseOrderIncomingInvoiceRelation/{id}`, `DELETE /purchaseOrder/purchaseOrderIncomingInvoiceRelation/{id}`, `DELETE /purchaseOrder/purchaseOrderIncomingInvoiceRelation/list`, `GET /supplierInvoice`
- **Nøkkelord:** koble faktura til ordre, matche faktura, innkjøpsordre faktura, fakturamatch, knytte bilag, link purchase order invoice, fakturakontroll
- Krever Logistikk Basic. Finn bilags-id for fakturaen (GET /supplierInvoice?...&fields=id,voucher(id)). POST /purchaseOrder/purchaseOrderIncomingInvoiceRelation med orderOut{id=innkjøpsordre}, voucher{id=bilag}, registerGoodsReceipt=true hvis varemottak skal registreres samtidig. Flere: /list. Endre/fjerne: PUT/DELETE .../{id}, DELETE .../list?ids=. Krever bekreftelse.

### Kontrollere innkjøpsordre mot varemottak og faktura (treveis matching)
- **Kall:** `GET /purchaseOrder/purchaseOrderIncomingInvoiceRelation`, `GET /purchaseOrder/{id}`, `GET /purchaseOrder/goodsReceiptLine`, `GET /supplierInvoice`, `GET /ledger/voucher/{id}`
- **Nøkkelord:** treveis matching, 3-veis match, kontroll faktura mot ordre, fakturert vs bestilt, mottatt vs fakturert, avstemme innkjøp, hvilken faktura hører til ordren, three way match
- Krever Logistikk Basic. 1) Relasjoner: GET /purchaseOrder/purchaseOrderIncomingInvoiceRelation?orderOutId=<poId> (eller voucherId=<bilag>)&fields=id,orderOut(id,number),voucher(id,number). 2) Bestilt: GET /purchaseOrder/{id}?fields=orderLines(product(number),count,unitCostCurrency,amountExcludingVatCurrency). 3) Mottatt: GET /purchaseOrder/goodsReceiptLine?purchaseOrderId=. 4) Fakturert: GET /supplierInvoice?voucherId=<id>&invoiceDateFrom=&invoiceDateTo= eller GET /ledger/voucher/{id}?fields=postings(...). Sammenlign antall og beløp lokalt.

**Fallgruver:**
- GET /supplierInvoice krever invoiceDateFrom OG invoiceDateTo; invoiceDateTo er EKSKLUSIV (bruk dagen etter siste dato). Samme for dateTo på /ledger/posting og date på /ledger/posting/openPost og /ledger/openPost.
- Datofiltrene på /purchaseOrder (creationDate/deliveryDate) og /purchaseOrder/goodsReceipt (receivedDate) er INKLUSIVE – ulikt resten av API-et.
- GET /supplier har ikke navnefilter. Bruk GET /supplierCustomer/search?query=<navn>, organizationNumber= (eksakt) eller hent alle med fields=id,name og filtrer lokalt.
- POST /supplierInvoice/{invoiceId}/:addPayment er POST (ikke PUT) til tross for ':'-stien, krever oppsett fra Tripletex og paymentType er påkrevd (0 = sist brukte for leverandøren). Kan utløse ekte bankbetaling.
- PUT /supplierInvoice/voucher/{id}/postings er BETA og tar BILAGS-id (voucher.id), ikke faktura-id; sendToLedger=true krever oppsett fra Tripletex.
- Attestering: overrideApprovalFlow=true krever rollen firma-attestant; :reject krever comment. /supplierInvoice/forApproval viser bare API-brukerens egne uten showAll=true.
- :changeDimension krever alle fire: debitPostingIds (kommaseparert, kun kostnadslinjer), dimension (PROJECT|DEPARTMENT|EMPLOYEE|PRODUCT|FREE_DIMENSION_1-3) og dimensionId.
- Alle /purchaseOrder/*-endepunkter krever modulen Logistikk Basic – 403/422 betyr normalt at modulen mangler hos klienten.
- Forvirrende id-er i varemottak/avvik: :registerGoodsReceipt, :confirm, :receiveAndConfirm, GET /purchaseOrder/goodsReceipt/{id} og deviation :deliver/:approve/:undeliver tar INNKJØPSORDRE-id; PUT/DELETE /purchaseOrder/goodsReceipt/{id} tar varemottakets id; GET /purchaseOrder/deviation/{id} og GET /purchaseOrder/goodsReceiptLine/{id} tar ordrelinje-id. DELETE /purchaseOrder/deviation/{id} har misvisende beskrivelse – verifiser før bruk.
- Alle /document- og /documentArchive-endepunkter er BETA. Opplasting er multipart/form-data med feltet 'file'. /documentArchive/account/{id} tar kontoens id, ikke kontonummer.
- POST /ledger/voucher/importDocument godtar PDF/PNG/JPEG/TIFF; EHF/XML kun etter avtale med Tripletex. split=true gir ett bilag per side. POST /ledger/voucher/{voucherId}/attachment legger til sider i eksisterende vedlegg.
- Manuell leverandørfaktura via POST /ledger/voucher: kun amountGross brukes, postings må balansere (sum 0), row starter på 1, supplier{id} + invoiceNumber + termOfPayment settes på 2400-linjen for at reskontroen skal bli riktig.
- DELETE /supplier/{id} feiler hvis leverandøren har posteringer – sett isInactive=true med PUT i stedet. Feltet bankAccounts er DEPRECATED; bruk bankAccountPresentation.
- Leverandør- og kundekategorier er samme ressurs: /customer/category (bruk type-parameteren).
- Beløp på SupplierInvoice: amount er i NOK, amountCurrency i fakturavaluta, outstandingAmount er i fakturavaluta. amount/amountExcludingVat er 0 når verdien mangler.
- Ved PUT må id og version (hentet rett før) sendes med, ellers 409/konflikt.
- 403 betyr manglende rettighet/rolle for API-brukeren (f.eks. ikke attestant, mangler 'Avansert bilag') eller manglende modul hos klienten – ikke at objektet ikke finnes.
- GDPR: leverandører som er privatpersoner/ENK, bankkontonummer (bban/iban), attestanter (ansatte), receivedBy og /documentArchive/employee inneholder personopplysninger – bruk minimale fields= og vis aldri navn/kontonummer i svar.
- Alle skrivende kall (opprette/endre/slette leverandør, attestere, avvise, betale, sende innkjøpsordre, laste opp) krever brukerens bekreftelse og at klienten er eksplisitt angitt.
- count er 1000 som standard på listeendepunkter (/supplier, /supplierInvoice, /purchaseOrder ...) – paginér med from/count når fullResultSize er større.
- GET /purchaseOrder har ingen status-parameter (bare isClosed og withDeviationOnly) – filtrer status lokalt. GET /purchaseOrder/goodsReceipt?status= godtar kun STATUS_OPEN|STATUS_CONFIRMED.
- Masse-sletting er ulik: DELETE /purchaseOrder/goodsReceipt/list og /purchaseOrder/purchaseOrderIncomingInvoiceRelation/list tar ?ids=1,2 (påkrevd), mens DELETE /purchaseOrder/orderline/list og /purchaseOrder/goodsReceiptLine/list tar objektene i JSON-body.
- PUT /purchaseOrder/{id}/:send: sendType er DEFAULT|EMAIL|FTP; e-post går til receiverEmail på ordren, ellers leverandørens e-post. PUT /purchaseOrder/{id}/:sendByEmail tar body {email, subject, message}.
- GET /supplierCustomer/search returnerer bare AKTIVE kunder/leverandører – inaktive må hentes med GET /supplier?isInactive=true.
- POST /ledger/voucher har sendToLedger=true som standard (krever «Avansert bilag»); bruk sendToLedger=false for å lagre uten å bokføre. Inngående mva-koder: GET /ledger/vatType?typeOfVat=INCOMING_INVOICE eller INCOMING.
- GET /supplierInvoice viser fakturaer registrert i leverandørfaktura-flyten (EHF/bilagsmottak). Ved avstemming av leverandørgjeld er /ledger/posting/openPost på 2400-serien fasit.

## Prosjekt, aktiviteter, oppgaver

### Søke opp prosjekter (åpne, lukkede, per kunde, prosjektleder eller avdeling)
- **Kall:** `GET /project`, `GET /project/{id}`, `GET /project/number/{number}`, `GET /customer`
- **Nøkkelord:** finn prosjekt, søk prosjekt, liste prosjekter, åpne prosjekter, aktive prosjekter, lukkede prosjekter, prosjekter for kunde, prosjektnummer, prosjektoversikt, prosjektliste, project search, prosjekt id, sok prosjekt, apne prosjekter, prosjekter for ansatt, mine prosjekter, prosjekter per prosjektleder, finne prosjektnummer
- 1) Har du prosjektnummeret: GET /project/number/{number}. Ellers GET /project med filtre: name (inneholder), number (eksakt), customerId (finn kunde-id via GET /customer?customerName=...), projectManagerId, departmentId, isClosed=false for åpne (legg til includeRecentlyClosed=true for å få med de som er lukket siste 3 mnd), isOffer=false for å utelate tilbud, isFixedPrice, employeeInProjectId (prosjekter en ansatt deltar i), customerAccountManagerId, externalAccountsNumber, startDateFrom/To og endDateFrom/To (To er eksklusiv). 2) Bruk fields=id,number,name,displayName,customer(id,name),projectManager(id),startDate,endDate,isClosed,isFixedPrice,mainProject(id) og count/from for paging. 3) Detaljer: GET /project/{id}. Unngå å skrive ut navn på prosjektleder (GDPR) – bruk initialer. Standard count er 1000 – sjekk fullResultSize og bla med from/count ved store klienter.

### ✏️ Opprette nytt prosjekt for en kunde (timepris eller fastpris)
- **Kall:** `GET /customer`, `GET /employee`, `GET /project/category`, `GET /department`, `GET /project/settings`, `POST /project`
- **Nøkkelord:** opprett prosjekt, nytt prosjekt, lage prosjekt, registrere prosjekt, starte prosjekt, fastprisprosjekt, timeprisprosjekt, prosjekt på kunde, new project, create project, oppdrag, prosjekt pa kunde, prosjekttilbud, opprette tilbud, internprosjekt
- 1) Finn kunde-id (GET /customer?customerName=...&fields=id,name) og prosjektleder-id (GET /employee?assignableProjectManagers=true&fields=id – minimalt av hensyn til GDPR). 2) Valgfritt: kategori (GET /project/category), avdeling (GET /department). 3) POST /project med body (spec markerer ingen felt som påkrevd, men i praksis kreves name, projectManager og startDate) {name, projectManager:{id}, customer:{id}, startDate (yyyy-MM-dd), isFixedPrice:true/false, fixedprice (ved fastpris), isInternal, projectCategory:{id}, department:{id}, invoiceComment, reference}. number kan utelates – da genereres det automatisk (se autoGenerateProjectNumber i GET /project/settings). isOffer=true lager et tilbud i stedet for prosjekt. 4) Returnerer prosjekt med id – bruk denne videre til aktiviteter, timepriser og deltakere. Skrivende: bekreft med bruker først.

### ✏️ Opprette delprosjekt (underprosjekt) under et hovedprosjekt
- **Kall:** `GET /project`, `POST /project`
- **Nøkkelord:** delprosjekt, underprosjekt, hovedprosjekt, prosjekthierarki, subproject, mainproject, fase, etappe
- 1) Finn hovedprosjektets id (GET /project?number=... eller name=...). 2) POST /project med mainProject:{id: <hovedprosjekt>}, name, projectManager:{id}, startDate, og ev. samme customer. 3) Delprosjekter kan senere summeres i rapporter, f.eks. GET /balanceSheet?projectId=...&includeSubProjects=true. Skrivende.

### ✏️ Endre prosjekt (prosjektleder, datoer, fastpris, fakturakommentar, klar til fakturering)
- **Kall:** `GET /project/{id}`, `PUT /project/{id}`, `PUT /project/list`
- **Nøkkelord:** endre prosjekt, oppdatere prosjekt, bytte prosjektleder, ny sluttdato, endre fastpris, klar til fakturering, fakturakommentar, prisloft, rabatt prosjekt, update project, forfall prosjekt, fakturamottaker prosjekt
- 1) GET /project/{id}?fields=id,version,name,... for å få gjeldende version. 2) PUT /project/{id} [BETA] med id, version og feltene som endres, f.eks. projectManager:{id}, endDate, fixedprice, isPriceCeiling/priceCeilingAmount, discountPercentage, markUpOrderLines, invoiceComment, isReadyForInvoicing=true, invoiceDueDate + invoiceDueDateType (DAYS|MONTHS|RECURRING_DAY_OF_MONTH), invoiceReceiverEmail. 3) Mange prosjekter samtidig: PUT /project/list med liste av prosjekter (hver med id+version). Feil version gir 409 – hent på nytt. Skrivende.

### ✏️ Avslutte (lukke) prosjekt eller gjenåpne det
- **Kall:** `GET /project/{id}`, `PUT /project/{id}`, `GET /project/{id}/period/invoicingReserve`, `PUT /project/list`
- **Nøkkelord:** lukke prosjekt, avslutte prosjekt, stenge prosjekt, ferdigstille prosjekt, gjenåpne prosjekt, arkivere prosjekt, close project, isclosed, ferdig prosjekt, gjenapne prosjekt
- 1) Sjekk først at alt er fakturert: GET /project/{id}/period/invoicingReserve?dateFrom=<prosjektstart>&dateTo=<dagen etter siste dag, dateTo er eksklusiv> – invoiceReserveTotalAmountCurrency bør være 0 (feltet finnes også read-only på GET /project/{id}). 2) GET /project/{id}?fields=id,version,isClosed. 3) PUT /project/{id} med id, version, isClosed=true (og ev. endDate). Gjenåpne med isClosed=false. Flere: PUT /project/list. Lukk heller enn å slette prosjekter som har timer/bilag. Skrivende.

### ✏️ Slette prosjekt(er)
- **Kall:** `DELETE /project/{id}`, `DELETE /project/list`, `DELETE /project`
- **Nøkkelord:** slette prosjekt, fjerne prosjekt, delete project, slette flere prosjekter, rydde prosjekter, feilregistrert prosjekt
- Én: DELETE /project/{id} [BETA]. Flere: DELETE /project/list?ids=1,2,3 [BETA] eller DELETE /project med body-liste av prosjekter. Sletting feiler typisk med valideringsfeil (422) hvis prosjektet har timer, bilag, ordre eller fakturaer – da bør prosjektet lukkes (isClosed=true) i stedet. Irreversibelt – krever eksplisitt bekreftelse fra bruker.

### ✏️ Opprette mange prosjekter samtidig eller importere prosjekter fra fil (Excel/CSV)
- **Kall:** `POST /project/list`, `POST /project/import`
- **Nøkkelord:** masseopprette prosjekter, importere prosjekter, prosjektimport, excel import, csv import, bulk prosjekt, flere prosjekter, migrering prosjekter, konvertering, import project
- JSON: POST /project/list [BETA] med en liste av Project-objekter (samme felt som POST /project). Fil: POST /project/import som multipart/form-data med feltet file, og query fileFormat=XLS|CSV (påkrevd), ev. encoding, delimiter og ignoreFirstRow=true når første rad er overskrift. Test gjerne på én rad først. Skrivende.

### ✏️ Hente og vedlikeholde prosjektkategorier
- **Kall:** `GET /project/category`, `GET /project/category/{id}`, `POST /project/category`, `PUT /project/category/{id}`
- **Nøkkelord:** prosjektkategori, ny kategori, endre kategori, kategorier prosjekt, prosjekttype, project category
- Liste: GET /project/category (filtre id, name, number, description; fields=id,number,name). Ny: POST /project/category {name, number, description}. Endre: GET /project/category/{id} for version, deretter PUT /project/category/{id}. Kategorier brukes normalt bare når projectCategories=true i /project/settings. Ingen DELETE finnes i API-et. POST/PUT er skrivende.

### Liste aktiviteter (fakturerbare, generelle, prosjektaktiviteter, fravær)
- **Kall:** `GET /activity`, `GET /activity/{id}`, `GET /activity/category/list`, `GET /activity/category/{id}`
- **Nøkkelord:** aktiviteter, liste aktiviteter, timeaktiviteter, fakturerbare aktiviteter, ikke fakturerbare, fraværsaktiviteter, generelle aktiviteter, activity list, timekoder, aktivitetskategori, fravaersaktiviteter
- GET /activity med filtre name, number, isChargeable, isProjectActivity, isGeneral, isTask, isInactive=false, absence=true (fravær); fields=id,number,name,isChargeable,rate,isProjectActivity,isGeneral,isTask. Enkelt: GET /activity/{id}. Aktivitetskategorier: GET /activity/category/list eller /activity/category/{id} (brukes f.eks. som activityCategoryId på GET /task).

### ✏️ Opprette ny aktivitet (generell eller generell prosjektaktivitet)
- **Kall:** `POST /activity`, `POST /activity/list`
- **Nøkkelord:** ny aktivitet, opprette aktivitet, lage timeaktivitet, fakturerbar aktivitet, ny timekode, create activity, generell prosjektaktivitet
- POST /activity med {name, number, activityType, isChargeable, rate, costPercentage, description}. activityType: GENERAL_ACTIVITY (generell, ikke prosjekt), PROJECT_GENERAL_ACTIVITY (kan brukes på alle prosjekter), TASK. PROJECT_SPECIFIC_ACTIVITY kan IKKE lages her – den lages via POST /project/projectActivity med en ny activity inni. Flere samtidig: POST /activity/list. Ingen PUT/DELETE for /activity i API-et – feilregistrerte aktiviteter må rettes i Tripletex-GUI. isProjectActivity/isGeneral/isTask er read-only og styres av activityType. Skrivende.

### ✏️ Knytte aktivitet til prosjekt med budsjett (prosjektaktivitet)
- **Kall:** `GET /activity`, `POST /project/projectActivity`, `GET /project/projectActivity/{id}`, `DELETE /project/projectActivity/{id}`, `DELETE /project/projectActivity/list`, `GET /project/{id}`, `PUT /project/{id}`
- **Nøkkelord:** knytte aktivitet til prosjekt, prosjektaktivitet, legg til aktivitet på prosjekt, budsjett timer aktivitet, budsjetthonorar, prosjektspesifikk aktivitet, fjern aktivitet fra prosjekt, lukke aktivitet, fase prosjekt, legg til aktivitet pa prosjekt
- 1) Finn aktivitet (GET /activity?isProjectActivity=true) – eller send en ny aktivitet inline. 2) POST /project/projectActivity {project:{id}, activity:{id} (eller activity:{name, activityType:'PROJECT_SPECIFIC_ACTIVITY', isChargeable}), startDate, endDate, budgetHours, budgetHourlyRateCurrency, budgetFeeCurrency}. 3) Se prosjektets aktiviteter: GET /project/{id}?fields=projectActivities(id,activity(id,name),budgetHours,isClosed). 4) Fjern: DELETE /project/projectActivity/{id} eller /list?ids=... (feiler normalt hvis timer er ført). Det finnes ingen PUT /project/projectActivity/{id}; endring av budsjett/isClosed på en eksisterende prosjektaktivitet må ev. gjøres via PUT /project/{id} med projectActivities (id+version) – test i sandbox først. Skrivende.

### Finne hvilke prosjekter og aktiviteter en ansatt kan føre timer på en gitt dag
- **Kall:** `GET /project/>forTimeSheet`, `GET /activity/>forTimeSheet`, `GET /timesheet/entry/>recentProjects`
- **Nøkkelord:** hvilke prosjekter kan jeg føre timer på, timeføring, timeregistrering, føre timer, tilgjengelige aktiviteter, timeliste, for timesheet, prosjekter for timeføring, registrere timer prosjekt, hvilke prosjekter kan jeg fore timer pa, timeforing, fore timer, prosjekter for timeforing
- 1) GET /project/>forTimeSheet?date=yyyy-MM-dd (employeeId valgfri, standard er token-eier; includeProjectOffers=true tar med tilbud). 2) GET /activity/>forTimeSheet?projectId=<id>&date=... (projectId er påkrevd; filterExistingHours=true skjuler aktiviteter med timer allerede; query= for tekstsøk). 3) Nylig brukte prosjekter: GET /timesheet/entry/>recentProjects (employeeId valgfri). 4) Selve timeføringen skjer med POST /timesheet/entry i timer-gruppen (skrivende – bekreft først). Stier med '>' må ev. URL-kodes som %3E. Timeføring er personopplysning – bruk fields= minimalt.

### ✏️ Legge til eller fjerne prosjektdeltakere
- **Kall:** `GET /project/{id}`, `GET /employee`, `POST /project/participant`, `POST /project/participant/list`, `GET /project/participant/{id}`, `PUT /project/participant/{id}`, `DELETE /project/participant/list`
- **Nøkkelord:** prosjektdeltaker, legg til ansatt på prosjekt, fjerne deltaker, prosjektteam, prosjektmedlemmer, tilgang til prosjekt, admin tilgang prosjekt, participant, kun deltakere kan føre timer, legg til ansatt pa prosjekt, kun deltakere kan fore timer
- 1) Se deltakere: GET /project/{id}?fields=participants(id,employee(id),adminAccess) – hent ikke navn/e-post med mindre nødvendig (GDPR). 2) Finn ansatt-id via GET /employee?fields=id (minimalt). 3) Legg til: POST /project/participant {project:{id}, employee:{id}, adminAccess:false} eller POST /project/participant/list for flere [BETA]. 4) Endre admin-tilgang: GET /project/participant/{id} for version, PUT /project/participant/{id}. 5) Fjern: DELETE /project/participant/list?ids=<deltaker-ider> (ikke ansatt-ider; det finnes ingen DELETE /project/participant/{id}) Relevant når prosjektet har forParticipantsOnly=true. Skrivende.

### ✏️ Sette eller endre timepriser på prosjekt (fast timepris, forhåndsdefinerte eller prosjektspesifikke)
- **Kall:** `GET /project/hourlyRates`, `GET /project/hourlyRates/{id}`, `POST /project/hourlyRates`, `POST /project/hourlyRates/list`, `PUT /project/hourlyRates/{id}`, `PUT /project/hourlyRates/list`, `PUT /project/hourlyRates/updateOrAddHourRates`
- **Nøkkelord:** timepris prosjekt, sette timepris, endre timepris, ny timesats, prisjustering, fast timepris, honorarsats, timeprismodell, hourly rate, timepris fra dato, indeksregulering timepris
- 1) Se eksisterende: GET /project/hourlyRates?projectId=<id>&fields=id,version,startDate,hourlyRateModel,fixedRate,showInProjectOrder (filter type=TYPE_FIXED_HOURLY_RATE osv., startDateFrom/To). 2) Ny sats fra dato: POST /project/hourlyRates {project:{id}, startDate, hourlyRateModel: TYPE_FIXED_HOURLY_RATE + fixedRate | TYPE_PREDEFINED_HOURLY_RATES (bruker aktivitets-/ansattsatser) | TYPE_PROJECT_SPECIFIC_HOURLY_RATES + projectSpecificRates[], showInProjectOrder}. 3) Endre: PUT /project/hourlyRates/{id} (med version) eller /list for flere. 4) Samme sats på mange prosjekter: PUT /project/hourlyRates/updateOrAddHourRates?ids=<prosjekt-ider> med HourlyRate-body {startDate, hourlyRateModel, fixedRate}. Skrivende.

### ✏️ Slette timepriser på prosjekt
- **Kall:** `DELETE /project/hourlyRates/{id}`, `DELETE /project/hourlyRates/list`, `DELETE /project/hourlyRates/deleteByProjectIds`
- **Nøkkelord:** slette timepris, fjerne timesats, feil timepris, delete hourly rate, rydde timepriser
- Én: DELETE /project/hourlyRates/{id}. Flere: DELETE /project/hourlyRates/list?ids=<timepris-ider>. Per prosjekt: DELETE /project/hourlyRates/deleteByProjectIds?ids=<prosjekt-ider>&date=yyyy-MM-dd (begge påkrevd; spec dokumenterer ikke nøyaktig hvilke satser date avgrenser til, så list satsene før/etter med GET /project/hourlyRates?projectId=... og test i sandbox). Irreversibelt – bekreft med bruker.

### ✏️ Sette personlige/aktivitetsspesifikke timepriser og finne ansatte som mangler timepris
- **Kall:** `GET /project/{id}/actionList/employeesWithMissingHourlyRate`, `GET /project/hourlyRates`, `GET /project/hourlyRates/projectSpecificRates`, `GET /project/hourlyRates/projectSpecificRates/{id}`, `POST /project/hourlyRates/projectSpecificRates`, `POST /project/hourlyRates/projectSpecificRates/list`, `PUT /project/hourlyRates/projectSpecificRates/{id}`, `PUT /project/hourlyRates/projectSpecificRates/list`, `DELETE /project/hourlyRates/projectSpecificRates/{id}`, `DELETE /project/hourlyRates/projectSpecificRates/list`
- **Nøkkelord:** timepris per ansatt, personlig timepris, timepris per aktivitet, mangler timepris, kostprosent, internkost timer, prosjektspesifikke timepriser, project specific rate, handlingsliste
- 1) Hvem mangler sats: GET /project/{id}/actionList/employeesWithMissingHourlyRate (returnerer id, displayName, canSetHourlyRate – vis ikke navn videre, bruk «ansatt 1/2»). 2) Finn prosjektets timepris-id med modell TYPE_PROJECT_SPECIFIC_HOURLY_RATES: GET /project/hourlyRates?projectId=...&type=TYPE_PROJECT_SPECIFIC_HOURLY_RATES. 3) Se eksisterende: GET /project/hourlyRates/projectSpecificRates?projectHourlyRateId=...(&employeeId, activityId). 4) Opprett: POST /project/hourlyRates/projectSpecificRates {projectHourlyRate:{id}, employee:{id} og/eller activity:{id}, hourlyRate, hourlyCostPercentage} – /list for flere. 5) Endre med PUT (version), slett med DELETE /{id} eller /list?ids=. Timepris per ansatt kan være sensitiv – fields= minimalt. Skrivende.

### Se handlingslisten (hva som mangler) for et prosjekt
- **Kall:** `GET /project/{id}/actionList`, `GET /project/{id}/actionList/employeesWithMissingHourlyRate`
- **Nøkkelord:** handlingsliste, hva mangler på prosjektet, oppfølging, action list, sjekkliste prosjekt, gjøremål prosjekt, hva mangler pa prosjektet, oppfolging, gjoremal prosjekt, mangler fastpris, mangler budsjett, mangler fakturaplan, prosjektkontroll
- GET /project/{id}/actionList returnerer en liste med kodeverdier for hva som mangler: MISSING_FIXED_PRICE, MISSING_FIXED_HOURLY_RATE, EMPLOYEES_MISSING_HOURLY_RATE, EMPLOYEES_MISSING_HOURLY_COST, MISSING_PROJECT_SPECIFIC_RATES, MISSING_BUDGET, MISSING_INVOICE_PLAN. For EMPLOYEES_MISSING_HOURLY_RATE: GET /project/{id}/actionList/employeesWithMissingHourlyRate (id, displayName, canSetHourlyRate – vis ikke navn, bruk «ansatt 1/2»). Kun lesing. Gå så videre til timepris-/budsjett-oppgavene for å rette opp.

### Hente prosjektregnskap: inntekter, kostnader og dekningsbidrag for en periode
- **Kall:** `GET /project/{id}/period/overallStatus`, `GET /project/{id}/period/monthlyStatus`, `GET /project/{id}`
- **Nøkkelord:** prosjektregnskap, prosjektøkonomi, lønnsomhet prosjekt, dekningsbidrag, db prosjekt, inntekt og kostnad, resultat per prosjekt, etterkalkyle, prosjektrapport, margin prosjekt, månedsstatus prosjekt, overall status, prosjektokonomi, lonnsomhet prosjekt, manedsstatus prosjekt
- 1) Totalt for periode: GET /project/{id}/period/overallStatus?dateFrom=yyyy-MM-dd&dateTo=yyyy-MM-dd (dateTo eksklusiv) → income, costs, totalFeeCurrency (honorar av timer), totalHourCostCurrency (internkost timer), totalTravelExpensesCurrency, totalTravelIncomeCurrency. DB = income − costs. 2) Per måned: GET /project/{id}/period/monthlyStatus – OBS avvikende datoregler: dateFrom rundes til første dag i måneden, dateTo rundes til siste dag i måneden og er INKLUSIV, og dateTo må være i samme år som dateFrom (del opp over årsskifte) → liste med income, costs, dateFrom, dateTo per måned. 3) GET /project/{id}?fields=contributionMarginPercent gir DB-% fra Tripletex. For tall fra hovedboka, se oppgaven om prosjektposteringer.

### Hente posteringer, hovedbok og saldobalanse per prosjekt (prosjekt som dimensjon)
- **Kall:** `GET /ledger/posting`, `GET /ledger`, `GET /balanceSheet`, `GET /travelExpense`
- **Nøkkelord:** posteringer prosjekt, hovedbok prosjekt, saldobalanse prosjekt, resultat per prosjekt, prosjektdimensjon, kostnader på prosjekt, bilag på prosjekt, prosjektregnskap hovedbok, inkludert delprosjekter, ledger project, kostnader pa prosjekt, bilag pa prosjekt
- 1) Enkeltposteringer: GET /ledger/posting?dateFrom=...&dateTo=...&projectId=<id> (dateFrom/dateTo påkrevd, dateTo eksklusiv; fields=id,date,account(number,name),amount,description,voucher(number)). 2) Hovedbok gruppert på konto: GET /ledger?dateFrom&dateTo&projectId. 3) Saldobalanse/resultat per prosjekt: GET /balanceSheet?dateFrom&dateTo&projectId=<id>&includeSubProjects=true (eller projectIds=1,2,3), accountNumberFrom=3000&accountNumberTo=8999 for resultatkontoer. 4) Reiseregninger på prosjektet: GET /travelExpense?projectId=... (personopplysning – fields= minimalt).

### Timelisterapport for prosjekt: fakturerbare, ikke fakturerbare og ikke godkjente timer
- **Kall:** `GET /project/{id}/period/hourlistReport`, `GET /timesheet/entry`
- **Nøkkelord:** timer på prosjekt, timeliste prosjekt, timerapport, fakturerbare timer, ikke fakturerbare timer, ikke godkjente timer, godkjent men ikke fakturert, registrerte timer, hourlist report, timeforbruk, medgåtte timer, timer pa prosjekt, medgatte timer
- 1) Sammendrag: GET /project/{id}/period/hourlistReport?dateFrom=...&dateTo=... (begge påkrevd, dateTo eksklusiv) → registeredHours, chargeableHours, nonChargeableHours, approvedButUnchargedHours, nonApprovedHours. 2) Detaljer ved behov: GET /timesheet/entry?projectId=<id>&dateFrom&dateTo&fields=date,hours,activity(name),chargeable (dateFrom/dateTo påkrevd). Timeføringer per ansatt er personopplysninger – aggreger, vis ikke navn.

### Hente fakturareserve (opptjent, ikke fakturert) for ett eller mange prosjekter – f.eks. til periodisering ved månedsslutt
- **Kall:** `GET /project/{id}/period/invoicingReserve`, `GET /project/batchPeriod/invoicingReserveByProjectIds`, `GET /project`
- **Nøkkelord:** fakturareserve, ufakturert, ikke fakturert, opptjent ikke fakturert, igangværende arbeid, varer i arbeid, wip, periodisering, periodisere inntekt, månedsavslutning, årsoppgjør, a konto, hva kan faktureres, fakturagrunnlag, invoicing reserve, igangvaerende arbeid, manedsavslutning, arsoppgjor
- Ett prosjekt: GET /project/{id}/period/invoicingReserve?dateFrom=...&dateTo=... → invoiceFeeReserveCurrency (timer), invoiceExtracostsReserveCurrency (utlegg/tillegg), periodOrderLinesIncomeCurrency, invoiceAkontoReserveAmountCurrency, invoiceReserveTotalAmountCurrency. Mange: hent åpne prosjekt-ider (GET /project?isClosed=false&fields=id) og kall GET /project/batchPeriod/invoicingReserveByProjectIds?ids=1,2,3&dateFrom=...&dateTo=... (alle tre påkrevd, maks 1000 ider; dateTo eksklusiv). Summen brukes som grunnlag for periodisering av opptjent inntekt (f.eks. konto 1530/3xxx) – selve bilaget føres via /ledger/voucher (hovedbok-gruppen).

### Se hva som er fakturert og utestående på et prosjekt
- **Kall:** `GET /project/{id}/period/invoiced`, `GET /ledger/posting`, `GET /project/{id}`
- **Nøkkelord:** fakturert prosjekt, utestående prosjekt, betalt prosjekt, forfalt prosjekt, fakturaer på prosjekt, kundereskontro prosjekt, innbetalt, invoiced, utestaende prosjekt, fakturaer pa prosjekt, a konto prosjekt, akonto
- GET /project/{id}/period/invoiced?dateFrom=...&dateTo=... (påkrevd) → sumAmount (fakturert), sumAmountPaid, sumAmountOutstanding, sumAmountDue, sumAmountDueOutstanding (forfalt ubetalt). For enkeltposter mot kundereskontro: GET /ledger/posting?projectId=<id>&dateFrom&dateTo&type=OUTGOING_INVOICE_CUSTOMER_POSTING. A konto og reserve: GET /project/{id}?fields=totalInvoicedOnAccountAmountAbsoluteCurrency,invoiceReserveTotalAmountCurrency.

### Sjekke budsjettstatus (budsjett mot faktisk) for ett eller flere prosjekter
- **Kall:** `GET /project/{id}/period/budgetStatus`, `GET /project/batchPeriod/budgetStatusByProjectIds`, `GET /resultbudget/project/{id}`, `GET /project/capacityPlan/budget`
- **Nøkkelord:** budsjett prosjekt, budsjettstatus, budsjett mot faktisk, avvik budsjett, overskridelse, prognose prosjekt, resultatbudsjett prosjekt, budget status, kostnadsbudsjett, inntektsbudsjett
- Ett prosjekt: GET /project/{id}/period/budgetStatus (tar ingen datoer, til tross for navnet) → totalTotalIncomeCurrency (faktisk), budgetTotalIncomeCurrency, budgetTotalCostCurrency. Mange: GET /project/batchPeriod/budgetStatusByProjectIds?ids=1,2,3 (maks 1000). Resultatbudsjett per konto: GET /resultbudget/project/{id}?year=YYYY (hovedbok-gruppen). Timer mot timebudsjett: GET /project/capacityPlan/budget (se kapasitetsplan-oppgaven).

### Hente kapasitetsplan: budsjetterte mot førte timer per aktivitet og ansatt
- **Kall:** `GET /project/capacityPlan/budget`, `GET /project/resourcePlanBudget`
- **Nøkkelord:** kapasitetsplan, ressursplan, bemanning, planlagte timer, timebudsjett, belegg, timer mot budsjett, capacity plan, resource plan
- GET /project/capacityPlan/budget?projectId=<id>&periodStart=yyyy-MM-dd&periodEnd=yyyy-MM-dd&periodType=MONTH (periodStart, periodEnd og periodType HOUR|DAY|WEEK|MONTH er påkrevd; periodEnd eksklusiv) → activityEntries[] (activityId, activityName) med employeeEntries (budget, remaining, totalHours, totalAllocated, hourEntries) per aktivitet. GET /project/resourcePlanBudget er deprecated – bruk kun capacityPlan. Tomt svar kan bety at kapasitetsplanlegging ikke er i bruk (se capacityPlanning i GET /project/settings). Aggreger per aktivitet; vis ikke ansattnavn.

### ✏️ Registrere varer, materiell og utlegg på prosjekt for viderefakturering (prosjektordrelinjer)
- **Kall:** `GET /product`, `GET /project/orderline/orderLineTemplate`, `POST /project/orderline`, `POST /project/orderline/list`, `GET /project/orderline`, `GET /project/orderline/query`, `GET /project/orderline/{id}`, `PUT /project/orderline/{id}`, `DELETE /project/orderline/{id}`
- **Nøkkelord:** viderefakturering, utlegg prosjekt, materiell prosjekt, varer på prosjekt, prosjektordrelinje, påslag, tilleggsarbeid, fakturerbar kostnad, budsjettlinjer, legge til vare på prosjekt, project order line, varer pa prosjekt, paslag, legge til vare pa prosjekt
- 1) Finn produkt (GET /product?name=... eller productNumber). 2) Hent ferdig utfylt mal: GET /project/orderline/orderLineTemplate?projectId=...&productId=... (begge påkrevd) – gir riktig pris, mva-kode og påslag. 3) POST /project/orderline {project:{id}, product:{id}, date, count, unitCostCurrency, unitPriceExcludingVatCurrency, markup, discount, vatType:{id}, isChargeable:true, description} – bruk /list ved flere [BETA]. 4) Se linjer: GET /project/orderline?projectId=<id> (påkrevd; isBudget=true for budsjettlinjer – isBudget er read-only og kan ikke settes ved POST) eller GET /project/orderline/query?projectId&query=<tekst>. 5) Endre: PUT /project/orderline/{id} (version); slett: DELETE /project/orderline/{id}. Linjer som er fakturert (invoice satt) bør ikke endres. Skrivende.

### ✏️ Fakturere prosjekt (lage faktura på timer, fastpris, a konto eller utlegg)
- **Kall:** `GET /project/{id}/period/invoicingReserve`, `GET /project/{id}/period/hourlistReport`, `GET /project/{id}`, `POST /order`, `PUT /order/{id}/:invoice`
- **Nøkkelord:** fakturere prosjekt, prosjektfaktura, faktura prosjekt, a konto faktura, delfaktura, fakturere timer, sluttfaktura, fastprisfaktura, fakturagrunnlag, invoice project, ehf prosjekt
- 1) Finn grunnlag: GET /project/{id}/period/invoicingReserve og hourlistReport for perioden (dateFrom/dateTo påkrevd, dateTo eksklusiv). 2) GET /project/{id}?fields=id,customer(id),invoiceComment,invoiceDueDate,invoiceDueDateType,currency(id). 3) POST /order {customer:{id}, project:{id}, orderDate, deliveryDate, invoiceComment, orderLines:[{description, count, unitPriceExcludingVatCurrency, vatType:{id}}]}. 4) PUT /order/{id}/:invoice?invoiceDate=yyyy-MM-dd (påkrevd). sendToCustomer=false oppretter fakturaen uten å sende den – den er likevel en endelig, bokført faktura (ikke et utkast). Sending: sendType=EMAIL|EHF|AVTALEGIRO|EFAKTURA|VIPPS|PAPER|MANUAL. A konto: createOnAccount=WITH_VAT|WITHOUT_VAT + amountOnAccount (+ onAccountComment). API-et har ingen egen «fakturer prosjekt»-action som automatisk henter inn timer/prosjektordrelinjer – ordrelinjene må bygges selv. Skrivende og ev. sending til kunde – krever bekreftelse.

### ✏️ Flytte kostnad til riktig prosjekt på leverandørfaktura (endre prosjektdimensjon)
- **Kall:** `GET /supplierInvoice`, `PUT /supplierInvoice/{invoiceId}/:changeDimension`, `GET /project`
- **Nøkkelord:** endre prosjekt på faktura, feil prosjekt, flytte kostnad til prosjekt, omkontering prosjekt, prosjektdimensjon leverandørfaktura, change dimension, kostnadsføre på prosjekt, inngående faktura prosjekt, endre prosjekt pa faktura, prosjektdimensjon leverandorfaktura, kostnadsfore pa prosjekt, inngaende faktura prosjekt
- 1) Finn leverandørfakturaen: GET /supplierInvoice?invoiceDateFrom=...&invoiceDateTo=...(påkrevd)&invoiceNumber=...&fields=id,invoiceNumber,voucher(id,postings(id,account(number),amountGross)). 2) Finn prosjekt-id (GET /project?number=...). 3) PUT /supplierInvoice/{invoiceId}/:changeDimension?debitPostingIds=<ider>&dimension=PROJECT&dimensionId=<prosjekt-id> (alle påkrevd). Skrivende – bekreft først.

### ✏️ Registrere og følge opp underleverandører (underentrepriser) på prosjekt
- **Kall:** `GET /supplier`, `GET /project/subcontract`, `GET /project/subcontract/query`, `GET /project/subcontract/{id}`, `POST /project/subcontract`, `PUT /project/subcontract/{id}`, `DELETE /project/subcontract/{id}`
- **Nøkkelord:** underleverandør, underentreprise, ue, underentreprenør, innleid, budsjett underleverandør, subcontract, leverandør på prosjekt, underleverandor, underentreprenor, budsjett underleverandor, leverandor pa prosjekt
- 1) Finn leverandør-id: GET /supplier?organizationNumber=... 2) Liste: GET /project/subcontract?projectId=<id> (påkrevd), eller søk GET /project/subcontract/query?projectId&query=<tekst>. 3) Opprett: POST /project/subcontract {project:{id}, supplier:{id}, name, description, budgetFeeCurrency, budgetExpensesCurrency, budgetIncomeCurrency, budgetNetAmountCurrency}. 4) Endre: PUT /project/subcontract/{id} (med version); slett: DELETE /project/subcontract/{id}. Budsjettfeltene er mest relevante når budgetOnSubcontracts=true i /project/settings. Skrivende.

### ✏️ Hente kontrollskjema (egenkontroll/SJA) for prosjekt og kopiere verdier fra forrige skjema
- **Kall:** `GET /project/controlForm`, `GET /project/controlForm/{id}`, `GET /project/controlFormType`, `GET /project/controlFormType/{id}`, `PUT /project/dynamicControlForm/{id}/:copyFieldValuesFromLastEditedForm`, `GET /documentArchive/dynamicControlForm/{id}`
- **Nøkkelord:** kontrollskjema, egenkontroll, sja, sikker jobbanalyse, sjekkliste, signert skjema, utfylt skjema, hms, ferdigmelding, kopiere skjema, control form
- 1) Skjema på prosjekt: GET /project/controlForm?projectId=<id> (påkrevd) → title, comment, completed, signatureRequired, signed. Detalj: GET /project/controlForm/{id}. 2) Tilgjengelige skjematyper: GET /project/controlFormType (og /{id}) – kun id og name. 3) Forhåndsutfylle et dynamisk skjema: PUT /project/dynamicControlForm/{id}/:copyFieldValuesFromLastEditedForm (id = skjemaet det kopieres TIL) – kopierer kun inn i seksjoner som er tomme/standard og der malen har copyFieldValuesByDefault=true; signerte/fullførte skjema påvirkes ikke (skrivende). API-et har ikke noe søk etter dynamiske kontrollskjema, så id må være kjent. 4) Vedlegg til dynamisk skjema: GET /documentArchive/dynamicControlForm/{id}. [BETA] på controlForm-/controlFormType-endepunktene.

### ✏️ Lese eller endre prosjektinnstillinger for selskapet
- **Kall:** `GET /project/settings`, `PUT /project/settings`
- **Nøkkelord:** prosjektinnstillinger, oppsett prosjekt, godkjenning av timer, automatisk prosjektnummer, fastpris fullføringsgrad, standard timeprismodell, auto lukke fakturerte prosjekter, project settings, kapasitetsplanlegging på, kontrollskjema påkrevd, fastpris fullforingsgrad, kapasitetsplanlegging pa, kontrollskjema pakrevd
- GET /project/settings (fields= for de feltene du trenger) viser bl.a. autoGenerateProjectNumber/autoGenerateStartingNumber, mustApproveRegisteredHours (og ...ForHourlyRateProjects/...ForFixedPriceProjects), approveHourLists, approveInvoices, fixedPriceProjectsFeeCalcMethod (FIXED_PRICE_PROJECTS_CALC_METHOD_INVOICED_FEE|..._PERCENT_COMPLETED), projectHourlyRateModel, projectTypeOfContract (PROJECT_FIXED_PRICE|PROJECT_HOUR_RATES), capacityPlanning, resourcePlanning, projectCategories, onlyProjectMembersCanRegisterInfo, onlyProjectActivitiesTimesheetRegistration, budgetOnSubcontracts, autoCloseInvoicedProjects, controlFormsRequiredForInvoicing/controlFormsRequiredForHourTracking. PUT /project/settings endrer for hele selskapet – hent først, send bare endrede felt, og bekreft med bruker.

### Liste oppgaver (tasks) per prosjekt, kunde, ansvarlig eller status
- **Kall:** `GET /task`, `GET /project/task`, `GET /activity/category/list`
- **Nøkkelord:** oppgaver, gjøremål, oppgaveliste, tasks, åpne oppgaver, frister, ansvarlig oppgave, oppgaver på prosjekt, oppgaver per kunde, prioritet, arbeidsordre, gjoremal, apne oppgaver, oppgaver pa prosjekt
- GET /task med filtre projectId, customerId, ownerId, participantId, createdById, departmentId, activityCategoryId (fra GET /activity/category/list), statusIds, startDate (fra og med)/endDate (til, eksklusiv), query (navn/nummer/beskrivelse). fields=id,name,statusName,priorityName,startDate,endDate,budgetHours,isClosed,project(id,name),customer(id,name). Alle felt på Task er read-only – API-et har ingen POST/PUT for oppgaver. GET /project/task?projectId= er deprecated – bruk /task.

### ✏️ Hente prosjektmal for å opprette nytt prosjekt med standardoppsett
- **Kall:** `GET /project/template/{id}`, `POST /project`
- **Nøkkelord:** prosjektmal, mal, template, kopiere oppsett, standardprosjekt, nytt prosjekt fra mal
- GET /project/template/{id} gir malens felt (projectCategory, projectManager, department, isFixedPrice, fixedprice, markUpOrderLines, projectHourlyRates, forParticipantsOnly osv.). Det finnes ikke et søk-endepunkt for maler – id må være kjent. Bruk verdiene som utgangspunkt i body til POST /project (skrivende).

### ✏️ Hente og laste opp dokumenter i prosjektets dokumentarkiv
- **Kall:** `GET /documentArchive/project/{id}`, `POST /documentArchive/project/{id}`
- **Nøkkelord:** prosjektdokumenter, dokumentarkiv prosjekt, vedlegg prosjekt, kontrakt prosjekt, laste opp dokument, tegninger, fdv, document archive
- Liste: GET /documentArchive/project/{id}?periodDateFrom=...&periodDateTo=... (id = prosjekt-id; datoene er valgfrie, periodDateTo eksklusiv) [BETA]. Last opp: POST /documentArchive/project/{id} som multipart/form-data med feltet file [BETA]. Skrivende ved opplasting.

### ✏️ Føre bilag/postering med prosjekt som dimensjon (kostnad eller inntekt på prosjekt)
- **Kall:** `GET /project`, `POST /ledger/voucher`
- **Nøkkelord:** bilag på prosjekt, bilag pa prosjekt, postere på prosjekt, postere pa prosjekt, kostnadsføre på prosjekt, kostnadsfore pa prosjekt, prosjektdimensjon, manuelt bilag prosjekt, periodisering prosjekt, omfordele kostnad prosjekt, føre på prosjekt, fore pa prosjekt, voucher project
- 1) Finn prosjekt-id: GET /project?number=...&fields=id,number,name. 2) POST /ledger/voucher {date, description, postings:[{row:1, account:{id}, amountGross, amountGrossCurrency, project:{id}, vatType:{id}, description}, {row:2, motpost …}]} – prosjekt settes per postering (Posting.project), ikke på bilaget. Postingene må balansere (sum 0), og bare brutto-beløp brukes. Brukes f.eks. for periodisering av fakturareserve eller omfordeling av kostnader mellom prosjekter. Hovedbok-gruppen har detaljene for /ledger/voucher. Skrivende – bekreft klient og bilag først.

**Fallgruver:**
- Mange prosjekt-endepunkter er [BETA]: PUT/DELETE /project/{id}, /project/list (POST/PUT/DELETE), DELETE /project, /project/orderline*, /project/participant*, /project/controlForm* og /project/controlFormType*. De kan endre seg og bør testes i sandbox før bruk i produksjon.
- Prosjektmodulen må være aktiv i klientens abonnement. 403 betyr typisk manglende modul, manglende rettighet (f.eks. ikke prosjektleder/prosjektadministrator) eller at prosjektet har accessType NONE/READ for brukeren.
- Stier med '>' (GET /project/>forTimeSheet, GET /activity/>forTimeSheet) må skrives nøyaktig; enkelte HTTP-klienter krever URL-koding av '>' som %3E. GET /activity/>forTimeSheet krever projectId.
- Alle /project/{id}/period/*-kall unntatt budgetStatus krever dateFrom og dateTo (yyyy-MM-dd). For overallStatus, hourlistReport, invoiced og invoicingReserve er dateTo EKSKLUSIV (hele september: dateFrom=2026-09-01&dateTo=2026-10-01). UNNTAK monthlyStatus: dateFrom rundes ned til første dag i måneden, dateTo rundes opp til siste dag i måneden og er INKLUSIV, og dateTo må ligge i samme år som dateFrom. /period/budgetStatus tar ingen datoer.
- GET /project/batchPeriod/invoicingReserveByProjectIds krever ids, dateFrom og dateTo; budgetStatusByProjectIds krever bare ids. Maks 1000 ider per kall.
- GET /project/capacityPlan/budget krever periodStart, periodEnd (eksklusiv) og periodType (HOUR|DAY|WEEK|MONTH). GET /project/resourcePlanBudget og GET /project/task er deprecated – bruk henholdsvis /project/capacityPlan/budget og /task.
- GET /task er kun lesing (alle Task-felt er read-only) – oppgaver kan ikke opprettes eller endres via API-et.
- Aktiviteter: activityType styrer typen (GENERAL_ACTIVITY | PROJECT_GENERAL_ACTIVITY | PROJECT_SPECIFIC_ACTIVITY | TASK). PROJECT_SPECIFIC_ACTIVITY kan ikke lages via POST /activity – den må lages via POST /project/projectActivity. /activity har ingen PUT eller DELETE i API-et.
- Påkrevde query-parametere: GET /project/orderline, GET /project/subcontract og GET /project/controlForm krever projectId; GET /project/orderline/orderLineTemplate krever projectId og productId; POST /project/import krever fileFormat (XLS|CSV); DELETE /project/hourlyRates/deleteByProjectIds krever ids og date.
- Timepriser: hourlyRateModel avgjør hvilke felt som brukes – fixedRate bare ved TYPE_FIXED_HOURLY_RATE, projectSpecificRates bare ved TYPE_PROJECT_SPECIFIC_HOURLY_RATES; TYPE_PREDEFINED_HOURLY_RATES bruker aktivitetens/ansattes standardsatser. Ny sats fra en dato lages som ny ProjectHourlyRate med startDate, ikke ved å overskrive den gamle.
- PUT bruker optimistisk låsing: send med gjeldende version (hent objektet med fields=id,version først); utdatert version gir 409 Conflict.
- Prosjektnummer (number) genereres automatisk hvis det utelates og autoGenerateProjectNumber er på; ellers må det oppgis og være unikt. isOffer=true lager et tilbud, ikke et prosjekt – filtrer med isOffer=false når du lister prosjekter.
- Prosjekter med timer, bilag, ordre eller fakturaer kan normalt ikke slettes – lukk dem med isClosed=true i stedet. GET /project med isClosed=false skjuler lukkede prosjekter; bruk includeRecentlyClosed=true for de som er lukket siste 3 måneder.
- Det finnes ingen egen «fakturer prosjekt»-action: prosjektfakturering gjøres ved å lage ordre med project:{id} (POST /order) og fakturere med PUT /order/{id}/:invoice (invoiceDate påkrevd). Fakturareserve fra /period/invoicingReserve er grunnlaget, men linjene må bygges selv.
- Fakturareserve (invoicingReserve) er opptjent, ikke fakturert inntekt – nyttig for periodisering/igangværende arbeid ved månedsslutt og årsoppgjør, men selve periodiseringsbilaget må føres i hovedboka (/ledger/voucher).
- PUT /project/settings endrer innstillingene for hele selskapet – vær ekstra forsiktig og bekreft alltid.
- PUT /project/dynamicControlForm/{id}/:copyFieldValuesFromLastEditedForm er en action (kolon-sti) som bare fyller tomme seksjoner der malen har copyFieldValuesByDefault=true; signerte eller fullførte skjema endres ikke.
- GDPR: prosjektleder, deltakere, personlige timepriser (projectSpecificRates med employee), kapasitetsplan per ansatt og timeføringer er personopplysninger. Bruk fields= minimalt (f.eks. projectManager(id)), aggreger tall og vis initialer/«ansatt 1» i svar.
- Alle skrivende kall (POST/PUT/DELETE og :action) krever at brukeren har bekreftet klient og handling først.
- Listekall har standard count=1000 og from=0 – sjekk fullResultSize og bla med from/count; bruk alltid fields= for å begrense svaret.
- Read-only felt som ikke kan settes via API: Task (alle felt), Activity.isProjectActivity/isGeneral/isTask (styres av activityType), ProjectOrderLine.isBudget, Project.contributionMarginPercent/invoiceReserveTotalAmountCurrency/invoicingPlan.
- Manglende endepunkter: ingen PUT/DELETE på /activity, ingen DELETE på /project/category, ingen PUT på /project/projectActivity, ingen søk på /project/template (id må være kjent), ingen søk etter dynamiske kontrollskjema, og ingen POST/PUT på /task.
- Liste-DELETE-kall (/project/list, /project/participant/list, /project/projectActivity/list, /project/hourlyRates/list, /project/hourlyRates/projectSpecificRates/list) tar ids som kommaseparert query-parameter med ID-ene til selve objektene (f.eks. deltaker-id, ikke ansatt-id). DELETE /project (uten /list) tar i stedet en body-liste av Project-objekter.
- Prosjekt er også regnskapsdimensjon: posteringer/hovedbok/saldobalanse per prosjekt hentes med projectId på GET /ledger/posting, GET /ledger og GET /balanceSheet (dateFrom/dateTo påkrevd, dateTo eksklusiv; includeSubProjects=true på balanceSheet tar med delprosjekter). Ved POST /ledger/voucher settes prosjekt per postering (Posting.project).

## Timeføring og timelister

### Hente timeføringer for en periode (alle ansatte eller én ansatt)
- **Kall:** `GET /timesheet/entry`, `GET /employee`
- **Nøkkelord:** timeliste, timer, timeføringer, timeoversikt, hvor mange timer, timer forrige måned, hente timer, timesheet, hours
- GET /timesheet/entry med påkrevd dateFrom og dateTo (dateTo er eksklusiv: hele sept = dateFrom=2026-09-01&dateTo=2026-10-01). Filtrer med employeeId/projectId/activityId (kommaseparerte id-lister) og ev. comment. Svaret har sumAllHours i tillegg til values. Bruk minimalt fields=id,date,hours,chargeableHours,project(id,number,name),activity(id,name),employee(id) – ikke hent navn/e-post på ansatte (GDPR); rapporter per 'ansatt 1/2' eller initialer. Finn employeeId via GET /employee?fields=id,employeeNumber kun ved behov. Paginer med from/count.

### Hente timer på et prosjekt (timeliste/timerapport per prosjekt)
- **Kall:** `GET /project`, `GET /timesheet/entry`, `GET /project/{id}/period/hourlistReport`
- **Nøkkelord:** prosjekttimer, timer på prosjekt, timerapport, timeliste prosjekt, hourlist, prosjektoppfølging, prosjektrapport, registrerte timer
- 1) Finn prosjekt-id: GET /project?number=… eller name=… (fields=id,number,name). 2) Detaljer: GET /timesheet/entry?projectId={id}&dateFrom=…&dateTo=… (dateTo eksklusiv) med fields=date,hours,chargeableHours,activity(name),employee(id),comment. 3) Aggregert: GET /project/{id}/period/hourlistReport?dateFrom=…&dateTo=… gir registeredHours, chargeableHours, nonChargeableHours, approvedButUnchargedHours og nonApprovedHours. Rapporter aggregert per aktivitet, ikke per navngitt ansatt.

### Finne ufakturerte (og fakturerte) timer på prosjekt – fakturagrunnlag og fakturareserve
- **Kall:** `GET /timesheet/entry`, `GET /project/{id}/period/invoicingReserve`, `GET /project/batchPeriod/invoicingReserveByProjectIds`, `GET /project/{id}/period/invoiced`, `GET /project/{id}/period/hourlistReport`
- **Nøkkelord:** ufakturerte timer, ikke fakturert, fakturagrunnlag, fakturareserve, fakturerbare timer, wip, arbeid i arbeid, timer til fakturering, fakturerte timer, invoicing reserve
- Per timeføring: GET /timesheet/entry?projectId=…&dateFrom=…&dateTo=…&fields=id,date,hours,chargeable,chargeableHours,hourlyRate,invoice(id,invoiceNumber) – rader med chargeable=true og invoice=null er ufakturert; invoice satt = fakturert. Beløp: GET /project/{id}/period/invoicingReserve (dateFrom/dateTo påkrevd) eller for mange prosjekter GET /project/batchPeriod/invoicingReserveByProjectIds?ids=…(maks 1000). Allerede fakturert: GET /project/{id}/period/invoiced. approvedButUnchargedHours fra hourlistReport gir godkjente, ikke fakturerte timer. Selve faktureringen skjer via ordre (salg-gruppen, PUT /order/{id}/:invoice).

### Summere totalt antall timer for en ansatt i en periode
- **Kall:** `GET /timesheet/entry/>totalHours`, `GET /timesheet/entry`
- **Nøkkelord:** sum timer, totalt timer, antall timer, timesum, total hours, hvor mye har ansatt jobbet, arbeidede timer
- GET /timesheet/entry/>totalHours?employeeId=…&startDate=yyyy-MM-dd&endDate=yyyy-MM-dd (NB: startDate/endDate, ikke dateFrom/dateTo; endDate er eksklusiv). Standardverdier: employeeId = token-eier, startDate = i dag, endDate = i morgen – oppgi derfor alltid alle tre. Returnerer ett tall i value. For flere ansatte: GET /timesheet/entry med dateFrom/dateTo og les sumAllHours, eller fields=employee(id),hours og summer lokalt. Stien inneholder '>' – quote i shell / URL-encode som %3E.

### ✏️ Føre timer for en ansatt på prosjekt/aktivitet
- **Kall:** `GET /employee`, `GET /project/>forTimeSheet`, `GET /activity/>forTimeSheet`, `POST /timesheet/entry`, `GET /timesheet/settings`
- **Nøkkelord:** føre timer, fore timer, registrere timer, legge inn timer, timeføring, ny timeføring, post timer, log hours, create timesheet entry
- 1) employeeId: GET /employee?employeeNumber=…&fields=id (minimalt). 2) Gyldige prosjekter for dato: GET /project/>forTimeSheet?employeeId=…&date=… 3) Gyldige aktiviteter: GET /activity/>forTimeSheet?projectId=…&employeeId=…&date=… (for interne/generelle aktiviteter uten prosjekt brukes GET /activity?isGeneral=true). 4) POST /timesheet/entry body {employee:{id}, project:{id} (utelat for generell aktivitet), activity:{id}, date:'yyyy-MM-dd', hours:7.5, comment:'…'}. Sjekk GET /timesheet/settings (requireCommentsOnRegisteredHoursAllProjects) om kommentar er påkrevd. Kun én føring per ansatt/dato/aktivitet/prosjekt – finnes den, oppdater med PUT i stedet. Skrivende: bekreft med bruker først.

### ✏️ Føre mange timer på en gang (bulk/import av timelister)
- **Kall:** `POST /timesheet/entry/list`, `GET /timesheet/entry`
- **Nøkkelord:** importere timer, bulk timer, masseregistrering, timer fra excel, flere timeføringer, import timeliste, batch
- Bygg en JSON-array med TimesheetEntry-objekter ({employee:{id}, project:{id}, activity:{id}, date, hours, comment}) – flere ansatte kan sendes i samme kall (POST /timesheet/entry/list, body er en liste). Sjekk først med GET /timesheet/entry (samme periode, fields=id,date,employee(id),project(id),activity(id)) at kombinasjonen ansatt/dato/aktivitet/prosjekt ikke finnes fra før – duplikater gir valideringsfeil (422) og kan stoppe hele kallet. Send i passe store bolker. Skrivende: vis sammendrag (antall rader, sum timer per prosjekt) og få bekreftelse før POST.

### ✏️ Endre en eller flere timeføringer (timer, dato, aktivitet, kommentar)
- **Kall:** `GET /timesheet/entry/{id}`, `GET /timesheet/entry`, `PUT /timesheet/entry/{id}`, `PUT /timesheet/entry/list`
- **Nøkkelord:** endre timer, korrigere timer, rette timeføring, oppdatere timer, flytte timer til annet prosjekt, feilført time, update timesheet entry
- Hent føringen først (GET /timesheet/entry/{id} eller søk med dateFrom/dateTo) inkl. id,version,employee(id),project(id),activity(id),date,hours,comment,locked. Er locked=true (godkjent uke/måned eller fakturert) må uken/måneden gjenåpnes/oppheves først. PUT /timesheet/entry/{id} med HELT objekt inkl. version – felt som er med men tomme/0 blir nullet. Flere samtidig: PUT /timesheet/entry/list med liste av komplette objekter. Skrivende: bekreft med bruker.

### ✏️ Slette en feilført timeføring
- **Kall:** `GET /timesheet/entry`, `DELETE /timesheet/entry/{id}`
- **Nøkkelord:** slette timer, fjerne timeføring, slett time, delete hours, feilregistrert, dobbeltført
- Finn føringen med GET /timesheet/entry?employeeId=…&dateFrom=…&dateTo=…&fields=id,version,date,hours,project(number),activity(name),locked. DELETE /timesheet/entry/{id}?version=… Låste (godkjente/fakturerte) føringer kan ikke slettes før uke/måned er gjenåpnet; fakturerte timer må krediteres i stedet. Sletting er irreversibel – bekreft med bruker.

### Finne prosjekter og aktiviteter en ansatt kan føre timer på (inkl. nylig brukte)
- **Kall:** `GET /project/>forTimeSheet`, `GET /activity/>forTimeSheet`, `GET /timesheet/entry/>recentProjects`, `GET /timesheet/entry/>recentActivities`, `GET /activity`
- **Nøkkelord:** hvilke prosjekter, gyldige aktiviteter, aktivitetsliste, nylig brukte prosjekter, siste prosjekter, recent projects, recent activities, for timesheet, timekoder
- Gyldige for en dato: GET /project/>forTimeSheet?employeeId=…&date=… og GET /activity/>forTimeSheet?projectId=…&employeeId=…&date=… (projectId påkrevd; filterExistingHours=true skjuler aktiviteter med timer fra før). Nylig brukte: GET /timesheet/entry/>recentProjects?employeeId=… og GET /timesheet/entry/>recentActivities?projectId=…&employeeId=… (projectId påkrevd). Generelle/interne aktiviteter (ferie, sykdom, intern tid): GET /activity?isGeneral=true eller absence=true. Uten employeeId brukes token-eier. fields=id,number,name.

### Sjekke status på månedstimelister (levert/godkjent) for ansatte
- **Kall:** `GET /employee`, `GET /timesheet/month/byMonthNumberList`, `GET /timesheet/month/{id}`, `GET /timesheet/month/byMonthNumber`
- **Nøkkelord:** månedsstatus, manedsstatus, er timelisten godkjent, levert timeliste, godkjent måned, hvem har ikke levert, monthly status, timeliste status
- 1) Ansatt-id-er: GET /employee?fields=id (ev. departmentId). 2) GET /timesheet/month/byMonthNumberList?employeeIds=1,2,3&monthYearList=2026-08,2026-09 (begge påkrevd; format yyyy-MM) med fields=id,employee(id),monthYear,completed,approved,approvedDate,approvedUntilDate. completed=false betyr ikke levert. Enkeltpost: GET /timesheet/month/{id}. byMonthNumber (én måned) er DEPRECATED – bruk byMonthNumberList. Oppgi resultat som antall/initialer, ikke navn.

### Hente fleksisaldo, timesum, normaltid og feriesaldo for en måned
- **Kall:** `GET /timesheet/month/byMonthNumberList`, `GET /employee/standardTime/byDate`, `GET /timesheet/settings`
- **Nøkkelord:** fleksitid, fleksisaldo, flexsaldo, timebank, plusstimer, minustimer, normaltid, standardtid, feriesaldo, feriedager igjen, avspasering, overtid saldo
- GET /timesheet/month/byMonthNumberList?employeeIds=…&monthYearList=2026-09&fields=employee(id),monthYear,hourSummary(sumHours,standardTime,chargeableHours,nonChargeableHours,hoursWithPay),flexSummary(incomingHourBalance,outgoingHourBalance,change),vacationSummary(incomingVacationBalance,outgoingVacationBalance,vacationTakenThisYear). Fleks/feriesaldo er bare meningsfullt når det er slått på: sjekk GET /timesheet/settings (flexBalance, vacationBalance). Normaltid for ansatt: GET /employee/standardTime/byDate?employeeId=…&date=… Saldo per person er personopplysning – vis aggregert eller anonymisert.

### ✏️ Godkjenne månedstimelister (f.eks. før lønnskjøring)
- **Kall:** `GET /timesheet/month/byMonthNumberList`, `PUT /timesheet/month/:approve`
- **Nøkkelord:** godkjenne timeliste, godkjenne måned, godkjenne maned, attestere timer, approve month, timegodkjenning, godkjenne før lønn, lukke måned
- 1) Sjekk status med GET /timesheet/month/byMonthNumberList?employeeIds=…&monthYearList=yyyy-MM (completed/approved). 2) PUT /timesheet/month/:approve?employeeIds=1,2,3&monthYear=2026-09 (valgfritt approvedUntilDate=yyyy-MM-dd for delvis godkjenning; standard er slutten av måneden). Oppgi ALLTID employeeIds – uten blir token-eier brukt. Er id oppgitt ignoreres andre parametre. Ingen body. Godkjenning låser timene (locked=true). Krever at token-bruker har rett til å godkjenne timer (403 ellers). Skrivende: bekreft med bruker.

### ✏️ Levere (fullføre) månedstimeliste på vegne av ansatt
- **Kall:** `PUT /timesheet/month/:complete`, `GET /timesheet/month/byMonthNumberList`
- **Nøkkelord:** levere timeliste, fullføre måned, fullfore maned, sende inn timer, complete month, markere som ferdig
- PUT /timesheet/month/:complete?employeeIds=…&monthYear=yyyy-MM (eller id=… som overstyrer resten). Ingen body. Kontroller etterpå med GET /timesheet/month/byMonthNumberList at completed=true. Skrivende: bekreft med bruker.

### ✏️ Oppheve godkjenning eller gjenåpne en måned for korrigering
- **Kall:** `PUT /timesheet/month/:unapprove`, `PUT /timesheet/month/:reopen`, `GET /timesheet/month/byMonthNumberList`
- **Nøkkelord:** oppheve godkjenning, angre godkjenning, gjenåpne måned, gjenapne maned, låse opp timeliste, unapprove month, reopen month, korrigere godkjent timeliste
- Rekkefølge: først PUT /timesheet/month/:unapprove?employeeIds=…&monthYear=yyyy-MM (fjerner godkjenning), deretter ved behov PUT /timesheet/month/:reopen (fjerner levert-status slik at ansatt kan endre). Ingen body; id overstyrer andre parametre. Timer som allerede er fakturert eller lønnet forblir låst. Skrivende: bekreft med bruker.

### Sjekke ukestatus – hvem har ikke levert/fått godkjent timelisten for en uke
- **Kall:** `GET /timesheet/week`, `GET /employee`
- **Nøkkelord:** ukestatus, ukeliste, ikke levert, manglende timeliste, uke 39, week status, godkjent uke, purre timer
- GET /timesheet/week?weekYear=2026-39&employeeIds=… (weekYear = ISO år-ukenummer, f.eks. 2026-39) med fields=id,employee(id),year,week,completed,approved,approvedDate. Filtrer på approvedBy=<ansatt-id> for å se uker en bestemt leder har godkjent. Ansatte uten rad eller med completed=false har ikke levert. Oppgi som antall/initialer.

### ✏️ Levere, godkjenne, oppheve godkjenning eller gjenåpne en uke
- **Kall:** `PUT /timesheet/week/:complete`, `PUT /timesheet/week/:approve`, `PUT /timesheet/week/:unapprove`, `PUT /timesheet/week/:reopen`, `GET /timesheet/week`
- **Nøkkelord:** godkjenne uke, levere uke, fullføre uke, gjenåpne uke, oppheve godkjenning uke, approve week, complete week, reopen week, unapprove week
- Alle tar id ELLER (employeeId + weekYear, f.eks. 2026-39) som query, ingen body. Merk: uke-kallene tar én employeeId (ikke liste) – loop per ansatt. Flyt: :complete (levert) → :approve (godkjent). Tilbake: :unapprove → :reopen. Hent id/status via GET /timesheet/week. Skrivende: bekreft med bruker.

### ✏️ Stemple inn (starte stemplingsur)
- **Kall:** `GET /timesheet/settings`, `GET /timesheet/timeClock/present`, `PUT /timesheet/timeClock/:start`
- **Nøkkelord:** stemple inn, starte klokke, start stemplingsur, clock in, innstempling, starte arbeidsdag
- Sjekk at stemplingsur er aktivert (GET /timesheet/settings?fields=timeClock). Sjekk at ingen klokke allerede kjører: GET /timesheet/timeClock/present?employeeId=… Deretter PUT /timesheet/timeClock/:start?activityId=… (påkrevd) &projectId=… (for prosjektaktivitet) &employeeId=… (standard token-eier – oppgi alltid) &date=… (standard i dag) &lunchBreakDuration=… &comment=… Ingen body. NB: comment overskriver kommentaren på en eksisterende timeføring hvis klokka startes på den. Skrivende: bekreft med bruker.

### ✏️ Stemple ut (stoppe stemplingsur)
- **Kall:** `GET /timesheet/timeClock/present`, `PUT /timesheet/timeClock/{id}/:stop`
- **Nøkkelord:** stemple ut, stoppe klokke, stopp stemplingsur, clock out, utstempling, avslutte arbeidsdag
- Finn kjørende klokke: GET /timesheet/timeClock/present?employeeId=…&fields=id,version,date,timeStart,project(id),activity(id). PUT /timesheet/timeClock/{id}/:stop?version=…&comment=… (kommentar kan være påkrevd hvis firmaet krever kommentar). Timene legges automatisk på timeføringen. Skrivende: bekreft med bruker.

### ✏️ Se og korrigere stemplinger (hvem er stemplet inn, start-/stopptid, lunsj)
- **Kall:** `GET /timesheet/timeClock`, `GET /timesheet/timeClock/{id}`, `PUT /timesheet/timeClock/{id}`
- **Nøkkelord:** stemplinger, hvem er på jobb, stemplet inn nå, kjørende klokker, korrigere stempling, endre starttid, time clock entries, isrunning
- Søk: GET /timesheet/timeClock?dateFrom=…&dateTo=…(eksklusiv)&isRunning=true/false&employeeId=…&projectId=…&hourId=<timeføring-id> med fields=id,version,employee(id),date,timeStart,timeStop,lunchBreakDuration,timesheetEntry(id). Korriger: hent med GET /timesheet/timeClock/{id} og send komplett objekt med version til PUT /timesheet/timeClock/{id}. Oppmøtedata er personopplysninger – vis antall/initialer. Skrivende ved PUT: bekreft.

### ✏️ Registrere planlagt ferie/fri eller allokerte timer for ansatte
- **Kall:** `GET /activity`, `POST /timesheet/allocated`, `POST /timesheet/allocated/list`
- **Nøkkelord:** registrere ferie, legge inn ferie, planlagt ferie, allokere timer, ressursplan, fri, feriesøknad, allocated hours, vacation planning
- Finn firmaets interne ferieaktivitet: GET /activity?absence=true (eller isGeneral=true) &fields=id,name. POST /timesheet/allocated body {employee:{id}, activity:{id}, project:{id}(valgfri), date, hours, managerComment}. Flere ansatte/dager: POST /timesheet/allocated/list. Kun én per ansatt/dato/aktivitet/prosjekt; kun ferie/fri-timer kan ha kommentar; kommentar sender varsel til ansatt. Skrivende: bekreft med bruker.

### Se allokerte timer og ferieplaner/feriesøknader
- **Kall:** `GET /timesheet/allocated`, `GET /timesheet/allocated/{id}`
- **Nøkkelord:** allokerte timer, ferieplan, hvem har ferie, feriesøknader, ventende ferie, ikke godkjent ferie, allocated
- GET /timesheet/allocated?dateFrom=…&dateTo=…(eksklusiv)&employeeIds=…&projectIds=…&activityIds=… med fields=id,version,employee(id),activity(name),date,hours,isApproved. isApproved=false = ikke godkjent ennå. Enkeltpost: GET /timesheet/allocated/{id}. Fravær er personopplysning – oppgi aggregert/initialer.

### ✏️ Godkjenne eller oppheve godkjenning av feriesøknader (allokerte ferietimer)
- **Kall:** `GET /timesheet/allocated`, `PUT /timesheet/allocated/{id}/:approve`, `PUT /timesheet/allocated/:approveList`, `PUT /timesheet/allocated/{id}/:unapprove`, `PUT /timesheet/allocated/:unapproveList`, `DELETE /timesheet/allocated/{id}`
- **Nøkkelord:** godkjenne ferie, avvise ferie, feriegodkjenning, approve vacation, unapprove, godkjenne fri, ferieønske, oppheve godkjenning ferie, feriesoknad
- Kun for allokerte timer på firmaets interne ferie-/fri-aktivitet. Enkelt: PUT /timesheet/allocated/{id}/:approve?managerComment=… Mange: PUT /timesheet/allocated/:approveList?ids=… ELLER employeeIds=…&dateFrom=…&dateTo=…(eksklusiv) – ids overstyrer resten, og uten ids OG uten employeeIds gjelder kallet bare token-eier. Godkjente timer kopieres inn i timelisten bare hvis uke/måned ikke er godkjent og ingen stemplingsur kjører. Oppheve/avvise: :unapprove / :unapproveList (samme parametre); for å fjerne søknaden helt: DELETE /timesheet/allocated/{id}. Ingen body. Ansatt får varsel ved endring – bekreft med bruker før kall.

### ✏️ Endre eller slette allokerte timer
- **Kall:** `GET /timesheet/allocated/{id}`, `PUT /timesheet/allocated/{id}`, `PUT /timesheet/allocated/list`, `DELETE /timesheet/allocated/{id}`
- **Nøkkelord:** endre ferie, slette ferie, flytte ferie, endre allokering, slette allokerte timer, update allocated
- Hent posten (GET /timesheet/allocated/{id}) og send HELT objekt med version til PUT /timesheet/allocated/{id} – felt som er tomme/0 blir nullet. Flere: PUT /timesheet/allocated/list. Slett: DELETE /timesheet/allocated/{id}. Endret kommentar sender varsel til ansatt. Skrivende: bekreft med bruker.

### ✏️ Vedlikeholde firmafridager (inneklemte dager, julaften, nyttårsaften)
- **Kall:** `GET /timesheet/companyHoliday`, `GET /timesheet/companyHoliday/{id}`, `POST /timesheet/companyHoliday`, `PUT /timesheet/companyHoliday/{id}`, `DELETE /timesheet/companyHoliday/{id}`
- **Nøkkelord:** firmafridag, inneklemt dag, julaften fri, halv dag, helligdager, fridager i år, company holiday, normaltid, røde dager
- [BETA] Se: GET /timesheet/companyHoliday?years=2026&fields=id,version,date,percentage. Opprett: POST /timesheet/companyHoliday {date:'2026-12-24', percentage:100} (50 = halv dag). Endre: PUT /timesheet/companyHoliday/{id} med version. Slett: DELETE /timesheet/companyHoliday/{id}. Påvirker normaltid/fleks for alle ansatte. Skrivende kall: bekreft med bruker.

### ✏️ Registrere lønnsarter/tillegg i timelisten (overtid, kveldstillegg, helgetillegg)
- **Kall:** `GET /salary/type`, `GET /timesheet/salaryTypeSpecification`, `GET /timesheet/salaryTypeSpecification/{id}`, `POST /timesheet/salaryTypeSpecification`, `PUT /timesheet/salaryTypeSpecification/{id}`, `DELETE /timesheet/salaryTypeSpecification/{id}`
- **Nøkkelord:** overtid, registrere overtid, tillegg i timeliste, kveldstillegg, helgetillegg, lønnsart timeliste, variabel lønn, salary type specification
- [BETA] 1) Finn lønnsart som kan brukes i timelisten: GET /salary/type?showInTimesheet=true&fields=id,number,name. 2) POST /timesheet/salaryTypeSpecification {employee:{id}, salaryType:{id}, date, count, description}. Kun én per ansatt/dato/lønnsart. Se eksisterende: GET /timesheet/salaryTypeSpecification?employeeId=…&dateFrom=…&dateTo=… Endre/slett: PUT/DELETE /timesheet/salaryTypeSpecification/{id} (hent version først). Lønnsdata er personopplysninger – vis aggregert. Skrivende: bekreft med bruker.

### ✏️ Registrere prosjektrelaterte lønnsarter/tillegg (tillegg per prosjekt og aktivitet)
- **Kall:** `GET /salary/type`, `GET /timesheet/salaryProjectTypeSpecification`, `GET /timesheet/salaryProjectTypeSpecification/{id}`, `POST /timesheet/salaryProjectTypeSpecification`, `PUT /timesheet/salaryProjectTypeSpecification/{id}`, `DELETE /timesheet/salaryProjectTypeSpecification/{id}`
- **Nøkkelord:** prosjekttillegg, overtid på prosjekt, lønnsart prosjekt, tillegg prosjekt, project salary type, prosjektlønn
- 1) Lønnsart: GET /salary/type?showInTimesheet=true&fields=id,number,name. 2) POST /timesheet/salaryProjectTypeSpecification {employee:{id}, project:{id}, activity:{id}, salaryType:{id}, date, count, description}. Søk: GET /timesheet/salaryProjectTypeSpecification?employeeId=…&projectId=…&activityId=…&dateFrom=…&dateTo=…(eksklusiv); includeNotConnectedToActivities=true (sammen med activityId) tar med de som ikke er koblet til aktivitet. wagePayment satt = tillegget er tatt med i en lønnsslipp – ikke endre/slette slike uten å avklare lønnen. Endre/slett: PUT/DELETE /timesheet/salaryProjectTypeSpecification/{id} (hent version først). Lønnsdata er personopplysninger – vis aggregert. Skrivende: bekreft med bruker.

### ✏️ Hente lønnsgrunnlag fra timelister før lønnskjøring (timelønn, overtid, tillegg) og lage lønnsutkast
- **Kall:** `GET /timesheet/month/byMonthNumberList`, `GET /timesheet/entry`, `GET /timesheet/salaryTypeSpecification`, `GET /timesheet/salaryProjectTypeSpecification`, `POST /salary/transaction`
- **Nøkkelord:** lønnsgrunnlag, lonnsgrunnlag, timer til lønn, timelønnede, timelonn, overtid til utbetaling, lønnskjøring, lønnsutkast, lonnsutkast, variabel lønn
- 1) Sjekk at månedene er godkjent: GET /timesheet/month/byMonthNumberList (approved=true; hourSummary.hoursWithPay/hourlyWageHoursWithPay gir timer med lønn). 2) Detaljer ved behov: GET /timesheet/entry (dateFrom/dateTo) og tillegg via GET /timesheet/salaryTypeSpecification og GET /timesheet/salaryProjectTypeSpecification (dateFrom/dateTo, employeeId). 3) Lønnsutkast (lønn-gruppen): POST /salary/transaction med payslips/specifications – IKKE godkjenn/utbetal. Behandle lønnsdata kun lokalt, vis aggregat. Skrivende steg 3: bekreft med bruker.

### Lese timelisteinnstillingene for firmaet
- **Kall:** `GET /timesheet/settings`
- **Nøkkelord:** timelisteinnstillinger, er stemplingsur på, krav om kommentar, fleksitid aktivert, feriesaldo aktivert, standard aktivitet, timesheet settings
- [BETA] GET /timesheet/settings?fields=timeClock,timesheetCompleted,flexBalance,vacationBalance,showDetailedTimeSheet,requireCommentsOnRegisteredHoursAllProjects,defaultProjectActivity(id,name). Kun lesing – innstillingene kan ikke endres via API. Bruk før føring (påkrevd kommentar?), stempling (timeClock på?) og fleks-/feriesaldo-rapporter.

### Sammenligne budsjetterte og faktiske timer på prosjekt
- **Kall:** `GET /project/capacityPlan/budget`, `GET /timesheet/entry`, `GET /project/{id}/period/hourlistReport`
- **Nøkkelord:** budsjett timer, timebudsjett, budsjett mot faktisk, avvik timer, kapasitetsplan, overskridelse, prosjektkontroll, capacity plan
- GET /project/capacityPlan/budget?projectId=…&periodStart=…&periodEnd=…(eksklusiv)&periodType=MONTH (HOUR|DAY|WEEK|MONTH, alle tre påkrevd) gir budsjetterte og førte timer per aktivitet og ansatt. Suppler med GET /project/{id}/period/hourlistReport eller GET /timesheet/entry?projectId=… (dateFrom/dateTo). Rapporter per aktivitet/prosjekt, ikke per navngitt ansatt.

### Kontrollere fravær (ferie, sykdom, permisjon) i timelistene mot permisjonsregistreringer
- **Kall:** `GET /activity`, `GET /timesheet/entry`, `GET /employee/employment`, `GET /employee/employment/leaveOfAbsence`
- **Nøkkelord:** fravær, fravaer, sykefravær, sykefravaer, egenmelding, permisjon, ferie tatt, fraværsaktivitet, absence, leave of absence
- 1) Fraværsaktiviteter: GET /activity?absence=true&fields=id,name. 2) Timer på dem: GET /timesheet/entry?activityId=<ids>&dateFrom=…&dateTo=…(eksklusiv)&fields=employee(id),date,hours,activity(name). 3) Permisjoner: finn arbeidsforhold-id med GET /employee/employment?employeeId=…&fields=id, deretter GET /employee/employment/leaveOfAbsence?employmentIds=…&date=… (date standard i dag). Sykefravær er helseopplysninger (særlig kategori) – hent kun når oppgaven krever det, behandle lokalt og oppgi bare aggregater.

### Se timepris, internkost og normalarbeidstid for ansatte (grunnlag for timeverdi og fleks)
- **Kall:** `GET /employee/hourlyCostAndRate`, `GET /employee/standardTime`, `GET /employee/standardTime/byDate`, `GET /project/hourlyRates`
- **Nøkkelord:** timepris, timesats, kostpris, internkost, timekost, hourly rate, hourly cost, normalarbeidstid, normaltid, arbeidstid per dag, standard time, prosjektpris, timepriser prosjekt
- Timepris/kostpris per ansatt (gyldig fra dato): GET /employee/hourlyCostAndRate?employeeId=…&fields=date,rate,budgetRate,hourCostRate. Normalarbeidstid: GET /employee/standardTime?employeeId=…&fields=fromDate,hoursPerDay eller GET /employee/standardTime/byDate?employeeId=…&date=… Prosjektets timepriser: GET /project/hourlyRates?projectId=…&startDateFrom=…&fields=* (type: TYPE_PREDEFINED_HOURLY_RATES|TYPE_PROJECT_SPECIFIC_HOURLY_RATES|TYPE_FIXED_HOURLY_RATE). Uten employeeId brukes token-eier. Timesats/kost per person er personopplysning – vis aggregert. Nye satser (POST /employee/hourlyCostAndRate, POST /employee/standardTime) er skrivende og hører til ansatt-gruppen.

**Fallgruver:**
- GET /timesheet/entry krever dateFrom og dateTo; dateTo er eksklusiv (til og IKKE med). Hele september = dateFrom=2026-09-01&dateTo=2026-10-01. Svaret har sumAllHours i tillegg til values.
- GET /timesheet/entry/>totalHours bruker startDate/endDate (ikke dateFrom/dateTo), endDate eksklusiv; standard er token-eier, startDate=i dag og endDate=i morgen.
- Stier med '>' (/timesheet/entry/>totalHours, >recentProjects, >recentActivities, /project/>forTimeSheet, /activity/>forTimeSheet) må quotes i shell og ev. URL-encodes som %3E.
- Handlingskall med ':' (/:approve, /:complete, /:unapprove, /:reopen, /:start, /:stop, /:approveList, /:unapproveList) er PUT med query-parametre og ingen body.
- Månedskall bruker monthYear=yyyy-MM (f.eks. 2026-09) og employeeIds (liste); ukekall bruker weekYear=ISO år-uke (f.eks. 2026-39) og én employeeId. Er id oppgitt ignoreres øvrige parametre.
- Uten employeeId/employeeIds brukes token-eieren (ofte regnskapsfører-/integrasjonsbrukeren) – oppgi alltid ansatt eksplisitt ved godkjenning, levering, stempling og summering.
- Kun én timeføring per ansatt/dato/aktivitet/prosjekt (også for allokerte timer og én lønnsart per ansatt/dato/lønnsart) – POST feiler med 422 hvis den finnes; oppdater med PUT i stedet.
- PUT på timesheet/entry, allocated og timeClock: felt som er med men ikke satt eller 0 blir nullet. Hent objektet først og send komplett objekt med version.
- Låste timeføringer (locked=true: godkjent uke/måned eller fakturert) kan ikke endres/slettes. Opphev godkjenning (:unapprove) og gjenåpne (:reopen) først; fakturerte timer må krediteres.
- Prosjekt/aktivitet må være gyldig for ansatt og dato (åpent prosjekt, ansatt deltaker, aktivitet koblet til prosjektet). Bruk /project/>forTimeSheet og /activity/>forTimeSheet for å unngå 422. Generelle aktiviteter (ferie, sykdom, intern tid) føres uten project.
- chargeable, chargeableHours, hourlyRate, hourlyCost og locked er skrivebeskyttet; fakturerbarhet styres av aktivitet/prosjekt. projectChargeableHours kan settes.
- /timesheet/allocated/:approve og :unapprove gjelder kun firmaets interne ferie-/fri-aktivitet. Godkjente timer kopieres til timelisten bare hvis uke/måned ikke er godkjent og ingen stemplingsur kjører. Endringer sender varsel til ansatt (bivirkning).
- Stemplingsur: :start krever activityId (og projectId for prosjektaktivitet), bare én klokke kan kjøre per ansatt; :stop krever id fra GET /timesheet/timeClock/present. Kommentar kan være obligatorisk (se /timesheet/settings). Stemplingsur må være aktivert i firmaet.
- BETA-endepunkter: /timesheet/companyHoliday, /timesheet/salaryTypeSpecification og /timesheet/settings kan endres uten varsel. /timesheet/settings er kun lesbar. /timesheet/month/byMonthNumber er DEPRECATED – bruk byMonthNumberList.
- 403 betyr normalt at modulen Timeliste/Prosjekt ikke er aktiv hos klienten, eller at token-brukeren mangler rettighet til å se/godkjenne andres timer. 422 = valideringsfeil (ugyldig kombinasjon, låst periode, duplikat, manglende kommentar).
- Fleks- og feriesaldo i MonthlyStatus (flexSummary, vacationSummary) er bare meningsfulle når flexBalance/vacationBalance er slått på i /timesheet/settings.
- GDPR: alle /timesheet-endepunkter er personopplysninger (timer, fravær, stempling, lønnsarter). Bruk alltid minimal fields= (employee(id), ikke navn/e-post), vis aggregater eller 'ansatt 1/2'/initialer, og ikke lagre radene i filer. Sykefravær/permisjon er særlig sensitive.
- Alle skrivende kall (føre/endre/slette timer, godkjenne/levere/gjenåpne uke eller måned, stemple, ferie- og lønnsartregistrering) krever eksplisitt bekreftelse fra bruker og at klienten er navngitt.
- Listekall har count=1000 som standard (from=0). Sjekk fullResultSize og paginer med from/count ved store uttrekk (mange ansatte/lange perioder).
- GET /timesheet/month/byMonthNumberList krever både employeeIds og monthYearList (yyyy-MM, kommaseparert) selv om beskrivelsen nevner token-eier som standard.
- PUT /timesheet/allocated/:approveList og :unapproveList: ids overstyrer alt annet; uten ids og uten employeeIds gjelder kallet bare token-eier.
- dateTo er eksklusiv også på /timesheet/allocated, /timesheet/timeClock, /timesheet/salaryTypeSpecification og /timesheet/salaryProjectTypeSpecification (der er dateFrom/dateTo valgfrie).
- PUT /timesheet/timeClock/:start med comment overskriver kommentaren på en eksisterende timeføring som klokka startes på.

## Reiseregninger og utlegg

### Liste reiseregninger og utlegg for en periode, ansatt, prosjekt eller avdeling (inkl. sum reisekostnader)
- **Kall:** `GET /travelExpense`, `GET /project`, `GET /department`, `GET /ledger/posting`
- **Nøkkelord:** liste reiseregninger, søk reiseregning, sok reiseregning, oversikt reiseregninger, utlegg i perioden, reiseregninger per ansatt, reiseregninger på prosjekt, reiseregninger avdeling, travel expenses list, reisekostnader prosjekt, reisekostnader avdeling, sum reiseregninger, reiseutgifter i år, kostnader per prosjekt, rapport reise, fakturerbare reisekostnader
- GET /travelExpense med filtre employeeId, departmentId, projectId, projectManagerId, departureDateFrom (fra og med) og returnDateTo (til og UTEN), og evt. state (ALL|OPEN|DELIVERED|APPROVED|REJECTED|SALARY_PAID). Ingen påkrevde parametere, men avgrens alltid. Bruk minimal fields=, f.eks. fields=id,number,title,state,amount,paymentAmount,date,travelDetails(departureDate,returnDate,destination,isForeignTravel),project(id,number),department(id). Utlegg har ikke travelDetails. Unngå employee(*) – bruk employee(id) og vis 'ansatt 1/2' i svar (GDPR). Paginer med from/count. Rapport per prosjekt/avdeling: finn id med GET /project?number=.. / GET /department?name=.., hent med projectId/departmentId og state=ALL, legg til fields amount,chargeableAmount,paymentAmount,isChargeable og summer i koden. For bokførte tall: GET /ledger/posting med dateFrom/dateTo (begge påkrevd) + projectId/departmentId. NB: GET /travelExpense har ikke filter på id-liste, nummer eller bilagsdato – søk på nummer må filtreres i koden. departureDateFrom/returnDateTo gjelder reisedatoene; ansattutlegg har ingen travelDetails og kan falle utenfor datofilteret – hent utlegg uten datofilter og filtrer på feltet date i koden.

### Hente én reiseregning med alle linjer (diett, km, nattillegg, kostnader)
- **Kall:** `GET /travelExpense/{id}`, `GET /travelExpense/cost`, `GET /travelExpense/perDiemCompensation`, `GET /travelExpense/mileageAllowance`, `GET /travelExpense/accommodationAllowance`
- **Nøkkelord:** vis reiseregning, detaljer reiseregning, hent reiseregning, innhold reiseregning, linjer reiseregning, travel expense details
- GET /travelExpense/{id}?fields=id,number,title,state,amount,paymentAmount,travelAdvance,travelDetails(*),perDiemCompensations(*),mileageAllowances(*),accommodationAllowances(*),costs(*),voucher(id,number),project(id,number) henter alt i ett kall. Alternativt søk linjer per type med travelExpenseId=<id> på /cost, /perDiemCompensation, /mileageAllowance og /accommodationAllowance. Begrens persondata med fields= (GDPR).

### Finne reiseregninger som venter på godkjenning eller bokføring
- **Kall:** `GET /travelExpense`
- **Nøkkelord:** til godkjenning, venter godkjenning, levert ikke godkjent, ikke bokført, ubehandlede reiseregninger, attestere, pending approval, godkjenningskø
- Levert, ikke godkjent: GET /travelExpense?state=DELIVERED. Godkjent, men ikke bokført: GET /travelExpense?state=APPROVED&fields=id,number,state,amount,voucher(id),approvedDate og filtrer på voucher tom. Avvist: state=REJECTED (rejectedComment er med i objektet). Kombiner med departureDateFrom/returnDateTo for perioden. Vis kun aggregater/initialer (GDPR).

### ✏️ Opprette ny reiseregning for en ansatt
- **Kall:** `GET /employee`, `GET /project`, `GET /department`, `POST /travelExpense`
- **Nøkkelord:** ny reiseregning, opprett reiseregning, registrer reise, lag reiseregning, tjenestereise, reise med overnatting, dagsreise, create travel expense
- 1) Finn ansatt-id: GET /employee?employeeNumber=<nr>&fields=id,employeeNumber (unngå å hente navn/persondata unødig). 2) Evt. GET /project?fields=id,number,name og GET /department?fields=id,name. 3) POST /travelExpense med body {employee:{id}, title, project:{id}, department:{id}, travelDetails:{departureDate:'yyyy-MM-dd', returnDate, departureTime:'HH:mm', returnTime, departureFrom, destination, purpose, isForeignTravel, isDayTrip, isCompensationFromRates:true}, travelAdvance}. Diett/kostnader kan legges inn i samme kall (perDiemCompensations, costs) eller etterpå via egne endepunkter. Kjøregodtgjørelse og nattillegg MÅ legges inn via egne endepunkter (read-only på hovedobjektet). Skrivende – krever brukerens bekreftelse.

### ✏️ Registrere ansattutlegg (utlegg uten reise) med kvittering
- **Kall:** `GET /travelExpense/costCategory`, `GET /travelExpense/paymentType`, `POST /travelExpense`, `POST /travelExpense/cost`, `POST /travelExpense/{travelExpenseId}/attachment`
- **Nøkkelord:** ansattutlegg, utlegg, registrer utlegg, refusjon utlegg, privat betalt, kjøpt privat, kjopt privat, kvittering utlegg, employee expense, refundere ansatt
- Utlegg er en TravelExpense UTEN travelDetails. 1) GET /travelExpense/costCategory?showOnEmployeeExpenses=true&isInactive=false&fields=id,description,account(number),vatType(id,number) for utgiftstype. 2) GET /travelExpense/paymentType?showOnEmployeeExpenses=true&fields=id,description,account(number) (f.eks. 'betalt privat'). 3) POST /travelExpense {employee:{id}, title} uten travelDetails. 4) POST /travelExpense/cost {travelExpense:{id}, costCategory:{id}, paymentType:{id}, date, amountCurrencyIncVat, currency:{id}, vatType:{id}, comments}. 5) Last opp kvittering: POST /travelExpense/{travelExpenseId}/attachment (multipart, felt 'file'). Skrivende – bekreft først.

### ✏️ Legge til kostnad (hotell, fly, taxi, parkering) på en reiseregning
- **Kall:** `GET /travelExpense/costCategory`, `GET /travelExpense/paymentType`, `GET /ledger/vatType`, `GET /currency`, `POST /travelExpense/cost`
- **Nøkkelord:** legg til kostnad, hotellkostnad, flybillett, taxi, parkering, bompenger, legitimert overnatting, utgift på reise, utenlandsk valuta kvittering, add cost
- Finn costCategory (GET /travelExpense/costCategory?description=<tekst>&isInactive=false (description = inneholder; query= er eksakt treff)), paymentType (GET /travelExpense/paymentType) og evt. mva-type (GET /ledger/vatType?number=...) og valuta (GET /currency?code=EUR). POST /travelExpense/cost med {travelExpense:{id}, costCategory:{id}, paymentType:{id}, date, amountCurrencyIncVat (beløp i valuta inkl. mva), currency:{id}, rate (kurs ved valuta), amountNOKInclVAT, vatType:{id}, comments, isChargeable}. Mva-kode styres ofte av kategorien (isVatLocked). Reiseregningen må være OPEN. Skrivende – bekreft først.

### ✏️ Endre, flytte eller slette kostnadslinjer på reiseregning/utlegg
- **Kall:** `GET /travelExpense/cost`, `GET /travelExpense/cost/{id}`, `PUT /travelExpense/cost/{id}`, `PUT /travelExpense/cost/list`, `DELETE /travelExpense/cost/{id}`
- **Nøkkelord:** endre kostnad, rett beløp, korriger utgift, slett kostnad, fjern kvitteringslinje, masseoppdater kostnader, update cost, delete cost
- Finn linjene: GET /travelExpense/cost?travelExpenseId=<id>&fields=id,version,date,amountCurrencyIncVat,amountNOKInclVAT,costCategory(id,description),paymentType(id),vatType(id,number). Filtre: vatTypeId, currencyId, amountFrom/amountTo, rateFrom/rateTo. Oppdater én: PUT /travelExpense/cost/{id} med id+version og endrede felt. Flere samtidig: PUT /travelExpense/cost/list (array av Cost). Slett: DELETE /travelExpense/cost/{id}. Kun mulig mens reiseregningen er OPEN (bruk :undeliver/:unapprove først). Skrivende – bekreft først.

### ✏️ Registrere deltakere på representasjon/bevertning
- **Kall:** `POST /travelExpense/costParticipant`, `POST /travelExpense/costParticipant/list`, `POST /travelExpense/costParticipant/createCostParticipantAdvanced`, `GET /travelExpense/costParticipant/{costId}/costParticipants`, `GET /travelExpense/costParticipant/{id}`, `DELETE /travelExpense/costParticipant/{id}`, `DELETE /travelExpense/costParticipant/list`
- **Nøkkelord:** deltakere representasjon, hvem deltok, kundemiddag deltakere, bevertning deltakere, legg til gjester, participants, representasjon dokumentasjon
- Kostnaden må finnes først (POST /travelExpense/cost). Enkeltdeltaker: POST /travelExpense/costParticipant {cost:{id}, displayName, employeeId (valgfritt)}. Flere: POST /travelExpense/costParticipant/list. Med query-parametere: POST /travelExpense/costParticipant/createCostParticipantAdvanced?costId=..&employeeId=..&displayName=.. (employeeId påkrevd – bruk 0 for eksterne). Les: GET /travelExpense/costParticipant/{costId}/costParticipants. Slett: DELETE /{id} eller DELETE /list (body med objekter). Deltakernavn er persondata – vis ikke fulle navn i svar. Skrivende – bekreft først.

### ✏️ Registrere kjøregodtgjørelse (kilometergodtgjørelse) med egen bil
- **Kall:** `GET /travelExpense/rateCategory`, `GET /travelExpense/rate`, `POST /travelExpense/mileageAllowance`
- **Nøkkelord:** kjøregodtgjørelse, kilometergodtgjørelse, km-godtgjørelse, bilgodtgjørelse, kjørte km, kjøring egen bil, elbil sats, firmabil, bompenger kjøring, mileage allowance
- 1) Finn gyldig satskategori for kjøredatoen: GET /travelExpense/rateCategory?type=MILEAGE_ALLOWANCE&dateFrom=<dato>&dateTo=<dato+1>&fields=id,name,fromDate,toDate,ameldingWageCode,wageCodeNumber (velg f.eks. bil/elbil). 2) Evt. GET /travelExpense/rate?rateCategoryId=..&type=MILEAGE_ALLOWANCE&fields=id,rate for sats. 3) POST /travelExpense/mileageAllowance {travelExpense:{id}, rateCategory:{id}, rateType:{id}, date, departureLocation, destination, km, isCompanyCar, vehicleType (default 0), tollCost (Cost for bompenger), autoPass, rushHour}. Rate/amount beregnes normalt fra sats når isCompensationFromRates=true. Kjøregodtgjørelse kan IKKE sendes inn via POST /travelExpense (read-only der). Skrivende – bekreft først.

### ✏️ Hente, endre eller slette kjøregodtgjørelse
- **Kall:** `GET /travelExpense/mileageAllowance`, `GET /travelExpense/mileageAllowance/{id}`, `PUT /travelExpense/mileageAllowance/{id}`, `DELETE /travelExpense/mileageAllowance/{id}`
- **Nøkkelord:** endre km, rett kilometer, slett kjøregodtgjørelse, søk kjøregodtgjørelse, km per ansatt, kjørte kilometer i år, update mileage
- Søk: GET /travelExpense/mileageAllowance med travelExpenseId, dateFrom/dateTo, kmFrom/kmTo, rateFrom/rateTo, amountFrom/amountTo, departureLocation, destination, isCompanyCar, rateCategoryId; fields=id,version,date,km,rate,amount,departureLocation,destination,travelExpense(id). Summer km/beløp for rapport (aggreger per ansatt-id, ikke navn). Endre: PUT /travelExpense/mileageAllowance/{id} med id+version. Slett: DELETE /{id}. Endring krever at reiseregningen er OPEN. PUT/DELETE er skrivende – bekreft først.

### ✏️ Legge til passasjerer (passasjertillegg) og kjørerute/mellomstopp på kjøregodtgjørelse
- **Kall:** `POST /travelExpense/passenger`, `POST /travelExpense/passenger/list`, `GET /travelExpense/passenger`, `GET /travelExpense/passenger/{id}`, `PUT /travelExpense/passenger/{id}`, `DELETE /travelExpense/passenger/{id}`, `DELETE /travelExpense/passenger/list`, `POST /travelExpense/drivingStop`, `GET /travelExpense/drivingStop/{id}`, `DELETE /travelExpense/drivingStop/{id}`
- **Nøkkelord:** passasjertillegg, passasjer, samkjøring, kollega med i bilen, flere i bilen, passenger supplement, kjørerute, mellomstopp, stopp underveis, rute, via, kjørebok detaljer, driving stops
- Kjøregodtgjørelsen må finnes (POST /travelExpense/mileageAllowance). POST /travelExpense/passenger {name, mileageAllowance:{id}} (eller /passenger/list for flere). Selve passasjertillegget (og tilhengertillegg) er egne MileageAllowance-linjer koblet i feltene passengerSupplement/trailerSupplement på hovedlinjen; Passenger-objektet dokumenterer hvem som satt på. Søk: GET /travelExpense/passenger?mileageAllowance=<id>. Endre: PUT /{id}. Slett: DELETE /{id} eller DELETE /list. Passasjernavn er persondata – ikke vis i svar. Kjørerute: POST /travelExpense/drivingStop {mileageAllowance:{id}, locationName, latitude, longitude, sortIndex, type}; hent med GET /travelExpense/drivingStop/{id} eller mileageAllowance.drivingStops; ingen søk/PUT – slett (DELETE /{id}) og opprett på nytt. Skrivende – bekreft først.

### ✏️ Registrere diett (kostgodtgjørelse) på innenlandsreise
- **Kall:** `GET /travelExpense/rateCategoryGroup`, `GET /travelExpense/rateCategory`, `GET /travelExpense/rate`, `POST /travelExpense/perDiemCompensation`
- **Nøkkelord:** diett, kostgodtgjørelse, diett innland, døgndiett, dagsdiett, reise med overnatting, hotell diett, per diem, diett etter statens satser
- 1) Satsgruppe for året: GET /travelExpense/rateCategoryGroup?isForeignTravel=false&dateFrom=<avreise>&dateTo=<retur+1>. 2) Satskategori: GET /travelExpense/rateCategory?type=PER_DIEM&isValidDomestic=true&isValidDayTrip=<true/false>&isRequiresOvernightAccommodation=..&dateFrom..&dateTo..&fields=id,name,fromDate,toDate. 3) Evt. sats: GET /travelExpense/rate?rateCategoryId=..&fields=id,rate,breakfastDeductionRate,lunchDeductionRate,dinnerDeductionRate. 4) POST /travelExpense/perDiemCompensation {travelExpense:{id}, rateCategory:{id}, rateType:{id}, overnightAccommodation (NONE|HOTEL|BOARDING_HOUSE_WITHOUT_COOKING|BOARDING_HOUSE_WITH_COOKING), location, count (antall døgn/dager), isDeductionForBreakfast, isDeductionForLunch, isDeductionForDinner}. Reisen må ha travelDetails med avreise/retur-tid. Skrivende – bekreft først.

### ✏️ Registrere utenlandsdiett (diett i utlandet) og finne riktig land/sone
- **Kall:** `GET /travelExpense/zone`, `GET /travelExpense/rateCategoryGroup`, `GET /travelExpense/rateCategory`, `GET /travelExpense/rate`, `POST /travelExpense/perDiemCompensation`, `GET /travelExpense/zone/{id}`
- **Nøkkelord:** utenlandsdiett, diett utland, utenlandsreise, reise til utlandet, landkode, sone, utenlandssats, foreign per diem, hvilken sone, land reise, utenlands sone, soner statens satser, zone lookup
- 1) Reisen må ha travelDetails.isForeignTravel=true. 2) Finn sone/land: GET /travelExpense/zone?query=<land> eller code=<ISO-kode>&date=<reisedato>&fields=id,countryCode,zoneName,currencyId. 3) GET /travelExpense/rateCategoryGroup?isForeignTravel=true&dateFrom..&dateTo.. og GET /travelExpense/rateCategory?type=PER_DIEM&requiresZone=true&dateFrom..&dateTo... 4) POST /travelExpense/perDiemCompensation {travelExpense:{id}, rateCategory:{id}, countryCode:'SE', travelExpenseZoneId:<id>, overnightAccommodation, count, location, måltidstrekk-felt}. Sats avhenger av sone og dato. Skrivende – bekreft først. Kun oppslag av sone: GET /travelExpense/zone?query=<land/by>&date=<reisedato>&isDisabled=false&fields=id,countryCode,zoneName,governmentName,continent,currencyId,fromDate,toDate (code= filtrerer på landkode), evt. GET /travelExpense/zone/{id}. Soner er versjonert på dato.

### ✏️ Hente, endre eller slette diett og måltidstrekk
- **Kall:** `GET /travelExpense/perDiemCompensation`, `GET /travelExpense/perDiemCompensation/{id}`, `PUT /travelExpense/perDiemCompensation/{id}`, `DELETE /travelExpense/perDiemCompensation/{id}`
- **Nøkkelord:** endre diett, måltidstrekk, frokosttrekk, trekk for frokost, lunsj dekket, middag dekket, slett diett, søk diett, diett i perioden
- Søk: GET /travelExpense/perDiemCompensation med travelExpenseId, rateCategoryId, rateTypeId, overnightAccommodation, countFrom/countTo, amountFrom/amountTo, location, isDeductionForBreakfast, isLunchDeduction, isDinnerDeduction (NB: søkeparameterne heter isLunchDeduction/isDinnerDeduction, mens body-feltene heter isDeductionForLunch/isDeductionForDinner). Endre: PUT /travelExpense/perDiemCompensation/{id} med id+version (f.eks. sette isDeductionForBreakfast=true når hotellfrokost var inkludert). Slett: DELETE /{id}. Kun når reiseregningen er OPEN. PUT/DELETE er skrivende – bekreft først.

### ✏️ Registrere, endre eller slette nattillegg for ulegitimert overnatting
- **Kall:** `GET /travelExpense/rateCategory`, `GET /travelExpense/rate`, `POST /travelExpense/accommodationAllowance`, `GET /travelExpense/accommodationAllowance`, `GET /travelExpense/accommodationAllowance/{id}`, `PUT /travelExpense/accommodationAllowance/{id}`, `DELETE /travelExpense/accommodationAllowance/{id}`
- **Nøkkelord:** nattillegg, ulegitimert overnatting, overnatting uten kvittering, privat overnatting, overnattet hos venner, overnattingsgodtgjørelse, accommodation allowance, endre nattillegg, slett nattillegg, søk nattillegg, antall netter, update accommodation allowance
- 1) GET /travelExpense/rateCategory?type=ACCOMMODATION_ALLOWANCE&isValidAccommodation=true&dateFrom..&dateTo..&fields=id,name,fromDate,toDate. 2) Evt. GET /travelExpense/rate?rateCategoryId=..&type=ACCOMMODATION_ALLOWANCE. 3) POST /travelExpense/accommodationAllowance {travelExpense:{id}, rateCategory:{id}, rateType:{id}, zone, location, address, count (antall netter)}. Nattillegg kan IKKE sendes via POST /travelExpense (read-only der). Hotell med kvittering føres som kostnad (/travelExpense/cost), ikke nattillegg. Søk/endre/slette: GET /travelExpense/accommodationAllowance (travelExpenseId, rateCategoryId, rateTypeId, countFrom/countTo, amountFrom/amountTo, location, address), GET /{id}, PUT /{id} med id+version, DELETE /{id} – kun når reiseregningen er OPEN. Adresse kan være persondata – vis ikke. Skrivende – bekreft først.

### Slå opp gjeldende satser for diett, kjøregodtgjørelse og nattillegg (statens satser)
- **Kall:** `GET /travelExpense/rateCategoryGroup`, `GET /travelExpense/rateCategoryGroup/{id}`, `GET /travelExpense/rateCategory`, `GET /travelExpense/rateCategory/{id}`, `GET /travelExpense/rate`, `GET /travelExpense/rate/{id}`
- **Nøkkelord:** statens satser, hva er diettsatsen, kilometersats i år, km-sats 2026, nattilleggssats, måltidstrekk sats, satser utland, satsoversikt, rates
- 1) GET /travelExpense/rateCategoryGroup?dateFrom=<åååå-01-01>&dateTo=<åååå+1-01-01>&isForeignTravel=false|true for årets grupper. 2) GET /travelExpense/rateCategory?travelReportRateCategoryGroupId=<id>&type=PER_DIEM|ACCOMMODATION_ALLOWANCE|MILEAGE_ALLOWANCE&fields=id,name,type,fromDate,toDate,isValidDayTrip,isValidDomestic,isValidForeignTravel,isRequiresZone. 3) GET /travelExpense/rate?rateCategoryId=<id>&dateFrom..&dateTo..&fields=id,zone,rate,breakfastDeductionRate,lunchDeductionRate,dinnerDeductionRate. dateTo er alltid 'til og uten'. Satser er versjonert per periode – velg alltid kategori gyldig på reisedatoen.

### Finne lønnsart og a-meldingskode for reisegodtgjørelser (trekkfri/trekkpliktig)
- **Kall:** `GET /travelExpense/rateCategory`, `GET /travelExpense/settings`
- **Nøkkelord:** a-melding reise, lønnsart diett, trekkpliktig diett, trekkfri bilgodtgjørelse, innberetningspliktig, a-meldingskode, lønnskode reise, overskytende diett, wage code
- GET /travelExpense/rateCategory?fields=id,name,type,ameldingWageCode,wageCodeNumber,fromDate,toDate, filtrer evt. med ameldingWageCode (inneholder) eller wageCodeNumber (lik), type og dateFrom/dateTo. Sjekk GET /travelExpense/settings (taxFreePerDiemRates, taxFreeMileageRates) for om selskapet bruker skattefrie satser. Beløp over statens satser blir trekkpliktig og innberettes via lønn/a-melding – se lønnsgruppen for utbetaling.

### ✏️ Laste opp kvitteringer/vedlegg til reiseregning eller utlegg
- **Kall:** `POST /travelExpense/{travelExpenseId}/attachment`, `POST /travelExpense/{travelExpenseId}/attachment/list`
- **Nøkkelord:** last opp kvittering, legg ved kvittering, vedlegg reiseregning, bilde av kvittering, pdf kvittering, flere kvitteringer, upload receipt, attachment
- Én fil: POST /travelExpense/{travelExpenseId}/attachment som multipart/form-data med feltet 'file' (PDF/PNG/JPEG). Flere filer: POST /travelExpense/{travelExpenseId}/attachment/list med 'file' som array. createNewCost=true oppretter en ny kostnadslinje per vedlegg (nyttig for utlegg); ellers legges filen til eksisterende vedlegg. Skrivende – bekreft først.

### ✏️ Laste ned eller fjerne vedlegg (evt. sende til bilagsmottak)
- **Kall:** `GET /travelExpense/{travelExpenseId}/attachment`, `DELETE /travelExpense/{travelExpenseId}/attachment`
- **Nøkkelord:** last ned kvittering, hent vedlegg, pdf reiseregning, slett vedlegg, flytt til bilagsmottak, send til innboks, del opp vedlegg, download attachment
- Last ned: GET /travelExpense/{travelExpenseId}/attachment (returnerer PDF/binær). Fjern: DELETE /travelExpense/{travelExpenseId}/attachment med version, og sendToInbox=true for å flytte vedlegget til bilagsmottaket i stedet for å slette (split=true deler i ett bilag per side). Vedlegg kan inneholde persondata – ikke del filene. DELETE er skrivende og bør som regel gjøres med sendToInbox=true – bekreft først.

### ✏️ Levere (sende inn) reiseregninger til godkjenning
- **Kall:** `PUT /travelExpense/:deliver`
- **Nøkkelord:** levere reiseregning, send inn reiseregning, lever utlegg, fullfør reiseregning, deliver, submit travel expense
- PUT /travelExpense/:deliver?id=<id1,id2,...> (kommaseparert liste, ingen body). Status går fra OPEN til DELIVERED. Reiseregningen må være komplett (travelDetails, linjer, evt. vedlegg) ellers 422. Skrivende – bekreft først.

### ✏️ Angre levering eller oppheve godkjenning av reiseregning (for å rette den)
- **Kall:** `PUT /travelExpense/:undeliver`, `PUT /travelExpense/:unapprove`
- **Nøkkelord:** angre levering, trekk tilbake, åpne reiseregning igjen, gjenåpne, rette levert reiseregning, undeliver, angre godkjenning, fjern godkjenning, avgodkjenn, oppheve attestering, unapprove
- Godkjent -> levert: PUT /travelExpense/:unapprove?id=<id1,id2,...> (status APPROVED -> DELIVERED; vil normalt avvises hvis bilag er opprettet eller status er SALARY_PAID – sjekk voucher(id) og state først). Levert -> åpen: PUT /travelExpense/:undeliver?id=<id1,id2,...> (DELIVERED -> OPEN) slik at linjer kan endres. Kjør i den rekkefølgen ved behov. Skrivende – bekreft først.

### ✏️ Godkjenne (attestere) reiseregninger og utlegg
- **Kall:** `GET /travelExpense`, `PUT /travelExpense/:approve`
- **Nøkkelord:** godkjenn reiseregning, attester, attestere utlegg, godkjenne alle leverte, approve travel expense, godkjenningsflyt
- 1) Finn leverte: GET /travelExpense?state=DELIVERED&fields=id,number,amount,title. 2) PUT /travelExpense/:approve?id=<id1,id2,...>. overrideApprovalFlow=true overstyrer attestasjonsflyten (krever rettighet – bruk kun når brukeren eksplisitt ber om det). Status blir APPROVED. Selvgodkjenning styres av settings.canApproveOwnExpenses. Skrivende – krever alltid eksplisitt bekreftelse.

### ✏️ Bokføre godkjente reiseregninger (opprette bilag i hovedboken)
- **Kall:** `GET /travelExpense`, `PUT /travelExpense/:createVouchers`, `GET /ledger/voucher/{id}`, `GET /ledger/voucher/{voucherId}/pdf`
- **Nøkkelord:** bokfør reiseregning, bokføre utlegg, lag bilag, opprett bilag reiseregning, kostnadsfør reise, postere reiseregning, create vouchers, bokfore
- 1) GET /travelExpense?state=APPROVED&fields=id,number,amount,voucher(id),accountingPeriodClosed. 2) PUT /travelExpense/:createVouchers?id=<id1,id2,...>&date=<yyyy-MM-dd> – date er PÅKREVD (bilagsdato) og må ligge i åpen periode. id er valgfri i spec-en, men angi den alltid eksplisitt (kommaseparert) så du ikke bokfører flere enn tiltenkt. 3) Kontroller bilaget: GET /travelExpense/{id}?fields=voucher(id,number) og GET /ledger/voucher/{id}?fields=id,number,date,postings(account(number),amountGross,employee(id)). PDF: GET /ledger/voucher/{voucherId}/pdf. Skrivende – bekreft først.

### Finne bokførte reiseregningsbilag og avstemme skyldig reiseregning mot ansattreskontro
- **Kall:** `GET /ledger/voucherType`, `GET /ledger/voucher`, `GET /ledger/posting`, `GET /ledger/posting/openPost`, `GET /travelExpense`
- **Nøkkelord:** avstem reiseregninger, skyldig reiseregning, skyldig ansatte, ansattreskontro, åpne poster ansatt, apne poster, reiseregningsbilag, bilagstype reiseregning, ikke utbetalt reiseregning
- 1) GET /ledger/voucherType?name=Reise for bilagstype-id. 2) GET /ledger/voucher?typeId=<id>&dateFrom=..&dateTo=.. (begge påkrevd). 3) Åpne poster per ansatt: GET /ledger/posting/openPost?date=<til og uten>&employeeId=..&fields=id,date,amount,account(number),employee(id). 4) Hovedbokposteringer: GET /ledger/posting?dateFrom..&dateTo..&employeeId=.. . 5) Sammenlign med GET /travelExpense?state=APPROVED (ikke utbetalt) vs SALARY_PAID. Rapporter per ansatt-id/initialer og aggregater (GDPR).

### ✏️ Endre reiseregning (tittel, reisedetaljer, prosjekt, avdeling, forskudd, viderefakturering)
- **Kall:** `GET /travelExpense/{id}`, `PUT /travelExpense/{id}`, `GET /project`, `GET /department`
- **Nøkkelord:** endre reiseregning, koble til prosjekt, bytt avdeling, reiseforskudd, forskudd, viderefakturer reise, fakturerbar reise, påslag, update travel expense
- Hent id+version: GET /travelExpense/{id}?fields=id,version,state. PUT /travelExpense/{id} med id, version og felt som skal endres: title, travelDetails(...), project:{id}, department:{id}, freeDimension1-3:{id}, travelAdvance (forskudd), isChargeable, isFixedInvoicedAmount/fixedInvoicedAmount, isMarkupInvoicedPercent/markupInvoicedPercent, isIncludeAttachedReceiptsWhenReinvoicing. Kun mulig når state=OPEN. Skrivende – bekreft først.

### ✏️ Kopiere en reiseregning (f.eks. gjentakende reise)
- **Kall:** `PUT /travelExpense/:copy`
- **Nøkkelord:** kopier reiseregning, dupliser, samme reise igjen, gjentakende reise, copy travel expense
- PUT /travelExpense/:copy?id=<id> (id påkrevd, ett element). Returnerer ny reiseregning i status OPEN. Oppdater deretter datoer med PUT /travelExpense/{nyId} og linjer via under-endepunktene. Skrivende – bekreft først.

### ✏️ Konvertere mellom reiseregning og ansattutlegg
- **Kall:** `GET /travelExpense/{id}`, `PUT /travelExpense/{id}/convert`
- **Nøkkelord:** konverter til utlegg, gjør om til reiseregning, feil type, bytt fra reise til utlegg, convert
- PUT /travelExpense/{id}/convert (path-id, ingen query/body) bytter mellom reiseregning og ansattutlegg. Reisespesifikke linjer (diett, km, nattillegg) hører ikke hjemme på et utlegg – sjekk innholdet først med GET /travelExpense/{id}?fields=id,state,travelDetails(departureDate),perDiemCompensations(id),mileageAllowances(id),accommodationAllowances(id),costs(id). Gjør det mens status er OPEN. Skrivende – bekreft først.

### ✏️ Slette reiseregning eller utlegg
- **Kall:** `GET /travelExpense/{id}`, `DELETE /travelExpense/{id}`
- **Nøkkelord:** slett reiseregning, slett utlegg, fjern reiseregning, feilregistrert reise, delete travel expense
- Sjekk status først: GET /travelExpense/{id}?fields=id,state,voucher(id). Normalt kan bare OPEN reiseregninger uten bilag slettes – kjør :unapprove/:undeliver først ved behov. DELETE /travelExpense/{id}. Permanent sletting – krever alltid eksplisitt bekreftelse fra brukeren.

### Hente kostnadskategorier og betalingstyper med kontering
- **Kall:** `GET /travelExpense/costCategory`, `GET /travelExpense/costCategory/{id}`, `GET /travelExpense/paymentType`, `GET /travelExpense/paymentType/{id}`
- **Nøkkelord:** kostnadskategorier, utgiftstyper, betalingstyper, hvilken konto, kontering utlegg, firmakort konto, privat betalt konto, mva-kode kategori, cost categories, payment types
- GET /travelExpense/costCategory?isInactive=false&fields=id,description,account(number,name),vatType(id,number),isVatLocked,showOnTravelExpenses,showOnEmployeeExpenses (filter: description inneholder, query, showOnEmployeeExpenses). GET /travelExpense/paymentType?isInactive=false&fields=id,description,account(number,name),showOnTravelExpenses,showOnEmployeeExpenses. Kategorien bestemmer kostnadskonto/mva, betalingstypen bestemmer motkonto (f.eks. skyldig ansatt vs firmakort). Kun lesing – oppsett endres i Tripletex-GUI.

### Sjekke selskapets oppsett for reiseregninger
- **Kall:** `GET /travelExpense/settings`
- **Nøkkelord:** reiseregning innstillinger, bruker vi satser, godkjenning påkrevd, kan godkjenne egne, skattefrie satser, kompenseres diett, settings
- GET /travelExpense/settings?fields=useRates,approvalRequired,taxFreePerDiemRates,taxFreeMileageRates,perDiemNotCompensated,accommodationNotCompensated,mileageNotCompensated,canApproveOwnExpenses. Kun lesing (ingen PUT i API-et). Bruk før registrering for å vite om satser brukes og om godkjenning kreves.

### Sjekke om reiseregninger/utlegg er utbetalt (via lønn) og finne lønnsslipp-koblingen
- **Kall:** `GET /travelExpense`, `GET /travelExpense/{id}`
- **Nøkkelord:** utbetalt reiseregning, er reiseregningen betalt, utbetaling utlegg, refusjon utbetalt, salary paid, reiseregning lønn, lønnsslipp reise, lonnsslipp reise, ikke utbetalt, skyldig utlegg
- GET /travelExpense?state=SALARY_PAID (utbetalt via lønn) eller state=APPROVED (godkjent, ikke utbetalt), evt. med departureDateFrom/returnDateTo og employeeId; fields=id,number,state,paymentAmount,approvedDate,voucher(id,number),payslip(id),showPayslip. Én: GET /travelExpense/{id}?fields=id,state,paymentAmount,payslip(id),voucher(id). Hent ikke lønnsslippens innhold (lønn per person er persondata) – oppgi kun status og summer. Gruppen har ikke noe utbetalingsendepunkt; utbetaling skjer via lønnskjøring eller bank/remittering.

### ✏️ Avvise eller sende tilbake en reiseregning til den ansatte
- **Kall:** `GET /travelExpense/{id}`, `PUT /travelExpense/:unapprove`, `PUT /travelExpense/:undeliver`
- **Nøkkelord:** avvis reiseregning, avvise utlegg, send tilbake reiseregning, returner reiseregning, reject travel expense, underkjenn, avvist reiseregning
- API v2 har IKKE noe :reject-endepunkt for reiseregninger (state REJECTED og rejectedComment kan bare leses). Nærmeste alternativ: sjekk status (GET /travelExpense/{id}?fields=id,state,voucher(id)), deretter PUT /travelExpense/:unapprove?id=<id> hvis APPROVED og PUT /travelExpense/:undeliver?id=<id> hvis DELIVERED, slik at reiseregningen blir OPEN igjen og kan rettes. Formell avvisning med kommentar må gjøres i Tripletex-GUI. Skrivende – bekreft først.

**Fallgruver:**
- Alle endepunkter i gruppen er merket PERSONDATA (knyttet til ansatte). Bruk alltid minimal fields= (f.eks. employee(id) i stedet for employee(*)), og vis aldri ansattnavn, adresser, passasjer-/deltakernavn eller beløp per navngitt person – bruk aggregater, initialer eller 'ansatt 1/2' (GDPR).
- Ansattutlegg og reiseregning er samme objekt (TravelExpense): utlegg har INGEN travelDetails. Bytt type med PUT /travelExpense/{id}/convert – reisespesifikke linjer (diett/km/nattillegg) kan gå tapt.
- Statusflyt: OPEN -> :deliver -> DELIVERED -> :approve -> APPROVED -> :createVouchers (bilag) -> SALARY_PAID når utbetalt via lønn. REJECTED ved avvisning (rejectedComment). Tilbake: :unapprove (APPROVED->DELIVERED) og :undeliver (DELIVERED->OPEN). Linjer kan bare endres/slettes i OPEN.
- Action-endepunktene er PUT med kolon: /travelExpense/:deliver, /:undeliver, /:approve, /:unapprove, /:createVouchers, /:copy. Parameteren id er en kommaseparert liste av id-er i query (ikke body); :copy tar kun én id (påkrevd).
- PUT /travelExpense/:createVouchers krever query-param date (yyyy-MM-dd) selv om beskrivelsen sier 'defaults to today'. Datoen må ligge i åpen regnskaps-/mva-periode (se accountingPeriodClosed/accountingPeriodVATClosed på objektet). Angi alltid id – ikke kjør uten id.
- mileageAllowances og accommodationAllowances er read-only på TravelExpense – de MÅ opprettes via POST /travelExpense/mileageAllowance og POST /travelExpense/accommodationAllowance. Diett (perDiemCompensations) og costs kan sendes inline ved POST /travelExpense eller via egne endepunkter.
- Satser er versjonert: velg rateCategory (og evt. rateType/TravelExpenseRate) som er gyldig på reisedatoen (dateFrom/dateTo, fromDate/toDate) og riktig type (PER_DIEM|ACCOMMODATION_ALLOWANCE|MILEAGE_ALLOWANCE), innland/utland, dagsreise/overnatting og sonekrav. Feil kategori for datoen gir 422.
- Utenlandsdiett krever travelDetails.isForeignTravel=true og land/sone (countryCode og/eller travelExpenseZoneId fra GET /travelExpense/zone med date=reisedato).
- Navneforskjell: søk på perDiemCompensation bruker isLunchDeduction/isDinnerDeduction, mens body-feltene heter isDeductionForLunch/isDeductionForDinner (frokost heter isDeductionForBreakfast begge steder).
- dateTo, returnDateTo og openPost-date er 'til og UTEN' (eksklusiv). departureDateFrom/dateFrom er inklusiv.
- PUT på reiseregning og linjer bør inneholde id og version (optimistisk låsing); feil version gir 409/422 – hent på nytt og prøv igjen.
- Vedlegg lastes opp som multipart/form-data med feltet 'file'. createNewCost=true lager én kostnadslinje per vedlegg. DELETE attachment med sendToInbox=true flytter til bilagsmottak i stedet for å slette.
- createCostParticipantAdvanced krever både costId og employeeId i query – bruk employeeId=0 for eksterne deltakere.
- drivingStop har ingen søk eller PUT – endre ved å slette og opprette på nytt. Stoppene leses via mileageAllowance.drivingStops.
- GET /travelExpense/settings, costCategory, paymentType, rate, rateCategory, rateCategoryGroup og zone er kun lesbare i API-et – oppsett og satser endres i Tripletex-GUI.
- 403 betyr normalt at token/bruker mangler rettighet til reiseregninger (eller til å godkjenne/attestere andres), eller at reiseregningsmodulen ikke er aktiv hos klienten. 422 betyr valideringsfeil (manglende felt, ugyldig sats/periode, feil status).
- Beløp over statens skattefrie satser blir trekkpliktige og går til lønn/a-melding via satskategoriens ameldingWageCode/wageCodeNumber – utbetaling via lønn gir status SALARY_PAID og payslip-kobling.
- Alle skrivende kall (opprette, endre, slette, levere, godkjenne, bokføre, laste opp) krever eksplisitt bekreftelse fra brukeren og at klienten er navngitt.
- Det finnes ikke noe :reject-endepunkt i API v2 – avvisning (REJECTED med rejectedComment) gjøres i GUI; via API kan du bare :unapprove/:undeliver tilbake til OPEN.
- GET /travelExpense kan ikke filtrere på reiseregningsnummer, id-liste eller bilagsdato; departureDateFrom/returnDateTo gjelder reisedatoer, så ansattutlegg (uten travelDetails) kan falle utenfor – filtrer på date/number i koden.
- costCategory-søk: query= er eksakt treff (Equals), description= er «inneholder». På paymentType er både query og description «inneholder».
- PUT /travelExpense/:undeliver har et TravelExpense-body-skjema i spec-en, men det er query-param id som styrer hvilke reiseregninger som angres.
- GET /travelExpense/{travelExpenseId}/attachment returnerer binær fil (PDF), ikke JSON – les som buffer og del ikke filen (kan inneholde persondata).
- Mange TravelExpense-felt er read-only (amount, paymentAmount, number, state, date, approvedDate, rejectedComment, mileageAllowances, accommodationAllowances) – de kan leses, men ignoreres/avvises i POST/PUT.

## Produkter, lager, logistikk

### Søke opp produkter/varer på navn, varenummer eller EAN
- **Kall:** `GET /product`, `GET /product/{id}`
- **Nøkkelord:** finn produkt, søk vare, sok vare, varenummer, artikkelnummer, produktliste, vareliste, ean, strekkode, product search, hent produkt, vareregister, eksportere vareliste, produkter fra leverandør, fakturalinje, tjenester
- GET /product med name= (inneholder), productNumber= (liste med varenumre; parameteren number er DEPRECATED), ean= (eksakt), isInactive=false, isStockItem=, supplierId=, vatTypeId=, accountId=, departmentId= eller prisintervall (priceExcludingVatCurrencyFrom/To, fra og med / til men ikke med). Bruk fields=id,number,name,priceExcludingVatCurrency,costExcludingVatCurrency,vatType(id,number),account(number),productUnit(nameShort),isStockItem,isInactive. count er 1000 som standard – paginer med from/count. Merk: priceExcludingVatCurrency = salgspris (spec-teksten sier misvisende «price of purchase»), costExcludingVatCurrency = innkjøps-/kostpris; costPrice er skrivebeskyttet. Detaljer: GET /product/{id}.

### ✏️ Opprette nytt produkt (vare eller tjeneste)
- **Kall:** `GET /ledger/vatType`, `GET /ledger/account`, `GET /product/unit`, `POST /product`
- **Nøkkelord:** nytt produkt, ny vare, opprett vare, registrere vare, legge inn produkt, ny tjeneste, create product, vareregistrering, salgspris, mva-kode, inntektskonto
- 1) MVA-kode: GET /ledger/vatType (f.eks. utgående 25 % = vatType number 3; 15 % mat = 31; fritatt = 5/6). 2) Inntektskonto: GET /ledger/account?number=3000. 3) Enhet: GET /product/unit?nameShort=stk. 4) Sjekk dublett: GET /product?productNumber=<nr>. 5) POST /product med name, number (varenummer som streng, må være unikt), priceExcludingVatCurrency (salgspris eks. mva) eller priceIncludingVatCurrency, costExcludingVatCurrency (kostpris), vatType{id}, account{id}, productUnit{id}, ev. currency{id}, department{id}, supplier{id}, ean, description, orderLineDescription, isStockItem=true for lagervare, minStockLevel, weight/weightUnit (kg|g|hg), volume/volumeUnit (cm3|dm3|m3). elNumber/nrfNumber, costPrice og lagerfeltene er skrivebeskyttet. Skrivende – krever bekreftelse.

### ✏️ Importere mange produkter på én gang (vareliste fra Excel/CSV)
- **Kall:** `GET /product`, `POST /product/list`
- **Nøkkelord:** import produkter, importere vareliste, masseopprettelse, bulk, mange varer, vareimport, produktimport, csv, excel, product list
- Les filen lokalt, slå opp id-er for vatType/account/productUnit én gang og gjenbruk. Sjekk eksisterende varenumre med GET /product?productNumber=...&fields=id,number. POST /product/list med en JSON-array av Product-objekter (samme felt som POST /product, uten id/version). Én ugyldig rad kan stoppe hele kallet – send i batcher (f.eks. 50–100) og logg feil per batch. Krever bekreftelse.

### ✏️ Endre pris eller opplysninger på produkt (prisjustering, masseprisendring)
- **Kall:** `GET /product/{id}`, `GET /product`, `PUT /product/{id}`, `PUT /product/list`
- **Nøkkelord:** endre pris, prisendring, prisjustering, prisøkning, prisokning, oppdatere produkt, endre vare, ny salgspris, ny kostpris, indeksregulering, update product
- Enkeltvare: GET /product/{id}?fields=id,version,priceExcludingVatCurrency,costExcludingVatCurrency, deretter PUT /product/{id} med id, version og endrede felt (priceExcludingVatCurrency, costExcludingVatCurrency, vatType, account, name, discountGroup …). Masseendring (f.eks. +3 %): GET /product med filter og fields=id,version,priceExcludingVatCurrency, beregn ny pris lokalt, PUT /product/list med [{id,version,priceExcludingVatCurrency}]. Feil version gir konflikt – hent på nytt. Endringen gjelder nye ordrelinjer, ikke eksisterende ordre/fakturaer. Krever bekreftelse.

### ✏️ Deaktivere eller slette et produkt
- **Kall:** `GET /product/{id}`, `PUT /product/{id}`, `DELETE /product/{id}`
- **Nøkkelord:** slett produkt, slette vare, deaktivere vare, inaktiv vare, arkivere produkt, utgått vare, rydde vareregister, delete product, inactive, ubrukt produkt
- Produkter som er brukt på ordre, faktura, bilag eller lager kan ikke slettes. Standard: PUT /product/{id} med id, version og isInactive=true. DELETE /product/{id} bare for ubrukte produkter (feltet isDeletable er deprecated og returnerer alltid false, så det kan ikke brukes til å sjekke på forhånd – ved feil, deaktiver i stedet). Krever bekreftelse.

### ✏️ Laste opp bilde eller dokumenter (datablad) på et produkt
- **Kall:** `POST /product/{id}/image`, `DELETE /product/{id}/image`, `GET /documentArchive/product/{id}`, `POST /documentArchive/product/{id}`
- **Nøkkelord:** produktbilde, varebilde, bilde, last opp bilde, slette bilde, datablad, produktdokument, sertifikat, fdv, vedlegg produkt, image, document archive
- Bilde: POST /product/{id}/image som multipart/form-data med feltet file (erstatter eksisterende bilde); fjern med DELETE /product/{id}/image. Andre dokumenter (datablad, FDV, sertifikater): POST /documentArchive/product/{id} (BETA, multipart med file); list med GET /documentArchive/product/{id} (periodDateFrom/periodDateTo valgfritt). Krever bekreftelse.

### Se lagerbeholdning for en vare nå (på lager, tilgjengelig, innkommende, utgående)
- **Kall:** `GET /product`, `GET /product/{id}`, `GET /product/inventoryLocation`
- **Nøkkelord:** lagerbeholdning, hvor mange på lager, antall på lager, tilgjengelig, disponibelt, reservert, innkommende, utgående, lagerstatus, stock, available stock, beholdning per lagerplass
- GET /product?isStockItem=true&productNumber=<nr>&fields=id,number,name,stockOfGoods,availableStock,incomingStock,outgoingStock,minStockLevel. Beholdningsfeltene er 'available only on demand' og kommer KUN med når de står eksplisitt i fields=. Per lager/lagerplass (Logistics Basic): GET /product/inventoryLocation?productId=<id>&fields=inventory(name),inventoryLocation(name),isMainLocation,stockOfGoods. stockOfGoods = fysisk beholdning; availableStock = disponibel beholdning etter reservasjoner.

### Hente lagerbeholdning og lagerbevegelser for en periode (inngående/utgående beholdning per lager)
- **Kall:** `GET /inventory/inventories`, `GET /inventory`
- **Nøkkelord:** lagerbevegelser, lagerendring, inngående beholdning, utgående beholdning, beholdning per dato, lagerliste, lagerrapport, beholdningsrapport, varelager 31.12, stock movement, inventories
- GET /inventory/inventories med påkrevd dateFrom og dateTo (yyyy-MM-dd, begge inkludert), ev. productId=, inventoryId= (fra GET /inventory) og onlyProductWithChangedStatus=true for kun varer med bevegelse. Respons per produkt: product + stock[] med inventory, inventoryId, openingStock, changesInPeriod, closingStock. Bruk fields=product(id,number,name,costExcludingVatCurrency),stock(*) og paginer med from/count.

### Beregne varelagerverdi og avstemme varelager mot hovedbok (1460) ved årsoppgjør
- **Kall:** `GET /inventory/inventories`, `GET /product`, `GET /inventory/stocktaking`, `GET /balanceSheet`, `GET /ledger/posting`
- **Nøkkelord:** varelagerverdi, lagerverdi, avstemme varelager, varelager 1460, 1460, 4290, varelagerendring, beholdningsendring, årsoppgjør, arsoppgjor, ukurans, nedskrivning varelager, saldobalanse, inventory valuation
- 1) GET /inventory/inventories?dateFrom=<år>-01-01&dateTo=<år>-12-31 → closingStock per vare og lager. 2) Kostpris: GET /product?ids=...&fields=id,number,costExcludingVatCurrency,costPrice, eller bruk siste fullførte varetelling: GET /inventory/stocktaking?isCompleted=true&fields=id,date,warehouseValue,discrepancySum. 3) Lagerverdi = sum(closingStock × kostpris). 4) Saldo i hovedbok: GET /balanceSheet?dateFrom=<år>-01-01&dateTo=<år+1>-01-01&accountNumberFrom=1400&accountNumberTo=1499 (dateTo er eksklusiv). Detaljer: GET /ledger/posting?dateFrom=&dateTo=&accountNumberFrom=1400&accountNumberTo=1499. 5) Differanse/ukurans føres som bilag mot 1460/4290 (se hovedbok-gruppen) – skrivende og krever bekreftelse.

### ✏️ Opprette og administrere lagre (hovedlager, filiallager)
- **Kall:** `GET /inventory`, `GET /inventory/{id}`, `POST /inventory`, `PUT /inventory/{id}`, `DELETE /inventory/{id}`
- **Nøkkelord:** nytt lager, opprett lager, endre lager, slett lager, hovedlager, filiallager, lageradresse, deaktivere lager, warehouse, inventory
- Finn lagre: GET /inventory?isMainInventory=true | name= | query= | isInactive=false, fields=id,version,number,name,isMainInventory,status,lastStocking,hasLocations. Opprett: POST /inventory med name, number, isMainInventory, description, address. Endre/deaktivere: PUT /inventory/{id} med id, version og f.eks. isInactive=true. DELETE /inventory/{id} bare når deletable=true (ingen beholdning/bevegelser). Krever bekreftelse ved skriving.

### ✏️ Opprette og vedlikeholde lagerplasser (hylle/reol) i et lager
- **Kall:** `GET /product/logisticsSettings`, `PUT /product/logisticsSettings`, `GET /inventory/location`, `GET /inventory/location/{id}`, `POST /inventory/location`, `POST /inventory/location/list`, `PUT /inventory/location/{id}`, `PUT /inventory/location/list`, `DELETE /inventory/location/{id}`, `DELETE /inventory/location/list`
- **Nøkkelord:** lagerplass, ny lagerplass, hylle, reol, lokasjon, lagerlokasjon, plassering, bin, slette lagerplass, warehouse location
- Krever Logistics Basic og at lagerplasser er aktivert (GET /product/logisticsSettings → hasWarehouseLocation; slå på med PUT hvis nødvendig). Søk: GET /inventory/location?warehouseId=<lager-id>&name=&isInactive=false. Opprett: POST /inventory/location {inventory:{id}, name}; mange: POST /inventory/location/list. Endre: PUT /inventory/location/{id} eller /list (id+version). Slett: DELETE /inventory/location/{id} eller DELETE /inventory/location/list?ids=1,2,3. Plass med beholdning kan ikke slettes – sjekk canDeactivate og sett isInactive=true. Krever bekreftelse.

### ✏️ Knytte et produkt til lager/lagerplass (hovedplassering)
- **Kall:** `GET /product/inventoryLocation`, `GET /product/inventoryLocation/{id}`, `POST /product/inventoryLocation`, `POST /product/inventoryLocation/list`, `PUT /product/inventoryLocation/{id}`, `PUT /product/inventoryLocation/list`, `DELETE /product/inventoryLocation/{id}`
- **Nøkkelord:** plassere vare, produktplassering, hovedplassering, hovedlagerplass, flytte vare, hvor ligger varen, vare på hylle, product location, main location
- Logistics Basic. Se eksisterende: GET /product/inventoryLocation?productId=<id>&inventoryId=&isMainLocation=true. Ny kobling: POST /product/inventoryLocation {product:{id}, inventory:{id}, inventoryLocation:{id}, isMainLocation:true}; mange: POST /product/inventoryLocation/list. Bytte hovedplassering/deaktivere: PUT /product/inventoryLocation/{id} (id+version, isMainLocation/isInactive). Fjern kobling: DELETE /product/inventoryLocation/{id} (ikke mulig med beholdning på plassen). Krever bekreftelse.

### ✏️ Starte en varetelling (lageropptelling) for et lager
- **Kall:** `GET /inventory`, `GET /inventory/stocktaking`, `POST /inventory/stocktaking`
- **Nøkkelord:** ny varetelling, start varetelling, opprett telling, lagertelling, inventering, årstelling, varetelling 31.12, telleliste, stocktaking, stock count
- Finn lager-id: GET /inventory. Sjekk at det ikke finnes åpen telling: GET /inventory/stocktaking?inventoryId=<id>&isCompleted=false. Opprett: POST /inventory/stocktaking?typeOfStocktaking=ALL_PRODUCTS_WITH_INVENTORIES (standard: alle varer med beholdning) | INCLUDE_PRODUCTS (alle lagervarer) | NO_PRODUCTS (tom liste, legg til linjer selv); body: date (telledato, f.eks. 2025-12-31), inventory{id}, comment. typeOfStocktaking i body er deprecated – bruk query-parameteren. Returnert id brukes mot productline-kallene. Krever bekreftelse.

### ✏️ Registrere opptalt antall på varetellingen
- **Kall:** `GET /inventory/stocktaking/productline`, `GET /inventory/stocktaking/productline/{id}`, `PUT /inventory/stocktaking/productline/{id}`, `POST /inventory/stocktaking/productline`, `DELETE /inventory/stocktaking/productline/{id}`, `PUT /inventory/stocktaking/productline/{id}/:changeLocation`
- **Nøkkelord:** registrere telling, opptalt antall, telt antall, tellelinje, ikke opptalte varer, legge til vare i telling, korrigere telling, flytte lagerplass, count, product line
- Hent linjer: GET /inventory/stocktaking/productline?stocktakingId=<id> (påkrevd) &productLineStatus=NOT_COUNTED_PRODUCTS|COUNTED_PRODUCTS|ALL_PRODUCTS, ev. query=, productGroupIds=, locationIds= (count er 10000 som standard); fields=id,version,product(number,name),count,unitCostCurrency,location(name),comment (unngå counter – det er en ansatt, GDPR). Registrer: PUT /inventory/stocktaking/productline/{id} med id, version, count (opptalt antall), ev. unitCostCurrency (kostpris eks. mva) og comment. Vare som mangler på listen: POST /inventory/stocktaking/productline {stocktaking:{id}, product:{id}, count, location:{id}}. Feil linje: DELETE .../{id}. Annen lagerplass: PUT .../{id}/:changeLocation?warehouseLocationId=<id> (BETA). Det finnes ingen /productline/list i spesifikasjonen selv om beskrivelsen nevner det – POST én og én. Krever bekreftelse. Feltene counted, dateCounted og expectedStock er merket «internal use» – bruk productLineStatus-filteret for status.

### ✏️ Se status, fullføre eller slette en varetelling (lagerverdi og avvik)
- **Kall:** `GET /inventory/stocktaking`, `GET /inventory/stocktaking/{id}`, `GET /inventory/stocktaking/productline`, `PUT /inventory/stocktaking/{id}`, `DELETE /inventory/stocktaking/{id}`, `GET /ledger/posting`
- **Nøkkelord:** fullføre varetelling, fullfore varetelling, avslutte telling, godkjenne telling, varetellingsliste, avvik varetelling, differanse, svinn, lagerverdi, slette varetelling, åpne varetellinger, stocktaking completed
- Liste: GET /inventory/stocktaking?inventoryId=&isCompleted=false|true&fields=id,version,number,date,inventory(name),isCompleted,warehouseValue,discrepancySum. Før fullføring: GET /inventory/stocktaking/productline?stocktakingId=<id>&productLineStatus=NOT_COUNTED_PRODUCTS skal være tom. Fullfør: PUT /inventory/stocktaking/{id} med id, version, isCompleted=true – setter lagerbeholdningen lik opptalt antall (i praksis irreversibelt, krever bekreftelse). Deretter kontroller bokført varelagerendring: GET /ledger/posting?dateFrom=&dateTo=&accountNumberFrom=1400&accountNumberTo=1499 (og 4000–4299). Åpen telling som skal forkastes: DELETE /inventory/stocktaking/{id} (krever bekreftelse).

### ✏️ Registrere leverandørprodukt og leverandørens innkjøpspris for en vare
- **Kall:** `GET /supplier`, `GET /product/supplierProduct`, `GET /product/supplierProduct/{id}`, `POST /product/supplierProduct/getSupplierProductsByIds`, `POST /product/supplierProduct`, `POST /product/supplierProduct/list`, `PUT /product/supplierProduct/{id}`, `PUT /product/supplierProduct/list`, `DELETE /product/supplierProduct/{id}`
- **Nøkkelord:** leverandørprodukt, leverandorprodukt, leverandørens varenummer, innkjøpspris, innkjopspris, innpris, hovedleverandør, bestillingsnummer, supplier product, vendor, videresalg
- Leverandør-id: GET /supplier?organizationNumber=. Søk: GET /product/supplierProduct (NB: fields er som standard bare id,name,number – angi f.eks. fields=id,version,name,number,supplier(name),costExcludingVatCurrency,currency(code),resaleProduct(number,name),isMainSupplierProduct,isInactive) med productId=|vendorId=|query=|productGroupId=, ev. targetCurrencyId= for omregnet pris (priceInTargetCurrency). Mange id-er: POST /product/supplierProduct/getSupplierProductsByIds med array [{id}] – lesende selv om det er POST. Opprett: POST /product/supplierProduct med name, number (leverandørens varenr.), supplier{id}, costExcludingVatCurrency (innkjøpspris i produktets valuta), currency{id}, productUnit{id}, vatType{id}, resaleProduct{id} (eget produkt det videreselges som), isMainSupplierProduct (pilot). Endre: PUT (id+version), mange: /list. Slett: DELETE /product/supplierProduct/{id}. Krever bekreftelse ved skriving.

### Finne produkter i grossistkatalog (EFO/NELFO, elnummer, NRF-nummer)
- **Kall:** `GET /product/external`, `GET /product/external/{id}`
- **Nøkkelord:** grossist, elnummer, el-nummer, nrf, nrf-nummer, efo, nelfo, grossistkatalog, ahlsell, onninen, solar, sonepar, brødrene dahl, elektroskandia, external product
- BETA. GET /product/external med wholesaler= (AHLSELL, BROEDRENE_DAHL, ELEKTROSKANDIA, HEIDENREICH, ONNINEN, SONEPAR, SOLAR, BERGAARD_AMUNDSEN, WURTH, …) eller organizationNumber= (påkrevd hvis wholesaler ikke er satt), pluss name=, elNumber= eller nrfNumber=. sorting brukes ikke på dette endepunktet. Resultatet er katalogdata, ikke eget vareregister – opprett eget produkt med POST /product ved behov. Detaljer: GET /product/external/{id}.

### ✏️ Opprette og vedlikeholde produktgrupper/varegrupper
- **Kall:** `GET /product/group`, `GET /product/group/{id}`, `GET /product/group/query`, `POST /product/group`, `POST /product/group/list`, `PUT /product/group/{id}`, `PUT /product/group/list`, `DELETE /product/group/{id}`, `DELETE /product/group/list`
- **Nøkkelord:** varegruppe, produktgruppe, ny varegruppe, kategori, produktkategori, undergruppe, hovedgruppe, slette varegruppe, product group
- Logistics Basic. Søk: GET /product/group?name=|query= eller wildcard GET /product/group/query?query=. Opprett: POST /product/group {name, parentGroup:{id}} (parentGroup for undergruppe); mange: POST /product/group/list. Endre: PUT /product/group/{id} eller /list (id+version). Slett: DELETE /product/group/{id} eller DELETE /product/group/list?ids=1,2 (kun når isDeletable=true). Krever bekreftelse.

### ✏️ Plassere produkter i varegrupper
- **Kall:** `GET /product/groupRelation`, `GET /product/groupRelation/{id}`, `POST /product/groupRelation`, `POST /product/groupRelation/list`, `DELETE /product/groupRelation/{id}`, `DELETE /product/groupRelation/list`
- **Nøkkelord:** koble vare til varegruppe, legge produkt i gruppe, gruppetilknytning, fjerne fra varegruppe, produkter i varegruppe, group relation
- Logistics Basic. Se koblinger: GET /product/groupRelation?productId=|productGroupId=&fields=id,product(number,name),productGroup(name). Koble: POST /product/groupRelation {product:{id}, productGroup:{id}}; mange: POST /product/groupRelation/list. Fjern: DELETE /product/groupRelation/{id}, eller DELETE /product/groupRelation/list med JSON-array av id-er i BODY (ikke ?ids= som på /product/group/list). Relasjoner kan ikke endres – slett og opprett ny. Krever bekreftelse.

### Se prishistorikk og siste innkjøps-/salgspris for et produkt
- **Kall:** `GET /product`, `GET /product/productPrice`
- **Nøkkelord:** prishistorikk, historiske priser, siste pris, prisendringer, når endret prisen, innkjøpspris, salgspris, kostpris, price history
- Logistics Basic. Finn produkt-id med GET /product?productNumber=. GET /product/productPrice?productId=<id> (påkrevd) &fromDate=&toDate= (toDate eksklusiv) eller showOnlyLastPrice=true (da ignoreres datoene). fields=fromDate,toDate,purchasePrice,purchasePriceCurrency,costPrice,salesPriceExcludingVat,salesPriceIncludingVat,vatType(number).

### ✏️ Administrere produktenheter (stk, timer, kg, meter)
- **Kall:** `GET /product/unit`, `GET /product/unit/{id}`, `GET /product/unit/query`, `POST /product/unit`, `POST /product/unit/list`, `PUT /product/unit/{id}`, `PUT /product/unit/list`, `DELETE /product/unit/{id}`
- **Nøkkelord:** enhet, ny enhet, måleenhet, maleenhet, stk, kg, meter, liter, salgsenhet, product unit, timeenhet, enhet time, pakke
- Søk: GET /product/unit?name=|nameShort=|commonCode= eller wildcard GET /product/unit/query?query=. Opprett: POST /product/unit {name, nameShort, nameEN, nameShortEN, commonCode} (commonCode = UN/ECE-kode, se product/unit/master); mange: /list. Endre: PUT (id+version). Slett: DELETE /product/unit/{id} kun når isDeletable=true (ikke brukt på produkter). Enheten settes på produktet via productUnit{id}. Krever bekreftelse ved skriving.

### Finne riktig standard enhetskode for EHF/PEPPOL
- **Kall:** `GET /product/unit/master`, `GET /product/unit/master/{id}`, `GET /product/unit`
- **Nøkkelord:** ehf enhet, peppol enhet, enhetskode, unece, rec 20, common code, c62, hur, kgm, e-faktura enhet, unit master
- GET /product/unit/master?name=|nameShort=|commonCode=|peppolName=|peppolSymbol=&isInactive=false (count er 2400 som standard, så hele listen kommer i ett kall) &fields=id,name,nameShort,commonCode,peppolName,peppolSymbol. Typiske koder: C62/EA = stk, HUR = time, KGM = kg, MTR = meter, LTR = liter. Masterlisten er skrivebeskyttet – sjekk at firmaets egne enheter (GET /product/unit) har riktig commonCode før EHF-fakturering.

### ✏️ Se rabattgrupper og knytte produkt til rabattgruppe
- **Kall:** `GET /product/discountGroup`, `GET /product/discountGroup/{id}`, `PUT /product/{id}`
- **Nøkkelord:** rabattgruppe, grossistrabatt, rabattkode, nettopris, discount group, efo rabattgruppe, grossistavtale
- GET /product/discountGroup?name=|number=&fields=id,name,number,nameAndNumber. Rabattgrupper kan kun leses via API (ingen POST/PUT). Knytt til produkt med PUT /product/{id} {id, version, discountGroup:{id}} – skrivende, krever bekreftelse.

### ✏️ Se eller endre logistikkinnstillinger (lagerplasser, foreslått varenummer, Bring)
- **Kall:** `GET /product/logisticsSettings`, `PUT /product/logisticsSettings`
- **Nøkkelord:** logistikkinnstillinger, lagerinnstillinger, slå på lagerplasser, foreslått varenummer, automatisk varenummer, innkjøpsordre standardkommentar, bring, logistics settings
- GET /product/logisticsSettings (for innlogget firma/klient) gir hasWarehouseLocation, moduleSuggestedProductNumber, suggestedProductNumber, purchaseOrderDefaultComment, moduleBring, rackbeatAgreementNumber (skrivebeskyttet). Endre med PUT /product/logisticsSettings med id, version og endrede felt. Firmainnstilling – krever bekreftelse.

### Finne transporttyper og hentesteder for bestilling fra grossist
- **Kall:** `GET /transportType`, `GET /transportType/{id}`, `GET /pickupPoint`, `GET /pickupPoint/{id}`
- **Nøkkelord:** transporttype, leveringsmåte, fraktmåte, hentested, henting, levering, grossistbestilling, innkjøpsordre frakt, pickup point, transport type
- GET /transportType?supplier= (påkrevd enum: DEFAULT_SUPPLIER, AHLSELL, SONEPAR, ONNINEN, SOLAR, ELEKTROSKANDIA, BERGAARD_AMUNDSEN, BROEDRENE_DAHL, HEIDENREICH, ELEKTROIMPORTOEREN) – BETA. NB: count er bare 3 som standard – sett f.eks. count=100; standard fields er id,nameKey,code,isPickUp (isPickUp=true betyr henting). Hentesteder: GET /pickupPoint?supplierId=&transportTypeId=&code=&name= (DEPRECATED). Id-ene brukes som transportType{id}/pickupPoint{id} på POST /purchaseOrder (innkjøp-gruppen).

### Se omsetning, varekostnad og bruttofortjeneste per produkt i en periode
- **Kall:** `GET /product`, `GET /ledger/posting`
- **Nøkkelord:** salg per vare, omsetning per produkt, varesalg, produktsalg, bruttofortjeneste, dekningsbidrag, db, varekostnad, solgte varer, hovedbok per produkt, sales by product
- Produkt-id: GET /product?productNumber=. GET /ledger/posting?dateFrom=&dateTo= (påkrevd, dateTo eksklusiv) &productId=<id>&accountNumberFrom=3000&accountNumberTo=3999&fields=date,amount,account(number),voucher(number),product(number,name),quantityAmount1 (antall der det er ført). Summer amount (inntekt er kredit/negativ). Varekostnad: samme kall med accountNumberFrom=4000&accountNumberTo=4999. For alle produkter: utelat productId og grupper lokalt på product.id.

### ✏️ Selge lagervare på ordre og plukke den fra lager
- **Kall:** `GET /order/orderline/orderLineTemplate`, `POST /order/orderline`, `PUT /order/orderline/{id}/:pickLine`, `PUT /order/orderline/{id}/:unpickLine`
- **Nøkkelord:** ordrelinje, selge vare, plukke, plukkliste, plukk, angre plukk, lagervare ordre, trekke fra lager, pick line, salgsordre
- Ordren må finnes (se salg-gruppen, POST /order). Forslag til linje med pris/mva: GET /order/orderline/orderLineTemplate?orderId=&productId= (begge påkrevd, BETA). Opprett: POST /order/orderline {order:{id}, product:{id}, count, inventory:{id}, inventoryLocation:{id}}. Plukk: PUT /order/orderline/{id}/:pickLine?inventoryId=&inventoryLocationId=&pickDate= (BETA; krever Logistics og aktivert funksjon for tilgjengelig lager; standardlager brukes hvis inventoryId mangler). Angre: PUT /order/orderline/{id}/:unpickLine. Krever bekreftelse.

### ✏️ Ta varer inn på lager (varemottak med eller uten innkjøpsordre)
- **Kall:** `POST /purchaseOrder`, `POST /purchaseOrder/orderline`, `PUT /purchaseOrder/goodsReceipt/{id}/:receiveAndConfirm`, `POST /purchaseOrder/goodsReceipt`, `GET /purchaseOrder/goodsReceipt`
- **Nøkkelord:** varemottak, motta varer, innkjøp til lager, innkjøpsordre, bestilling, øke lagerbeholdning, goods receipt, purchase order, mottakskontroll
- Logistics Basic; detaljer i innkjøp-gruppen. Med innkjøpsordre: POST /purchaseOrder {supplier:{id}, deliveryDate, ourContact …} + POST /purchaseOrder/orderline {purchaseOrder:{id}, product:{id}, count, unitCostCurrency}. Ved mottak av alt: PUT /purchaseOrder/goodsReceipt/{id}/:receiveAndConfirm?receivedDate=<dato> (påkrevd; id = innkjøpsordre-id; inventoryId= valgfritt, hovedlager er standard). Uten innkjøpsordre: POST /purchaseOrder/goodsReceipt {registrationDate, comment, goodsReceiptLines:[{product:{id}, quantityReceived, inventory:{id}, inventoryLocation:{id}}]} – status er STATUS_OPEN til mottaket er bekreftet. Oversikt: GET /purchaseOrder/goodsReceipt?receivedDateFrom=&receivedDateTo= (begge inkludert) &status=STATUS_OPEN|STATUS_CONFIRMED&withoutPurchase=true|false. Øker lagerbeholdningen. Krever bekreftelse.

### ✏️ Finne varer under minimumsbeholdning (bestillingsforslag) og sette minstebeholdning
- **Kall:** `GET /product`, `PUT /product/{id}`, `PUT /product/list`
- **Nøkkelord:** lavt lager, minimumsbeholdning, minstebeholdning, bestillingspunkt, bestillingsforslag, tomt på lager, utsolgt, påfyll, reorder, min stock level
- Finn: GET /product?isStockItem=true&isInactive=false&fields=id,number,name,availableStock,incomingStock,minStockLevel,supplier(name),mainSupplierProduct(number,costExcludingVatCurrency) og filtrer lokalt der availableStock+incomingStock < minStockLevel (det finnes ikke eget lavt-lager-endepunkt i v2). Sett minstebeholdning: PUT /product/{id} {id, version, minStockLevel} eller PUT /product/list (gjelder kun lagervarer i Logistics Basic) – skrivende, krever bekreftelse.

### Se resultatbudsjett for et produkt
- **Kall:** `GET /product`, `GET /resultbudget/product/{id}`
- **Nøkkelord:** budsjett per produkt, produktbudsjett, salgsbudsjett, resultatbudsjett, budsjett vare, budget
- Produkt-id: GET /product?productNumber=. GET /resultbudget/product/{id}?year=<åååå> (1900–2100, standard inneværende år). Sammenlign med faktisk: GET /ledger/posting med productId (se oppgaven om omsetning per produkt).

### Sjekke om klienten har logistikkmodulen (feilsøke 403 på lager-/produktgruppekall)
- **Kall:** `GET /company/salesmodules`, `GET /product/logisticsSettings`
- **Nøkkelord:** logistikkmodul, logistics basic, modul, 403, ikke tilgang, salgsmoduler, abonnement, lagermodul, sales modules
- GET /company/salesmodules (BETA) og se etter LOGISTICS i listen over aktive moduler. Kall merket 'Only available for Logistics Basic' (lagerplasser, produktgrupper, prishistorikk, innkjøpsordre, varemottak) gir 403/422 uten modulen. GET /product/logisticsSettings viser om lagerplasser er slått på (hasWarehouseLocation).

### ✏️ Opprette eget produkt fra grossistkatalog (EFO/NELFO-vare) med innkjøpspris
- **Kall:** `GET /product/external`, `GET /product`, `POST /product`, `POST /product/supplierProduct`
- **Nøkkelord:** efo-vare, nelfo-vare, importere fra grossist, elnummer til vare, nrf til vare, opprette vare fra katalog, grossistpris, innkjøpspris grossist, vvs-vare, elektrovare
- BETA. 1) GET /product/external?wholesaler=<enum>&elNumber=<nr> (eller nrfNumber=/name=; organizationNumber= påkrevd hvis wholesaler ikke er satt) &fields=id,name,elNumber,nrfNumber,costExcludingVatCurrency,priceExcludingVatCurrency,productUnit(id,nameShort),vatType(id). 2) Sjekk dublett: GET /product?name=<navn>&fields=id,number,name,elNumber,nrfNumber (elNumber/nrfNumber er skrivebeskyttet på Product og kan ikke settes via POST). 3) Opprett eget produkt: POST /product {name, number, priceExcludingVatCurrency, costExcludingVatCurrency, vatType{id}, productUnit{id}, account{id}}. 4) Ev. leverandørpris: POST /product/supplierProduct {name, number (grossistens varenr.), supplier{id}, costExcludingVatCurrency, resaleProduct{id}}. Skrivende – krever bekreftelse.

### Liste varelageret med beholdning og lagerverdi per vare nå (lagerliste til kunde/revisor)
- **Kall:** `GET /product`, `GET /product/inventoryLocation`, `GET /inventory/inventories`
- **Nøkkelord:** lagerliste, lagerverdi nå, varelagerliste, beholdningsliste, verdi på lager, lagerverdi per vare, revisor lagerliste, stock list, inventory value
- GET /product?isStockItem=true&isInactive=false&fields=id,number,name,stockOfGoods,availableStock,costExcludingVatCurrency,productUnit(nameShort) (lagerfeltene må stå eksplisitt i fields=; count=1000 standard – paginer). Lagerverdi per vare = stockOfGoods × costExcludingVatCurrency, summer lokalt. Per lager/lagerplass (Logistics Basic): GET /product/inventoryLocation?inventoryId=<id>&fields=product(number,name),inventoryLocation(name),stockOfGoods. For en historisk dato (f.eks. 31.12) bruk GET /inventory/inventories?dateFrom=&dateTo= (closingStock) – stockOfGoods er alltid dagens beholdning.

**Fallgruver:**
- Mange endepunkter krever modulen Logistics Basic (inventory/location, product/inventoryLocation, product/group, product/groupRelation, product/productPrice, samt purchaseOrder/goodsReceipt i innkjøp-gruppen). 403 eller valideringsfeil betyr som regel at modulen mangler – sjekk GET /company/salesmodules (LOGISTICS).
- Lagerfeltene på produkt (stockOfGoods, availableStock, incomingStock, outgoingStock) er 'available only on demand' – de returneres bare når de står eksplisitt i fields=.
- GET /inventory/inventories krever dateFrom og dateTo (begge inkludert), mens GET /ledger/posting og GET /balanceSheet har dateTo eksklusiv – vær nøye ved periodeavgrensning (f.eks. 31.12 vs 01.01).
- GET /product: parameteren number er DEPRECATED – bruk productNumber (liste). Product.number er en streng og må være unik.
- Product.isDeletable er deprecated og alltid false; prøv DELETE /product/{id} og deaktiver (isInactive=true) hvis produktet er i bruk.
- Alle PUT krever id og version; feil version gir konflikt. PUT /product/list og andre /list-kall tar en JSON-array, og én ugyldig rad kan stoppe hele kallet.
- Sletting av mange: DELETE /product/group/list og DELETE /inventory/location/list tar ?ids=1,2,3 i query, mens DELETE /product/groupRelation/list tar en JSON-array av id-er i body.
- POST /inventory/stocktaking: typeOfStocktaking (ALL_PRODUCTS_WITH_INVENTORIES standard | INCLUDE_PRODUCTS | NO_PRODUCTS) sendes som query-parameter; feltet i body er deprecated.
- GET /inventory/stocktaking/productline krever stocktakingId. Beskrivelsen nevner en /list-variant for POST, men den finnes ikke i spesifikasjonen – opprett linjer én og én.
- Å fullføre en varetelling (PUT /inventory/stocktaking/{id} isCompleted=true) justerer lagerbeholdningen og er i praksis irreversibelt – krev bekreftelse og kontroller bokføringen mot 1460/4290 etterpå.
- Tellelinjer har feltet counter (ansatt) – ikke hent eller vis det unødig (GDPR).
- Action-endepunkter med kolon: PUT /inventory/stocktaking/productline/{id}/:changeLocation (BETA, warehouseLocationId påkrevd), PUT /order/orderline/{id}/:pickLine og :unpickLine (BETA).
- POST /product/supplierProduct/getSupplierProductsByIds er et lesekall via POST (for lange id-lister); body er en array av objekter med id.
- product/external og transportType er BETA; pickupPoint er DEPRECATED. GET /product/external krever wholesaler eller organizationNumber, og sorting ignoreres. GET /transportType krever supplier (enum).
- Produktbilde (POST /product/{id}/image) og dokumentarkiv (POST /documentArchive/product/{id}) er multipart/form-data med feltet file; nytt bilde erstatter det gamle.
- Prisendring på produkt påvirker ikke eksisterende ordrelinjer/fakturaer. Priser sendes enten eks. eller inkl. mva – den andre beregnes ut fra vatType.
- Varelagerverdi i API-et er beholdning × kostpris; ukurans/nedskrivning og varelagerendring må vurderes og føres manuelt som bilag (skrivende).
- Avvikende standardverdier: GET /transportType har count=3 som standard (sett count eksplisitt), GET /product/supplierProduct returnerer bare fields=id,name,number som standard, GET /inventory/stocktaking/productline har count=10000 og GET /product/unit/master count=2400; øvrige lister har count=1000 – paginer med from.
- product/discountGroup og product/unit/master er skrivebeskyttet via API – kun GET. Rabattgrupper er grossistrabattgrupper, ikke kunderabatt (den settes på ordrelinje/kunde i salg-gruppen).
- Product-feltnavn er forvirrende i spec: priceExcludingVatCurrency/priceIncludingVatCurrency er SALGSpris (beskrevet som «price of purchase»), costExcludingVatCurrency er innkjøps-/kostpris. costPrice, profit, elNumber, nrfNumber og lagerfeltene er skrivebeskyttet.
- PUT /purchaseOrder/goodsReceipt/{id}/:receiveAndConfirm tar innkjøpsordre-id (ikke varemottak-id) i stien og krever receivedDate; GET /purchaseOrder/goodsReceipt har receivedDateFrom/To begge inkludert.
- GET /product/productPrice krever productId; toDate er eksklusiv, og showOnlyLastPrice=true overstyrer datoene.
- SupplierProduct.isMainSupplierProduct er kun tilgjengelig i pilot – kan ignoreres eller gi feil hos vanlige klienter.

## Anleggsmidler, årsoppgjør, SAF-T, signering (Penneo)

### Liste/søke opp anleggsmidler i anleggsregisteret
- **Kall:** `GET /asset`, `GET /asset/assetsExist`
- **Nøkkelord:** anleggsregister, anleggsmidler, liste anleggsmidler, driftsmidler, eiendeler, finn anleggsmiddel, asset list, oversikt anleggsmidler, anleggsregister i bruk, har klienten anleggsregister, asset register
- GET /asset med valgfritt name=/description= (inneholder-søk) eller id= (kommaseparert). Ingen dato- eller kontofilter. Bruk fields=id,name,dateOfAcquisition,acquisitionCost,lifetime,depreciationMethod,status,account(number,name),depreciationAccount(number),balanceOut,saleDate. Paginer med from/count (sett høy count eller paginer). Saldotall (balanceIn/balanceOut/annualDepreciation) er beregnet av Tripletex og read-only. GET /asset/assetsExist gir kun en boolsk verdi (summary: «Get if AssetOverview details is empty») – tolk varsomt og bekreft med GET /asset?count=1.

### Hente ett anleggsmiddel med saldo og avskrivningsgrunnlag
- **Kall:** `GET /asset/{id}`, `GET /asset`
- **Nøkkelord:** anleggsmiddel detaljer, saldo anleggsmiddel, bokført verdi, restverdi, årlig avskrivning, akkumulert avskrivning, avskrivningsgrunnlag, status avskrivning
- Finn id med GET /asset?name=... og hent GET /asset/{id}?fields=*. Read-only beregnede felt: startingBalance, balanceIn, balanceOut, balanceChange, depreciationBasis, numberOfMonths, annualDepreciation, depreciationAmount, totalDepreciationAmount, depreciationDiscrepancy, improvements, newHires (tilgang), salesAndOtherRealizations, accountingRelatedProfitOrLoss og status (READY_TO_DEPRECIATE, CORRECTION_NEEDED, COMPLETED, MISSING_INFO, REST_VALUE, NOTHING_TO_DEPRECIATE osv.). Skrivbare felt: acquisitionCost, incomingBalance, accumulatedDepreciation, depreciationRemainingValue, lifetime, depreciationMethod, depreciationRate, saleDate.

### ✏️ Registrere et nytt anleggsmiddel (driftsmiddel)
- **Kall:** `POST /asset`, `GET /ledger/account`
- **Nøkkelord:** nytt anleggsmiddel, registrere driftsmiddel, aktivere, aktivering, kjøp av maskin, inventar, opprette asset, levetid, avskrivningsmetode, ny bil, firmabil, kjøp av driftsmiddel, create asset
- 1) Finn balansekonto (11xx/12xx) og avskrivningskonto (60xx) med GET /ledger/account?number=1230&fields=id,number,name. 2) POST /asset med name, description, dateOfAcquisition (yyyy-MM-dd), acquisitionCost, account{id}, depreciationAccount{id}, lifetime (i MÅNEDER, 60 = 5 år), depreciationMethod (STRAIGHT_LINE | TAX_RELATED | MANUAL | CUSTOMIZED_AMOUNT | NO_DEPRECIATION), depreciationFrom (yyyy-MM-dd), evt. depreciationRate, depreciationRemainingValue (restverdi), incomingBalance, department{id}/project{id}. Historikk fra annet system: hasHistoryFromExternalSystem=true + externalLastDepreciation (dato), externalLastAccountedValue, externalAccumulatedDepreciation. Selve kjøpsbilaget kobles via posting.asset{id} (se oppgaven om å bokføre avskrivning/koble kjøp). Krever bekreftelse (skrivende).

### ✏️ Registrere mange anleggsmidler samtidig
- **Kall:** `POST /asset/list`, `GET /ledger/account`
- **Nøkkelord:** flere anleggsmidler, masseregistrering, bulk, opprette anleggsregister, batch, post asset list, mange driftsmidler
- POST /asset/list med en JSON-array av Asset-objekter (samme felt som POST /asset; lifetime i måneder). Slå opp konto-id-er først med GET /ledger/account?number=... Kontroller etterpå med GET /asset. For mange rader fra Excel: POST /asset/upload (BETA, se egen oppgave). Krever bekreftelse.

### ✏️ Endre et anleggsmiddel (levetid, avskrivningsmetode, konto, avdeling)
- **Kall:** `GET /asset/{id}`, `PUT /asset/{id}`
- **Nøkkelord:** endre anleggsmiddel, oppdatere levetid, endre avskrivningsmetode, korrigere anleggsmiddel, update asset, avskrivningssats
- Hent GET /asset/{id}?fields=* for gjeldende version. Send PUT /asset/{id} med id, version og feltene som endres (lifetime i måneder, depreciationMethod, depreciationRate, depreciationFrom, depreciationRemainingValue, acquisitionCost, account{id}, depreciationAccount{id}, department{id}, project{id}). Manglende/utdatert version gir konflikt. Beregnede saldofelt kan ikke settes. Sjekk status etterpå (CORRECTION_NEEDED/MISSING_INFO viser at noe mangler). Krever bekreftelse.

### ✏️ Registrere salg eller utrangering av et anleggsmiddel (avgang/realisasjon)
- **Kall:** `GET /asset/{id}`, `PUT /asset/{id}`, `POST /ledger/voucher`, `GET /ledger/account`
- **Nøkkelord:** salg av anleggsmiddel, avgang, realisasjon, utrangering, avhending, gevinst, tap, gevinst- og tapskonto, saledate, solgt bil
- 1) GET /asset/{id}?fields=id,version,balanceOut. 2) PUT /asset/{id} med id, version og saleDate=yyyy-MM-dd. 3) Bokfør salgsbilaget med POST /ledger/voucher der posteringen mot anleggskontoen har asset{id} satt (Posting.asset kobler posteringen til anleggsmiddelet); finn konto-id-er med GET /ledger/account. 4) Kontroller GET /asset/{id}?fields=salesAndOtherRealizations,accountingRelatedProfitOrLoss,balanceOut,status. Skattemessig gevinst- og tapskonto/saldoavskrivning har ikke eget API. Krever bekreftelse.

### ✏️ Bokføre avskrivning manuelt eller koble et kjøp til et anleggsmiddel
- **Kall:** `POST /ledger/voucher`, `GET /ledger/account`, `GET /ledger/voucherType`, `GET /asset`
- **Nøkkelord:** bokføre avskrivning, avskrivningsbilag, månedlig avskrivning, årlig avskrivning, koble postering til anleggsmiddel, tilgang, aktivering, 6010, 6000, depreciation voucher, periodisering
- Det finnes ikke et eget 'kjør avskrivninger'-endepunkt. Bokfør med POST /ledger/voucher {date, description, voucherType{id} (fra GET /ledger/voucherType), postings[]}: debet avskrivningskonto (f.eks. 6010) og kredit anleggskonto (12xx) – sett asset{id} på posteringen mot anleggskontoen slik at den havner i anleggsregisteret. Tilsvarende for kjøp (tilgang): asset{id} på debetposteringen mot 12xx. Bare bruttobeløp brukes (amountGross, og amountGrossCurrency likt for NOK), avrund til 2 desimaler, row fra 1 (0 er systemreservert), summen må gå i null. Beløpsforslag: annualDepreciation/depreciationAmount fra GET /asset/{id}. Krever bekreftelse.

### Se posteringer knyttet til et anleggsmiddel
- **Kall:** `GET /asset/{id}/postings`
- **Nøkkelord:** posteringer anleggsmiddel, avskrivningshistorikk, bilag anleggsmiddel, tilganger, hovedbok anleggsmiddel, asset postings
- GET /asset/{id}/postings?dateFrom=2025-01-01&dateToExclusive=2026-01-01&fields=id,date,description,amount,account(number),voucher(number,year). OBS: dateFrom og dateToExclusive har begge standardverdi = i dag, så uten dem blir listen tom – sett alltid periode (dateToExclusive er eksklusiv). Paginer med from/count.

### Avstemme anleggsregisteret mot hovedboken (saldobalanse 12xx)
- **Kall:** `GET /asset/balanceAccountsSum`, `GET /balanceSheet`, `GET /asset`
- **Nøkkelord:** avstemme anleggsmidler, anleggsavstemming, differanse anleggsregister, saldo 1200, balansekontoer, balanceaccountssum, kontroll anleggsmidler, årsavstemming
- 1) GET /asset/balanceAccountsSum gir ett tall (ResponseWrapperNumber, ingen parametre, ikke nærmere dokumentert – antagelig sum saldo på balansekontoene anleggsregisteret bruker). 2) GET /balanceSheet?dateFrom=2025-01-01&dateTo=2026-01-01&accountNumberFrom=1000&accountNumberTo=1299&fields=account(number,name),balanceIn,balanceChange,balanceOut (dateFrom/dateTo påkrevd, dateTo eksklusiv). 3) Summer balanceOut fra GET /asset?fields=account(number),balanceOut per konto og sammenlign; differanser tyder på posteringer uten asset-kobling eller feil inngående saldo.

### ✏️ Importere anleggsregister (inngående saldo) fra Excel
- **Kall:** `POST /asset/upload`, `GET /asset`
- **Nøkkelord:** importere anleggsmidler, excel import, anleggsregister import, inngående saldo anleggsmidler, startsaldo, oppstart ny klient, asset upload, konvertering
- [BETA] POST /asset/upload som multipart/form-data med feltet file (Excel i Tripletex' standardformat) og query isPreview* og startDate* (skal være 1. januar, f.eks. 2025-01-01). Kjør ALLTID først isPreview=true og vis resultatet (ListResponseAssetAccountRow: accountNumber, accountName, assets, balanceDifference = beløp på kontoen som ikke er knyttet til et anleggsmiddel etter import). Deretter isPreview=false etter bekreftelse. Kontroller med GET /asset. Angre med DELETE /asset/deleteImport.

### ✏️ Angre siste anleggsimport eller slette inngående saldo i anleggsregisteret
- **Kall:** `DELETE /asset/deleteImport`, `DELETE /asset/deleteStartingBalance`, `GET /asset`
- **Nøkkelord:** angre import, slette import anleggsmidler, slette startsaldo, tilbakestille anleggsregister, delete import, starting balance
- [BETA] DELETE /asset/deleteImport sletter den siste Excel-importen av anleggsmidler. DELETE /asset/deleteStartingBalance sletter startsaldoen for anleggsregisteret. Ingen parametre – virker på hele klientens anleggsregister. Destruktive – krever eksplisitt bekreftelse. Kontroller etterpå med GET /asset.

### ✏️ Slette eller duplisere et anleggsmiddel
- **Kall:** `DELETE /asset/{id}`, `POST /asset/duplicate/{id}`, `PUT /asset/{id}`, `GET /asset`
- **Nøkkelord:** slette anleggsmiddel, fjerne anleggsmiddel, kopiere anleggsmiddel, duplisere, duplicate asset, delete asset
- Finn id med GET /asset?name=... DELETE /asset/{id} sletter (kan feile hvis anleggsmiddelet har tilknyttede posteringer – vurder heller saleDate ved avgang). POST /asset/duplicate/{id} (ingen body) lager en kopi, nyttig for like maskiner/PC-er; juster kopien med PUT /asset/{id} (hent version først). Begge krever bekreftelse.

### ✏️ Laste opp eller hente dokumentasjon (faktura, kontrakt) på et anleggsmiddel
- **Kall:** `GET /documentArchive/asset/{id}`, `POST /documentArchive/asset/{id}`
- **Nøkkelord:** dokumentasjon anleggsmiddel, vedlegg anleggsmiddel, kjøpekontrakt, faktura driftsmiddel, dokumentarkiv, document archive asset
- [BETA] GET /documentArchive/asset/{id} (valgfritt periodDateFrom inkl./periodDateTo eksl.) lister arkiverte dokumenter for anleggsmiddelet. POST /documentArchive/asset/{id} laster opp fil som multipart/form-data (felt file). Opplasting krever bekreftelse.

### Eksportere SAF-T regnskapsfil for et år
- **Kall:** `GET /saft/exportSAFT`
- **Nøkkelord:** saf-t eksport, eksportere saft, saft fil, skatteetaten saft, revisor saft, saft xml, saft 1.3, export saft, regnskapsfil, bokettersyn, kontrollfil, saft zip, saf-t 1.30
- [BETA] GET /saft/exportSAFT?year=2025&version=1.3. year* (heltall) er påkrevd. version: "1.2" (standard hvis utelatt), "1.3" eller "1.4". SAF-T Financial 1.30 er gjeldende krav fra Skatteetaten fra 2025 – sett version eksplisitt. Svaret er application/octet-stream (zip), ikke JSON – lagre til fil (f.eks. saft_2025.zip). Kan ta tid for store klienter; kun lesende.

### ✏️ Importere SAF-T fra et annet regnskapssystem (konvertering/oppstart)
- **Kall:** `POST /saft/importSAFT`, `GET /saft/status`, `GET /ledger/account`
- **Nøkkelord:** saf-t import, importere saft, bytte regnskapssystem, konvertering, migrering, flytte regnskap til tripletex, overføre historikk, inngående balanse fra saft, import saft
- [BETA] POST /saft/importSAFT som multipart/form-data. Påkrevde deler (18): saftFile (XML; 1.2/1.3/1.4 autodetekteres), mappingFile (Excel med kontoplanmapping, mal: tripletex.no/resources/examples/saft_account_mapping.xls) og alle 16 boolske flagg: importCustomerVendors, createMissingAccounts, importStartBalanceFromOpening, importStartBalanceFromClosing, importVouchers, importDepartments, importProjects, tripletexGeneratesCustomerNumbers, createCustomerIB, updateAccountNames, createVendorIB, overrideVoucherDateOnDiscrepancy, overwriteCustomersContacts, onlyActiveCustomers, onlyActiveAccounts, updateStartBalance. Velg enten åpnings- eller utgående saldo som IB, ikke begge. Følg opp med GET /saft/status (status STARTED/COMPLETED/FAILED, failureErrorMessage, importLog). Svært inngripende – krever eksplisitt bekreftelse, helst testet på tom klient/sandbox først.

### Sjekke status på siste SAF-T-import
- **Kall:** `GET /saft/status`
- **Nøkkelord:** saft status, status import, importstatus, er saft importert, saft feil
- [BETA] GET /saft/status uten parametre. Returnerer SaftImportLog for siste import: importNumber, status (STARTED, COMPLETED, FAILED, BEING_REVERSED, UNKNOWN), failureErrorMessage og importLog (HTML). Tomt svar = ingen import er kjørt for selskapet. Gjelder kun import, ikke eksport.

### ✏️ Reversere (angre) siste SAF-T-import
- **Kall:** `POST /saft/reverse`, `GET /saft/status`
- **Nøkkelord:** reversere saft, angre saft import, rulle tilbake import, slette saft import, reverse saft
- [BETA] Sjekk først GET /saft/status (importNumber, status). POST /saft/reverse (ingen body/parametre) reverserer kun den SISTE importen og returnerer hvilket importNumber som ble reversert (status REVERSED). Destruktivt – krever eksplisitt bekreftelse.

### Hente saldobalanse for årsoppgjøret
- **Kall:** `GET /balanceSheet`, `GET /ledger/annualAccount`
- **Nøkkelord:** saldobalanse, råbalanse, årsoppgjør, arsoppgjor, balanse 31.12, resultat, balansekontoer, trial balance, utgående saldo, aarsoppgjoer, årsregnskap, resultatregnskap, balanse, saldoliste, kontrollbalanse
- GET /balanceSheet?dateFrom=2025-01-01&dateTo=2026-01-01 (dateTo er EKSKLUSIV – bruk 1. januar året etter for helt år). Valgfritt accountNumberFrom/To (f.eks. 1000-2999 balanse, 3000-8999 resultat), includeActiveAccountsWithoutMovements=true, departmentId/projectId. fields=account(number,name),balanceIn,balanceChange,balanceOut. Bekreft regnskapsårets start/slutt med GET /ledger/annualAccount?yearFrom=2025&yearTo=2026.

### Sjekke regnskapsår og om perioder er låst/lukket
- **Kall:** `GET /ledger/annualAccount`, `GET /ledger/annualAccount/{id}`, `GET /ledger/accountingPeriod`
- **Nøkkelord:** regnskapsår, regnskapsperiode, låst periode, lukket periode, periodelåsing, avslutte år, annual account, accounting period, avstemt periode
- GET /ledger/annualAccount?yearFrom=2025&yearTo=2026 (yearTo eksklusiv) gir regnskapsårets id, year, start og end; GET /ledger/annualAccount/{id} for ett år. GET /ledger/accountingPeriod?startFrom=2025-01-01&startTo=2026-01-01&fields=name,number,start,end,isClosed viser hvilke perioder som er lukket. Låsing/lukking av perioder og årsavslutning finnes ikke som offentlig endepunkt.

### ✏️ Registrere eller kontrollere åpningsbalanse (inngående balanse)
- **Kall:** `GET /ledger/voucher/openingBalance`, `GET /ledger/voucher/openingBalance/>correctionVoucher`, `POST /ledger/voucher/openingBalance`, `DELETE /ledger/voucher/openingBalance`, `GET /ledger/account`
- **Nøkkelord:** åpningsbalanse, inngående balanse, ib, startbalanse, oppstart, korreksjonsbilag, opening balance, ny klient
- Les: GET /ledger/voucher/openingBalance og korreksjonsbilaget med GET /ledger/voucher/openingBalance/>correctionVoucher. Opprett: POST /ledger/voucher/openingBalance med voucherDate (MÅ være 1. i en måned, helst 1. januar), balancePostings [{account{id}, amount}], samt customerPostings/supplierPostings/employeePostings for reskontro. Alle bevegelser før datoen nulles i et eget korreksjonsbilag; ubalanse føres automatisk på en hjelpekonto. DELETE /ledger/voucher/openingBalance sletter også korreksjonsbilaget. Finn konto-id-er med GET /ledger/account. employeePostings gjelder ansatte – bruk minimalt (GDPR). Skrivende kall krever bekreftelse.

### Kontrollere åpne poster i reskontro per 31.12
- **Kall:** `GET /ledger/posting/openPost`, `GET /ledger/closeGroup`
- **Nøkkelord:** åpne poster, apne poster, reskontro, kundereskontro, leverandørreskontro, avstemme reskontro, uoppgjorte poster, årsavstemming, open post, lukkede poster
- GET /ledger/posting/openPost?date=2026-01-01 (date* er eksklusiv, dvs. åpne poster per 31.12.2025) med accountId eller accountNumberFrom/To (f.eks. 1500 kunder, 2400 leverandører), customerId/supplierId. Sett sorted=false for raskere svar på store kontoer. fields=date,description,amount,customer(name),supplier(name),voucher(number). Se avstemte/lukkede postgrupper med GET /ledger/closeGroup?dateFrom=...&dateTo=... (begge påkrevd).

### ✏️ Opprette årsavstemmings-kontekst (balanseavstemming) for en klient
- **Kall:** `POST /balance/reconciliation/annual/context`
- **Nøkkelord:** årsavstemming, balanseavstemming, avstemming balanse, annual balance reconciliation, avstemmingskontekst
- POST /balance/reconciliation/annual/context med body {customerId, year} (begge writeOnly). Summary: «Create a annualBalance reconciliation context for a customer» – lite dokumentert; customerId er trolig regnskapsbyråets kunde/klient avstemmingen gjelder. Eksisterende: udokumentert GET /accountingOffice/reconciliations i byråkontoen (se hovedbok). Test i sandbox først. Skrivende, krever bekreftelse.

### Slå opp næringstyper (business activity types) for årsoppgjøret
- **Kall:** `GET /yearEnd/enumType/businessActivityTypes`
- **Nøkkelord:** næringstype, naeringstype, virksomhetstype, næringsspesifikasjon, skattekategori, primærnæring, jordbruk, business activity type, avdeling næring
- GET /yearEnd/enumType/businessActivityTypes?query=... (valgfritt id=, from/count) gir id og displayName. Brukes til å skille næringer/skattekategorier (f.eks. jordbruk vs. annen næring), bl.a. via Department.businessActivityTypeId. Kun oppslag.

### Sjekke signeringsstatus for årsregnskapet (Penneo)
- **Kall:** `GET /yearEnd/penneo/signingStatus`
- **Nøkkelord:** signeringsstatus, er årsregnskapet signert, signert, penneo status, signing status, signering aktivert
- GET /yearEnd/penneo/signingStatus?year=2025 (year* påkrevd) gir value.signingActivated (saksmappe opprettet for året) og value.signingComplete (alle har signert), basert på Tripletex' egen DB-post – kan ligge etter Penneo. Virker statusen utdatert, se oppgaven «Synkronisere signeringsstatus med Penneo» (skrivende).

### ✏️ Synkronisere signeringsstatus med Penneo
- **Kall:** `POST /yearEnd/penneo/sync`, `GET /yearEnd/penneo/signingStatus`
- **Nøkkelord:** synkronisere penneo, oppdatere signeringsstatus, penneo sync, status stemmer ikke, signert men vises ikke, refresh signing
- POST /yearEnd/penneo/sync (ingen body/parametre) oppdaterer Tripletex' database med gjeldende tilstand i Penneo (svar: ResponseWrapperString). Kontroller deretter GET /yearEnd/penneo/signingStatus?year=. Endrer lagret status i Tripletex – be om bekreftelse.

### Liste Penneo-saksmapper for årsregnskapet
- **Kall:** `GET /yearEnd/penneo/session`, `GET /yearEnd/penneo/casefiles`
- **Nøkkelord:** penneo saksmapper, case files, casefiles, hente saksmappe, signeringsoppdrag, penneo session
- GET /yearEnd/penneo/session?year=2025 autentiserer mot Penneo og returnerer saksmappene for året; deretter kan GET /yearEnd/penneo/casefiles?year=2025 brukes. year er formelt valgfri, men angi den alltid. Svaret er ResponseWrapperString – value er en rå JSON-streng fra Penneo som må parses (caseFileId, dokument-id-er, signer-id-er). Kan inneholde navn/e-post på signatarer – vis aldri disse (GDPR).

### ✏️ Sende årsregnskapet til signering i Penneo (opprette saksmappe, dokument og signaturlinjer)
- **Kall:** `GET /yearEnd/penneo/session`, `POST /yearEnd/penneo/casefiles`, `POST /yearEnd/penneo/documents`, `POST /yearEnd/penneo/signature-lines`, `POST /yearEnd/penneo/casefiles/{caseFileId}/activate`, `GET /yearEnd/penneo/signingStatus`
- **Nøkkelord:** sende til signering, signere årsregnskap, opprette saksmappe, laste opp årsregnskap, signaturlinje, aktivere signering, styret signerer, bankid signering, penneo
- 1) GET /yearEnd/penneo/session?year= for autentisering. 2) POST /yearEnd/penneo/casefiles {title, year} → caseFileId (parse value-strengen). 3) POST /yearEnd/penneo/documents {caseFileId, title, pdfBase64} (PDF base64-kodet) → documentId. 4) Per signatar: POST /yearEnd/penneo/signature-lines {documentId, role, signerId, year} (lager signaturlinje, kobler signatar og konfigurerer e-post i ett); signerId = signatar registrert i årsoppgjørsmodulen (styreleder/styremedlem/daglig leder). 5) POST /yearEnd/penneo/casefiles/{caseFileId}/activate?year= – kobler signatarer, konfigurerer e-post og aktiverer (signeringsforespørsler sendes). 6) Følg opp med GET /yearEnd/penneo/signingStatus?year=. Trinn 2-5 er skrivende og aktivering sender e-post – krever eksplisitt bekreftelse.

### ✏️ Oppdatere, erstatte eller fjerne et dokument i en Penneo-saksmappe
- **Kall:** `PUT /yearEnd/penneo/documents/{documentId}`, `DELETE /yearEnd/penneo/documents/{documentId}`, `GET /yearEnd/penneo/casefiles`
- **Nøkkelord:** erstatte dokument, ny versjon årsregnskap, oppdatere pdf, slette dokument penneo, feil i årsregnskap, update document
- Finn documentId i GET /yearEnd/penneo/casefiles?year= (parse value). PUT /yearEnd/penneo/documents/{documentId} med body {documentId, title, pdfBase64} erstatter innholdet. DELETE /yearEnd/penneo/documents/{documentId} fjerner dokumentet fra saksmappen. Endring er i praksis bare mulig før mappen er aktivert/signert – ellers slett saksmappen og start på nytt. Krever bekreftelse.

### Laste ned signert årsregnskap fra Penneo
- **Kall:** `GET /yearEnd/penneo/documents/{documentId}/download`, `GET /yearEnd/penneo/casefiles`
- **Nøkkelord:** laste ned signert, signert pdf, signert årsregnskap, download document, hente signert dokument
- Finn documentId via GET /yearEnd/penneo/casefiles?year= (parse value-strengen). GET /yearEnd/penneo/documents/{documentId}/download returnerer application/pdf (binært – lagre til fil, ikke JSON). 404 = dokumentet finnes ikke (text/plain), 500 = feil mot Penneo.

### ✏️ Administrere signatarer i Penneo: purre (sende lenke på nytt), reaktivere eller fjerne
- **Kall:** `POST /yearEnd/penneo/casefiles/{caseFileId}/signers/{signerId}/resend`, `POST /yearEnd/penneo/casefiles/{caseFileId}/signers/{signerId}/reactivate`, `GET /yearEnd/penneo/casefiles`, `DELETE /yearEnd/penneo/casefiles/{caseFileId}/signers/{signerId}`, `POST /yearEnd/penneo/signature-lines`
- **Nøkkelord:** purre signatur, sende lenke på nytt, resend, påminnelse signering, reaktivere signatar, ikke signert, signeringslenke, fjerne signatar, slette signatar, feil signatar, bytte styremedlem
- Finn caseFileId og signerId i GET /yearEnd/penneo/casefiles?year= (parse value-strengen). Purre: POST .../signers/{signerId}/resend sender signeringslenken på nytt (e-post). Reaktivere avvist/deaktivert signatar: POST .../signers/{signerId}/reactivate. Fjerne feil signatar: DELETE /yearEnd/penneo/casefiles/{caseFileId}/signers/{signerId}, og legg evt. til riktig med POST /yearEnd/penneo/signature-lines {documentId, role, signerId, year}. Alle er skrivende og resend/reactivate sender e-post – krever bekreftelse. Vis aldri signatarens navn/e-post i svar (GDPR) – bruk rolle eller «signatar 1».

### ✏️ Administrere kopimottakere (f.eks. revisor) på en Penneo-saksmappe
- **Kall:** `GET /yearEnd/penneo/recipients`, `POST /yearEnd/penneo/recipients`, `DELETE /yearEnd/penneo/recipients/{id}`
- **Nøkkelord:** kopimottaker, kopi til revisor, mottaker, recipient, legge til mottaker, fjerne mottaker
- Les: GET /yearEnd/penneo/recipients?caseFileId= (påkrevd; svar er ResponseWrapperString som må parses). Legg til: POST /yearEnd/penneo/recipients {caseFileId, name, email, storeAsContact (standard false)}. Fjern: DELETE /yearEnd/penneo/recipients/{id}?caseFileId= (caseFileId påkrevd også her). Navn/e-post er personopplysninger – ikke vis dem i svar; skrivende kall krever bekreftelse.

### ✏️ Avbryte signering ved å slette en Penneo-saksmappe
- **Kall:** `DELETE /yearEnd/penneo/casefiles/{caseFileId}`, `GET /yearEnd/penneo/casefiles`, `POST /yearEnd/penneo/sync`, `GET /yearEnd/penneo/signingStatus`
- **Nøkkelord:** slette saksmappe, avbryte signering, trekke tilbake, starte signering på nytt, delete case file
- Finn caseFileId via GET /yearEnd/penneo/casefiles?year=. DELETE /yearEnd/penneo/casefiles/{caseFileId} sletter hele saksmappen i Penneo (dokumenter og signaturlinjer følger med). Kjør POST /yearEnd/penneo/sync og kontroller GET /yearEnd/penneo/signingStatus?year= etterpå. Irreversibelt – krever eksplisitt bekreftelse.

### ✏️ Bokføre årsoppgjørsposteringer (skattekostnad, utbytte, disponering av resultat)
- **Kall:** `POST /ledger/voucher`, `GET /ledger/account`, `GET /ledger/voucherType`, `GET /balanceSheet`, `GET /ledger/accountingPeriod`
- **Nøkkelord:** årsoppgjørsposteringer, arsoppgjorsposteringer, skattekostnad, betalbar skatt, utsatt skatt, utbytte, avsatt utbytte, disponering, overføring annen egenkapital, årsavslutning, tilleggsposteringer, year-end entries, 8300, 8800, 2800
- Det finnes ikke egne endepunkter for skatteberegning eller resultatdisponering. 1) Hent resultat før skatt med GET /balanceSheet?dateFrom=2025-01-01&dateTo=2026-01-01&accountNumberFrom=3000&accountNumberTo=8999. 2) Finn konto-id-er (f.eks. 8300 betalbar skatt, 8320 endring utsatt skatt, 2500 betalbar skatt, 2120 utsatt skatt, 8800/8960 overføringer, 2800 avsatt utbytte, 2050 annen egenkapital) med GET /ledger/account?number=...&fields=id,number,name. 3) Sjekk at perioden ikke er lukket (GET /ledger/accountingPeriod, isClosed). 4) POST /ledger/voucher med date=2025-12-31, description, voucherType{id} (GET /ledger/voucherType) og balanserte postings (amountGross/amountGrossCurrency, 2 desimaler, row fra 1). Krever bekreftelse.

### ✏️ Kontrollere og bokføre månedlige/årlige avskrivninger for alle anleggsmidler
- **Kall:** `GET /asset`, `GET /asset/{id}/postings`, `GET /asset/balanceAccountsSum`, `GET /balanceSheet`, `POST /ledger/voucher`
- **Nøkkelord:** kjøre avskrivninger, kjore avskrivninger, månedlige avskrivninger, avskrivning alle anlegg, avskrivningskjøring, bokføre avskrivninger, 6000, 6010, 6015, ordinære avskrivninger, saldoavskrivning, lineær avskrivning, avskrivning mangler, depreciation run
- Krever navngitt klient. 1) `GET /asset`?fields=id,name,account(number),depreciationAccount(number),acquisitionCost,lifetime,depreciationMethod,dateOfAcquisition (verifiser feltnavn med lookup). 2) Per anlegg: `GET /asset/{id}/postings` for perioden – finnes avskrivningspostering hver måned? 3) `GET /balanceSheet` på 60xx for perioden mot forventet sum (kost/levetid per måned for lineære). 4) `GET /asset/balanceAccountsSum` mot 11xx–12xx. v2 har ikke endepunkt for å «kjøre» avskrivninger fra anleggsregisteret – gjøres i Tripletex-UI. Hvis brukeren ber om det og bekrefter: `POST /ledger/voucher` debet 60xx / kredit 11xx–12xx uten mva, og koble til anlegget som i «Bokføre avskrivning manuelt» (arsoppgjor).

**Fallgruver:**
- Asset.lifetime er i MÅNEDER, ikke år (5 år = 60).
- depreciationMethod-enum: MANUAL | TAX_RELATED | STRAIGHT_LINE | CUSTOMIZED_AMOUNT | NO_DEPRECIATION. status er read-only (UNKNOWN, MANUAL, NO_DEPRECIATION, INVALID_DATE, MISSING_TRANS_TYPE, MISSING_INFO, READY_TO_DEPRECIATE, CORRECTION_NEEDED, COMPLETED, REST_VALUE, NOTHING_TO_DEPRECIATE).
- Saldo-/avskrivningsfelt på Asset (balanceIn, balanceOut, annualDepreciation, depreciationAmount, accountingRelatedProfitOrLoss m.fl.) er read-only – kan ikke settes via PUT.
- GET /asset/{id}/postings: dateFrom og dateToExclusive har standardverdi i dag – angi alltid periode ellers blir listen tom.
- POST /asset/upload, DELETE /asset/deleteImport, DELETE /asset/deleteStartingBalance og alle /saft/*-kall er BETA – kan endre seg og gi 403 hvis ikke aktivert for klienten.
- POST /asset/upload: startDate skal være 1. januar, og isPreview=true bør alltid kjøres først; balanceDifference viser beløp på kontoen som ikke dekkes av anleggsmidler.
- GET /saft/exportSAFT returnerer application/octet-stream (zip), ikke JSON; year* er påkrevd og version er valgfri med standard 1.2 – sett version=1.3 (eller 1.4) eksplisitt for gjeldende SAF-T-krav.
- POST /saft/importSAFT krever multipart med saftFile, mappingFile og samtlige 16 boolske flagg; den er svært inngripende (oppretter kontoer, kunder/leverandører, bilag, IB). Bare siste import kan reverseres med POST /saft/reverse.
- Penneo-endepunktene returnerer ResponseWrapperString: value er en rå JSON-streng fra Penneo som må parses for å få caseFileId, documentId og signerId.
- Penneo krever at klienten har Penneo-integrasjon/årsoppgjørsmodul aktivert; kall GET /yearEnd/penneo/session først for å autentisere. 403/401 betyr typisk manglende modul, tilgang eller Penneo-kobling.
- Signatarer (styreleder, styremedlemmer, daglig leder) må være registrert i Tripletex' årsoppgjørsmodul – det finnes ikke offentlig API for å opprette dem; POST .../activate?year= og POST /yearEnd/penneo/signature-lines (year i body) finner dem for angitt år.
- POST /yearEnd/penneo/casefiles/{caseFileId}/activate og .../resend sender e-post til signatarer – regn dem som utsending og få eksplisitt bekreftelse.
- GET /yearEnd/penneo/recipients og DELETE /yearEnd/penneo/recipients/{id} krever query caseFileId.
- GET /yearEnd/penneo/signingStatus krever year og leser Tripletex' egen DB-post; POST /yearEnd/penneo/sync (skrivende) oppdaterer den fra Penneo.
- Penneo-mottakere og signatarer inneholder navn og e-post (personopplysninger) – vis aldri disse i svar, bruk rolle eller «signatar 1/2».
- GET /balanceSheet og GET /ledger/posting/openPost bruker eksklusiv sluttdato (dateTo/date): for hele 2025 bruk dateTo=2026-01-01.
- GET /ledger/closeGroup krever både dateFrom og dateTo.
- POST /ledger/voucher/openingBalance: voucherDate må være 1. i en måned; alt før datoen nulles i et korreksjonsbilag, og DELETE sletter også korreksjonsbilaget.
- Det finnes ikke et offentlig endepunkt for å 'kjøre avskrivninger'; avskrivning bokføres som vanlig bilag (POST /ledger/voucher) med posting.asset{id} satt på anleggskontoposteringen – ellers havner den ikke i anleggsregisteret og gir differanse mot hovedboken.
- Skattemessige avskrivninger, saldoskjema (RF-1084), gevinst- og tapskonto, skattemelding og næringsspesifikasjon har ingen offentlige endepunkter i API v2.
- PUT /asset/{id} krever id og gjeldende version i body (hent med GET /asset/{id} først).
- Penneo-kallene (session, casefiles, recipients og alle skrivende) returnerer ResponseWrapperString; year er formelt valgfri på session/casefiles/activate, men angi den alltid.
- Penneo-dokumenter lastes opp som base64-PDF i pdfBase64; GET /yearEnd/penneo/documents/{documentId}/download returnerer application/pdf (binært).
- GET /saft/status gjelder bare siste SAF-T-import (SaftImportLog: importNumber, status STARTED/COMPLETED/FAILED/BEING_REVERSED/UNKNOWN); tomt svar betyr ingen import.
- POST /asset/upload, POST /saft/importSAFT og POST /documentArchive/asset/{id} er multipart/form-data – ikke JSON.
- DELETE /asset/deleteImport og DELETE /asset/deleteStartingBalance tar ingen parametre og virker på hele klientens anleggsregister.
- POST /balance/reconciliation/annual/context er lite dokumentert (body {customerId, year}) og har ingen tilhørende GET – test i sandbox.

## Selskap, innstillinger, autentisering, webhooks, lisenser, oppslag

### Liste alle klientene jeg (regnskapsføreren) har innloggingstilgang til og finne klient-ID
- **Kall:** `GET /company/>withLoginAccess`
- **Nøkkelord:** klienter, klientliste, mine klienter, regnskapsklienter, kunder, klient-id, company id, companyid, proxy, innloggingstilgang, hvilke klienter, finn klient, withloginaccess, regnskapsfører, regnskapsforer, revisor, klientoversikt, regnskapsbyrå, portefølje, proxy login
- GET /company/>withLoginAccess med companyId 0 (egen bedrift) som brukernavn i Basic auth. Bruk fields=id,name,organizationNumber,type (count default 1000, bruk from/count ved flere). Feltet id er klientens company-id som brukes som brukernavn i Basic auth ("<id>:<sessionToken>") for alle videre kall mot klienten – ikke customerCompanyId. Unngå email/phoneNumber i fields (kan være personopplysninger for ENK). Lokalt: `npm run connect` lister klientene dynamisk – aldri hardkod eller filtrer listen, og gjør ingenting mot en klient før brukeren har navngitt den. '>' må være med i stien (aggregat-endepunkt).

### Sjekke hvem jeg er innlogget som og hvilket selskap tokenet peker mot
- **Kall:** `GET /token/session/>whoAmI`
- **Nøkkelord:** whoami, hvem er jeg, innlogget, innlogget bruker, hvilken bedrift, hvilket selskap, sjekk token, test tilkobling, tilkobling, proxy, employeeisproxy, company id, min bruker
- GET /token/session/>whoAmI (med companyId 0 eller klientens id som brukernavn). Bruk fields=employeeId,actualEmployeeId,companyId,company(id,name,organizationNumber),employeeIsProxy,loggedInWithConnect,language – ikke employee(*) (GDPR). companyId i svaret bekrefter hvilken klient kallet faktisk går mot; employeeIsProxy=true betyr regnskapsfører-innlogging hos klient (actualEmployeeId = den faktiske brukeren bak proxy). God første test ved 401/403. Lokalt: `npm run probe -- "klient"`.

### Hente firmaopplysninger for en klient (navn, org.nr., selskapsform, adresse, valuta, oppstartsdato)
- **Kall:** `GET /token/session/>whoAmI`, `GET /company/{id}`, `GET /company/>withLoginAccess`
- **Nøkkelord:** firmaopplysninger, selskapsinfo, firmainfo, organisasjonsnummer, org.nr, orgnr, adresse, forretningsadresse, valuta, basisvaluta, startdato, firmanavn, company, selskap, klientinfo
- 1) Finn company-id via GET /token/session/>whoAmI?fields=companyId (når kallet går mot klienten) eller fra GET /company/>withLoginAccess?fields=id,name. 2) GET /company/{id}?fields=id,version,name,organizationNumber,type,startDate,endDate,address(addressLine1,postalCode,city,country(isoAlpha2Code)),currency(code) med klientens id som companyId i auth. Alternativt i ett kall: whoAmI?fields=company(name,organizationNumber,type,currency(code)). Firmanavn/org.nr. er greit å vise; unngå e-post/telefon (kan være personopplysninger for ENK).

### Finne selskapsform/organisasjonsform til en klient (AS, ENK, ANS, DA, NUF osv.)
- **Kall:** `GET /company/{id}`, `GET /company/>withLoginAccess`
- **Nøkkelord:** selskapsform, organisasjonsform, foretaksform, as, enk, enkeltpersonforetak, ans, da, nuf, sa, asa, stiftelse, forening, type, årsoppgjør, arsoppgjor, skattemelding, næringsoppgave
- GET /company/{id}?fields=name,organizationNumber,type – type er enum (NONE, ENK, AS, NUF, ANS, DA, PRE, KS, ASA, BBL, BRL, GFS, SPA, SF, IKS, KF_FKF, FCD, EOFG, BA, STI, ORG, ESEK, SA, SAM, BO, VPFO, OS, FLI, Other). For mange klienter samtidig: GET /company/>withLoginAccess?fields=id,name,type. Relevant for valg av årsoppgjørsmodul (YEAR_END_REPORTING_AS/ENK/…) og skattemelding.

### ✏️ Oppdatere firmaopplysninger (adresse, e-post, telefon, navn, selskapsform)
- **Kall:** `GET /token/session/>whoAmI`, `GET /company/{id}`, `PUT /company`
- **Nøkkelord:** oppdatere firma, endre adresse, ny adresse, endre firmanavn, endre selskapsform, firmaopplysninger, oppdatere selskap, company update, endre e-post, endre telefon, flytting
- 1) Bekreft klient med GET /token/session/>whoAmI?fields=companyId,company(name). 2) GET /company/{id}?fields=id,version,name,type,organizationNumber,address(*) for gjeldende version. 3) PUT /company med body {id, version, <kun feltene som endres>} – delvis oppdatering via PUT er støttet. Skrivbare felt: name, startDate, endDate, organizationNumber, email, phoneNumber, phoneNumberMobile, faxNumber, address, type, currency. Ingen id i stien – oppdaterer selskapet kallet går mot (companyId i auth). Skrivende: krever brukerens bekreftelse. 409 = versjonskonflikt, hent på nytt.

### Sjekke hvilke moduler klienten har aktivert (lønn, prosjekt, anleggsregister, årsoppgjør, OCR/bilagsmottak)
- **Kall:** `GET /company/salesmodules`, `GET /subscription/packages`
- **Nøkkelord:** moduler, aktive moduler, salgsmoduler, har klienten lønn, lønnsmodul, lonnsmodul, prosjektmodul, anleggsregister, anleggsmidler, årsoppgjørsmodul, arsoppgjorsmodul, ocr, bilagsmottak, ehf, api-modul, abonnement, hvorfor 403, funksjonalitet
- GET /company/salesmodules?fields=name,costStartDate (BETA) gir aktive moduler (f.eks. WAGE, SMART_WAGE, PROJECT, SMART_PROJECT, FIXED_ASSETS_REGISTER, YEAR_END_REPORTING_AS, OCR, ELECTRONIC_VOUCHERS, API_V2, LOGISTICS). For en mer lesbar oversikt med aktiv/tilgjengelig og pris: GET /subscription/packages?fields=title,active,available,monthlyPrice. Nyttig når et endepunkt gir 403 – ofte mangler modulen.

### ✏️ Aktivere en ny modul for klienten (f.eks. lønn, prosjekt, anleggsregister eller årsoppgjør)
- **Kall:** `GET /company/salesmodules`, `GET /subscription/packages`, `POST /company/salesmodules`
- **Nøkkelord:** aktivere modul, slå på modul, sla pa modul, bestille modul, legge til modul, lønn, lonn, prosjekt, anleggsregister, årsoppgjør, arsoppgjor, sales module, oppgradere, kjøpe modul, kjope modul
- 1) GET /company/salesmodules?fields=name,costStartDate for å se hva som allerede er aktivt (evt. GET /subscription/packages?fields=title,active,available,monthlyPrice for pris). 2) POST /company/salesmodules med body {name: <enum, f.eks. WAGE | SMART_WAGE | PROJECT | SMART_PROJECT | TIME_TRACKING | FIXED_ASSETS_REGISTER | YEAR_END_REPORTING_AS | YEAR_END_REPORTING_ENK | YEAR_END_REPORTING_ANS/DA/SA/STI/ORG/FLI/NUF | OCR | ELECTRONIC_VOUCHERS | LOGISTICS>, costStartDate: 'YYYY-MM-DD'}. BETA, svarer 201. Mange moduler har ekstra kostnad for klienten – krever alltid eksplisitt bekreftelse. Det finnes ikke noe API-kall for å deaktivere en modul.

### Se hvilke abonnementspakker og priser som finnes for kontoen
- **Kall:** `GET /subscription/packages`
- **Nøkkelord:** abonnement, pakker, priser, pris, hva koster, månedspris, manedspris, tripletex-pakke, basis, smart, komplett, mikro, tilgjengelige moduler, kostnad
- GET /subscription/packages?fields=id,title,shortDescription,active,available,monthlyPrice,yearlyPrice,startUpPrice,perUserPrice,canDeactivate,possibleStartDate. Svaret er en ResponseWrapper der listen ligger i value (ikke values), og endepunktet har ingen paging. Kun lesing.

### ✏️ Si opp / stenge Tripletex-kontoen til en klient (med eller uten lesetilgang)
- **Kall:** `GET /token/session/>whoAmI`, `PUT /subscription/cancel`
- **Nøkkelord:** si opp, oppsigelse, stenge konto, avslutte abonnement, avslutte kunde, legge ned, avvikling, lesetilgang, arkiv, oppbevaringsplikt, cancel subscription, slette konto
- 1) Bekreft klient med GET /token/session/>whoAmI?fields=companyId,company(name,organizationNumber). 2) PUT /subscription/cancel med body {readAccess: true|false, nbOfYears: <antall år med lesetilgang>}. Husk bokføringslovens oppbevaringsplikt (5 år for primærdokumentasjon) – velg normalt readAccess=true. Svært inngripende og kan ha kostnad: kun etter eksplisitt bekreftelse fra brukeren.

### ✏️ Gjenåpne en stengt Tripletex-konto med tidligere moduler
- **Kall:** `PUT /subscription/reactivate`
- **Nøkkelord:** gjenåpne, gjenapne, reaktivere konto, åpne konto igjen, apne konto igjen, reactivate, angre oppsigelse, abonnement
- PUT /subscription/reactivate (ingen body) gjenåpner kontoen med tidligere moduler. Medfører fakturering av abonnement – krever brukerens bekreftelse.

### Slå opp land og landkode (ISO) for å sette land på kunde, leverandør, ansatt eller adresse
- **Kall:** `GET /country`, `GET /country/{id}`
- **Nøkkelord:** land, landkode, country, iso, iso-kode, norge, sverige, utland, utenlandsk kunde, utenlandsk leverandør, adresse, country id, se, dk, de
- GET /country?code=NO,SE,DK&fields=id,name,isoAlpha2Code,isoAlpha3Code (code tar kommaseparert liste med ISO-koder; count default 1000). Bruk id i f.eks. address.country.id / postalAddress.country.id ved POST/PUT av kunde/leverandør/ansatt. GET /country/{id} for enkeltoppslag. isDisabled=false for kun aktive land. Slå alltid opp id i stedet for å hardkode.

### Slå opp kommune, kommunenummer og arbeidsgiveravgiftssone
- **Kall:** `GET /municipality`, `GET /municipality/query`
- **Nøkkelord:** kommune, kommunenummer, fylke, aga-sone, arbeidsgiveravgiftssone, sone 1a, sone 2, sone 5, arbeidsgiveravgift, aga, virksomhet, underenhet, a-melding, lønn, lonn, municipality
- Søk på navn: GET /municipality/query?query=Bergen&fields=id,number,name,county (BETA, «containing»-søk; merk count default 25). Full liste med soner: GET /municipality?includePayrollTaxZones=true&fields=id,number,name,county,payrollTaxZone (count default 1000 – dekker alle kommuner; /municipality har ikke navnefilter). Kommune-id brukes på virksomhet/underenhet (Division.municipality) som styrer AGA-sone i a-meldingen.

### ✏️ Se og endre virksomheter/underenheter (divisjoner) og deres kommune for a-melding
- **Kall:** `GET /company/divisions`, `GET /division`, `PUT /division/{id}`, `GET /municipality/query`
- **Nøkkelord:** virksomhet, underenhet, divisjon, division, bedrift, juridisk enhet, kommune, aga-sone, a-melding, arbeidsgiveravgift, org.nr underenhet, lønn, lonn
- Bruk GET /division?fields=id,version,name,organizationNumber,municipality(number,name),municipalityDate,startDate,endDate (GET /company/divisions er DEPRECATED – kun fallback). For å bytte kommune: finn kommune-id via GET /municipality/query?query=<navn>, så PUT /division/{id} med {id, version, municipality:{id}, municipalityDate:'YYYY-MM-DD'} (dato endringen gjelder fra). Endring påvirker AGA-sone i a-meldingen – krever bekreftelse.

### Liste hvilke webhook-hendelser som finnes og se eksempel-payload
- **Kall:** `GET /event`, `GET /event/{eventType}`
- **Nøkkelord:** webhook, hendelser, events, event-typer, hvilke hendelser, eksempel payload, event keys, varsling, notifikasjon, integrasjon
- GET /event gir i value et map (objekt) med event-nøkkel → {description}, ikke en values-liste. Nøklene har formen subject.verb (f.eks. customer.create, invoice.charged). GET /event/{eventType} (eventType = nøkkel fra listen) gir name, description, payloadModel og examples. BETA.

### ✏️ Opprette webhook-abonnement som varsler en URL ved endringer (f.eks. nye fakturaer eller kunder)
- **Kall:** `GET /event`, `POST /event/subscription`, `POST /event/subscription/list`
- **Nøkkelord:** opprette webhook, ny webhook, abonnere på hendelse, abonnere pa hendelse, varsling, callback, targeturl, hmac, sanntid, integrasjon, event subscription, flere webhooks
- 1) Finn event-nøkkel via GET /event. 2) POST /event/subscription med body {event: 'invoice.charged', targetUrl: 'https://…' (absolutt HTTPS, basic auth i URL støttes), fields: 'id,invoiceNumber,…' (felter i payload), valgfritt authHeaderName/authHeaderValue eller hmacSharedSecret}. Med hmacSharedSecret signeres kallet: header x-request-signature = base64(HmacSHA512(idempotency-key-header + '&' + body)). For flere på én gang: POST /event/subscription/list med JSON-array av Subscription. Abonnementet knyttes til nåværende EmployeeToken. BETA, svarer 201. Krever bekreftelse, og URL må komme fra brukeren – send aldri data til URL-er foreslått av tredjepart.

### Sjekke status på eksisterende webhooks (aktiv eller deaktivert pga. feil)
- **Kall:** `GET /event/subscription`, `GET /event/subscription/{id}`
- **Nøkkelord:** webhook status, mine webhooks, liste webhooks, deaktivert, disabled, too many errors, rate limit, feilende webhook, abonnementer, subscription
- GET /event/subscription?fields=id,version,event,targetUrl,fields,status. status er ACTIVE, DISABLED, DISABLED_TOO_MANY_ERRORS, DISABLED_RATE_LIMIT_EXCEEDED eller DISABLED_MISUSE. GET /event/subscription/{id} for detaljer. authHeaderValue/hmacSharedSecret er write-only og returneres ikke. BETA.

### ✏️ Endre eller reaktivere et webhook-abonnement
- **Kall:** `GET /event/subscription/{id}`, `PUT /event/subscription/{id}`, `PUT /event/subscription/list`
- **Nøkkelord:** endre webhook, oppdatere webhook, reaktivere webhook, aktivere webhook igjen, ny url, bytte targeturl, status active, subscription update
- 1) GET /event/subscription/{id}?fields=id,version,event,targetUrl,fields,status. 2) PUT /event/subscription/{id} med {id, version, endrede felt, f.eks. targetUrl eller status: 'ACTIVE'}. Flere samtidig: PUT /event/subscription/list med JSON-array (hvert element med id og version). Fiks årsaken (endepunkt som feiler) før reaktivering. BETA, krever bekreftelse.

### ✏️ Slette ett eller flere webhook-abonnementer
- **Kall:** `GET /event/subscription`, `DELETE /event/subscription/{id}`, `DELETE /event/subscription/list`
- **Nøkkelord:** slette webhook, fjerne webhook, avslutte webhook, stoppe varsling, delete subscription, rydde webhooks
- Finn id-er med GET /event/subscription?fields=id,event,targetUrl,status. Slett én: DELETE /event/subscription/{id}. Slett flere: DELETE /event/subscription/list?ids=1,2,3 (ids påkrevd, kommaseparert). BETA. Sletting krever bekreftelse.

### Lage session token fra refresh token (tlxr_) for å kunne gjøre API-kall
- **Kall:** `POST /token/session/:createFromRefreshToken`
- **Nøkkelord:** session token, refresh token, tlxr, jwt, logge inn, innlogging, autentisering, token utløpt, 401, fornye token, ttl, createfromrefreshtoken
- POST /token/session/:createFromRefreshToken med body {refreshToken: 'tlxr_…', ttlSeconds: 300–28800}. Svaret gir value.token = sessionToken, brukes som passord i Basic auth med companyId (0 = egen bedrift, ellers klient-id) som brukernavn. Håndteres automatisk av src/auth.js i den lokale koblingen – tokenet i .env skal aldri vises, logges eller sendes videre. Endrer ingen regnskapsdata.

### Lage session token fra consumer token og employee token
- **Kall:** `POST /token/session/:create`, `PUT /token/session/:create`
- **Nøkkelord:** session token, consumer token, employee token, logge inn, autentisering, innlogging, expirationdate, sessiontoken, basic auth
- Foretrukket: POST /token/session/:create med body {consumerToken, employeeToken, expirationDate: 'YYYY-MM-DD'} (feltbeskrivelsene i spec er byttet om – følg feltnavnene). PUT /token/session/:create med query-parametere er DEPRECATED og legger tokens i URL/logger – unngå. Bruk value.token som passord i Basic auth ('<companyId|0>:<sessionToken>'). Endrer ingen regnskapsdata. Aldri vis eller logg tokens.

### ✏️ Logge ut / ugyldiggjøre et session token
- **Kall:** `DELETE /token/session/{token}`
- **Nøkkelord:** logge ut, utlogging, slette token, ugyldiggjøre token, ugyldiggjore, revoke, invalidere session, sikkerhet
- DELETE /token/session/{token} med session-tokenet i stien. Påvirker kun innloggingen, ikke regnskapsdata. Tokenet havner i URL – ikke logg forespørselen. Normalt unødvendig når refresh-token-flyten med kort TTL brukes.

### ✏️ Opprette et employee token (API-nøkkel) for en ansatt
- **Kall:** `GET /employee`, `PUT /token/employee/:create`
- **Nøkkelord:** employee token, api-nøkkel, api nokkel, ny api-tilgang, opprette token, integrasjonsbruker, systembruker, tilgangsnøkkel, tilgangsnokkel, api-bruker
- 1) Finn employeeId med GET /employee?fields=id (filtrer minimalt – GDPR, ikke skriv ut navn/e-post). 2) PUT /token/employee/:create med query-parametere tokenName*, consumerName*, employeeId*, companyOwned* (true/false), expirationDate* (YYYY-MM-DD). Kun utvalgte consumere har lov (ellers 403). Tokenet i svaret er hemmelig – aldri vis eller logg det. Krever bekreftelse. Vanligvis opprettes employee token manuelt av administrator under brukerinnstillinger → API-tilgang.

### Slå opp consumer token (hvilken integrasjon/API-konsument et token tilhører)
- **Kall:** `GET /token/consumer/byToken`
- **Nøkkelord:** consumer token, api consumer, integrasjon, hvilken app, applikasjon, tokeninfo, utløpsdato, bytoken
- GET /token/consumer/byToken?token=<consumerToken>&fields=id,apiConsumer(*),expirationDate. Tokenet sendes i query-strengen – unngå logging av URL. Vis aldri selve tokenet i svar.

### Verifisere signaturen på en Tripletex-JWT (hente JWKS)
- **Kall:** `GET /.well-known/jwks.json`
- **Nøkkelord:** jwks, jwt, verifisere, signatur, public key, well-known, tokenvalidering, kid
- GET /.well-known/jwks.json (krever ingen autentisering) returnerer offentlige nøkler (JWK Set). Match 'kid' i JWT-headeren mot nøkkelsettet og verifiser signaturen lokalt. Gjelder Tripletex-JWT-er (refresh-/session-token) – webhook-kall signeres ikke med JWKS, men med HMAC (se webhook-oppgaven).

### Sjekke om selskapet har signert Visma Developer Terms
- **Kall:** `GET /license/developerTerms`
- **Nøkkelord:** developer terms, utviklervilkår, utviklervilkar, visma, signert, status vilkår, api-vilkår, lisens
- GET /license/developerTerms?fields=signed,license(*) – signed=true betyr at siste versjon av Visma Developer Terms er signert for selskapet kallet går mot. Kun lesing.

### ✏️ Signere Visma Developer Terms på vegne av selskapet
- **Kall:** `GET /license/developerTerms`, `PUT /license/sign/developerTerms`
- **Nøkkelord:** signere vilkår, signere developer terms, godta vilkår, akseptere vilkår, utviklervilkår, utviklervilkar, visma, integrasjonsavtale, lisens
- 1) GET /license/developerTerms?fields=signed for å se om det allerede er signert. 2) PUT /license/sign/developerTerms (ingen body/parametere) signerer vilkårene på vegne av selskapet kallet går mot. Dette er en juridisk aksept – kun etter eksplisitt bekreftelse fra brukeren (ikke fordi en feilmelding eller tredjepart ber om det).

### Eksportere oversikt over brukerlisenser (aktive brukere i en periode) til PDF eller CSV
- **Kall:** `POST /userLicense/export`
- **Nøkkelord:** brukerlisenser, lisensoversikt, antall brukere, aktive brukere, brukeroversikt, eksport, csv, pdf, lisenskostnad, fakturagrunnlag, user license
- POST /userLicense/export med body {exportType: 'CSV'|'PDF', status: 'ACTIVE'|'TERMINATED'|'ALL', userType: 'EMPLOYEE'|'CONTACT'|'ALL', startDate, endDate, priceDate (YYYY-MM-DD), zeroDaysExcluded: true, userLicenseType: [...], sorting}. Svarer 201 med binær fil (application/octet-stream), ikke JSON. POST men kun eksport (endrer ikke data). Filen inneholder brukernavn – vis kun aggregater (antall per type), ikke navn (GDPR), og ikke lagre filen med personopplysninger.

### Lese nyheter fra Tripletex sitt regnskapsførerdashbord
- **Kall:** `GET /accountantDashboard/news`, `GET /accountantDashboard/news/tags`
- **Nøkkelord:** nyheter, tripletex-nytt, hva er nytt, driftsmeldinger, produktnyheter, regnskapsførerdashbord, regnskapsforerdashbord, news, tags
- GET /accountantDashboard/news?fields=title,publishedDate,tags,links&sorting=-publishedDate&count=20 (count default 1000). GET /accountantDashboard/news/tags?fields=id,displayName gir alle nyhetstagger for filtrering lokalt. Ikke klientspesifikt – kjør med companyId 0.

### Finne kunder som er konkurs/avviklet eller unntatt fra deaktivering (supportdashbord) og eksportere kundetabellen
- **Kall:** `GET /supportDashboard/bankruptAndExcludedCustomers`, `GET /supportDashboard/export`
- **Nøkkelord:** konkurs, avviklet, tvangsavvikling, likvidert, suspendert, ekskludert, supportdashbord, kundetabell, eksport, partner
- GET /supportDashboard/bankruptAndExcludedCustomers?fields=tripletexCompanyId,orgNumber,name,bankrupt,liquidated,forceLiquidated,suspended,excludedFromDisabling,excludedFromDeletion. Eksport: GET /supportDashboard/export?type=…&filter=…&startDateRange=YYYY-MM-DD&endDateRange=YYYY-MM-DD (alle fire påkrevd; type/filter har ingen dokumenterte enum-verdier i spec) – svaret er en binær fil (octet-stream). Beregnet for Tripletex-support/partnere – forvent 403 for vanlige regnskapsbrukere.

### Feilsøke 401/403 – sjekke innlogging, klient, moduler og tilganger
- **Kall:** `GET /token/session/>whoAmI`, `GET /company/salesmodules`, `GET /employee/entitlement`, `GET /employee/entitlement/client`
- **Nøkkelord:** 403, 401, forbidden, ingen tilgang, mangler tilgang, tilganger, rettigheter, entitlements, feilsøke, feilsoke, feil klient, modul mangler, tilgangsstyring
- 1) GET /token/session/>whoAmI?fields=employeeId,companyId,employeeIsProxy – bekreft at companyId er riktig klient (401 = token utløpt/ugyldig; lag nytt session token). 2) GET /company/salesmodules?fields=name – mangler modulen (f.eks. WAGE, PROJECT, FIXED_ASSETS_REGISTER) gir det ofte 403. 3) GET /employee/entitlement?fields=name,entitlementId (egen bruker som standard) eller GET /employee/entitlement/client?customerId=<klient>&fields=name,entitlementId (BETA) for rettigheter hos klienten. 403 (kode 9000) = AuthorisationManager sier nei: manglende rolle/modul eller at employee tokenet ikke har nødvendige rettigheter. Ikke skriv ut navn på ansatte (GDPR).

**Fallgruver:**
- Autentisering: Basic auth med brukernavn = companyId (0/blank = egen bedrift, ellers klientens id fra GET /company/>withLoginAccess) og passord = sessionToken. Feil companyId gir data fra feil klient eller 401/403 – bekreft alltid med GET /token/session/>whoAmI.
- Session token lages fra refresh token (tlxr_) med POST /token/session/:createFromRefreshToken; ttlSeconds må være 300–28800 (5 min–8 t). Utløpt token gir 401 – lag nytt. Tokens skal aldri vises, logges eller sendes videre.
- PUT /token/session/:create er DEPRECATED (tokens i query-string havner i logger) – bruk POST /token/session/:create med body.
- '>'-stier er aggregater/spesialoppslag (/company/>withLoginAccess, /token/session/>whoAmI) og ':'-stier er handlinger (/token/session/:create, /token/employee/:create); tegnene må være med i URL-en.
- PUT /company har ingen id i stien – den oppdaterer selskapet kallet går mot (companyId i auth). Send id og version i body; 409 = versjonskonflikt.
- GET /company/divisions er DEPRECATED – bruk GET /division (virksomheter/underenheter) i stedet.
- company/salesmodules, event, event/subscription og municipality/query er BETA og kan endre seg. POST /company/salesmodules kan påføre klienten kostnader og kan normalt ikke reverseres via API.
- Mange endepunkter i andre grupper krever at en modul er aktiv (lønn, prosjekt, anleggsregister, logistikk, årsoppgjør). 403 skyldes ofte manglende modul eller manglende rettigheter på employee tokenet – sjekk GET /company/salesmodules og GET /employee/entitlement.
- Webhooks: targetUrl må være absolutt HTTPS; abonnementet er knyttet til nåværende EmployeeToken; authHeaderValue og hmacSharedSecret er write-only. Abonnement deaktiveres automatisk ved mange feil (DISABLED_TOO_MANY_ERRORS) eller rate-limit – må reaktiveres med PUT og status ACTIVE.
- DELETE /event/subscription/list krever query-parameter ids (kommaseparert liste).
- PUT /token/employee/:create er kun tillatt for utvalgte consumere (ellers 403), og alle fem query-parametere (tokenName, consumerName, employeeId, companyOwned, expirationDate) er påkrevd.
- PUT /subscription/cancel, PUT /subscription/reactivate og PUT /license/sign/developerTerms er forretningskritiske/juridiske handlinger på kontonivå – kun etter eksplisitt bekreftelse fra brukeren, og husk oppbevaringsplikten (velg readAccess=true ved oppsigelse).
- POST /userLicense/export er en ren eksport (endrer ikke data) men returnerer fil med brukernavn – vis kun aggregater (GDPR).
- supportDashboard-endepunktene er ment for Tripletex-support/partnere; forvent 403 for vanlige regnskapsbrukere. GET /supportDashboard/export krever type, filter, startDateRange og endDateRange.
- Rate limiting per ansatt per API-consumer: se headerne X-Rate-Limit-Limit/Remaining/Reset; 429 betyr vent til perioden er over.
- Bruk alltid fields= for å begrense svar; whoAmI og company kan returnere personopplysninger (employee(*), e-post, telefon) som ikke skal skrives ut.
- Paging: count har default 1000 på de fleste listeendepunkter her, men GET /municipality/query har default count=25 – sett count eksplisitt ved søk som kan gi mange treff.
- Svarformat: GET /event returnerer value som et map (event-nøkkel → beskrivelse), og GET /subscription/packages returnerer listen i value (ikke values) uten paging. Vanlige søk (/country, /municipality, /event/subscription) bruker values + from/count.
- POST /event/subscription/list og PUT /event/subscription/list tar en JSON-array av Subscription-objekter (ikke ett objekt). PUT-elementene må ha id og version.
- Webhook-signering: med hmacSharedSecret settes header x-request-signature = base64(HmacSHA512(idempotency-key + '&' + body)). JWKS (/.well-known/jwks.json) brukes til Tripletex-JWT-er, ikke til webhook-verifisering.
- I spec er feltbeskrivelsene i PostSessionTokenBody byttet om (employeeToken beskrevet som consumer-token og omvendt) – følg feltnavnene consumerToken/employeeToken.
- POST /token/session/:createFromRefreshToken og GET /.well-known/jwks.json har ingen security i spec (krever ikke Basic auth); alle andre kall krever Basic auth med sessionToken.
- GET /supportDashboard/export og POST /userLicense/export returnerer binær fil (application/octet-stream), ikke JSON – lagre/parse som fil og ikke logg innholdet (kan inneholde navn).
- Opprettende POST-kall (salesmodules, event/subscription, session token) svarer 201; DELETE svarer 204 uten body.
- 'abonnement' er tvetydig: tag subscription = Tripletex-kontoens abonnement/pakker (oppsigelse, gjenåpning), mens event/subscription = webhook-abonnementer.
- Udokumenterte kall: at et kall mangler i openapi.json betyr ikke at det ikke finnes (avstemmingsmodulen har flere, f.eks. GET /accountingOffice/reconciliations, .../comments, PUT .../:complete). Sonder med GET: 404 «Object not found» = stien finnes ikke; 405 Method Not Allowed = stien finnes med annen metode; 422 «Expected number» = ordet ble tolket som {id} (sier ingenting). 403/422 på et skrivekall: les validationMessages – ofte en forretningsregel (f.eks. manglende kommentar), ikke manglende tilgang. Si «ikke funnet» og hva som er prøvd, aldri «finnes ikke», før UI-ets nettverkskall er sjekket. Beste kilde: UI-ets JavaScript under /page/<modul>/assets/*.js (søk etter "/v2/") eller nettverksloggen – asynkrone kall (SSE/EventSource) vises ikke alltid i loggen.

## Tripletex-connectoren (MCP) mot API v2

Verktøy merket «kun connector» har ikke noe offentlig v2-endepunkt – bruk connectoren til dem.

| Verktøy | Hva | API v2-kall |
|---|---|---|
| `check_client_account_status` | Sjekker om en klient har egen Tripletex-konto og hva byrået kan gjøre (koble til/opprette) – kun connector (delvis v2: se kall). | **kun connector** |
| `establish_client_access` | Oppretter eller kobler til en klients Tripletex-konto for byrået (klientopprettelse) – kun connector. | **kun connector** |
| `estimate_client_account_price` | Anslår pris for ny klientkonto (pakke, bilagsnivå, tilleggstjenester) – kun connector. | **kun connector** |
| `fetch_report` | Henter Tripletex-rapporter (resultat, saldobalanse, reskontro, prosjektøkonomi, nøkkeltall m.m.) som tabell – kun connector (delvis v2: se kall). | **kun connector** |
| `fetch_taxcards` | Henter skattekort-svar fra Skatteetaten og lagrer dem i Tripletex (steg 2 etter bestilling) – kun connector. | **kun connector** |
| `get_current_datetime` | Returnerer dato, klokkeslett, ukenummer og måned i Oslo-tid – kun connector (lokalt verktøy uten API-kall). | **kun connector** |
| `get_customer_invoice_send_types` | Viser hvilke sendekanaler (e-post, EHF, eFaktura, AvtaleGiro, papir) som er tilgjengelige for en kunde – kun connector (delvis v2: se kall). | **kun connector** |
| `get_immediate_manager` | Viser en ansatts nærmeste leder – kun connector (delvis v2 via avdelingsleder, se kall). | **kun connector** |
| `get_report_details` | Beskriver rapporter i rapportkatalogen (kolonner, filtre, sorteringsakser) – kun connector. | **kun connector** |
| `get_taxcard_status` | Viser hvilke ansatte som har eller mangler skattekort for et år – kun connector. | **kun connector** |
| `list_client_account_admins` | Lister kolleger i byrået med rollen brukeradministrator i klientkontoer – kun connector (delvis v2: se kall). | **kun connector** |
| `list_direct_reports` | Lister ansatte som har en gitt person som nærmeste leder – kun connector (delvis v2 via avdeling, se kall). | **kun connector** |
| `lookup_company_in_brreg` | Slår opp norsk foretak i Brønnøysundregistrene på org.nr., navn eller adresse – kun connector (ekstern kilde). | **kun connector** |
| `order_taxcards` | Bestiller skattekort fra Skatteetaten via Altinn for navngitte ansatte – kun connector. | **kun connector** |
| `reject_expense` | Avviser et levert utlegg/reiseregning med kommentar tilbake til den ansatte – kun connector (delvis v2 uten kommentar, se kall). | **kun connector** |
| `set_month_payout` | Setter utbetaling/trekk i lønn (timer) for fleksi- og feriesaldo på en månedstimeliste – kun connector (v2 kan bare lese, se kall). | **kun connector** |
| `tripletex_run_script` | Kjører JavaScript i sandkasse mot connectorens leseverktøy for mange selskaper samtidig – kun connector (tilsvarer egne skript med connect()). | **kun connector** |
| `update_result_budget` | Erstatter resultatbudsjett for én bærer og ett år per konto – kun connector (v2 kan bare lese, se kall). | **kun connector** |
| `add_accommodation_line` | Legger til en satsbasert nattillegg-linje på en åpen eller avvist reiseregning. | `POST /travelExpense/accommodationAllowance`, `GET /travelExpense/rateCategory`, `GET /travelExpense/zone` |
| `add_expense_lines` | Legger til kostnadslinjer (utlegg) på et åpent eller avvist utlegg eller en reiseregning. | `POST /travelExpense/cost`, `GET /travelExpense/costCategory`, `GET /travelExpense/paymentType` |
| `add_mileage_line` | Legger til en kjøregodtgjørelse-linje (km, evt. bompenger) på en åpen eller avvist reiseregning. | `POST /travelExpense/mileageAllowance`, `POST /travelExpense/cost`, `GET /travelExpense/rateCategory` |
| `add_per_diem_line` | Legger til diett (statlige satser) på en åpen eller avvist reiseregning, evt. med måltidstrekk. | `POST /travelExpense/perDiemCompensation`, `DELETE /travelExpense/perDiemCompensation/{id}`, `GET /travelExpense/rate`, `GET /travelExpense/zone` |
| `approve_expense` | Godkjenner et levert utlegg eller en reiseregning som leder/attestant. | `PUT /travelExpense/:approve` |
| `approve_month` | Godkjenner en timelistemåned for én eller flere ansatte og låser timene. | `PUT /timesheet/month/:approve` |
| `approve_week` | Godkjenner en timelisteuke for én eller flere ansatte og låser timene. | `PUT /timesheet/week/:approve` |
| `clock_in` | Starter stemplingsuret (inn-stempling) for innlogget bruker på en aktivitet/prosjekt. | `PUT /timesheet/timeClock/:start` |
| `clock_out` | Stopper det løpende stemplingsuret (ut-stempling) for innlogget bruker. | `GET /timesheet/timeClock/present`, `PUT /timesheet/timeClock/{id}/:stop` |
| `complete_month` | Markerer en timelistemåned som ferdig (levert til godkjenning). | `PUT /timesheet/month/:complete` |
| `complete_week` | Markerer en timelisteuke som ferdig (levert til godkjenning). | `PUT /timesheet/week/:complete` |
| `create_department` | Oppretter en ny avdeling med valgfritt nummer og avdelingsleder. | `POST /department` |
| `create_employee` | Oppretter ansatt med første arbeidsforhold (a-meldingsklar) i ett kall. | `POST /employee`, `POST /employee/employment`, `POST /employee/employment/details`, `GET /division`, `GET /employee/employment/occupationCode`, `GET /department` |
| `create_expense` | Oppretter et utlegg (refusjon av egne kostnader) med kostnadslinjer, valgfritt levert direkte. | `POST /travelExpense`, `POST /travelExpense/cost`, `PUT /travelExpense/:deliver`, `GET /travelExpense/costCategory` |
| `create_travel_expense` | Oppretter en reiseregning med reisedetaljer og valgfrie kostnads-, km-, diett- og nattilleggslinjer. | `POST /travelExpense`, `POST /travelExpense/cost`, `POST /travelExpense/mileageAllowance`, `POST /travelExpense/perDiemCompensation`, `POST /travelExpense/accommodationAllowance`, `PUT /travelExpense/:deliver` |
| `credit_invoice` | Lager kreditnota som nuller en hel utgående faktura. | `PUT /invoice/{id}/:createCreditNote` |
| `delete_customer` | Sletter en kunde permanent (blokkert hvis kunden har historikk – arkiver i stedet). | `DELETE /customer/{id}` |
| `delete_expense` | Sletter et åpent eller avvist utlegg/reiseregning permanent. | `DELETE /travelExpense/{id}` |
| `delete_expense_receipt` | Sletter et vedlagt kvitteringsvedlegg på et åpent eller avvist utlegg/reiseregning. | `GET /travelExpense/{travelExpenseId}/attachment`, `DELETE /travelExpense/{travelExpenseId}/attachment` |
| `delete_hours` | Sletter én eller flere timeføringer (på id eller dato+prosjekt+aktivitet). | `GET /timesheet/entry`, `DELETE /timesheet/entry/{id}` |
| `delete_order` | Sletter en salgsordre permanent (blokkert ved fakturaer/timer/bilag). | `DELETE /order/{id}` |
| `delete_supplier` | Sletter en leverandør permanent (blokkert hvis leverandøren har historikk – arkiver i stedet). | `DELETE /supplier/{id}` |
| `delete_wage_type_registration` | Sletter lønnsart-registreringer (overtid/tillegg) fra timelisten for én ansatt. | `GET /timesheet/salaryTypeSpecification`, `DELETE /timesheet/salaryTypeSpecification/{id}`, `DELETE /timesheet/salaryProjectTypeSpecification/{id}` |
| `execute_contact` | Oppretter eller oppdaterer en kontaktperson hos en kunde. | `POST /contact`, `PUT /contact/{id}` |
| `execute_customer` | Oppretter eller oppdaterer en kunde (adresser, e-post, sendemåte, kategorier, betalingsbetingelser). | `POST /customer`, `PUT /customer/{id}`, `GET /customer/category` |
| `execute_employee` | Oppdaterer felter på en eksisterende ansatt (kontaktinfo, avdeling, fødselsnr., kontonr., brukertype). | `GET /employee/{id}`, `PUT /employee/{id}` |
| `execute_employment` | Oppretter, endrer eller avslutter et arbeidsforhold for en eksisterende ansatt. | `POST /employee/employment`, `PUT /employee/employment/{id}`, `POST /employee/employment/details`, `PUT /employee/employment/details/{id}`, `GET /employee/employment/occupationCode` |
| `execute_hour_registration` | Registrerer eller oppdaterer timeføringer (upsert per dato/prosjekt/aktivitet) for én ansatt. | `GET /timesheet/entry`, `POST /timesheet/entry`, `PUT /timesheet/entry/{id}`, `POST /timesheet/entry/list`, `GET /activity/>forTimeSheet` |
| `execute_order` | Oppretter en salgsordre med ordrelinjer (produkt eller fritekst) for en kunde. | `POST /order`, `POST /order/orderline/list`, `GET /currency`, `GET /ledger/vatType`, `GET /product/{id}` |
| `execute_product` | Oppretter eller oppdaterer et produkt (vare/tjeneste) med pris og mva. | `POST /product`, `PUT /product/{id}` |
| `execute_project_operation` | Oppretter, oppdaterer, lukker eller sletter prosjekter i batch (opptil 100). | `POST /project`, `PUT /project/{id}`, `DELETE /project/{id}`, `POST /project/list`, `PUT /project/list` |
| `execute_supplier` | Oppretter eller oppdaterer en leverandør (org.nr., e-post, kontonr., adresser, kategorier). | `POST /supplier`, `PUT /supplier/{id}` |
| `execute_wage_type_registration` | Registrerer lønnsart-tillegg (f.eks. overtid) som antall på timelisten for én ansatt. | `GET /salary/type`, `POST /timesheet/salaryTypeSpecification`, `PUT /timesheet/salaryTypeSpecification/{id}`, `POST /timesheet/salaryProjectTypeSpecification`, `PUT /timesheet/salaryProjectTypeSpecification/{id}` |
| `get_activities_for_project` | Lister aktiviteter innlogget ansatt kan føre timer på for et prosjekt på en gitt dato. | `GET /activity/>forTimeSheet` |
| `get_amelding_status` | Viser status for a-meldingen for en måned og påløpt/ubetalt trekk og AGA. Egen kobling: npm run amelding -- status (internt kall GET /salary/tskinternal/amelding/ameldingStatus). | `POST /salary/taxDeduction/reconciliation/context`, `GET /salary/taxDeduction/reconciliation/{reconciliationId}/balanceAndOwedAmount`, `POST /salary/payrollTax/reconciliation/context`, `GET /salary/payrollTax/reconciliation/{reconciliationId}/overview` |
| `get_balance_sheet` | Henter saldobalanse per konto (IB, bevegelse, UB) for en periode med dimensjonsfilter. | `GET /balanceSheet` |
| `get_change_log` | Viser endringslogg (hvem/når opprettet/endret) for kunde, faktura, ordre eller timeføringer via fields=changes. | `GET /customer/{id}`, `GET /invoice/{id}`, `GET /order/{id}`, `GET /timesheet/entry` |
| `get_close_group` | Slår opp en lukkegruppe (utlignede poster) via lukkegruppe-id eller post-id. | `GET /ledger/closeGroup/{id}`, `GET /ledger/posting/{id}` |
| `get_contact` | Henter én kontaktperson med detaljer. | `GET /contact/{id}` |
| `get_current_clock_status` | Viser om innlogget bruker er inn- eller utstemplet. | `GET /timesheet/timeClock/present` |
| `get_customer` | Henter én kunde med adresser, sendemåte, valuta og kategorier. | `GET /customer/{id}` |
| `get_employee` | Henter komplett ansattpost med arbeidsforhold, historikk og a-meldingsstatus. | `GET /employee/{id}`, `GET /employee/employment`, `GET /employee/employment/details` |
| `get_expense` | Henter et utlegg eller en reiseregning med alle linjer, vedlegg og godkjenningsstatus. | `GET /travelExpense/{id}`, `GET /travelExpense/cost`, `GET /travelExpense/mileageAllowance`, `GET /travelExpense/perDiemCompensation`, `GET /travelExpense/accommodationAllowance` |
| `get_expense_receipt` | Gir en kortlivet lenke til kvitteringen på et utlegg eller en reiseregning. | `GET /travelExpense/{travelExpenseId}/attachment` |
| `get_holiday_balance` | Viser feriesaldo (dager igjen, tatt, planlagt) og opptjente feriepenger for én ansatt. | `GET /timesheet/month/byMonthNumber`, `GET /employee/{id}`, `GET /timesheet/entry` |
| `get_invoice` | Henter én utgående faktura (på id eller fakturanummer) med ordrelinjer og bilag. | `GET /invoice/{id}`, `GET /invoice` |
| `get_invoice_pdf_url` | Gir lenke til PDF av en utgående faktura (v2 strømmer PDF-en direkte). | `GET /invoice/{invoiceId}/pdf` |
| `get_month_overview` | Viser månedsoversikt for én ansatt: status, timesum, fleksisaldo, feriesaldo og utbetalingsfelt. | `GET /timesheet/month/byMonthNumber` |
| `get_month_status` | Viser levert/godkjent-status og timesum for en måned for én eller flere ansatte. | `GET /timesheet/month/byMonthNumber`, `GET /timesheet/salaryTypeSpecification` |
| `get_my_payslip` | Henter én av mine lønnsslipper med lønnsarter/linjer. | `GET /salary/payslip/{id}` |
| `get_my_wage_compilation` | Henter min årlige lønnssammenstilling (lønn, trekk, skatt). | `GET /salary/compilation` |
| `get_my_wage_compilation_pdf` | Laster ned min årlige lønnssammenstilling som PDF. | `GET /salary/compilation/pdf` |
| `get_order` | Henter én salgsordre med ordrelinjer og valuta. | `GET /order/{id}` |
| `get_payslip_pdf_url` | Gir lenke til PDF av en lønnsslipp (v2 strømmer PDF-en direkte). | `GET /salary/payslip/{id}/pdf` |
| `get_project` | Henter full konfigurasjon for ett eller flere prosjekter (mva, fastpris, deltakere, fakturakommentar). | `GET /project/{id}`, `GET /project/number/{number}`, `GET /project/participant/{id}` |
| `get_recent_projects_and_activities` | Lister innlogget ansatts nylig brukte prosjekter og aktiviteter pluss generelle aktiviteter. | `GET /timesheet/entry/>recentProjects`, `GET /timesheet/entry/>recentActivities`, `GET /activity/>forTimeSheet` |
| `get_reminder` | Henter én purring med dato, trinn, gebyr, renter og KID. | `GET /reminder/{id}` |
| `get_reminder_pdf_url` | Gir lenke til PDF av en purring (v2 strømmer PDF-en direkte). | `GET /reminder/{reminderId}/pdf` |
| `get_supplier` | Henter én leverandør med adresser, kategorier og bankkontoer. | `GET /supplier/{id}` |
| `get_supplier_invoice` | Henter én leverandørfaktura med linjer, betalinger, attestering og posteringer (ny flyt kun via connector). | `GET /supplierInvoice/{id}`, `GET /ledger/voucher/{id}`, `GET /ledger/posting` |
| `get_supplier_invoices_for_approval` | Lister leverandørfakturaer som venter på attestering/godkjenning. | `GET /supplierInvoice/forApproval` |
| `get_voucher_document` | Gir nedlastingslenke til dokumentet bak en leverandørfaktura eller et bilagsmottak-element. | `GET /ledger/voucher/{voucherId}/pdf`, `GET /supplierInvoice/{invoiceId}/pdf`, `GET /document/{id}/content` |
| `get_voucher_inbox_count` | Returnerer antall ubehandlede dokumenter i bilagsmottaket. | `GET /voucherInbox/inboxCount` |
| `get_week_status` | Viser levert/godkjent-status for en uke for én eller flere ansatte. | `GET /timesheet/week`, `GET /timesheet/salaryTypeSpecification` |
| `invoice_order` | Gjør en ordre om til utgående faktura (evt. forhåndsbetalt eller a-konto). | `PUT /order/{id}/:invoice` |
| `list_active_companies` | Lister selskapene økten er koblet til. | `GET /token/session/>whoAmI`, `GET /company/{id}` |
| `list_company_holidays` | Lister selskapets helligdager/fridager for et år eller en periode. | `GET /timesheet/companyHoliday` |
| `list_suppliers` | Lister leverandører med eksakte filtre (e-post, org.nr., nummer, kategori). | `GET /supplier` |
| `list_timesheet_wage_types` | Lister lønnsarter (overtid/tillegg) innlogget ansatt kan registrere på timelisten. | `GET /salary/type` |
| `logged_in_user_info` | Viser innlogget bruker: navn, ansatt-id, avdeling og selskapskontekst. | `GET /token/session/>whoAmI`, `GET /employee/{id}`, `GET /voucherInbox/emailAddress` |
| `remove_expense_line` | Sletter én kostnadslinje fra et åpent eller avvist utlegg/reiseregning. | `DELETE /travelExpense/cost/{id}` |
| `remove_travel_line` | Sletter én diett-, kjøregodtgjørelse- eller nattilleggslinje fra en åpen reiseregning. | `DELETE /travelExpense/perDiemCompensation/{id}`, `DELETE /travelExpense/mileageAllowance/{id}`, `DELETE /travelExpense/accommodationAllowance/{id}` |
| `reopen_month` | Gjenåpner en levert timelistemåned slik at timene kan redigeres. | `PUT /timesheet/month/:reopen` |
| `reopen_week` | Gjenåpner en levert timelisteuke slik at timene kan redigeres. | `PUT /timesheet/week/:reopen` |
| `search_accounts` | Slår opp konti i kontoplanen (nummer, reskontrotype). | `GET /ledger/account` |
| `search_activities` | Søker i aktivitetskatalogen (navn, nummer, fakturerbar). | `GET /activity` |
| `search_client_companies` | Søker blant klientene byrået har proxy-tilgang til. | `GET /company/>withLoginAccess` |
| `search_contacts` | Søker kontaktpersoner på navn, e-post eller kunde. | `GET /contact` |
| `search_countries` | Søker i landkatalogen (ISO-koder, norsk/engelsk navn). | `GET /country` |
| `search_customer_categories` | Lister kundekategorier (felles for kunder og leverandører) og hvilken slot de hører til. | `GET /customer/category` |
| `search_customers` | Søker kunder på navn, e-post, telefon, org.nr. eller kategori. | `GET /customer` |
| `search_departments` | Lister/søker avdelinger med avdelingsleder. | `GET /department`, `GET /department/query` |
| `search_employee_categories` | Lister ansattkategorier. | `GET /employee/category` |
| `search_employees` | Søker ansatte på navn, avdeling, e-post eller ansattnummer. | `GET /employee` |
| `search_expense_cost_categories` | Lister kostnadskategorier for utlegg og reiseregninger. | `GET /travelExpense/costCategory` |
| `search_expense_payment_types` | Lister betalingstyper for utleggslinjer (privat utlegg, firmakort m.m.). | `GET /travelExpense/paymentType` |
| `search_expenses` | Lister utlegg og reiseregninger, filtrert på ansatt og status. | `GET /travelExpense` |
| `search_hour_entries` | Lister timeføringer i en periode for en ansatt, med helligdagsflagg og lønnsart-registreringer. | `GET /timesheet/entry`, `GET /timesheet/companyHoliday`, `GET /timesheet/salaryTypeSpecification` |
| `search_invoices` | Søker utgående (sendte) fakturaer på dato, kunde eller nummer, med utestående beløp. | `GET /invoice` |
| `search_ledger_postings` | Søker hovedboksposteringer på periode, konto(område) eller leverandør. | `GET /ledger/posting` |
| `search_my_payslips` | Lister mine egne lønnsslipper. | `GET /salary/payslip` |
| `search_occupation_codes` | Søker yrkeskoder (STYRK-08) for arbeidsforhold i a-meldingen. | `GET /employee/employment/occupationCode` |
| `search_open_postings` | Lister åpne (ikke utlignede) poster i kunde-/leverandørreskontro eller andre konti. | `GET /ledger/posting/openPost`, `GET /ledger/openPost` |
| `search_orders` | Søker salgsordrer på dato, kunde, lukket- eller abonnementsstatus. | `GET /order` |
| `search_products` | Søker produkter i produktkatalogen (navn, nummer, EAN). | `GET /product` |
| `search_project_categories` | Lister prosjektkategorier. | `GET /project/category` |
| `search_projects` | Søker prosjekter på navn, nummer, kunde eller prosjektleder. | `GET /project` |
| `search_reminders` | Søker purringer på dato, faktura eller kunde. | `GET /reminder` |
| `search_result_budgets` | Leser resultatbudsjett for et år per selskap, avdeling, prosjekt, produkt eller ansatt. | `GET /resultbudget`, `GET /resultbudget/company`, `GET /resultbudget/department/{id}`, `GET /resultbudget/project/{id}`, `GET /resultbudget/product/{id}`, `GET /resultbudget/employee/{id}` |
| `search_supplier_invoices` | Søker leverandørfakturaer på leverandør, dato, beløp eller status (ny flyt kun via connector, gammelt register via v2). | `GET /supplierInvoice` |
| `search_suppliers` | Fritekstsøk etter leverandører på navn, nummer eller org.nr. | `GET /supplierCustomer/search`, `GET /supplier` |
| `search_travel_zones` | Lister reisesoner (land) for diett- og nattilleggssatser. | `GET /travelExpense/zone` |
| `search_vat_types` | Lister mva-typer/-koder med sats og fradrag. | `GET /ledger/vatType` |
| `search_voucher_types` | Lister bilagstyper. | `GET /ledger/voucherType` |
| `search_wage_type_registrations` | Lister lønnsart-registreringer (overtid/tillegg) i en periode for en ansatt. | `GET /timesheet/salaryTypeSpecification`, `GET /timesheet/salaryProjectTypeSpecification` |
| `send_amelding` | Sender a-meldingen for en måned til Skatteetaten. Egen kobling: npm run amelding -- send (internt kall POST /salary/tskinternal/amelding/send). |  |
| `send_invoice` | Sender en opprettet faktura til kunden via e-post, EHF, eFaktura, AvtaleGiro eller papir. | `PUT /invoice/{id}/:send` |
| `send_invoice_reminder` | Sender purring (myk, purring med gebyr eller inkassovarsel) på en forfalt faktura. | `PUT /invoice/{id}/:createReminder` |
| `submit_expense` | Leverer et utlegg/reiseregning til godkjenning. | `PUT /travelExpense/:deliver` |
| `suggest_per_diem` | Forhåndsviser offisielle diettsatser for en reiseregning. | `GET /travelExpense/{id}`, `GET /travelExpense/rate`, `GET /travelExpense/rateCategory`, `GET /travelExpense/zone` |
| `unapprove_expense` | Trekker tilbake godkjenning av et utlegg/reiseregning (tilbake til levert). | `PUT /travelExpense/:unapprove` |
| `unapprove_month` | Trekker tilbake godkjenning av en timelistemåned (tilbake til levert). | `PUT /timesheet/month/:unapprove` |
| `unapprove_week` | Trekker tilbake godkjenning av en timelisteuke (tilbake til levert). | `PUT /timesheet/week/:unapprove` |
| `update_expense` | Endrer hodet på et åpent/avvist utlegg eller reiseregning (tittel, prosjekt, avdeling, reisedetaljer). | `GET /travelExpense/{id}`, `PUT /travelExpense/{id}` |
| `update_expense_line` | Endrer én kostnadslinje (beløp, kategori, betalingstype, dato) på et åpent utlegg/reiseregning. | `PUT /travelExpense/cost/{id}` |
| `upload_expense_receipt` | Laster opp kvittering (PDF/bilde) til nytt eller eksisterende utlegg/reiseregning; automatisk tolking skjer kun i connectoren. | `POST /travelExpense`, `POST /travelExpense/{travelExpenseId}/attachment` |
| `withdraw_expense` | Trekker tilbake mitt eget leverte utlegg/reiseregning til åpen. | `PUT /travelExpense/:undeliver` |

## Ikke i API v2

- **Hente, bestille eller sjekke status på skattekort** – Ikke i v2. Connector: fetch_taxcards, get_taxcard_status, order_taxcards (order er skrivende – krever bekreftelse). Skattekort er personopplysninger – vis kun status/antall.
- **Slå opp selskap i Brønnøysundregistrene (org.nr., roller, konkurs, næringskode)** – Ikke i v2. Connector: lookup_company_in_brreg (eller Brregs åpne API). Konkurs/avviklet blant kundene: `GET /supportDashboard/bankruptAndExcludedCustomers` (system).
- **Lage og sende tilbud til kunde** – Ingen tilbuds-endepunkter i v2 eller Tripletex-connector. Alternativ: opprett ordre (`POST /order`) og send ordrebekreftelse, eller lag tilbud i UI.
- **Sende inn MVA-meldingen til Skatteetaten** – Ikke i v2 eller Tripletex-connector. v2 dekker status (`GET /vatReturns/status`), grunnlag og avstemming (mva). Innsending gjøres av brukeren i Tripletex/Altinn.
- **Levere årsregnskap, skattemelding/næringsspesifikasjon eller aksjonærregisteroppgave** – Ikke i v2 eller Tripletex-connector. v2 dekker signering i Penneo (/yearEnd/penneo/*), saldobalanse og SAF-T; innsending gjøres i Tripletex årsoppgjørsmodul eller Altinn.
- **Registrere eller endre resultatbudsjett** – v2 er kun lesing (`GET /resultbudget/company` m.fl.). Connector: update_result_budget (skrivende – krever bekreftelse); ellers UI.
- **Hente Tripletex sine ferdige standardrapporter (rapport-PDF/rapportbygger)** – Ikke i v2. Connector: fetch_report, get_report_details, get_balance_sheet. Alternativt bygg selv fra `GET /balanceSheet` (se «Resultatregnskap og balanse …»).
- **Låse eller gjenåpne en regnskapsperiode** – Ikke i v2 (kun `GET /ledger/accountingPeriod`). Gjøres i Tripletex-UI.
- **Endre forfallsdato eller beløp på en utstedt kundefaktura** – Ingen endepunkt for å endre utstedt faktura i v2. Krediter (`PUT /invoice/{id}/:createCreditNote`) og fakturer på nytt, eller endre i UI. Avtalt betalingsutsettelse kan leses via invoiceRemark (salg).
- **Sende betalinger til banken (remittering/autopay) eller utbetale nettolønn** – Delvis. POST /supplierInvoice/{invoiceId}/:addPayment registrerer betaling av leverandørfaktura; med betalingstype for Autopay/Nets (useDefaultPaymentType eller riktig paymentType) kan den gå til banken, men det krever oppsett gjort av Tripletex, og betalingen må normalt godkjennes i Tripletex/nettbank. Ingen v2-endepunkter for å sende utbetaling av nettolønn. Lønn godkjennes aldri av Claude. Skrivende – krever alltid bekreftelse.
- **Opprette ny klientkonto / etablere tilgang til ny klient i regnskapsbyrået** – Å opprette en ny klientkonto finnes ikke i v2 (connector: check_client_account_status, estimate_client_account_price, establish_client_access). Eksisterende klienter: GET /company/>withLoginAccess. Tilgang for ansatte til klienter: GET /employee/entitlement/client og PUT /employee/entitlement/:grantClientEntitlementsByTemplate (skrivende – krever bekreftelse).
- **Sende refusjonskrav for sykepenger/foreldrepenger til NAV** – Ikke i v2 eller connector – NAV-portal/Altinn. Bokføring av innbetalt refusjon: se «Bokføre refusjon av sykepenger/foreldrepenger fra NAV».
- **Sette oppdragsansvarlig/saksbehandler per klient i byrået** – Ikke i v2 eller Tripletex-connector. Gjøres i Tripletex byråoversikt (UI).
