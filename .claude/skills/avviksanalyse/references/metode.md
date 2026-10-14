# Avviksanalyse – metode

Referanse for `avviksanalyse`. Tallene kommer fra `regnskapsrapport` (`npm run -s regnskap`); fortegn og grupper står i
`.claude/skills/regnskapsrapport/references/oppstilling.md`. Avvik = denne perioden − sammenligning, i presentasjonsfortegn.

## 1. Terskler – hva som skal forklares

| Sammenligning | Kronegrense | %-terskel | Utslag |
|---|---|---|---|
| Mot budsjett | V | 10 % | |
| Mot samme periode i fjor | V | 15 % | |
| Mot forrige periode (måned/termin) | V | 20 % | |

- **Skal forklares (N2):** \|avvik\| ≥ V, uansett prosent.
- **Følg med:** \|avvik %\| ≥ terskel og \|avvik\| ≥ V/2. Listes med én setning, uten full narrativ.
- Under V/2 forklares ikke enkeltvis; slike linjer samles i «Øvrige linjer» i broen.
- V fra kundeinstruksen; mangler den: høyeste av 5 000 kr og 0,5 % av omsetningen (årsomsetning, eller periodens × 12 / antall måneder).
- Kjent avvik i kundeinstruksen med samme beløp: KJENT, ingen ny forklaring. Nytt beløp: forklares på nytt.
- Mål: høyst 10 linjer som skal forklares per klient og periode. Blir det flere, er V for lav eller tallene ikke ferdig ajourført – si det.

## 2. Prioritering

Når flere avvik er over grensen, i denne rekkefølgen:
1. Størst avvik i kroner (størst effekt på resultatet).
2. Størst avvik i prosent (kan være feilføring eller manglende periodisering).
3. Uventet retning: motsatt av trenden, eller kostnad med kreditsaldo / inntekt med debetsaldo (N8).
4. Nytt avvik: linjen var på nivå forrige periode og er det ikke nå.
5. Voksende avvik: har økt tre perioder på rad (les forrige perioders rapport eller `regnskap` for tidligere perioder).

## 3. Dekomponering – driver per type

| Type | Typiske kontoer | Slik dekomponeres det | Typisk utsikt |
|---|---|---|---|
| **Lønnsdrevet** | 5000–5999 | Antall årsverk × snittkostnad per årsverk: (årsverk nå − før) × snitt før = antallseffekt; (snitt nå − snitt før) × årsverk nå = satseffekt. Feriepenger, AGA og pensjon følger grunnlaget. Bare aggregater – aldri lønn per person | vedvarende |
| **Volumdrevet** | 3000–3999, 4000–4999, 7770, frakt 6100 | Volum × pris: (volum nå − før) × pris før = volumeffekt; (pris nå − før) × volum nå = priseffekt. Volum = antall fakturaer, ordre eller enheter når det finnes; ellers inntekt som volummål for varekostnad (bruttomargin) | følger salget |
| **Skjønnsmessig** | 7100–7199 reise, 7300–7399 salg og representasjon, 6700–6799 fremmede tjenester, 6800–6899 kontor | Per leverandør og bilag (drill-down) | ofte engangs |
| **Kontraktsfast** | 6300 husleie, 7500 forsikring, 6420/6550/6800 lisenser og abonnement, 7400 kontingent | Forventet beløp per periode × antall perioder; avvik = prisendring, ny avtale eller manglende/doble føringer | vedvarende ved prisendring |
| **Engangs** | 6540 inventar, 7830 tap, 6700 rådgivning, 3800/7800 gevinst og tap ved salg | Navngi posten (bilag, leverandør) | engangs |
| **Periodisering / timing** | alle; typisk faktura for flere måneder på én måned, eller manglende faktura | Fakturaperiode mot bilagsdato. Beløp som hører til andre perioder er timing | snur neste periode |
| **Mva- og valutaeffekt** | kostnader med feil mva-kode (brutto bokført), 8060/8160 agio/disagio | Mva-del av beløpet (kode mot konto); valuta: beløp i valuta × kursendring | følger kurs / rettes |

- Hele avviket skal fordeles på drivere. Det som ikke kan forklares, er «diverse».
- **«Diverse» skal være under 20 % av avviket** (N4). Er det mer, dekomponer videre (drill-down) eller si at avviket ikke er forklart.
- Lønnsdata: bare antall og summer. Antall lønnsslipper per måned (som mål på antall ansatte):
  `npm run -s lonn -- datoer --client "<klient>" --fra ÅÅÅÅ-MM --til ÅÅÅÅ-MM --json` (`antall_slipper`); stillingsprosent fra «Lønn» i
  kundeinstruksen. Snitt = lønnskostnad / antall. Vis «ett årsverk mer», aldri navn, initialer eller lønn per ansatt.
- Mva-effekt: en kostnad bokført brutto (uten fradrag) gir 25 % for høy kostnad – pek på `bilagskontroll` (M4) for rettingen.
- Valuta: bare når klienten har valutakontoer eller utenlandske leverandører i perioden.

## 4. Drill-down: konto → leverandør → bilag

