# Mva-avstemming: endepunktindeks

Designgrunnlag. Opprinnelig indeksert fra lokale filer (openapi.json, openapi-internal.json, docs/avstemmingsmodul.md, docs/api-v2-oppgaver.md, src/*.js, tools/*.py) og kontrollert en gang til av en egen verifiseringsagent. Rettelsene fra verifiseringen er tatt inn her. **Kalibrering K0 (2026-09-24, bare GET, én kalibreringsklient)** er lagt inn med status `testet K0 2026-09-24`, og resultatene står i `kalibrering.md`.

## Tegnforklaring

**Kilde:**
- `public`: openapi.json
- `internal`: openapi-internal.json. Kan endres uten varsel.
- `udok`: finnes bare i avstemmingsmodul.md eller UI-kode
- `cli`: eksisterende npm-skript eller modul i `C:/Users/Sjur/Tripletex API`
- `connector`: Tripletex-MCP. Brukes bare der API-et ikke strekker til.
- `ekstern`: Brregs åpne API via `src/leverandor.js`

**Status:**
- `testet`: dokumentert som kjørt
- `testet K0 2026-09-24`: kjørt lesende i kalibreringen og svarte som beskrevet i raden (se `kalibrering.md`)
- `K0: 403` / `K0: 500`: kjørt i kalibreringen, men sperret eller feilet. Bruk fallback.
- `kartlagt`: brukt eller listet i docs, men uten eget testnotat
- `fra spec`: står i spesifikasjonen, ikke testet
- `fra UI-kode`: sett i Tripletex' UI-kode, ikke testet
- `IKKE BEKREFTET`: kunne ikke verifiseres lokalt

**Kontekst:**
- **K** = klientkontekst (`connect("klient")`, companyId = kunde-id)
- **B** = byråkonto (companyId 0 med tokenet til byrået klienten tilhører, silfer eller unikum). tripletex.js blokkerer companyId 0, så byråkall må gå fra eget skript med `authorization(0, konto)`.

**Skriver?:**
- `nei` = bare lesing
- `JA` = skrivende. Krever Sjurs bekreftelse og legges i samlepakke 1 eller 2.
- `JA*` = teknisk PUT/POST som ikke endrer regnskapet (eksport eller valideringsspørring)

**Faste regler for alle kall:**
- Oppgi alltid `fields=` eksplisitt. Standardfeltene inneholder ofte `employee`, `createdBy`, `uploadedBy`, `lastUpdatedBy`, `reconciledBy` eller `controlledBy`.
- `dateTo`/`invoiceDateTo`/`toDate` er eksklusiv (dagen etter terminslutt). Unntak er merket.
- Alt som skrives ut, går gjennom `redact()`.
- Privatpersoner vises som «privatkunde n»/«leverandør n». Firmanavn og org.nr. er greit.
- `id ≠ number` for vatType.

---

## 0. Oppsett, id-kart og byrånivå (stadium S0–S1)

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| GET | /company/>withLoginAccess | public | testet (tripletex.js `clients()`) | Klientliste. `id` = kunde-id i byrået (Basic-auth companyId i klientkontekst og `customerId` i modulen). `customerCompanyId` = klientens company-id/contextId. | `count=1000`, `fields=id,name,organizationNumber,customerCompanyId`. Aldri email/phone/address. Skriv `>` bokstavelig eller som %3E. | nei | token (rawRequest) |
| GET | /accountingOffice/clients/{id} | internal | testet K0 2026-09-24 | Alternativt oppslag for customerCompanyId per kunde-id | `fields=customerCompanyId,organizationNumber`. `/accountingOffice/clients?query=&fields=id,name,customerCompanyId` virker også. customerCompanyId = `whoAmI.companyId` i klientkontekst (bruk `fields=companyId`, fordi `company(id)` gir null). | nei | B |
| GET | /accountingOffice/clientOverview/context/{customerId} | internal | kartlagt | canAccessVat/Balance/Bank, vatRegistered, hasGeneral/PrimaryIndustry | `year`. Industry-feltene er `null` når canAccessVat=false: det betyr ukjent, ikke «nei». Hent ikke accountManagerDisplayName eller ameldingStatuses. | nei | B |
| GET | /accountingOffice/reconciliations/permissions/{customerId} | internal | testet | API-brukerens tilgang. Avgjør modul eller Excel. | `fields=canAccessVat,canAccessBalance,canAccessBank`. Gjelder API-brukeren, ikke klientens moduler. | nei | B |
| GET | /accountingOffice/reconciliations/verifyModule | internal | fra spec | Om avstemmingsmodulen er aktiv i byrået | Svarer med ren boolean (ikke `fields=value`). Kjøres én gang per byrå, og svaret caches. | nei | B |
| GET | /accountingOffice/reconciliations/periodsOverview | internal | testet K0 2026-09-24 | Perioder per type med termNumber, start, slutt og reconciliation(id,status). Gir også lengden på BALANCE-perioden. | `customerId*`, `year*`, `type*` = VAT_GENERAL_INDUSTRY / VAT_PRIMARY_INDUSTRY / BALANCE. `type=VAT` eller `BANK` gir 422. `fields=*,periods(*,reconciliation(id,status,type))`. endDate er eksklusiv. **BALANCE er månedlig** (termNumber 1–12) og har i tillegg en ANNUAL_BALANCE-periode med term=1, som filtreres bort på reconciliation.type. VAT_PRIMARY_INDUSTRY og VAT_GENERAL_INDUSTRY gir samme avstemminger (gruppe «VAT»), så reportType skilles med `reconciliations?type=`. `reconciliation=null` betyr at avstemmingen ikke finnes. | nei | B |
| GET | /accountingOffice/reconciliations | internal | testet K0 2026-09-24 | Finne avstemmingen: id, status, modifiable, requiresControl, document | `customerId`, `year`, `term` og `type` filtrerer på serversiden (alle fire gir 1 eller 0 treff). **Kontroller likevel customer.id, year, term og type lokalt**, fordi ukjente parametere ignoreres uten feil (f.eks. `customerIds` gir alle kunder). `status` er ikke et filter. En ugyldig type gir 404. `term` betyr måned for BALANCE og termin for VAT, så bruk den alltid sammen med `type`. `fullResultSize` er bare en nedre grense: bla til en side gir færre enn count. Standardrekkefølgen er etter id, så bruk `sorting=term`. Status: DRAFT/COMPLETED/CONTROLLED/ERROR/WARNING. | nei | B |
| GET | /accountingOffice/reconciliations/{id} | internal | kartlagt | Status og document(id) for én avstemming | `fields=id,status,modifiable,requiresControl,document(id,fileName)` | nei | B |
| GET | /clientTasks/inboxes · /forApprovals · /travelsAndExpenses · /forReviews · /remits | internal | fra spec | Tellere per klient: innboks, attestering, reiser/utlegg, til gjennomgang, betalinger til godkjenning | `clientCompanyIds=` med de klientene Sjur har navngitt. `accountManagerIds` er ansatt-id-er og skal ikke logges. Hva som telles i travelsAndExpenses og forReviews er ikke dokumentert. | nei | B |
| GET | /todoList/vatReturnsSection | internal | fra spec | Mva-status og frist per klient. Primærkilde for frist sammen med vatReturnsOverview. | `fromDate*`, `toDate*` (ekskl.), `clientCompanyIds`, `statusTypes`. `fields=customerId,clientCompanyId,period,periodStart,year,dueDate,customDueDate,status(type),customStatus(type),url`. `status` uten understruktur gir med `lastUpdatedBy` (personnavn). Enum: OVERDUE/NOT_STARTED/INCOMPLETE/COMPLETED/NOT_APPLICABLE. | nei | B |
| GET | /ledger/vatSettings | public | fra spec (sondert) | Registreringsstatus og aktiverte kodegrupper | `vatRegistrationStatus` (VAT_NOT_REGISTERED/VAT_APPLICANT/VAT_REGISTERED/VAT_COMPENSATION) og alle `has*`-flagg. Merk: `hasVatInImport` = kode 14/15/20/21, ikke 81–85. 31→hasVatOutMedium, 33→hasVatOutLow, 11→hasVatInMedium, 5→hasVatOutNoneInside, 52→hasVatOutExportNone, 6→hasVatOutOutside, 12/32→hasVatIn/OutFish, 86/87→hasVatInHighForeignServices, 88/89→hasVatInLowForeignServices, 51/91/92→hasVatInAndOutReverseDuty. | nei | K |
| GET | /vatTermSizeSettings | public | fra spec | Termintype per reportType | `sorting=fromDate`. Ingen filter, så reportType filtreres lokalt. termSize: ONE_/TWO_/THREE_/FOUR_/SIX_MONTHS, YEAR, NOT_REGISTERED. Gjeldende rad er den siste med fromDate ≤ terminstart. | nei | K |
| GET | /ledger/postingRules | public | fra spec (sondert) | multipleIndustries (to meldinger), vatPerDepartment, standard reskontrokonti, øreavrundingskonto | `fields=multipleIndustries,vatPerDepartment,accountReceivableCustomersId(id,number),accountDebtVendorsId(id,number),accountRoundDiffId(id,number)`. `*Id`-feltene er Account-objekter. | nei | K |
| GET | /vatReturnsOverview/reportTypes | internal | testet K0 2026-09-24 | Alminnelig næring og/eller primærnæring | `fields=hasGeneralIndustry,hasPrimaryIndustry` | nei | K |
| GET | /vatReturnsOverview/overview | internal | testet K0 2026-09-24 | Alle terminer i året: id (vatReturns-id), start, slutt, **dueDate**, status, voucherId, voucherNumber (string), amount, isPaid | `year`, `reportType`. Status følger VatReturns2022-enum (NOT_STARTED … FEEDBACK_RECEIVED, MANUAL_DELIVERY, USER_FORBIDDEN, SENDING_FAILED), ikke deliveryStatus-enum. **`term` er 0 for opprettede og leverte terminer**, så terminnummeret tas fra start/end eller status/list. dueDate er flyttet ved helg (10.10 på lørdag blir 12.10), så fristen hentes herfra og beregnes ikke. Terminer som ikke er opprettet har id=0. | nei | K |
| GET | /vatReturns/status/list | public | testet K0 2026-09-24 | Levert og betalt for alle terminer i perioden | `startDate`, `endDate` (ekskl.), `reportType`. `fields=year,term,vatReturns2022Id,voucherNumber,totalAmountVatBasis,altinnPaymentAmount,deliveryStatus(status,time),paymentStatus(status,totalAmount,remainingAmount,paymentDate)`. Svaret har **ikke** startDate/endDate. Terminer før 2022 er utelatt. Levert = RECEIPT_RECEIVED eller MANUAL_DELIVERY. | nei | K |
| GET | /vatReturns/status | public | testet (probe) | Én termin | Oppgi alltid `year`, `term` og `reportType`. Uten dem kommer forrige termin. Eksplisitte fields som over. | nei | K |
| GET | /company/{id} | public | fra spec | Org.nr. og selskapsform | `fields=id,name,organizationNumber,type,startDate` | nei | K |
| GET | /company/salesmodules | public | K0: 403 (BETA) | Salgsmoduler (PRIMARY_INDUSTRY, PROJECT, LOGISTICS, OCR, ZTL = bankintegrasjon, ikke Zettle) | `fields=name,costStartDate` | nei | K |
| GET | /company/modules | internal | testet K0 2026-09-24 | Boolske modulflagg for ruting og moduldiagnose (gir ikke tredjepartstillegg) | `fields=invoice,project,moduleproject,moduleLogistics,approveVoucher,salary,electronicVouchers,ocr,moduleFixedAssetRegister,autoPayOcr,remit,moduleCurrency,moduleMultipleLedgers` | nei | K |
| GET | /addon/company/{id} | internal | testet K0 2026-09-24: **ikke bruk** | ~~Aktive integrasjoner~~ | Kallet gir tilleggskatalogen, ikke firmaets tillegg. Svaret er identisk for kunde-id, company-id og en id som ikke finnes (id-en sjekkes bare som positivt heltall), og alle tillegg har active=false. Integrasjonene står i klientprofilen eller utledes fra posteringer. `/integration` ga 0 og har personfelt. | nei | – |
| GET | /accountingOffice/clientsModules/{category}/{customerId} | internal | fra spec | EHF-mottak, bankintegrasjon, INVOICE_OPTION_VIPPS | `category` = EHF / BANK_INTEGRATIONS / VOUCHER_AUTOMATIONS. `fields=modules(module,status)` | nei | B |
| GET | /ledger/accountingPeriod | public | testet K0 2026-09-24 | Månedsperioder i terminen og isClosed | `startFrom`, `startTo` (ekskl.). Match på `start`. `end` er eksklusiv. `fields=id,number,start,end,isClosed,checkLedgerLogTime`. Låsfeltet er `isClosed`, og låsing skjer i praksis per år. Hent aldri `*EmployeeName` eller `*EmployeePictureId`. `/getAccountingPeriodByDate` gir 403 og brukes ikke. | nei | K |
| CLI | `src/leverandor.js` brreg-hjelper (`brreg()`/`brregOrgnr()`/`fakta()`), importert i skript | ekstern via cli | i bruk | Klientens mva-registrering og `registreringsdatoMerverdiavgiftsregisteret`, konkurs, avvikling, sletting, org.form, næringskode | `fakta()` må utvides med `frivilligMvaRegistrertBeskrivelser`. Bruk aldri `npm run leverandor -- oppslag` på klientens eget org.nr., for det lagrer klienten i leverandørindeksen. Ikke les roller (persondata). | nei (lokal cache) | ingen token |
| GET | /anomalies/context · /anomalies/clientsOverview · /anomalies/clients | internal | K0: 403 (code 9000, både B og K) | ~~Om avviksmodulen er aktiv, og hva den koster~~ | Kan ikke leses med API-tokenet. Sjur oppgir `anomalies_aktiv` i profilen (MANUELT). | nei | B |
| GET | /altinn/systemuser/hasSystemUser | internal | testet K0 2026-09-24 | Diagnose før /claimsAndPayments | `isAgent`. At svaret er `false` betyr ikke at kallet er blokkert. | nei | K |
| GET | /idporten/loginstatus | internal | testet | Dokumenterer at API-tokenet ikke har ID-porten-økt (active:false) | – | nei | K |
| GET | /company/settings/altinn | internal | testet K0 2026-09-24 | Diagnoseflagget `altinn_id_satt` i P0 (sier ingenting om ID-porten eller systembruker) | **Bare `fields=altInnId`**, aldri `fields=*` (passordfelt). Verdien logges ikke. Det finnes også en PUT på samme sti, og den brukes ikke. | nei | K |

## 1. Felles datasett (hentes én gang per klient og termin, deles av alle områder)

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| GET | /ledger/account | public | testet | Kontoplan | `count=1000`. `fields=id,number,name,type,ledgerType,isInactive,isBankAccount,isCloseable,requireReconciliation,vatType(number),vatLocked,legalVatTypes(id,number),currency(code)`. Aldri bankAccountNumber/IBAN. `ledgerType` finnes bare med modulen «flere reskontroer», og enum-verdien er VENDOR, ikke SUPPLIER. | nei | K |
| GET | /ledger/vatType | public | fra spec (sondert) | Kodekart med spesifikasjonskoder (tap på krav, uttak, justering, tilbakeføring) og relative koder | `count=1000&shouldIncludeSpecificationTypes=true`. `fields=id,number,name,percentage,deductionPercentage,parentType(id,number)`. Det finnes ikke noe specificationType-felt, så kodene må kartlegges på navn én gang. `vatDate` virker bare sammen med `typeOfVat`. | nei | K |
| GET | /advancedVoucher/internal/vatTypes | internal | fra spec | Koder per dato med direction, basisPercentage og isReverseIn(Non)DeductableVatCode | `dates=<datoer>` (kommaseparert). Fallback: GET /incomingInvoice/internal/vat?vatDate= (testet K0 2026-09-24: 200 selv om resten av /incomingInvoice gir 403) | nei | K |
| GET | /balanceSheet | public | testet | Saldobalanse for T, T−1, T i fjor og hittil i år | `dateFrom*`, `dateTo*` (ekskl.), `accountNumberFrom/To` (To inkl.), `includeActiveAccountsWithoutMovements=true`. `fields=account(id,number,name),balanceIn,balanceChange,balanceOut`. Bare NOK. | nei | K |
| GET | /ledger/posting | public | testet K0 2026-09-24 | Lett posteringskube for [1.1. i fjor, T_slutt+15 d) | `dateFrom*`, `dateTo*` (ekskl.), som filtrerer på **posting.date**. `accountId` tar ett tall, så bruk heller `accountNumberFrom/To`. Filteret `type` finnes (INCOMING_PAYMENT, OUTGOING_INVOICE_CUSTOMER_POSTING, WAGE …). Ingen filtre på vatType, beløp eller tekst. `fields=id,date,amount,amountGross,amountCurrency,currency(code),row,systemGenerated,type,invoiceNumber,termOfPayment,externalRef,isVatReadonly,isAmountVatClosed,account(id,number),vatType(id,number,percentage),customer(id),supplier(id),asset(id),project(id),closeGroup(id,date),voucher(id)`. Nestet `voucher(id,date,changes(changeType,timestamp))` godtas (CREATE og UPDATE, ca. 5 s per 4 500 linjer). Aldri employee eller employeeId. **K0:** Bla med from/count til en side gir færre enn count. `fullResultSize` er bare en indikator på at det finnes flere sider, ikke et totalantall. `vatType.number` er en **streng** (`"0"`). Systemgenererte 27xx-linjer har row 0 og vatType `"0"`, men det finnes også manuelle linjer (systemGenerated=false) på 2700/2703/2710. `isAmountVatClosed=true` = en kodet linje som er med i en levert melding. Terminen følger posting.date, ikke voucher.date. | nei | K |
| GET | /ledger/voucher | public | testet K0 2026-09-24 (id,date,changes) | Bilagskart (én rad per bilag) | `dateFrom*`, `dateTo*` (ekskl.), `typeId`, `number`. `fields=id,number,year,date,voucherType(id,name),supplierVoucherType,vendorInvoiceNumber,ediDocument(id),attachment(id),document(id),reverseVoucher(id,number,year,date),changes(timestamp,changeType)`. Ta ikke med employeeId i changes. Ingen changedSince. `supplierVoucherType=TYPE_INCOMING_INVOICE_UNIFIED` betyr ny leverandørfakturaflyt. | nei | K |
| GET | /ledger/voucherType | public | fra spec (sondert) | Bilagstype-id-er (lønn, utgående faktura, reiseregning, utlegg) | `fields=id,name`. Navnene avhenger av språk. | nei | K |
| GET | /customer | public | fra spec (probe) | Kundekart | `id=<liste>`, og `isInactive=true` i eget kall. `fields=id,customerNumber,organizationNumber,isPrivateIndividual,isInactive,isSupplier,isFactoring,ledgerAccount(id,number),physicalAddress(country(isoAlpha2Code)),postalAddress(country(isoAlpha2Code))`. Navn tas bare med for firma. | nei | K |
| GET | /supplier | public | fra spec (brukt i leverandor.js) | Leverandørkart | Som over, med `supplierNumber,isCustomer`. Aldri bankAccountPresentation. | nei | K |
| GET | /invoice | public | fra spec (probe) | Utgående fakturaer og kreditnotaer, T til T+45 d | `invoiceDateFrom*`, `invoiceDateTo*` (ekskl.), `status`. Gir bare fakturerte fakturaer. `creditedInvoice` er et heltall (kan ikke nestes). `fields=id,invoiceNumber,invoiceDate,invoiceDueDate,deliveryDate,amount,amountExcludingVat,amountOutstanding,isCreditNote,isCredited,creditedInvoice,customer(id,isPrivateIndividual,organizationNumber),orders(id,deliveryAddress(country(isoAlpha2Code)),invoiceOnAccountVatHigh,totalInvoicedOnAccountAmountAbsoluteCurrency,orderLines(product(id),vatType(number),amountExcludingVatCurrency)),voucher(id,number,date)` | nei | K |
| GET | /supplierInvoice | public | testet K0 2026-09-24 (id,voucher) | Leverandørfakturaer i det gamle registeret. **Standardvei for leverandørfakturaer** så lenge /incomingInvoice gir 403. | `invoiceDateFrom*` (T_start−6 mnd), `invoiceDateTo*` (T_slutt+62 d, ekskl.), `voucherId`, `supplierId`. amountExcludingVat=0 betyr ukjent. Ny flyt og manuelle 2400-bilag mangler, så kryssjekk alltid mot 2400-posteringer. | nei | K |
| GET | /incomingInvoice/search | internal | **K0: 403** (code 9000, BETA/pilot) | Ny leverandørfakturaflyt: inbox/nonPosted/approval/ledger | 403 uansett status og filtre. Sjekk én gang per klient og cache svaret. Ved 403: /supplierInvoice + 2400-posteringer + connector `search_supplier_invoices`. Ellers: ett kall per `status`. `invoiceDateFrom/To` (To ekskl.). `from` er maks 10000. | nei | K |
| GET | /incomingInvoice/{voucherId} | internal | **K0: 403** (BETA) | Fakturadato, reverseVoucherId og generalIndustryVatPeriodClosed per bilag i ny flyt (enkeltoppslag) | `fields=voucherId,invoiceHeader(vendorId,invoiceDate,invoiceNumber,invoiceAmount),orderLines(row,accountId,vatTypeId,amountExclVat,amountVat,assetId),metadata(voucherNumber,voucherYear,reverseVoucherId,generalIndustryVatPeriodClosed)`. Ikke employeeId. | nei | K |
| GET | /ledger/voucher/>nonPosted | public | fra spec (sondert) | Kladder og bilag som ikke er godkjent | `includeNonApproved*=true`, `dateFrom`, `dateTo` (ekskl.), `changedSince`. Ikke description. | nei | K |
| GET | /vatReturns/validateCreate | internal | testet K0 2026-09-24 (GET) | Tripletex' egen forhåndssjekk før meldingen opprettes | `year`, `vatTerm` (ikke `term`), `reportType` (valgfri). `fields=incompleteVouchers,accountingPeriodClosed,beforeStartBalance,invalidDate,accountsRequiringHarmonization(number,name),helpAccountPostedOn(number,name),alreadyExists,success`. Levert termin gir `alreadyExists=true`. | nei | K |
| GET | /vatReturnsOverview/vatTermAmount | internal | testet K0 2026-09-24 | Terminbeløpet Tripletex beregner, også for terminer som ikke er opprettet og for løpende termin | `year`, `term` (ikke `vatTerm`), `reportType` (valgfri, standard GENERAL_INDUSTRY). Svar `{value}` i hele kroner. **+ = å betale, − = til gode**, samme fortegn som altinnPaymentAmount. = Σ per kode av trunc(−Σ(amountGross − amount)), avkortet mot null per kode. **Svarer 0 uten feil** ved manglende eller feil term/parameternavn eller feil reportType. Valider derfor parametrene, og kryssjekk 0 mot `>vatTerm`. | nei | K |
| GET | /ledger/posting/openPost | public | testet K0 2026-09-24 | Åpne poster per D | `date*` = D (ekskl.), `accountId` eller `accountNumberFrom/To` (**påkrevd**, ellers kommer leverandørposter på andre kontoer med), `sorted=false`, `fields=id,date,amount,closeGroup(id,date)`. **Historisk snitt:** poster som ble lukket etter D, regnes som åpne. Σ amount = /balanceSheet UB (dateTo=D). | nei | K |
| GET | /asset · /asset/overview | public · internal | fra spec | Anleggsregister og tilgang/påkostning/avgang per år | /asset har ingen filtre. /asset/overview tar `year` og `showAllAssets=true`. | nei | K |
| CLI | `npm run -s bankavstemming -- --client "<klient>" --fra <år>-01 --til <siste mnd i T> --ut <arbeidsmappe>/bank` | cli | testet | status.json og data.json per konto og måned | Med `--alle` tar kjøringen ca. 40 s for alle klientene. Filene inneholder banktekster og hører hjemme i arbeidsmappa. CSV-grenen mangler datofilter og id. Hovedbokssiden gir bare antall og sum. | nei | K |
| CLI | `npm run -s leverandor -- importer --client "<klient>" --fra <T_start> --til <T_slutt+1> --json` | cli | i bruk (data/leverandorer.json har 30 poster) | Leverandørindeks: mva-registrering, land, næringskode, status, vurdering 86/87/VOEC. «Vurdert av Sjur» overstyrer. | Tar bare leverandører med postering på 2400–2499. Andre supplier-id-er (kortkjøp) slås opp separat. Enkeltpersonforetak lagres som hash. | nei (lokal indeks) | K |

## 2. Forutsetninger: ubehandlet og omsetning (punkt 1 og 2)

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| GET | /voucherInbox/inboxCount | public | fra spec | Rask telling. 0 betyr at F1.1/F1.2 er OK. | – | nei | K |
| GET | /voucherInbox/inboxFiltered | internal | fra spec | Innboksen med type, fakturadato, beløp, mva, skannestatus og duplikatmerking | Ingen datofilter, så hele innboksen blas. `fields=id,filterType,receivedDate,invoiceDate,dueDate,invoiceAmount,invoiceCurrency,vatAmount,vatPercentage,supplierName,vatNumber,pdfScanningStatus,isLocked,isSpam,duplicateVoucherNumberAsString,importFailureReason,unresolvedAnomalyCount,canBeSentToLedger,canBeRegisteredAsCustomsDeclaration,voucherId`. Aldri bankAccount, senderEmailAddress, documentUploaderName/Email, rejectedByName, buyersContact eller merchantName. | nei | K |
| GET | /voucherInbox/inboxIncompleteCount · /inboxAttestationCount · /inboxAnomalyCount | internal | fra spec | Tellinger | – | nei | K |
| GET | /ledger/voucher/>voucherReception | public | fra spec (probe) | Offentlig fallback for bilagsmottaket | `dateFrom`, `dateTo` (ekskl.). `fields=id,date,vendorInvoiceNumber,supplierVoucherType,attachment(id)`. description kan inneholde navn. | nei | K |
| GET | /tripletexDashboard/voucherSummary | internal | fra spec | Innboks, attestering og ikke bokført i ett kall. Rask telling og del av fingerprint. | `fields=voucherReceptionData(count),attestationVouchersData(count),nonPostedVouchersData(count)` | nei | K |
| GET | /attestation/companyModules | internal | fra spec | Attesteringsoppsett uten persondata | `fields=allowPostingBeforeVoucherApproved,companyAttestorCanOverride` | nei | K |
| GET | /voucherInbox/context | internal | fra spec | voucherAttestationEnabled, hasModuleVoucherApproval | Bare eksplisitte fields. Objektet har employeeId og voucherScanningEmail. | nei | K |
| GET | /supplierInvoice/forApproval | public | fra spec (probe) | Gammel attesteringsflyt | `showAll=true`. `fields=id,invoiceNumber,invoiceDate,amount,amountExcludingVat,supplier(id,organizationNumber),voucher(id,number,date)`. Ikke approvalListElements. | nei | K |
| GET | /ledger/voucher/attestations | internal | fra spec | Ny attesteringsflyt | `attestationStatusEnums=ATTESTATION_DELIVERED` er påkrevd ifølge beskrivelsen, men står ikke i parameterlisten. Verdien ALL gir tom liste. Ikke attestationSteps eller lastComment. | nei | K |
| GET | /travelExpense | public | fra spec (**personendepunkt**) | Levert men ikke godkjent, eller godkjent men ikke bokført. Bare tellinger og summer. | Ett kall per `state`. `fields=id,state,date,type,amount,highRateVAT,mediumRateVAT,lowRateVAT,accountingPeriodVATClosed,voucher(id)`. Aldri employee, approvedBy, travelDetails eller costs. Kjøres bare når telleren er over 0. | nei | K |
| GET | /documentReception | internal | fra spec | Uleste dokumenter | `onlyUnread=true`, `startDate`, `endDate` (**inkl.**). Ikke receiverName eller senderName. | nei | K |
| GET | /bank/reconciliation/internal/directposting/draft | internal | fra spec | Utkast til direkteposteringer som holder banktransaksjoner uten bilag | `bankReconciliationId`. **`fields=drafts(id,bankReconciliationId,flowType,createdDate,escapedVoucherId,bankTransactionIds)`**. Ikke payload eller transactionEntries. | nei | K |
| GET | /order | public | fra spec | Levert men ikke fakturert, fakturautkast, abonnement, a konto | `orderDateFrom*`, `orderDateTo*` (ekskl.), `isClosed`, `isSubscription`. Feltet status gjelder bare logistikkunder. Ikke kundenavn for privatpersoner. | nei | K |
| GET | /invoice/{orderId}/invoices | internal | fra spec | Fakturaer per abonnementsordre | Bruk heller orders(id) fra /invoice. | nei | K |
| GET | /internal/order/recurring/hasPilot · /hasMigratedSubscriptions · /overview | internal | fra spec | Ny repeterende fakturering. Migrert gir risiko for dobbelttelling. | Pagineres med cursor. Ikke customerName eller receiverEmail. | nei | K |
| GET | /project · /project/batchPeriod/invoicingReserveByProjectIds | public | fra spec | Opptjent men ikke fakturert. Erstatter /timesheet. | `isClosed=false`, `includeRecentlyClosed=true`. `ids*` maks 1000, `dateFrom*`, `dateTo*` (ekskl.). Ikke projectManager. | nei | K |
| GET | /tripletexDashboard/invoiceReserve | internal | fra spec | Totalreserve som ruting. 0 betyr at prosjektkallene hoppes over. | Ikke datoavgrenset. | nei | K |

## 3. Reskontro

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| GET | /ledger/openPost | public | testet K0 2026-09-24 | Kryssjekk: sum åpne poster per konto | `date*`, `accountId`. Ingen intervall. sumAmount = closingBalance = UB, og tallene er de samme som openPost. | nei | K |
| GET | /ledger/closeGroup | public | kartlagt (probe) | Lukkinger som krysser D, og feil lukking | `dateFrom*`, `dateTo*` (ekskl.) | nei | K |
| GET | /ledger/>supplierBalance | internal | fra spec | IB, endring og UB per leverandør | **Oppgi alltid `dateFrom`** (standardverdien er i dag). `dateTo` er dokumentert som eksklusiv. | nei | K |
| GET | /internal/supplierSubLedger/summary · /details | internal | testet K0 2026-09-24: **ikke fasit** | Bare sekundær diagnose for 2400 | **Ingen `fields`-parameter.** `openAmount`/`totalOpenAmount` er **dagens** restbeløp, også med historisk `openPostingsAsOfDate`, så kallet kan ikke brukes som fasit for D. Posteringsmengden med `openPostingsAsOfDate=D` (eksklusiv) er lik openPost(date=D). totalDebit − totalCredit er historisk, men avvek med et konstant, uforklart beløp fra 2400. Brukes den: `onlyOpenPostings=true`, `openPostingsAsOfDate=D`, `endDate=D−1`, `startDate` = første regnskapsår, `supplierCount=1000`. /details gir ikke amount eller account. | nei | K |
| GET | /reminder | public | kartlagt (probe) | Purretrinn, inkassovarsel og inkasso (hovedkilde for tapsrisiko) | `dateFrom*`, `dateTo*` (ekskl.), `invoiceId`, `termOfPaymentTo`. `type` = SOFT_REMINDER/REMINDER/NOTICE_OF_DEBT_COLLECTION/DEBT_COLLECTION. Ikke bankkontofeltene eller comment. | nei | K |
| GET | /voucherStatus | public | kartlagt (probe) | Inkasso via integrasjon (tillegg) | `type=DEBT_COLLECTION`. Krever at integrasjonen er satt opp. | nei | K |
| GET | /internal/invoiceOverview (+ />sum) | internal | fra spec | brregStatus (kodene er ikke dokumentert), factoringCustomerId, amountOutstanding | Filtrene står ikke i spec. Viser status i dag. Ikke customer(name), projectManagerName eller comment. | nei | K |
| GET | /internal/invoiceOverview/otherPostingOverview (+ />hasUnknownPayments, />sum) | internal | fra spec | UNKNOWN_PAYMENT, ADVANCED_VOUCHER, OPENING_BALANCE, INCOME | Ingen filtre (heller ikke på >sum). Bla gjennom og filtrer på type og status lokalt. Ikke customerName, senderName eller senderMessage. | nei | K |
| GET | /incomingInvoice/internal/checkForDuplicateInvoiceNumber | internal | fra spec | Tripletex' egen duplikatsjekk for én kandidat | `vendorId*`, `invoiceNumber`, `excludeVoucherId`. Svarer med ett objekt. | nei | K |
| GET | /incomingInvoice/internal/creditNotes | internal | fra spec | Leverandørkreditnotaer med posted-flagg | `vendorId*` (én leverandør per kall) | nei | K |
| GET | /incomingInvoice/internal/{vendorId}/invoiceHistoryByVendor | internal | fra spec | Originalfaktura til en leverandørkreditnota | `count` | nei | K |
| GET | /currency/{id}/rate | public | fra spec | Kurs per T_slutt for åpne poster i valuta | Alternativt /currency/{from}/{to}/exchangeRate | nei | K |
| GET | /anomalies/aggregate (+ /count/byCheckType) | internal | fra spec | Tripletex' avviksdeteksjon (DUPLICATE_POSTINGS, OLD_DATE, VAT_NUMBER, VENDOR_VAT_NUMBER, CUSTOMER_VAT_NUMBER, VENDOR_ORG_NUMBER_MISMATCH, NEW_SIGN_ON_ACCOUNT …) | `customerId` (tekstliste). **`status` tar én verdi, så det blir ett kall per status.** `startDate/endDate` gjelder tidspunktet avviket ble funnet, ikke bilagsdato, så hent fra T_start til kjøredato og filtrer på voucher.date. Hent `anomalyId` (det er den PUT /anomalies/status krever). Ikke company, comments eller actions. | nei | B |
| GET | /anomalies/{id} | internal | fra spec | currentVatCode, allowedVatCodes, posteringer | `clientCompanyId*` = klientens company-id (ikke kunde-id) | nei | B |
| PUT | /ledger/posting/:closePostings | public | fra spec | Utligne eksakte par | Body er en array av posting-id-er som summerer til 0 og har samme motpart. Kontoen må være isCloseable. | JA | K |
| PUT | /internal/invoiceOverview/otherPostingOverview/{postingId}/:matchUnknownPayment | internal | fra spec | Koble ukjent innbetaling til faktura | `invoiceId*` | JA | K |
| PUT | /ledger/internal/general/:reopenPostings | internal | fra spec (BETA) | Oppheve feil utligning | Parameteren heter `closeGroupIds`, men beskrivelsen sier posting-id-er. Tvetydig, så dette gjøres heller i UI. | JA | K |
| PUT | /ledger/voucher/{id}/:reverse | public | fra spec | Tilbakeføre dublett eller feilkodet bilag (dato i åpen termin) | `date*`. Tilbakeføringen reverserer fradraget i den nye terminen (jf. en testklient T4). Ikke for lønnsbilag. | JA | K |
| GET | /incomingInvoice/internal/{voucherId}/validateReverse | internal | fra spec | Forhåndssjekk før tilbakeføring i ny flyt | `reverseVoucherDate*` | nei | K |
| POST | /incomingInvoice/{voucherId}/reverse | internal | fra spec, BETA, pilot | Tilbakeføre i ny leverandørfakturaflyt | `reverseVoucherDate*` (query, ikke `date`) | JA | K |

## 4. Bank

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| GET | /bank/reconciliation | public | testet (K0: bankAccountClosingBalanceCurrency = state.bankStatementOutBalance) | Alle kontoer og måneder i ett kall. Rask sti for BK1. | `accountId=<liste>`, `accountingPeriodId=<liste>`. `fields=id,type,isClosed,closedDate,approvable,bankAccountClosingBalanceCurrency,account(id),accountingPeriod(id,start,end)`. Ikke closedByEmployee. | nei | K |
| GET | /bank/reconciliation/{id} | public | fra spec | Én avstemming med version, approvable og transaksjoner med id | `fields=id,version,isClosed,approvable,bankAccountClosingBalanceCurrency,transactions(id,postedDate,amountCurrency,matched)` | nei | K |
| GET | /bank/reconciliation/internal/state | internal | testet K0 2026-09-24 | Supplement for åpne eller manglende måneder: approvable-flagg og isReadOnly. Beløpene gir de offentlige kallene. | `accountId*`, `startDate` (**påkrevd**, uten den kommer 500; hvilken som helst dag i måneden). `balanceOutDifference` = ledgerAccountOutBalance − bankStatementOutBalance (verifisert). bankOut=null gir differanse = saldo i hovedboken. `reconciliation=null` = ingen avstemming. `isReadOnly=true` = en **senere** måned er lukket. `isApprovableIncomplete=true` også uten avstemming og med saldo 0, så flaggene kan ikke brukes alene. Ett kall per konto og måned. | nei | K |
| GET | /bank/reconciliation/internal/period | internal | fra spec | Alle måneder for én konto | `accountId*`, `isForWholeYear=true` (semantikken må verifiseres) | nei | K |
| GET | /bank/reconciliation/external/state | internal | fra spec | Bare EXTERNAL_PSD2-kontoer | `fromDate`, `toDate` (**inkl.**), maks 366 d | nei | K |
| GET | /bank/statement · /bank/statement/{id} | public | testet (id,fromDate,toDate) | Dekning av kontoutskrifter, hull, overlapp og sluttsaldo | `accountId=<liste>` (ett kall). Saldofeltene er ikke testet. 403 hos enkelte klienter. Ikke fileName. | nei | K |
| GET | /bank/statement/transaction | public | testet | Transaksjoner med id, matched og **paymentId** | `bankStatementId*`. Ikke /details. | nei | K |
| GET | /bank/statement/transaction/query | internal | fra spec | JSON med id uten bankStatementId | `isIncoming*`, `isOutgoing*`, `isPosted*`, `isNotPosted*`. Formatet på `period` er ukjent. | nei | K |
| PUT | /bank/reconciliation/transactions/unmatched:csv | public | testet | Umatchede banktransaksjoner (lesende PUT) | `reconciliationId`. CSV uten id. Filtrer på dato og dedupliser lokalt. | JA* | K |
| GET | /bank/reconciliation/closedWithUnmatchedTransactions | public | fra spec | Ja/nei per konto | Gir bare **den siste** slike avstemmingen, så den kan ikke brukes til å gå gjennom alle. | nei | K |
| GET | /bank/reconciliation/match | public | fra spec | DIRECT_POSTING, AUTOPOSTING_APPROVED, ADJUSTMENT | `bankReconciliationId=<liste>`, `approved` | nei | K |
| GET | /bank/reconciliation/internal/match | internal | fra spec | Ventende forslag i den interne formen som updateSuggestions krever | `approved=false`, `isAutoPosting` | nei | K |
| GET | /bank/reconciliation/internal/autoposting/suggestions | internal | fra spec | Tripletex-forslag (BANK_FEES, TRANSFER_ENTRIES, INTERMEDIATE_ACCOUNT, OUTGOING_INVOICE_WITHOUT_KID, INCOMING_INVOICE_MANUALLY_PAID …) | `bankReconciliationId` | nei | K |
| GET | /bank/reconciliation/internal/paymentType/defaultInterimAccount | internal | fra spec | Standard interimskonto. (`/internal/interimAccount` gir kontoer for overføring mellom perioder, ikke denne.) | – | nei | K |
| GET | /bank/reconciliation/internal/{id}/changelog | internal | fra spec | Gjenåpnet eller endret etter levering | changeType CREATE/UPDATE/DELETE/**LOCKED**/REOPENED. Ikke employeeNameAndNumber eller changeLogEmployeeDTO. | nei | K |
| GET | /bank/reconciliation/internal/attachment/{id}/voucherInbox · /attachment/documents | internal | fra spec | Dokumentasjon som allerede ligger i Tripletex | Ikke blob | nei | K |
| GET | /bank/reconciliation/internal/export/emailHistory | internal | fra spec | Om listen med åpne poster alt er sendt til kunden | Ikke recipients eller sentBy | nei | K |
| GET | /bank/statement/>balance | internal | fra spec | Bokført og disponibel saldo på en dato | `accountId*`, `onDate`. Bruk bare når `bookedDate = onDate`. | nei | K |
| GET | /bank/agreements | internal | fra spec (K0: `/bank/agreements/autoPayStatus` gir 403) | AutoPay-avtaler, aktiv/inaktiv, saldo | **`updateBalance=false`** (standard er true og henter saldo fra banken). true bare i dekningskontrollen IN15. Aldri iban, bban eller uploaderEmployee. | nei | K |
| GET | /bank/integration/switch/ztlAccounts · /ztlAccount/{id}/hasValidConsent | internal | **K0: 500** (code 1000, ztlAccounts) – test på nytt eller bruk fallback (bankavstemming/kontoutskrift) | lastUpdated, saldo og samtykke | Aldri bban/iban. Nytt samtykke krever BankID i UI. | nei | K |
| GET | /bank/maintenance/ongoingForActiveAgreements | internal | fra spec | Bankvedlikehold forklarer manglende import | – | nei | K |
| GET | /bank/transaction/comment | internal | fra spec | Kommentar på en transaksjon | `bankTransactionId*`. Bare over terskel. Ikke employee. | nei | K |
| GET | /bank/reconciliation/paymentType | public | fra spec | Posteringstyper (gebyr, renter) | – | nei | K |
| GET | /ledger | public | fra spec | Valutasaldo i hovedboken (closingBalanceCurrency) | `accountId` er ett tall. Ikke postings. | nei | K |
| GET | /ledger/internal/general/sums | internal + udok | fra UI-kode | IB, endring og UB i NOK og valuta for mange kontoer | `accountIds`. Datoparametrene (`dateFrom`, `dateToExclusive`) står bare i UI-koden. Foretrekk /balanceSheet. | nei | K |
| GET | /ledger/paymentTypeOut | public | fra spec (BETA) | Hvilken bankkonto mva betales fra (showVatReturns) | `isInactive=false` | nei | K |
| PUT | /bank/reconciliation/{id} | public | fra spec | Lukke en måned ({id, version, isClosed:true}) eller sette saldo på manuell avstemming | Må være approvable. 409 betyr gammel version. Lukk kronologisk. | JA | K |
| PUT | /bank/reconciliation/internal/approve | internal | fra spec | «Godkjenn og lukk» fra UI | `accountId*`, `startDate`. Velg én metode etter test. | JA | K |
| POST | /bank/reconciliation | public | fra spec | Manuell avstemming (type MANUAL) for kontoer uten feed | Ikke idempotent. Sjekk med GET først. | JA | K |
| PUT | /bank/reconciliation/internal/autoposting/suggestions/acceptAll · /acceptGroup · /{id}/accept · /{id}/reject | internal | fra spec | Godta Tripletex' forslag | acceptGroup tar forslags-id-er (`id=`), ikke scenario. **Fører bilag.** | JA | K |
| PUT | /bank/reconciliation/internal/match/updateSuggestions | internal | fra spec | Godkjenne eller avvise ventende matchforslag | `approve*`. Body er intern ReconciliationMatch fra /internal/match. | JA | K |
| POST | /bank/reconciliation/match | public | fra spec | MANUAL/ADJUSTMENT for enkeltposter | Aldri bare på beløpslikhet | JA | K |
| PUT | /bank/reconciliation/match/:suggest | public | fra spec | Kjøre automatisk matching på nytt | Lager forslag | JA | K |
| PUT | /bank/reconciliation/internal/export/pdf · /export/xlsx | internal | fra spec | Tripletex' egen avstemmingsrapport (APPROVED) og liste over åpne poster (OPEN_TRANSACTIONS) | `actionType=FileDownload`. **Aldri SendEmail og aldri emailAddresses.** | JA* | K |

## 5. Bilagskontroll A og B (punkt 4–10 og riktig mva-behandling)

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| GET | /advancedVoucher/internal/legalVatTypes | internal | fra spec | Lovlige koder per konto og dato | `dates*`, `accountIds*`. **`fields=dates(date,accounts(accountId,vatTypeIds))`** | nei | K |
| GET | /incomingInvoice/internal/vat/legalVatTypes | internal | fra spec | Fallback, én dato | `date*`, `accountIds*`. Feltet heter `legalVatTypeIds` her. | nei | K |
| GET | /incomingInvoice/internal/{voucherId} | internal | **K0: 403** | Fakturahode, anomalyFindings (VAT_CODE), anomalyCheck | Ta med `anomalyFindings(id,…)` for å kunne lukke dem. Aldri changedByEmployeeId, attestationActions eller lookupData. | nei | K |
| GET | /incomingInvoice/internal/originalOrderLine/list/{voucherId} | internal | fra spec | EHF-linjer med kategori og sats | Hold orderLineType=ROUND_OFF utenfor | nei | K |
| GET | /incomingInvoice/internal/{voucherId}/changes | internal | **K0: 403** | Endringslogg med action-tekst | `fields=action,timestamp,changeType` | nei | K |
| GET | /document/{id}/content | public | fra spec (BETA). Testet for rapport-PDF. | EHF-XML (TaxSubtotal, IssueDate, selgers og kjøpers org.nr.), PDF-vedlegg, kvittering, modulens PDF | `download=true`. Binært, så egen fetch. Tolk bare skatte-, dato- og org.nr.-feltene i minnet. Maks ca. 4 kall parallelt. | nei | K/B |
| GET | /ledger/voucher/{voucherId}/pdf · /ledger/voucher/{id} | public | fra spec | Bilagsbilde til skjønnsvurdering, og detaljer før retting (version) | Bare for flaggede bilag, innenfor PDF-budsjettet. Leses i minnet, aldri siteres. | nei | K |
| GET | /invoice/{id} · /product · /invoice/settings | public · public · internal | fra spec | Originalfaktura med orderLines, produktets kode, fakturagebyr (fixedInvoiceFee) | – | nei | K |
| GET | /asset/{id}/postings | public | fra spec | Tilgang og avgang per anlegg | `dateFrom` og `dateToExclusive`. **Standardverdien er i dag, så oppgi alltid begge.** | nei | K |
| GET | /documentArchive/asset/{id} · /documentArchive/customer/{id} | public | fra spec (BETA) | Dokumentasjon for kapitalvarer og eksport | `periodDateFrom/To` | nei | K |
| GET | /vatReturns/{id} | internal | testet K0 2026-09-24 | Rapporterte linjer per standardCode for leverte terminer (lesevariant av ET1) og for utkastet | `id` = vatReturns2022Id fra status/list. **Kall uten fields eller med `fields=*`.** Eksplisitte fields på vatGroups eller lines (også `vatGroups(*)`) tømmer linjene og gir name og summer = null. Toppnivåfelt som `totalAmountVatToPay` går fint. Linjene har `vatType{id,url}`, så nummeret hentes via /ledger/vatType. Kode 86/87/88/89 gir to linjer (rate negativ, `isReversable=true` = motposten). Beløpene er hele kroner avkortet mot null. Grunnlag for kode 1/3 = −ledger.amount. `changes(changeType,timestamp)` virker. Svaret inneholder altinnMetadata{id,url}, men hent aldri createdInfo eller partyId. | nei | K |
| PUT | /ledger/voucher/{id} | public | fra spec | Rette koden på et manuelt bilag i åpen termin | Hele bilaget med version og linjer med row≥1. Linjer med row 0 blir laget på nytt. Påstanden om 422 i perioder med avstemt kontoutskrift er **ikke verifisert**. | JA | K |
| POST | /ledger/voucher | public | fra spec | Nytt, riktig bilag etter tilbakeføring | Bare brutto, sum 0, row≥1. Ikke manuelle 27xx-linjer. | JA | K |
| PUT | /supplierInvoice/voucher/{id}/postings | public | fra spec (BETA) | Erstatte debetlinjene på en leverandørfaktura, eventuelt flytte datoen | `id` = bilags-id. **`sendToLedger` er false som standard.** `voucherDate` flytter bilags- og fakturadato. | JA | K |
| PUT | /anomalies/{id}/:changeVatCode | internal | fra spec | Bytte kode via avviksmodulen | `clientCompanyId*`, body {vatNumber}. Id-typen (anomali eller aggregert) er tvetydig og må testes. | JA | B |
| PUT | /anomalies/status · POST /anomalies/{anomalyId}/comments | internal | fra spec | Sette RESOLVED/ARCHIVED med begrunnelse | Items {companyId (klient), anomalyIds (= AggregateAnomaly.anomalyId)} | JA | B |
| PUT | /incomingInvoice/internal/{voucherId}/anomalyFindings/{findingId}/:setUserStatus | internal | fra spec | Lukke Tripletex' egne fakturafunn | `userStatus*` | JA | K |
| PUT | /ledger/vatType/createRelativeVatType | public | fra spec | Relativ kode for forholdsmessig fradrag | `name` (maks 8 tegn), `vatTypeId`, `percentage`, alt i query | JA | K |

## 6. Avstemmingsmodulen (VAT og BALANCE)

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| POST | /vat/reconciliation/context | internal | testet (201, idempotent) | Opprette eller hente mva-avstemmingen for terminen | Body {customerId (kunde-id), year, term, vatReportType:"GENERAL_INDUSTRY"/"PRIMARY_INDUSTRY"} | JA | B |
| GET | /vat/reconciliation/{id}/overview | internal | testet K0 2026-09-24 (før og etter levering) | Linjer per vatTypeId: basis, ledgerData, ledgerDataAtPreviousReconciliation, reportedData, taxAdminData, difference | Krever at avstemmingen finnes (nye terminer har ingen, og context-POST er ikke testet i K0). **Før levering:** basis og ledgerData er fylt ut, og reported, taxAdmin, difference og prev er null. Σ ledgerData = vatTermAmount før levering og = altinnPaymentAmount etter. Fortegnet viser bidraget til beløpet å betale (utgående +, fradrag −), og en fradragslinje kan være + ved netto kreditnotaer. Beløpene er hele kroner avkortet mot null. `vatTypeId` er den globale vatType-id-en, ikke mva-koden. Kode 86 gir to linjer med samme vatTypeId. `ledgerDataAtPreviousReconciliation` fylles først ved COMPLETED. `difference` er null før levering og = ledger − reported når taxAdmin er null. Om difference tar med taxAdmin, er uavklart, så regn begge avvikene selv. 403 hvis kunden ikke også er delegert klient. | nei | B |
| GET | /vat/reconciliation/{id}/status · /statusList/{id} · /reportTypes | internal | status og statusList testet K0 2026-09-24 | VatStatus sett fra byrået. Egnet til polling av mange klienter. | Eksplisitte fields uten employee | nei | B |
| GET | /vat/reconciliation/uri | internal | fra spec | Relativ sti til avstemmingssiden (lenke til Sjur-økta) | `term`, `year`, `vatReportType`. **Ingen fields.** Sett https://tripletex.no foran. | nei | K (proxy) |
| GET | /accountingOffice/reconciliations/{id}/validations | internal | testet (K0 2026-09-24: tom liste) | Hva som blokkerer :complete, og riktig referenceId | `fields=referenceId,message`. **K0:** listen er tom på alle mva-avstemminger (fullført, åpen, og levert men ikke synket) og på en BALANCE i DRAFT. Tom betyr altså ikke «avstemt», og kallet gir ingen referenceId før levering. Om det gir referenceId ved avvik etter levering, er uavklart. | nei | B |
| GET · POST | /accountingOffice/reconciliations/{id}/comments | internal | testet (201). GET testet K0 2026-09-24. | Lese eller skrive kommentar per linje | Body {referenceId*, comment ≤1024}. Feil referenceId gir 201 uten at kommentaren vises. GET: `fields=id,reconciliationId,referenceId,createdAt,comment`, aldri createdBy. Svarnøkler: id, version, url, reconciliationId, createdAt, createdBy, referenceId, comment. referenceId for mva-linjer, BALANCE-linjer og 2740 er **ikke verifisert** (krever «test»-metoden, K0 test 2). Kode 86 har to linjer med samme vatTypeId. Feriepenger bruker kontonummer, og en kommentar lagret på konto-id finnes også. | JA (POST) | B |
| POST | /accountingOffice/reconciliations/{id}/comments/list | internal | fra UI-kode | Alle kommentarer i ett kall | Array av {referenceId, comment}. Test med én først. | JA | B |
| DELETE | /accountingOffice/reconciliations/{id}/comments/{commentId} · /attachments/{attachmentId} | internal | fra UI-kode | Rydde kommentarer og vedlegg som havnet på feil referenceId | – | JA | B |
| GET · POST | /accountingOffice/reconciliations/{id}/attachments | internal | POST testet (PDF), GET testet K0 2026-09-24 (tom liste, skjema ukjent) | Vedlegg per linje (kundens kildedokumenter og Tripletex-eksporter) | `referenceId*` (query), multipart `file`. GET før POST gir idempotens. Ikke uploadedBy. | JA (POST) | B |
| PUT | /accountingOffice/reconciliations/{id}/:complete | internal | testet (mva på en testklient, T1–T3 og lønn). Ikke BALANCE. | Fullføre: status COMPLETED, låst, PDF i document | 422 gir {referenceId, message} i validationMessages. Uprøvd med taxAdminData=null. | JA | B |
| PUT | /accountingOffice/reconciliations/{id}/:generatePdfReport | internal | fra spec | Returnerer det **arkiverte** dokumentet og genererer bare hvis det mangler (avstemmingsmodul.md sier feilaktig at rapporten lages på nytt) | Ingen body (body gir 400) | JA* | B |
| POST | /accountingOffice/reconciliations/{id}/:downloadCustomizedPdfReport | internal | fra spec | **Bare for balanseavstemming.** Andre typer gir 400. Uttrekk uten attestasjon. | {accountIds (konto-id-er, ikke kontonumre), includeComments, includeAttachments, includeDecimals} | JA* | B |
| PUT | /accountingOffice/reconciliations/{id}/:unlock | internal | fra spec + UI-kode | Gjenåpne fullført avstemming (korrigert melding) | Egen bekreftelse | JA | B |
| PUT | /accountingOffice/reconciliations/{id}/:setRequiresControl | internal/udok | fra UI-kode | Kreve kontroll (fire øyne) | Valgfritt | JA | B |
| GET | /accountingOffice/reconciliations/{id}/control | public | fra spec | Kontrollhistorikk (RECONCILED, CONTROL_REQUESTED, CONTROLLED) | `fields=type,timestamp`. Ikke employee. | nei | B |
| POST | /balance/reconciliation/context | internal | fra spec (+ UI-kode) | Opprette eller hente balanseavstemmingen for **måneden** | {customerId, year, term}. For BALANCE er `term` = måned (K0: BALANCE er månedlig), så én mva-termin gir to kall (mnd 2n−1 og 2n). Om kallet er idempotent, er ikke verifisert. Les periodsOverview(type=BALANCE) først, fordi de fleste månedene allerede finnes. | JA | B |
| GET | /balance/reconciliation/{id}/table | internal | testet K0 2026-09-24 | Linjer per konto: balanceIn/Change/Out, stored*, documentedBalance, difference, status (NOT_RECONCILED/RECONCILED/REJECTED/CONTROLLED/IGNORED), availableStatuses, errors, attachedVouchers, autoReconciled(FromTypeName), inactiveAccounts | Svaret er {period, groups[{displayName, lines[]}], inactiveAccounts[]}. Linjene har ingen egen id (nøkkelen er `accountId`). **Nestet fields virker bare med `*` først:** `fields=*,groups(*,lines(accountId,displayName,balanceIn,balanceChange,balanceOut,documentedBalance,difference,status,autoReconciled,autoReconciledFromTypeName))`. Da slipper du reconciledBy/controlledBy (med `fields=*` er de {id,url}). Uten `*` først blir groups tomme. balanceOut = /balanceSheet UB med dateTo = periodens endDate (eksklusiv), og stoppregelen holder. Med: klasse 1–2-kontoer med saldo eller bevegelse. **Auto:** 2740 først etter VAT :complete (begge terminmånedene). 2600/2610/2770/2771 etter at lønnsavstemmingen er fullført. 2700–2710 aldri. 19xx blir **ikke** auto når banken lukkes: da er documentedBalance = saldo og difference = 0, men status NOT_RECONCILED. | nei | B |
| PUT | /balance/reconciliation/{id}/table/{accountId} · /table/list | internal | fra UI-kode (K0: rowId = accountId, ikke skrevet) | Sette documentedBalance og status (RECONCILED, eller IGNORED for statiske og inaktive kontoer) | **rowId = `line.accountId`** (UI-kode). Body = linjen fra GET med `reconciledBy: null, controlledBy: null` og bare de nødvendige endringene. `table/list` tar en array av slike linjer og svarer med `values[]`. `fields=accountId,documentedBalance,difference,status`. GET på disse stiene gir HTTP 400 (code 4000) med meldingen «405 Method Not Allowed», så feilhåndteringen må lese meldingen. Prøveskriving gjenstår (K0 test 15). | JA | B |
| GET | /balance/reconciliation/{id}/account/{accountId}/vouchers | public | testet | Bilag, kommentarer og vedlegg bak en balanselinje | `fromDate`, `toDateExclusive`. 403 hvis tokenet ikke også har delegert klienttilgang. | nei | B |
| PUT | /balance/reconciliation/{id}/:reopen · /:complete | internal | fra spec | Gjenåpne eller fullføre BALANCE (alternativt kall) | Egen bekreftelse | JA | B |
| POST | /balance/reconciliation/annual/context | public | fra spec | ANNUAL_BALANCE ved årsslutt | {customerId, year} | JA | B |
| PUT | /accountingOffice/reconciliations/documentationFolderId | internal | fra spec | Hente eller opprette klientens dokumentasjonsmappe i Tripletex | `customerId*`. Kan opprette mappe. | JA | B |

## 7. Mva-melding: utkast, merknader og innsending

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| POST | /vatReturns | internal | fra spec | Opprette og beregne meldingen. Lukker mva-terminen og bokfører trolig oppgjørsbilaget. Det siste er antatt, ikke dokumentert. | Body {year, term, reportType}. Status går til INSTANCE_CREATED (Altinn-instans), så kallet kan kreve ID-porten. **Sjur oppretter i UI til kallet er testet.** | JA | K |
| GET | /vatReturns/>vatTerm | internal | testet K0 2026-09-24 | Utkastet og tidligere meldinger med linjer. **Gir et fullt beregnet utkast også før «Opprett»** (id=0, NOT_STARTED, voucher=null, linjer per standardCode). For en levert termin gir den meldingen som ble levert. | `year`, `vatTerm` (ikke `term`, som gir 500), `reportType` (valgfri). **Uten fields eller med `fields=*`** (samme felle som /vatReturns/{id}). Når id=0 er `isPaid=true` og `remainingAmountVatToPay=0` meningsløse og ignoreres. Termin uten posteringer gir tomme vatGroups og total 0. Utkastet beregnes fra hovedboken når kallet gjøres. | nei | K |
| POST | /vatReturns/{id}/validate | internal | fra spec | Skatteetatens validering (SUCCESS/INVALID/WARNING/MISSING_INFORMATION) | Ingen fields-parameter, så svaret filtreres lokalt. Krever trolig ID-porten. Ved 401/403 skjer valideringen i Sjurs økt. | JA* | K |
| PUT | /vatReturns/vatSpecificationLine/{id}/:modifyComment | internal | fra spec | Merknad på en linje i utkastet (strukturert eller fritekst) | Body {comment, isStructured, vatReturnsId}. Om `comment` skal være technicalName eller title er ukjent. Kallet motsier docs. Meldingsnivå kan ikke settes via API (userComment er readOnly). | JA | K |
| GET | /vatReturns/comment · /vatReturns/comment/>all | public | fra spec (BETA) | Gyldige strukturerte merknader per mva-kode, med expectedSign og deliveredSign | Ingen vatCode-parameter, så svaret filtreres lokalt. Caches per kjøring. | nei | K |
| POST · GET | /vatReturns/{id}/attachment (+ /list) · /vatReturns/{vatReturnsId}/attachments | internal | fra spec | Vedlegg til meldingen. **Går til Skatteetaten.** | Bare dokumenter Sjur har sett. Aldri personopplysninger. | JA (POST) | K |
| PUT | /vatReturns/{vatReturnsId}/{attachmentId}/:delete | internal | fra spec | Fjerne feil vedlegg før sending | – | JA | K |
| PUT · POST | /vatReturns/{id}/:reverse · /vatReturns/{id}/:delete | internal | fra spec | Angre en opprettet melding som ikke er sendt (reversere oppgjørsbilaget eller slette) | Aldri på en sendt melding | JA | K |
| POST | /vatReturns/{id}/:manuallyDelivered | internal | fra spec | Markere som levert når Sjur har levert i Altinn utenfor Tripletex | Bare etter at Sjur har sagt det | JA | K |
| POST | /vatReturns/{id}/isFeedbackProvided · /getFeedback | internal | fra spec | Tilbakemelding eller kvittering når status henger på WAITING_FOR_REPLY | getFeedback oppdaterer status og kvittering (ingen regnskapsendring). Kan kreve ID-porten. | JA* / JA | K |
| GET | /vatReturns/{id}/xml | internal | fra spec | XML til arkivet | application/xml. rawRequest tåler bare JSON, så egen fetch. | nei | K |
| GET | /altinn/instance/{id} | internal | fra spec (BETA) | Altinn-arkivreferanse | `fields=altinnId,instanceGuid`. Ikke createdInfo. | nei | K |
| GET | /vatReturns/vatDeliveryStatusUpdate/{id} | internal | fra spec | Hvilken termin en leveringsoppdatering gjelder | Sjelden nødvendig | nei | K |

## 8. Skattekonto og betalingsgrunnlag (punkt 12 og 16)

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| GET | /claimsAndPayments | internal | testet K0 2026-09-24 | Krav på skattekontoen med status (åpent eller oppgjort) | `year*`. `fields=claimIdentifier,claimType,claimGroup,claimDescription,periodDescription,amount,outstandingAmount,rent,dueDate,claimCreatedDate,instalments(dueDate,amount,outstandingAmount,kid)`. Hent aldri accountNumber, iban, swiftBic eller bankInformation. Gir **alle krav med aktivitet i året, også oppgjorte**, men ikke saldo eller innbetalinger. `year` følger claimCreatedDate, så hent terminens år og året etter. Åpent krav: outstandingAmount ≠ 0. Mva: filtrer **lokalt** på `claimGroup == "Merverdiavgift"` (parameteren ignoreres), uten hvitliste over claimType. Sett: mvaMelding, konteringMvaÅBetale, konteringTilgodeMva, konteringKorrigertTilgodeMva, fastsettingsrenterMva11_2, forsinkelsesrenterMva. Termin fra periodDescription («<mnd> - <mnd> NN, ÅÅÅÅ»). En endringsmelding gir flere krav per termin, og renter har egne KID-er. For tilgode er dueDate utbetalingsdatoen. Sporadisk 500 (code 1002): 3 nye forsøk med 1–2 s pause. Forutsetter hasSystemUser=true, ellers er status «ukjent». | nei | K |
| GET | /claimsAndPayments/byClient | internal | **K0: 403** (code 1000 «KB-005», klient med isAgent=false) | Samme kall fra byrået | Bruk klientkontekst. customerCompanyId som customerId gir 404. Krever trolig agent- eller regnskapsførersystembruker i Altinn (usikkert). | nei | B |
| GET | /vatReturns/{id}/paymentInfo | internal | testet K0 2026-09-24 | **Betalingsgrunnlaget**: KID, Skatteetatens konto, beløp og forfall etter levering | `fields=kid,account,amount,dueDate`. Svarer for alle leverte terminer, også tilgode (negativt beløp). amount = totalAmountVatToPay. dueDate = meldingens forfall. **KID er unik per termin** (den gjelder også tilleggskrav fra endringsmelding) og = KID på mvaMelding-kravet i claimsAndPayments. Objektets id ≠ vatReturns-id. KID og konto brukes bare i minnet. | nei | K |
| GET | /vatReturns/{vatReturnsId}/paymentHistory | internal | testet K0 2026-09-24 (bare hint: tilgode vises som OPEN_POST selv når Skatteetaten har gjort opp) | Betalinger registrert på terminen, og restbeløp | **`fields=remainingAmountToPay,transactions(type,paymentType,date,amountNegative,isReversed,postingId,voucherId,voucherNumberAsString)`**. Aldri description eller text1–3. | nei | K |
| GET | /ledger/posting/vatPaymentStatusUpdate/{id} | internal | fra spec | Hvilken termin en betalingspostering oppdaterte | 404 er normalt for manuelle bilag | nei | K |

## 9. Betaling (Sjurs «betaling opprettet» og punkt 17)

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| GET | /bank/globals | internal | fra spec | Bankintegrasjon (remitPaymentType OFF/NETS/AUTOPAY/BOTH/ZTL) og betalingsrett for API-brukeren | Ikke loginEmployeeId eller actualEmployeeId | nei | K |
| GET | /bank/paymentWidget | internal | **K0: 403** (code 9000, hele betalingsfunksjonen er sperret for API-brukeren) | «Betal»-dialogen for mva: betalingstyper, beløp, dato, konto, låst KID | `scenario*=VAT_RETURNS_2022` (eller `VAT_RETURNS_2022_PRIMARY_INDUSTRY`), `scenarioId*` = vatReturns2022Id. privacy.js maskerer bankAccount i utskrift, så råverdien brukes bare i minnet. | nei | K |
| POST | /bank/paymentWidget | internal | fra spec (ikke testet; GET gir 403, så vei A er ute til Sjur har avklart betalingsrollen) | **Opprette mva-betaling** (AutoPay eller ZTL). Legges til godkjenning. | Body = widgeten fra GET, med selectedPaymentType AUTOPAY/ZTL. **Aldri POSTING_RULE eller NOT_PAID**, for da bokføres betalingen straks. Svaret gir ingen id. Ta et øyeblikksbilde av betalingslisten før kallet og sammenlign etterpå. Eksplisitt ja per betaling. | JA | K |
| GET | /bank/payment · /bank/payment/{id} | internal | **K0: 403** (code 9000) | Betalingsoversikten | Ingen filtre, så bla gjennom og filtrer lokalt: `isSalary=false`, `paymentCategory=VAT`. `fields=id,paymentSource,statusId,isFinalStatus,isSalary,paymentCategory,paymentDate,amountCurrency,kid,paymentTypeId,urlForVoucher,expired,numberOfApprovers,numberOfApprovedInBank`. Aldri creditor*, acceptors eller receiverLink. | nei | K |
| GET | /bank/payment/statuslog/{id} · /bank/payment/info/statuses/counts | internal | fra spec | Hendelser (APPROVED, REJECTED, INSUFFICIENT_FUNDS, PAID, BOOKED) og billig telling av betalinger som venter | `paymentSource*`. Ikke actionCreator. | nei | K |
| GET | /bank/ztl/payment/internal · /ztl/account | internal | fra spec | ZTL-betalinger med datofilter og tilgjengelig saldo | `fromDate`, `toDate` (ekskl.) | nei | K |
| PUT | /bank/payment/{id} | internal | fra spec | Endre dato på en betaling som ikke er godkjent | Sjekk isDueDateUpdatable. isKidUpdatable=false for mva, så feil KID betyr slett og opprett på nytt. | JA | K |
| DELETE | /bank/payment/{id} · /vatReturns/paymentPosting/{paymentType}/{id}/:delete | internal | fra spec | Fjerne feil betaling eller feil registrering | Egen bekreftelse | JA | K |

## 10. Etterarbeid: lås, arkiv og oppfølging (punkt 14, 15, 17)

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| GET | /advancedVoucher/internal/{voucherId} | internal | fra spec | `metadata(accountingLockedThroughDate,vatLockedThroughDateGeneral,vatLockedThroughDatePrimary)`. Feltnavnet er verifisert i spec. Bekrefter mva- og regnskapslås. | voucherId = oppgjørsbilaget. **Aldri `force=true`.** | nei | K |
| PUT | /ledger/accountingPeriod/:check | internal | fra spec | «Review accounting period» (markPeriodAsChecked). Setter trolig **bare et kontrollstempel, ikke en lås**. | Brukes ikke som periodelås | JA | K |
| GET | /todoList/periodOverviewsSection | internal | fra spec | Lenke og status for periodelåsing i Sjur-økta | `fromDate*`, `toDate*`. Ikke accountManagerName. | nei | B |
| GET | /event | public | **IKKE BEKREFTET** (BETA; hendelsesnavn bare live) | Webhook for levert eller betalt | Payload har bare company/year/term. Polling brukes i stedet. | nei | K |


## 10a. Dokumentasjon og kvitteringer (kartlagt 24.09.2026)

| Metode | Sti | Kilde | Status | Formål | Viktige parametere / fields | Skriver? | Kontekst |
|---|---|---|---|---|---|---|---|
| GET | /vatReturns/{id} | internal | testet 24.09.2026 | `receiptId`, `closedDate`, `altinnMetadata(id,altinnId,partyId,instanceGuid)` for levert melding | `fields=id,status,receiptId,closedDate` | nei | K |
| GET | /document/{receiptId}/content | public | **403 code 9000** for API-brukeren (24.09.2026) | Kvittering for innsendt mva-melding (PDF) | Binært svar. Samme sperre som betaling. | nei | K |
| GET | /vatReturns/{id}/xml | internal | **403 code 9000** | Selve mva-meldingen | – | nei | K |
| GET | /altinn/instance/{id} | internal | testet 24.09.2026 | Altinn-instansen (id, altinnId, partyId, instanceGuid). Ingen dokumentlenker. | – | nei | K |
| GET | /vatReturns/{id}/paymentHistory | internal | testet 24.09.2026 | Oppgjørsbilag og betalinger mot meldingen (for 2740) | Ikke hent navnefelt | nei | K |
| GET | /voucherInbox/inboxFiltered | internal | **403 code 9000** | Innboksen med fakturanr., selgers org.nr. og Tripletex' dublettmerking | Reserve: /supplierInvoice gir også bilag som ikke er bokført (voucher.number = 0, tempNumber), som fanget purringen i piloten | nei | K |
| PUT | /bank/reconciliation/internal/export/pdf | internal | fra spec | Tripletex' egen PDF av bankavstemmingen (vedlegg på 19xx) | Eksport, men PUT-verb: testes én gang etter ja | (eksport) | K |
| GET | /ledger/balanceSheet/pdf · /ledger/internal/general/pdf · /ledger/balanceReport/pdf | internal | fra spec | Tripletex' egne PDF-er (saldobalanse, hovedbok, balanse) som vedlegg | – | nei | K |
| PUT | /accountingOffice/reconciliations/documentationFolderId | internal | fra spec | Hent eller opprett dokumentasjonsmappa for en klient | Kan opprette mappe, så krever ja | JA | B |
| POST | /accountingOffice/reconciliations/{id}/attachments?referenceId= | internal | testet 23.09.2026 (PDF) | Laste opp dokumentasjon på en linje | multipart, felt `file` | JA | B |
| POST | /vatReturns/{id}/attachment(/list) | internal | fra spec | **Ikke bruk til dokumentasjon**: vedlegget følger mva-meldingen til Skatteetaten | – | JA | K |
| GET | /claimsAndPayments | internal | testet 24.09.2026 (to klienter) | Krav og betalinger på skattekontoen: claimGroup, claimType, amount, outstandingAmount, rent, dueDate, periodDescription | `year*`. Hent terminens år, året før og året etter. 500 av og til: nytt forsøk. | nei | K |

## 11. Kall Claude aldri gjør

| Sti | Grunn |
|---|---|
| POST /vatReturns/{id}/:send · /:resend | Sjur sender selv med ID-porten |
| POST /vat/reconciliation/{id}/syncWithTaxAdmin | Krever ID-porten-økt. Sjur synker i UI. Spec: ingen body, svar NO_DATA eller SYNCHRONIZED. |
| PUT /bank/payment/:approve | Claude godkjenner aldri betalinger (redirect til BankID) |
| PUT /accountingOffice/reconciliations/{id}/:control | Claude kontrollerer ikke eget arbeid (fire øyne) |
| PUT /bank/reconciliation/internal/export/* med actionType=SendEmail | Sender e-post |
| GET /incomingInvoice/internal/anomalyExport/{companyId} | Har ikke fields-parameter og returnerer alltid kontonummer, KID og navn for hele historikken. Droppes. |
| GET /enhetsregisteret | Overflødig (Brreg-hjelperen dekker behovet) og returnerer email og address |
| Tripletex-MCP `vatReturnApi_*`/`taxDebtApi_*`/`outgoingPaymentApi_*` | Tilhører ReAI-connectoren, ikke Tripletex. Merknaden i api-v2-oppgaver.md om dette ser feil ut. |

Connector-kall som bare er reserve (etter CLAUDE.md-unntaket): `search_supplier_invoices`/`get_supplier_invoice` når /incomingInvoice/search gir 403 og /supplierInvoice mangler ny flyt. `lookup_company_in_brreg` er ikke nødvendig, fordi leverandor.js dekker behovet. Begge er **IKKE BEKREFTET** lokalt. Svarene kan inneholde navn på attestanter, og de skal aldri gjengis.

---

## Ikke funnet

| Hva | Søkt i | Konsekvens |
|---|---|---|
| Oppgjørsdata fra Vipps, Stripe, Zettle, Shopify, Klarna eller kassesystem | Begge spec-ene (vipps, stripe, zettle, shopify, settlement, payout, kasse …) og `npm run finn` | F2.5–F2.7 og MX16 bygger på hovedbok, bank og kundens oppgjørsrapport. ZTL er bankintegrasjonen, ikke Zettle. |
| Egen avstemmingstype for «forutsetninger» eller bank | Reconciliation.type-enum, periodsOverview.reconciliationGroup | Funn legges som kommentarer i VAT- eller BALANCE-avstemmingen. Bank lukkes i klientens egen bankavstemming. |
| referenceId-konvensjon (mva-linje, BALANCE-linje, 2740, hele terminen) | Skjemaer, avstemmingsmodul.md, K0 (/validations er tom før levering) | Krever Sjurs «test»-kommentar (K0 test 2). rowId er løst: rowId = accountId. |
| Tolletatens innførselsdata | Spec-ene (customs, toll, declaration), finn | MI2 krever en fil fra Sjur |
| Leverandørens mva-status i API v2 | /company/brreg/lookup, VatSettings, anomalyExport | Brreg via leverandor.js. Brreg har ikke historikk for avregistrering. |
| Kapitalvareregister eller justeringsgrunnlag | capital, justering, adjustment | kapitalvarer.md i klientmappa, og vedlegg i BALANCE |
| Tolldeklarasjon for utførsel | customs, toll | EX3 gjøres av Sjur (vedlegg, dokumentarkiv, lokal mappe) |
| Filter på opprettet/endret-tid for bokførte bilag og posteringer | Alle ledger-, voucher- og posting-stier | Bare />nonPosted?changedSince. ET1 fungerer som port for full skanning. |
| Saldo og historikk for skattekontoen, og klientens kontonummer for tilbakebetaling | skattekonto, taxAccount, claimsAndPayments, refund | /claimsAndPayments (testet K0) gir krav med outstandingAmount, men verken saldo eller innbetalinger. Kontonummeret må Sjur sjekke hos Skatteetaten. |
| Låse regnskapsperiode via API | accountingPeriod, lock, close | Sjur låser i UI. :check er ikke en lås. |
| Merknad på meldingsnivå via API | /vatReturns*, CommentInput | Bare linjenivå (:modifyComment) |
| Direkte UI-lenke til mva-meldingen | uri/url i spec-ene | Kandidat: TodoListVat.url. /vat/reconciliation/uri gir avstemmingssiden. |
| PDF av selve mva-meldingen | pdf, receipt under /vatReturns | XML + receiptId (antatt å være et dokument-id) |
| Filtre på /bank/payment, /otherPostingOverview og /internal/invoiceOverview | Parameterlister i intern spec | Filtreres lokalt, eller filtrene leses fra UI-koden |
| Kundereskontro-sammendrag per kunde (som supplierSubLedger) | customerSubLedger, >customerBalance | Summer openPost lokalt |
| Kjøretøyklasse per bil | vehicle, asset | Legges i klientprofil.md |
| Bilagsdato i /incomingInvoice/search | Response-skjemaet | Kobles via voucherId mot bilagskartet |
| Mva-KID før levering | kid i /vatReturns*, widget | K0: KID er unik per termin og kan ikke lagres i profilen. Den hentes per termin etter levering fra `/vatReturns/{id}/paymentInfo`. |
| Kobling fra leverandørkreditnota til originalfaktura | SupplierInvoice, /incomingInvoice/internal/* | Heuristikk (invoiceHistoryByVendor, beløp) |

## Må testes lesende før bruk (kalibrering K0, én gang per byrå)

K0 ble kjørt 2026-09-24 på kalibreringsklienten, med bare GET-kall. Detaljene står i `kalibrering.md`, og de generelle funnene om modulen står i `docs/avstemmingsmodul.md` (seksjon «Kalibrering K0»). `kalibrering.json` bygges fra `kalibrering.md`. Utfall: **BRUK**, **FALLBACK**, **MANUELT** eller **IKKE TESTET**.

1. `/vat/reconciliation/{id}/overview` på en åpen termin: finnes ledgerData og basis før opprettelse og levering? Er fortegnene som etter levering?
   - **BRUK (høy).** basis og ledgerData finnes før levering, og Σ ledgerData = vatTermAmount. Fortegnet er bidraget til beløpet å betale, med samme konvensjon på leverte og ikke-leverte terminer. Krever at avstemmingen finnes.
2. referenceId for mva-linje (vatTypeId?), BALANCE-linje (konto-id?) og 2740. Metode: /validations, deretter «test»-kommentar skrevet av Sjur i UI, deretter GET comments.
   - **MANUELT (middels).** /validations er tom før levering. «Test»-kommentaren fra Sjur gjenstår (IKKE TESTET).
3. `/balance/reconciliation/{id}/table` på en eksisterende avstemming: hva er rowId? Blir 19xx autoReconciled når bankavstemmingen lukkes? Følger BALANCE-perioden mva-terminen?
   - **BRUK (høy).** rowId = accountId. 19xx blir ikke autoReconciled: documentedBalance = saldo og diff 0, men status NOT_RECONCILED. BALANCE er **månedlig**.
4. `/ledger/posting/openPost` med historisk dato mot `/internal/supplierSubLedger/summary?openPostingsAsOfDate` og `/balanceSheet`: regnes poster som ble lukket etter D som åpne?
   - **BRUK (høy).** Ja, og Σ = UB. supplierSubLedger er ikke fasit, fordi openAmount er dagens restbeløp.
5. `/vatReturnsOverview/vatTermAmount`: fortegn, målt mot altinnPaymentAmount for en levert termin.
   - **BRUK (høy).** + = å betale. = altinnPaymentAmount. Tall også for terminer som ikke er opprettet. Svarer 0 uten feil ved feil parametere.
6. `/ledger/posting`: har systemgenererte 27xx-linjer (row 0) vatType? Hva betyr isAmountVatClosed? Styres terminen av linjedato eller bilagsdato? Godtas nestede felt `voucher(changes(...))`?
   - **BRUK (høy).** vatType er `"0"` (streng). isAmountVatClosed = kodet linje i levert melding. Terminen følger posting.date. changes godtas. fullResultSize er ikke et totalantall.
7. `/vatReturns/validateCreate`, `/vatReturns/>vatTerm` og `/vatReturns/{id}` på en levert termin.
   - **BRUK (høy).** `>vatTerm` gir utkastet før Opprett. Kall uten fields eller med `fields=*`.
8. `/claimsAndPayments?year=`: svarer kallet med API-tokenet? Hvilke verdier har claimType for mva?
   - **BRUK (høy)** i klientkontekst. Filtrer på claimGroup «Merverdiavgift». Kallet gir også oppgjorte krav. byClient gir 403.
9. `/bank/reconciliation/internal/state`: svarer kallet med API-tokenet?
   - **BRUK (høy).** startDate er påkrevd, og fortegnet er verifisert. Brukes som supplement.
10. `/incomingInvoice/search`: gir kallet 403 (pilotbegrenset)?
    - **FALLBACK (høy).** 403 code 9000 på hele fakturaobjektet.
11. `/bank/paymentWidget` (GET) på en levert termin: betalingstyper og KID.
    - **FALLBACK (høy).** 403 på hele betalingsfunksjonen. KID hentes fra `/vatReturns/{id}/paymentInfo`, og den er unik per termin. Om API-brukeren kan få betalingsrolle, er MANUELT.
12. `/accountingOffice/reconciliations` med filtrene customerId, year, term og type.
    - **BRUK (høy).** Filtrene virker, men kontroller svaret lokalt. fullResultSize er bare en nedre grense.
13. `/addon/company/{id}`: hvilket id-begrep brukes?
    - **MANUELT (høy).** Kallet gir katalogen uansett id, så det strykes. Integrasjonene står i klientprofilen.
14. `/anomalies/context`: er modulen aktiv, og hva koster den?
    - **MANUELT (middels).** 403, så Sjur oppgir `anomalies_aktiv`.
15. Skrivekall som prøves én gang etter Sjurs ja: `:modifyComment` på én linje (technicalName eller title), PUT `table/{rowId}` på én linje, `comments/list`, lukking av én bankmåned (PUT isClosed eller internal/approve, velg én), og eventuelt `POST /vatReturns` på en testtermin.
    - **IKKE TESTET.** I tillegg: context-POST for VAT og BALANCE (idempotens, og overview før levering for nye terminer).
16. Holder én ID-porten-innlogging i Tripletex-UI på tvers av klienter i byråkontoen? (Påvirker flerklientøkta.)
    - **IKKE TESTET.** Kan bare observeres i UI av Sjur.

Tilleggstester i K0:
- `/ledger/accountingPeriod`: **BRUK**. isClosed, end er eksklusiv, låsing per år.
- `/company/settings/altinn`: **BRUK**, med `fields=altInnId`.
