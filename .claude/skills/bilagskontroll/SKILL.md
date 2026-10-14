---
name: "bilagskontroll"
description: "Kontroll av bokførte bilag for en periode i Tripletex: bilag uten vedlegg, feil periode, dubletter, mva-kode mot konto, observasjonskonti (1370, 7799), private kostnader i drift og runde manuelle poster, pluss en stikkprøve med registrert seed, med liste over det som må rettes. Fører ingenting. Lukker Tally-oppgaven «Kontroll av bilag». Bruk ved «kontroll av bilag», «bilagskontroll», «kontroller føringene for <måned>», «bilag uten vedlegg», «dubletter», «feil periode», «sjekk mva-kodene», «hva ligger på 1370»."
---

# Bilagskontroll

Stikkprøvekontroll av bilag bokført i måneden: maskinelle kontroller på alle posteringer, og én lesende agent på høyst 10 bilag som krever skjønn
pluss et tilfeldig utvalg med registrert seed (metode, arbeidspapir og avviksgrad: `docs/stikkprover.md`).
Skillen fører ingenting: føring er `bilagsforing`, og rettinger skjer etter ja. `mva-kontroll` leser de to månedlige resultatene i stedet for å lage
egen unntaksliste. Dubletter blant åpne reskontroposter er `reskontroavstemming`.

## Når

- Tally-oppgaven «Kontroll av bilag», den 15., for forrige måned. Ferdig først: «Bilagsbehandling» for måneden (`bilagsforing`).
- Brukeren oppgir klient og måned `ÅÅÅÅ-MM` (standard forrige måned).
- Steg 0 i tillegg: Missive (utkast til kunden i steg 7).

## Kundeinstruks

«Mva» (registrert fra dato, delvis fradrag) · «Bilagsføringsregler» (faste leverandører og konto, valuta, betalingsløsninger) · «Mangelliste» (konto for
manglende bilag, typisk 1370 eller 7799) · «Kjente avvik» · «Regnskapssystem og byrå» (V).

## Steg

Alle kall med `--client "<klient>"`. `<mappe>` = kort arbeidsmappe (for eksempel `%TEMP%\rr\bilagskontroll-ÅÅÅÅ-MM`); D = første dag etter måneden.

### 1. Modus
`npm run -s api -- GET /ledger/vatSettings fields=vatRegistrationStatus` og Enhetsregisteret (Tally `lookup_brreg`) → registrert, ikke registrert eller uklar.
Uklar (for eksempel VAT_APPLICANT i Tripletex og registrert i Brreg) stopper kontrollen til brukeren har avklart det.

### 2. Data (API)
- Posteringer i måneden:
  `npm run -s api -- GET /ledger/posting dateFrom=ÅÅÅÅ-MM-01 dateTo=<D> fields=id,date,description,account(number),vatType(number),amount,amountGross,invoiceNumber,supplier(id,organizationNumber),voucher(id,number,year,voucherType(id),attachment(id),ediDocument(id),reverseVoucher(id)) --sider --ut <mappe>/posteringer.json`
- Leverandørfakturaer fra måneden før, alle stadier (bilagsnummer 0 = ikke bokført):
  `npm run -s api -- GET /supplierInvoice invoiceDateFrom=<forrige mnd>-01 invoiceDateTo=<D> fields=id,invoiceNumber,invoiceDate,isCreditNote,amount,supplier(id,organizationNumber),voucher(id,number),originalInvoiceDocumentId --sider --ut <mappe>/fakturaer.json`
- Ikke bokførte bilag: `npm run -s api -- GET "/ledger/voucher/>nonPosted" includeNonApproved=true dateFrom=ÅÅÅÅ-MM-01 dateTo=<D> fields=id,date`.
- Samme mønster: `/voucherInbox/inboxCount` · `/ledger/voucherType` med `fields=id,name` (manuelle bilagstyper) · `/balanceSheet` med
  `dateFrom=ÅÅÅÅ-01-01 dateTo=<D> fields=account(number),balanceOut` → UB for observasjonskontoene.
