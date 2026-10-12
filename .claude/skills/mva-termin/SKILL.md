---
name: mva-avstemming
description: "Lett mva-avstemming per termin for én eller flere navngitte Tripletex-klienter. Ett skript kjører maskinelt reskontro, bank, mva-koder, EHF, dubletter, ubehandlede bilag og skattekonto. En agent brukes bare på en kort unntaksliste. Resultatet er en kort beslutningsliste. Deretter bank og dokumentasjon i avstemmingsmodulen, reell gjennomgang av 1500/2400, kontroll av utkastet før og etter «Opprett», 2740 og fullføring etter innsending. Kontrollene som hører til årsoppgjøret, kjøres med --aarlig. Klienter som ikke er mva-registrert har egen modus. Trigger: «avstem mva», «mva-avstemming», «avstem mva-terminen», «klar til å sende mva», «sjekk mva-behandlingen», «mva termin <n> for <klient>», «nå har jeg opprettet utkast», «sendt og synkronisert»."
---

# Mva-avstemming (termin-flyt)

**Budsjett:** Skriptet gjør jobben og bruker ingen tokens. Claude leser bare JSON-sammendraget. Unntakslista koster mest (én agent, ca. 100–130k tokens ved 9–10 bilag).

## Faste regler
- **Klient og termin:** Jobb bare mot klienter Sjur har navngitt. Er termin eller år uklart, spør. Hold deg til terminen: BALANCE er månedlig, så én termin er to måneder. Tidligere terminer røres ikke.
- **Skriving:** krever ja i chat, per handling, med GET før og etter. Sjur har gitt varig tillatelse (25.09.2026) til dette:
  - opplasting av dokumentasjon til avstemmingsmodulen
  - status og dokumentert saldo på balanselinjer etter at dokumentasjonen er lastet opp
  - utligning av åpne poster som går i null (`modul utlign` og `modul lukk`, tillatt i `.claude/settings.local.json`)
- **Blokkert skriving:** Blir et skrivekall stoppet (tillatelsesregler, 403, 422), si klart «ikke gjort» og hva som må til. Skriv aldri noe som kan leses som at det er utført.
- **Rettinger:** Rett direkte på bilaget når det går. Bank- og OCR-bilag kan ikke endres via API-et (422). Da lages et korrigeringsbilag etter ja, og det utlignes mot den opprinnelige posten.
- **Det Claude aldri gjør:**
  - Sender inn mva-meldingen. Sjur gjør det med ID-porten, som varer 10 minutter og gjelder alle klienter.
  - Oppretter meldingen («Opprett») eller synkroniserer med Skatteetaten.
  - Godkjenner betalinger (`:approve`) eller kontrollerer egen avstemming (`:control`).
  - Låser perioden. Det finnes ikke noe API-kall for det, så Sjur gjør det i Tripletex.
  - Sender e-post.
