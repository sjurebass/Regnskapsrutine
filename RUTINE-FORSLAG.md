# Forslag: løpende kontrollrutine for Tripletex-klientene

Utkast 17.09.2026. Utgangspunkt: 25 klienter, én mappe per kunde, `logg.md` per kunde.
Eksisterende skills: `lonnsavstemming-a07`, `bankavstemming-aapne-poster`, `aarsoppgjoer-kontroll`.

---

## 1. Dagens situasjon – og flaskehalsen

Alt som er gjort så langt er **hendelsesstyrt**: du ber om en lønnsavstemming, jeg lager den.
Tre av 25 klienter har fått lønnsavstemming i 2026; resten har tomme årsmapper.

Flaskehalsen er ikke analysen – den er **datauthentingen**. I dag kommer tall inn ved at du
laster ned A07-XML fra Altinn, eksporterer fra Tripletex eller limer inn skjermbilder, eventuelt
at jeg leser av sider via Claude i Chrome. Det betyr at ingenting kan kjøre uten at du sitter der.

**Skillet som avgjør hvor mye som faktisk kan bli automatisk:**

| | Datakilde | Hva jeg kan gjøre alene |
|---|---|---|
| **Rute A** | Tripletex REST API (consumer token + employee token per klient) | Hente hovedbok, reskontro, bilag, saldobalanse, bankposter, ansatte selv – kjøre hele katalogen under på alle 25 klienter uten at du er til stede |
| **Rute B** | Claude i Chrome mot Tripletex-grensesnittet | Hente det samme, men tregere, skjørere ved UI-endringer, og det krever innlogget nettleser – altså at maskinen står på |
| **Rute C** | Du eksporterer, jeg analyserer | Det vi gjør i dag. Analysen er automatisk, uthentingen er ikke |

Anbefaling: **Rute A for alt tallmessig**, Rute B som reserve for det API-et ikke dekker
(f.eks. selve bankavstemmingsbildet), Rute C for Altinn-data (A07, mva-melding) som uansett
må hentes utenfra.

---

## 2. Kontrollkatalog – månedlig

Kjøres på alle klienter etter at måneden er ferdigført. Hver kontroll har en ID vi kan referere til.

### Bank og likvider

| ID | Kontroll | Hva den gjør | Utslag |
|---|---|---|---|
| B1 | Åpne bankposter | Uavstemte poster per bankkonto per måned (finnes allerede som skill) | Poster eldre enn 30 dager |
| B2 | Bank mot kontoutdrag | Bokført saldo 19xx mot faktisk saldo siste dag i måneden | Differanse ≠ 0 |
| B3 | Bankkonti uten tilkobling | Konti i kontoplanen uten automatisk bankavstemming | Finnes i det hele tatt |
| B4 | Negativ bank/kasse | Kasse i minus, bank i minus uten kredittramme | Saldo < 0 |
| B5 | Eldre åpne poster | Poster som har ligget åpne > 90 dager | Antall og beløp |

### Reskontro

| ID | Kontroll | Hva den gjør | Utslag |
|---|---|---|---|
| R1 | Kundereskontro mot hovedbok | Sum åpne kundeposter mot saldo 1500 | Differanse ≠ 0 |
| R2 | Leverandørreskontro mot hovedbok | Sum åpne leverandørposter mot saldo 2400 | Differanse ≠ 0 |
| R3 | Feil fortegn | Kunder i kredit, leverandører i debet | Beløp over terskel |
| R4 | Aldersfordeling kunder | Forfalt > 30/60/90 dager, kandidater til tapsavsetning | Forfalt > 90 dager |
| R5 | Forfalte leverandørfakturaer | Ubetalt etter forfall – varsel før purregebyr | Forfall passert |
| R6 | Dublettfakturaer | Samme leverandør + beløp + dato/fakturanr. bokført to ganger | Treff |

### Merverdiavgift

| ID | Kontroll | Hva den gjør | Utslag |
|---|---|---|---|
| M1 | Mva-konti mot mva-melding | 2700/2710/2740 mot innlevert melding for terminen | Differanse ≠ 0 |
| M2 | Oppgjørskonto nullstilt | Oppgjørskonto skal gå i null etter oppgjør og betaling | Restsaldo |
| M3 | Rimelighetskontroll sats | Bokført utgående mva mot 25 %/15 %/12 % av grunnlaget per sats | Avvik > 1 % |
| M4 | Mva-kode mot konto | Konti med uventet mva-kode (representasjon, bil, gebyr, utland) | Treff |
| M5 | Inngående mva uten bilag | Fradragsført mva på bilag uten vedlegg | Treff |
| M6 | Levert og betalt | Er terminen levert, og er betalingen bokført? | Mangler |

### Lønn

