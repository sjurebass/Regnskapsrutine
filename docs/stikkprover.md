# Stikkprøver – utvalg, arbeidspapir og avvik

Referanse, ikke en skill. Metoden byrået bruker når en kontroll ikke kan lese hele populasjonen: `bilagskontroll` (bilag i måneden) og
`kvalitetskontroll` (oppdragskontrollen per klient). `revisjonsstotte` bruker bevisstandarden og oppfølgingen her (revisor trekker sitt eget utvalg).
Kontrollene har ID-ene U1–U14 (tabellen nederst).

Grunnlaget er byråets internkontroll og kvalitetskontroll etter regnskapsførerregelverket og god regnskapsføringsskikk (GRFS: dokumentasjon av
utført arbeid, kvalitetskontroll og oppfølging av avvik), som Finanstilsynet og Regnskap Norges kvalitetskontroll etterprøver. En stikkprøve
skal kunne gjentas av en annen: samme populasjon, metode og seed gir samme utvalg.

## Hele populasjonen eller stikkprøve

- Maskinelle kontroller kjøres på alle posteringer (D1–D7, M4–M8, R6). Det er ikke stikkprøve.
- Stikkprøve brukes der noen må lese dokumentet, se etter godkjenning eller regne på nytt, og populasjonen er for stor til å ta alt.
- Under 20 enheter, eller en årlig kontroll: test alle.

## Utvalgsmetoder

| Metode | Når | Slik | `--metode` |
|---|---|---|---|
| Tilfeldig | Standard for bilag og transaksjoner | Alle enheter har lik sjanse. Seedet tallgenerator, seed skrives i arbeidspapiret. | `tilfeldig` |
| Systematisk | Jevn dekning over perioden: bilag over et helt år, månedlige og terminvise kontroller | Intervall = populasjon / antall, start trukket med seed, hver n-te enhet. Har populasjonen et mønster (samme leverandør hver måned), bruk tilfeldig. | `systematisk` |
| Målrettet | Risiko: i tillegg til tilfeldig, eller alene når populasjonen er liten eller uensartet | Enheter som treffer kriteriene under, rangert på antall kriterier og så beløp, med begrunnelse per enhet. Uten seed (fast rangering). Ikke representativt: feil projiseres ikke, de telles fullt. | `maalrettet` |
| Skjønnsmessig «på måfå» | **Frarådes** | Kan ikke gjentas eller etterprøves, og man velger ubevisst øverst på lista eller runde beløp. Mangler populasjonslista, bruk systematisk på det som finnes og skriv hvorfor. | – |

Standard for bilag er målrettet + tilfeldig: to uttrekk. Et bilag som kommer i begge, testes én gang med begge grunnene;
det tilfeldige utvalget trekkes ikke på nytt (overlappet står i arbeidspapiret).

## Utvalgsstørrelse

**Risiko** for kontrollen er risikoklassen fra kundetiltakene (Tally `client_compliance`: lav, middels, høy), løftet ett trinn per forhøyende
faktor (to eller flere gir høy):
- avvik i samme kontroll siste 12 måneder (også revisors merknader),
- ny klient (første 12 måneder) eller ny regnskapsfører på oppdraget,
- ny prosess eller nytt system (ny bank, nytt lønnssystem, ny betalingsløsning),
- ingen annen kontroll fanger samme feil, eller revisor bygger på byråets kontroll.

| Frekvens | Populasjon i testperioden | Lav | Middels | Høy |
|---|---|---|---|---|
| Årlig | 1 | 1 | 1 | 1 |
| Kvartalsvis | 4 | 2 | 2 | 3 |
| Per termin (mva, trekk og AGA) | 6 | 2 | 2 | 3 |
| Månedlig | 12 | 2 | 3 | 4 |
| Ukentlig | 52 | 5 | 8 | 15 |
| Per bilag, få | under 20 | alle | alle | alle |
| Per bilag | 20–249 | 20 | 30 | 40 |
| Per bilag, mange | 250 eller flere | 25 | 40 | 60 |

Testperioden er perioden konklusjonen gjelder (kvalitetskontroll: siden forrige gjennomgang; revisjonsstøtte: regnskapsåret).
En kontroll som kjøres hver måned (`bilagskontroll`), fordeler årsutvalget på månedene, rundet opp og minst 2:

| Bilag per år | Lav | Middels | Høy |
|---|---|---|---|
| under 250 | 2 | 3 | 4 |
| 250 eller flere | 3 | 4 | 5 |

