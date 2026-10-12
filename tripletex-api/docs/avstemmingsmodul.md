# Avstemmingsmodulen (regnskapsbyrå) – interne API-kall

Kartlagt 2026-09-23 med silfer-tokenet på klient A og unikum-tokenet på klient B (samme modul, samme kall – bruk tokenet til byrået klienten tilhører). Ingen av kallene under står i
`openapi.json` (unntatt der det er merket «spec»). De er funnet ved å sonde med GET og ved å lese Tripletex-UI-koden
(`https://tripletex.no/page/ao-reconciliation/assets/index-*.js`, `altinn-sync-widget-*.js`). Tripletex kan endre dem
uten varsel – test med et lesende kall før bruk.

Metoder i UI-koden: `De(...)` = GET, `Nn(...)` = POST, `Gn(...)` = PUT.

## Grunnleggende

| Begrep | Verdi (eksempelklient) | Hvor |
|---|---|---|
| Byråkonto | Silfer AS, companyId 0 via silfer-tokenet (<byrå-id>) | Alle `/accountingOffice/*`-kall |
| Kunde-/klient-id | <kunde-id> | `customer.id` i modulen = id fra `/company/>withLoginAccess` |
| Klientens company-id (`contextId`) | <company-id> | `GET /accountingOffice/clients/{kunde-id}?fields=customerCompanyId` eller `whoAmI.companyId` i klientkontekst |

- `src/tripletex.js` blokkerer companyId 0 med vilje. Kall mot byråkontoen gjøres i egne skript med `authorization(0,'silfer')`.
- **`contextId` fra byråkontoen blir ignorert av API-tokenet** der kallet leser klientdata (A07-bestilling, `/ledger/account?contextId=`):
  du får byråets egne data. Kall slike ting fra klientens kontekst (Basic-auth companyId = kunde-id).
- 404 «Object not found» = stien finnes ikke. 405 «Method Not Allowed» = stien finnes med annen metode.
  422 «Expected number» = ordet ble tolket som `{id}`. Les alltid `validationMessages` – de forteller hva som mangler.
- Detaljkallene gir 403 for kunder tokenet ikke også har delegert klienttilgang til.
- `permissions/{kunde-id}` sier hva **API-brukeren** har tilgang til, ikke hva klienten har. klient D: `canAccessSalary=false`
  → lønnsbildene gir 403, selv om Eps har lønn (importert fra annet system). Context-POST gir likevel 201 og lager tomme
  avstemminger – ikke opprett lønnsavstemminger når `canAccessSalary=false`.

## Felles for alle avstemmingstyper

| Kall | Hva |
|---|---|
| `GET /accountingOffice/reconciliations?fields=id,year,term,type,status,startDate,endDate,customer(id,name,organizationNumber),document(id)&count=1000` | Alle avstemminger i modulen |
| `GET /accountingOffice/reconciliations/{id}` | Én avstemming. `status`: DRAFT, COMPLETED, CONTROLLED, ERROR, WARNING. `modifiable=false` = låst |
| `GET /accountingOffice/reconciliations/periodsOverview?customerId=&year=&type=` | Perioder og status per type (fields: `*,periods(*,reconciliation(id,status))`) |
| `GET /accountingOffice/reconciliations/{id}/validations` | Hva som blokkerer fullføring (`[{referenceId, message}]`). **Beste måte å finne riktig `referenceId` for kommentar/vedlegg** – les den før du kommenterer |
| `GET /accountingOffice/reconciliations/{id}/control` (spec) | Historikk: RECONCILED, CONTROL_REQUESTED, CONTROLLED |
| `GET/POST /accountingOffice/reconciliations/{id}/comments` | Kommentarer: `{referenceId*, comment}` (maks 1024 tegn) |
| `GET /accountingOffice/reconciliations/{id}/attachments` | Vedlegg |
| `POST /accountingOffice/reconciliations/{id}/attachments?referenceId=<ref>` (multipart, felt `file`) | Last opp vedlegg på en linje → 201 (testet 2026-09-23, PDF) |
| `DELETE .../{id}/attachments/{vedleggId}`, `DELETE .../{id}/comments/{kommentarId}`, `POST .../{id}/comments/list` | Slett vedlegg/kommentar, flere kommentarer (fra UI-koden, ikke testet) |
| `PUT /accountingOffice/reconciliations/{id}/:unlock` | Gjenåpne fullført avstemming (fra UI-koden, ikke testet) |
| `PUT /accountingOffice/reconciliations/{id}/:generatePdfReport` | Lag rapport på nytt (fra UI-koden, ikke testet) |
| `PUT /accountingOffice/reconciliations/{id}/control/:reconcile` (spec) | Logger RECONCILED. **Endrer ikke status** |
| `PUT /accountingOffice/reconciliations/{id}/control/:requestControl` (spec) | Be om kontroll. Body = array med ansatt-id-er |
| `PUT /accountingOffice/reconciliations/{id}/:complete` | **Fullfører**: COMPLETED, låst, lager PDF-rapport (`document`). Ved avvik: 422 med `{referenceId, message}` som må forklares med kommentar |
| `PUT /accountingOffice/reconciliations/{id}/:control` | Merk som kontrollert (ikke testet) |
| `PUT /accountingOffice/reconciliations/{id}/:setRequiresControl?requiresControl=true` | Krev kontroll (ikke testet) |
| `GET /accountingOffice/reconciliations/permissions/{kunde-id}` | `canAccessVat/Salary/Balance/Bank` |
| `GET /accountingOffice/clientOverview/context/{kunde-id}?year=` | `customerCompanyId`, mva-registrering, a-meldingsstatus per måned |
| `GET /accountingOffice/reconciliations/context` | Innlogget bruker i modulen |
| `GET /document/{id}/content` (spec) | PDF-rapporten |