| ID | Kontroll | Hva den gjør | Utslag |
|---|---|---|---|
| L1 | A07 mot Tripletex | Full terminavstemming (finnes allerede som skill) | Som i dag |
| L2 | Skyldig trekk og AGA | 2600 og 2770 mot terminbeløp, forfall den 15. | Rest eller manglende betaling |
| L3 | Feriepengeavsetning | Avsetning mot 10,2 %/12 % av feriepengegrunnlaget hittil | Avvik > terskel |
| L4 | A-melding levert | Levert innen den 5. hver måned | Mangler |
| L5 | Lønn mot bank | Sum utbetalt lønn mot faktiske bankutbetalinger | Differanse |

### Bilag og bokføringskvalitet

| ID | Kontroll | Hva den gjør | Utslag |
|---|---|---|---|
| D1 | Bilag uten vedlegg | Bokførte bilag som mangler dokumentasjon | Antall og beløp |
| D2 | Observasjonskonti | Saldo på oppsamlings-/observasjonskonti | Saldo ≠ 0 |
| D3 | Feil periode | Bilagsdato og periode spriker, eller bokføring i gammel periode | Treff |
| D4 | Periodelåsing | Er forrige måned låst etter avslutning? | Ulåst |
| D5 | Runde beløp og manuelle poster | Manuelle bilag med runde beløp over terskel – typisk skjønnsposter | Treff |
| D6 | Ubehandlet fakturamottak | Fakturaer som ligger i innboksen uten å være bokført | Antall og alder |

### Eier og nærstående

| ID | Kontroll | Hva den gjør | Utslag |
|---|---|---|---|
| E1 | Mellomregning aksjonær | Utvikling på mellomregningskonto – lån til aksjonær utløser utbyttebeskatning | Debetsaldo mot aksjonær |
| E2 | Privatuttak i drift | Kostnadsposter som ser private ut (typiske leverandører/tekster) | Treff til vurdering |

### Drift og rimelighet

| ID | Kontroll | Hva den gjør | Utslag |
|---|---|---|---|
| A1 | Måned mot måned | Resultatkonti med avvik > 30 % eller > terskelbeløp | Avvik |
| A2 | Mot samme måned i fjor | Samme, mot fjorår | Avvik |
| A3 | Manglende faste kostnader | Husleie, forsikring, abonnement som pleier å komme hver måned og mangler | Mangler |
| A4 | Avskrivninger | Er månedens avskrivninger bokført? Nye anleggsmidler kostnadsført i stedet for aktivert? | Mangler eller treff |
| A5 | Nullsaldo-konti | Balansekonti uten bevegelse på 12 måneder – kandidater for opprydding | Treff |

### Bransjeavhengig (kjøres der det er relevant)

| ID | Kontroll | Hva den gjør |
|---|---|---|
| P1 | Ufakturerte timer | Registrerte timer som ikke er fakturert |
| P2 | Prosjektmargin | Prosjekter med negativ eller fallende dekningsbidrag |
| P3 | Varelager | Bokført lager mot siste telling, ukurans |
| P4 | Leieinntekter | Avtalt leie mot fakturert leie (eiendomsklientene) |

---

## 3. Terminvise og årlige oppgaver

| Frist | Oppgave | Automatiserbar |
|---|---|---|
| Den 5. hver måned | A-melding levert – kontroll, ikke innsending | Kontroll: ja |
| Den 15. i partallsmåned | Skattetrekk og AGA forfaller – L2 kjøres før forfall | Ja |
| 10. apr / 10. jun / 31. aug / 10. okt / 10. des / 10. feb | Mva-termin – M1–M6 kjøres *før* innsending, ikke etter | Kontroll: ja |
| Kvartalsvis | Resultatrapport til kunde med kommentar og avviksliste | Ja, utkast |
| 31. januar | Aksjonærregisteroppgaven – kontroll mot aksjeeierbok og E1 | Delvis |
| 15. feb og 15. apr | Forskuddsskatt – rimelighet mot fjorårets resultat | Ja |
| 31. mai | Skattemelding – `aarsoppgjoer-kontroll` | Finnes |
| 31. juli | Årsregnskap til Regnskapsregisteret | Finnes |

---

## 4. Foreslått rutine

### Månedshjulet

**Arbeidsdag 5–8 i måneden** – lukkekontroll for forrige måned, alle klienter i batch:

1. Jeg kjører hele månedskatalogen (B, R, M, D, E, A) på alle 25 klienter.
2. Hver klient får en `Kontroll YYYY-MM <Klientnavn>.xlsx` i årsmappa, med Silfer-header
   og ett ark per kontrollområde – samme mal som lønnsavstemmingen.
3. Alle funn samles i én **statusrapport** på toppnivå: én linje per klient med
   grønn/gul/rød, antall avvik og de tre mest alvorlige punktene.