- Leverandørene i måneden mot indeksen (`npm run -s leverandor -- finn <orgnr> --json`) og 12 måneders historikk på 2400 (`/ledger/posting` med
  `accountNumberFrom=2400 accountNumberTo=2400 fields=supplier(id) --sider`) → ny eller ukjent leverandør.
Behold bilagsnummer, konto, kode og beløp. Posteringstekst brukes bare i skriptet (signalordene i E2) og vises ikke.

### 3. Maskinelle kontroller
Kjør tabellen i `references/kontroller.md`: D1, M5, M4, M7, M8, D3, R6, D5, D2, E2, D7, D6. Hvert funn får alvor (STOPP, BLOKK, SPØR, FORKLAR, INFO)
og gjelder ett bilag eller én samlelinje. Klient som ikke er registrert: kodekontrollene for uregistrerte i samme fil i stedet for M4, M5 og M8.

### 4. Stikkprøve – unntaksliste (høyst 10) og tilfeldig utvalg, én lesende agent
1. **Unntakslista (målrettet):** kandidatene etter `references/kontroller.md` (skjønnskontoer, utenlandsk eller ukjent leverandør uten vurdering, funn som
   krever skjønn, og treff fra `utvalg` med `--metode maalrettet --over <V> --antall <ledige plasser>`). Sorter etter mva-effekt, så beløp. Resten telles som «utelatt».
2. **Tilfeldig utvalg:** `npm run -s utvalg -- --client "<klient>" --fra ÅÅÅÅ-MM-01 --til <siste dag i måneden> --konto 3000-4999,5900-7999 --metode tilfeldig --antall <n> --seed ÅÅÅÅMMDD --ut <mappe>/utvalg`
   (`--til` er med). n = 2–5 etter månedstabellen i `docs/stikkprover.md` (risiko fra kundetiltakene, ett trinn opp ved avvik forrige måned).
   Seed og populasjon (antall, sum) til arbeidspapiret (U1). Det målrettede uttrekket i punkt 1 bruker samme `--konto`.
3. Agenten får `docs/fradragsregler-kort.md`, begge listene (bilagsnr., konto, kode, beløp, leverandør med org.nr. og vurdering fra `leverandorindeks`) og
   dokumentene: `npm run -s dokument -- --client "<klient>" --bilag <nr-år> --ut <mappe>/dok` (EHF og leverandørfaktura: `--faktura <id>`) gir PDF og
   maskert `.txt`. Agenten leser `.txt` (skann: PDF-en med Read) og skriver ingenting.
4. Svarkontrakt per bilag: `konklusjon` (verdiene i `docs/fradragsregler-kort.md`), sikkerhet, hjemmel og anbefalt korreksjon, og for det tilfeldige
   utvalget Bestått/Avvik per testtrinn T1–T5 (U2–U6, `references/kontroller.md`). Ingen sitater fra bilaget.

### 5. Kjente avvik og leverandører
Funn med samme nøkkel og beløp som i «Kjente avvik» → «kjent, uendret». Nye vurderinger av en leverandør tilbys lagret i `leverandorindeks` etter ja.

### 6. Beslutningsliste og rettinger etter ja
Konklusjonene blir funn etter tabellen i `references/kontroller.md`, med grad (merknad, avvik, vesentlig avvik) og aggregering mot V etter
`docs/stikkprover.md` (U8). Lista har fire deler: må rettes · spørsmål · følg opp · nummerert ja-liste.
Svar som gjelder klienten varig (konto for en fast leverandør, mva-kode), tilbys lagret i kundeinstruksen.

**Stopp:** vesentlige avvik (feil ≥ V enkeltvis eller samlet, samme avvik som forrige måned) er meldt oppdragsansvarlig (`be_om_avklaring` på
«Kontroll av bilag» med `to` = oppdragsansvarlig, etter ja) før oppgaven fullføres eller perioden lukkes – til da skriver Claude meldingen og venter.

**Skriving (etter ja):** kjøres først uten `--bekreft` (viser kallet).
1. Reverser bilag som er bokført to ganger: `npm run -s api -- PUT "/ledger/voucher/<bilag-id>/:reverse" date=ÅÅÅÅ-MM-DD --client "<klient>" --bekreft`
   (dato i åpen periode; lønnsbilag kan ikke reverseres).
