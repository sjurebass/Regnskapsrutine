---
name: "mva-termin"
description: "Mva per termin: hvilke klienter som mangler mva-melding eller betaling (Tripletex, Fiken og PowerOffice via Altinn i Tally), kontroll før innsending (reskontro 1500/2400, bank, 27xx/2740, utkast mot hovedbok, unntaksliste for bilag) og etterarbeid etter at meldingen er sendt. Lukker Tally-oppgavene «MVA-kontroll» og «MVA-innlevering». Bruk ved «hvem mangler mva for t<n>», «avstem mva», «mva-avstemming», «mva termin <n> for <klient>», «klar til å sende mva», «nå har jeg opprettet utkast», «sendt og synkronisert»."
---

# Mva per termin

Skillen har tre deler:

- **Del A – oversikt over alle klientene:** hvem har levert og betalt for terminen, og hvem gjenstår. Bare lesing, helt i MCP.
- **Del B – kontroll før innsending for én klient:** lett kontroll med en kort beslutningsliste. Lesingen går i MCP; dokumentasjon og
  utligning i avstemmingsmodulen krever CLI eller Tripletex-UI.
- **Del C – etter innsending:** status, betaling, 2740 og fullføring.

Den lukker Tally-oppgavene «MVA-kontroll» og «MVA-innlevering». Alt skjer i chatten.

## Faste regler

- Klient og termin må være sagt. Er termin eller år uklart, spør. Hold deg til terminen: tidligere terminer røres ikke.
- **Lett per termin.** Ikke la agenter lese alle bilag med hele regelverket. En agent brukes bare på en unntaksliste på høyst 10 bilag.
  Tunge kontroller (kontoplan, § 3-26, registreringsplikt, gamle reskontroposter) hører til årsoppgjøret.
- Feil i en levert termin rettes i inneværende termin.
- Claude sender aldri mva-meldingen, oppretter den ikke («Opprett»), synkroniserer ikke med Skatteetaten, godkjenner ikke betalingen
  og låser ikke perioden. Regnskapsføreren gjør det med ID-porten (økten varer 10 minutter og gjelder alle klienter, så forbered alt først).
- Blir et skrivekall stoppet, si «ikke gjort» og hva som må til.
- Personvern: kundenavn er greit i reskontrodokumentasjon. Ingen andre personopplysninger. Fritekst siteres aldri.
- Svar som gjelder klienten varig (en leverandørs mva-behandling, «1960 tas i årsoppgjøret»), lagres i kundeinstruksen (`kundeinstruks`).
  Svar om ett funn lagres som kjent avvik der.

## Steg 0 – Sjekk tilkoblingene

Kall Tally `whoami` og Tripletex `search_client_companies` i samme runde. Rapporter på én linje.

## Del A – Hvem mangler mva for terminen

1. **Frister:** terminene er januar–februar (frist 10. april), mars–april (10. juni), mai–juni (31. august), juli–august (10. oktober),
   september–oktober (10. desember) og november–desember (10. februar). Faller fristen på en helg eller helligdag, flyttes den til neste virkedag.
   Tally `frister_fra_staten` og `list_deadlines` viser fristene byrået har registrert.
2. **Tripletex-klientene**, i ett `tripletex_run_script`-kall:
   - `get_vat_registration_status` per klient. Hold VAT_REGISTERED, VAT_APPLICANT, VAT_NOT_REGISTERED og VAT_COMPENSATION adskilt.
     Feil (ingen mva-innstillinger, mangler tilgang) er egen gruppe, aldri «ikke registrert».
   - Om terminen er levert og betalt: MCP-en har ikke et eget verktøy for mva-meldingens status. Bruk Altinn-innboksen (punkt 3), saldoen på
     2740 (`get_balance_sheet`) og bokført betaling, eller CLI-hurtigveien (`GET /vatReturns/status/list`).
3. **Alle klienter, også Fiken og PowerOffice:** Tally `list_altinn_innboks` per klient (avsender Skatteetaten), og se etter
   «Kvittering for mottatt mva-melding» for terminen. Les en melding med `les_altinn_melding` bare når det trengs.