I tillegg kommer de målrettede, høyst 10 (i `bilagskontroll` per måned, sammen med unntakslista); resten telles som «utelatt n» og er ikke testet.
Et utvalg mindre enn tabellen er et funn (U1). Ved avvik i utvalget: se «Aggregering» før konklusjon.

## Målrettede kriterier

| Kriterium | Hvorfor | I `utvalg` |
|---|---|---|
| Over beløp | Vesentlighet | `--over <beløp>`; standard 5 000 kr, sett klientens V |
| Uten vedlegg | Dokumentasjonskravet (bokf.l. § 10) | ja (ikke for systembilag som betaling og lønn) |
| Runde beløp (hele tusen, fra 1 000 kr) | Anslag, mulig fiktivt bilag | ja |
| Siste 3 dager i perioden | Periodeavgrensning (cut-off) | ja; første dager i neste periode: eget uttrekk når den er bokført |
| Helg | Uvanlig tidspunkt for manuell føring | ja |
| Manuelle bilag | Overstyring utenom flyten (bank, faktura, lønn) | ja (bilag uten bilagstype) |
| Nye leverandører | Første bruk på 12 måneder (D7) | ja |
| Nærstående | Aksjonær, styremedlem, daglig leder eller selskap de kontrollerer (asl. § 3-8; sktl. § 13-1) | nei – manuelt fra Brreg-roller (Tally `lookup_brreg`), aksjonærregisteret og kundeinstruksen; personer omtales med rolle |

## Kommandoen

```
npm run -s utvalg -- --client "<klient>" --fra ÅÅÅÅ-MM-DD --til ÅÅÅÅ-MM-DD [--antall N] [--metode tilfeldig|systematisk|maalrettet]
                     [--seed <tall>] [--konto 4000-7999] [--over <beløp>] [--risiko lav|middels|hoy] [--ut <mappe>] [--json]
```

- Populasjon: bokførte bilag med dato fra og med `--fra` til og med `--til`, valgfritt avgrenset til et kontointervall. Per bilag: id, nummer-år,
  dato, beløp (sum debet), vedlegg ja/nei, bilagstype, manuelt eller automatisk, og maskert tekst. `--over` avgrenser populasjonen i tilfeldig
  og systematisk utvalg; i målrettet er det kriteriet «stort beløp».
- `<mappe>/utvalg.json`: populasjon (antall, sum), metode, seed og utvalget med begrunnelse per bilag. Bare sammendraget vises i chatten;
  `tekst` siteres aldri.
- **Seed:** velg et nytt tall per kontroll, for eksempel testdatoen `ÅÅÅÅMMDD`, og skriv det i arbeidspapiret (uten `--seed` lager kommandoen
  et og skriver det ut). Blir bilag ført i perioden etter uttrekket, endres populasjonen og utvalget; arbeidspapiret har derfor populasjonens
  antall og sum fra uttrekket.
- Uten `--antall` brukes tabellen for bilag med `--risiko` (standard lav: 20 eller 25), aldri mer enn populasjonen. Månedlige uttrekk og
  målrettede uttrekk får alltid `--antall`.
- **Bilagstester (U2–U6) avgrenses til inntekt og kostnad uten lønn:** `--konto 3000-4999,5900-7999`. Uten avgrensning domineres utvalget av
  betalinger og remitteringer, der vedlegg ikke er forventet. Lønn testes i `lonnsavstemming` (L1), ikke med stikkprøve av lønnsbilag.

Eksempler (månedlig bilagskontroll, middels risiko, under 250 bilag i året; og kvalitetskontroll over et år):

```
npm run -s utvalg -- --client "<klient>" --fra 2026-09-01 --til 2026-09-30 --konto 3000-4999,5900-7999 --metode maalrettet --over 25000 --antall 10 --ut <mappe>/maalrettet
npm run -s utvalg -- --client "<klient>" --fra 2026-09-01 --til 2026-09-30 --konto 3000-4999,5900-7999 --metode tilfeldig --antall 3 --seed 20261015 --ut <mappe>/tilfeldig
npm run -s utvalg -- --client "<klient>" --fra 2025-10-01 --til 2026-09-30 --konto 3000-4999,5900-7999 --metode systematisk --antall 30 --seed 20261020 --ut <mappe>/aar
```

## Arbeidspapir

Ett arbeidspapir per kontroll og klient. Det er byråinternt: arket «Stikkprøve» i skillens Silfer-fil, eller avsnittet i oppdragskontrollen.
Initialer, aldri navn. Claude fyller ut alt unntatt «Gjennomgått av», som en annen enn utføreren signerer.