- Opprettelse (`POST .../context`) er idempotent: samme kunde, år og termin gir samme id. Tripletex-UI oppretter også
  avstemminger når sider åpnes.
- Kommentarstil: én kort setning med årsaken, som en regnskapsfører skriver den – f.eks. «Kravet skyldes ubetalt AGA etter korreksjon, se vedlegg.» eller «Utbetalte feriepenger.» Ingen utregninger eller utfylling.
- Kommentar med feil `referenceId` blir lagret (201), men vises ikke i UI. Er du i tvil: be brukeren skrive «test» på
  linjen i UI, og les referansen med `GET .../comments`.
- Sletting av kommentarer: stien `.../comments/{id}` finnes (405 på GET), men er ikke testet.

## Lønn

Oppretting: `POST /salary/{type}/reconciliation/context {customerId, year, term}` → `{reconciliationId}`. Termin = 2 måneder.

| Type (`type` i modulen) | Sti-segment | Lesekall | `referenceId` for kommentar |
|---|---|---|---|
| Skattetrekk (TAX_DEDUCTION) | `taxDeduction` | `/overview`, `/paymentsOverview`, `/balanceAndOwedAmount` | epochDays for måneden (20635 = 2026-07-01) |
| Arbeidsgiveravgift (PAYROLL_TAX) | `payrollTax` | `/overview` (per sone), `/paymentsOverview` | **konto-id** for 2770 (`overview.account.id`), verifisert via `/validations` |
| Utleggstrekk (MANDATORY_DEDUCTION) | `mandatoryDeduction` | `/overview`, `/paymentsOverview` | epochDays for måneden |
| Feriepenger (HOLIDAY_ALLOWANCE) | `holidayAllowance` | `/holidayAllowanceDetails`, `/holidayAllowanceSummary` | **kontonummer**: 2940 (skyldige feriepenger), 2785 (AGA av feriepenger) |
| Finansskatt (FINANCE_TAX) | `financeTax` | `/overview`, `/paymentsOverview` | ikke verifisert |
| Samlet lønn (SALARY) | `/salary/reconciliation/{id}` | `/vacationPay` gir ekte tall. **`/overview` gir plassholderdata – ikke bruk** | – |

Andre: `GET /salary/reconciliation/{kunde-id}/aggregatedContext?year=&term=` (alle lønnsavstemminger og kontroller for
terminen), `GET /salary/reconciliation/{id}/ameldingStatus`, `GET /salary/tskinternal/amelding/ameldingStatus?date=&contextId=`.

**Tallene:** `ledgerSum` = hovedbok, `ameldingSum` = a-melding, `taxAuthoritiesSum` = A07 (null til A07 er hentet),
`discrepancy` = avvik. `paymentsOverview` viser betalt og rest per måned hittil i år (fant overbetalt trekk).