4. **Spesielle tilfeller:**
   - Registrert midt i året: terminnummeret i Tripletex teller fra registreringsdatoen. Sjekk at du ser på riktig periode.
   - Tripletex kan si VAT_APPLICANT selv om Enhetsregisteret sier registrert (`lookup_company_in_brreg`). Si det.
   - Ikke registrert: sjekk kjøp av tjenester fra utlandet over 2 000 kr i terminen (omvendt avgiftsplikt, særskilt melding) og § 3-26 (uttak ved
     oppføring av bygg for salg).
   - Skattekontoen kan allerede ha et krav for terminen. Si det før noen sender, så meldingen ikke leveres to ganger.
5. **Svar:** tabell med klient · system · status (levert, ikke levert, til gode, ikke registrert, kunne ikke leses) · betaling · neste steg.
   Ved ny kjøring: si bare hva som er endret.

## Del B – Kontroll før innsending (én klient)

Les kundeinstruksen først (seksjonene «Mva», «Bank», «Kjente avvik»).

1. **Bank:** alle bankkontoer lukket for terminens to måneder, eller åpne poster forklart (se `bankavstemming`). Bilag fra mottaket som hører til
   terminen, må føres først (`bilagsforing`).
2. **Reskontro 1500/2400** per siste dag i terminen – en reell vurdering av hver åpen post datert i inneværende år, ikke bare sum mot hovedbok
   (`search_open_postings` med dato dagen etter terminslutt, `get_balance_sheet`). Eldre poster blir én linje «vurderes i årsoppgjøret».
   - Kunder: betalt etter periodeslutt · ikke forfalt · forfalt (purring, inkasso) · over 90 dager (tapsvurdering, konkurs i Brreg; konstatert tap
     gir rett til å kreve tilbake utgående mva, § 4-7, konkurs alene er ikke konstatert tap) · ufordelte innbetalinger og kreditnotaer · småbeløp ·
     poster som går i null.
   - Leverandører: forfalt uten betaling · betaling uten faktura (mangler kostnad og fradrag) · dobbeltbetaling · refusjoner ført som gjeld
     (forsikring, pensjon, Skatteetaten – innbetalinger fra Skatteetaten på 2400 flyttes til riktig konto, for eksempel 2600) · periodisering.
3. **Mva-kontoer:** 27xx og 2740 for terminen (`search_ledger_postings` 2700–2799). Rimelighet: utgående mva mot sats × grunnlag per kode.
   Oppgjørskontoen 2740 forklares per måned.
4. **Unntaksliste:** bilag som må vurderes faglig (mva-kode mot konto, representasjon, bil, gebyr, utland, fradrag uten vedlegg, store beløp,
   nye eller utenlandske leverandører). Høyst 10 bilag. Én agent får `references/fradragsregler-kort.md`, bilagene og leverandørindeksen
   (`leverandorindeks`) og svarer med vurdering per bilag. Ingen agent når lista er tom.
5. **Beslutningsliste:** portfarge (grønn, gul, rød), én linje per punkt med det som må rettes og spørsmål først, og en nummerert liste over det som krever ja.
6. **Rettinger** etter ja. Rett direkte på bilaget når det går. Bank- og OCR-bilag kan ikke endres via API-et (422); da lages et korrigeringsbilag
   som utlignes mot den opprinnelige posten. **Krever CLI (Sjur) eller Tripletex-UI:** rettinger av bilag.
7. **Utkastet** (etter at regnskapsføreren har trykket «Opprett»): linjene per kode mot hovedboken, fortegn mot forventet (kode 1 blir netto negativ
   når fakturaer fra tidligere terminer er reversert, og trenger merknad «kreditnota»), og oppgjørsbilaget, som nullstiller 27xx mot 2740 og er datert
   siste dag i terminen.

**Krever CLI (Sjur) eller Tripletex-UI:** dokumentasjon i avstemmingsmodulen. Omfanget er avgrenset til linjene mva-flyten berører:

- 19xx med bevegelse eller avstemming: Tripletex' bankavstemmings-PDF og kontoutskrift på begge månedene.
- 1500 og 2400 i siste måned: vurderingsnotatet med tiltaksliste.
- 2740 i begge måneder: notat med saldo per månedsslutt og forklaring. Etter «Opprett» er dokumentert saldo i siste måned −(beløp å betale).
- 27xx i siste måned (0 etter oppgjørsbilaget).