```
STIKKPRØVE – ARBEIDSPAPIR
Kontroll-ID:          U2, U3, U4 (kilde: bilagskontroll)
Klient · periode:     Eksempel AS · 2026-09
Formål:               Avgjøre om bilagene i perioden er dokumentert, riktig ført og i riktig periode.
Populasjon:           bilag 2026-09-01–2026-09-30, konto 3000–4999 og 5900–7999: 184 bilag, 1 234 567,00 kr (utvalg.json, uttrukket 2026-10-15)
Metode og seed:       målrettet over V (25 000): 4 bilag · tilfeldig: 3 bilag (middels, under 250/år) · seed 20261015 · overlapp 0
Testtrinn:            T1 vedlegg er gyldig bilag · T2 konto, mva-kode og beløp = dokumentet · T3 riktig periode · T4 godkjent · T5 matchet mot bank/reskontro
Forventet dokumentasjon: vedlegg eller EHF i Tripletex, godkjenning med dato, bankmatch eller åpen post
```

| # | Bilag | Dato | Beløp | Grunn | T1 | T2 | T3 | T4 | T5 | Resultat | Bevis |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 412-2026 | 2026-09-28 | 31 250,00 | over V, siste 3 dager | ✓ | ✓ | ✗ | ✓ | ✓ | Avvik | vedlegg, faktura datert 2026-10-02 |
| 2 | 377-2026 | 2026-09-12 | 1 890,00 | tilfeldig | ✓ | ✓ | ✓ | ✓ | ✓ | Bestått | vedlegg, bankmatch |

| # | Avvik | Feil (kr) | Årsak | Grad | Tiltak | Eier (rolle) | Frist |
|---|---|---|---|---|---|---|---|
| 1 | Kostnad for oktober ført i september | 31 250,00 | rutine ikke fulgt | Vesentlig avvik | korrigeringsbilag; periodekontroll ved føring | regnskapsfører | 2026-10-20 |

```
Aggregering:          kjent feil 31 250 · projisert feil 0 · samlet 31 250 mot V 25 000
Konklusjon:           Vesentlig avvik – meldt oppdragsansvarlig 2026-10-15
Utført av:            AB · 2026-10-15          Gjennomgått av: ____ · ________
```

Resultat per utvalgsenhet er Bestått eller Avvik. Et testtrinn som ikke gjelder (for eksempel godkjenning når kunden ikke har godkjenningsflyt
i instruksen), merkes «–» og forklares én gang.

## Bevisstandard

Tilstrekkelig (minst én per testtrinn):
- Bilag med vedlegg som oppfyller bokf.f. kap. 5: salgsdokument (§ 5-1-1) eller kjøpsdokument med selger, kjøper, dato, ytelse, beløp og mva; EHF som er lest.
- Godkjenning med godkjenner og dato: attesteringsflyten i Tripletex (`/supplierInvoice/{id}` med `approvalListElements(status,actionDate)`),
  e-post fra kunden med avsender og dato, signert dokument.
- Systemlogg med tidspunkt: endringslogg på bilaget (`/ledger/voucher/{id}` med `changes(timestamp,changeType)`), status i avstemmingsmodulen,
  Tally-oppgave fullført med dato og dokument, Altinn-kvittering i Tally.
- Gjenberegning: Claude regner på nytt (mva = grunnlag × sats, periodisering, avskrivning, saldo i dokumentet = hovedbok på datoen) og får samme svar ± 1 kr.
- Ekstern bekreftelse: kontoutskrift eller årsoppgave fra bank og långiver, saldobekreftelse fra motpart.

Ikke tilstrekkelig:
- Muntlig bekreftelse alene («daglig leder sier at …»), uten dokument som støtter den.
- Udatert dokument, eller dokument uten identifiserbar utsteder eller godkjenner.
- Rapport eller skjermbilde uten dato og utvalgskriterier.
- Tally-oppgave fullført uten dokument (K6).
- Proforma, ordrebekreftelse, tilbud, purring eller betalingsoppfordring i stedet for faktura.
- Dokumentasjon laget etter at testen startet, uten at mottaksdatoen står i arbeidspapiret.

## Avviksklassifisering

