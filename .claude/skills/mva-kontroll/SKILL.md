---
name: "mva-kontroll"
description: "Kontroll av mva for én klient og én termin før innsending: forutsetninger fra bank-, reskontro- og bilagskontrollen, 27xx og oppgjørskonto 2740 per måned, rimelighet per sats, unntaksliste på høyst 10 bilag med fradragsvurdering, kontroll av utkastet mot hovedboken og beslutningsliste med portfarge. Lukker Tally-oppgaven «MVA-kontroll». Bruk ved «mva-kontroll for <klient>», «avstem mva», «mva-avstemming», «kontroller mva for terminen», «mva termin <n> for <klient>», «klar til å sende mva», «nå har jeg opprettet utkast», «sjekk 2740»."
---

# Mva-kontroll før innsending

Lett kontroll av mva for én klient og én termin, med en kort beslutningsliste. Skillen leser resultatene fra `bankavstemming`, `reskontroavstemming` og
`bilagskontroll` og gjør bare terminkontrollene selv. Oversikt over alle klienter og etterarbeid etter sending: `mva-innlevering`.
Tunge kontroller (kontoplan, § 3-26, registreringsplikt, gamle reskontroposter) hører til `aarsoppgjoer-forberedelse`.

## Når

- Tally-oppgaven «MVA-kontroll», den 25. i måneden før fristen. Én klient om gangen; klient, termin og år må være sagt. Uklart → spør.
- Ferdig først: «Bilagsbehandling», «Bankavstamming» og «Kontroll av bilag» for begge månedene, og reskontro-oppgavene for terminens siste måned.
- Hold deg til terminen; tidligere terminer røres ikke. Steg 5 kjøres når regnskapsføreren sier «nå har jeg opprettet utkast».

## Kundeinstruks

«Mva» (registrert fra dato, termin, delvis fradrag, omvendt avgiftsplikt) · «Bank» (kontoer uten bankfeed) · «Kjente avvik» (samme nøkkel og beløp → «kjent, uendret»).

## Steg

### 1. Forutsetninger – les resultatet, ikke gjør arbeidet på nytt
- **Modus:** `get_vat_registration_status` og Enhetsregisteret (`lookup_company_in_brreg`) → registrert, ikke registrert eller uklar.
  Uklar (for eksempel VAT_APPLICANT i Tripletex og registrert i Brreg) stopper kontrollen til brukeren har avklart det.
- **Bilag:** `get_voucher_inbox_count` = 0 og ingen ikke-bokførte leverandørfakturaer datert i terminen (`search_supplier_invoices`). Ellers → `bilagsforing`.
- **Bank:** `get_bank_reconciliation_periods` → alle kontoer lukket for begge månedene, eller åpne poster forklart i «Bankavstamming». Ellers → `bankavstemming`.
- **Reskontro:** «Avstemming kundereskontro» og «Avstemming leverandørreskontro» for siste måned fullført (Tally `list_tasks`) med arbeidsboka i
  samlingen `Reskontro ÅÅÅÅ` (`list_documents`). Konstatert tap på en kundefordring gir rett til å kreve tilbake utgående mva (mval. § 4-7); konkurs alene er ikke konstatert tap.
- **Bilagskontroll:** «Kontroll av bilag» for begge månedene fullført, med arbeidsboka i `Bilagskontroll ÅÅÅÅ`. Åpne BLOKK-funn (M4, M5, M7, M8, D3, R6)
  går rett inn i beslutningslista. Mangler en måned, kjøres steg 3 for den måneden.
- Mangler noe: si hva og pek på skillen. Brukeren velger mellom å vente og å fortsette med «ikke kontrollert» på punktet.

### 2. Mva-kontoene (M3 og 2740)
Ett `tripletex_run_script`: `get_balance_sheet` 2700–2799 per månedsslutt (IB, endring, UB) og `search_ledger_postings` for terminen med mva-kode
(konto, kode, beløp, bruttobeløp, bilagsnr.). Behold summer per kode og måned; ingen tekster.
- **Sats (M3):** utgående mva per kode mot 25, 15 eller 12 % av grunnlaget. Avvik over 1 % → funn med koden og bilagene som skiller.
- **2740 per måned:** IB, oppgjørsbilaget for forrige termin, innbetaling eller tilbakebetaling, og saldo per månedsslutt. Hver saldo får én forklaring
  (for eksempel «skyldig termin 3, betalt 12.09»). Saldo uten forklaring → funn.
- **27xx:** før «Opprett» er saldoen på 2700–2739 terminens mva. Posteringer i terminen med feil kode listes med bilagsnummer.
- **Ikke registrert:** 27xx skal være tom, bortsett fra omvendt avgiftsplikt (kode 87, 89, 92). Kjøp av fjernleverbare tjenester fra utlandet over 2 000 kr
  i et kvartal krever melding for omvendt avgiftsplikt (frist 10.5, 31.8, 10.11 og 10.2).