Sett dokumentert saldo og status «avstemt» først etter at dokumentasjonen er lastet opp. Notatene (2740, reskontrovurdering) og
kontoutskriftene lagres i tillegg i klientens dokumentarkiv i Tally: kategori `MVA_RAPPORT` (kontoutskrift: `BILAG`), periode `ÅÅÅÅ-T<n>`,
samling `Mva ÅÅÅÅ`, knyttet til oppgaven «MVA-kontroll» (`docs/dokumentlagring.md`). Ikke avstem hele balansen, og ikke fullfør
BALANCE, med mindre brukeren ber om det. Utligning av poster som går i null (én konto, én motpart, sum 0,00) gjøres med `modul utlign`.

## Del C – Etter innsending

Når regnskapsføreren har sendt og synkronisert:

1. Status går fra venter på svar til kvittering mottatt. Skatteetatens tall kan komme timer etter kvitteringen og krever ny synk.
2. Betalingsinformasjon: KID, beløp og forfall (flyttes når fristen er i helgen). Betalingen opprettes i Tripletex og legger seg til godkjenning hos
   kunden; Claude godkjenner aldri.
3. Oppdater 2740-notatet til «levert» og fullfør mva-avstemmingen når hovedbok, rapportert og Skatteetaten stemmer på hver linje.
   **Krever CLI (Sjur) eller Tripletex-UI.**
4. Lagre det endelige 2740-notatet og kvitteringen i Tally (kategori `MVA_RAPPORT`, samling `Mva ÅÅÅÅ`, oppgaven «MVA-innlevering»), se `docs/dokumentlagring.md`.
5. Be regnskapsføreren låse perioden. Det finnes ikke noe API-kall for det.

## Flere klienter

Del A kjøres for alle i ett skript. Del B kjøres per klient; flere klienter kan gå parallelt med én lesende agent hver, men stegene for én klient
er sekvensielle. Bare hovedagenten skriver.

## Hurtigvei – bare Sjur

Finnes `C:\Users\Sjur\Tripletex API`, gjør skriptet kontrollene i del B maskinelt og bruker ingen tokens. Les bare JSON-svaret
(`port`, `antall`, `punkter`, `tilVurdering`, `mappe`):

```powershell
npm --prefix "C:\Users\Sjur\Tripletex API" run -s mva -- "<klient>" --aar <år> --termin <n> --json [--gjenbruk] [--aarlig]
npm --prefix "C:\Users\Sjur\Tripletex API" run -s modul -- <kommando> --client "<klient>" ...
```

- `--gjenbruk` bruker lagrede data og fletter inn `vurdering.json` fra unntakslista. `--aarlig` tar med årsoppgjørskontrollene.
- `modul`: `perioder`, `linjer`, `bankpdf`, `last-opp [--erstatt]`, `sett-status`, `utlign`, `lukk`, `mva-oversikt`, `kontroll-utkast`, `notat-2740`,
  `reskontro-vurdering`, `fullfor`, `laas-opp`. Skriving krever `--bekreft` og ja i chat. Notatene er Silfer-PDF og lastes opp i modulen.
- Arbeidsdata ligger i `%LOCALAPPDATA%\silfer-mva\<år>-T<n>\<kunde-id>\` og slettes når terminen er ferdig. Notat-PDF-ene som `modul` lager, lagres i Tally før de slettes.
- Detaljer om kallene: `references/endepunkter.md` og `tripletex-api/docs/avstemmingsmodul.md`.

## Det du aldri gjør

- Sender, oppretter eller synkroniserer mva-meldingen.
- Godkjenner betalinger eller kontrollerer egen avstemming.
- Låser perioder.
- Sender e-post.
- Avstemmer hele balansen eller går tilbake til tidligere terminer uten at brukeren ber om det.

## Fullfør i Tally

1. «MVA-kontroll» fullføres når del B er ferdig og meldingen er klar til innsending. «MVA-innlevering» fullføres når kvitteringen er mottatt og
   betalingen er opprettet eller tilgodebeløpet registrert.
2. Foreslå tidsbruk og spør: «Skal jeg fullføre <oppgave> for <klient> og føre <X> minutter?»
3. Ved ja: `add_task_comment` (termin, beløp å betale eller til gode, forfall, hva som gjenstår), `log_time`, `complete_task`.

## Referanser

Les ikke `references/` i drift, bortsett fra `fradragsregler-kort.md` for agenten på unntakslista. Resten er designdokumenter
(se `README.md`) og brukes med grep ved konkrete oppslag.
