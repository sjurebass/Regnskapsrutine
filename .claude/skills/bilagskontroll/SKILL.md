---
name: "bilagskontroll"
description: "Kontroll av bokførte bilag for en periode i Tripletex: bilag uten vedlegg, feil periode, dubletter, mva-kode mot konto, observasjonskonti (1370, 7799), private kostnader i drift og runde manuelle poster, med liste over det som må rettes. Fører ingenting. Lukker Tally-oppgaven «Kontroll av bilag». Bruk ved «kontroll av bilag», «bilagskontroll», «kontroller føringene for <måned>», «bilag uten vedlegg», «dubletter», «feil periode», «sjekk mva-kodene», «hva ligger på 1370»."
---

# Bilagskontroll

Stikkprøvekontroll av bilag bokført i måneden: maskinelle kontroller på alle posteringer, og én lesende agent på høyst 10 bilag som krever skjønn.
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

### 1. Modus
`get_vat_registration_status` og Enhetsregisteret (Tally `lookup_brreg` eller `lookup_company_in_brreg`) → registrert, ikke registrert eller uklar.
Uklar (for eksempel VAT_APPLICANT i Tripletex og registrert i Brreg) stopper kontrollen til brukeren har avklart det.

### 2. Data – ett `tripletex_run_script`
- `search_ledger_postings` for måneden: 4000–7999, 1000–1999 og 2700–2799 (bilag-id og -nr., dato, konto, mva-kode, beløp, bruttobeløp, leverandør).
- `search_supplier_invoices` fra måneden før, alle stadier: status, fakturanr., leverandør med org.nr., fakturadato, bilagsnr., kreditnota, vedlegg/EHF.
- `get_voucher_inbox_count`; `search_voucher_types` (manuelle bilagstyper); `get_balance_sheet` UB for observasjonskontoene.
- Leverandørene i måneden mot `data/leverandorer.json` og 12 måneders historikk på 2400 → ny eller ukjent leverandør.
Behold bilagsnummer, konto, kode og beløp. Posteringstekst brukes bare i skriptet (signalordene i E2) og returneres ikke.

### 3. Maskinelle kontroller
Kjør tabellen i `references/kontroller.md`: D1, M5, M4, M7, M8, D3, R6, D5, D2, E2, D7, D6. Hvert funn får alvor (STOPP, BLOKK, SPØR, FORKLAR, INFO)
og gjelder ett bilag eller én samlelinje. Klient som ikke er registrert: kodekontrollene for uregistrerte i samme fil i stedet for M4, M5 og M8.

### 4. Unntaksliste – høyst 10 bilag, én lesende agent
1. Velg kandidatene etter `references/kontroller.md` (skjønnskontoer, utenlandsk eller ukjent leverandør uten vurdering, funn som krever skjønn).
   Sorter etter mva-effekt, så beløp. Resten telles som «utelatt».
2. Agenten får `docs/fradragsregler-kort.md`, lista (bilagsnr., konto, kode, beløp, leverandør med org.nr. og vurdering fra `leverandorindeks`) og
   lenker fra `get_voucher_document`. Finner ToolSearch et verktøy som leser bilagsdokumentet eller EHF-en, får agenten bruke det. Agenten skriver ingenting.
3. Svarkontrakt per bilag: `konklusjon` (verdiene i `docs/fradragsregler-kort.md`), sikkerhet, hjemmel og anbefalt korreksjon, uten sitater fra bilaget.
4. Ingen agent når lista er tom.

### 5. Kjente avvik og leverandører
Funn med samme nøkkel og beløp som i «Kjente avvik» → «kjent, uendret». Nye vurderinger av en leverandør tilbys lagret i `leverandorindeks` etter ja.

### 6. Beslutningsliste og rettinger etter ja
Konklusjonene blir funn etter tabellen i `references/kontroller.md`. Lista har fire deler: må rettes · spørsmål · følg opp · nummerert ja-liste.
Svar som gjelder klienten varig (konto for en fast leverandør, mva-kode), tilbys lagret i kundeinstruksen.

**Krever skriving utenfor MCP: Tripletex-UI (eller API-kobling):**
1. Bytt mva-kode eller beløp på bilaget når perioden er åpen. Bank- og OCR-bilag gir 422: før et korrigeringsbilag med henvisning til originalen.
2. Reverser bilag som er bokført to ganger. Feil periode: korrigeringsbilag i åpen periode.
3. Avvis dokumenter i bilagsmottaket som er purring eller kopi av et bokført bilag.
4. Ompostér fra observasjonskontoen når bilaget er kommet.
5. Les på nytt når brukeren sier at det er gjort. Til da står punktet som «ikke gjort».

### 7. Til kunden
Bilag som mangler og spørsmål bare kunden kan svare på, uten byråets vurderinger og hjemler → Missive-utkast etter ja, som punktliste.

## Svar

- Første linje: port · antall bilag i måneden · kontrollert maskinelt · lest av agent (og «utelatt n»).
- Funn-tabellen (ID · Bilag/konto · Beløp · Status · Forslag · Krever): må rettes først, så spørsmål, så følg opp. Høyst 10 linjer; resten står i arbeidsboka.
- Nummerert ja-liste til slutt.
- Firmanavn på leverandører er greit; enkeltpersonforetak er «ENK-leverandør», privatpersoner «privatperson». Ingen bilagstekster.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `BILAG`, periode `ÅÅÅÅ-MM`, samling `Bilagskontroll ÅÅÅÅ`, oppgave «Kontroll av bilag»): `Bilagskontroll ÅÅÅÅ-MM <Klient>.xlsx` med arkene Sammendrag · Funn · Bilagsvurdering · Til kunden.
Arbeidsboka har byråets vurderinger og er intern: arkiver den rett etter opplasting (`organize_document`, `archived: true`). Kunden får «Til kunden» som Missive-utkast.
Fullfør i Tally: se `tally-gjoremal`. «Kontroll av bilag» fullføres når beslutningslista er levert og alle BLOKK-funn er rettet eller kvittert som kjent avvik. Kommentaren inneholder måned, antall bilag kontrollert, funn per alvor og hva som venter.

## Fallgruver

- `search_ledger_postings` har ikke bilagsfilter. Grupper per bilag-id i skriptet; et leverandørbilag er 2400 kredit + kostnad uten banklinje.
- Bilag som ikke er bokført (bilagsnummer 0 på leverandørfakturaen) ser ingen av posteringskontrollene. De telles under D6.
- Samme leverandør kan ligge to ganger (skrivefeil, uten org.nr.). Dubletter matches på org.nr. via `leverandorindeks`, ikke bare Tripletex-id.
- Fakturanummer normaliseres før sammenligning (store bokstaver, bare A–Z og 0–9, uten innledende nuller).
- Kontonavn med «fradragsberettiget» i NS 4102 gjelder inntektsskatt, ikke mva.
- Personbil og varebil klasse 2 skilles ikke på konto. Fradrag på bilkonto går til unntakslista, aldri rett til BLOKK.

## Referanser

Kontroller: D1, D2, D3, D5, D6, D7, E2, M4, M5, M7, M8, R6 (`docs/kontrollkatalog.md`). Terskler, alvor, unntaksliste og konklusjoner: `references/kontroller.md`.
Regler: `docs/fradragsregler-kort.md` (agentens svarkontrakt), `docs/fradragsregler.md` (rettsgrunnlag, grep på paragraf).
Naboskills: `bilagsforing`, `mva-kontroll`, `leverandorindeks`, `reskontroavstemming`, `kundeinstruks`, `tally-gjoremal`.