**Feriepenger:** modulen sammenligner netto endring på 2940/2785 med det som er opptjent i feriepengelisten. Utbetaling av
feriepenger i terminen gir derfor et forventet avvik som må forklares med kommentar på 2940 og 2785 før `:complete`.
Kontroll: opptjent (liste = netto 5020) − utbetalt = netto endring 2940. Utbetaling av fjorårets feriepenger (juni) = `prevYearSettledVacationPay`
i `GET /salary/reconciliation/{SALARY-id}/vacationPay` (klient A T3 2026: 101 668,92, avvik forklart på øret). AGA: 14,1 % av utbetalingen flyttes fra 2785.

### A07 fra Skatteetaten

Kall fra **klientens kontekst** (Basic-auth companyId = kunde-id, `contextId` = klientens company-id):

1. `GET /altinn/systemuser/hasSystemUser?isAgent=false` i klientkonteksten – men **false er ikke nødvendigvis et hinder**: for klient B (Unikum) var den false, og A07-bestilling fra klientkonteksten virket likevel (2026-09-23). Prøv bestillingen.
2. Bestill: `POST /salary/tskinternal/amelding/reconciliation/reports?contextId=<id>` med body `{year, monthFrom, monthTo}` → 204.
   Svaret kommer asynkront (SSE-hendelse `amelding_reconciliation_report`). Spør `.../latest` hvert 5. sekund (tok ca. 10–30 sek).
3. Les: `GET /salary/tskinternal/amelding/reconciliation/reports/latest?contextId=<id>&fromYearMonth=2026-07&toYearMonth=2026-08`
   → `details.paymentInformation` (sum trekk, AGA, finansskatt), `details.submissions[]` (hver a-melding med tidspunkt og
   summer) og `details.businesses[].payrollTax` (grunnlag per sone). Kun aggregater.

- Rapportene lagres per foretakskontekst. Fra klientkonteksten ser du også rapporter hentet i UI.
- **Bestilling fra byråkontoen henter byråets egen A07** (Silfer AS) – `contextId` blir ignorert. Kontroller alltid
  A07-summene mot `ameldingSum` før bruk.
- Etter henting fylles `taxAuthoritiesSum` i lønnsavstemmingene. Når regnskap = a-melding = A07 går `:complete` rett gjennom.

### Arbeidsflyt som virket (klient A termin 4)

1. `POST .../context` for hver type → id-er.
2. Bestill og les A07 fra klientkonteksten. Kontroller mot `ameldingSum`.
3. Les `overview` for hver type. Avvik: finn årsaken (bilag), skriv kommentar på riktig `referenceId`.
4. `PUT /accountingOffice/reconciliations/{id}/:complete`. Ved 422: kommenter `referenceId`-ene i meldingen og prøv igjen.
5. Rapporten ligger i `document` (PDF). Status COMPLETED, låst.

## Mva

| Kall | Hva |
|---|---|
| `POST /vat/reconciliation/context {customerId, year, term, vatReportType:"GENERAL_INDUSTRY"}` | Opprett/hent mva-avstemming (idempotent) |
| `GET /vat/reconciliation/{id}/overview` | `period` + `groups[].lines[]`: `vatTypeId`, `displayName`, `basis` (grunnlag), `ledgerData` (hovedbok), `reportedData` (mva-melding), `taxAdminData` (Skatteetaten), `difference` |
| `GET /vat/reconciliation/{id}/status` | Mva-meldingens status for terminen: `deliveryStatus`, `paymentStatus`, `totalAmountVatBasis`, `altinnPaymentAmount` |
| `GET /vat/reconciliation/statusList/{id}` | Samme for alle terminer i året |
| `GET /vat/reconciliation/{id}/reportTypes` og `GET /vatReturnsOverview/reportTypes?contextId=` | Alminnelig/primærnæring |
| `POST /vat/reconciliation/{id}/syncWithTaxAdmin` (body `{}`) | Henter Skatteetatens tall. **Krever aktiv ID-porten-innlogging** – ikke testet |
| `GET /idporten/loginstatus`, `POST /idporten/login {internalRedirectUrl}` | ID-porten. API-brukeren har `active:false` |
| `GET /ledger/internal/general/sums?accountIds=&contextId=&dateFrom=&dateToExclusive=` | Saldo for 2740 (IB, endring, UB) i UI-toppen |

- Mva-avstemmingen for en termin gir først mening når mva-meldingen er levert (`reportedData` er null før det).
- Synkronisering med Skatteetaten gjelder **én termin om gangen** (terminen som er åpen i UI) og krever ID-porten-innlogging
  hos **brukeren som synkroniserer**. ID-porten-økten deles ikke med API-brukeren (`/idporten/loginstatus` = `active:false` for
  API-tokenet også etter at brukeren logget inn), så synkroniseringen må gjøres i UI. Etterpå kan API-et lese `taxAdminData`.
  Testet 2026-09-23: T1 fikk Skatteetaten-tall på alle linjer, T2 forble `null` til den ble synkronisert.
