# Tripletex API v2 – alle kall

Spec 2.75.11, 802 kall, bygget 2026-10-12 fra https://tripletex.no/v2/openapi.json.
Søk: `node tripletex-api/finn.js <ord>`. Parametere: `node tripletex-api/finn.js --sti /sti`. * = påkrevd parameter. Flagg: BETA, INTERNAL, DEPRECATED, PERSONDATA (bruk minimal fields=, GDPR).

## Innhold

- [MVA / merverdiavgift](#mva) (14)
- [Bank, avstemming og utbetalinger](#bank) (40)
- [Lønn, lønnsavstemminger, pensjon](#lonn) (53)
- [Ansatte, arbeidsforhold, avdelinger, kontakter](#ansatte) (80)
- [Hovedbok, bilag, posteringer, kontoplan, perioder, budsjett, avstemming](#hovedbok) (89)
- [Kunder, ordre, faktura, purring, abonnement/CRM](#salg) (65)
- [Leverandører, leverandørfaktura, innkjøp, dokumentarkiv](#innkjop) (94)
- [Prosjekt, aktiviteter, oppgaver](#prosjekt) (86)
- [Timeføring og timelister](#timer) (55)
- [Reiseregninger og utlegg](#reise) (67)
- [Produkter, lager, logistikk](#produkt) (85)
- [Anleggsmidler, årsoppgjør, SAF-T, signering (Penneo)](#arsoppgjor) (36)
- [Selskap, innstillinger, autentisering, webhooks, lisenser, oppslag](#system) (38)

<a id="mva"></a>
## MVA / merverdiavgift

### ledger/vatSettings
MVA-innstillinger for selskapet: registreringsstatus (ikke registrert, søker, registrert, kompensasjon) og hvilke typer omsetning/mva-koder som er aktivert.

*Nøkkelord:* mva-innstillinger, mva innstillinger, mva-registrert, mva registrert, momsregistrert, ikke mva-registrert, merverdiavgiftsregisteret, registreringsstatus, avgiftsplikt, mva-plikt, frivillig registrering, mva-kompensasjon, kompensasjonsmelding, aktivere mva-kode, aktivere importkoder, aktivere uttakskoder, snudd avregning, omvendt avgiftsplikt, tjenester fra utlandet, tilbakeføring, vat settings, vat registration, mva, moms, merverdiavgift

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/vatSettings` | Get VAT settings for the logged in company. |  |  |
| `PUT /ledger/vatSettings` | Update VAT settings for the logged in company. |  |  |

### ledger/vatType
MVA-koder (mva-typer) med sats og fradragsprosent, inkludert relative koder for forholdsmessig fradrag av inngående mva.

*Nøkkelord:* mva-kode, mvakode, mva-koder, momskode, avgiftskode, mva-type, mva-sats, momssats, høy sats, hoy sats, middels sats, lav sats, 25 %, 15 %, 12 %, fritatt, nullsats, utenfor mva-loven, forholdsmessig fradrag, fradragsprosent, inngående mva, inngaende mva, utgående mva, utgaende mva, vat code

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /ledger/vatType/createRelativeVatType` | Create a new relative VAT Type. These are used if the company has 'forholdsmessig fradrag for inngående MVA'. | name*, vatTypeId*, percentage* |  |
| `GET /ledger/vatType/{id}` | Get vat type by ID. | id* |  |
| `GET /ledger/vatType` | Find vat types corresponding with sent data. | id, number, typeOfVat, vatDate, shouldIncludeSpecificationTypes |  |

### vatReturns
Status for MVA-meldingen per termin: levert/ikke levert til Skatteetaten, betalt/restbeløp, mva-grunnlag og bilagsnummer for mva-oppgjøret.

*Nøkkelord:* mva-melding, mva melding, mvamelding, momsmelding, skattemelding for merverdiavgift, omsetningsoppgave, terminoppgave, mva-termin, termin, levert, innsendt, kvittering, altinn, skatteetaten, betalingsstatus, skyldig mva, mva til gode, restbeløp, restbelop, frist, mva-oppgjør, mva-oppgjor, momsoppgjør, vat return, vat status

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /vatReturns/status` | Get VAT status for current company with sent data | year, term, reportType |  |
| `GET /vatReturns/status/list` | Get a list of VAT status' for current company with sent data | startDate, endDate, reportType |  |

### vatReturns/comment
Strukturerte merknader (standardkommentarer) som kan knyttes til linjer i MVA-meldingen, gruppert per mva-kode (BETA, kun lesing).

*Nøkkelord:* merknad, merknader, kommentar, strukturert merknad, mva-melding merknad, forklaring til skatteetaten, tap på krav, tap pa krav, fortegn, vat comment, structured comment, merknad til mva-melding, merknad tap på krav, merknad uttak, merknad justering, standardmerknad, forklaring avvik

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /vatReturns/comment/>all` | - Get all structured comments available |  | BETA |
| `GET /vatReturns/comment` | - Get all structured comments related to a given vatCode |  | BETA |

### vatTermSizeSettings
Terminlengde for MVA-rapportering (tomånedlig, månedlig, årstermin osv.) per rapporttype (alminnelig næring/primærnæring) med gyldig-fra-dato.

*Nøkkelord:* terminlengde, termin, terminvis, tomånedlig, tomanedlig, månedlig, manedlig, årstermin, arstermin, primærnæring, primarnaering, alminnelig næring, alminnelig naering, rapporteringstermin, mva-periode, vat term, term size, termsize, terminordning, årsmelding mva, arsmelding mva, månedsmelding, manedsmelding, primærnæring termin

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /vatTermSizeSettings/{id}` | Get VatTermSizeSettings by ID. VatTermSizeSettings is used to define VAT term lengths. | id* |  |
| `PUT /vatTermSizeSettings/{id}` | Update VatTermSizeSettings. | id* |  |
| `DELETE /vatTermSizeSettings/{id}` | Delete VatTermSizeSettings | id* |  |
| `GET /vatTermSizeSettings` | Search for VatTermSizeSettings |  |  |
| `POST /vatTermSizeSettings` | Create VatTermSizeSettings |  |  |

<a id="bank"></a>
## Bank, avstemming og utbetalinger

### bank
Oppslag i bankregisteret (banknavn, registernummer, støttede kontoutskriftsformater, autopay/ZTL-støtte) – brukes for å finne bankId før import av kontoutskrift.

*Nøkkelord:* bank, banker, bankregister, registernummer, banknavn, bankid, bank id, dnb, nordea, sparebank1, danske bank, handelsbanken, sbanken, eika, autopay, ztl, bankintegrasjon, filformat, kontoutskriftsformat, bankforbindelse, hvilken bank, bank lookup, sparebanken, støttede formater, stottede formater

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /bank/{id}` | Get bank. | id* |  |
| `GET /bank` | Find bank corresponding with sent data. | id, registerNumbers, isBankReconciliationSupport, isAutoPaySupported, isZtlSupported, query |  |

### bank/reconciliation
Bankavstemminger per hovedbokskonto og regnskapsperiode: opprette, hente, oppdatere saldo, lukke/gjenåpne, slette og eksportere uavstemte transaksjoner.

*Nøkkelord:* bankavstemming, bankavstemning, avstemming, avstemning, automatisk bankavstemming, manuell bankavstemming, bank reconciliation, manedsavstemming, avstemme bank, lukke avstemming, avstemt til og med, gjenapne, utgående saldo, saldo iflg bank, uavstemte poster, åpne poster bank, apne poster, uavstemt, differanse bank, 1920, bankkonto, månedsavstemming, avstemme, bank rec, bankrec

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /bank/reconciliation/closedWithUnmatchedTransactions` | Get the last closed reconciliation with unmached transactions by account ID. | accountId*, start |  |
| `PUT /bank/reconciliation/transactions/unmatched:csv` | Get all unmatched transactions in csv format | reconciliationId |  |
| `GET /bank/reconciliation/{id}` | Get bank reconciliation. | id* |  |
| `PUT /bank/reconciliation/{id}` | Update a bank reconciliation. | id* |  |
| `DELETE /bank/reconciliation/{id}` | Delete bank reconciliation by ID. | id* |  |
| `GET /bank/reconciliation/>last` | Get the last created reconciliation by account ID. | accountId* |  |
| `GET /bank/reconciliation/>lastClosed` | Get last closed reconciliation by account ID. | accountId*, after |  |
| `GET /bank/reconciliation` | Find bank reconciliation corresponding with sent data. | id, accountingPeriodId, accountId |  |
| `POST /bank/reconciliation` | Post a bank reconciliation. |  |  |

### bank/reconciliation/match
Matcher mellom banktransaksjoner og hovedbokposteringer i en bankavstemming: forslag (auto-match), manuell matching, godkjenning, oppheving og telling.

*Nøkkelord:* match, matching, matche, koble, koble transaksjon, avstemme transaksjon, automatch, auto-match, automatisk matching, forslag, matchforslag, suggest, godkjenne forslag, avvise forslag, manuell match, oppheve match, fjerne kobling, justering, adjustment, direkteføring, direct posting, reconciliation match, avstemt, matchet

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /bank/reconciliation/match/count` | Get the total number of matches | bankReconciliationId* |  |
| `GET /bank/reconciliation/match/{id}` | Get bank reconciliation match by ID. | id* |  |
| `PUT /bank/reconciliation/match/{id}` | Update a bank reconciliation match by ID. | id* |  |
| `DELETE /bank/reconciliation/match/{id}` | Delete a bank reconciliation match by ID. | id* |  |
| `GET /bank/reconciliation/match` | Find bank reconciliation match corresponding with sent data. | id, bankReconciliationId, approved |  |
| `POST /bank/reconciliation/match` | Create a bank reconciliation match. |  |  |
| `GET /bank/reconciliation/match/query` | Wildcard search. | bankReconciliationId, approved | INTERNAL |
| `PUT /bank/reconciliation/match/:suggest` | Suggest matches for a bank reconciliation by ID. | bankReconciliationId* |  |

### bank/reconciliation/matches/counter
[BETA] Teller for antall auto-matchede og foreslåtte matcher siden avstemmingssiden sist ble åpnet (UI-varsel), med mulighet for nullstilling.

*Nøkkelord:* teller, counter, antall matcher, nye matcher, nye forslag, automatchet, auto matched, nullstille teller, reset counter, varsel bankavstemming, beta

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /bank/reconciliation/matches/counter` | Get number of matches since last page access. | bankReconciliationId* | BETA |
| `POST /bank/reconciliation/matches/counter` | Reset the number of matches after the page has been accessed. | bankReconciliationId* | BETA |

### bank/reconciliation/paymentType
Betalingstyper/posteringstyper som brukes i bankavstemmingen (med debet- og kreditkonto), f.eks. til å føre gebyr, renter og differanser direkte fra avstemmingen.

*Nøkkelord:* betalingstype, betalingstyper avstemming, payment type, posteringstype, bankgebyr, gebyr, renteinntekt, rentekostnad, renter bank, avrunding, debetkonto, kreditkonto, direkteføring, justeringspostering, motkonto, bank fee, interest, posteringstyper avstemming

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /bank/reconciliation/paymentType/{id}` | Get payment type by ID. | id* |  |
| `GET /bank/reconciliation/paymentType` | Find payment type corresponding with sent data. | id, description |  |

### bank/reconciliation/settings
Selskapets innstillinger for bankavstemming, i praksis antall matcher per side i avstemmingsbildet.

*Nøkkelord:* innstillinger bankavstemming, avstemmingsinnstillinger, settings, reconciliation settings, antall per side, numberofmatchesperpage, sidestørrelse, oppsett bankavstemming, konfigurasjon bank

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /bank/reconciliation/settings` | Get bank reconciliation settings. |  |  |
| `POST /bank/reconciliation/settings` | Post bank reconciliation settings. |  |  |
| `PUT /bank/reconciliation/settings/{id}` | Update bank reconciliation settings. | id* |  |

### bank/statement
Kontoutskrifter (bankfiler) importert til en bankkonto: importere fil, liste, hente inngående/utgående saldo og slette feilimport.

*Nøkkelord:* kontoutskrift, kontoutskrifter, bankutskrift, bank statement, statement, bankfil, importere bankfil, import kontoutskrift, laste opp kontoutskrift, telepay, psd2, inngående saldo, utgående saldo, slette kontoutskrift, feilimport, dobbeltimport, kontoutdrag, bankutdrag, bankimport, transferwise, wise, ztl, folio, inngaende saldo, utgaende saldo

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /bank/statement/{id}` | Get bank statement. | id* |  |
| `DELETE /bank/statement/{id}` | Delete bank statement by ID. | id* |  |
| `POST /bank/statement/import` | Upload bank statement file. | bankId*, accountId*, fromDate*, toDate*, externalId, fileFormat* |  |
| `GET /bank/statement` | Find bank statement corresponding with sent data. | id, accountId, fileFormats |  |

### bank/statement/transaction
Enkelttransaksjoner på en importert kontoutskrift (dato, beløp, tekst, matchstatus) med mulighet for ekstra detaljer per transaksjon.

*Nøkkelord:* banktransaksjon, banktransaksjoner, bankposter, bankpost, transaksjon, transaction, bevegelser, kontobevegelser, innbetaling, utbetaling, transaksjonsdetaljer, betalingsreferanse, kid, umatchet, uavstemt transaksjon, mangler bilag, mangler dokumentasjon, bankbevegelse, banklinje, ukjent innbetaling, ukjent beløp

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /bank/statement/transaction/{id}` | Get bank transaction by ID. | id* |  |
| `GET /bank/statement/transaction/{id}/details` | Get additional details about transaction by ID. | id* |  |
| `GET /bank/statement/transaction` | Find bank transaction corresponding with sent data. | bankStatementId* |  |

### ledger/paymentTypeOut
[BETA] Betalingstyper for utgående betalinger (kontoinnstillinger 'Utgående betalinger') som brukes ved betaling av leverandørfaktura, MVA-melding, lønnsutbetaling og skattetrekk/forskuddsskatt.

*Nøkkelord:* utbetaling, utbetalinger, utgående betaling, utgående betalinger, betalingstype, betalingstyper, payment type out, paymenttypeout, betale leverandørfaktura, leverandørbetaling, leverandorbetaling, lønnsutbetaling, lonnsutbetaling, mva betaling, nettbank, remittering, betalingsmåte, kredittkort, firmakort, utbetalingstype, betalingsmetode, forskuddsskatt, skattetrekk

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/paymentTypeOut/{id}` | Get payment type for outgoing payments by ID. | id* | BETA |
| `PUT /ledger/paymentTypeOut/{id}` | Update existing payment type for outgoing payments | id* | BETA |
| `DELETE /ledger/paymentTypeOut/{id}` | Delete payment type for outgoing payments by ID. | id* | BETA |
| `GET /ledger/paymentTypeOut` | Gets payment types for outgoing payments | id, description, isInactive | BETA |
| `POST /ledger/paymentTypeOut` | Create new payment type for outgoing payments |  | BETA |
| `PUT /ledger/paymentTypeOut/list` | Update multiple payment types for outgoing payments at once |  | BETA |
| `POST /ledger/paymentTypeOut/list` | Create multiple payment types for outgoing payments at once |  | BETA |

<a id="lonn"></a>
## Lønn, lønnsavstemminger, pensjon

### financeTax/reconciliation
Avstemming av finansskatt på lønn (kun finansforetak) per termin: hovedbok mot a-melding og Skatteetaten, pluss innbetalinger hittil i år.

*Nøkkelord:* finansskatt, finansskatt på lønn, finansskatt pa lonn, avstemming finansskatt, finansforetak, a-melding, amelding, termin, hovedbok mot a-melding, avvik, innbetaling, betalingsoversikt, finance tax, reconciliation, skatteetaten, bankvirksomhet, forsikringsselskap, finansnæring, finansnaering, finansskatt termin

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/financeTax/reconciliation/{reconciliationId}/overview` | Get finance tax overview for a specific reconciliation term | reconciliationId* | PERSONDATA |
| `GET /salary/financeTax/reconciliation/{reconciliationId}/paymentsOverview` | Get finance tax payment overview from start of year to the current reconciliation term | reconciliationId* | PERSONDATA |
| `POST /salary/financeTax/reconciliation/context` | Create a financeTax reconciliation context for a customer |  | PERSONDATA |

### salary/holidayAllowance/reconciliation
Avstemming av feriepenger: skyldige feriepenger og arbeidsgiveravgift av feriepenger i hovedbok mot feriepengelisten, med opptjent/utbetalt/skyldig per sats.

*Nøkkelord:* feriepenger, feriepengeavstemming, avstemme feriepenger, skyldige feriepenger, skyldig feriepenger, 2940, aga av feriepenger, arbeidsgiveravgift av feriepenger, 2785, feriepengeliste, feriepengegrunnlag, opptjent feriepenger, utbetalt feriepenger, feriepengesats, holiday allowance, vacation pay, reconciliation, lonnsavstemming, lønnsavstemming, feriepenger avstemming, feriepengeavsetning, avsetning feriepenger, feriepengegjeld, avstemme feriepengegjeld

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/holidayAllowance/reconciliation/{reconciliationId}/holidayAllowanceDetails` | Get a holiday allowance details for the current reconciliation term | reconciliationId* | PERSONDATA |
| `GET /salary/holidayAllowance/reconciliation/{reconciliationId}/holidayAllowanceSummary` | Salary holiday allowance reconciliation summary | reconciliationId* | PERSONDATA |
| `POST /salary/holidayAllowance/reconciliation/context` | Create a holiday allowance reconciliation context for a customer |  | PERSONDATA |

### salary/mandatoryDeduction/reconciliation
Avstemming av påleggstrekk (utleggstrekk, bidragstrekk o.l.) per termin: hovedbok mot a-melding per periode, pluss innbetalinger hittil i år.

*Nøkkelord:* påleggstrekk, paleggstrekk, trekkpålegg, trekkpalegg, utleggstrekk, bidragstrekk, trekk i lønn, trekk i lonn, nav innkreving, namsmann, skyldig trekk, mandatory deduction, a-melding, avstemming, termin, avvik, lonnsavstemming, utlegg, barnebidrag, skyldig påleggstrekk, skyldig paleggstrekk, lønnstrekk, lonnstrekk

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/mandatoryDeduction/reconciliation/{reconciliationId}/overview` | Salary mandatory deduction reconciliation overview | reconciliationId* | PERSONDATA |
| `GET /salary/mandatoryDeduction/reconciliation/{reconciliationId}/paymentsOverview` | Get mandatory deduction payments overview from start of year to the current reconciliation term | reconciliationId* | PERSONDATA |
| `POST /salary/mandatoryDeduction/reconciliation/context` | Create a mandatoryDeduction reconciliation context for a customer |  | PERSONDATA |

### salary/payrollTax/reconciliation
Avstemming av arbeidsgiveravgift per termin: hovedbok mot a-melding og Skatteetaten, fordelt på avgiftssoner, pluss innbetalinger hittil i år.

*Nøkkelord:* arbeidsgiveravgift, aga, avstemme aga, skyldig arbeidsgiveravgift, 2770, 2780, 5400, avgiftssone, grunnlag aga, termin, a-melding, payroll tax, employer contribution, innbetaling aga, lonnsavstemming, arbeidsgiver avgift, aga termin, arbeidsgiveravgift termin, aga-sone, sone 1a, fribeløp, fribelop, aga av pensjon, lønnsavstemming, a07-avstemming

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/payrollTax/reconciliation/{reconciliationId}/overview` | Salary payroll tax reconciliation overview | reconciliationId* | PERSONDATA |
| `GET /salary/payrollTax/reconciliation/{reconciliationId}/paymentsOverview` | Get a payroll tax payments from start of year to the current reconciliation term | reconciliationId* | PERSONDATA |
| `POST /salary/payrollTax/reconciliation/context` | Create a payroll tax reconciliation context for a customer |  | PERSONDATA |

### salary/taxDeduction/reconciliation
Avstemming av forskuddstrekk per termin: hovedbok (2600) mot a-melding og Skatteetaten per måned, pluss registrerte innbetalinger hittil i år.

*Nøkkelord:* forskuddstrekk, skattetrekk, avstemme skattetrekk, avstemme forskuddstrekk, forskuddstrekk termin, 2600, skyldig skattetrekk, a-melding, amelding, a07, termin, tax deduction, withholding tax, reconciliation, innbetaling skattetrekk, avvik, lonnsavstemming, lønnsavstemming, skattetrekk termin, trekk termin, skyldig forskuddstrekk, a07-avstemming, a-melding mot hovedbok

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/taxDeduction/reconciliation/{reconciliationId}/overview` | Get salary tax deduction data for the reconciliation table | reconciliationId* | PERSONDATA |
| `GET /salary/taxDeduction/reconciliation/{reconciliationId}/paymentsOverview` | Get salary tax deduction payment overview from start of year to the current reconciliation term | reconciliationId* | PERSONDATA |
| `POST /salary/taxDeduction/reconciliation/context` | Create a taxDeduction reconciliation context for a customer |  | PERSONDATA |

### salary/reconciliation/tax-deduction
Saldo og skyldig beløp for forskuddstrekk i en avstemming – brukes til å sjekke at skattetrekkskontoen dekker skyldig trekk.

*Nøkkelord:* skattetrekkskonto, skattetrekk konto, saldo skattetrekk, skyldig forskuddstrekk, dekning skattetrekk, underdekning skattetrekk, bankgaranti skattetrekk, 1950, 2600, tax deduction balance, owed amount, forskuddstrekk, skattetrekk, skattetrekksmidler, skattetrekkskonto dekning, balanceandowedamount

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/taxDeduction/reconciliation/{reconciliationId}/balanceAndOwedAmount` | Get tax deduction details for a reconciliation | reconciliationId* | PERSONDATA |

### company/settings/altinn
Firmaets Altinn-oppsett (Altinn-ID og passord) som Tripletex bruker ved innsending av a-melding og henting av skattekort.

*Nøkkelord:* altinn, altinn-id, altinn id, altinn innlogging, altinn passord, a-melding innsending, sende a-melding, skattekort, altinn settings, innsending, altinnoppsett, altinn-oppsett, systembruker, altinn-bruker

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /company/settings/altinn` | Find Altinn id for login in company. |  |  |
| `PUT /company/settings/altinn` | Update AltInn id and password. |  |  |

### salary/type
Lønnsarter med nummer, navn, a-meldingskode, skatte-/AGA-/feriepengeplikt og debet-/kreditkonto (kun lesing i API-et).

*Nøkkelord:* lønnsart, lonnsart, lønnsarter, lonnsarter, wage type, salary type, fastlønn, fastlonn, timelønn, timelonn, overtid, a-melding kode, inntektsbeskrivelse, skattepliktig, aga-pliktig, feriepengepliktig, lønnskonto, 5000, lønnsartnummer, lonnsartnummer, ytelse, a-melding ytelse, lønnsart konto, bilgodtgjørelse, naturalytelse

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/type/{id}` | Find salary type by ID. | id* | PERSONDATA |
| `GET /salary/type` | Find salary type corresponding with sent data. | id, number, name, description, showInTimesheet, isInactive, employeeIds | PERSONDATA |

### salary/compilation
Sammenstillingsoppgave (tidligere lønns- og trekkoppgave) per ansatt og år: lønn, utgiftsgodtgjørelser, forskuddstrekk og påleggstrekk, også som PDF.

*Nøkkelord:* sammenstillingsoppgave, lønns- og trekkoppgave, lonns og trekkoppgave, lønnsoppgave, lonnsoppgave, årsoppgave lønn, arsoppgave lonn, lønnsoppstilling, salary compilation, årslønn, feriepengegrunnlag, forskuddstrekk hittil i år, trekkoppgave, pdf, lto, sammenstilling, arsoppgave, årsoppgave, lønnsoppgave ansatt

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/compilation/pdf` | Find salary compilation (PDF document) by employee. | employeeId*, year | PERSONDATA |
| `GET /salary/compilation` | Find salary compilation by employee. | employeeId*, year | PERSONDATA |

### salary/payslip
Lønnsslipper per ansatt og periode med lønnslinjer (spesifikasjoner), brutto, netto og feriepenger, også som PDF.

*Nøkkelord:* lønnsslipp, lonnsslipp, lønnsslipper, lønnsspesifikasjon, lonnsspesifikasjon, payslip, pay slip, brutto, netto, utbetalt lønn, lønnslinjer, lønnsspesifikasjoner, lønnshistorikk, lønn per måned, pdf lønnsslipp, lonn, lønnsseddel, lonnsseddel, lønnsspes, lonnsspes, lønnskostnad per måned, feriepenger utbetalt, lønnsstatistikk

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/payslip/{id}/pdf` | Find payslip (PDF document) by ID. | id* | PERSONDATA |
| `GET /salary/payslip/{id}` | Find payslip by ID. | id* | PERSONDATA |
| `GET /salary/payslip` | Find payslips corresponding with sent data. | id, employeeId, wageTransactionId, activityId, yearFrom, yearTo, monthFrom, monthTo, voucherDateFrom, voucherDateTo, comment | PERSONDATA |

### salary/settings
Firmaets lønnsinnstillinger: kommune/sone for arbeidsgiveravgift og beregningsregel (AA, BB, CC, DD, EE, GG osv.).

*Nøkkelord:* lønnsinnstillinger, lonnsinnstillinger, innstillinger lønn, beregningsregel aga, beregningsmetode arbeidsgiveravgift, kommune aga, sone, avgiftssone, generelle næringer, salary settings, payroll tax method, arbeidsgiveravgift, aga, beregningskode aga, aga-sone, aga sone, aga-kommune, næringskode aga, lonnsoppsett, lønnsoppsett

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/settings` | Get salary settings of logged in company. |  | PERSONDATA |
| `PUT /salary/settings` | Update settings of logged in company. |  | PERSONDATA |

### salary/settings/holiday
Feriepengeinnstillinger per år: antall feriedager, feriepengesats (10,2/12 %), sats for 60+ og 6G-begrensning.

*Nøkkelord:* feriepengesats, feriepengeprosent, feriepenger innstilling, feriedager, ferie, 5 uker ferie, 10,2, 12 prosent, over 60, 60 år, 6g, tilleggsferie, ferieinnstillinger, holiday settings, vacation pay percentage, feriepengesats 12, feriepenger 10,2, feriepenger over 60, feriepengeinnstillinger

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /salary/settings/holiday/list` | Update multiple holiday settings of current logged in company. |  | PERSONDATA |
| `POST /salary/settings/holiday/list` | Create multiple holiday settings of current logged in company. |  | PERSONDATA |
| `DELETE /salary/settings/holiday/list` | Delete multiple holiday settings of current logged in company. | ids* | PERSONDATA |
| `GET /salary/settings/holiday` | Find holiday settings of current logged in company. |  | PERSONDATA |
| `POST /salary/settings/holiday` | Create a holiday setting of current logged in company. |  | PERSONDATA |
| `PUT /salary/settings/holiday/{id}` | Update a holiday setting of current logged in company. | id* | PERSONDATA |

### pension
Global oppslagsliste over pensjonsinnretninger/-leverandører som brukes når firmaets pensjonsordning registreres.

*Nøkkelord:* pensjon, pensjonsinnretning, pensjonsleverandør, pensjonsleverandor, pensjonsselskap, otp-leverandør, livselskap, pension provider, global pension, pensjonsordning oppslag, pensjonsselskap oppslag, pensjonsleverandør liste, otp-leverandor

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /pension` | Find countries corresponding with sent data. | query, startDate |  |

### salary/settings/pensionScheme
Firmaets pensjonsordninger (OTP) med avtalenummer og gyldighetsperiode, som rapporteres i a-meldingen.

*Nøkkelord:* pensjonsordning, pensjonsordninger, otp, obligatorisk tjenestepensjon, tjenestepensjon, innskuddspensjon, pensjonsavtale, avtalenummer, pensjon a-melding, pension scheme, pensjonsinnretning, pensjon, otp-avtale, pensjonsordning a-melding, tjenestepensjonsordning, pensjonsordningsnummer

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/settings/pensionScheme/{id}` | Get Pension Scheme for a specific ID | id* | PERSONDATA |
| `PUT /salary/settings/pensionScheme/{id}` | Update a Pension Scheme | id* | PERSONDATA |
| `DELETE /salary/settings/pensionScheme/{id}` | Delete a Pension Scheme | id* | PERSONDATA |
| `PUT /salary/settings/pensionScheme/list` | Update multiple Pension Schemes. |  | PERSONDATA |
| `POST /salary/settings/pensionScheme/list` | Create multiple Pension Schemes. |  | PERSONDATA |
| `DELETE /salary/settings/pensionScheme/list` | Delete multiple Pension Schemes. | ids* | PERSONDATA |
| `GET /salary/settings/pensionScheme` | Find pension schemes. | number | PERSONDATA |
| `POST /salary/settings/pensionScheme` | Create a Pension Scheme. |  | PERSONDATA |

### salary/settings/standardTime
Firmaets normalarbeidstid (timer per dag fra en gitt dato), brukt i timeliste, fleksitid og stillingsberegning.

*Nøkkelord:* normalarbeidstid, normaltid, arbeidstid, standard arbeidstid, timer per dag, 7,5 timer, 37,5 timer, standard time, fleksitid, full stilling, arbeidstid firma, normalarbeidstid firma, arbeidstimer per dag, normaltimer

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/settings/standardTime/{id}` | Find standard time by ID. | id* | PERSONDATA |
| `PUT /salary/settings/standardTime/{id}` | Update standard time. | id* | PERSONDATA |
| `GET /salary/settings/standardTime/byDate` | Find standard time by date | date | PERSONDATA |
| `GET /salary/settings/standardTime` | Get all standard times. |  | PERSONDATA |
| `POST /salary/settings/standardTime` | Create standard time. |  | PERSONDATA |

### salary/transaction
Lønnskjøringer (lønnsutkast/lønnsbilag) med lønnsslipper og lønnslinjer, inkl. historisk lønn og vedlegg.

*Nøkkelord:* lønnskjøring, lonnskjoring, kjøre lønn, kjore lonn, lønnsutkast, lonnsutkast, lønnsbilag, lonnsbilag, lønnsutbetaling, salary transaction, payroll run, payroll, lønn, lonn, historisk lønn, lønnsvedlegg, generer skattetrekk, faste lønnslinjer, lønnsperiode, lønnsavregning, lonnsavregning, lønnsbehandling, lønnsutkast med faste linjer, slette lønnsutkast

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /salary/transaction/{id}` | Find salary transaction by ID. | id* | PERSONDATA |
| `DELETE /salary/transaction/{id}` | Delete salary transaction by ID. | id* | PERSONDATA |
| `PUT /salary/transaction/{id}/deleteAttachment` | Delete attachment. | id*, sendToVoucherInbox, split | PERSONDATA |
| `POST /salary/transaction` | Create a new salary transaction. | generateTaxDeduction | PERSONDATA |
| `POST /salary/transaction/{id}/attachment` | Upload an attachment to a salary transaction | id* | PERSONDATA |
| `POST /salary/transaction/{id}/attachment/list` | Upload multiple attachments to a salary transaction | id* | PERSONDATA |

<a id="ansatte"></a>
## Ansatte, arbeidsforhold, avdelinger, kontakter

### contact
Kontaktpersoner (eksterne personer, ikke ansatte) knyttet til kunder, med navn, e-post, telefon og avdeling – brukes bl.a. som «deres referanse» på ordre og faktura.

*Nøkkelord:* kontakt, kontaktperson, kontaktpersoner, kundekontakt, contact, contacts, deres referanse, fakturamottaker, kontaktliste, ekstern kontakt, kontaktperson kunde, deres ref, fakturakontakt, customer contact, kontakt hos kunde, kontaktpers

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /contact/{id}` | Get contact by ID. | id* | PERSONDATA |
| `PUT /contact/{id}` | Update contact. | id* | PERSONDATA |
| `POST /contact/list` | Create multiple contacts. |  | PERSONDATA |
| `DELETE /contact/list` | Delete multiple contacts. | ids* | BETA PERSONDATA |
| `GET /contact` | Find contacts corresponding with sent data. | id, firstName, lastName, email, customerId, departmentId | PERSONDATA |
| `POST /contact` | Create contact. |  | PERSONDATA |

### department
Avdelinger brukt som dimensjon i regnskapet (avdelingsregnskap), på ansatte, prosjekter og produkter.

*Nøkkelord:* avdeling, avdelinger, department, departments, avdelingsnummer, avdelingsleder, avdelingsregnskap, kostnadssted, kostnadsbærer, resultatenhet, avdelingsdimensjon, profit center, cost center, inaktiv avdeling, avdelingsresultat, avd, avdelingsnr, avdelingsmodul, avdelingsoppsett

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /department/{id}` | Get department by ID. | id* |  |
| `PUT /department/{id}` | Update department. | id* |  |
| `DELETE /department/{id}` | Delete department by ID | id* |  |
| `GET /department` | Find department corresponding with sent data. | id, name, departmentNumber, departmentManagerId, isInactive |  |
| `POST /department` | Add new department. |  |  |
| `PUT /department/list` | Update multiple departments. |  |  |
| `POST /department/list` | Register new departments. |  |  |
| `GET /department/query` | Wildcard search. | id, query, isInactive |  |

### division
Virksomheter/underenheter (bedriftsnummer) som arbeidsforhold knyttes til for a-meldingen og arbeidsgiveravgiftssone.

*Nøkkelord:* virksomhet, virksomheter, underenhet, underenheter, division, divisions, bedriftsnummer, org.nr, orgnr, opplysningspliktig, aga-sone, brreg, virksomhetsnummer, orgnr underenhet, underenhet a-melding, virksomhet a-melding, arbeidsgiveravgiftssone, aga sone, filial, lokasjon, aga-kommune virksomhet

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /division` | Get divisions. | query |  |
| `POST /division` | Create division. |  |  |
| `PUT /division/list` | Update multiple divisions. |  |  |
| `POST /division/list` | Create divisions. |  |  |
| `PUT /division/{id}` | Update division information. | id* |  |

### employee
Ansatte og brukere i selskapet: opprette, søke, oppdatere personalia, avdeling, kategori og brukertype/innlogging.

*Nøkkelord:* ansatt, ansatte, employee, employees, medarbeider, arbeidstaker, personal, personalregister, ansattnummer, ansattliste, bruker, brukere, brukertype, innlogging, tilgang, prosjektleder, nyansatt, onboarding, personopplysninger, ansattreskontro, fodselsnummer, d-nummer, kontonummer ansatt, sluttet, inaktiv ansatt, vår referanse, var referanse, ansattoversikt, personalliste, brukeradministrasjon, ny bruker, deaktivere ansatt

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/{id}` | Get employee by ID. | id* | PERSONDATA |
| `PUT /employee/{id}` | Update employee. | id* | PERSONDATA |
| `POST /employee/list` | Create several employees. |  | PERSONDATA |
| `GET /employee` | Find employees corresponding with sent data. | id, firstName, lastName, employeeNumber, email, allowInformationRegistration, includeContacts, departmentId, onlyProjectManagers, onlyContacts, assignableProjectManagers, periodStart, periodEnd, hasSystemAccess, onlyEmployeeTokens, isInactive | PERSONDATA |
| `POST /employee` | Create one employee. |  | PERSONDATA |
| `GET /employee/searchForEmployeesAndContacts` | Get employees and contacts by parameters. Include contacts by default. | id, firstName, lastName, email, includeContacts, isInactive, hasSystemAccess, excludeReadOnly | PERSONDATA |

### employee/category
Ansattkategorier for å gruppere ansatte (f.eks. funksjonærer, timelønnede, lærlinger) i rapporter og filtre.

*Nøkkelord:* ansattkategori, ansattkategorier, kategori, employee category, ansattgruppe, gruppering, lønnsgruppe, funksjonær, timelønnet, lærling, laerling, personalkategori, category, ansattkategori lønn, kategori ansatt

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/category/{id}` | Get employee category by ID. | id* | PERSONDATA |
| `PUT /employee/category/{id}` | Update employee category information. | id* | PERSONDATA |
| `DELETE /employee/category/{id}` | Delete employee category by ID | id* | PERSONDATA |
| `PUT /employee/category/list` | Update multiple employee categories. |  | PERSONDATA |
| `POST /employee/category/list` | Create new employee categories. |  | PERSONDATA |
| `DELETE /employee/category/list` | Delete multiple employee categories | ids* | PERSONDATA |
| `GET /employee/category` | Find employee category corresponding with sent data. | id, name, number, query | PERSONDATA |
| `POST /employee/category` | Create a new employee category. |  | PERSONDATA |

### employee/employment
Arbeidsforhold for en ansatt med start-/sluttdato, sluttårsak, virksomhet og skattetrekkskode, som rapporteres i a-meldingen.

*Nøkkelord:* arbeidsforhold, ansettelse, employment, ansettelsesforhold, startdato, sluttdato, oppsigelse, sluttårsak, sluttarsak, a-melding, amelding, arbeidsforholds-id, hovedarbeidsgiver, biarbeidsgiver, trekkode, virksomhet, aa-registeret, aa-register, avslutte arbeidsforhold, skattetrekkskode, ansettelsesdato, tiltredelse, fratredelse, sluttet, gjenansettelse, arbeidsforhold-id, ingen arbeidsforhold pensjon

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/employment/{id}` | Find employment by ID. | id* | PERSONDATA |
| `PUT /employee/employment/{id}` | Update employemnt. | id* | PERSONDATA |
| `GET /employee/employment` | Find all employments for employee. | employeeId | PERSONDATA |
| `POST /employee/employment` | Create employment. |  | PERSONDATA |

### employee/employment/details
Datostyrte detaljer på arbeidsforholdet: stillingsprosent, årslønn/timelønn, yrkeskode, arbeidstidsordning, ansettelsesform og AGA-kommune.

*Nøkkelord:* arbeidsforholdsdetaljer, stillingsprosent, stillingsbrøk, årslønn, arslonn, månedslønn, manedslonn, timelønn, timelonn, lønnsendring, lonnsendring, lønnsjustering, yrkeskode, styrk, arbeidstidsordning, ansettelsesform, fast ansatt, midlertidig, avlønningstype, employment details, aga-kommune, skift, a-melding, stillingsandel, fastlønn, fastlonn, yrke, lønnsopplysninger arbeidsforhold, arbeidsgiveravgiftskommune

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/employment/details/{id}` | Find employment details by ID. | id* | PERSONDATA |
| `PUT /employee/employment/details/{id}` | Update employment details. | id* | PERSONDATA |
| `GET /employee/employment/details` | Find all employmentdetails for employment. | employmentId | PERSONDATA |
| `POST /employee/employment/details` | Create employment details. |  | PERSONDATA |

### employee/employment/employmentType
Kodeverk for arbeidsforholdstype, ansettelsesform, sluttårsak, lønnstype, arbeidstid og maritime arbeidsforhold.

*Nøkkelord:* arbeidsforholdstype, employment type, ordinært arbeidsforhold, maritimt arbeidsforhold, frilanser, oppdragstaker, ansettelsesform, sluttårsak, sluttarsak, skipsregister, skipstype, fartsområde, kodeverk, koder, a-melding kodeliste, maritime

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/employment/employmentType/employmentEndReasonType` | Find all employment end reason type IDs. |  | PERSONDATA |
| `GET /employee/employment/employmentType/employmentFormType` | Find all employment form type IDs. |  | PERSONDATA |
| `GET /employee/employment/employmentType/maritimeEmploymentType` | Find all maritime employment type IDs. | type* | PERSONDATA |
| `GET /employee/employment/employmentType/salaryType` | Find all salary type IDs. |  | PERSONDATA |
| `GET /employee/employment/employmentType/scheduleType` | Find all schedule type IDs. |  | PERSONDATA |
| `GET /employee/employment/employmentType` | Find all employment type IDs. |  | PERSONDATA |

### employee/employment/leaveOfAbsence
Permisjoner og permitteringer på et arbeidsforhold (prosent, periode, type), som rapporteres i a-meldingen.

*Nøkkelord:* permisjon, permisjoner, permittering, permittert, foreldrepermisjon, fødselspermisjon, fodselspermisjon, utdanningspermisjon, velferdspermisjon, militærtjeneste, leave of absence, furlough, lønnstrekk, a-melding permisjon, permisjonsprosent, permisjonsfravær, pappapermisjon, omsorgspermisjon, ulønnet permisjon, ulonnet permisjon, delvis permittert, permisjon a-melding

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/employment/leaveOfAbsence/{id}` | Find leave of absence by ID. | id* | PERSONDATA |
| `PUT /employee/employment/leaveOfAbsence/{id}` | Update leave of absence. | id* | PERSONDATA |
| `GET /employee/employment/leaveOfAbsence` | Find all leave of absence corresponding with the sent data. | employmentIds, date, minPercentage, maxPercentage | PERSONDATA |
| `POST /employee/employment/leaveOfAbsence` | Create leave of absence. |  | PERSONDATA |
| `POST /employee/employment/leaveOfAbsence/list` | Create multiple leave of absences. |  | PERSONDATA |

### employee/employment/leaveOfAbsenceType
Kodeliste over permisjonstyper (permisjon, permittering, foreldrepenger, militær, utdanning, velferd m.m.).

*Nøkkelord:* permisjonstype, permisjonstyper, leave of absence type, permitteringstype, kodeliste permisjon, foreldrepenger, velferdspermisjon, utdanningspermisjon, permisjonskode

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/employment/leaveOfAbsenceType` | Find all leave of absence type IDs. |  | PERSONDATA |

### employee/employment/occupationCode
Yrkeskoder (STYRK-08) som må settes på arbeidsforholdet for a-meldingen.

*Nøkkelord:* yrkeskode, yrkeskoder, styrk, styrk-08, stillingskode, occupation code, yrke, stillingstittel, profesjonskode, a-melding yrke, yrkesbetegnelse

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/employment/occupationCode/{id}` | Get occupation by ID. | id* | PERSONDATA |
| `GET /employee/employment/occupationCode` | Find all profession codes. | id, nameNO, code | PERSONDATA |

### employee/employment/remunerationType
Kodeliste over avlønningstyper (fastlønn, timelønn, provisjon, honorar, akkord).

*Nøkkelord:* avlønningstype, avlonningstype, lønnstype, lonnstype, fastlønn, fastlonn, timelønn, timelonn, provisjon, honorar, akkord, remuneration type, månedslønn

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/employment/remunerationType` | Find all remuneration type IDs. |  | PERSONDATA |

### employee/employment/workingHoursScheme
Kodeliste over arbeidstidsordninger (ikke skift, døgnkontinuerlig, skift, offshore m.m.).

*Nøkkelord:* arbeidstidsordning, arbeidstid, skift, skiftarbeid, turnus, døgnkontinuerlig, dognkontinuerlig, offshore, working hours scheme, ikke skift, helkontinuerlig

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/employment/workingHoursScheme` | Find working hours scheme ID. |  | PERSONDATA |

### employee/hourlyCostAndRate
Datostyrt timekost, internsats og budsjettsats per ansatt, brukt i prosjektregnskap og fakturering av timer.

*Nøkkelord:* timekost, timesats, timepris, internpris, kostpris, budsjettsats, hourly rate, hourly cost, timekostnad, prosjektkalkyle, fakturerbar sats, internsats, hour cost rate, timekost ansatt, salgspris time, timerate, kostsats, timekostsats

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/hourlyCostAndRate/{id}` | Find hourly cost and rate by ID. | id* | PERSONDATA |
| `PUT /employee/hourlyCostAndRate/{id}` | Update hourly cost and rate. | id* | PERSONDATA |
| `GET /employee/hourlyCostAndRate` | Find all hourly cost and rates for employee. | employeeId | PERSONDATA |
| `POST /employee/hourlyCostAndRate` | Create hourly cost and rate. |  | PERSONDATA |

### employee/nextOfKin
Pårørende/nærmeste pårørende registrert på en ansatt.

*Nøkkelord:* pårørende, parorende, nærmeste pårørende, naermeste parorende, next of kin, ektefelle, samboer, partner, forelder, barn, søsken, kontakt ved ulykke, nødkontakt, nodkontakt, hms, pårørendeliste

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/nextOfKin/{id}` | Find next of kin by ID. | id* | PERSONDATA |
| `PUT /employee/nextOfKin/{id}` | Update next of kin. | id* | PERSONDATA |
| `GET /employee/nextOfKin` | Find all next of kin for employee. | employeeId | PERSONDATA |
| `POST /employee/nextOfKin` | Create next of kin. |  | PERSONDATA |

### employee/preferences
Brukerinnstillinger per ansatt, som språk, prosjektfilter, ordrelinjeforslag og standard lager.

*Nøkkelord:* innstillinger, brukerinnstillinger, preferanser, preferences, språk, sprak, language, engelsk, norsk, prosjektfilter, standard lager, ordrelinjeforslag, min bruker, innlogget bruker

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /employee/preferences/:changeLanguage` | Change current employees language to the given language | language | PERSONDATA |
| `GET /employee/preferences/>loggedInEmployeePreferences` | Get employee preferences for current user |  | PERSONDATA |
| `PUT /employee/preferences/{id}` | Update employee preferences information. | id* | PERSONDATA |
| `PUT /employee/preferences/list` | Update multiple employee preferences. |  | PERSONDATA |
| `GET /employee/preferences` | Find employee preferences corresponding with sent data. | id, employeeId | PERSONDATA |

### employee/standardTime
Datostyrt normalarbeidstid (timer per dag) per ansatt, brukt i timeføring, fleksitid og overtid.

*Nøkkelord:* normaltid, normalarbeidstid, arbeidstid, timer per dag, standard time, standardtid, fleksitid, overtid, deltid, heltid, timebank, arbeidsdag, normaltid ansatt, arbeidstimer per dag, hours per day

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/standardTime/{id}` | Find standard time by ID. | id* | PERSONDATA |
| `PUT /employee/standardTime/{id}` | Update standard time. | id* | PERSONDATA |
| `GET /employee/standardTime/byDate` | Find standard time for employee by date. | employeeId, date | PERSONDATA |
| `GET /employee/standardTime` | Find all standard times for employee. | employeeId | PERSONDATA |
| `POST /employee/standardTime` | Create standard time. |  | PERSONDATA |

### employee/entitlement
Tilganger/rettigheter for brukere, både i egen konto og i klientkontoer (regnskapsførerbyrå), satt via maler.

*Nøkkelord:* tilgang, tilganger, rettighet, rettigheter, entitlement, entitlements, rolle, roller, brukerrettigheter, tilgangsmal, regnskapsfører, revisor, klienttilgang, klientkonto, byrå, personalansvarlig, fakturaansvarlig, avdelingsleder, 403, ingen tilgang, tilgangsgjennomgang, tilgangskontroll, privilegier, privileges, brukertilgang, proxy-innlogging, klientrettigheter

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /employee/entitlement/client` | Find all entitlements at client for user. | employeeId, customerId | BETA PERSONDATA |
| `GET /employee/entitlement/{id}` | Get entitlement by ID. | id* | PERSONDATA |
| `PUT /employee/entitlement/:grantClientEntitlementsByTemplate` | Update employee entitlements in client account. | employeeId*, customerId*, template*, addToExisting | BETA PERSONDATA |
| `PUT /employee/entitlement/:grantEntitlementsByTemplate` | Update employee entitlements. | employeeId*, template* | BETA PERSONDATA |
| `GET /employee/entitlement` | Find all entitlements for user. | employeeId | PERSONDATA |

<a id="hovedbok"></a>
## Hovedbok, bilag, posteringer, kontoplan, perioder, budsjett, avstemming

### balance/reconciliation
Avstemming av balansekontoer i regnskapsbyrå-modulen: opprette en årsavstemmingskontekst for en klient og år, og hente bilagene som ligger bak saldoen på en konto i avstemmingsperioden.

*Nøkkelord:* avstemming, balanseavstemming, årsavstemming, arsavstemming, avstemme balansekonto, kontoavstemming, saldokontroll, spesifikasjon balanse, årsoppgjør, arsoppgjor, reconciliation, balance reconciliation, annual context, reconciliationid, regnskapsbyrå, regnskapsbyra, saldospesifikasjon, spesifisere saldo, kontrollere saldo, avstemmingsmodul, bilag bak saldo, balance reconciliation vouchers

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `POST /balance/reconciliation/annual/context` | Create a annualBalance reconciliation context for a customer |  |  |
| `GET /balance/reconciliation/{reconciliationId}/account/{accountId}/vouchers` |  | reconciliationId*, accountId*, fromDate, toDateExclusive, query |  |

### accountingOffice/reconciliations/{reconciliationId}/control/:controlReconciliation
Markerer en avstemming som kontrollert (fire-øyne-kontroll/godkjenning av avstemmingen) i regnskapsbyrå-modulen.

*Nøkkelord:* kontrollert, kontrollere avstemming, godkjenne avstemming, fire øyne, fire oyne, reviewer, kvalitetskontroll, control reconciliation, controlled, signere avstemming, attestere avstemming, kontrollør, kontrollor

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /accountingOffice/reconciliations/{reconciliationId}/control/:controlReconciliation` | Mark a reconciliation as controlled | reconciliationId* |  |

### accountingOffice/reconciliations/{reconciliationId}/control
Lister kontrollhistorikken for en avstemming (hvem som avstemte, ba om kontroll og kontrollerte, og når).

*Nøkkelord:* kontrollhistorikk, avstemmingslogg, hvem avstemte, status avstemming, reconciled, control requested, controlled, reconciliation control, revisjonsspor, sporbarhet

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /accountingOffice/reconciliations/{reconciliationId}/control` | Returns a list of reconciliation controls with the given reconciliationId | reconciliationId* |  |

### accountingOffice/reconciliations/{reconciliationId}/control/:reconcile
Markerer en avstemming som avstemt (ferdig avstemt av saksbehandler) i regnskapsbyrå-modulen.

*Nøkkelord:* avstemt, marker avstemt, ferdig avstemt, reconcile, reconciled, avstemme konto, lukke avstemming, kontoavstemming ferdig

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /accountingOffice/reconciliations/{reconciliationId}/control/:reconcile` | Mark a reconciliation as reconciled | reconciliationId* |  |

### accountingOffice/reconciliations/{reconciliationId}/control/:requestControl
Ber én eller flere ansatte (oppdragsansvarlig/kontrollør) om å kontrollere en avstemming.

*Nøkkelord:* be om kontroll, send til kontroll, request control, oppdragsansvarlig, kontrollør, kontrollor, godkjenner, fire øyne, reviewer, attestasjon avstemming

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /accountingOffice/reconciliations/{reconciliationId}/control/:requestControl` | Request control of a reconciliation | reconciliationId* |  |

### balanceSheet
Saldobalanse: inngående saldo, bevegelse og utgående saldo per konto for en periode, med filter på avdeling, prosjekt, kunde, ansatt og frie dimensjoner.

*Nøkkelord:* saldobalanse, saldo, råbalanse, rabalanse, trial balance, balance sheet, inngående balanse, ib, ub, utgående balanse, bevegelse, resultat, balanse, kontosaldo, resultatregnskap, balanseregnskap, hittil i år, saldoliste, resultatrapport, balanserapport, hovedbokssaldo, profit and loss, p&l, periodeoversikt, fri dimensjon

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /balanceSheet` | Get balance sheet (saldobalanse). | dateFrom*, dateTo*, accountNumberFrom, accountNumberTo, customerId, employeeId, departmentId, projectId, includeSubProjects, includeActiveAccountsWithoutMovements, customerIds, employeeIds, departmentIds, projectIds, freeDimension1, freeDimension2, freeDimension3 |  |

### currency
Valutaer og valutakurser (Norges Bank-kurser) samt omregning av beløp mellom valutaer og til selskapets valuta på en gitt dato.

*Nøkkelord:* valuta, valutakurs, kurs, eur, usd, sek, omregning, agio, disagio, valutadifferanse, currency, exchange rate, rate, nok, norges bank, utenlandsk valuta, valutakurser, dagskurs, gbp, dkk, valutaomregning, fx

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /currency/{id}` | Get currency by ID. | id* |  |
| `GET /currency` | Find currencies corresponding with sent data. | id, code |  |
| `GET /currency/{fromCurrencyID}/{toCurrencyID}/exchangeRate` | Returns the amount in the specified currency, where the input amount is in fromCurrency, using the newest exchange rate available for the given date | fromCurrencyID*, toCurrencyID*, amount*, date* |  |
| `GET /currency/{fromCurrencyID}/exchangeRate` | Returns the amount in the company currency, where the input amount is in fromCurrency, using the newest exchange rate available for the given date | fromCurrencyID*, amount*, date* |  |
| `GET /currency/{id}/rate` | Find currency exchange rate corresponding with sent data. | id*, date* |  |

### ledger
Hovedbok per konto (inngående saldo, bevegelse, utgående saldo og posteringer) og åpne poster summert per konto per dato (LedgerAccount).

*Nøkkelord:* hovedbok, hovedbokskonto, kontoutskrift, kontospesifikasjon, general ledger, ledger, åpne poster, apne poster, open post, reskontro, kundereskontro, leverandørreskontro, leverandorreskontro, saldo per konto, inngående saldo, utgående saldo, kontokort, hovedboksutskrift, kontoutdrag, saldo på konto, saldo pa konto, inngaende saldo, utgaende saldo

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/openPost` | Find open posts corresponding with sent data. | date*, accountId, supplierId, customerId, employeeId, departmentId, projectId, productId, accountingDimensionValue1Id, accountingDimensionValue2Id, accountingDimensionValue3Id |  |
| `GET /ledger` | Get ledger (hovedbok). | dateFrom*, dateTo*, openPostings, accountId, supplierId, customerId, employeeId, departmentId, projectId, productId, accountingDimensionValue1Id, accountingDimensionValue2Id, accountingDimensionValue3Id |  |

### ledger/account
Kontoplanen: søke opp, opprette, endre, deaktivere og slette kontoer, inkl. MVA-kode, bankkontoinfo, SAF-T-kode og krav om avdeling/prosjekt/dimensjon.

*Nøkkelord:* kontoplan, konto, kontonummer, hovedbokskonto, ns 4102, ns4102, standard kontoplan, chart of accounts, account, saft, saf-t, grupperingskode, mva-kode på konto, bankkonto, deaktivere konto, ny konto, opprette konto, balansekonto, resultatkonto, reskontrotype, kontotype, avstemmingspliktig konto, lovlige mva-koder, ledger type, flere reskontroer

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/account/{id}` | Get account by ID. | id* |  |
| `PUT /ledger/account/{id}` | Update account. | id* |  |
| `DELETE /ledger/account/{id}` | Delete account. | id* |  |
| `PUT /ledger/account/list` | Update multiple accounts. |  |  |
| `POST /ledger/account/list` | Create several accounts. |  |  |
| `DELETE /ledger/account/list` | Delete multiple accounts. | ids* |  |
| `GET /ledger/account` | Find accounts corresponding with sent data. | id, number, isBankAccount, isInactive, isApplicableForSupplierInvoice, ledgerType, isBalanceAccount, saftCode |  |
| `POST /ledger/account` | Create a new account. |  |  |

### ledger/accountingDimensionName
Frie (egendefinerte) regnskapsdimensjoner – opprette, navngi, aktivere/deaktivere og slette inntil tre ekstra dimensjoner.

*Nøkkelord:* fri dimensjon, frie dimensjoner, egendefinert dimensjon, dimensjon, analysedimensjon, kostnadssted, kostnadsbærer, kostnadsbaerer, segment, accounting dimension, free dimension, user defined dimension, dimensionindex, dimensjonsnavn, egne dimensjoner, egendefinerte felt

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/accountingDimensionName/{id}` | Get a single accounting dimension name by ID | id* |  |
| `PUT /ledger/accountingDimensionName/{id}` | Update an accounting dimension | id* |  |
| `DELETE /ledger/accountingDimensionName/{id}` | Delete an accounting dimension name by ID | id* |  |
| `GET /ledger/accountingDimensionName` | Get all accounting dimension names. | activeOnly |  |
| `POST /ledger/accountingDimensionName` | Create a new free (aka 'user defined') accounting dimension |  |  |
| `GET /ledger/accountingDimensionName/search` | Search for accounting dimension names according to criteria. | dimensionIndex, activeOnly, onlyDimensionsWithActiveValues |  |

### ledger/accountingDimensionValue
Verdier for de frie regnskapsdimensjonene (f.eks. filial, bil, kampanje) – opprette, oppdatere, søke og slette.

*Nøkkelord:* dimensjonsverdi, dimensjonsverdier, verdi fri dimensjon, kostnadssted, segmentverdi, accounting dimension value, free dimension value, dimension value, vis i bilagsregistrering, showinvoucherregistration

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/accountingDimensionValue/{id}` | Find accounting dimension values by ID. | id* |  |
| `DELETE /ledger/accountingDimensionValue/{id}` | Delete an accounting dimension value. Values that have been used in postings can not be deleted. | id* |  |
| `POST /ledger/accountingDimensionValue` | Create a new value for one of the free (aka 'user defined') accounting dimensions |  |  |
| `PUT /ledger/accountingDimensionValue/list` | Update accounting dimension values |  |  |
| `GET /ledger/accountingDimensionValue/search` | Search for accounting dimension values according to criteria. | dimensionIndex, activeOnly, showInVoucherRegistration |  |

### ledger/accountingPeriod
Regnskapsperioder (måneder) med start, slutt og om perioden er lukket, samt når hovedbok og lønn sist ble kontrollert – kun lesing.

*Nøkkelord:* regnskapsperiode, periode, periodelåsing, periodelasing, låst periode, last periode, lukket periode, månedsavslutning, manedsavslutning, accounting period, isclosed, periodeavslutning, regnskapsmåned, regnskapsmaned, kontrollert periode, periodekontroll, lukket måned

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/accountingPeriod/{id}` | Get accounting period by ID. | id* |  |
| `GET /ledger/accountingPeriod` | Find accounting periods corresponding with sent data. | id, numberFrom, numberTo, startFrom, startTo, endFrom, endTo |  |

### ledger/annualAccount
Regnskapsår (årsregnskapsperioder) med start- og sluttdato.

*Nøkkelord:* regnskapsår, regnskapsar, årsregnskap, arsregnskap, annual account, fiscal year, avvikende regnskapsår, årsoppgjør, arsoppgjor, regnskapsåret, regnskapsaret, årsperiode, arsperiode

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/annualAccount/{id}` | Get annual account by ID. | id* |  |
| `GET /ledger/annualAccount` | Find annual accounts corresponding with sent data. | id, yearFrom, yearTo |  |

### ledger/closeGroup
Lukkegrupper: grupper av posteringer som er lukket/utliknet mot hverandre (f.eks. faktura mot innbetaling).

*Nøkkelord:* lukkegruppe, lukket post, utlikning, utlignet, motpostert, avstemt post, close group, matched, matching, reskontroavstemming, åpne poster, apne poster

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/closeGroup/{id}` | Get close group by ID. | id* |  |
| `GET /ledger/closeGroup` | Find close groups corresponding with sent data. | id, dateFrom*, dateTo* |  |

### ledger/posting
Posteringer (transaksjonslinjer) i hovedboken – søke med filtre på konto, kunde, leverandør, prosjekt, avdeling, dimensjon og type, finne åpne poster og lukke poster mot hverandre.

*Nøkkelord:* postering, posteringer, transaksjon, transaksjoner, føring, foring, posting, postings, åpne poster, apne poster, open post, lukke poster, utlikne, utligne, kundereskontro, leverandørreskontro, leverandorreskontro, ansattreskontro, kontoutskrift, kontospesifikasjon, reskontropost, kid, externalref, fakturanummer, matching

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /ledger/posting/:closePostings` | Close postings. |  |  |
| `GET /ledger/posting/{id}` | Find postings by ID. | id* |  |
| `GET /ledger/posting/openPost` | Find open posts corresponding with sent data. | date*, accountId, supplierId, customerId, employeeId, departmentId, projectId, productId, accountNumberFrom, accountNumberTo, accountingDimensionValue1Id, accountingDimensionValue2Id, accountingDimensionValue3Id, sorted |  |
| `GET /ledger/posting` | Find postings corresponding with sent data. | dateFrom*, dateTo*, openPostings, accountId, supplierId, customerId, employeeId, departmentId, projectId, productId, accountNumberFrom, accountNumberTo, type, accountingDimensionValue1Id, accountingDimensionValue2Id, accountingDimensionValue3Id |  |

### ledger/postingByDate
Rask, paginert uthenting av alle posteringer i et datointervall (for eksport, dataanalyse og synkronisering).

*Nøkkelord:* eksport posteringer, datauttrekk, alle transaksjoner, bulk, synkronisering, dataanalyse, postingbydate, posting export, hovedbok eksport, transaksjonsliste, rask uthenting, alle posteringer, full eksport, revisjonsuttrekk, revisoruttrekk

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/postingByDate` | Get postings by date range with pagination. Returns the same PostingDTO as /ledger/posting. Simplified endpoint for better performance. Fields and Changes are not supported. Token must have access to all vouchers in the company, otherwise a validation error is returned. If access control for salary information is activated, the token must have access to salary information as well. | dateFrom*, dateTo* |  |

### ledger/voucher/openingBalance
Åpningsbalanse (IB) ved oppstart i Tripletex: registrere, hente og slette åpningsbalansebilaget med tilhørende korreksjonsbilag, inkl. reskontrosaldoer.

*Nøkkelord:* åpningsbalanse, apningsbalanse, inngående balanse, inngaende balanse, ib, opening balance, oppstart, konvertering, overgang fra annet system, startsaldo, korreksjonsbilag, correction voucher, reskontro ib, kundereskontro ib, leverandørreskontro ib, åpningsbalansebilag, apningsbalansebilag, ib-bilag, hjelpekonto

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/voucher/openingBalance/>correctionVoucher` | Get the correction voucher for the opening balance. |  |  |
| `GET /ledger/voucher/openingBalance` | Get the voucher for the opening balance. |  |  |
| `POST /ledger/voucher/openingBalance` | Add an opening balance on the given date. All movements before this date will be 'zeroed out' in a separate correction voucher. The opening balance must have the first day of a month as the date, and it's also recommended to have the first day of the year as the date. If the postings provided don't balance the voucher, the difference will automatically be posted to a help account |  |  |
| `DELETE /ledger/voucher/openingBalance` | Delete the opening balance. The correction voucher will also be deleted |  |  |

### ledger/voucher
Bilag: søke, opprette (manuelle bilag/journalposter), endre, reversere, slette, bokføre fra kladd, sende til bilagsmottak, laste opp og hente vedlegg/PDF og importere dokumenter og GBAT10.

*Nøkkelord:* bilag, bilagsnummer, føre bilag, fore bilag, bokføre, bokfore, manuelt bilag, memorialbilag, journalpost, voucher, journal entry, reversere, tilbakeføre, slette bilag, vedlegg, kladd, ikke bokført, gbat10, periodisering, bilagsføring, bilagsforing, ompostering, korreksjonsbilag, bilagsjournal, føring

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/voucher/{id}` | Get voucher by ID. | id* |  |
| `PUT /ledger/voucher/{id}` | Update voucher. Postings with guiRow==0 will be deleted and regenerated. | sendToLedger, id* |  |
| `DELETE /ledger/voucher/{id}` | Delete voucher by ID. | id* |  |
| `POST /ledger/voucher/{voucherId}/attachment` | Upload attachment to voucher. If the voucher already has an attachment the content will be appended to the existing attachment as new PDF page(s). Valid document formats are PDF, PNG, JPEG and TIFF. Non PDF formats will be converted to PDF. Send as multipart form. | voucherId* |  |
| `DELETE /ledger/voucher/{voucherId}/attachment` | Delete attachment. | voucherId*, version, sendToInbox, split |  |
| `GET /ledger/voucher/{voucherId}/pdf` | Get PDF representation of voucher by ID. | voucherId* |  |
| `GET /ledger/voucher/>externalVoucherNumber` | Find vouchers based on the external voucher number. | externalVoucherNumber |  |
| `POST /ledger/voucher/importDocument` | Upload a document to create one or more vouchers. Valid document formats are PDF, PNG, JPEG and TIFF. EHF/XML is possible with agreement with Tripletex. Send as multipart form. | split |  |
| `POST /ledger/voucher/importGbat10` | Import GBAT10. Send as multipart form. |  |  |
| `GET /ledger/voucher/>nonPosted` | Find non-posted vouchers. | dateFrom, dateTo, includeNonApproved*, changedSince |  |
| `GET /ledger/voucher/{id}/options` | Returns a data structure containing meta information about operations that are available for this voucher. Currently only implemented for DELETE: It is possible to check if the voucher is deletable. | id* |  |
| `GET /ledger/voucher` | Find vouchers corresponding with sent data. | id, number, numberFrom, numberTo, typeId, dateFrom*, dateTo* |  |
| `POST /ledger/voucher` | Add new voucher. IMPORTANT: Also creates postings. Only the gross amounts will be used. Amounts should be rounded to 2 decimals. | sendToLedger, convertFromAmountGrossCurrency |  |
| `PUT /ledger/voucher/list` | Update multiple vouchers. Postings with guiRow==0 will be deleted and regenerated. | sendToLedger |  |
| `PUT /ledger/voucher/{id}/:reverse` | Reverses the voucher, and returns the reversed voucher. Supports reversing most voucher types, except salary transactions. | id*, date* |  |
| `PUT /ledger/voucher/{id}/:sendToInbox` | Send voucher to inbox. | id*, version, comment |  |
| `PUT /ledger/voucher/{id}/:sendToLedger` | Send voucher to ledger. | id*, version, number |  |
| `POST /ledger/voucher/{voucherId}/pdf/{fileName}` | Use POST ledger/voucher/{voucherId}/attachment instead. | voucherId*, fileName* | DEPRECATED |
| `GET /ledger/voucher/>voucherReception` | Find vouchers in voucher reception. | dateFrom, dateTo, searchText |  |

### ledger/voucher/historical
Import av historiske bilag fra tidligere regnskapssystem (lukkede år) med vedlegg, lukking av historiske poster og opprettelse av ansatte fra import.

*Nøkkelord:* historiske bilag, historikk, konvertering, migrering, import fra annet system, tidligere regnskapssystem, historical voucher, historical import, lukkede år, lukkede ar, overgang, visma, poweroffice, fiken, uni

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /ledger/voucher/historical/:closePostings` | Close postings. | postingIds | BETA |
| `POST /ledger/voucher/historical/employee` | Create one employee, based on import from external system. Validation is less strict, ie. employee department isn't required. |  | BETA |
| `POST /ledger/voucher/historical/historical` | API endpoint for creating historical vouchers. These are vouchers created outside Tripletex, and should be from closed accounting years. The intended usage is to get access to historical transcations in Tripletex. Also creates postings. All amount fields in postings will be used. VAT postings must be included, these are not generated automatically like they are for normal vouchers in Tripletex. Requires the \"All vouchers\" and \"Advanced Voucher\" permissions. | comment, useCustomNumberSeries |  |
| `PUT /ledger/voucher/historical/:reverseHistoricalVouchers` | Deletes all historical vouchers. Requires the "All vouchers" and "Advanced Voucher" permissions. |  | BETA |
| `POST /ledger/voucher/historical/{voucherId}/attachment` | Upload attachment to voucher. If the voucher already has an attachment the content will be appended to the existing attachment as new PDF page(s). Valid document formats are PDF, PNG, JPEG and TIFF. Non PDF formats will be converted to PDF. Send as multipart form. | voucherId* |  |

### ledger/voucherType
Bilagstyper (f.eks. Leverandørfaktura, Utgående faktura, Bankinnbetaling, Memorialpostering) brukt ved registrering og filtrering av bilag.

*Nøkkelord:* bilagstype, bilagsart, voucher type, memorial, memorialpostering, leverandørfaktura, typeid, utgående faktura, utgaende faktura, bankbilag, leverandorfaktura, bilagskategori

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/voucherType/{id}` | Get voucher type by ID. | id* |  |
| `GET /ledger/voucherType` | Find voucher types corresponding with sent data. | name |  |

### ledger/postingRules
Selskapets posteringsregler: hvilke standardkontoer systemet bruker automatisk (kundefordringer, leverandørgjeld, ansattgjeld, øreavrunding m.m.).

*Nøkkelord:* posteringsregler, standardkontoer, systemkontoer, kundefordringer, 1500, leverandørgjeld, leverandorgjeld, 2400, øreavrunding, oreavrunding, posting rules, mva per avdeling, default accounts, avrundingskonto, ansattgjeld, abonnementsperiodisering, systemkonto

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /ledger/postingRules` | Get posting rules for current company. The posting rules defined which accounts from the chart of accounts that are used for postings when the system creates postings. |  |  |

### resultbudget
Resultatbudsjett (kun lesing) for selskapet, avdelinger, prosjekter, produkter og ansatte per konto og periode, til budsjettoppfølging.

*Nøkkelord:* budsjett, resultatbudsjett, budsjettavvik, avvik, budsjett mot regnskap, result budget, budget, avdelingsbudsjett, prosjektbudsjett, periodisert budsjett, måltall, maltall, budsjettall, budsjettoppfølging, budsjettoppfolging, budget vs actual, årsbudsjett, arsbudsjett

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /resultbudget/company` | Get result budget for company | year |  |
| `GET /resultbudget/department/{id}` | Get result budget associated with a departmentId | id*, year |  |
| `GET /resultbudget/employee/{id}` | Get result budget associated with an employeeId | id*, year |  |
| `GET /resultbudget/product/{id}` | Get result budget associated with a productId | id*, year |  |
| `GET /resultbudget/project/{id}` | Get result budget associated with a projectId | id*, year |  |
| `GET /resultbudget` | Find result budgets corresponding with sent data. Either specify the ids of the departments, projects, products or employees to return result budgets for, or use the boolean parameters includeAll***ResultBudgets to get all results budgets. | departmentIds, projectIds, productIds, employeeIds, year, includeAllDepartmentResultBudgets, includeAllProjectResultBudgets, includeAllProductResultBudgets, includeAllEmployeeResultBudgets |  |

### voucherApprovalListElement
Enkeltlinjer i attestasjons-/godkjenningsflyten for bilag (hvem som skal eller har godkjent, status og kommentarer).

*Nøkkelord:* attestasjon, attestere, godkjenning, godkjenne bilag, attestant, approval, voucher approval, godkjenningsflyt, anvisning, attestasjonsliste

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /voucherApprovalListElement/{id}` | Get by ID. | id* |  |

### voucherInbox
Bilagsmottaket (innboksen): e-postadressen for å sende inn fakturaer og bilag, og antall dokumenter som venter på behandling.

*Nøkkelord:* bilagsmottak, innboks, inbox, voucher inbox, e-postadresse bilag, epost bilag, skanning, ubehandlede bilag, antall bilag, ehf, dokumentmottak, inngående faktura, bilagsmottaket, innboks antall, e-post til bilagsmottak

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /voucherInbox/emailAddress` | Get the email address for sending invoices and vouchers to the voucher inbox. |  |  |
| `GET /voucherInbox/inboxCount` | Get count of items in the Voucher Inbox |  |  |

### voucherMessage
Kommentarer/meldinger knyttet til bilag (BETA) – lese og legge til kommentarer på ett eller flere bilag.

*Nøkkelord:* kommentar, bilagskommentar, melding, notat på bilag, voucher message, comment, spørsmål til kunde, sporsmal til kunde, dokumentasjonsbehov, kommentarer på bilag, kommentarer pa bilag

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /voucherMessage` | Find voucherMessage (or a comment) put on a voucher by inputting voucher ids | voucherIds | BETA |
| `POST /voucherMessage` | Post new voucherMessage. |  | BETA |

### voucherStatus
Prosess-/integrasjonsstatus for bilag (f.eks. inkasso og ekstern leverandørfakturabehandling), som krever oppsett fra Tripletex.

*Nøkkelord:* bilagsstatus, status, inkasso, debt collection, integrasjon, voucher status, prosessstatus, oversendt inkasso, ekstern behandling, referansenummer, inkassobyrå, inkassobyra, integrasjonspartner

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /voucherStatus/{id}` | Get voucherStatus by ID. | id* |  |
| `GET /voucherStatus` | Find voucherStatus corresponding with sent data. The voucherStatus is used to coordinate integration processes. Requires setup done by Tripletex, currently supports debt collection. | ids, voucherIds, status, type |  |
| `POST /voucherStatus` | Post new voucherStatus. |  |  |

<a id="salg"></a>
## Kunder, ordre, faktura, purring, abonnement/CRM

### deliveryAddress
Leveringsadresser knyttet til kunder og ordre – søke opp, hente og endre (inkl. matrikkel knr/gnr/bnr); ikke kundens post-/fakturaadresse, som endres på kunden.

*Nøkkelord:* leveringsadresse, leveranseadresse, delivery address, deliveryaddress, levering, postnummer, poststed, matrikkel, gnr, bnr, leveringssted, fraktadresse, byggeplass, anleggsadresse

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /deliveryAddress/{id}` | Get address by ID. | id* |  |
| `PUT /deliveryAddress/{id}` | Update address. | id* |  |
| `GET /deliveryAddress` | Find addresses corresponding with sent data. | id, addressLine1, addressLine2, postalCode, city, name |  |

### customer
Kunderegisteret: søke, opprette, oppdatere, masseimportere, deaktivere og slette kunder, inkl. fakturainnstillinger (sendemåte, betalingsfrist, purreinnstillinger, reskontrokonto).

*Nøkkelord:* kunde, kunderegister, kundekort, kundenummer, kundenr, kundeliste, organisasjonsnummer, orgnr, org.nr, customer, debitor, fakturaepost, betalingsfrist, betalingsbetingelser, sendemåte, sendemate, ehf, efaktura, privatkunde, bedriftskunde, ny kunde, inaktiv kunde, kundeimport, purreinnstillinger, faktoring

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /customer/{id}` | Get customer by ID. | id* |  |
| `PUT /customer/{id}` | Update customer. | id* |  |
| `DELETE /customer/{id}` | Delete customer by ID | id* | BETA |
| `GET /customer` | Find customers corresponding with sent data. | id, customerAccountNumber, organizationNumber, email, invoiceEmail, customerName, phoneNumberMobile, isInactive, accountManagerId, changedSince, category1Id, category2Id, category3Id |  |
| `POST /customer` | Create customer. Related customer addresses may also be created. |  |  |
| `PUT /customer/list` | Update multiple customers. Addresses can also be updated. |  | BETA |
| `POST /customer/list` | Create multiple customers. Related supplier addresses may also be created. |  | BETA |

### customer/category
Kategorier (1–3) som brukes til å gruppere og filtrere kunder og leverandører, f.eks. bransje, region eller kundetype.

*Nøkkelord:* kundekategori, kategori, leverandorkategori, leverandørkategori, kundegruppe, segment, gruppering, customer category, kategori1, kategori2, kategori3, kundetype

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /customer/category/{id}` | Find customer/supplier category by ID. | id* |  |
| `PUT /customer/category/{id}` | Update customer/supplier category. | id* |  |
| `GET /customer/category` | Find customer/supplier categories corresponding with sent data. | id, name, number, description, type |  |
| `POST /customer/category` | Add new customer/supplier category. |  |  |

### invoice
Utgående kundefakturaer: søke/fakturajournal, hente, opprette, sende (e-post/EHF/eFaktura/papir), laste ned PDF, kreditere (kreditnota), registrere innbetaling og opprette purring/inkassovarsel.

*Nøkkelord:* faktura, utgående faktura, utgaende faktura, salgsfaktura, kundefaktura, invoice, fakturanummer, kid, kreditnota, kreditnote, kreditere, credit note, innbetaling, registrere betaling, purring, inkassovarsel, ehf, efaktura, fakturajournal, utestående, utestaende, forfalt, ubetalt, kundefordring, faktura pdf

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /invoice/{id}/:createCreditNote` | Creates a new Invoice representing a credit memo that nullifies the given invoice. Updates this invoice and any pre-existing inverse invoice. | id*, date*, comment, creditNoteEmail, sendToCustomer, sendType |  |
| `PUT /invoice/{id}/:createReminder` | Create invoice reminder and sends it by the given dispatch type. Supports the reminder types SOFT_REMINDER, REMINDER and NOTICE_OF_DEBT_COLLECTION. DispatchType NETS_PRINT must have type NOTICE_OF_DEBT_COLLECTION. SMS and NETS_PRINT must be activated prior to usage in the API. | id*, type*, date*, includeCharge, includeInterest, dispatchType, dispatchTypes, smsNumber, email, address, postalCode, city |  |
| `GET /invoice/{id}` | Get invoice by ID. | id* |  |
| `GET /invoice/{invoiceId}/pdf` | Get invoice document by invoice ID. | invoiceId*, download |  |
| `PUT /invoice/{id}/:payment` | Update invoice. The invoice is updated with payment information. The amount is in the invoice’s currency. | id*, paymentDate*, paymentTypeId*, paidAmount*, paidAmountCurrency |  |
| `GET /invoice` | Find invoices corresponding with sent data. Includes charged outgoing invoices only. | id, invoiceDateFrom*, invoiceDateTo*, invoiceNumber, kid, voucherId, customerId, status |  |
| `POST /invoice` | Create invoice. Related Order and OrderLines can be created first, or included as new objects inside the Invoice. | sendToCustomer, paymentTypeId, paidAmount |  |
| `POST /invoice/list` | Create multiple invoices. Max 100 at a time. | sendToCustomer | BETA |
| `PUT /invoice/{id}/:send` | Send invoice by ID and sendType. Optionally override email recipient. | id*, sendType*, overrideEmailAddress |  |

### invoiceRemark
Fakturamerknader (intern merknad på faktura, f.eks. avtalt betalingsutsettelse og dato purring er utsatt til).

*Nøkkelord:* fakturamerknad, merknad, notat på faktura, invoice remark, invoiceremark, betalingsutsettelse, utsatt purring, purrestopp, purrepause, betalingsavtale, avtale om betaling, postponereminders

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /invoiceRemark/{id}` | Get invoice remark by ID. | id* |  |

### invoice/paymentType
Betalingstyper for innbetalinger på kundefaktura (bank, kontant, kort, Vipps osv.) – trengs som paymentTypeId ved registrering av betaling.

*Nøkkelord:* betalingstype, innbetalingstype, paymenttype, paymenttypeid, betalingsmåte, betalingsmate, bank, kontant, kort, vipps, innbetaling, innbetalingskonto, bankkonto 1920

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /invoice/paymentType/{id}` | Get payment type by ID. | id* |  |
| `GET /invoice/paymentType` | Find payment type corresponding with sent data. | id, description, query |  |

### invoice/details
Prosjektfakturadetaljer (ProjectInvoiceDetails): honorar, påslag, timer, utlegg og a konto-saldo per prosjekt på en faktura.

*Nøkkelord:* prosjektfaktura, prosjektfakturadetaljer, fakturadetaljer, honorar, timer fakturert, påslag, paslag, utlegg, viderefakturering, a konto saldo, akonto saldo, project invoice details, projectinvoicedetails

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /invoice/details/{id}` | Get ProjectInvoiceDetails by ID. | id* |  |
| `GET /invoice/details` | Find ProjectInvoiceDetails corresponding with sent data. | id, invoiceDateFrom*, invoiceDateTo* |  |

### order
Ordre (salgsordre) med ordrelinjer som grunnlag for faktura: opprette, endre, fakturere, samlefakturere, abonnement, ordrebekreftelse, pakkseddel og vedlegg.

*Nøkkelord:* ordre, salgsordre, order, ordrebekreftelse, pakkseddel, følgeseddel, folgeseddel, fakturagrunnlag, fakturere ordre, fakturering, utfakturering, samlefaktura, abonnement, repeterende faktura, gjentakende faktura, a konto, akonto, forskuddsfaktura, fakturautkast, forhåndsvisning, forhandsvisning, vedlegg, restordre, backorder, subscription

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /order/{id}/:approveSubscriptionInvoice` | To create a subscription invoice, first create a order with the subscription enabled, then approve it with this method. This approves the order for subscription invoicing. | id*, invoiceDate* |  |
| `PUT /order/{id}/:attach` | Attach document to specified order ID. | id*, addToInvoiceMode, addToOrderMode |  |
| `GET /order/{id}` | Get order by ID. | id* |  |
| `PUT /order/{id}` | Update order. | id*, updateLinesAndGroups |  |
| `DELETE /order/{id}` | Delete order. | id* |  |
| `GET /order/packingNote/{orderId}/pdf` | Get PDF representation of packing note by ID. | orderId*, type, download |  |
| `GET /order/orderConfirmation/{orderId}/pdf` | Get PDF representation of order by ID. | orderId*, download, includeAttachments |  |
| `PUT /order/{id}/:invoice` | Create new invoice or subscription invoice from order. | id*, invoiceDate*, sendToCustomer, sendType, paymentTypeId, paidAmount, paidAmountAccountCurrency, paymentTypeIdRestAmount, paidAmountAccountCurrencyRest, createOnAccount, amountOnAccount, onAccountComment, createBackorder, invoiceIdIfIsCreditNote, overrideEmailAddress |  |
| `PUT /order/:invoiceMultipleOrders` | Charges a single customer invoice from multiple orders. The orders must be to the same customer, currency, due date, receiver email, attn. and smsNotificationNumber | id*, invoiceDate*, sendToCustomer, createBackorders | BETA |
| `GET /order` | Find orders corresponding with sent data. | id, number, customerId, orderDateFrom*, orderDateTo*, deliveryComment, isClosed, isSubscription |  |
| `POST /order` | Create order. |  |  |
| `PUT /order/sendInvoicePreview/{orderId}` | Send Invoice Preview to customer by email. | orderId*, email, message, saveAsDefault |  |
| `POST /order/list` | Create multiple Orders with OrderLines. Max 100 at a time. |  | BETA |
| `PUT /order/sendOrderConfirmation/{orderId}` | Send Order Confirmation to customer by email. | orderId*, email, message, saveAsDefault |  |
| `PUT /order/sendPackingNote/{orderId}` | Send Packing Note to customer by email. | orderId*, email, message, saveAsDefault, type |  |
| `PUT /order/{id}/:unApproveSubscriptionInvoice` | Unapproves the order for subscription invoicing. | id* |  |

### order/orderGroup
Ordregrupper for å gruppere ordrelinjer med overskrift, kommentar og delsum på ordre/faktura.

*Nøkkelord:* ordregruppe, gruppe, delsum, subtotal, overskrift, seksjon, ordergroup, linjegruppe, gruppering av linjer

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /order/orderGroup/{id}` | Get orderGroup by ID. A orderGroup is a way to group orderLines, and add comments and subtotals | id* |  |
| `DELETE /order/orderGroup/{id}` | Delete orderGroup by ID. | id* |  |
| `GET /order/orderGroup` | Find orderGroups corresponding with sent data. | ids, orderIds |  |
| `PUT /order/orderGroup` | Put orderGroup. | OrderLineIds, removeExistingOrderLines | BETA |
| `POST /order/orderGroup` | Post orderGroup. | orderLineIds | BETA |

### order/orderline
Ordrelinjer (varelinjer) på en ordre: produkt, antall, pris, rabatt, MVA-kode, samt plukking for lagerkunder.

*Nøkkelord:* ordrelinje, ordrelinjer, varelinje, fakturalinje, orderline, antall, enhetspris, pris, rabatt, påslag, paslag, mva-kode, mvakode, produkt, vare, plukk, plukke, plukkliste, linjetemplate, orderlinetemplate

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /order/orderline/{id}` | Get order line by ID. | id* |  |
| `PUT /order/orderline/{id}` | Put order line | id* | BETA |
| `DELETE /order/orderline/{id}` | Delete order line by ID. | id* | BETA |
| `POST /order/orderline/list` | Create multiple order lines. |  |  |
| `GET /order/orderline/orderLineTemplate` | Get order line template from order and product | orderId*, productId* | BETA |
| `PUT /order/orderline/{id}/:pickLine` | Pick order line. This is only available for customers who have Logistics and who activated the available inventory functionality. | id*, inventoryId, inventoryLocationId, pickDate | BETA |
| `POST /order/orderline` | Create order line. When creating several order lines, use /list for better performance. |  |  |
| `PUT /order/orderline/{id}/:unpickLine` | Unpick order line.This is only available for customers who have Logistics and who activated the available inventory functionality. | id* | BETA |

### discountPolicy
Rabattavtaler per kunde, produkt eller varegruppe (kun Logistikk Basis / grossistintegrasjon, BETA).

*Nøkkelord:* rabatt, kunderabatt, rabattavtale, prisavtale, varegrupperabatt, produktrabatt, discount, discountpolicy, nettopris, grossist

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /discountPolicy/{id}` | Get discount by ID. Available for Logistics Basis and Wholesaler integration. | id* | BETA |
| `GET /discountPolicy` | Find discounts corresponding with sent data. Available for Logistics Basis and Wholesaler integration. | customerId, productId, productGroupId, query, activeProducts | BETA |

### crm/prospect
CRM-prospekter/salgsmuligheter (leads) knyttet til kunde, selger og prosjekt/tilbud – kun lesing, og endepunktene er DEPRECATED.

*Nøkkelord:* prospekt, prospect, salgsmulighet, lead, crm, pipeline, konkurrent, potensiell kunde, tapt salg, salgsoppfølging

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /crm/prospect/{id}` | Get prospect by ID. | id* | DEPRECATED |
| `GET /crm/prospect` | Find prospects corresponding with sent data. | name, description, createdDateFrom, createdDateTo, customerId, salesEmployeeId, isClosed, closedReason, closedDateFrom, closedDateTo, competitor, prospectType, projectId, projectOfferId | DEPRECATED |

### reminder
Purringer som er opprettet på kundefakturaer: søke opp, hente detaljer (gebyr, renter, type) og laste ned purre-PDF.

*Nøkkelord:* purring, purringer, purrehistorikk, betalingspåminnelse, betalingspaminnelse, påminnelse, inkassovarsel, varsel om inkasso, inkasso, purregebyr, forsinkelsesrente, morarente, reminder, soft reminder, purre pdf, innfordring, dunning

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /reminder/{reminderId}/pdf` | Get reminder document by reminder ID. | reminderId* |  |
| `GET /reminder/{id}` | Get reminder by ID. | id* |  |
| `GET /reminder` | Find reminders corresponding with sent data. | id, dateFrom*, dateTo*, termOfPaymentTo, termOfPaymentFrom, invoiceId, customerId |  |

### supplierCustomer
Felles søk i aktive kunder og leverandører (kontakter/motparter) med fritekst.

*Nøkkelord:* kunde eller leverandør, kunde eller leverandor, motpart, motpartssøk, fritekst, suppliercustomer, finne firma, firmasøk, firmasok, kunde og leverandør, aktør

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /supplierCustomer/search` | Find all active suppliers and customers. | query |  |

<a id="innkjop"></a>
## Leverandører, leverandørfaktura, innkjøp, dokumentarkiv

### document
Lese metadata og laste ned innholdet (fil) for dokumenter i Tripletex, f.eks. originalfakturaen bak en leverandørfaktura eller et arkivdokument (BETA).

*Nøkkelord:* dokument, document, fil, vedlegg, last ned, laste ned, download, original faktura, originalfaktura, pdf, innhold, content, bilagsdokument, originalbilag, ehf xml

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /document/{id}/content` | Get content of document given by ID. | id*, download | BETA |
| `GET /document/{id}` | Get document by ID. | id* | BETA |

### documentArchive
Dokumentarkivet: laste opp, liste, endre og slette arkiverte filer knyttet til leverandør, kunde, prosjekt, produkt, konto, anleggsmiddel, ansatt eller kontrollskjema, samt opplasting til arkivmottak (BETA).

*Nøkkelord:* dokumentarkiv, arkiv, arkivere, document archive, dokumentasjon, avtale, kontrakt, last opp, laste opp, upload, arkivmottak, reception, kontrollskjema, årsoppgjør dokumentasjon, arsoppgjor, anleggsmiddel, kontodokumentasjon, avstemmingsdokumentasjon, vedlegg

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /documentArchive/account/{id}` | Find documents archived associated with account object type. | id*, periodDateFrom, periodDateTo | BETA |
| `POST /documentArchive/account/{id}` | Upload file to Account Document Archive. | id* | BETA |
| `GET /documentArchive/asset/{id}` | Find documents archived associated with asset object type. | id*, periodDateFrom, periodDateTo | BETA |
| `POST /documentArchive/asset/{id}` | Upload file to Asset Document Archive. | id* | BETA |
| `GET /documentArchive/customer/{id}` | Find documents archived associated with customer object type. | id*, periodDateFrom, periodDateTo | BETA |
| `POST /documentArchive/customer/{id}` | Upload file to Customer Document Archive. | id* | BETA |
| `PUT /documentArchive/{id}` | Update document archive. | id* | BETA |
| `DELETE /documentArchive/{id}` | Delete document archive. | id* | BETA |
| `GET /documentArchive/dynamicControlForm/{id}` | Find documents archived associated with control form object type. | id*, periodDateFrom, periodDateTo | BETA |
| `POST /documentArchive/dynamicControlForm/{id}` | Upload file to Control Form Document Archive. | id* | BETA |
| `POST /documentArchive/dynamicControlForm/{id}/list` | Upload multiple files to Control Form Document Archive. Send as multipart form. | id* | BETA |
| `GET /documentArchive/employee/{id}` | Find documents archived associated with employee object type. | id*, periodDateFrom, periodDateTo | BETA |
| `POST /documentArchive/employee/{id}` | Upload file to Employee Document Archive. | id* | BETA |
| `GET /documentArchive/product/{id}` | Find documents archived associated with product object type. | id*, periodDateFrom, periodDateTo | BETA |
| `POST /documentArchive/product/{id}` | Upload file to Product Document Archive. | id* | BETA |
| `GET /documentArchive/project/{id}` | Find documents archived associated with project object type. | id*, periodDateFrom, periodDateTo | BETA |
| `POST /documentArchive/project/{id}` | Upload file to Project Document Archive. | id* | BETA |
| `GET /documentArchive/supplier/{id}` | Find documents archived associated with supplier object type. | id*, periodDateFrom, periodDateTo | BETA |
| `POST /documentArchive/supplier/{id}` | Upload file to Supplier Document Archive. | id* | BETA |
| `POST /documentArchive/reception` | Upload a file to the document archive reception. Send as multipart form. |  | BETA |

### purchaseOrder
Innkjøpsordrer (krever Logistikk Basic): opprette, finne, endre, sende til leverandør på e-post/FTP, vedlegg og slette.

*Nøkkelord:* innkjøpsordre, innkjopsordre, innkjøp, innkjop, bestilling, bestille varer, purchase order, po, ordre til leverandør, sende innkjøpsordre, logistikk, logistics basic, restordre, leveringsdato, varekjøp, varekjop, innkjøpsordrer, rekvisisjon, innkjøp prosjekt

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /purchaseOrder/{id}` | Find purchase order by ID. Only available for Logistics Basic. | id* |  |
| `PUT /purchaseOrder/{id}` | Update purchase order. Only available for Logistics Basic. | id* |  |
| `DELETE /purchaseOrder/{id}` | Delete purchase order. Only available for Logistics Basic. | id* |  |
| `POST /purchaseOrder/{id}/attachment` | Upload attachment to purchase order. Only available for Logistics Basic. | id* |  |
| `DELETE /purchaseOrder/{id}/attachment` | Delete attachment. Only available for Logistics Basic. | id* |  |
| `GET /purchaseOrder` | Find purchase orders with send data. Only available for Logistics Basic. | number, deliveryDateFrom, deliveryDateTo, creationDateFrom, creationDateTo, id, supplierId, projectId, isClosed, withDeviationOnly |  |
| `POST /purchaseOrder` | Creates a new purchase order. Only available for Logistics Basic. |  |  |
| `PUT /purchaseOrder/{id}/:send` | Send purchase order by ID and sendType. Only available for Logistics Basic. | id*, sendType |  |
| `PUT /purchaseOrder/{id}/:sendByEmail` | Send purchase order by customisable email. Only available for Logistics Basic. | id* |  |
| `POST /purchaseOrder/{id}/attachment/list` | Upload multiple attachments to Purchase Order. Only available for Logistics Basic. | id* |  |

### purchaseOrder/deviation
Avvik ved varemottak (for få, for mange, skadet, erstatning) med tiltak som restordre eller retur, og godkjenningsflyt for avvikene.

*Nøkkelord:* avvik, deviation, avviksbehandling, for få, for mange, skadet vare, defekt, retur, returnere, restordre, erstatningsvare, reklamasjon, godkjenne avvik

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /purchaseOrder/deviation/{id}/:approve` | Approve deviations. Only available for Logistics Basic. | id* |  |
| `GET /purchaseOrder/deviation/{id}` | Get deviation by order line ID. Only available for Logistics Basic. | id* |  |
| `PUT /purchaseOrder/deviation/{id}` | Update deviation. Only available for Logistics Basic. | id* |  |
| `DELETE /purchaseOrder/deviation/{id}` | Delete goods receipt by purchase order ID. Only available for Logistics Basic. | id* |  |
| `PUT /purchaseOrder/deviation/{id}/:deliver` | Send deviations to approval. Only available for Logistics Basic. | id* |  |
| `GET /purchaseOrder/deviation` | Find handled deviations for purchase order. Only available for Logistics Basic. | purchaseOrderId* |  |
| `POST /purchaseOrder/deviation` | Register deviation on goods receipt. Only available for Logistics Basic. |  |  |
| `PUT /purchaseOrder/deviation/list` | Update multiple deviations. Only available for Logistics Basic. |  |  |
| `POST /purchaseOrder/deviation/list` | Register multiple deviations. Only available for Logistics Basic. |  |  |
| `PUT /purchaseOrder/deviation/{id}/:undeliver` | Set status to Not delivered for deviations. Only available for Logistics Basic. | id* |  |

### purchaseOrder/goodsReceipt
Varemottak: registrere mottatte varer på en innkjøpsordre (eller uten ordre), bekrefte mottaket (som fører varene inn på lager) og korrigere/slette mottak.

*Nøkkelord:* varemottak, varemottakelse, mottak, mottatt, goods receipt, motta varer, bekrefte varemottak, mottakskontroll, lagerinngang, inn på lager, restordre, delleveranse, levert, varemottak uten ordre

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /purchaseOrder/goodsReceipt/{id}/:confirm` | Confirm goods receipt. Only available for Logistics Basic. | id*, createRestOrder |  |
| `GET /purchaseOrder/goodsReceipt/{id}` | Get goods receipt by purchase order ID. Only available for Logistics Basic. | id* |  |
| `PUT /purchaseOrder/goodsReceipt/{id}` | Update goods receipt. Only available for Logistics Basic. | id* |  |
| `DELETE /purchaseOrder/goodsReceipt/{id}` | Delete goods receipt by ID. Only available for Logistics Basic. | id* |  |
| `POST /purchaseOrder/goodsReceipt/list` | Register multiple goods receipts without an existing purchase order. Only available for Logistics Basic. |  |  |
| `DELETE /purchaseOrder/goodsReceipt/list` | Delete multiple goods receipts by ID. Only available for Logistics Basic. | ids* |  |
| `GET /purchaseOrder/goodsReceipt` | Get goods receipt. Only available for Logistics Basic. | receivedDateFrom, receivedDateTo, status, withoutPurchase |  |
| `POST /purchaseOrder/goodsReceipt` | Register goods receipt without an existing purchase order. When registration of several goods receipt, use /list for better performance. Only available for Logistics Basic. |  |  |
| `PUT /purchaseOrder/goodsReceipt/{id}/:receiveAndConfirm` | Receive all ordered products and approve goods receipt. Only available for Logistics Basic. | id*, receivedDate*, inventoryId |  |
| `PUT /purchaseOrder/goodsReceipt/{id}/:registerGoodsReceipt` | Register goods receipt. Quantity received on the products is set to the same as quantity ordered. To update the quantity received, use PUT /purchaseOrder/goodsReceiptLine/{id}. Only available for Logistics Basic. | id*, registrationDate*, inventoryId, comment |  |

### purchaseOrder/goodsReceiptLine
Linjer på et varemottak: mottatt antall per produkt, lager og lagerplass – registrere, justere og slette.

*Nøkkelord:* varemottakslinje, mottakslinje, goods receipt line, mottatt antall, antall mottatt, lagerplass, lokasjon, quantity received, rest, delmottak

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /purchaseOrder/goodsReceiptLine/{id}` | Get goods receipt line by purchase order line ID. Only available for Logistics Basic. | id* |  |
| `PUT /purchaseOrder/goodsReceiptLine/{id}` | Update a goods receipt line on a goods receipt. Only available for Logistics Basic. | id* |  |
| `DELETE /purchaseOrder/goodsReceiptLine/{id}` | Delete goods receipt line by ID. Only available for Logistics Basic. | id* |  |
| `PUT /purchaseOrder/goodsReceiptLine/list` | Update goods receipt lines on a goods receipt. Only available for Logistics Basic. |  |  |
| `POST /purchaseOrder/goodsReceiptLine/list` | Register multiple new goods receipts on an existing purchase order. Only available for Logistics Basic. |  |  |
| `DELETE /purchaseOrder/goodsReceiptLine/list` | Delete goods receipt lines by ID. Only available for Logistics Basic. |  |  |
| `GET /purchaseOrder/goodsReceiptLine` | Find goods receipt lines for purchase order. Only available for Logistics Basic. | purchaseOrderId* |  |
| `POST /purchaseOrder/goodsReceiptLine` | Register new goods receipt; new product on an existing purchase order. When registration of several goods receipts, use /list for better performance. Only available for Logistics Basic. |  |  |

### purchaseOrder/purchaseOrderIncomingInvoiceRelation
Kobling mellom innkjøpsordre og inngående faktura (bilag), brukt til å matche ordre, varemottak og leverandørfaktura.

*Nøkkelord:* koble faktura, kobling, relasjon, matching, 3-veis match, treveis matching, innkjøpsordre faktura, leverandørfaktura ordre, bilag, voucher, purchase order invoice, fakturakontroll

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /purchaseOrder/purchaseOrderIncomingInvoiceRelation/{id}` | Find purchase order relation to voucher by ID. Only available for Logistics Basic. | id* |  |
| `PUT /purchaseOrder/purchaseOrderIncomingInvoiceRelation/{id}` | Update purchase order relation to voucher. Only available for Logistics Basic. | id* |  |
| `DELETE /purchaseOrder/purchaseOrderIncomingInvoiceRelation/{id}` | Delete purchase order voucher relation. Only available for Logistics Basic. | id* |  |
| `POST /purchaseOrder/purchaseOrderIncomingInvoiceRelation/list` | Create a new list of relations between purchase order and voucher. Only available for Logistics Basic. |  |  |
| `DELETE /purchaseOrder/purchaseOrderIncomingInvoiceRelation/list` | Delete multiple purchase order voucher relations. Only available for Logistics Basic. | ids* |  |
| `GET /purchaseOrder/purchaseOrderIncomingInvoiceRelation` | Find purchase order relation to voucher with sent data. Only available for Logistics Basic. | id, orderOutId, voucherId |  |
| `POST /purchaseOrder/purchaseOrderIncomingInvoiceRelation` | Create new relation between purchase order and a voucher. Only available for Logistics Basic. |  |  |

### purchaseOrder/orderline
Linjer på en innkjøpsordre: produkt, antall, innkjøpspris og rabatt – opprette, endre og slette enkeltvis eller i liste.

*Nøkkelord:* innkjøpsordrelinje, ordrelinje, orderline, linje, vare, produkt, antall, innkjøpspris, innkjopspris, rabatt, enhetspris, purchase order line

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /purchaseOrder/orderline/{id}` | Find purchase order line by ID. Only available for Logistics Basic. | id* |  |
| `PUT /purchaseOrder/orderline/{id}` | Updates purchase order line. Only available for Logistics Basic. | id* |  |
| `DELETE /purchaseOrder/orderline/{id}` | Delete purchase order line. Only available for Logistics Basic. | id* |  |
| `PUT /purchaseOrder/orderline/list` | Update a list of purchase order lines. Only available for Logistics Basic. |  |  |
| `POST /purchaseOrder/orderline/list` | Create list of new purchase order lines. Only available for Logistics Basic. |  |  |
| `DELETE /purchaseOrder/orderline/list` | Delete purchase order lines by ID. Only available for Logistics Basic. |  |  |
| `POST /purchaseOrder/orderline` | Creates purchase order line. Only available for Logistics Basic. |  |  |

### supplier
Leverandørregisteret: søke opp, opprette, endre, deaktivere og slette leverandører (grunnlaget for leverandørreskontroen).

*Nøkkelord:* leverandør, leverandor, leverandører, leverandorer, leverandørregister, leverandørliste, leverandørnummer, leverandørkort, kreditor, kreditorer, vendor, supplier, org.nr, organisasjonsnummer, orgnr, bankkonto leverandør, kontonummer leverandør, iban, bic, opprette leverandør, ny leverandør, deaktivere leverandør, grossist, leverandørkategori, faktura-epost

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /supplier/{id}` | Get supplier by ID. | id* |  |
| `PUT /supplier/{id}` | Update supplier. | id* |  |
| `DELETE /supplier/{id}` | Delete supplier by ID | id* |  |
| `GET /supplier` | Find suppliers corresponding with sent data. | id, supplierNumber, organizationNumber, email, invoiceEmail, isInactive, accountManagerId, changedSince, isWholesaler, showProducts, category1Id, category2Id, category3Id |  |
| `POST /supplier` | Create supplier. Related supplier addresses may also be created. |  |  |
| `PUT /supplier/list` | Update multiple suppliers. Addresses can also be updated. |  |  |
| `POST /supplier/list` | Create multiple suppliers. Related supplier addresses may also be created. |  |  |

### supplierInvoice
Inngående fakturaer (leverandørfaktura/EHF): søke, hente PDF, attestere/godkjenne, avvise, sende til attestant, endre kontering/dimensjon og registrere betaling.

*Nøkkelord:* leverandørfaktura, leverandorfaktura, inngående faktura, inngaende faktura, innkjøpsfaktura, regning, supplier invoice, incoming invoice, accounts payable, ehf, attestering, attestere, attestant, godkjenne faktura, avvise faktura, kontering, kid, fakturanummer, forfall, forfallsliste, betale leverandør, remittering, kreditnota leverandør, leverandørgjeld, utestående leverandør

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `POST /supplierInvoice/{invoiceId}/:addPayment` | Register payment, paymentType == 0 finds the last paymentType for this vendor.Use of this method requires setup done by Tripletex. | invoiceId*, paymentType*, amount, kidOrReceiverReference, bban, paymentDate, useDefaultPaymentType, partialPayment |  |
| `PUT /supplierInvoice/{invoiceId}/:addRecipient` | Add recipient to supplier invoices. | invoiceId*, employeeId*, comment |  |
| `PUT /supplierInvoice/:addRecipient` | Add recipient. | employeeId*, invoiceIds, comment |  |
| `PUT /supplierInvoice/{invoiceId}/:approve` | Approve supplier invoice. | invoiceId*, comment, overrideApprovalFlow |  |
| `PUT /supplierInvoice/:approve` | Approve supplier invoices. | invoiceIds, comment, overrideApprovalFlow |  |
| `PUT /supplierInvoice/{invoiceId}/:changeDimension` | Change dimension on a supplier invoice. | invoiceId*, debitPostingIds*, dimension*, dimensionId* |  |
| `GET /supplierInvoice/{invoiceId}/pdf` | Get supplierInvoice document by invoice ID. | invoiceId* |  |
| `GET /supplierInvoice/{id}` | Get supplierInvoice by ID. | id* |  |
| `GET /supplierInvoice/forApproval` | Get supplierInvoices for approval | searchText, showAll, employeeId |  |
| `GET /supplierInvoice` | Find supplierInvoices corresponding with sent data. | id, invoiceDateFrom*, invoiceDateTo*, invoiceNumber, kid, voucherId, supplierId |  |
| `PUT /supplierInvoice/voucher/{id}/postings` | Put debit postings. | id*, sendToLedger, voucherDate | BETA |
| `PUT /supplierInvoice/{invoiceId}/:reject` | reject supplier invoice. | invoiceId*, comment* |  |
| `PUT /supplierInvoice/:reject` | reject supplier invoices. | comment*, invoiceIds |  |

<a id="prosjekt"></a>
## Prosjekt, aktiviteter, oppgaver

### activity
Aktiviteter som timer føres på (generelle, generelle prosjektaktiviteter, prosjektspesifikke og oppgaver), inkl. fakturerbar og timesats.

*Nøkkelord:* aktivitet, aktiviteter, timeaktivitet, fakturerbar, ikke fakturerbar, generell aktivitet, prosjektaktivitet, fraværsaktivitet, activity, activities, timeføring, timeregistrering, aktivitetsnummer, chargeable, timekode, arbeidstype, fravaersaktivitet, timeforing, fraværskode, fravaerskode, timepris aktivitet, aktivitetssats

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /activity/{id}` | Find activity by ID. | id* |  |
| `POST /activity/list` | Add multiple activities. |  |  |
| `GET /activity/>forTimeSheet` | Find applicable time sheet activities for an employee on a specific day. | projectId*, employeeId, date, filterExistingHours, query |  |
| `GET /activity` | Find activities corresponding with sent data. | id, name, number, description, isProjectActivity, isGeneral, isChargeable, isTask, isInactive, absence |  |
| `POST /activity` | Add activity. |  |  |

### activity/category
Aktivitetskategorier (brukes blant annet til å gruppere og filtrere oppgaver).

*Nøkkelord:* aktivitetskategori, aktivitetskategorier, kategori aktivitet, activity category, oppgavekategori, gruppering aktiviteter

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /activity/category/{id}` | Find activity category by ID. | id* |  |
| `GET /activity/category/list` | List activity categories. |  |  |

### project
Kjerneressursen for prosjekter: søke, hente, opprette, oppdatere, lukke, slette og importere prosjekter og delprosjekter (timepris, fastpris, tilbud, internprosjekt).

*Nøkkelord:* prosjekt, prosjekter, delprosjekt, underprosjekt, hovedprosjekt, prosjektnummer, prosjektleder, tilbud, internprosjekt, lukke prosjekt, avslutte prosjekt, opprette prosjekt, prosjektimport, project, mainproject, fixed price, prosjektoversikt, oppdrag, prosjektnr, prosjektstyring, byggeprosjekt, kundeoppdrag, prosjekttilbud, fastprisprosjekt, prosjektansvarlig

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/{id}` | Find project by ID. | id* |  |
| `PUT /project/{id}` | Update project. | id* | BETA |
| `DELETE /project/{id}` | Delete project. | id* | BETA |
| `PUT /project/list` | Update multiple projects. |  | BETA |
| `POST /project/list` | Register new projects. Multiple projects for different users can be sent in the same request. |  | BETA |
| `DELETE /project/list` | Delete projects. | ids* | BETA |
| `GET /project` | Find projects corresponding with sent data. | id, name, number, isOffer, projectManagerId, customerAccountManagerId, employeeInProjectId, departmentId, startDateFrom, startDateTo, endDateFrom, endDateTo, isClosed, isFixedPrice, customerId, externalAccountsNumber, includeRecentlyClosed |  |
| `POST /project` | Add new project. |  |  |
| `DELETE /project` | Delete multiple projects. |  | BETA |
| `GET /project/number/{number}` | Find project by number. | number* |  |
| `GET /project/>forTimeSheet` | Find projects applicable for time sheet registration on a specific day. | includeProjectOffers, employeeId, date |  |
| `POST /project/import` | Upload project import file. | fileFormat*, encoding, delimiter, ignoreFirstRow |  |

### project/{id}/actionList
Handlingsliste for ett prosjekt: hva som mangler eller må følges opp, blant annet ansatte som mangler personlig timepris.

*Nøkkelord:* handlingsliste, oppfølging prosjekt, mangler timepris, manglende timesats, action list, todo prosjekt, gjøremål prosjekt, employees with missing hourly rate, sjekkliste prosjekt, varsler prosjekt, oppfolging prosjekt, gjoremal prosjekt, mangler fastpris, mangler budsjett, mangler fakturaplan, mangler internkost, missing hourly rate

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/{id}/actionList` | Get action list items for a project. | id* |  |
| `GET /project/{id}/actionList/employeesWithMissingHourlyRate` | Get employees with missing hourly rate for a project using person-specific hourly rates. | id* |  |

### project/capacityPlan
Kapasitetsplan: budsjetterte mot faktisk førte timer per aktivitet og ansatt for et prosjekt i en periode.

*Nøkkelord:* kapasitetsplan, kapasitetsplanlegging, ressursplan, bemanning, budsjetterte timer, planlagte timer, timebudsjett, belegg, capacity plan, capacityplan, resource planning, utnyttelse, timer mot budsjett

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/capacityPlan/budget` | Get budgeted and worked hours per activity and employee for a project in the specified period. | projectId, periodStart*, periodEnd*, periodType* |  |

### project/resourcePlanBudget
Utgått (deprecated) ressursplan-endepunkt for planlagte timer per periode; bruk project/capacityPlan/budget i stedet.

*Nøkkelord:* ressursplan, ressursplanlegging, resource plan, resourceplanbudget, planlagte timer, deprecated, utgått, bemanningsplan, utgatt

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/resourcePlanBudget` | Get resource plan entries in the specified period. | projectId, periodStart*, periodEnd*, periodType* | DEPRECATED |

### project/category
Prosjektkategorier for å gruppere og rapportere prosjekter (f.eks. service, nybygg, rådgivning).

*Nøkkelord:* prosjektkategori, prosjektkategorier, prosjekttype, kategori, gruppering prosjekter, project category, projectcategory, prosjektgruppe, klassifisering prosjekt

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/category/{id}` | Find project category by ID. | id* |  |
| `PUT /project/category/{id}` | Update project category. | id* |  |
| `GET /project/category` | Find project categories corresponding with sent data. | id, name, number, description |  |
| `POST /project/category` | Add new project category. |  |  |

### project/dynamicControlForm
Dynamiske (egendefinerte) kontrollskjema på prosjekt, med action for å kopiere feltverdier fra sist redigerte skjema.

*Nøkkelord:* kontrollskjema, dynamisk kontrollskjema, egenkontroll, sja, sikker jobbanalyse, sjekkliste, hms, dokumentasjon utført arbeid, control form, dynamic control form, kopier feltverdier, fdv, dokumentasjon utfort arbeid, forhåndsutfylle skjema, forhandsutfylle skjema

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /project/dynamicControlForm/{id}/:copyFieldValuesFromLastEditedForm` | Into each section in the specified form that only has empty or default values, and copyFieldValuesByDefault set as true in the form's template, copy field values from the equivalent section in the most recently edited control form. Signed or completed forms will not be affected. | id* |  |

### project/orderline
Prosjektordrelinjer: varer, materiell, utlegg og budsjettlinjer knyttet til prosjektet som senere viderefaktureres til kunden.

*Nøkkelord:* prosjektordrelinje, ordrelinje prosjekt, viderefakturering, videresalg, utlegg, materiell, varelinjer, påslag, fakturerbar, budsjettlinje, project order line, orderline, tilleggskostnader, merarbeid, vareforbruk prosjekt, paslag, utlegg viderefakturering, varekost prosjekt, prosjektvarer, materialer, materialforbruk

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/orderline/{id}` | Get order line by ID. | id* | BETA |
| `PUT /project/orderline/{id}` | Update project orderline. | id* | BETA |
| `DELETE /project/orderline/{id}` | Delete order line by ID. | id* |  |
| `POST /project/orderline/list` | Create multiple order lines. |  | BETA |
| `GET /project/orderline/orderLineTemplate` | Get order line template from project and product | projectId*, productId* | BETA |
| `GET /project/orderline` | Find all order lines for project. | projectId*, isBudget | BETA |
| `POST /project/orderline` | Create order line. When creating several order lines, use /list for better performance. |  | BETA |
| `GET /project/orderline/query` | Wildcard search. | id, projectId, query, isBudget | BETA |

### project/participant
Prosjektdeltakere: hvilke ansatte som er med på prosjektet og om de har admin-tilgang (styrer også hvem som kan føre timer når prosjektet er kun for deltakere).

*Nøkkelord:* prosjektdeltaker, prosjektdeltakere, deltaker, prosjektmedlem, prosjektteam, team, tilgang prosjekt, adminaccess, participant, legge til ansatt på prosjekt, fjerne ansatt fra prosjekt, prosjektmedarbeider, legge til ansatt pa prosjekt, medarbeider prosjekt, hvem er på prosjektet, hvem er pa prosjektet

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `POST /project/participant/list` | Add new project participant. Multiple project participants can be sent in the same request. |  | BETA |
| `DELETE /project/participant/list` | Delete project participants. | ids* | BETA |
| `GET /project/participant/{id}` | Find project participant by ID. | id* | BETA |
| `PUT /project/participant/{id}` | Update project participant. | id* | BETA |
| `POST /project/participant` | Add new project participant. |  | BETA |

### project/batchPeriod
Samlet (batch) uthenting av budsjettstatus og fakturareserve for mange prosjekter i én spørring.

*Nøkkelord:* fakturareserve, budsjettstatus, alle prosjekter, batch, flere prosjekter, opptjent ikke fakturert, igangværende arbeid, varer i arbeid, wip, work in progress, periodisering, månedsavslutning, invoicing reserve, budget status, ufakturert, igangvaerende arbeid, manedsavslutning, opptjent inntekt, opptjent ikke fakturert inntekt, 1530, årsoppgjør, arsoppgjor, periodiseringsgrunnlag, alle prosjekter samlet

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/batchPeriod/budgetStatusByProjectIds` | Get the budget status for the projects in the specific period. | ids* |  |
| `GET /project/batchPeriod/invoicingReserveByProjectIds` | Get the invoicing reserve for the projects in the specific period. | ids*, dateFrom*, dateTo* |  |

### project/period
Periodetall for ett prosjekt: inntekt/kostnad (prosjektregnskap), månedsstatus, timelisterapport, fakturert, fakturareserve og budsjettstatus.

*Nøkkelord:* prosjektregnskap, prosjektøkonomi, prosjektstatus, dekningsbidrag, db, lønnsomhet, utestående, fakturareserve, fakturerbare timer, ikke godkjente timer, månedsstatus, budsjettstatus, overall status, hourlist report, etterkalkyle, prosjektrapport, prosjektresultat, prosjektokonomi, lonnsomhet, utestaende, manedsstatus, faktureringsgrad, fakturerte timer, prosjektmargin, margin

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/{id}/period/budgetStatus` | Get the budget status for the project period | id* |  |
| `GET /project/{id}/period/hourlistReport` | Find hourlist report by project period. | dateFrom*, dateTo*, id* |  |
| `GET /project/{id}/period/invoiced` | Find invoiced info by project period. | dateFrom*, dateTo*, id* |  |
| `GET /project/{id}/period/invoicingReserve` | Find invoicing reserve by project period. | dateFrom*, dateTo*, id* |  |
| `GET /project/{id}/period/monthlyStatus` | Find overall status by project period. | dateFrom*, dateTo*, id* |  |
| `GET /project/{id}/period/overallStatus` | Find overall status by project period. | dateFrom*, dateTo*, id* |  |

### project/projectActivity
Kobling mellom prosjekt og aktivitet (prosjektaktivitet), med budsjett-timer, budsjettert timepris/honorar og start/slutt.

*Nøkkelord:* prosjektaktivitet, aktivitet på prosjekt, knytte aktivitet, budsjett timer, budsjetthonorar, budsjettert timepris, prosjektspesifikk aktivitet, project activity, projectactivity, fase, arbeidspakke, lukke aktivitet, aktivitet pa prosjekt

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/projectActivity/{id}` | Find project activity by id | id* |  |
| `DELETE /project/projectActivity/{id}` | Delete project activity | id* |  |
| `DELETE /project/projectActivity/list` | Delete project activities | ids* |  |
| `POST /project/projectActivity` | Add project activity. |  |  |

### project/controlForm
Lesetilgang [BETA] til kontrollskjema registrert på et prosjekt (tittel, kommentar, utfylt, signaturkrav og signert).

*Nøkkelord:* kontrollskjema, egenkontroll, sjekkliste, signert, utfylt, ferdigmelding, samsvarserklæring, control form, controlform, hms, dokumentasjon, samsvarserklaering, fg-skjema, sluttkontroll

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/controlForm/{id}` | Get project control form by ID. | id* | BETA |
| `GET /project/controlForm` | Get project control forms by project ID. | projectId* | BETA |

### project/controlFormType
Typer kontrollskjema som finnes i selskapet (kan kreves før fakturering eller timeføring).

*Nøkkelord:* kontrollskjematype, skjematype, kontrollskjema, maler kontrollskjema, control form type, controlformtype, påkrevd skjema, sjekklistetyper, pakrevd skjema

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/controlFormType/{id}` | Get project control form type by ID. | id* | BETA |
| `GET /project/controlFormType` | Get project control form types |  | BETA |

### project/hourlyRates
Timepriser på prosjekt: timeprismodell (forhåndsdefinerte, prosjektspesifikke eller fast timepris) med gyldighet fra dato.

*Nøkkelord:* timepris, timesats, timepriser, honorar, fast timepris, prosjektspesifikke timepriser, forhåndsdefinerte timepriser, timeprismodell, hourly rate, hourlyrates, fixedrate, prisendring, fakturasats, timerate, timepris prosjekt, forhandsdefinerte timepriser, timeprisregulering, indeksregulering, prisregulering, timepris fra dato, timepriser prosjekt

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/hourlyRates/{id}` | Find project hourly rate by ID. | id* |  |
| `PUT /project/hourlyRates/{id}` | Update a project hourly rate. | id* |  |
| `DELETE /project/hourlyRates/{id}` | Delete Project Hourly Rate | id* |  |
| `PUT /project/hourlyRates/list` | Update multiple project hourly rates. |  |  |
| `POST /project/hourlyRates/list` | Create multiple project hourly rates. |  |  |
| `DELETE /project/hourlyRates/list` | Delete project hourly rates. | ids* |  |
| `DELETE /project/hourlyRates/deleteByProjectIds` | Delete project hourly rates by project id. | ids*, date* |  |
| `GET /project/hourlyRates` | Find project hourly rates corresponding with sent data. | id, projectId, type, startDateFrom, startDateTo, showInProjectOrder |  |
| `POST /project/hourlyRates` | Create a project hourly rate. |  |  |
| `PUT /project/hourlyRates/updateOrAddHourRates` | Update or add the same project hourly rate from project overview. | ids* |  |

### project/hourlyRates/projectSpecificRates
Prosjektspesifikke timepriser per ansatt og/eller aktivitet, inkl. kostprosent, under en prosjekttimepris med modellen TYPE_PROJECT_SPECIFIC_HOURLY_RATES.

*Nøkkelord:* personlig timepris, timepris per ansatt, timepris per aktivitet, prosjektspesifikk sats, kostpris time, internkost, hourlycostpercentage, project specific rate, projectspecificrates, timesats ansatt, differensiert timepris

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/hourlyRates/projectSpecificRates/{id}` | Find project specific rate by ID. | id* |  |
| `PUT /project/hourlyRates/projectSpecificRates/{id}` | Update a project specific rate. | id* |  |
| `DELETE /project/hourlyRates/projectSpecificRates/{id}` | Delete project specific rate | id* |  |
| `PUT /project/hourlyRates/projectSpecificRates/list` | Update multiple project specific rates. |  |  |
| `POST /project/hourlyRates/projectSpecificRates/list` | Create multiple new project specific rates. |  |  |
| `DELETE /project/hourlyRates/projectSpecificRates/list` | Delete project specific rates. | ids* |  |
| `GET /project/hourlyRates/projectSpecificRates` | Find project specific rates corresponding with sent data. | id, projectHourlyRateId, employeeId, activityId |  |
| `POST /project/hourlyRates/projectSpecificRates` | Create new project specific rate. |  |  |

### project/subcontract
Underleverandører/underentrepriser på prosjektet med budsjett for honorar, utgifter, inntekt og netto.

*Nøkkelord:* underleverandør, underentreprise, underentreprenør, ue, innleid, subcontract, sub-contract, leverandør prosjekt, budsjett underleverandør, innkjøp prosjekt, entreprise, underleverandor, underentreprenor, leverandor prosjekt, budsjett underleverandor, innkjop prosjekt, innleid arbeid, innleie, ue-kostnad

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/subcontract/{id}` | Find project sub-contract by ID. | id* |  |
| `PUT /project/subcontract/{id}` | Update project sub-contract. | id* |  |
| `DELETE /project/subcontract/{id}` | Delete project sub-contract by ID. | id* |  |
| `GET /project/subcontract` | Find project sub-contracts corresponding with sent data. | projectId* |  |
| `POST /project/subcontract` | Add new project sub-contract. |  |  |
| `GET /project/subcontract/query` | Wildcard search. | id, projectId, query |  |

### project/settings
Selskapsinnstillinger for prosjektmodulen: nummerering, godkjenning av timer, fastpris-beregning, kontrollskjemakrav, kapasitetsplan m.m.

*Nøkkelord:* prosjektinnstillinger, innstillinger prosjekt, oppsett prosjektmodul, godkjenne timer, automatisk prosjektnummer, fastprisberegning, fullføringsgrad, project settings, timeprismodell standard, lukke fakturerte prosjekter, viderefakturering standard, nho, fullforingsgrad, timegodkjenning, godkjenning timer, prosjektnummerering, nkode

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/settings` | Get project settings of logged in company. | useNkode |  |
| `PUT /project/settings` | Update project settings for company |  |  |

### project/task
Utgått (deprecated) liste over oppgaver per prosjekt; bruk GET /task i stedet.

*Nøkkelord:* prosjektoppgave, oppgaver prosjekt, project task, deprecated, utgått, gjøremål, task, utgatt, gjoremal

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/task` | Find all tasks for project. | projectId* | DEPRECATED |

### project/template
Prosjektmaler med standardverdier (kategori, prosjektleder, timepriser, fastpris m.m.) som leses via id og brukes som utgangspunkt ved oppretting av nye prosjekter.

*Nøkkelord:* prosjektmal, mal, template, project template, standardprosjekt, kopiere prosjekt, maloppsett

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /project/template/{id}` | Get project template by ID. | id* |  |

### task
Oppgaver (tasks) på tvers av prosjekter og kunder med status, prioritet, eier, datoer og budsjett-timer – kun lesing via API-et.

*Nøkkelord:* oppgave, oppgaver, gjøremål, task, tasks, oppgaveliste, frister, ansvarlig, eier, status oppgave, prioritet, planlegging, arbeidsordre, todo, oppgaver per kunde, gjoremal, oppgavestatus, oppgaveeier, deadline, frist

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /task` | Find tasks. | query, startDate, endDate, statusIds, ownerId, activityCategoryId, customerId, projectId, departmentId, createdById, participantId |  |

<a id="timer"></a>
## Timeføring og timelister

### timesheet/allocated
Allokerte (planlagte) timer per ansatt, særlig ferie/fri på firmaets interne ferieaktivitet, med godkjenning som kopierer timene inn i timelisten.

*Nøkkelord:* allokerte timer, allokering, planlagte timer, ressursplanlegging, bemanningsplan, ferie, feriesøknad, feriesoknad, ferieplan, godkjenne ferie, avvise ferie, allocated hours, vacation, holiday request, leave request, lederkommentar, manager comment, sommerferie, fellesferie, bedriftsferie, ferietimer, planlagt fravær, planlagt fravaer

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /timesheet/allocated/{id}/:approve` | Only for allocated hours on the company's internal holiday/vacation activity. Mark the allocated hour entry as approved. The hours will be copied to the time sheet if the relevant week/month is not approved, and there are no interfering time clocks that are active. A notification will be sent to the entry's employee if the entry's approval status or comment has changed. | id*, managerComment | PERSONDATA |
| `PUT /timesheet/allocated/:approveList` | Only for allocated hours on the company's internal holiday/vacation activity. Mark the allocated hour entry/entries as approved. The hours will be copied to the time sheet if the relevant weeks/months are not approved, and there are no interfering time clocks that are active. Notifications will be sent to the entries' employees if the entries' approval statuses or comments have changed. If IDs are provided, the other args are ignored. | ids, employeeIds, dateFrom, dateTo, managerComment | PERSONDATA |
| `GET /timesheet/allocated/{id}` | Find allocated hour entry by ID. | id* | PERSONDATA |
| `PUT /timesheet/allocated/{id}` | Update allocated hour entry by ID. Note: Allocated hour entry object fields which are present but not set, or set to 0, will be nulled. Only holiday/vacation hours can receive comments. A notification will be sent to the entry's employee if the entry's comment has changed. | id* | PERSONDATA |
| `DELETE /timesheet/allocated/{id}` | Delete allocated hour entry by ID. | id* | PERSONDATA |
| `PUT /timesheet/allocated/list` | Update allocated hour entry. Multiple objects for different users can be sent in the same request. Note: Allocated hour entry object fields which are present but not set, or set to 0, will be nulled. Only holiday/vacation hours can receive comments. Notifications will be sent to the entries' employees if the entries' comments have changed. |  | PERSONDATA |
| `POST /timesheet/allocated/list` | Add new allocated hour entry. Multiple objects for several users can be sent in the same request. Only holiday/vacation hours can receive comments. Notifications will be sent to the entries' employees if the entries have comments. |  | PERSONDATA |
| `GET /timesheet/allocated` | Find allocated hour entries corresponding with sent data. | ids, employeeIds, projectIds, activityIds, dateFrom, dateTo | PERSONDATA |
| `POST /timesheet/allocated` | Add new allocated hour entry. Only one entry per employee/date/activity/project combination is supported. Only holiday/vacation hours can receive comments. A notification will be sent to the entry's employee if the entry has a comment. |  | PERSONDATA |
| `PUT /timesheet/allocated/{id}/:unapprove` | Only for allocated hours on the company's internal holiday/vacation activity. Mark the allocated hour entry as unapproved. A notification will be sent to the entry's employee if the entry's approval status or comment has changed. | id*, managerComment | PERSONDATA |
| `PUT /timesheet/allocated/:unapproveList` | Only for allocated hours on the company's internal holiday/vacation activity. Mark the allocated hour entry/entries as unapproved. Notifications will be sent to the entries' employees if the entries' approval statuses or comments have changed. If IDs are provided, the other args are ignored. | ids, employeeIds, dateFrom, dateTo, managerComment | PERSONDATA |

### timesheet/companyHoliday
[BETA] Firmaets egne fridager (dato og prosent fri), f.eks. inneklemte dager, julaften og nyttårsaften, som påvirker normaltid i timelisten.

*Nøkkelord:* firmafridag, fridag, fridager, helligdag, helligdager, inneklemt dag, inneklemte dager, julaften, nyttårsaften, nyttarsaften, halv dag, company holiday, røde dager, rode dager, arbeidskalender, firmafridager, påskeaften, paskeaften, redusert normaltid

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /timesheet/companyHoliday/{id}` | Get company holiday by its ID | id* | BETA PERSONDATA |
| `PUT /timesheet/companyHoliday/{id}` | Update a company holiday | id* | BETA PERSONDATA |
| `DELETE /timesheet/companyHoliday/{id}` | Delete a company holiday | id* | BETA PERSONDATA |
| `GET /timesheet/companyHoliday` | Search for company holidays by id or year. | ids, years | BETA PERSONDATA |
| `POST /timesheet/companyHoliday` | Create a company holiday |  | BETA PERSONDATA |

### timesheet/entry
Registrere, søke, endre og slette timeføringer (timer per ansatt, dato, prosjekt og aktivitet), inkludert sum timer og nylig brukte prosjekter/aktiviteter.

*Nøkkelord:* timer, timeføring, timeforing, timeregistrering, timeliste, timelister, føre timer, fore timer, registrere timer, timeseddel, timesheet, prosjekttimer, fakturerbare timer, fakturerbar tid, ufakturerte timer, sum timer, total hours, arbeidstimer, fakturagrunnlag, tidsregistrering, timerapport, timeregnskap, time tracking, timer på prosjekt, timepris

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /timesheet/entry/{id}` | Find timesheet entry by ID. | id* | PERSONDATA |
| `PUT /timesheet/entry/{id}` | Update timesheet entry by ID. Note: Timesheet entry object fields which are present but not set, or set to 0, will be nulled. | id* | PERSONDATA |
| `DELETE /timesheet/entry/{id}` | Delete timesheet entry by ID. | id*, version | PERSONDATA |
| `PUT /timesheet/entry/list` | Update timesheet entry. Multiple objects for different users can be sent in the same request. |  | PERSONDATA |
| `POST /timesheet/entry/list` | Add new timesheet entry. Multiple objects for several users can be sent in the same request. |  | PERSONDATA |
| `GET /timesheet/entry` | Find timesheet entry corresponding with sent data. | id, employeeId, projectId, activityId, dateFrom*, dateTo*, comment | PERSONDATA |
| `POST /timesheet/entry` | Add new timesheet entry. Only one entry per employee/date/activity/project combination is supported. |  | PERSONDATA |
| `GET /timesheet/entry/>recentActivities` | Find recently used timesheet activities. | employeeId, projectId* | PERSONDATA |
| `GET /timesheet/entry/>recentProjects` | Find projects with recent activities (timesheet entry registered). | employeeId | PERSONDATA |
| `GET /timesheet/entry/>totalHours` | Find total hours registered on an employee in a specific period. | employeeId, startDate, endDate | PERSONDATA |

### timesheet/month
Status, levering, godkjenning, oppheving av godkjenning og gjenåpning av månedstimelister per ansatt, med timesum, fleksisaldo og feriesaldo.

*Nøkkelord:* månedstimeliste, maanedstimeliste, godkjenne timeliste, godkjenne måned, godkjenne maned, attestere timer, levere timeliste, fullføre måned, gjenåpne måned, gjenapne maned, oppheve godkjenning, approve month, complete month, reopen month, fleksitid, fleks, fleksisaldo, flexsaldo, feriesaldo, timebank, avspasering, lønnsgrunnlag timer, godkjenning av timer, attestasjon timer, timelister før lønn

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /timesheet/month/:approve` | approve month(s). If id is provided the other args are ignored | id, employeeIds, monthYear, approvedUntilDate | PERSONDATA |
| `PUT /timesheet/month/:complete` | complete month(s). If id is provided the other args are ignored | id, employeeIds, monthYear | PERSONDATA |
| `GET /timesheet/month/{id}` | Find monthly status entry by ID. | id* | PERSONDATA |
| `GET /timesheet/month/byMonthNumber` | Find monthly status for given month. | employeeIds*, monthYear* | DEPRECATED PERSONDATA |
| `GET /timesheet/month/byMonthNumberList` | Find monthly status for given month list. | employeeIds*, monthYearList* | PERSONDATA |
| `PUT /timesheet/month/:reopen` | reopen month(s). If id is provided the other args are ignored | id, employeeIds, monthYear | PERSONDATA |
| `PUT /timesheet/month/:unapprove` | unapprove month(s). If id is provided the other args are ignored | id, employeeIds, monthYear | PERSONDATA |

### timesheet/salaryProjectTypeSpecification
Lønnsarter/tillegg i timelisten knyttet til prosjekt og aktivitet (f.eks. prosjekttillegg eller overtid på prosjekt); feltet wagePayment viser lønnsslippen når tillegget er tatt med i lønn.

*Nøkkelord:* prosjektlønnsart, prosjektlonnsart, prosjekttillegg, lønnsart prosjekt, lonnsart prosjekt, overtid prosjekt, project salary type, salary project type specification, tillegg på prosjekt, tillegg per aktivitet, overtid på prosjekt, overtid pa prosjekt, prosjektlønn, prosjektlonn

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /timesheet/salaryProjectTypeSpecification/{id}` | Get timesheet ProjectSalaryType specification for a specific ID | id* | PERSONDATA |
| `PUT /timesheet/salaryProjectTypeSpecification/{id}` | Update a timesheet ProjectSalaryType specification | id* | PERSONDATA |
| `DELETE /timesheet/salaryProjectTypeSpecification/{id}` | Delete a timesheet SalaryType specification | id* | PERSONDATA |
| `GET /timesheet/salaryProjectTypeSpecification` | Get list of time sheet ProjectSalaryType specifications | dateFrom, dateTo, employeeId, projectId, activityId, includeNotConnectedToActivities | PERSONDATA |
| `POST /timesheet/salaryProjectTypeSpecification` | Create a timesheet ProjectSalaryType specification |  | PERSONDATA |

### timesheet/salaryTypeSpecification
[BETA] Lønnsarter/tillegg registrert i timelisten per ansatt og dato uten prosjektkobling (f.eks. overtid, kveldstillegg, helgetillegg) som grunnlag for lønnskjøringen.

*Nøkkelord:* lønnsart, lonnsart, lønnsarter i timeliste, overtid, overtidstillegg, kveldstillegg, helgetillegg, skifttillegg, utrykning, vakttillegg, salary type, salary type specification, variabel lønn, variabel lonn, variable tillegg, timelønn, timelonn, lønnstillegg, lonnstillegg, tillegg i timeliste, overtid 50, overtid 100

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /timesheet/salaryTypeSpecification/{id}` | Get timesheet SalaryType Specification for a specific ID | id* | BETA PERSONDATA |
| `PUT /timesheet/salaryTypeSpecification/{id}` | Update a timesheet SalaryType Specification | id* | BETA PERSONDATA |
| `DELETE /timesheet/salaryTypeSpecification/{id}` | Delete a timesheet SalaryType Specification | id* | BETA PERSONDATA |
| `GET /timesheet/salaryTypeSpecification` | Get list of timesheet SalaryType Specifications | dateFrom, dateTo, employeeId | BETA PERSONDATA |
| `POST /timesheet/salaryTypeSpecification` | Create a timesheet SalaryType Specification. Only one entry per employee/date/SalaryType |  | BETA PERSONDATA |

### timesheet/settings
[BETA] Firmaets timelisteinnstillinger (stemplingsur på/av, levering av timeliste, fleks- og feriesaldo, krav om kommentar, standard aktivitet).

*Nøkkelord:* timelisteinnstillinger, innstillinger timer, oppsett timeliste, timesheet settings, fleksitid aktivert, krav om kommentar, obligatorisk kommentar, stemplingsur aktivert, standardaktivitet, default activity, konfigurasjon timeliste, feriesaldo aktivert, levering av timeliste påkrevd

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /timesheet/settings` | Get timesheet settings of logged in company. |  | BETA PERSONDATA |

### timesheet/timeClock
Stemplingsur (stoppeklokke) for inn- og utstempling som automatisk oppretter/oppdaterer timeføringer.

*Nøkkelord:* stemplingsur, stempling, stemple inn, stemple ut, innstempling, utstempling, stoppeklokke, time clock, clock in, clock out, start klokke, stopp klokke, kjørende klokke, kjorende klokke, lunsjpause, lunch break, oppmøte, oppmote, stemplingsklokke, punch in, punch out, hvem er stemplet inn

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /timesheet/timeClock/{id}` | Find time clock entry by ID. | id* | PERSONDATA |
| `PUT /timesheet/timeClock/{id}` | Update time clock by ID. | id* | PERSONDATA |
| `GET /timesheet/timeClock` | Find time clock entries corresponding with sent data. | id, employeeId, projectId, activityId, dateFrom, dateTo, hourId, isRunning | PERSONDATA |
| `GET /timesheet/timeClock/present` | Find a user’s present running time clock. | employeeId | PERSONDATA |
| `PUT /timesheet/timeClock/:start` | Start time clock. | employeeId, projectId, activityId*, date, lunchBreakDuration, comment | PERSONDATA |
| `PUT /timesheet/timeClock/{id}/:stop` | Stop time clock. | id*, version, comment | PERSONDATA |

### timesheet/week
Ukestatus for timelister per ISO-uke og ansatt, med levering, godkjenning, oppheving av godkjenning og gjenåpning av uker.

*Nøkkelord:* ukestimeliste, ukentlig timeliste, ukenummer, iso-uke, ukestatus, godkjenne uke, levere uke, fullføre uke, fullfore uke, gjenåpne uke, gjenapne uke, oppheve godkjenning uke, weekyear, approve week, complete week, reopen week, ikke levert timeliste, manglende timer, ukeliste timer, week status, unapprove week

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /timesheet/week/:approve` | Approve week. By ID or (ISO-8601 week and employeeId combination). | id, employeeId, weekYear | PERSONDATA |
| `PUT /timesheet/week/:complete` | Complete week. By ID or (ISO-8601 week and employeeId combination). | id, employeeId, weekYear | PERSONDATA |
| `PUT /timesheet/week/:reopen` | Reopen week. By ID or (ISO-8601 week and employeeId combination). | id, employeeId, weekYear | PERSONDATA |
| `GET /timesheet/week` | Find weekly status By ID, week/year combination, employeeId or an approver | ids, employeeIds, weekYear, approvedBy | PERSONDATA |
| `PUT /timesheet/week/:unapprove` | Unapprove week. By ID or (ISO-8601 week and employeeId combination). | id, employeeId, weekYear | PERSONDATA |

<a id="reise"></a>
## Reiseregninger og utlegg

### travelExpense/accommodationAllowance
Nattillegg/overnattingsgodtgjørelse for ulegitimert overnatting (uten hotellkvittering) på reiseregning.

*Nøkkelord:* nattillegg, natt tillegg, ulegitimert overnatting, overnattingsgodtgjørelse, overnattingsgodtgjorelse, privat overnatting, overnatting uten kvittering, overnatting, brakke, pendlerbolig, accommodation allowance, trekkfritt nattillegg, nattilegg, nattillegg utland, overnatting privat

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/accommodationAllowance/{id}` | Get travel accommodation allowance by ID. | id* | PERSONDATA |
| `PUT /travelExpense/accommodationAllowance/{id}` | Update accommodation allowance. | id* | PERSONDATA |
| `DELETE /travelExpense/accommodationAllowance/{id}` | Delete accommodation allowance. | id* | PERSONDATA |
| `GET /travelExpense/accommodationAllowance` | Find accommodation allowances corresponding with sent data. | travelExpenseId, rateTypeId, rateCategoryId, rateFrom, rateTo, countFrom, countTo, amountFrom, amountTo, location, address | PERSONDATA |
| `POST /travelExpense/accommodationAllowance` | Create accommodation allowance. |  | PERSONDATA |

### travelExpense/cost
Kostnadslinjer (utgifter med kvittering) på en reiseregning eller et utlegg, f.eks. hotell, fly, tog, taxi, parkering, bompenger og representasjon.

*Nøkkelord:* kostnad, kostnader, utgift, utgifter, utleggslinje, hotell, fly, flybillett, tog, taxi, drosje, parkering, bompenger, representasjon, mva på utlegg, reisekostnad, legitimerte utgifter, cost, expense line, viderefakturer kostnad, valuta kvittering, bomring, utleggskvittering

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/cost/{id}` | Get cost by ID. | id* | PERSONDATA |
| `PUT /travelExpense/cost/{id}` | Update cost. | id* | PERSONDATA |
| `DELETE /travelExpense/cost/{id}` | Delete cost. | id* | PERSONDATA |
| `GET /travelExpense/cost` | Find costs corresponding with sent data. | travelExpenseId, vatTypeId, currencyId, rateFrom, rateTo, amountFrom, amountTo | PERSONDATA |
| `POST /travelExpense/cost` | Create cost. |  | PERSONDATA |
| `PUT /travelExpense/cost/list` | Update costs. |  | PERSONDATA |

### travelExpense/costParticipant
Deltakere knyttet til en kostnadslinje, typisk for representasjon og bevertning der det kreves oversikt over hvem som deltok.

*Nøkkelord:* deltaker, deltakere, deltagere, representasjon, bevertning, kundemiddag, forretningsmiddag, middag, gjester, internt arrangement, participant, cost participant, representasjonsutgifter

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `POST /travelExpense/costParticipant/createCostParticipantAdvanced` | Create participant on cost using explicit parameters | displayName, costId*, employeeId* | PERSONDATA |
| `GET /travelExpense/costParticipant/{id}` | Get cost participant by ID. | id* | PERSONDATA |
| `DELETE /travelExpense/costParticipant/{id}` | Delete cost participant. | id* | PERSONDATA |
| `POST /travelExpense/costParticipant/list` | Create participants on cost. |  | PERSONDATA |
| `DELETE /travelExpense/costParticipant/list` | Delete cost participants. |  | PERSONDATA |
| `GET /travelExpense/costParticipant/{costId}/costParticipants` | Get cost's participants by costId. | costId* | PERSONDATA |
| `POST /travelExpense/costParticipant` | Create participant on cost. |  | PERSONDATA |

### travelExpense/drivingStop
Stopp og delstrekninger (rute med koordinater) på en kjøregodtgjørelse, for dokumentasjon av kjøreruten.

*Nøkkelord:* kjørerute, kjorerute, rute, stopp, delstrekning, via, mellomstopp, kjørebok, kjorebok, strekning, driving stop, waypoint, koordinater

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/drivingStop/{id}` | Get driving stop by ID. | id* | PERSONDATA |
| `DELETE /travelExpense/drivingStop/{id}` | Delete mileage allowance stops. | id* | PERSONDATA |
| `POST /travelExpense/drivingStop` | Create mileage allowance driving stop. |  | PERSONDATA |

### travelExpense/mileageAllowance
Kjøregodtgjørelse (kilometergodtgjørelse/bilgodtgjørelse) på reiseregning med km, strekning, sats, firmabil, passasjer-/tilhengertillegg og bompenger.

*Nøkkelord:* kjøregodtgjørelse, kjoregodtgjorelse, kilometergodtgjørelse, kilometergodtgjorelse, km-godtgjørelse, km godtgjørelse, bilgodtgjørelse, bilgodtgjorelse, kjøring, egen bil, privatbil, firmabil, elbil, kjørebok, statens sats, trekkfri bilgodtgjørelse, tilhengertillegg, bompenger, mileage, mileage allowance, km godtgjorelse, km-godtgjorelse, kjørte kilometer

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/mileageAllowance/{id}` | Get mileage allowance by ID. | id* | PERSONDATA |
| `PUT /travelExpense/mileageAllowance/{id}` | Update mileage allowance. | id* | PERSONDATA |
| `DELETE /travelExpense/mileageAllowance/{id}` | Delete mileage allowance. | id* | PERSONDATA |
| `GET /travelExpense/mileageAllowance` | Find mileage allowances corresponding with sent data. | travelExpenseId, rateTypeId, rateCategoryId, kmFrom, kmTo, rateFrom, rateTo, amountFrom, amountTo, departureLocation, destination, dateFrom, dateTo, isCompanyCar | PERSONDATA |
| `POST /travelExpense/mileageAllowance` | Create mileage allowance. |  | PERSONDATA |

### travelExpense/passenger
Passasjerer på en kjøregodtgjørelse, som gir grunnlag for passasjertillegg.

*Nøkkelord:* passasjer, passasjerer, passasjertillegg, samkjøring, samkjoring, medpassasjer, kollega i bilen, passenger, passenger supplement

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/passenger/{id}` | Get passenger by ID. | id* | PERSONDATA |
| `PUT /travelExpense/passenger/{id}` | Update passenger. | id* | PERSONDATA |
| `DELETE /travelExpense/passenger/{id}` | Delete passenger. | id* | PERSONDATA |
| `POST /travelExpense/passenger/list` | Create passengers. |  | PERSONDATA |
| `DELETE /travelExpense/passenger/list` | Delete passengers. |  | PERSONDATA |
| `GET /travelExpense/passenger` | Find passengers corresponding with sent data. | mileageAllowance, name | PERSONDATA |
| `POST /travelExpense/passenger` | Create passenger. |  | PERSONDATA |

### travelExpense/perDiemCompensation
Diett/kostgodtgjørelse på reiseregning, innland og utland, med antall døgn, overnattingstype, land/sone og måltidstrekk.

*Nøkkelord:* diett, diett innland, utenlandsdiett, kostgodtgjørelse, kostgodtgjorelse, per diem, døgndiett, dagsdiett, dagsreise, overnattingsreise, måltidstrekk, maltidstrekk, frokosttrekk, lunsjtrekk, middagstrekk, statens satser, særavtalen, saeravtalen, trekkfri diett, trekkpliktig diett, reisedøgn, dietter, diettgodtgjørelse, diettgodtgjorelse, reisediett

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/perDiemCompensation/{id}` | Get per diem compensation by ID. | id* | PERSONDATA |
| `PUT /travelExpense/perDiemCompensation/{id}` | Update per diem compensation. | id* | PERSONDATA |
| `DELETE /travelExpense/perDiemCompensation/{id}` | Delete per diem compensation. | id* | PERSONDATA |
| `GET /travelExpense/perDiemCompensation` | Find per diem compensations corresponding with sent data. | travelExpenseId, rateTypeId, rateCategoryId, overnightAccommodation, countFrom, countTo, rateFrom, rateTo, amountFrom, amountTo, location, address, isDeductionForBreakfast, isLunchDeduction, isDinnerDeduction | PERSONDATA |
| `POST /travelExpense/perDiemCompensation` | Create per diem compensation. |  | PERSONDATA |

### travelExpense
Hovedobjektet for reiseregninger og ansattutlegg: søke, opprette, endre, slette, levere, godkjenne, kopiere, konvertere, bokføre (lage bilag) og håndtere vedlegg/kvitteringer.

*Nøkkelord:* reiseregning, reiseregninger, ansattutlegg, utlegg, reiserefusjon, levere reiseregning, godkjenne reiseregning, attestere, attestasjon, bokføre reiseregning, bokfore, kvittering, vedlegg, reiseforskudd, viderefakturering, travel expense, employee expense, skyldig reiseregning, ansattreskontro, reiserekning, reisebilag, refusjon ansatt, utleggsrefusjon, reiseutlegg, expense report

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /travelExpense/:approve` | Approve travel expenses. | id, overrideApprovalFlow | PERSONDATA |
| `PUT /travelExpense/{id}/convert` | Convert travel to/from employee expense. | id* | PERSONDATA |
| `PUT /travelExpense/:copy` | Copy travel expense. | id* | PERSONDATA |
| `PUT /travelExpense/:createVouchers` | Create vouchers | id, date* | PERSONDATA |
| `GET /travelExpense/{id}` | Get travel expense by ID. | id* | PERSONDATA |
| `PUT /travelExpense/{id}` | Update travel expense. | id* | PERSONDATA |
| `DELETE /travelExpense/{id}` | Delete travel expense. | id* | PERSONDATA |
| `GET /travelExpense/{travelExpenseId}/attachment` | Get attachment by travel expense ID. | travelExpenseId* | PERSONDATA |
| `POST /travelExpense/{travelExpenseId}/attachment` | Upload attachment to travel expense. | travelExpenseId*, createNewCost | PERSONDATA |
| `DELETE /travelExpense/{travelExpenseId}/attachment` | Delete attachment. | travelExpenseId*, version, sendToInbox, split | PERSONDATA |
| `PUT /travelExpense/:deliver` | Deliver travel expenses. | id | PERSONDATA |
| `GET /travelExpense` | Find travel expenses corresponding with sent data. | employeeId, departmentId, projectId, projectManagerId, departureDateFrom, returnDateTo, state | PERSONDATA |
| `POST /travelExpense` | Create travel expense. |  | PERSONDATA |
| `PUT /travelExpense/:unapprove` | Unapprove travel expenses. | id | PERSONDATA |
| `PUT /travelExpense/:undeliver` | Undeliver travel expenses. | id | PERSONDATA |
| `POST /travelExpense/{travelExpenseId}/attachment/list` | Upload multiple attachments to travel expense. | travelExpenseId*, createNewCost | PERSONDATA |

### travelExpense/rate
Konkrete satser (beløp per døgn/km/natt og måltidstrekksatser) knyttet til en satskategori og sone, gyldige i en periode.

*Nøkkelord:* sats, satser, statens satser, diettsats, kilometersats, km-sats, nattilleggssats, måltidstrekk sats, frokosttrekk, skattefri sats, rate, travel rate, årets satser, arets satser, diettsats 2026, kilometersats elbil, satser utland

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/rate/{id}` | Get travel expense rate by ID. | id* | PERSONDATA |
| `GET /travelExpense/rate` | Find rates corresponding with sent data. | rateCategoryId, type, isValidDayTrip, isValidAccommodation, isValidDomestic, isValidForeignTravel, requiresZone, requiresOvernightAccommodation, dateFrom, dateTo | PERSONDATA |

### travelExpense/rateCategory
Satskategorier for diett, nattillegg og kjøregodtgjørelse, med gyldighetsperiode, krav (sone/overnatting) og kobling til lønnsart og a-meldingskode.

*Nøkkelord:* satskategori, satstype, diettkategori, a-meldingskode, trekkfri, trekkpliktig, dagsreise, rate category, wage code, per diem category, mileage category, a-melding reise, amelding reise, lønnsart reise, lonnsart reise, lønnsart diett, innberetning diett, lønnskode reise

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/rateCategory/{id}` | Get travel expense rate category by ID. | id* | PERSONDATA |
| `GET /travelExpense/rateCategory` | Find rate categories corresponding with sent data. | type, name, travelReportRateCategoryGroupId, ameldingWageCode, wageCodeNumber, isValidDayTrip, isValidAccommodation, isValidDomestic, requiresZone, isRequiresOvernightAccommodation, dateFrom, dateTo | PERSONDATA |

### travelExpense/rateCategoryGroup
Grupper av satskategorier (f.eks. innenlands/utenlands for et gitt år/periode) som brukes for å finne riktige satser for reisen.

*Nøkkelord:* satsgruppe, satsgrupper, innenlands, utenlands, innland, utland, satsår, særavtale, statens reiseregulativ, rate category group, foreign travel

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/rateCategoryGroup/{id}` | Get travel report rate category group by ID. | id* | PERSONDATA |
| `GET /travelExpense/rateCategoryGroup` | Find rate categoriy groups corresponding with sent data. | name, isForeignTravel, dateFrom, dateTo | PERSONDATA |

### travelExpense/costCategory
Kostnadskategorier (utgiftstyper) for kostnadslinjer, med tilknyttet konto og mva-kode som styrer konteringen.

*Nøkkelord:* kostnadskategori, utgiftstype, utgiftskategori, kontering, kostnadskonto, bevertning, cost category, expense category, konto for utlegg, mva-kode utlegg, kostnadstype reise

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/costCategory/{id}` | Get cost category by ID. | id* | PERSONDATA |
| `GET /travelExpense/costCategory` | Find cost category corresponding with sent data. | id, description, isInactive, showOnEmployeeExpenses, query | PERSONDATA |

### travelExpense/paymentType
Betalingstyper for kostnadslinjer (f.eks. betalt privat av ansatt eller med firmakort), med motkonto som styrer om beløpet skal refunderes.

*Nøkkelord:* betalingstype, betalingsmåte, betalingsmate, betalt privat, privat utlegg, firmakort, kredittkort, firmakredittkort, bedriftskort, motkonto, payment type, company card, refusjon til ansatt, skyldig ansatt, betalt med firmakort

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/paymentType/{id}` | Get payment type by ID. | id* | PERSONDATA |
| `GET /travelExpense/paymentType` | Find payment type corresponding with sent data. | id, description, isInactive, showOnEmployeeExpenses, query | PERSONDATA |

### travelExpense/settings
Selskapets oppsett for reiseregninger: bruk av satser, godkjenningskrav, skattefrie satser og om diett/nattillegg/km skal kompenseres.

*Nøkkelord:* reiseregning oppsett, godkjenningsflyt, godkjenning påkrevd, godkjenne egne, skattefrie satser, skattefri, bruk satser, travel settings, innstillinger reiseregning, reiseregningsinnstillinger, travel expense settings, kan godkjenne egne utlegg

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/settings` | Get travel expense settings of logged in company. |  | PERSONDATA |

### travelExpense/zone
Soner/land for utenlandsreiser (landkode, sonenavn, valuta, gyldighet) som styrer hvilke utenlandssatser som gjelder.

*Nøkkelord:* sone, soner, landkode, utenlandsreise, utland, utenlands, utenlandssats, reisemål, reisemal, statens satser utland, zone, country code, land diett, landsats, utenlandssone

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /travelExpense/zone/{id}` | Get travel expense zone by ID. | id* | PERSONDATA |
| `GET /travelExpense/zone` | Find travel expense zones corresponding with sent data. | id, code, isDisabled, query, date | PERSONDATA |

<a id="produkt"></a>
## Produkter, lager, logistikk

### inventory
Lagre (varelager/warehouse): søke opp, opprette, endre, deaktivere og slette lagre, inkludert hovedlager.

*Nøkkelord:* lager, lagre, varelager, hovedlager, filiallager, nytt lager, lagersted, lageroversikt, warehouse, inventory, logistikk, lagerstyring, lageradresse, deaktivere lager, lagerlokale, sentrallager, inventory list

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /inventory/{id}` | Get inventory by ID. | id* |  |
| `PUT /inventory/{id}` | Update inventory. | id* |  |
| `DELETE /inventory/{id}` | Delete inventory. | id* |  |
| `GET /inventory` | Find inventory corresponding with sent data. | id, name, isMainInventory, isInactive, query |  |
| `POST /inventory` | Create new inventory. |  |  |

### inventory/inventories
Lagerbeholdning per produkt og lager for en periode: inngående beholdning, endring i perioden og utgående beholdning.

*Nøkkelord:* lagerbeholdning, beholdning, lagerstatus, lagersaldo, varebeholdning, inngående beholdning, inngaende beholdning, utgående beholdning, utgaende beholdning, lagerbevegelse, lagerendring, varelagerendring, lagerverdi, varelagerverdi, antall på lager, lagerliste, beholdningsliste, opening stock, closing stock, stock level, beholdningsendring, varelager 31.12, lagerbeholdning per dato, stock movement

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /inventory/inventories` | Find inventories corresponding with sent data. | dateFrom*, dateTo*, productId, inventoryId, onlyProductWithChangedStatus |  |

### inventory/location
Lagerplasser (hylle, reol, bin) innenfor et lager – krever Logistics Basic og at lagerplasser er slått på.

*Nøkkelord:* lagerplass, lagerplasser, lagerlokasjon, lokasjon, hylle, hylleplass, reol, bin, plassering, lagerplassering, warehouse location, inventory location, reolplass

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /inventory/location/{id}` | Get inventory location by ID. Only available for Logistics Basic. | id* |  |
| `PUT /inventory/location/{id}` | Update inventory location. Only available for Logistics Basic. | id* |  |
| `DELETE /inventory/location/{id}` | Delete inventory location. Only available for Logistics Basic. | id* |  |
| `PUT /inventory/location/list` | Update multiple inventory locations. Only available for Logistics Basic. |  |  |
| `POST /inventory/location/list` | Add multiple inventory locations. Only available for Logistics Basic. |  |  |
| `DELETE /inventory/location/list` | Delete inventory location. Only available for Logistics Basic. | ids* |  |
| `GET /inventory/location` | Find inventory locations by inventory ID. Only available for Logistics Basic. | warehouseId, isInactive, name |  |
| `POST /inventory/location` | Create new inventory location. Only available for Logistics Basic. |  |  |

### inventory/stocktaking
Varetellinger (lageropptelling/inventering) per lager: opprette, søke opp, fullføre og slette, med lagerverdi og avvikssum.

*Nøkkelord:* varetelling, vareopptelling, opptelling, telling, lagertelling, inventering, telleliste, årstelling, arstelling, varetelling 31.12, lagerkontroll, svinn, årsoppgjør, arsoppgjor, stocktaking, stock count, inventory count, lagerverdi, telleavvik, telledifferanse, lageropptelling

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /inventory/stocktaking/{id}` | Get stocktaking by ID. | id* |  |
| `PUT /inventory/stocktaking/{id}` | Update stocktaking. | id* |  |
| `DELETE /inventory/stocktaking/{id}` | Delete stocktaking. | id* |  |
| `GET /inventory/stocktaking` | Find stocktaking corresponding with sent data. | id, isCompleted, inventoryId |  |
| `POST /inventory/stocktaking` | Create new stocktaking. | typeOfStocktaking |  |

### inventory/stocktaking/productline
Linjene i en varetelling (ett produkt per linje) med opptalt antall, kostpris, kommentar og lagerplass.

*Nøkkelord:* tellelinje, varetellingslinje, tellingslinje, opptalt antall, telt antall, antall, ikke opptalt, opptalte varer, kostpris, enhetskost, flytte lagerplass, productline, product line, count, stocktaking line

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /inventory/stocktaking/productline/{id}/:changeLocation` | Change location on order line. | id*, warehouseLocationId* | BETA |
| `GET /inventory/stocktaking/productline/{id}` | Get order line by ID. | id* |  |
| `PUT /inventory/stocktaking/productline/{id}` | Update order line. | id* |  |
| `DELETE /inventory/stocktaking/productline/{id}` | Delete order line. | id* |  |
| `GET /inventory/stocktaking/productline` | Find all order lines by stocktaking ID. | stocktakingId*, query, productGroupIds, locationIds, productLineStatus |  |
| `POST /inventory/stocktaking/productline` | Create order line. When creating several order lines, use /list for better performance. |  |  |

### product/external
[BETA] Oppslag i grossistenes produktkataloger (EFO/NELFO) på elnummer, NRF-nummer eller navn, typisk for el- og VVS-bransjen.

*Nøkkelord:* grossist, grossistkatalog, varekatalog, efo, nelfo, elnummer, el-nummer, nrf, nrf-nummer, vvs, elektro, elektriker, rørlegger, rorlegger, ahlsell, onninen, solar, sonepar, brødrene dahl, brodrene dahl, elektroskandia, external product, eksternt produkt, prisfil

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /product/external/{id}` | Get external product by ID. | id* | BETA |
| `GET /product/external` | Find external products corresponding with sent data. The sorting-field is not in use on this endpoint. | name, wholesaler, organizationNumber, elNumber, nrfNumber, isInactive | BETA |

### product
Produktregisteret (varer og tjenester): søke, opprette, endre, deaktivere og slette produkter samt produktbilder, med salgspris, kostpris, MVA-kode, inntektskonto og enhet.

*Nøkkelord:* produkt, produkter, vare, varer, varenummer, artikkel, artikkelnummer, tjeneste, vareregister, produktregister, varekartotek, product, sku, ean, strekkode, salgspris, utpris, kostpris, innpris, innkjøpspris, innkjopspris, mva-kode, lagervare, vareliste, prisliste

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /product/{id}` | Get product by ID. | id* |  |
| `PUT /product/{id}` | Update product. | id* |  |
| `DELETE /product/{id}` | Delete product. | id* |  |
| `POST /product/{id}/image` | Upload image to product. Existing image on product will be replaced if exists | id* |  |
| `DELETE /product/{id}/image` | Delete image. | id* |  |
| `PUT /product/list` | Update a list of products. |  |  |
| `POST /product/list` | Add multiple products. |  |  |
| `GET /product` | Find products corresponding with sent data. | number, ids, productNumber, name, ean, isInactive, isStockItem, isSupplierProduct, supplierId, currencyId, vatTypeId, productUnitId, departmentId, accountId, costExcludingVatCurrencyFrom, costExcludingVatCurrencyTo, priceExcludingVatCurrencyFrom, priceExcludingVatCurrencyTo, priceIncludingVatCurrencyFrom, priceIncludingVatCurrencyTo |  |
| `POST /product` | Create new product. |  |  |

### product/supplierProduct
Leverandørprodukter: leverandørens varenummer og innkjøpspris knyttet til et eget produkt som videreselges.

*Nøkkelord:* leverandørprodukt, leverandorprodukt, leverandørvare, leverandørens varenummer, bestillingsnummer, innkjøpspris, innkjopspris, innpris, hovedleverandør, videresalg, resale, supplier product, leverandørpris, leverandørs varenummer, innkjøpsvare, efo-vare

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /product/supplierProduct/{id}` | Get supplierProduct by ID. | id* |  |
| `PUT /product/supplierProduct/{id}` | Update supplierProduct. | id* |  |
| `DELETE /product/supplierProduct/{id}` | Delete supplierProduct. | id* |  |
| `POST /product/supplierProduct/getSupplierProductsByIds` | Find the products by ids. Method was added as a POST because GET request header has a maximum size that we can exceed with customers that a lot of products. |  |  |
| `GET /product/supplierProduct` | Find products corresponding with sent data. | productId, resaleIds, vendorId, query, isInactive, productGroupId, targetCurrencyId |  |
| `POST /product/supplierProduct` | Create new supplierProduct. |  |  |
| `PUT /product/supplierProduct/list` | Update a list of supplierProduct. |  |  |
| `POST /product/supplierProduct/list` | Create list of new supplierProduct. |  |  |

### product/discountGroup
Rabattgrupper (typisk grossistens/EFO-NELFOs rabattgrupper) som produkter kan tilhøre – kun lesbare via API; kunderabatt på ordre/faktura hører til salg-gruppen.

*Nøkkelord:* rabattgruppe, rabattgrupper, rabattkode, grossistrabatt, nettopris, discount group, efo rabattgruppe, nelfo rabattgruppe, grossistavtale, rabattgruppenummer

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /product/discountGroup/{id}` | Get discount group by ID. | id* |  |
| `GET /product/discountGroup` | Find discount groups corresponding with sent data. | id, name, number |  |

### product/inventoryLocation
Kobling mellom produkt og lager/lagerplass (hvor varen står), med hovedplassering og beholdning per plass – krever Logistics Basic.

*Nøkkelord:* produktplassering, varelokasjon, produkt lagerplass, hovedplassering, hovedlagerplass, hvor ligger varen, beholdning per lagerplass, plassering, hylleplass, main location, product inventory location

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /product/inventoryLocation/{id}` | Get inventory location by ID. Only available for Logistics Basic. | id* |  |
| `PUT /product/inventoryLocation/{id}` | Update product inventory location. Only available for Logistics Basic. | id* |  |
| `DELETE /product/inventoryLocation/{id}` | Delete product inventory location. Only available for Logistics Basic. | id* |  |
| `GET /product/inventoryLocation` | Find inventory locations by product ID. Only available for Logistics Basic. | productId, inventoryId, isMainLocation |  |
| `POST /product/inventoryLocation` | Create new product inventory location. Only available for Logistics Basic. |  |  |
| `PUT /product/inventoryLocation/list` | Update multiple product inventory locations. Only available for Logistics Basic. |  |  |
| `POST /product/inventoryLocation/list` | Add multiple product inventory locations. Only available for Logistics Basic. |  |  |

### product/logisticsSettings
Firmaets logistikkinnstillinger: lagerplasser av/på, foreslått varenummer, standardkommentar på innkjøpsordre og Bring-modul.

*Nøkkelord:* logistikkinnstillinger, lagerinnstillinger, logistics settings, lagerplasser på, foreslått varenummer, foreslatt varenummer, varenummerserie, innkjøpsordre kommentar, bring, rackbeat, aktivere lagerplasser, neste varenummer, bring-modul, logistikkoppsett

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /product/logisticsSettings` | Get logistics settings for the logged in company. |  |  |
| `PUT /product/logisticsSettings` | Update logistics settings for the logged in company. |  |  |

### product/group
Produktgrupper/varegrupper i et hierarki med overordnet gruppe – krever Logistics Basic.

*Nøkkelord:* produktgruppe, produktgrupper, varegruppe, varegrupper, varekategori, produktkategori, kategori, hovedgruppe, undergruppe, sortiment, product group

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /product/group/{id}` | Find product group by ID. Only available for Logistics Basic. | id* |  |
| `PUT /product/group/{id}` | Update product group. Only available for Logistics Basic. | id* |  |
| `DELETE /product/group/{id}` | Delete product group. Only available for Logistics Basic. | id* |  |
| `PUT /product/group/list` | Update a list of product groups. Only available for Logistics Basic. |  |  |
| `POST /product/group/list` | Add multiple products groups. Only available for Logistics Basic. |  |  |
| `DELETE /product/group/list` | Delete multiple product groups. Only available for Logistics Basic. | ids* |  |
| `GET /product/group` | Find product group with sent data. Only available for Logistics Basic. | id, name, query |  |
| `POST /product/group` | Create new product group. Only available for Logistics Basic. |  |  |
| `GET /product/group/query` | Wildcard search. Only available for Logistics Basic. | query, name |  |

### product/groupRelation
Koblinger mellom produkter og produktgrupper (et produkt kan ligge i flere grupper) – krever Logistics Basic.

*Nøkkelord:* gruppetilknytning, koble produkt til gruppe, varegruppe kobling, produkt i varegruppe, gruppemedlemskap, product group relation, flytte produkt til varegruppe, produkter i varegruppe, varegruppetilknytning

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /product/groupRelation/{id}` | Find product group relation by ID. Only available for Logistics Basic. | id* |  |
| `DELETE /product/groupRelation/{id}` | Delete product group relation. Only available for Logistics Basic. | id* |  |
| `POST /product/groupRelation/list` | Add multiple products group relations. Only available for Logistics Basic. |  |  |
| `DELETE /product/groupRelation/list` | Delete multiple product group relations. Only available for Logistics Basic. |  |  |
| `GET /product/groupRelation` | Find product group relation with sent data. Only available for Logistics Basic. | id, productId, productGroupId |  |
| `POST /product/groupRelation` | Create new product group relation. Only available for Logistics Basic. |  |  |

### product/productPrice
Prishistorikk for et produkt (innkjøpspris, kostpris og salgspris eks./inkl. MVA per periode) – krever Logistics Basic.

*Nøkkelord:* prishistorikk, prisendring, prisendringer, historiske priser, siste pris, salgspris, innkjøpspris, innkjopspris, kostpris, prisutvikling, product price, price history

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /product/productPrice` | Find prices for a product. Only available for Logistics Basic. | productId*, fromDate, toDate, showOnlyLastPrice |  |

### product/unit
Firmaets egne produktenheter (stk, timer, kg, m osv.) med kortnavn og standard enhetskode.

*Nøkkelord:* enhet, enheter, måleenhet, maleenhet, salgsenhet, stk, stykk, kg, meter, liter, unit, product unit, enhetskode, common code, enhet time, timeenhet, pakke, eske

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /product/unit/{id}` | Get product unit by ID. | id* |  |
| `PUT /product/unit/{id}` | Update product unit. | id* |  |
| `DELETE /product/unit/{id}` | Delete product unit by ID. | id* |  |
| `GET /product/unit` | Find product units corresponding with sent data. | id, name, nameShort, commonCode |  |
| `POST /product/unit` | Create new product unit. |  |  |
| `PUT /product/unit/list` | Update list of product units. |  |  |
| `POST /product/unit/list` | Create multiple product units. |  |  |
| `GET /product/unit/query` | Wildcard search. | query |  |

### product/unit/master
Tripletex sin felles hovedliste over standardenheter med UN/ECE- og PEPPOL-koder, brukt bl.a. i EHF.

*Nøkkelord:* standardenhet, enhetsliste, peppol, ehf, e-faktura, efaktura, unece, rec 20, common code, enhetskode, peppol-symbol, unit master, masterenhet

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /product/unit/master/{id}` | Get product unit master by ID. | id* |  |
| `GET /product/unit/master` | Find product units master corresponding with sent data. | id, name, nameShort, commonCode, peppolName, peppolSymbol, isInactive |  |

### pickupPoint
[DEPRECATED] Hentesteder/utleveringssteder hos grossist eller transportør, brukt på innkjøpsordre.

*Nøkkelord:* hentested, hentepunkt, utleveringssted, avhenting, henting, pickup point, grossist, hentested grossist, deprecated

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /pickupPoint/{id}` | Find pickup point by ID. | id* | DEPRECATED |
| `GET /pickupPoint` | Search pickup points. | supplierId, transportTypeId, code, name | DEPRECATED |

### transportType
[BETA] Transporttyper/leveringsmåter (f.eks. henting eller levering) per grossist, brukt på innkjøpsordre.

*Nøkkelord:* transporttype, leveringsmåte, leveringsmate, fraktmåte, fraktmate, frakt, forsendelse, henting, transport type, grossist, hente selv, grossistlevering

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /transportType/{id}` | Find transport type by ID. | id* | BETA |
| `GET /transportType` | Search transport type by supplier. | supplier* | BETA |

<a id="arsoppgjor"></a>
## Anleggsmidler, årsoppgjør, SAF-T, signering (Penneo)

### asset
Anleggsregisteret: opprette, endre, duplisere, slette, importere og avstemme anleggsmidler (driftsmidler) med kostpris, levetid, avskrivningsmetode, salgsdato og tilknyttede posteringer.

*Nøkkelord:* anleggsmiddel, anleggsmidler, anleggsregister, driftsmiddel, driftsmidler, avskrivning, avskrivninger, avskriving, saldoavskrivning, lineær avskrivning, avskrivningsplan, levetid, kostpris, anskaffelseskost, bokført verdi, restverdi, avgang, realisasjon, salg av driftsmiddel, aktivering, saldogruppe, fixed asset, asset register, depreciation, anleggsmiddler

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /asset/balanceAccountsSum` | Get balanceAccountsSum. |  |  |
| `GET /asset/{id}` | Get asset by ID. | id* |  |
| `PUT /asset/{id}` | Update asset. | id* |  |
| `DELETE /asset/{id}` | Delete asset. | id* |  |
| `POST /asset/list` | Create several assets. |  |  |
| `DELETE /asset/deleteImport` | Delete most recent assets import. |  | BETA |
| `DELETE /asset/deleteStartingBalance` | Delete the asset starting balance. |  | BETA |
| `GET /asset/assetsExist` | Get if AssetOverview details is empty. |  |  |
| `GET /asset/{id}/postings` | Get postings associated with asset | id*, dateFrom, dateToExclusive |  |
| `GET /asset` | Find assets corresponding with sent data. | id, name, description |  |
| `POST /asset` | Create one asset. |  |  |
| `POST /asset/duplicate/{id}` | Create copy of one asset | id* |  |
| `POST /asset/upload` | Upload Excel file with Assets in the standard Tripletex defined format. | isPreview*, startDate* | BETA |

### penneo
Digital signering av årsregnskap/årsberetning via Penneo i årsoppgjørsmodulen: saksmapper (case files), PDF-dokumenter, signaturlinjer, signatarer, kopimottakere, status og synkronisering.

*Nøkkelord:* penneo, signering, signere årsregnskap, signert årsregnskap, e-signering, elektronisk signatur, bankid, signatar, signaturlinje, styret signerer, styreleder, daglig leder, saksmappe, case file, kopimottaker, signeringslenke, purre signatur, signeringsstatus, årsregnskap, arsregnskap, aarsregnskap, årsberetning, generalforsamlingsprotokoll, signing, signer

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `POST /yearEnd/penneo/casefiles/{caseFileId}/activate` | Fully activate a case file for signing (links signers, configures emails, and activates) | caseFileId*, year |  |
| `GET /yearEnd/penneo/session` | Authenticate and get case files from Penneo for a specific year | year |  |
| `POST /yearEnd/penneo/signature-lines` | Create signature line, link signer, and configure email in one operation |  |  |
| `GET /yearEnd/penneo/casefiles` | Get case files from Penneo for a specific year | year |  |
| `POST /yearEnd/penneo/casefiles` | Create a new case file in Penneo |  |  |
| `POST /yearEnd/penneo/documents` | Add a document to an existing case file |  |  |
| `DELETE /yearEnd/penneo/casefiles/{caseFileId}` | Delete a case file from Penneo | caseFileId* |  |
| `PUT /yearEnd/penneo/documents/{documentId}` | Update an existing document in a case file | documentId* |  |
| `DELETE /yearEnd/penneo/documents/{documentId}` | Delete a document from a case file | documentId* |  |
| `DELETE /yearEnd/penneo/recipients/{id}` | Delete a recipient from a case file | id*, caseFileId* |  |
| `DELETE /yearEnd/penneo/casefiles/{caseFileId}/signers/{signerId}` | Delete a signer from a case file | caseFileId*, signerId* |  |
| `GET /yearEnd/penneo/documents/{documentId}/download` | Download a document from Penneo | documentId* |  |
| `GET /yearEnd/penneo/recipients` | Get all recipients for a case file | caseFileId* |  |
| `POST /yearEnd/penneo/recipients` | Add a copy recipient to a case file |  |  |
| `GET /yearEnd/penneo/signingStatus` | Get annual accounts signing status for a year based on the backend DB record | year* |  |
| `POST /yearEnd/penneo/casefiles/{caseFileId}/signers/{signerId}/reactivate` | Reactivate a signer in a case file | caseFileId*, signerId* |  |
| `POST /yearEnd/penneo/casefiles/{caseFileId}/signers/{signerId}/resend` | Resend a sign link to a specific signer | caseFileId*, signerId* |  |
| `POST /yearEnd/penneo/sync` | Synchronize database with current Penneo casefile state |  |  |

### saft
SAF-T Financial (BETA): eksport av regnskapsdata som zip/XML (Skatteetaten, revisor, systembytte) og import av SAF-T fra et annet regnskapssystem, med importstatus og reversering av siste import.

*Nøkkelord:* saf-t, saft, saf t, saf-t financial, saf-t 1.30, saf-t eksport, saf-t import, saft export, saft import, standard audit file, saft skatteetaten, saft til revisor, bokettersyn, kontrollfil, regnskapsfil, systembytte, konvertering, migrering, overføre regnskap, importere regnskap fra annet system, inngående balanse fra saft, kontoplan mapping, grupperingskode, reversere import, saft status

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /saft/exportSAFT` | Create SAF-T export for the Tripletex account. | year*, version | BETA |
| `GET /saft/status` | Get the status of the latest SAF-T import for the company. |  | BETA |
| `POST /saft/importSAFT` | Import SAF-T. Send XML file as multipart form. Supports SAF-T 1.2, 1.3 and 1.4, auto-detected from the file. |  | BETA |
| `POST /saft/reverse` | Reverse the latest SAF-T import for the company. |  | BETA |

### yearEnd/enumType
Oppslagsverdier for årsoppgjørsmodulen: næringstyper (business activity types) som brukes for å skille næringer/skattekategorier, bl.a. på avdelinger.

*Nøkkelord:* årsoppgjør, arsoppgjor, aarsoppgjoer, næringstype, naeringstype, næring, virksomhetstype, business activity type, næringsspesifikasjon, skattekategori, oppslagsverdier, jordbruk, primærnæring, naeringsspesifikasjon, naering, business activity, annen næring, skogbruk, fiske

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /yearEnd/enumType/businessActivityTypes` | Get business activity types | id, query |  |

<a id="system"></a>
## Selskap, innstillinger, autentisering, webhooks, lisenser, oppslag

### accountantDashboard/news
Offentlige nyhetsartikler og nyhetstagger fra Tripletex sitt regnskapsførerdashbord (produktnyheter og driftsmeldinger).

*Nøkkelord:* nyheter, news, regnskapsførerdashbord, regnskapsforerdashbord, accountant dashboard, driftsmelding, produktnyheter, tripletex-nytt, artikler, nyhetstagger, kunngjøringer, kunngjoringer, hva er nytt, nyhetsartikler, release notes, oppdateringer i tripletex

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /accountantDashboard/news` | Get public news articles |  |  |
| `GET /accountantDashboard/news/tags` | Get all existing news tags |  |  |

### token/consumer
Oppslag av consumer token (integrasjonens/API-konsumentens nøkkel) ut fra token-strengen.

*Nøkkelord:* consumer token, consumertoken, api-konsument, api konsument, integrasjonsnøkkel, integrasjonsnokkel, api consumer, applikasjonsnøkkel, token, autentisering, api-nøkkel, api nokkel, consumer key, integrasjonspartner, hvilken integrasjon, bytoken

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /token/consumer/byToken` | Get consumer token by token string. | token* |  |

### token/employee
Opprettelse av employee token (brukerens API-nøkkel knyttet til en ansatt og en consumer) – kun for utvalgte consumere.

*Nøkkelord:* employee token, employeetoken, ansattoken, brukernøkkel, brukernokkel, api-tilgang, api tilgang, api-nøkkel, api nokkel, opprette token, integrasjon, tilgangsnøkkel, tilgangsnokkel, utløpsdato token, api-bruker, integrasjonsbruker, employee key, brukertoken

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /token/employee/:create` | Create an employee token. Only selected consumers are allowed | tokenName*, consumerName*, employeeId*, companyOwned*, expirationDate* |  |

### .well-known
Offentlig JSON Web Key Set (JWKS) for å verifisere signaturen på Tripletex-JWT-er (f.eks. refresh-/session-tokens).

*Nøkkelord:* jwks, jwks.json, well-known, json web key, jwt, signatur, verifisere token, public key, offentlig nøkkel, offentlig nokkel, nøkkelsett, tokenverifisering

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /.well-known/jwks.json` | Get JSON Web Key Set for JWT token verification. |  |  |

### token/session
Innlogging mot API-et: lage/slette session token (fra consumer+employee token eller refresh token) og finne ut hvem som er innlogget (whoAmI).

*Nøkkelord:* session token, sessiontoken, innlogging, logge inn, autentisering, authentication, refresh token, tlxr, jwt, whoami, hvem er jeg, innlogget bruker, logge ut, utlogging, basic auth, companyid, proxy, 401, api-innlogging, createfromrefreshtoken, ttlseconds, sesjonstoken, token utløpt, token utlopt, actualemployeeid

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /token/session/:create` | Create session token. | consumerToken*, employeeToken*, expirationDate* | DEPRECATED |
| `POST /token/session/:create` | Create session token. |  |  |
| `POST /token/session/:createFromRefreshToken` | Create session token from refresh token. |  |  |
| `DELETE /token/session/{token}` | Delete session token. | token* |  |
| `GET /token/session/>whoAmI` | Find information about the current user. |  |  |

### company
Selskapets/klientens firmaopplysninger (navn, org.nr., selskapsform, adresse, valuta) og listen over regnskapsklienter man har innloggingstilgang til.

*Nøkkelord:* selskap, firma, klient, klienter, klientliste, regnskapsklient, firmaopplysninger, organisasjonsnummer, org.nr, orgnr, selskapsform, organisasjonsform, enkeltpersonforetak, withloginaccess, regnskapsfører, regnskapsforer, revisor, underenhet, klientoversikt, regnskapsbyrå, portefølje, proxy login, klient-id, firmanavn, foretaksform

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /company/>withLoginAccess` | Returns client customers (with accountant/auditor relation) where the current user has login access (proxy login). |  |  |
| `GET /company/{id}` | Find company by ID. | id* |  |
| `GET /company/divisions` | Find divisions. |  | DEPRECATED |
| `PUT /company` | Update company information. |  |  |

### company/salesmodules
Aktive salgsmoduler (funksjonalitet/abonnementsmoduler som lønn, prosjekt, anleggsregister, årsoppgjør, OCR) og aktivering av nye moduler (BETA).

*Nøkkelord:* moduler, salgsmoduler, sales modules, aktivere modul, lønnsmodul, lonnsmodul, prosjektmodul, anleggsregister, årsoppgjørsmodul, timeføring, timeforing, ocr, api_v2, logistikk, bilagspakke, lisens, abonnement, autoplus, bilagstolkning, elektroniske bilag, wage, hvorfor 403, manglende modul, arsoppgjorsmodul

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /company/salesmodules` | Get active sales modules. |  | BETA |
| `POST /company/salesmodules` | Add (activate) a new sales module. |  | BETA |

### country
Oppslag i landregisteret (navn og ISO-koder) for å sette land på adresser, kunder, leverandører og ansatte.

*Nøkkelord:* land, landkode, country, iso, iso-kode, alpha2, alpha3, norge, utland, utenlandsk, adresse land, country id, nasjonalitet, ztl, landliste, landskode, sverige, danmark, isoalpha2code, utenlandsk kunde, utenlandsk leverandør, utenlandsk leverandor

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /country/{id}` | Get country by ID. | id* |  |
| `GET /country` | Find countries corresponding with sent data. | id, code, isDisabled, supportedInZtl |  |

### event
Oversikt over tilgjengelige webhook-hendelser (event-nøkler) og eksempel-payload for hver hendelsestype (BETA).

*Nøkkelord:* webhook, webhooks, hendelse, hendelser, event, events, event-nøkler, event nokler, varsling, notifikasjon, callback, payload, eksempel, integrasjon, sanntid, webhook-hendelser, event types, subject.verb, eksempel-payload, hendelsestyper

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /event/{eventType}` | Get example webhook payload | eventType* | BETA |
| `GET /event` | Get all (WebHook) event keys. |  | BETA |

### event/subscription
Opprette, liste, endre og slette webhook-abonnementer som sender varsler til en HTTPS-URL når data endres i Tripletex (BETA).

*Nøkkelord:* webhook, webhook-abonnement, abonnement, subscription, event subscription, hendelsesabonnement, callback-url, targeturl, hmac, signatur, varsling, notifikasjon, deaktivert webhook, disabled, reaktivere webhook, slette webhook, integrasjon, sanntidsvarsel, webhooks, x-request-signature, authheadername, callback url, webhook status, disabled_too_many_errors

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /event/subscription/{id}` | Get subscription by ID. | id* | BETA |
| `PUT /event/subscription/{id}` | Change a current subscription, based on id. | id* | BETA |
| `DELETE /event/subscription/{id}` | Delete the given subscription. | id* | BETA |
| `PUT /event/subscription/list` | Update multiple subscription. |  | BETA |
| `POST /event/subscription/list` | Create multiple subscriptions for current EmployeeToken. |  | BETA |
| `DELETE /event/subscription/list` | Delete multiple subscriptions. | ids* | BETA |
| `GET /event/subscription` | Find all ongoing subscriptions. |  | BETA |
| `POST /event/subscription` | Create a new subscription for current EmployeeToken. |  | BETA |

### license
Status for og signering av Visma Developer Terms (utviklervilkår) på vegne av selskapet.

*Nøkkelord:* lisens, license, developer terms, utviklervilkår, utviklervilkar, visma developer terms, vilkår, vilkar, signere vilkår, avtale, godta vilkår, api-vilkår, developer terms signert, juridisk aksept, visma

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /license/developerTerms` | Returns whether the company has signed the latest Visma Developer Terms. |  |  |
| `PUT /license/sign/developerTerms` | Signs the Visma Developer Terms on behalf of the company. |  |  |

### municipality
Oppslag av norske kommuner med kommunenummer, fylke og arbeidsgiveravgiftssone (sone for AGA).

*Nøkkelord:* kommune, kommuner, kommunenummer, municipality, fylke, arbeidsgiveravgift, aga, aga-sone, arbeidsgiveravgiftssone, sone, payroll tax zone, virksomhet, underenhet, a-melding, skattekommune, kommunenr, aga sone, arbeidsgiveravgiftsone, sone 1a, sone 4a, sone 5, tiltakssonen, nord-troms, finnmark, payrolltaxzone

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /municipality/query` | Wildcard search. | id, query | BETA |
| `GET /municipality` | Get municipalities. | includePayrollTaxZones |  |

### subscription
Tripletex-abonnementet (kontoen) for selskapet: tilgjengelige pakker/moduler med priser, oppsigelse/stenging av kontoen og gjenåpning – ikke webhook-abonnementer.

*Nøkkelord:* abonnement, subscription, pakker, priser, si opp, oppsigelse, stenge konto, avslutte konto, lesetilgang, gjenåpne, gjenapne, reaktivere, tripletex-pakke, lisens, tripletex-abonnement, kontoabonnement, avslutte tripletex, bytte pakke, mikro, komplett, månedspris

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `PUT /subscription/cancel` | Close account with/without read access |  |  |
| `GET /subscription/packages` | Returns the packages that can exist for an account. |  |  |
| `PUT /subscription/reactivate` | Reopen account with previous modules |  |  |

### supportDashboard
Support-/partnerdashbord: kunder som er konkurs eller unntatt fra deaktivering/sletting, og eksport av kundetabellen (normalt kun for Tripletex-support/partnere).

*Nøkkelord:* support, supportdashbord, support dashboard, konkurs, avvikling, tvangsavvikling, likvidert, ekskludert, suspendert, kundetabell, eksport, partner, export, tvangsoppløsning, tvangsopplosning, slettet foretak, konkursbo, bankrupt, liquidated

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `GET /supportDashboard/export` | Export the customers table to a specific format | type*, filter*, startDateRange*, endDateRange* |  |
| `GET /supportDashboard/bankruptAndExcludedCustomers` | Returns the customers for support dashboard. |  |  |

### userLicense
Eksport av brukerlisenstabellen (hvilke brukere/lisenser som er aktive i en periode) til PDF eller CSV.

*Nøkkelord:* brukerlisens, brukerlisenser, user license, lisenser, antall brukere, brukere, eksport, csv, pdf, fakturagrunnlag, lisensoversikt, aktive brukere, brukeroversikt, lisenskostnad, lisensrapport, brukerlisensrapport, terminerte brukere, kontaktbrukere, user license export

| Kall | Hva | Parametere | Flagg |
|---|---|---|---|
| `POST /userLicense/export` | Export the user licenses table to a specific format |  |  |