### 3. Unntaksliste – bare når en bilagskontroll mangler
Samme utvalg, agent og svarkontrakt som `bilagskontroll` steg 4 (`.claude/skills/bilagskontroll/references/kontroller.md`): høyst 10 bilag sortert etter
mva-effekt, én lesende agent med `docs/fradragsregler-kort.md`, oppslag i `leverandorindeks` og lenker fra `get_voucher_document`. Ingen agent når lista er tom.
Nye vurderinger av en leverandør tilbys lagret i `leverandorindeks` etter ja.

### 4. Beslutningsliste og rettinger etter ja
Lista (se Svar) har det som må rettes først. Hvert punkt rettes etter ja. Svar som gjelder klienten varig, tilbys lagret i kundeinstruksen.

**Krever skriving utenfor MCP: Tripletex-UI (eller API-kobling):**
1. Rett mva-koden eller beløpet direkte på bilaget når terminen er åpen og bilaget kan endres.
2. Bank- og OCR-bilag gir 422: før et korrigeringsbilag i terminen som reverserer feil linje og fører riktig, med henvisning til originalen.
3. Utlign poster som går i null (én konto, én motpart, sum 0,00) i Tripletex-UI.
4. Les på nytt når brukeren sier at det er gjort, og oppdater lista. Til da står punktet som «ikke gjort».

### 5. Utkastet (M1) – etter at regnskapsføreren har trykket «Opprett»
- Linjene per kode (grunnlag og mva) mot hovedboken for terminen. Utkastet viser hele kroner avkortet; under 1 kr per linje er ikke avvik.
  Kode 86 gir to linjer (ut og inn). Summen av linjene = beløp å betale eller til gode, også i hovedboken.
- Fortegn: en linje med fortegn motsatt av det Skatteetaten forventer (typisk fradragslinjen når kreditnotaer fra tidligere terminer er større enn kjøpene)
  må ha merknad, for eksempel «kreditnota».
- Oppgjørsbilaget nullstiller 2700–2739 mot 2740 og er datert siste dag i terminen. Etterpå er 2740 i siste måned −(beløp å betale), eller + ved tilgode.
- MCP-en har ikke eget verktøy for utkastet (sjekk med ToolSearch). Ellers gir brukeren linjene fra Tripletex-UI.

## Svar

- Første linje: port (grønn/gul/rød etter `docs/skill-mal.md`) · termin · beløp å betale eller til gode ifølge hovedboken.
- Funn-tabellen (ID · Konto/motpart · Beløp · Status · Forslag · Krever): må rettes og spørsmål først, så følg opp. Høyst 10 linjer.
- Nummerert liste over det som krever ja. Kjente avvik står som én linje «kjent, uendret».
- Aldri bilagstekster eller leverandørtekster; bilagsnummer, konto, kode og beløp holder.

## Lever

Lever: `silfer-rapport` (spec.json → xlsx/pdf) + `docs/dokumentlagring.md` (kategori `MVA_RAPPORT`, periode `ÅÅÅÅ-T<n>`, samling `Mva ÅÅÅÅ`, oppgave «MVA-kontroll»): 2740-notatet som PDF (mønster `silfer-rapport/scripts/eksempler/notat_2740.json`: saldo per månedsslutt med forklaring, bevegelser, terminene i året, kontroll per kode).
**Krever skriving utenfor MCP: Tripletex-UI (eller API-kobling):** i avstemmingsmodulen får 2740 notatet i begge månedene, og 27xx i siste måned er 0. Dokumentert saldo og status «avstemt» settes først etter at notatet er lastet opp.
Fullfør i Tally: se `tally-gjoremal`. «MVA-kontroll» fullføres når beslutningslista er grønn (eller gul med alt avklart) og meldingen er klar til innsending. Kommentaren inneholder termin, port, beløp å betale eller til gode og hva som gjenstår.

## Fallgruver

- Ikke avstem hele balansen og ikke fullfør BALANCE i modulen uten at brukeren ber om det. 19xx dokumenteres i `bankavstemming`, 1500/2400 i `reskontroavstemming`.
- 2740 blir automatisk avstemt i begge terminmånedene først når mva-avstemmingen er fullført etter innsending (`mva-innlevering`). 2700–2739 blir aldri det.
- Registrert midt i året: terminnummeret i Tripletex teller fra registreringsdatoen. Sjekk at perioden er riktig.
- Notatet lages ikke før 2740 er forklart for begge månedene. «Mangler forklaring» skal ikke stå i et notat som lastes opp.
- En bilagskontroll som er eldre enn siste føring i måneden, er utdatert. Kjør `bilagskontroll` på nytt for den måneden.

## Referanser

Kontroller: M1, M3 (her); M4, M5, M7, M8, D3, R6 (`bilagskontroll`); R1–R13 (`reskontroavstemming`); B1–B5 (`bankavstemming`); M2, M6 (`mva-innlevering`).
Regler: `docs/fradragsregler-kort.md` (agentens svarkontrakt), `docs/fradragsregler.md` (rettsgrunnlag). Naboskills: `leverandorindeks`, `kundeinstruks`, `aarsoppgjoer-forberedelse`, `tally-gjoremal`.