- Fortegn: fradragslinjer har negativt `basis`/`ledgerData` når meldingen er levert. Sum av `ledgerData` = mva å betale
  (+) eller til gode (−) og stemmer med `altinnPaymentAmount` i `statusList`. Kjøp av tjenester fra utlandet (kode 86)
  kommer som to linjer som går i null.
- En termin kan mangle avstemming (`periodsOverview.periods[].reconciliation = null`). Opprett den med context-POST (eller
  åpne terminen i UI) før synkronisering.
- `referenceId` for mva-kommentarer er trolig linjen (`vatTypeId`) – ikke verifisert. Bruk «test»-metoden.
- Fullføring: felles `PUT /accountingOffice/reconciliations/{id}/:complete` – testet OK 2026-09-23 på klient A T1–T3 (avvik 0 på alle linjer → COMPLETED, låst, PDF «Merverdiavgift_<klient>_Term<n>_<år>_<tid>.pdf»). Kontroller først at `ledgerData = reportedData = taxAdminData` på alle linjer.

## Balanse (fra UI-koden, ikke testet)

`POST /balance/reconciliation/context`, `POST /balance/reconciliation/annual/context` (spec), `GET /balance/reconciliation/{id}/table`,
`GET .../table/{accountId}`, `GET .../table/list`, `GET .../account/{accountId}/vouchers` (spec – testet, `accountId` = konto-id hos
klienten), `PUT /balance/reconciliation/{id}/:complete | :reopen | :control | :uncontrol`.

## Bank (fra UI-koden, ikke testet)

`GET /bank/reconciliation/internal/state`, `/bank/reconciliation` (spec). Se også bank-oppgavene i indeksen.

## Kalibrering K0 (2026-09-24)

Kjørt på klient A med silfer-tokenet, både i byråkontekst (`authorization(0,'silfer')`) og i klientkontekst. Bare GET-kall. Hver testgruppe ble etterprøvd av en uavhengig kontrollør. Detaljer og konsekvenser for mva-flyten står i `mva-avstemming/references/kalibrering.md` i avstemminger-repoet.

**Denne seksjonen går foran avsnittene over der de er uenige.** Det gjelder særlig disse avsnittene under Mva: «gir først mening når levert», «Fortegn» og «/validations er beste måte å finne referenceId».

### Id-begreper og liste

- `customerId` i modulen = `connect()`-id = `/company/>withLoginAccess`.id.
- `customerCompanyId` = `whoAmI.companyId`. Bruk `fields=companyId`, fordi `fields=company(id)` gir null.
- `GET /accountingOffice/reconciliations`: `customerId`, `year`, `term` og `type` filtrerer på serversiden. Ukjente parametere ignoreres uten feil (f.eks. `customerIds` gir alle kunder), og `status` er ikke et filter. En ugyldig `type` gir 404. Kontroller derfor alltid svaret lokalt.
- `fullResultSize` er bare en nedre grense. Bla til en side gir færre enn `count`. `list()` i tripletex.js stopper på fullResultSize, og det mønsteret skal ikke kopieres her.
- Standardrekkefølgen er etter id. `sorting=term` virker.
- **`term` betyr måned for BALANCE og tomånedlig termin for VAT.** Bruk alltid `term` sammen med `type`.
- `periodsOverview`:
  - `type` = VAT_GENERAL_INDUSTRY, VAT_PRIMARY_INDUSTRY eller BALANCE. `VAT` og `BANK` gir 422.
  - VAT_PRIMARY og VAT_GENERAL gir samme perioder (gruppe «VAT»), så reportType skilles med `reconciliations?type=`.
  - `endDate` er eksklusiv.
  - `period.reconciliation.url` er en API-URL, ikke en UI-lenke.

### Mva (VAT)

- **`/vat/reconciliation/{id}/overview` finnes før levering**, så lenge avstemmingen er opprettet:
  - `basis` og `ledgerData` er fylt ut.
  - `reportedData`, `taxAdminData`, `difference` og `ledgerDataAtPreviousReconciliation` er null.
  - Σ ledgerData = `/vatReturnsOverview/vatTermAmount` før levering, og = `altinnPaymentAmount` etter.