- **Betaling:** opprettes i Tripletex og legger seg til godkjenning hos kunden. API-brukeren får 403, så inntil videre gir Claude bare beløp, KID og forfall.
- **Feil i levert termin:** rettes i inneværende termin.
- **Dokumentasjon:** Så mye som mulig lagres som vedlegg og kommentarer i avstemmingsmodulen. Notater lages som Silfer-PDF og lagres også i `<Kunde>/<år>/Dokumentasjon/`. Kontoutskrifter og bankavstemmings-PDF-er legges i `Bankavstemminger/`.
- **Personvern:** Ingen personopplysninger i chat eller filer. Unntak: kundenavn i reskontrodokumentasjon (Sjur 25.09.2026). Arbeidsdata ligger i `%LOCALAPPDATA%\silfer-mva\`. Fritekst siteres aldri.

## Verktøy
- **Kjøring:** Alt kjøres fra `C:\Users\Sjur\Tripletex API`. Bruk PowerShell for `npm run api -- GET /sti`. Git Bash gjør stien om til en Windows-sti, med mindre `MSYS_NO_PATHCONV=1` er satt.
- **`npm run -s mva -- "<klient>" --aar <år> --termin <n> --json [--gjenbruk] [--aarlig]`:** kontrollene og beslutningslista.
- **`npm run -s modul -- <kommando> --client "<klient>" ...`:** avstemmingsmodulen, bank og reskontro:
  - `perioder --aar --type BALANCE|VAT_GENERAL_INDUSTRY` og `linjer --id [--konto 19]`: finne avstemminger og balanselinjer
  - `bankpdf --konto --maaned ÅÅÅÅ-MM --ut <mappe>`: Tripletex' bankavstemmings-PDF, bare for lukkede måneder
  - `last-opp --id --ref <konto-id> --fil <sti> --bekreft [--erstatt]`: vedlegg på en linje. `referenceId` for balanselinjer er konto-id-en.
  - `sett-status --id --konto <konto-id> --status RECONCILED [--dokumentert <beløp>] --bekreft`: nekter å sette avstemt når differansen ikke er 0
  - `utlign --konto 1500|2400 [--bekreft]` og `lukk --ids a,b --bekreft`: lukker bare grupper med én konto, én motpart og sum 0,00
  - `mva-oversikt --id` og `fullfor --id [--bekreft]`: fullfører en mva-avstemming bare når hovedbok, rapportert og Skatteetaten stemmer på hver linje. En balanseavstemming fullføres bare når alle linjene har status og avstemte linjer har 0 i differanse.
  - `laas-opp --id --bekreft`: låser opp en fullført avstemming, for eksempel for å bytte et vedlegg. Krever ja fra Sjur, og avstemmingen fullføres igjen med `fullfor`.
  - `kontroll-utkast --aar --termin`: utkastet eller meldingen mot hovedboken per kode, fortegn og merknad, oppgjørsbilaget, 27xx, levering og betalingsinfo
  - `notat-2740 --aar --termin --forklaring-MM "beløp|tekst"`: Silfer-PDF med alt beregnet unntatt forklaringen per måned, som er en faglig vurdering og gis inn. Havner i `<Kunde>/<år>/Dokumentasjon/`.
  - `reskontro-vurdering --dato ÅÅÅÅ-MM-DD --vurderinger <fil.json>`: kategorier, Brreg og vedlegg beregnes. Vurdering og tiltak per motpart står i JSON-fila (`{konklusjon, kunder[], leverandorer[], tiltak[]}`). Uten fila markeres notatet «vurdering mangler».
- **Parallellitet:** Stegene for én klient avhenger av hverandre (skript → agent → `--gjenbruk` → skriving). Kjør flere klienter parallelt, ikke stegene for én klient.

## Per termin
1. **Kjør skriptet.** Les bare JSON-svaret: `port`, `antall`, `punkter`, `tilVurdering`, `mappe`.
2. **Unntakslista** (`tilVurdering`):
   - Er den tom, hopp over steget.
   - Ellers får én agent `references/fradragsregler-kort.md`, `<mappe>/overlevering.json` og vedleggene i `<mappe>/vedlegg/`. Agenten skriver `vurdering.json`. Kjør så skriptet på nytt med `--gjenbruk`.
   - En ny kjøring uten `--gjenbruk` arkiverer `vurdering.json`. Varige svar fra Sjur legges derfor i `klientprofil.md` (under Notater) eller i `kjente-avvik.md`.
3. **Vis resultatet:** portfarge, én linje per punkt (det som må rettes og spørsmål først), lenke til `beslutning-1.md` og en nummerert liste over det som krever ja.
4. **Bank (BK1/BK7):**
   - **BK1:** Sjur fører åpne poster mot bilag.
   - **Kontoutskrifter fra Sjur:** koble dem til konto ut fra kontonummer og utgående saldo, og kontroller at saldoen stemmer før opplasting.
   - **Manuell avstemming:** `POST /bank/reconciliation` (MANUAL, saldo fra utskriften), deretter `PUT /bank/reconciliation/internal/approve`. Er en senere måned allerede godkjent, gir det 422. Da åpnes den senere måneden, den tidlige avstemmes, og den senere lukkes igjen. Sjur skal si ja til å åpne.
   - **Uten kontoutskrift og med saldo 0 i hovedboken:** avstem mot 0 etter Sjurs ja.
   - **Lukk bankmånedene** med differanse 0.
   - **Last opp** Tripletex-PDF og kontoutskrift på 19xx-linjen i begge månedene. Gjelder bare kontoer med avstemming eller bevegelse.
5. **Balanselinjer:** Sett dokumentert saldo og avstemt først etter at dokumentasjonen er lastet opp.
6. **Reskontro 1500/2400:** en reell vurdering av hver åpen post, ikke bare sum mot hovedbok (se minnet «reskontro-gjennomgang»).
   - Bare poster datert i inneværende år. Eldre poster blir én samlelinje, «vurderes i årsoppgjøret».
   - Sjekk: forfalte kundekrav (Brreg: konkurs), ufordelte innbetalinger, leverandørfakturaer forfalt uten betaling, betalinger uten faktura (manglende fradrag), dobbeltbetalinger og refusjoner ført som gjeld. Innbetalinger fra Skatteetaten på 2400 flyttes til riktig konto, for eksempel 2600.
   - Utlign det som går i null. Last opp vurderingsnotatet med tiltaksliste på 1500/2400 i siste måned, og sett status.
7. **Før innsending:**
   - utkastet (`/vatReturns/>vatTerm`) mot hovedboken per kode, `vatTermAmount` og `validateCreate`
   - linjer med fortegn motsatt `expectedSign` trenger merknad. Eksempel: kode 1 blir netto negativ når fakturaer fra tidligere terminer er reversert.
   - lønn: A07 mot hovedbok (skillen lonnsavstemming-a07)
   - 2740: notat per 31.xx for begge månedene, lastet opp, og status avstemt
8. **Etter «Opprett» (Sjur):**
   - kontroller linjene, merknadene og oppgjørsbilaget, som nullstiller 27xx mot 2740 og er datert siste dag i terminen
   - oppdater 2740 i siste måned: dokumentert saldo = −(beløp å betale), og erstatt notatet
9. **Etter «Send» og «Synk» (Sjur):**
   - `vatReturns/status`: WAITING_FOR_REPLY går over til RECEIPT_RECEIVED
   - `paymentInfo`: KID, beløp og forfall. Forfallet flyttes når fristen faller på en helg.
   - når Skatteetatens tall finnes (de kan komme timer etter kvitteringen og krever ny synk): `modul fullfor`, og oppdater 2740-notatet til «levert»
   - balanseavstemmingen for siste måned kan bli fullført samtidig (august T4 2026 var COMPLETED rett etterpå). Skal notatet byttes, kreves `laas-opp` (etter ja), `last-opp --erstatt` og `fullfor`.
   - be Sjur låse perioden
10. **Balanselinjer, avgrenset (Sjur 25.09.2026: «litt over the top» å avstemme hele balansen):**
   - Bare linjene mva-flyten berører:
     - 19xx med bevegelse eller avstemming
     - 1500 og 2400 i siste måned
     - 2740
     - 27xx, som er 0 etter oppgjørsbilaget, i siste måned
   - Ingen balansespesifikasjon for de andre kontoene, og BALANCE fullføres ikke (`:complete` krever status på alle linjene).
   - Hele balansen tas bare når Sjur ber om det.

**Svar fra Sjur lagres ett sted, så de ikke kommer igjen:**
- Gjelder svaret klienten generelt, legg det i `klientprofil.md`.
- Gjelder det ett funn, legg nøkkelen (10 hex-tegn) og forklaringen i `kjente-avvik.md`.

## Årlig (ved årsoppgjøret og første gang en klient kjøres)
Legg til `--aarlig`. Da tas også disse kontrollene med:
- kontoplanens standardkoder
- motparter i reskontro med feil fortegn og gamle åpne poster, inkludert poster fra tidligere år
- bank hittil i år
- registreringsplikt og § 3-26 selv om de er avklart

## Ikke les i drift
`references/` er designdokumenter (arbeidsflyt, kontroller, endepunkter, fradragsregler, bilagsvurdering, kalibrering). Bruk dem bare til konkrete oppslag med grep, eller når flyten skal videreutvikles. Unntaket er `fradragsregler-kort.md`, som agenten på unntakslista leser. Praksis og presiseringer fra første fulle kjøring står i `arbeidsflyt.md` avsnitt 0a.

## Status (25.09.2026)
- **Bygget og brukt på en registrert klient (Flip Oppussing T4 2026):**
  - skriptet (UREGISTRERT UR0–UR7, reskontro, bank, EHF, dubletter, ubehandlede bilag, skattekonto) og unntakslista
  - `modul.js`: perioder, linjer, vedlegg og opplasting med erstatning, status på linjer, bank-PDF, utligning, mva-oversikt og fullføring
- **Bygget 25.09.2026:** `kontroll-utkast`, `notat-2740` og `reskontro-vurdering` i `modul.js` (`src/mva/notater.js`). Silfer-PDF lages med Edge headless.
- **Gjøres manuelt:** skjønnet i notatene (forklaring av saldo, vurdering og tiltak per motpart) og retting av refusjoner fra Skatteetaten.
- **Etter «Send»:** Skatteetatens tall kom ikke inn i mva-avstemmingen selv om kvitteringen var mottatt. Be Sjur synkronisere på nytt etter at kvitteringen er kommet.
- **Blokkert (403 for API-brukeren):** betaling, kvittering og XML for mva-meldingen, og innboksliste.
- **Finnes ikke i API-et:** periodelås og status «gjennomgått» på reskontrosiden.
