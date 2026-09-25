---
name: mva-avstemming
description: "Lett mva-avstemming per termin for én eller flere navngitte Tripletex-klienter. Ett skript kjører maskinelt reskontro, bank, mva-koder, EHF, dubletter, ubehandlede bilag og skattekonto. En agent brukes bare på en kort unntaksliste. Resultatet er en kort beslutningsliste. Kontrollene som hører til årsoppgjøret, kjøres med --aarlig. Klienter som ikke er mva-registrert har egen modus. Trigger: «avstem mva», «mva-avstemming», «avstem mva-terminen», «klar til å sende mva», «sjekk mva-behandlingen», «mva termin <n> for <klient>»."
---

# Mva-avstemming (lett termin-flyt)

**Budsjett:** normalt under 30 000 tokens per klient og termin. Skriptet gjør jobben og bruker ingen tokens. Claude leser bare JSON-sammendraget.

## Faste regler
- **Klient og termin:** Jobb bare mot klienter Sjur har navngitt. Er termin eller år uklart, spør.
- **Skriving:** Ingen skrivende kall uten ja i chat. Det gjelder korreksjoner, kommentarer, vedlegg, `:complete`, lukking av bankmåneder, betaling og profilfiler.
- **Det Claude aldri gjør:**
  - Sender inn mva-meldingen. Sjur gjør det med ID-porten, som varer 10 minutter og gjelder alle klienter.
  - Synkroniserer med Skatteetaten.
  - Godkjenner betalinger (`:approve`).
  - Kontrollerer egen avstemming (`:control`).
  - Sender e-post.
- **Betaling:** betyr at betalingen opprettes i Tripletex og legger seg til godkjenning hos kunden (`POST /bank/paymentWidget`). Den bekreftes med ett ja etter at tabellen er vist.
- **Feil i levert termin:** rettes i inneværende termin.
- **Dokumentasjon:** Så mye som mulig lagres som vedlegg og kommentarer i avstemmingsmodulen. Kvitteringene for alle årets mva-meldinger legges på 2740 i balanseavstemmingen.
- **Personvern:** Ingen personopplysninger i chat eller filer. Arbeidsdata ligger i `%LOCALAPPDATA%\silfer-mva\`. Fritekst siteres aldri.

## Per termin
1. **Kjør skriptet** fra `C:\Users\Sjur\Tripletex API`, én klient om gangen. Det tar ca. 30 s per klient.
   ```
   npm run -s mva -- "<klient>" --aar <år> --termin <n> --json
   ```
   Les bare JSON-svaret: `port`, `antall`, `punkter`, `tilVurdering`, `mappe`. Ikke les datasettene i mappa.
2. **Unntakslista** (`tilVurdering`):
   - **Er den tom:** hopp over dette steget. Det er det vanlige for klienter som ikke er registrert.
   - **Ellers:** gi én agent (Agent-verktøyet, ikke Workflow) bare `references/fradragsregler-kort.md` og bilagene i `<mappe>/overlevering.json` (maks 10). Agenten henter vedlegg lesende for de bilagene og skriver `<mappe>/vurdering.json`. Kjør så skriptet på nytt med `--gjenbruk`, som ikke gjør nye kall mot Tripletex.
3. **Vis Sjur resultatet:**
   - portfarge og én linje per punkt, med det som må rettes og spørsmålene først
   - lenke til `<mappe>\beslutning-1.md`
   - én nummerert liste over det som krever ja
4. **Etter ja:** skriving i fast rekkefølge (arbeidsflyt.md avsnitt 8). Skriveutføreren er ikke bygget, så hver skriving gjøres som et enkeltkall med GET før og etter.
5. **Registrerte klienter** i tillegg:
   - innsending: Sjur sender i ID-porten-vinduer på 10 minutter
   - synk og fullføring i modulen
   - betaling og dokumentasjon (arbeidsflyt.md 7–11 og 14a)

**Svar fra Sjur lagres ett sted, så de ikke kommer igjen:**
- Gjelder det klienten generelt (inntektsklassifisering, § 3-26, prosjektkontoer), legg det i `klientprofil.md`.
- Gjelder det ett funn, legg nøkkelen (10 hex-tegn) og forklaringen i `kjente-avvik.md`.

## Årlig (ved årsoppgjøret og første gang en klient kjøres)
Legg til `--aarlig`. Da tas også disse kontrollene med:
- kontoplanens standardkoder
- motparter i reskontro med feil fortegn og gamle åpne poster
- bank hittil i år
- registreringsplikt og § 3-26 selv om de er avklart

Per termin kommer bare det som er nytt eller fortsatt åpent.

## Ikke les i drift
`references/` er designdokumenter (arbeidsflyt, kontroller, endepunkter, fradragsregler, bilagsvurdering, kalibrering). Bruk dem bare til konkrete oppslag med grep, eller når flyten skal videreutvikles. Unntaket er `fradragsregler-kort.md`, som agenten på unntakslista leser.

## Status (24.09.2026)
- **Bygget:**
  - modus UREGISTRERT (UR0–UR7)
  - reskontro, bank (også manuell avstemming for kontoer uten integrasjon), EHF-kontroll, dubletter og purringer, ubehandlede bilag og skattekonto
  - unntaksliste, dokumentasjonsplan og kort beslutningsliste
  - testet på en klient uten mva-registrering, T4 2026
- **Ikke bygget:** terminkontrollene for registrerte klienter (utover EHF-kontrollen), skriveutfører, opplasting av dokumentasjon og arkiv.
- **Blokkert (403 for API-brukeren):** betaling, kvittering og XML for mva-meldingen, og innboksliste.