2. Korrigeringsbilag i åpen periode (feil periode; bank- og OCR-bilag med feil kode, med henvisning til originalen) og ompostering fra
   observasjonskontoen når bilaget er kommet: føres med `periodisering` (føringskontroll og tørrkjøring der).

**Bare i Tripletex-UI:**
1. Bytt mva-kode eller beløp på bilaget når perioden er åpen (bank- og OCR-bilag gir 422: korrigeringsbilag i punkt 2 over).
2. Avvis dokumenter i bilagsmottaket som er purring eller kopi av et bokført bilag.

Les på nytt (steg 2) når brukeren sier at det er gjort. Til da står punktet som «ikke gjort».

### 7. Til kunden
Bilag som mangler og spørsmål bare kunden kan svare på, uten byråets vurderinger og hjemler → Missive-utkast etter ja, som punktliste.

## Svar

- Første linje: port · antall bilag i måneden · kontrollert maskinelt · lest av agent (og «utelatt n») · stikkprøve n (seed, bestått, avvik).
- Funn-tabellen (ID · Bilag/konto · Beløp · Status · Forslag · Krever): må rettes først, så spørsmål, så følg opp; graden står først i Forslag.
  Høyst 10 linjer; resten står i arbeidsboka.
- Nummerert ja-liste til slutt.
- Firmanavn på leverandører er greit; enkeltpersonforetak er «ENK-leverandør», privatpersoner «privatperson». Ingen bilagstekster.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `BILAG`, periode `ÅÅÅÅ-MM`, samling `Bilagskontroll ÅÅÅÅ`, oppgave «Kontroll av bilag»): `Bilagskontroll ÅÅÅÅ-MM <Klient>.xlsx` med arkene Sammendrag · Funn · Bilagsvurdering · Stikkprøve (arbeidspapiret) · Til kunden.
Arbeidsboka har byråets vurderinger og er intern: arkiver den rett etter opplasting (`organize_document`, `archived: true`). Kunden får «Til kunden» som Missive-utkast.
Fullfør i Tally: se `tally-gjoremal`. «Kontroll av bilag» fullføres når beslutningslista er levert, alle BLOKK-funn er rettet eller kvittert som kjent avvik, og vesentlige avvik er meldt oppdragsansvarlig. Kommentaren inneholder måned, antall bilag kontrollert, stikkprøven (antall, seed), funn per alvor og hva som venter.

## Fallgruver

- `/ledger/posting` har ikke bilagsfilter. Grupper per `voucher.id` i skriptet; et leverandørbilag er 2400 kredit + kostnad uten banklinje. `dateTo` er eksklusiv.
- Bilag som ikke er bokført (bilagsnummer 0 på leverandørfakturaen) ser ingen av posteringskontrollene. De telles under D6.
- Samme leverandør kan ligge to ganger (skrivefeil, uten org.nr.). Dubletter matches på org.nr. via `leverandorindeks`, ikke bare Tripletex-id.
- Fakturanummer normaliseres før sammenligning (store bokstaver, bare A–Z og 0–9, uten innledende nuller).
- Kontonavn med «fradragsberettiget» i NS 4102 gjelder inntektsskatt, ikke mva.
- Personbil og varebil klasse 2 skilles ikke på konto. Fradrag på bilkonto går til unntakslista, aldri rett til BLOKK.

## Referanser

Kontroller: D1, D2, D3, D5, D6, D7, E2, M4, M5, M7, M8, R6, U1–U6, U8 (`docs/kontrollkatalog.md`). Terskler, alvor, unntaksliste, testtrinn og konklusjoner:
`references/kontroller.md`. Utvalg, arbeidspapir og avviksgrad: `docs/stikkprover.md`.
Regler: `docs/fradragsregler-kort.md` (agentens svarkontrakt), `docs/fradragsregler.md` (rettsgrunnlag, grep på paragraf).
Naboskills: `bilagsforing`, `mva-kontroll`, `leverandorindeks`, `reskontroavstemming`, `kundeinstruks`, `tally-gjoremal`.