4. Du går gjennom statusrapporten, ikke 25 filer. Bare gul og rød krever noe av deg.
5. `logg.md` per kunde oppdateres automatisk, som i dag.

**Arbeidsdag 9–12** – oppfølging:

6. For klienter med manglende dokumentasjon lager jeg **utkast til kundemail** med
   konkret liste (bygger på den eksisterende bankavstemmingsrapporten). Du sender.
7. Avvik som krever faglig vurdering (E1, E2, R4, P2) legges i en egen «til vurdering»-liste.

**Før hver mva- og skattetrekkstermin** – M1–M6 og L1–L2 på klientene det gjelder.

### Terskler og støy

En kontrollrutine som gir 400 treff i måneden blir ignorert. Derfor:

- Vesentlighetsgrense per klient, f.eks. høyeste av 5 000 kr og 0,5 % av omsetning.
- **Kjente avvik kvitteres ut én gang.** Et pensjonsavvik som allerede er forklart, eller de samme tre faste
  avvikene måned etter måned, skal ikke meldes som nytt hver gang – de legges i en
  `kjente-avvik.md` per klient med forklaring og utløpsdato, og rapporteres som
  «kjent, uendret» så lenge beløpet er det samme.
- Målet er **under 10 linjer per klient per måned**.

---

## 5. Mappestruktur

```
avstemminger/
  status/
    2026-09 Statusrapport alle klienter.xlsx     <- den ene filen du faktisk åpner
    historikk.md
  <Klient> (id)/
    logg.md
    kjente-avvik.md                              <- nytt: kvitterte avvik
    klientprofil.md                              <- nytt: mva-plikt, lønn j/n, bransje,
                                                    vesentlighetsgrense, hvilke kontroller
                                                    som er aktive, særegenheter
    2026/
      Kontroll 2026-08 <Klient>.xlsx/.pdf
      A07/
      Dokumentasjon/
```

`klientprofil.md` er det som gjør batch-kjøring mulig – uten den vet jeg ikke om en klient
har lønn, varelager eller prosjekt, og kontrollene blir enten for mange eller for få.

---

## 6. Status – hva som er bygget

Bygget 17.09.2026. Se [SETUP.md](SETUP.md) for oppsett.

**Ferdig**

- API-klient mot Tripletex v2 (`tools/tripletex.py`) – session token, klientbytte via
  companyId, paging, retry på 429/5xx og fornying av utløpt token midt i en kjøring.
- Datalag med cache per klient og periode (`tools/hent.py`), slik at 39 kontroller deler
  de samme uttrekkene i stedet for å hente hver for seg.
- **Alle 39 kontrollene i katalogen over**, i `tools/kontroller/`.
- Rapportene: Excel per klient med Silfer-profil (Sammendrag, Funn, Saldobalanse) og
  én samlet statusrapport. Eksempler ligger i `mal/`.
- Vesentlighetsgrense og `kjente-avvik.md` med nøkkel per avvik – et kvittert avvik
  dukker opp igjen først når beløpet endrer seg.
- `klientprofil.md` per kunde, som styrer hvilke kontroller som gjelder.
- Automatisk linje i `logg.md` per kunde og i `status/historikk.md`.
- Selvtest (`selvtest.py`) som kjører hele katalogen mot testdata med kjent fasit.

**Omfang**

Kunderegisteret har 24 kunder: 14 i Tripletex, 7 i Fiken, 3 i PowerOffice.
Rutinen dekker de 10 Tripletex-klientene som er merket `aktiv` i `klienter.json`.
Fiken- og PowerOffice-kundene faller utenfor – begge har API-er, så det er mulig å
utvide senere, men datamodellene er ulike nok til at det er en egen jobb.

**Gjenstår**

1. Tokens fra Tripletex, og en verifisering med `sjekk-tilgang.py` mot en ekte klient.
   Kontrollene er bygget mot API-spesifikasjonen, men ingen av dem har møtt ekte data
   ennå – regn med justering av terskler og kontonumre den første måneden.
2. Bekrefte `klientprofil.md` for hver klient som skal være med.
3. Utkast til kundemail for manglende dokumentasjon.
4. Kvartalsrapport til kunde.
5. Fast kjøring rundt arbeidsdag 5 hver måned.

---

## 7. Det jeg ikke bør gjøre automatisk

For ordens skyld, grensen bør ligge her:

- **Ingen bokføring.** Jeg foreslår posteringer, du bokfører.
- **Ingen innsending** av mva-melding, a-melding eller skattemelding.
- **Ingen utsendelse** av e-post til kunder uten at du har lest utkastet.
- **Ingen betalinger.**
- Konklusjoner som krever faglig skjønn (tapsavsetning, ulovlig lån, grensetilfeller på
  fradragsrett) flagges med forslag, men avgjøres av deg.