- **Fortegn** (rettelse av avsnittet over): fortegnet viser linjens bidrag til beløpet å betale. Utgående mva er +, fradrag er −. En fradragslinje kan være + når kreditnotaene er større enn kjøpene. Konvensjonen er den samme på leverte og ikke-leverte terminer.
- **Beløp** er hele kroner avkortet mot null, ikke avrundet. Sammenligning mot hovedboken tåler under 1 kr per linje.
- **Linjer:**
  - `vatTypeId` er Tripletex' globale vatType-id, ikke mva-koden. Oppslag via `/ledger/vatType`.
  - Kode 86 gir to linjer med **samme** vatTypeId (+ og −).
- **Felt som følger status:**
  - `ledgerDataAtPreviousReconciliation` fylles først når avstemmingen er COMPLETED, ikke ved levering.
  - `difference` er null før levering, og = ledgerData − reportedData når taxAdmin er null.
  - Om `difference` tar med taxAdmin når den er fylt ut, er uavklart. Regn begge avvikene selv.
- **`totalAmountVatBasis`** (`/vat/reconciliation/{id}/status`) ≠ Σ basis. Den er Σ basis pluss grunnlaget for kode 86 én gang.
- **Levert men ikke synket** (taxAdminData null) holder avstemmingen i DRAFT med `pending=true`. Sjur synker i UI, og etterpå kan den fullføres.
- **Validations og kommentarer:**
  - `/accountingOffice/reconciliations/{id}/validations` er **tom** på fullførte, åpne og levert-men-ikke-synkede mva-avstemminger, og på en BALANCE i DRAFT. Den gir altså ingen referenceId før levering, og en tom liste betyr ikke «avstemt».
  - referenceId for mva-linjer er fortsatt ikke verifisert, så bruk «test»-metoden.
  - Kommentarskjema: `{id, version, url, reconciliationId, createdAt, createdBy, referenceId, comment}`. Utelat `createdBy` med `fields=`.
  - I feriepengeavstemmingen for klient A ligger samme kommentar på både konto-id og kontonummer for 2940. Kontonummer er riktig format (bare det ble brukt i forrige termin), og konto-id-varianten er et feilforsøk som bør ryddes.

### Balanse (BALANCE)

- **Perioden er månedlig** (termNumber 1–12), og det finnes i tillegg en ANNUAL_BALANCE-periode med term=1 som må filtreres bort på `reconciliation.type`. Én mva-termin gir to BALANCE-avstemminger.
- **`GET /balance/reconciliation/{id}/table`:**
  - Svaret er `{period, groups[{displayName, lines[]}], inactiveAccounts[]}`.
  - Linjefelt: `accountId`, `displayName`, `balanceIn/Change/Out`, `storedBalanceIn/Change/Out`, `documentedBalance`, `difference`, `status` (NOT_RECONCILED/RECONCILED/REJECTED/CONTROLLED/IGNORED), `availableStatuses`, `reconciledAt/By`, `controlledAt/By`, `errors`, `attachedVouchers`, `autoReconciled` og `autoReconciledFromTypeName`.
  - Linjene har ingen egen id.
  - Nestet `fields` virker bare med `*` først: `fields=*,groups(*,lines(accountId,balanceOut,documentedBalance,difference,status,autoReconciled))`. Uten `*` først blir groups tomme.
  - Med `fields=*` er `reconciledBy/controlledBy` bare `{id,url}`, men de utelates likevel.
- **Innhold:**
  - Med er klasse 1–2-kontoer med saldo eller bevegelse, gruppert per kontogruppe. Resten ligger i `inactiveAccounts`.
  - `balanceOut` = `/balanceSheet` UB med `dateTo` = periodens endDate.
- **Auto-avstemming:**
  - 2740 blir autoReconciled («Merverdiavgift») i begge terminmånedene først når VAT er fullført.
  - 2600/2610/2770/2771 blir auto når lønnsavstemmingen er fullført.
  - 2700/2703/2710 blir aldri auto.
  - 19xx blir **ikke** auto når bankmåneden lukkes. Da er documentedBalance = saldo og difference = 0, men status NOT_RECONCILED. Status ser heller ikke ut til å fjernes når banken gjenåpnes.
- **Skriving (fra UI-koden, ikke testet):**
  - `PUT /balance/reconciliation/{id}/table/{accountId}` med hele linjen og `controlledBy: null, reconciledBy: null`, altså rowId = accountId.
  - `PUT .../table/list` tar en array av linjer og svarer med `values[]`.
  - GET på disse stiene gir HTTP 400 (code 4000) med meldingen «405 Method Not Allowed». Les meldingen, ikke bare statuskoden.