```
npm run -s api -- GET /ledger/posting dateFrom=<fra> dateTo=<til> accountNumberFrom=<konto> accountNumberTo=<konto> "fields=id,date,amount,description,voucher(number,year),supplier(id,name,organizationNumber,isPrivateIndividual)" --sider --ut <mappe>/poster-<konto>-<periode>.json --client "<klient>"
```

- Kjør for perioden og for sammenligningen (samme kontoer). `dateTo` er eksklusiv.
- Grupper per leverandør (org.nr., ellers id) med et lite skript: sum nå, sum før, endring. Leverandører uten poster i sammenligningen er «nye».
- Privatpersoner (`isPrivateIndividual`) og poster uten leverandør vises som «privatperson» eller «uten leverandør», aldri med navn.
- Bilagsnivå bare for de største endringene (topp 3 per konto): bilagsnummer, dato, beløp. Fritekst siteres ikke.
- Lønnskontoer (5000–5999) drilles aldri ned på ansatt; bruk antall og summer.
- Inntekter: `customer(id,name,organizationNumber,isPrivateIndividual)` i stedet for `supplier(…)`. Privatkunder vises som antall og sum.

## 5. Narrativ – én per avvik over V

```
<Linje>: <gunstig|ugunstig> avvik på <kr> (<%>) mot <sammenligning> for <periode>.
Driver: <hovedårsak med beløp>. <1–2 setninger med tallene som forklarer det, inkludert motgående poster>.
Utsikt: <engangs | vedvarende | snur neste periode | bedres | forverres>.
Tiltak: <ingen | følg med | undersøk (hva) | periodiser (konto, beløp) | rett føringen (bilag)>.
```

Eksempel: «Lønnskostnad: ugunstig avvik på 25 950 kr (22,5 %) mot september 2025. Driver: ett årsverk mer (+21 300) og høyere snittlønn (+4 650).
Utsikt: vedvarende. Tiltak: ingen.»

Kvalitet: konkret (navngir driveren), tallfestet (kr per driver), årsak (hvorfor, ikke bare hva), utsikt, tiltak, 2–4 setninger.

## 6. Anti-mønstre (skal ikke brukes)

- Sirkulær forklaring: «Inntekten er høyere fordi salget er høyere.»
- Vag: «Kostnadene var høye denne måneden.» – hvilke, hvor mye, hvorfor?
- «Timing» uten å si hva som er forskjøvet, fra hvilken periode og når det snur.
- «Engangs» uten å navngi posten (bilag, leverandør eller type).
- «Diverse små poster» for et avvik over V (dekomponer).
- Bare største driver, uten motgående poster.
- Forklaring hentet fra kundens tekst uten at tallene er sjekket i hovedboken.

## 7. Bro (waterfall)

Broen viser veien fra sammenligningen til denne perioden: **start + Σ drivere = slutt**.

| Driver | Type | Beløp | Kumulativt |
|---|---|---|---|
| Driftsresultat sep 2025 (start) | | | 91 520 |
| Salgsinntekt, høyere volum | volumdrevet | +43 500 | 135 020 |
| Varekostnad, volum og pris | volumdrevet | −26 200 | 108 820 |
| Lønn, ett årsverk mer | lønnsdrevet | −25 950 | 82 870 |
| Reisekostnad, kundebesøk | skjønnsmessig | −4 900 | 77 970 |
| Inventar kostnadsført i fjor | engangs | +3 500 | 81 470 |
| Øvrige linjer under V/2 | diverse | −1 670 | 79 800 |
| Driftsresultat sep 2026 (slutt) | | | 79 800 |

- Fortegn i broen er **effekt på resultatet**: høyere inntekt +, høyere kostnad −. Broen for én kostnadslinje bruker kostnadens fortegn
  (start = kostnaden i fjor, høyere kostnad +).
- 5–8 drivere; resten samles i «Øvrige linjer under V/2» (type diverse). Rekkefølge: størst positiv til størst negativ, eller resultatoppstillingens rekkefølge.
- **Kontroll (N3):** start + Σ drivere − slutt = 0 på øret. Start og slutt hentes fra `regnskap`, ikke regnes for hånd.
- **«Diverse» (N4):** \|diverse\| / \|slutt − start\| < 20 %.
- I Silfer-filen: eget ark «Bro» som `tabell` med `ib.verdi` = start, `ub.verdi` = slutt, `lopende` over beløpskolonnen og `kontrollsum`
  (se `.claude/skills/silfer-rapport/references/spec.md` og eksempelet `regnskapsrapport.json`). Går broen ikke opp, blir boksen oransje.

## 8. Videre til andre skills

| Funn | Til |
|---|---|
| Timing: kostnad eller inntekt som hører til andre perioder | `periodisering` (forskuddsbetalt 17xx, påløpt 29xx, opptjent/uopptjent inntekt) |
| Feilføring: feil konto, feil periode, dobbel føring | korrigeringsbilag via `periodisering` (`bilag manuell` med tørrkjøring) |
| Mva-kode mot konto, brutto kostnad | `bilagskontroll` (M4) |
| Manglende faste kostnader (0 nå, fast før) | `periodeavslutning` (A3) |
| Tap på fordringer, gamle åpne poster | `reskontroavstemming` (R4, R12) |
| Avskrivning mangler | `periodisering` (avskrivninger) og `balanseavstemming` (A4) |