| Grad | Når | Status i funn-formatet | Port | Alvor i Tally (`list_avvik`) | Videre |
|---|---|---|---|---|---|
| Merknad | Ingen feil i regnskapet: formfeil i bilaget, godkjenning etter bokføring, oppgave fullført sent uten følger | `OK` (Forslag: «merknad: …», samles i én linje) | grønn | lav | regnskapsfører, ved neste kjøring |
| Avvik | Feil i regnskapet under V, eller enkeltstående svikt i en kontroll (én måned uten dokumentert avstemming, ett bilag uten vedlegg) | `AVVIK` | gul | middels | regnskapsfører retter |
| Vesentlig avvik | Feil over V (enkeltvis eller samlet), gjentatte avvik, eller svikt i en nøkkelkontroll | `AVVIK` (Krever `regnskapsfører`, Forslag: «meldes oppdragsansvarlig») | rød | høy | oppdragsansvarlig |

- **Gjentatte avvik:** samme kontroll-ID har avvik i to kjøringer på rad (måneder eller gjennomganger), eller tre eller flere avvik av samme type i ett utvalg.
- **Nøkkelkontroller:** bank (B1–B3), reskontro mot hovedbok (R1, R2), mva mot melding (M1), A07 mot regnskap (L1), dokumentert balanse (S1),
  kundetiltak (K2) og rapportering i tide (K5). Svikt = ikke utført eller ikke dokumentert for en periode med pliktig rapportering.
- Fra alvor i `bilagskontroll`: BLOKK med beløp eller mva-effekt ≥ V → vesentlig avvik; annen BLOKK og FORKLAR → avvik; INFO og formmerknad → merknad.
  STOPP og SPØR står som `IKKE AVKLART` til de er avklart, og klassifiseres da.
- Kjente avvik med samme nøkkel og beløp (`KJENT`) klassifiseres ikke på nytt.

**Stopp:** vesentlig avvik er meldt oppdragsansvarlig (Tally) – til da attesteres, lukkes eller fullføres ingenting som avviket gjelder; Claude lager meldingen og venter.

## Aggregering

1. Samle avvikene per kontroll-ID og per område (samme konto, samme type feil: dokumentasjon, periode, mva).
2. **Kjent feil:** summen av feilbeløpene (absolutt) i hele utvalget.
3. **Projisert feil** (bare tilfeldig og systematisk utvalg): feil i det tilfeldige utvalget / sum beløp i det tilfeldige utvalget × populasjonens sum.
   Målrettede enheter telles med faktisk feil, aldri projisert.
4. **Samlet** = kjent feil i målrettet utvalg + projisert feil. Samlet ≥ V → vesentlig avvik, også når hvert avvik er under V.
   Samlet mellom V/2 og V → utvid utvalget ett trinn (eller test hele området) før konklusjonen.
5. Avvik uten beløp (manglende godkjenning, manglende dokument) telles: to eller flere i samme utvalg → kontrollen virker ikke (avvik; nøkkelkontroll → vesentlig).
6. Skriv tallene i arbeidspapiret og om en annen kontroll ville fanget feilen (for eksempel bankavstemmingen). Den kan redusere graden ett trinn, aldri til OK.

## Oppfølging

Hvert avvik og vesentlig avvik får:

| Felt | Innhold |
|---|---|
| Rotårsak | Én av: rutine mangler · rutine ikke fulgt · kompetanse · kapasitet eller frist · system eller integrasjon · kunden leverte ikke |
| Tiltak | Konkret: retting (bilag, avstemming), endret rutine, opplæring, ny kontroll, kundeinstruksen oppdatert, beskjed til kunden |
| Eier | Rolle: regnskapsfører, oppdragsansvarlig eller kunden. I Tally er eieren en bruker; i repoet og i filer står rollen |
| Frist | Dato. Vesentlig avvik: før neste pliktige rapportering, høyst 30 dager |
| Ny test | Samme kontroll-ID, nytt utvalg med ny seed, ett trinn større (tidligere avvik), etter fristen. Avviket lukkes først når ny test er bestått (U9) |

Tiltak blir Tally-oppgaver (`create_task`) etter ja. Endringer for klienten går i kundeinstruksen (`kundeinstruks`), «Kjente avvik» bare når avviket
er forklart og varig.

## Kontroller (U-serien)