- `GET /balance/reconciliation/{id}` gir 404, så bruk `/accountingOffice/reconciliations/{id}`.

### Bank

- **`GET /bank/reconciliation/internal/state`:**
  - `accountId` og `startDate` er påkrevd. Uten startDate kommer 500, men datoen kan være hvilken som helst dag i måneden.
  - `balanceOutDifference` = ledgerAccountOutBalance − bankStatementOutBalance. Mangler kontoutskriften, er differansen lik saldoen i hovedboken.
  - `reconciliation=null` betyr at det ikke finnes noen avstemming.
  - Beløpene er de samme som i offentlige `/bank/reconciliation` (`bankAccountClosingBalanceCurrency`) og `/balanceSheet`.
  - `isReadOnly=true` betyr at en senere måned er lukket.
  - `isApprovableIncomplete=true` også uten avstemming og med saldo 0.
- `requireReconciliation` på bankkontoene sier ikke hvilke kontoer som avstemmes. Den var false på alle kontoene hos klient A.

### Skattekonto og betaling (klientkontekst)

- **`GET /claimsAndPayments?year=`** virker med API-tokenet når klienten har Altinn-systembruker (`hasSystemUser=true`):
  - Kallet gir alle krav med aktivitet i året, også oppgjorte. `year` følger claimCreatedDate.
  - Mva kjennes på `claimGroup` = «Merverdiavgift». Parameteren ignoreres, så filtrer lokalt.
  - Sett claimType: mvaMelding, konteringMvaÅBetale, konteringTilgodeMva, konteringKorrigertTilgodeMva, fastsettingsrenterMva11_2 og forsinkelsesrenterMva.
  - Sporadisk 500 (code 1002), så gjør nye forsøk.
- **`/claimsAndPayments/byClient`** fra byrået gir 403 «KB-005» for en klient med isAgent=false.
- **`GET /vatReturns/{id}/paymentInfo`** gir KID, konto, beløp (= totalAmountVatToPay) og forfall for alle leverte terminer. KID er unik per termin.
- **Sperret for API-brukeren** (403 code 9000 hos klient A): `/bank/paymentWidget`, `/bank/payment` og `/bank/agreements/autoPayStatus`.
- For tilgodeterminer viser `/vatReturns` og `paymentHistory` ofte `isPaid=false` og en åpen post selv når Skatteetaten har gjort opp. Oppgjøret leses fra claimsAndPayments og 2740.

### Mva-melding (klientkontekst)

- **`/vatReturnsOverview/vatTermAmount`:**
  - Parametrene er `year`, `term` og `reportType` (valgfri). Svaret er `{value}`: + = å betale, − = til gode.
  - Kallet gir tall også for terminer som ikke er opprettet.
  - **Det svarer 0 uten feil** når parameteren er feil (f.eks. `vatTerm`) eller term eller reportType er feil.
- **`/vatReturns/>vatTerm`:**
  - Parametrene er `year`, `vatTerm` og `reportType`. Parameteren `term` gir 500.
  - Kallet gir et beregnet utkast (id=0, NOT_STARTED) også før «Opprett».
  - **Kall det og `/vatReturns/{id}` uten fields eller med `fields=*`.** Eksplisitte fields på vatGroups eller lines tømmer linjene.
- `/vatReturns/validateCreate` er GET.
- `/vatReturnsOverview/overview` har `term=0` for opprettede terminer. `dueDate` er flyttet ved helg.

### Sperret eller ubrukelig for API-tokenet

- `/anomalies/context`, `/anomalies/clientsOverview`, `/anomalies/clients` og `/anomalies?customerId=` gir 403 code 9000 i begge kontekster.
- `/anomalies/aggregate*` svarer 200 med 0, og det kan ikke skilles fra «modul inaktiv».
- `/incomingInvoice/search` og `/{voucherId}`, `/internal/{voucherId}` og `/changes` gir 403 code 9000. `/incomingInvoice/internal/vat` svarer 200.
- `/addon/company/{id}` gir bare tilleggskatalogen, uansett id.
- `/ledger/accountingPeriod/getAccountingPeriodByDate` og `/company/salesmodules` gir 403.
- `/bank/integration/switch/ztlAccounts` gir 500.
- Mønster: 403 code 9000 med `validationMessages=null` betyr at funksjonen er sperret for tokenet eller klienten, uansett parametere.
