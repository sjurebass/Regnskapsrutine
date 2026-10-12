# Bilagsvurdering av mva – fremgangsmåte for agenten

> **Merk (oktober 2026):** Designdokument fra september 2026. `klientprofil.md`, `kjente-avvik.md`, `logg.md` og kundemappene `<Kunde>/<år>/…` er erstattet av kundeinstruksen i Tally (skillen `kundeinstruks`), og leveranser lagres i Tally eller avstemmingsmodulen. `npm run mva`/`modul` og `%LOCALAPPDATA%\silfer-mva` gjelder bare CLI-hurtigveien. Driftsflyten står i `SKILL.md`.

Denne filen beskriver hvordan agenten vurderer mva-behandlingen av bilagene i en termin for én Tripletex-klient.

Grunnlag:
- `fradragsregler.md` er det faglige grunnlaget. Les den før første bilag.
- `regelbase.json` er den maskinlesbare forhåndssjekken.
- Klientens `klientprofil.md` overstyrer kontoer, vesentlighet og mva-status. Ligger i `C:\Users\Sjur\Desktop\avstemminger\<Klient (id)>\`.
- Klientens `kjente-avvik.md` inneholder avvik som allerede er kvittert ut. Ligger i samme mappe.

Agenten skal gjøre en faglig vurdering av det som faktisk er kjøpt. Det holder ikke å sjekke konto og kode mekanisk.

**Faste rammer**
- Arbeid bare mot én klient, og bare den Sjur har navngitt. Er det uklart, spør.
- Bare lesende kall. Korreksjoner, kommentarer i Tripletex og nye bilag er skrivende og krever at Sjur bekrefter først (se seksjon 6).
- GDPR: se seksjon 8. Ingen personopplysninger i output.

---

## 1. Datauttrekk

Kjør fra `C:\Users\Sjur\Tripletex API`:
- `export MSYS_NO_PATHCONV=1; npm run -s api -- GET "/sti?..." --client "<klient>"`, eller
- et node-skript som importerer `src/tripletex.js` (`connect`).

Bruk alltid `fields=`. Personendepunktene (`/employee`, `/salary`, `/timesheet`, `/travelExpense`, `/contact`) skal ikke brukes. Alt som skrives ut, sendes gjennom `redact()` fra `src/privacy.js`.

### 1.1 Hentes én gang per klient og termin og deles mellom delagentene
Lagres som JSON i en midlertidig mappe for kjøringen: `scratchpad/mva-<klient>-<termin>/`.

| # | Kall | Formål |
|---|---|---|
| 1 | `GET /ledger/vatSettings?fields=vatRegistrationStatus,hasVatInHighForeignServices,hasVatInLowForeignServices,hasVatInImport,hasVatInAndOutReverseDuty,hasAdjustmentVat,hasWithdrawalVat,hasDrawbackVat,hasVatOutOutside` | Mva-status (`VAT_NOT_REGISTERED`, `VAT_APPLICANT`, `VAT_REGISTERED` eller `VAT_COMPENSATION`). Styrer hele regelsettet |
| 2 | `GET /vatTermSizeSettings` og `GET /vatReturns/status/list?startDate=&endDate=` | Terminlengde og status. Gir fakturadato → termin |
| 3 | `GET /ledger/vatType?count=1000&sorting=number&shouldIncludeSpecificationTypes=true&fields=id,number,name,percentage,deductionPercentage,parentType(id,number)` | Koden `id` oversettes til SAF-T-nummer. **Bruk alltid `number`, aldri `id`** (i piloten var id 12 = kode 13 og id 111 = kode 12). En kode er relativ bare når `parentType` er satt **og** `deductionPercentage` er under 100. Spesifikasjonskodene (JUST, TAP, TILB, UTTAK) har `parentType` med 100 % og er ikke relative. Kontroller at `number` følger SAF-T før regelbasen brukes (usikkerhet U1) |
| 4 | `GET /ledger/posting?dateFrom=&dateTo=&count=1000&from=<n>&fields=id,voucher(id),row,date,description,account(number,name,vatType(number),vatLocked,legalVatTypes(number)),vatType(id,number,percentage,deductionPercentage,parentType(number)),amount,amountGross,currency(code),supplier(id),customer(id),type,systemGenerated,project(id)` | Alle posteringer, hentet side for side. `/ledger/posting` har **ikke** `voucherId` (parameteren ignoreres i stillhet), så grupper på `voucher.id` lokalt. Hent 27xx direkte med `accountNumberFrom=2700&accountNumberTo=2749`. Lønn (5000–5999, `type=WAGE`) brukes bare som summer per konto |
| 5 | `GET /ledger/voucher?dateFrom=&dateTo=&count=1000&fields=id,number,tempNumber,date,description,voucherType(name),vendorInvoiceNumber,reverseVoucher(id),attachment(id,fileName,mimeType),ediDocument(id,fileName,mimeType)` | Bilagshoder. `number=0` og `tempNumber>0` betyr at bilaget ikke er bokført. Rapporteres for seg og tas med i kontrollene i 1.4. `attachment.size` og `mimeType` er upålitelige. **Datofilteret gir bare bilag med bilagsdato i terminen.** Periodiseringer, lønnsperiodisering og reverseringer med bilagsdato før terminen mangler (10 bilag i piloten). Samle derfor alle `voucher.id` fra posteringene (kall 4) og hent de som mangler, med `GET /ledger/voucher/{id}?fields=...` (samme felt). Kontroller til slutt at hver `voucher.id` i posteringene har et bilagshode |
| 6 | `GET /supplierInvoice?invoiceDateFrom=&invoiceDateTo=&fields=id,invoiceNumber,invoiceDate,supplier(id,organizationNumber),voucher(id,number),amount,amountExcludingVat,currency(code),isCreditNote,originalInvoiceDocumentId,orderLines(description,count,amountExcludingVatCurrency,amountIncludingVatCurrency,vatType(number,percentage))` | Fakturadato (for termin), fakturanummer (for duplikater) og **selgers mva-kode per linje** (`orderLines.vatType`). Datoområdet utvides med én termin bakover for å fange sen bokføring. `amount` er negativ, så sammenlign absoluttverdier. `orderLines` tillater ikke `account`. Rader med `amount = 0` og uten `voucher` er støy og filtreres bort, men antallet rapporteres i metodefanen |
| 7 | `GET /supplier?fields=id,name,organizationNumber,isPrivateIndividual,currency(code),physicalAddress(country(isoAlpha2Code)),postalAddress(country(isoAlpha2Code))` | Leverandørtype og land. Hent **ikke** bankkonto. Land og valuta var tomme på **alle** leverandører i piloten, og fire manglet org.nr. (blant dem hovedentreprenøren, med feilstavet navn). Leverandørens org.nr. og land fastsettes derfor i denne rekkefølgen: EHF `AccountingSupplierParty` → org.nr. på PDF-fakturaen → `supplier.organizationNumber` → Brreg-søk på navn (bare AS, ikke personer). En leverandør som verken har norsk org.nr. eller land etter dette, merkes `uklassifisert` og vurderes manuelt (se regelbase `leverandortyper`). Avvik mellom Tripletex og EHF/Brreg (manglende org.nr., navneavvik) rapporteres på klientnivå som datakvalitet |
| 8 | `GET /asset?fields=id,name,dateOfAcquisition,acquisitionCost,account(number)` | Kandidater til kapitalvarer |
| 9 | **Leverandørindeksen** (`npm run -s leverandor -- importer --client "<klient>" --fra <T_start> --til <D> --json`), som bruker Brreg bare for nye leverandører og for poster eldre enn 30 dager | For klienten og hver leverandør: mva-registrert og fra hvilken dato, org.form, næringskode, land, konkurs/slettet, og tidligere vurderinger (utenlandsk, omvendt avgiftsplikt, kostnadstype, fradrag). Underenheter får mva-status fra hovedenheten (testet: underenheten står som ikke registrert selv når hovedenheten er registrert). **Brreg er alltid fasit for registrering.** Et «…MVA»-suffiks i EHF eller på PDF er ikke bevis (piloten fant en offentlig innkrevingsmyndighet med «MVA» uten registrering). Se 1.1a |
| 10 | `GET /project?fields=id,number,name,startDate,endDate,isClosed` (bare når klientprofilen har prosjekter, eller posteringene har `project.id`) | Kobler byggekostnader til prosjekt for § 3-26-vurderingen og for tilvalg. Prosjektnavn kan være gateadresse og er da greit (eiendom, ikke person) |

### 1.1a Leverandørindeksen (felles for alle klienter)
Indeksen ligger i `C:\Users\Sjur\Tripletex API\data\leverandorer.json` og brukes med `npm run -s leverandor -- …` (se CLAUDE.md i den mappa). Den gjør at en leverandør som er vurdert hos én klient, ikke vurderes på nytt hos neste.
- **Før websøk:** `leverandor -- finn <orgnr|navn> --json`. Finnes en vurdering, brukes den. En vurdering gjort av Sjur (`vurdert_av: "Sjur"`) er fasit.
- **Org.nr. fra EHF eller PDF som mangler i Tripletex:** `leverandor -- oppslag <orgnr> --alias "<navn i Tripletex>"`. Neste import kjenner leverandøren igjen på navnet, også med skrivefeil.
- **Etter vurdering** av utenlandske, uklassifiserte eller spesielle leverandører (f.eks. plattformgebyrer, forsikring, VOEC): `leverandor -- vurder <orgnr|navn> [--navn "<navn>" --land <XX>] --kostnadstype ".." --fradrag ".." --sats ".." --omvendt 86|87|88|89|nei --kilde "<url eller hjemmel>" --sikkerhet høy|middels|lav`. Vurder bare det som gjelder leverandøren generelt, ikke det enkelte bilaget.
- Importen lister også leverandører uten mva-registrering, konkurs/slettet og org.nr. som mangler i Tripletex. Disse går rett inn i forhåndssjekken (regelbase `leverandortyper`) og i datakvalitetsfunnet på klientnivå.
- Indeksen lagrer ikke hvilke klienter som bruker leverandøren. ENK og navn som kan være personer lagres bare som hash.

Tripletex sine egne kall for avviksanalyse og Brreg (`/incomingInvoice/*`) gir 403. Kontrollen bygges derfor selv, slik det er beskrevet her.

### 1.2 Vedlegg (hentes bare for bilag i utvalget, seksjon 2b/2c)
- PDF: `GET /document/{attachment.id}/content`. Svaret er binært, så `rawRequest()` i `tripletex.js` kan ikke brukes. Bruk `fetch(BASE_URL+sti, {headers:{Authorization: await authorization(...)}})` fra `src/auth.js` og les som `arrayBuffer`. Filtypen kjennes igjen på de første bytene (`%PDF` eller `<?xml`).
- Alternativ: `GET /ledger/voucher/{id}/pdf`. 0 byte betyr at bilaget ikke har vedlegg.
- Tekst: `pdftotext` (mingw64). Bilder (JPG/PNG) leses med Read-verktøyet eller OCR. Python er ikke installert, så XML parses i node.
- Filene lagres bare i `scratchpad/mva-<klient>-<termin>/vedlegg/`, og mappen slettes når kjøringen er ferdig (seksjon 8).

### 1.3 EHF (hentes for alle bilag med `ediDocument`, fordi det er billig og deterministisk)
`GET /document/{ediDocument.id}/content`. Felter som leses:
- `IssueDate` → termin
- `AccountingSupplierParty/Party/PartyTaxScheme/CompanyID` på formen `NO#########MVA` → selgers mva-ID. `PartyTaxScheme` forekommer ofte **to ganger** (`TaxScheme/ID` = `VAT` og en med «Foretaksregisteret»), og rekkefølgen varierer. Velg elementet der `TaxScheme/ID` er `VAT`, ikke det første. Org.nr. hentes fra `PartyLegalEntity/CompanyID` (eller `EndpointID` med schemeID 0192). Selve registreringen avgjøres av Brreg (kall 9), ikke av suffikset
- `PostalAddress/Country` → selgerland
- `AccountingCustomerParty/.../CompanyID` → skal være klientens org.nr. Sammenlign bare de ni sifrene. «NO…MVA» på en klient som ikke er registrert, er selgers formfeil og ikke et funn
- `ID` (fakturanummer), `BillingReference/InvoiceDocumentReference/ID` (kreditnotaens henvisning til original), `OrderReference/ID`, `ContractDocumentReference/ID` og `InvoicePeriod` → brukes til å skille ekte duplikater fra faste periodebeløp og til kontrollen av kreditnota
- `TaxTotal/TaxSubtotal` (`TaxableAmount`, `TaxAmount`, `TaxCategory/ID` S/Z/E/AE/O/G/K, `Percent`)
- linjer med `Item/Name` og `ClassifiedTaxCategory`
- `LegalMonetaryTotal/PayableAmount`
- `InvoiceTypeCode` / `CreditNote`
- `DocumentCurrencyCode`

Den innebygde PDF-en (`EmbeddedDocumentBinaryObject`) skal ikke pakkes ut, med mindre en faglig vurdering krever det. Kontakt-e-post, telefon og `PayeeFinancialAccount` i XML-en skal aldri leses ut eller lagres. Det samme gjelder fritekstfeltet `Note` og `Contact/Name`: i piloten inneholdt `Note` saksbehandlers navn og e-post. `Note` kan leses lokalt som signal, men gjengis aldri og går gjennom fritekstfilteret (seksjon 8).

Når `Item/Name` er generisk («iht. avtale», «a konto», «timer»), er EHF-linjene ikke nok for vurderingen av punkt 6–8. Da leses det vedlagte spesifikasjonsdokumentet eller den innebygde PDF-en.

### 1.4 Bilag som ikke er bokført (`number=0`, `tempNumber>0`)
Bilag som ligger i innboksen eller er registrert uten å være bokført, har **ingen posteringer**. Derfor fanges de ikke av noen posteringsregel. Piloten fant en purring fra et inkassobyrå som lå inne som «faktura» med samme fakturanummer som en bokført faktura. Hadde den blitt bokført, ville kostnaden blitt dobbel.

For hvert slikt bilag:
1. Hent EHF eller vedlegg på samme måte som for bokførte bilag (1.2 og 1.3).
2. Kjør duplikatkontrollen på **selgers org.nr. (fra EHF eller PDF) + fakturanummer** mot alle bokførte bilag de siste 12 månedene. `supplier.id` kan ikke brukes, fordi bilaget ofte mangler leverandør, og fordi samme selger kan være registrert to ganger.
3. Kjør kontrollen av salgsdokument (R-IKKE-SALGSDOKUMENT) uansett mva-status.
4. Kontroller om beløpet er summen av andre fakturaer fra samme selger pluss renter eller gebyr. Det tyder på purring eller inkassovarsel.
5. Rapporter med `tempNumber` som identitet (se seksjon 4) og konklusjonen `ikke_salgsdokument`, `ok` (kan bokføres) eller `maa_avklares`.

Å avvise, slette eller bokføre et slikt bilag er skrivende og krever at Sjur bekrefter (seksjon 6).

---

## 2. Utvalg: hvilke bilag leses?

Tre lag. Lag (a) går alltid på alle posteringer. Lag (b) og (c) bestemmer hvilke vedlegg agenten leser.

### (a) Deterministisk forhåndssjekk på ALLE posteringer (regelbase.json)
Kjøres i kode uten å lese vedlegg. Hvert treff får en `regel_id` og en alvorlighet.
- **Kode mot konto:** risikokontoer som representasjon, gaver, velferd, bil, diett og bank eller forsikring, med fradragskode. Kontoer som skal ha fradrag, med kode 0 og mva på fakturaen.
- **Sats:** implisitt sats (`amountGross/amount − 1`) passer ikke med kodens prosent. Kode 1 på vann og avløp (15 % fra 1.7.2025).
- **27xx:** saldo eller bevegelse hos en klient som ikke er registrert, med unntak for 87/89/92. Postering på 2710 uten tilhørende kostnadslinje.
- **Leverandør:** fradragskode på bilag fra en leverandør som ikke er registrert i Merverdiavgiftsregisteret på fakturadatoen, eller som mangler org.nr.
- **Utland:** utenlandsk leverandør (EHF-land, valuta, ingen norsk org.nr., navnemønster) med kode 0 eller 1 og ingen 86/87. For klient som ikke er registrert: summen per kvartal sammenlignes med grensen på 2 000 kr. Leverandører som er `uklassifisert` (verken norsk org.nr. eller land), tas alltid med i utvalget og klassifiseres manuelt. Ellers kan en utenlandsk tjeneste gli forbi fordi land og valuta er tomme.
- **EHF mot postering:** `orderLines.vatType` / `TaxSubtotal` mot bokført kode og mva-beløp. For registrert klient: S/25 skal gi 2710-beløp ≈ `TaxAmount` (toleranse ±1 kr). E/Z/O skal ha kode 0.
- **Termin:** fakturadato i en annen termin enn bilagsdatoen.
- **Duplikat:** to regler (se regelbasen).
  - R-DUPLIKAT-FAKTURANR (høy): samme selger og samme fakturanummer. Selger identifiseres med org.nr. fra EHF/PDF/Brreg, ikke `supplier.id`. Omfatter bilag som ikke er bokført (1.4).
  - R-DUPLIKAT-BELOP (middels): samme selger og samme beløp innen ±30 dager. Treffet filtreres (merkes `filtrert`, men beholdes i rådata med begrunnelse) når begge fakturaene har ulikt fakturanummer **og** ulik referanse (målepunkt, ordre- eller kontraktsreferanse, `InvoicePeriod`). Faste periodebeløp som nettleie og abonnement ga falske positiver i piloten. Regelen svekkes ikke: uten slike referanser leses begge bilagene.
- **Kreditnota:** negativ leverandørfaktura med annen kode enn originalen, eller med kode 0 når originalen hadde fradrag.
- **Bank (§ 8-8):** leverandørgjeld på 10 000 kr eller mer lukket mot 1900–1909.
- **Uten vedlegg:** fradragskode og verken `attachment` eller `ediDocument`.
- **Kontoplan:** kostnadskontoer med standardkode for fradrag hos klient som ikke er registrert (risiko, ikke avvik). Rapporteres én gang per konto med antall bilag og sum, ikke per bilag.
- **Kreditnota uten henvisning:** kreditnota uten `BillingReference` eller henvisning til original i teksten (bokf.f. § 5-2-7). Gjelder alle klienter.
- **Salgsdokument:** R-IKKE-SALGSDOKUMENT kjøres for **alle** klienter og også for bilag som ikke er bokført, på EHF-type, fakturatekst og (når lest) PDF-tekst.
- **Klientnivåregler** (`nivaa: klient` i regelbasen, for eksempel R-UREG-3-26 og R-UREG-SALG-AVGIFTSPLIKTIG) evalueres **én gang per klient og termin** og gir ett klientflagg. Tekstreffene per postering legges ved som dokumentasjon og gjør ikke bilaget til et avviksbilag. Bilagene vurderes ellers på vanlig måte.

### (b) Risikobasert utvalg der agenten leser vedlegget
Et bilag kommer med i utvalget når minst én av disse gjelder:
1. Det har et treff i (a) med alvorlighet `høy` eller `middels`.
2. Det er postert på en **risikokonto** (NS 4102, klientprofilen kan overstyre):
   - 5900–5999 (personal og velferd)
   - 6540 (inventar)
   - 6550–6553 (driftsmateriell og IT, privat bruk)
   - 6600–6699 (vedlikehold, bolig eller hytte?)
   - 6700–6799 (rådgivning: transaksjon eller privat?)
   - 6800–6899 (kontor, møtemat)
   - 6900–6909 (telefon og bredbånd)
   - 7000–7099 og 6440 (transportmidler)
   - 7100–7199 (reise og diett)
   - 7300–7330 (reklame, profilartikler og sponsing)
   - 7350–7369 (representasjon)
   - 7400–7439 (kontingent og gave)
   - 7700–7799 (annet)
   - 1100–1299 og 1400–1499 (aktiveringer)
   - klientens **prosjektkontoer** for byggekostnader fra klientprofilen (`prosjektkontoer`, for eksempel 4500–4599 hos utbyggere)
3. **Beløpet** er minst `vesentlighet` fra klientprofilen (standard 5 000 kr), eller mva-beløpet er minst 50 000 kr (kapitalvare, maskiner) eller 100 000 kr (bygg). For utbyggere og andre klienter der nesten alle bilag passerer 5 000 kr, bør klientprofilen sette en høyere `vesentlighet` (for eksempel 25 000 kr). Bilag under grensen fanges fortsatt av punkt 1, 2, 4–7 og det tilfeldige utvalget.
4. Leverandøren er **ny** (ikke brukt de siste 12 månedene), **utenlandsk**, et **ENK**, en **offentlig enhet** eller en **nærstående** (samme eier, styre eller konsern etter klientprofilen). For nærstående leverandører gjelder i tillegg at de er slettet, konkurs eller under avvikling.
5. Bilaget har **ikke vedlegg**, har bare én vedleggsside som ser ut som en kvittering, eller teksten inneholder signalord fra regelbasen (julebord, gave, lunsj, hotell, leiebil, parkering, lading, privat, aksje, emisjon, megler, forskudd og lignende).
6. Kreditnotaer og fakturaer rundt terminskifte (fakturadato de siste 5 dagene i forrige termin eller de første 15 virkedagene i terminen).
7. For klient som ikke er registrert: alle bilag med utenlandsk leverandør, alle salgsbilag på 3000–3999 som ikke gjelder bolig- eller tomtesalg, og alle bilag som gjelder innleie, prosjektledelse eller byggeledelse.
8. Leverandøren er `uklassifisert` (verken norsk org.nr. eller land etter oppslagene i 1.1).
9. Bilaget er et kostnadsbilag uten `ediDocument` (PDF eller bilde) med beløp over halvparten av `vesentlighet`. EHF-bilag er dekket deterministisk av 1.3, men PDF-bilag har ingen slik kontroll.

I tillegg trekkes et **tilfeldig kontrollutvalg** blant de resterende kostnadsbilagene: 10 %, minst 5 og høyst 25 bilag. **Taket på 25 gjelder bare det tilfeldige utvalget**, aldri lag (b) eller (c). Frøet settes lik termin-ID, så utvalget kan gjenskapes. Det tilfeldige utvalget tester om forhåndssjekken overser noe. Hvis minst ett bilag i utvalget gir AVVIK, utvides utvalget med 10 nye bilag.

### (c) Alle bilag for små klienter (anbefalte terskler)
Agenten leser **alle** kostnadsbilag med vedlegg når ett av disse gjelder:
- terminen har **150 eller færre** bokførte kostnadsbilag (4000–7999 og aktiveringer på 1xxx), eller
- samlet inngående mva i terminen er under **50 000 kr** (registrert klient), eller
- det er klientens **første kjøring** med denne flyten, eller klienten har hatt AVVIK på minst 3 bilag i forrige termin.

Referanse: Testklienten hadde 159 bilag på 8 måneder, altså om lag 40 per tomånederstermin. Da leses alle.

For store klienter over tersklene gjelder (a) + (b) + tilfeldig utvalg. Rapporten skal oppgi hvor mye av populasjonen som er dekket: antall bilag, beløp og mva lest, og hvor stor andel det er av totalen.

### Rekkefølge når lagene kolliderer
Piloten brukte et fast tak på 25 vedlegg og leste derfor bare 25 av 45 bilag, selv om (c) sier at alle skal leses. Dette gjelder:
1. Gjelder (c), leses **alle** kostnadsbilag med vedlegg. Da trengs ikke noe tilfeldig utvalg.
2. Gjelder ikke (c), leses **alle** bilag i (b). Det finnes ikke noe tak på (b).
3. Er (b) så stort at kjøringen ikke kan fullføres (over 150 bilag), prioriteres i denne rekkefølgen: treff med `høy`, treff med `middels`, bilag uten EHF, størst beløp. Det som ikke blir lest, rapporteres som `ikke_lest` med antall og beløp, og agenten sier fra til orkestratoren. Agenten skal ikke stille og rolig kutte utvalget.
4. «Lest» betyr at vedlegget (PDF eller bilde) er lest, **eller** at alle EHF-linjene er vurdert faglig og `Item/Name` er spesifikk nok (1.3). Sammendraget oppgir begge tallene hver for seg.

---

## 3. Sjekkliste per bilag (ta spørsmålene i rekkefølge)

Hvert svar noteres kort. Stopp ved første «ingen fradrag», men noter eventuelle feil fra senere trinn, for eksempel manglende omvendt avgiftsplikt.

1. **Klientens status på fakturadatoen.** Er klienten registrert? Er den ikke det, skal kode 0 brukes, og videre gjelder punkt **2** (salgsdokument og duplikat, som fanget purringen i piloten), **4** (kjøper), **10** (termin, kreditnota, dobbeltføring), **11** (omvendt avgiftsplikt) og **12** (§ 3-26, tilvalg og annen mulig avgiftspliktig omsetning). Punkt 3 brukes bare til å identifisere selger og land. Punkt 5–9 gjelder ikke, fordi det ikke er fradrag å vurdere. Er fakturaen fra før registreringen: § 8-6.
2. **Salgsdokument.** Er vedlegget selgers faktura, EHF eller salgskvittering? Ordrebekreftelse, proforma, purring, betalingspåminnelse («Payment Reminder»), inkassovarsel, kontoutskrift, betalingsbekreftelse, terminalslipp og «IKKJE KVITTERING FOR KJØP» er det ikke. En purring kjennes ofte igjen på at beløpet er summen av flere fakturaer pluss renter og gebyr, og at fakturanummeret er det samme som på en faktura som allerede er bokført. Er det lesbart, og er det duplikat av et annet bilag (også bilag som ikke er bokført, 1.4)?
3. **Selger.** Står det navn og org.nr. med «MVA»? Stemmer Brreg-statusen på fakturadatoen? Er selgeren utenlandsk og samtidig registrert i Norge, eller skal kjøper beregne mva selv? Står det VOEC-nummer på fakturaen?
4. **Kjøper.** Er fakturaen stilet til klienten (navn og org.nr., EHF `AccountingCustomerParty`)? Er den stilet til privatperson, eier, søsterselskap eller gammelt navn? Gjelder unntakene for utlegg med signert oppstilling eller fusjon?
5. **Innhold.** Er ytelsen beskrevet med leveringstid og mva i NOK per sats? Er satsen riktig for ytelsen (25/15/12/0, vann og avløp 15 %)? Er beløpet riktig regnet ut? Er det mva på en unntatt eller fritatt ytelse (husleie uten frivillig registrering, forsikring, bank, helse, kurs, gebyrer)?
6. **Tilknytning og tilordning.** Hva er kjøpt, og til hva? Er kjøpet til bruk i den avgiftspliktige virksomheten, og ikke til eier, aksjetransaksjon, unntatt eiendomssalg eller privat bruk? Signaler er leveringsadresse (vurder lokalt, skriv den aldri ut), tidspunkt, varetype og antall.
7. **Avskjæring.** Rammes kjøpet av § 8-3 a–g eller § 8-4? Kontroller enhetsprisen mot 200 kr for gaver. For bil: vognkortet eller klassen. For hotell: skill rom fra mat. Gir § 8-5 (samme art) fradrag likevel?
8. **Fordeling.** Har klienten delt virksomhet? Er fellesanskaffelser fordelt (§ 8-2), og med riktig og oppdatert nøkkel?
9. **Betaling.** Er beløpet 10 000 kr eller mer, og er det betalt via bank (§ 8-8)?
10. **Termin.** Ligger fakturadatoen i terminen? Er kreditnotaen ført med samme kode som originalen, og viser den til originalfakturaen (bokf.f. § 5-2-7)? Mangler henvisningen, men originalen kan identifiseres og behandlingen er riktig, er konklusjonen `ok_formmerknad`. Er noe ført dobbelt?
11. **Utland, import og omvendt avgiftsplikt.**
    - Fjernleverbar tjeneste fra utlandet: 86/88 for registrert klient, 87/89 for klient som ikke er registrert og er over grensen på 2 000 kr per kvartal.
    - Import: 81/83 etter tolldeklarasjonen, ikke speditørens mva-utlegg med kode 1.
    - Utenlandsk eller VOEC-mva skal holdes utenfor fradraget.
    - AE på EHF fra norsk selger av byggetjenester skal flagges.
12. **Spesialsignaler.** Kapitalvare (mva på minst 50 000 kr for maskiner eller 100 000 kr for bygg)? Hendelse som utløser justering? Uttak? Tegn på § 3-26 (egen byggeledelse)? Nærstående selger som går konkurs?
    - Salgsoppgjør for bolig med tilvalg eller endringsarbeid: vurder etter `fradragsregler.md` seksjon 7 punkt 5a (BFU 15/13). Sjekk om tilvalgsbeløpet tilsvarer entreprenørens tilvalgsfaktura, og om kjøperen av tilvalget er den samme som kjøperen av boligen.
    - § 3-26-ord i **entreprenørens** fakturatekst («byggherre», «innleide», «prosjektledelse») er fakta om hva som er kjøpt. De er ikke bevis for egen byggeledelse og skal ikke gjøre bilaget til et avvik. Noter dem til klientflagget.

**Formfeil kontra reell feil:** vurder om mangelen gir reell tvil om fradragsretten eller risiko for dobbelt fradrag. Er det bare en formfeil og selger faktisk er registrert, er konklusjonen «manglende dokumentasjon» med anbefaling om ny faktura. Det er ikke «avskåret fradrag». Er formfeilen uten betydning for fradraget eller bokføringen (kreditnota uten henvisning der originalen er entydig), er konklusjonen `ok_formmerknad`.

### Deterministisk bruk av EHF
For hvert bokført EHF-bilag:
- `sum(TaxSubtotal.TaxAmount der kategori=S)` skal ≈ sum av 2710–2714 på bilaget (registrert klient), med toleranse ±1 kr.
- For hver EHF-linje skal `ClassifiedTaxCategory` stemme med bokført kode. S/25 gir 1, S/15 gir 11, S/12 gir 13, og E/Z/O/G/K gir 0. AE gir omvendt avgiftsplikt: bare klimakvoter og gull innenlands, ellers feil.
- `PayableAmount` skal stemme med 2400 (`abs`).
- `AccountingCustomerParty` skal være klientens org.nr. `PartyTaxScheme` skal slutte på `MVA` når `TaxAmount` er over 0.
- `IssueDate` skal ligge i terminen.

Dette gir `sikkerhet: høy` for beløps- og kodeavvik. Fradragsretten (punkt 6–8) vurderes uansett faglig ut fra `Item/Name`. At EHF og postering stemmer, beviser ikke at det er fradragsrett.

For klient som ikke er registrert, skal alle posteringer ha kode 0 selv om `orderLines.vatType` er 1 eller 11. Da er det riktig at selgers kode avviker fra bokført kode. I stedet kontrolleres at `PayableAmount` er lik summen av kostnads- og aktiveringslinjene (brutto, `amount = amountGross`), altså at selgers mva ligger i kostnaden og ikke på 27xx.

---

## 4. Utdataformat per bilag

Én JSON-post per vurdert bilag, i en liste `vurderinger[]`. I tillegg kommer en `sammendrag`-blokk med dekning og summer.

```json
{
  "bilagsnr": "123-2026",
  "temp_nr": null,
  "bokfort": true,
  "voucher_id": 0,
  "dato": "2026-05-14",
  "fakturadato": "2026-05-12",
  "termin": "2026-3",
  "konto": 7350,
  "kontonavn": "Representasjon",
  "kode": "1",
  "sats_bokfort": 25.0,
  "belop_eks_mva": 4000.00,
  "mva_bokfort": 1000.00,
  "belop_brutto": 5000.00,
  "leverandor": "Eksempel Restaurant AS",
  "leverandor_orgnr": "999999999",
  "leverandor_mva_registrert": true,
  "kilde": ["posting", "ehf", "pdf", "brreg"],
  "regel_treff": ["R-AVSK-REPR"],
  "vurdering": "Kort faglig begrunnelse: hva er kjøpt, hvorfor behandlingen er riktig eller feil. Ingen personopplysninger.",
  "konklusjon": "avskaaret_fradrag",
  "anbefalt_korreksjon": {
    "konto": 7350,
    "kode": "0",
    "mva_belop_endring": -1000.00,
    "kostnad_endring": 1000.00,
    "termin_for_korreksjon": "2026-3",
    "tekst": "Reverser inngående mva, før brutto på 7350 med kode 0."
  },
  "hjemmel": "mval. § 8-3 første ledd bokstav e",
  "kilde_url": "https://www.skatteetaten.no/rettskilder/type/handboker/merverdiavgiftshandboken/gjeldende/M-8/M-8-3/M-8-3.6/",
  "sikkerhet": "høy",
  "trenger_sjur": false,
  "kjent_avvik_nokkel": "MVA|123-2026|R-AVSK-REPR|1000.00"
}
```

**Tillatte verdier for `konklusjon`:**
- `ok`
- `ok_formmerknad`: mva-behandlingen er riktig, men bilaget har en formfeil uten betydning for fradraget eller bokføringen, for eksempel kreditnota uten henvisning til original når originalen er entydig. Anbefal retting hos leverandøren. Telles ikke som avvik
- `ikke_salgsdokument`: dokumentet (typisk et bilag som ikke er bokført, se 1.4) er ikke et salgsdokument (purring, inkassovarsel, kontoutskrift, ordrebekreftelse) og skal ikke bokføres. Er dokumentet allerede bokført som kostnad, brukes i stedet `manglende_dokumentasjon`, eller `avskaaret_fradrag` når det er tatt fradrag
- `feil_kode`: feil kode eller sats, men fradragsretten er riktig bedømt
- `avskaaret_fradrag`: fradrag er tatt der det ikke gis (§§ 8-1 til 8-4, klient ikke registrert)
- `manglende_dokumentasjon`: bilag, kjøper eller «MVA» mangler, fremmedspråklig faktura, utlegg uten oppstilling
- `feil_termin`
- `tapt_fradrag`: fradrag er ikke tatt der det burde. Rapporteres, men har lavere prioritet
- `omvendt_avgiftsplikt_mangler`
- `maa_avklares`: skjønn eller usikker regel, se seksjon 6

**Tillatte verdier for `sikkerhet`:**
- `høy`: deterministisk (EHF, sats, klientstatus) eller en klar regel og klare fakta
- `middels`: klar regel, men fakta er utledet av tekst eller signaler
- `lav`: regelen er merket [USIKKER] eller [SKJØNN], eller fakta mangler

`trenger_sjur` er `true` når konklusjonen er `maa_avklares`, når sikkerheten er `lav`, eller når saken står på listen i seksjon 6.

`kjent_avvik_nokkel` har formatet `MVA|<bilagsnr>|<regel_id>|<beløp>`. Flyten (`npm run mva`) gjør råstrengen om til 10 hex-tegn (sha1, samme format som månedskontrollen i `tools/modeller.py`) før den matcher mot `kjente-avvik.md`, fordi «|» ødelegger markdown-tabellen. Hex-nøkkelen står i beslutningslista. Den brukes til å matche mot `kjente-avvik.md`, og endrer beløpet seg, blir det ny nøkkel. For bilag som ikke er bokført (bilagsnummer 0), brukes `T<tempNumber>` i stedet for bilagsnummeret, for eksempel `MVA|T874|R-IKKE-SALGSDOKUMENT|272700.67`. Bilagsnummer 0 skal aldri brukes i nøkkelen, fordi flere ikke-bokførte bilag da får samme nøkkel. Funn på klientnivå bruker `MVA|KLIENT|<regel_id>|<termin>`.

**Sammendrag:**

```json
{
  "klient": "…", "termin": "…", "mva_status": "VAT_REGISTERED",
  "populasjon": {"bilag": 0, "posteringer": 0, "inngaaende_mva": 0.0},
  "lest": {"bilag": 0, "vedlegg_lest": 0, "ehf_linjer_vurdert": 0, "ikke_lest": {"bilag": 0, "belop": 0.0}, "andel_belop": 0.0, "andel_mva": 0.0, "andel_selgers_mva_ehf": 0.0, "metode": "alle|risiko+tilfeldig"},
  "regeltreff": [{"regel_id": "R-DUPLIKAT-BELOP", "treff": 0, "filtrert": 0, "filtergrunn": "ulikt fakturanr og målepunkt"}],
  "datahull": ["bilagshoder hentet på id", "leverandører uten org.nr. i Tripletex", "supplierInvoice med beløp 0 filtrert"],
  "funn": {"ok": 0, "ok_formmerknad": 0, "ikke_salgsdokument": 0, "feil_kode": 0, "avskaaret_fradrag": 0, "manglende_dokumentasjon": 0, "feil_termin": 0, "tapt_fradrag": 0, "omvendt_avgiftsplikt_mangler": 0, "maa_avklares": 0},
  "netto_mva_effekt": 0.0,
  "klientnivaa": ["registreringsplikt § 3-26?", "kontoplan standardkoder", "særskilt melding omvendt avgiftsplikt Q2?"],
  "ikke_bokfort": 0,
  "til_andre_agenter": [{"agent": "balanse", "bilagsnr": "…", "funn": "leverandørbetaling ført mot 1370 i stedet for 2400"}],
  "usikre_regler_brukt": ["U3", "U5"]
}
```

Funn som ikke gjelder mva, men som agenten ser underveis (for eksempel feil motkonto ved betaling), føres i `til_andre_agenter` og vurderes ikke videre av mva-agenten.

Funn på klientnivå som ikke hører til ett bestemt bilag, føres i `klientnivaa`. Eksempler: mulig registreringsplikt, manglende særskilt mva-melding for omvendt avgiftsplikt, gammel fordelingsnøkkel og manglende kapitalvareregister.

---

## 5. Konklusjonsregler

- **AVVIK** (`feil_kode`, `avskaaret_fradrag`, `feil_termin`, `omvendt_avgiftsplikt_mangler`) krever både en regel i `fradragsregler.md` uten merket [USIKKER] og fakta som går klart fram av bilaget.
- Er regelen [USIKKER] eller [SKJØNN], er konklusjonen `maa_avklares`. Agenten oppgir da hva som mangler og hvilket spørsmål som skal stilles til kunden.
- Fradrag er aldri avskåret bare på grunn av kontonavnet. Vurderingen bygger på hva som faktisk er kjøpt.
- `ok_formmerknad` og filtrerte regeltreff er ikke AVVIK. Filtrerte treff skal likevel stå i `regeltreff` med begrunnelse, slik at Sjur kan se hva som er silt bort.
- Kjente avvik fra `kjente-avvik.md` med gyldig dato merkes «KVITTERT» og skal ikke telles som nye.

---

## 6. Eskalering: dette avgjør agenten aldri alene (`trenger_sjur: true`)

1. **Registreringsplikt** (§ 2-1, § 3-26 byggearbeid i egen regi, fremmed regi eller bygging på kjøpers tomt, konserninterne tjenester). Agenten flagger og lister opp de fakta som trengs.
2. **Beregning av uttak** etter § 3-26 eller §§ 3-21 til 3-25. Det gjelder verdsetting, påslag og timer.
3. **Fordelingsnøkler** etter § 8-2 og endring av relative koder.
4. **Justering og tilbakeføring** av kapitalvarer, og hvordan en overdragelse behandles.
5. **Tilbakegående avgiftsoppgjør** etter § 8-6.
6. **Kvalifisert uaktsomhet** og illojale opplegg (Invex-typen), og nærstående selgere i konkurs.
7. **Privat bruk hos eier** og kostnader som kan være skjult utbytte eller lønn. Både mva- og skattesiden skal til Sjur.
8. **Mobil- og bredbåndsandel** og annen fordeling av privat del etter skjønn.
9. Alle regler merket **[USIKKER]** (U1–U23 i `fradragsregler.md`).
10. Korreksjoner for **en termin som allerede er innlevert**, altså endringsmelding.
11. **Bilag som ikke er bokført:** å avvise, slette, bokføre eller kommentere et dokument i innboksen (for eksempel en purring registrert som faktura) er skrivende.
12. **Tilvalg og endringsarbeid** ved boligsalg (fradragsregler.md seksjon 7 punkt 5a, U23).
13. Alle **korreksjoner i det hele tatt**. Agenten foreslår bare. Ingen bilag, reverseringer, kodeendringer, kommentarer, vedlegg eller endringer i vatType eller vatSettings skal føres eller lastes opp i Tripletex uten at Sjur har bekreftet det i chat for akkurat den handlingen.

---

## 7. Hvor resultatet havner

1. **Rådata:** `vurderinger.json` og `sammendrag.json` i kjøringens midlertidige mappe. Sendes til orkestratoren, som lager den samlede mva-avstemmingen.
2. **Avstemmingsmodulen i Tripletex** (kommentar og vedlegg på avstemming av mva-kontoene 27xx for terminen). Agenten lager bare *utkastet*:
   - en kort kommentar per konto med antall funn og netto mva-effekt,
   - rapporten som vedlegg.

   Opplasting er et skrivende kall og krever bekreftelse fra Sjur. Endepunktet er ikke verifisert i API-dokumentasjonen, så det må sjekkes i `docs/api-v2-indeks.json` før bruk.
3. **Excel som reserve** når modulen ikke kan brukes: Silfer-branding, lagret i `C:\Users\Sjur\Desktop\avstemminger\<Klient (id)>\<år>\`. Første fane er et sammendrag. Andre fane har én rad per vurdert bilag med feltene fra seksjon 4 og kolonnen «Nøkkel». Tredje fane har klientnivåfunn. Fjerde fane er metode og dekning.
4. **Kjente avvik:** Sjur kopierer «Nøkkel» og forklaringen inn i `kjente-avvik.md`. Agenten skriver aldri til filen selv.
5. Forbedringer i den eksisterende M4-kontrollen (`tools/kontroller/mva.py`, `TYPISK_UTEN_FRADRAG`) er foreslått i regelbasen, men filen er ikke endret. Endringer i repoet gjøres bare etter avtale.

---

## 8. GDPR

- Vedlegg (PDF og EHF) lastes ned bare til `scratchpad/mva-<klient>-<termin>/vedlegg/`, leses lokalt og **slettes når kjøringen er ferdig**. Det skal skje også når kjøringen feiler, altså i en `finally`-blokk.
- Helst leses vedleggene bare i minnet: fetch, parse, forkast.
- Tidligere pilotfiler i `scratchpad/pilot-vedlegg/` inneholder kontakt-e-post, telefon og kontonummer. De bør slettes. Sjur bekrefter.
- Output skal aldri inneholde fødselsnummer eller D-nummer, kontonummer eller IBAN, e-post, telefon, adresse eller navn på ansatte og privatpersoner. Det gjelder også navn på ENK-leverandører. Bruk «privatperson», «ansatt 1», «ENK-leverandør 1» eller initialer. Firmanavn, org.nr. for AS og beløp er greit.
- Leveringsadresser og kjøpernavn brukes bare lokalt som signal, for eksempel «levert til privatadresse». De gjengis aldri.
- Lønn vurderes bare aggregert per konto. `/employee` og `/salary` brukes ikke. For § 3-26 beskrives antall stillinger eller årsverk og funksjon (prosjektledelse eller byggeledelse) uten navn.
- `vurdering`-feltet og PDF-tekst skal gjennom `redact()` før de skrives til fil.
- Ingenting fra bilagene lagres i minne, notater eller logger utover den midlertidige mappen.

### 8.1 Fritekst: `redact()` er ikke nok
Piloten viste at `redact()` i `src/privacy.js` bare maskerer **navngitte felt**. Fritekst går gjennom umaskert. Disse kildene lekket personopplysninger i piloten:
- **Kontonavn:** 2915/2916 hadde personnavn, og bankkontoene i 1920-serien hadde kontonummer i navnet.
- **Posteringstekster** og bilagsbeskrivelser.
- **EHF `Note`**, der en offentlig etat hadde saksbehandlers navn og e-post.
- **PDF-tekst**, der purringen hadde en PIN-kode til inkassoportalen.

Derfor gjelder dette til `privacy.js` har et eget fritekstfilter (endring i repoet gjøres bare etter avtale med Sjur):
1. **Kontonavn skrives ikke ut** for 1900–1999, 2900–2999 og andre kontoer som klientprofilen merker som personkontoer. Bruk bare kontonummeret («konto 2915»). For andre kontoer brukes standardnavnet i NS 4102, ikke klientens eget kontonavn, når navnet kan inneholde fritekst.
2. **Fritekstfilter i skriptet** før noe skrives til fil eller output. Det kjøres på posteringstekst, bilagsbeskrivelse, EHF `Note` og `Item/Name`, og PDF-tekst:
   - e-post: `[\w.+-]+@[\w-]+\.[\w.-]+`
   - telefon: `(\+47\s?)?(\d{2}\s?){4}` og `\d{3}\s?\d{2}\s?\d{3}`
   - kontonummer: `\b\d{4}[ .]?\d{2}[ .]?\d{5}\b` og IBAN `\b[A-Z]{2}\d{2}[A-Z0-9 ]{11,30}\b`
   - fødselsnummer og D-nummer: `\b\d{6}\s?\d{5}\b`
   - PIN, passord, kode og brukernavn: hele linjen fjernes når den inneholder `pin|passord|password|kode|brukernavn|user(name)?|login`
   - Filteret kjøres bare på fritekst, ikke på strukturerte beløps- og nummerfelt (telefonmønsteret treffer ellers beløp og fakturanummer).
   - Personnavn kan ikke filtreres pålitelig med regex. Agenten **siterer derfor aldri fritekst** fra bilag i `vurdering`, men skriver sin egen beskrivelse («faktura for grunnarbeid», «purring fra inkassobyrå»).
3. **EHF `Note` og PDF-tekst** brukes bare i minnet. Råteksten lagres ikke i JSON-filene i kjøringsmappen. Bare avledede felt (kategori, beløp, dato, fakturanummer, selgers org.nr.) lagres.
4. **Kontroll før levering:** kjør fritekstfilteret på alle utdatafiler og stopp leveransen hvis det gir treff.

### 8.2 Opprydding
- Alt i `scratchpad/mva-<klient>-<termin>/vedlegg/` og all rådata-JSON med posteringstekst slettes i `finally`.
- Skriptene kan beholdes når de ikke inneholder data.
- Eldre pilotfiler i `scratchpad/pilot-vedlegg/` (`599567404-att.pdf`, `653321450-edi.xml`, `682664536-edi.xml`) inneholder kontaktinfo og kontonummer og ligger fortsatt der etter piloten for T4 2026. De slettes når Sjur bekrefter.

---

## 9. Pilot – testklient T4 2026

Lesende prøvekjøring 24.09.2026 på en klient som ikke er registrert (`VAT_NOT_REGISTERED`, ikke i Merverdiavgiftsregisteret). Termin 4 (1.7.–31.8.2026). Ingen skriving i Tripletex eller repoene.

**Mekanikk**
- 13 API-kall for datauttrekk (3,4 s), 44 EHF-er hentet og parset (8,8 s), Brreg for 14 org.nr., forhåndssjekk på 296 posteringer (28 ms), 25 vedlegg med `pdftotext` (6,8 s). Nesten all tid gikk til faglig lesing.
- Lag (a): ingen fradrags- eller utgående koder, 27xx tomme, `amount = amountGross` på alle kostnads- og aktiveringslinjer, ingen kjøp fra utlandet (grunnlag Q3 0 kr).
- Lag (b): 25 bilag lest (62,7 % av kostnadsbeløpet) og alle EHF-linjer vurdert (84,7 % av selgers mva på bokførte EHF-er). Resultat: 21 ok, 2 manglende dokumentasjon, 2 må avklares. Netto mva-effekt 0 kr.
- Klientnivå: mulig registreringsplikt etter § 3-26/§ 2-1 (lønn og boligprosjekter i egen regi), tilvalg ved boligsalg (BFU 15/13), standardkode 1 på fire kostnadskontoer, og ett funn til balanseagenten (leverandørbetalinger mot 1370).

**Læring (innarbeidet i denne versjonen)**
1. `/ledger/voucher` med datofilter mangler bilag som bare har posteringer i terminen. Hent bilagshoder på id fra posteringene (1.1 kall 5).
2. Bilag som ikke er bokført, har ingen posteringer og ble oversett av alle posteringsregler. En purring registrert som faktura ble fanget bare via selgers org.nr. og fakturanummer fra EHF. Ny 1.4, ny konklusjon `ikke_salgsdokument` og `T<tempNumber>` i nøkkelen.
3. Leverandørregisteret er ufullstendig (tomt land, manglende eller feilstavet org.nr.). Selger identifiseres fra EHF/PDF/Brreg, og `uklassifisert` leverandører leses alltid.
4. EHF: `PartyTaxScheme` forekommer to ganger i varierende rekkefølge. Kjøpers «…MVA» og selgers «…MVA» er ikke bevis for registrering. Brreg er fasit.
5. `redact()` dekker ikke fritekst (kontonavn, posteringstekst, EHF `Note`, PDF-tekst). Nytt fritekstfilter og forbud mot å sitere fritekst (8.1).
6. Falske positiver: duplikat på faste nettleiebeløp, § 3-26-tekstmønstre fra entreprenørens egen fakturatekst, og kontoplanregelen per bilag. Reglene er beholdt, men treffene filtreres med begrunnelse eller aggregeres på klient- eller kontonivå.
7. Prosjektkontoer i 45xx må stå i klientprofilen. Ellers kan § 3-26-regelen bomme når bare 45xx har bevegelse.
8. Taket på 25 vedlegg var i strid med lag (c). Taket gjelder nå bare det tilfeldige utvalget, og det som ikke leses, rapporteres som `ikke_lest`.
9. Sjekklisten for klienter som ikke er registrert omfatter nå punkt 2, 4, 10, 11 og 12, ikke bare 10–11.
10. `vatType.id` er ikke `number`, og spesifikasjonskoder har `parentType` med 100 %. Bruk alltid `number`, og relativ kode krever `deductionPercentage` under 100.
11. Kreditnota uten henvisning til original, der originalen er entydig, har fått egen konklusjon: `ok_formmerknad`. Bilag uten salgsdokument forblir `manglende_dokumentasjon` også når det ikke har mva-effekt, fordi kravet følger av bokf.f. § 5-5-1.
12. Tilvalg ved salg av selveierseksjon: BFU 15/13 sier at tilvalg til samme kjøper som kjøper eiendommen normalt følger det unntatte eiendomssalget. Saken er likevel `maa_avklares` inntil kontrakt, tilvalgsavtale og tidspunkt for overtakelse er sett (fradragsregler.md 7 punkt 5a, U23).

**Åpent etter piloten:** de eldre pilotfilene er slettet (24.09.2026). Fritekstfilteret i `privacy.js` er ikke laget (repoendring krever avtale).