| ID | Kontroll | Utslag | Skill | Data (API) | Grunnlag |
|---|---|---|---|---|---|
| U1 | Utvalget er dokumentert og kan gjentas: populasjon (antall, sum), metode, seed og antall etter tabellen | Mangler seed, skjønnsmessig utvalg eller færre enn tabellen | `bilagskontroll`, `kvalitetskontroll` | `utvalg` (`utvalg.json`) | GRFS: dokumentasjon av utført arbeid |
| U2 | Bilaget har vedlegg som er gyldig salgs- eller kjøpsdokument | Mangler eller ugyldig → avvik; formfeil → merknad | `bilagskontroll`, `kvalitetskontroll` | `utvalg`, `dokument --bilag` | bokf.l. § 10; bokf.f. kap. 5 |
| U3 | Konto, mva-kode og beløp stemmer med dokumentet (gjenberegning) | Avvik ≥ 1 kr; ≥ V → vesentlig | `bilagskontroll`, `kvalitetskontroll` | `dokument`, `/ledger/voucher/{id}` (postings) | bokf.l. § 4; mval. § 15-10 |
| U4 | Riktig periode: leverings- eller fakturadato og bilagsdato i samme periode, særlig siste og første dager | Annen periode → avvik; annen mva-termin og ≥ V → vesentlig | `bilagskontroll`, `kvalitetskontroll` | `utvalg --metode maalrettet`, `/ledger/posting` | bokf.l. § 7; rskl. § 4-1 |
| U5 | Godkjenning: leverandørfaktura godkjent med dato etter kundeinstruksen | Mangler → avvik; ingen godkjenningsflyt i instruksen → «–» | `bilagskontroll`, `kvalitetskontroll` | `/supplierInvoice/{id}` (`approvalListElements(status,actionDate)`) | GRFS: oppdragsavtale og rutiner |
| U6 | Oppgjør: bilaget er matchet mot bank eller står som åpen post i reskontro | Verken bank eller åpen post | `bilagskontroll`, `kvalitetskontroll` | `/ledger/posting`, `/ledger/posting/openPost` | bokf.l. § 11 |
| U7 | Månedlige og terminvise kontroller er utført i tide og dokumentert i utvalgte perioder, og saldo i dokumentet = hovedbok | Ikke utført, udokumentert eller saldo ≠ hovedbok; nøkkelkontroll → vesentlig | `kvalitetskontroll` | Tally `list_tasks`, `list_documents`; `modul -- perioder`, `/balanceSheet` | GRFS: dokumentert avstemming; bokf.l. § 11 |
| U8 | Avvik er klassifisert og aggregert, og vesentlige avvik er meldt oppdragsansvarlig før noe attesteres eller lukkes | Ikke meldt, eller samlet feil ≥ V uten vesentlig avvik | `bilagskontroll`, `kvalitetskontroll` | arbeidspapiret, Tally `get_quality_workspace` | GRFS: kvalitetskontroll |
| U9 | Ny test etter tiltak: kontroll med tidligere avvik er testet på nytt (ny seed, ett trinn større) og bestått | Ikke testet etter frist, eller avvik igjen → vesentlig | `kvalitetskontroll` | Tally `list_avvik`, `list_tasks`, forrige arbeidspapir | GRFS: oppfølging av avvik |
| U10 | Nærstående: transaksjoner med nærstående er funnet, dokumentert (avtale, vedtak) og ført riktig | Uten dokumentasjon → avvik; lån til aksjonær uten vedtak → vesentlig | `kvalitetskontroll`, `bilagskontroll` | Tally `lookup_brreg`, `/ledger/posting` | asl. §§ 3-8, 8-7; sktl. § 13-1 |
| U11 | Revisors forespørsel er en PBC-liste: hvert punkt har område, periode, eier, frist og status | Punkt uten eier eller forfalt | `revisjonsstotte` | Missive, Tally `get_arsoppgjor_status` | GRFS: oppdragsdokumentasjon |
| U12 | Saldo i dokumentasjonen til revisor = hovedbok på samme dato, per konto | Differanse ≥ 1 kr → sendes ikke | `revisjonsstotte` | `/balanceSheet`, `modul -- linjer`, Tally `list_documents` | bokf.l. § 11 |
| U13 | Oversendelsen er dokumentert (hva, når, kanal) og inneholder ikke mer persondata enn revisor trenger | Mangler logg, eller persondata utenfor forespørselen | `revisjonsstotte` | Tally `update_arsoppgjor` (`oversendelse-revisor`), `list_documents` | GRFS: dokumentasjon; GDPR art. 5 (dataminimering) |
| U14 | Revisors merknader (nummerert brev, korrigeringer) har rotårsak, tiltak, eier og frist | Merknad uten tiltak eller eier | `revisjonsstotte`, `kvalitetskontroll` | Tally `list_tasks`, `list_documents` | GRFS: oppfølging av avvik |
