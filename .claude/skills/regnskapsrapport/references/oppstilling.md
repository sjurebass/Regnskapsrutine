# Oppstilling – resultat og balanse for små foretak

Referanse for `regnskapsrapport` (og `scripts/lag_spec.py`). Oppstillingen følger regnskapsloven §§ 6-1 og 6-2 med forenklingene for små
foretak (rskl. § 1-6), artsinndelt, med NS 4102-kontoplanen. Grupperingen går på kontonummer, ikke kontonavn. Ingen US GAAP/IFRS-begreper.

## Resultatregnskap (rskl. § 6-1, artsinndelt)

Gruppene er de samme som i `npm run -s regnskap` (gruppe-id = rad-id i `regnskap.json`). Linjene i § 6-1 som deler en gruppe
(salgsinntekt og annen driftsinntekt, avskrivning og nedskrivning) skilles på kontonivå i spesifikasjonen.

| Linje i oppstillingen | Kontoer | Gruppe-id | Tripletex-fortegn | Vises som |
|---|---|---|---|---|
| Driftsinntekter (salgsinntekt 3000–3399, annen driftsinntekt 3400–3999) | 3000–3999 | `driftsinntekter` | kredit (−) | positiv |
| Varekostnad | 4000–4999 | `varekostnad` | debet (+) | positiv |
| Lønnskostnad | 5000–5999 | `lonnskostnad` | debet (+) | positiv |
| Avskrivning og nedskrivning (nedskrivning 6050–6099) | 6000–6099 | `avskrivning` | debet (+) | positiv |
| Annen driftskostnad | 6100–7999 | `annenDriftskostnad` | debet (+) | positiv |
| **Sum driftskostnader** | varekostnad + lønn + avskrivning + annen | `sumDriftskostnader` | | |
| **Driftsresultat** | driftsinntekter − sum driftskostnader | `driftsresultat` | | |
| Finansinntekter | 8000–8099 | `finansinntekter` | kredit (−) | positiv |
| Finanskostnader | 8100–8299 | `finanskostnader` | debet (+) | positiv |
| **Resultat før skatt** | driftsresultat + finansinntekter − finanskostnader | `resultatForSkatt` | | |
| Skattekostnad | 8300–8499 | `skattekostnad` | debet (+) | positiv |
| Andre resultatposter (vises bare når ≠ 0) | 8500–8799 | `andreResultatposter` | debet (+) | positiv |
| **Årsresultat** (periodens resultat) | resultat før skatt − skatt − andre poster | `aarsresultat` | | |
| Overføringer og disponeringer (bare når bokført) | 8800–8999 | `disponeringer` | | |
| **Resultat etter disponeringer** (bare når det skiller seg fra årsresultatet) | årsresultat − disponeringer | `resultatEtterDisponeringer` | | |

- 8500–8799 skal normalt være tomme (ekstraordinære poster finnes ikke lenger i rskl.). Saldo der gir N6 MERKNAD: omklassifiser.
- Lønn er alltid én linje i rapporten til kunden. Spesifikasjon per konto (5000, 5400, 5900 …) er greit; aldri per ansatt.
- Varelagerklienter: 4090 (beholdningsendring) hører til varekostnaden. Sjekk at varetellingen er bokført før bruttomarginen tolkes.

## Balanse (rskl. § 6-2)

| Linje | Kontoer | Gruppe-id | Tripletex-fortegn | Vises som |
|---|---|---|---|---|
| Anleggsmidler (immaterielle 1000–1099, varige driftsmidler 1100–1299, finansielle 1300–1399) | 1000–1399 | `anleggsmidler` | debet (+) | positiv |
| Omløpsmidler (varer 1400–1499, fordringer 1500–1799, investeringer 1800–1899, bank og kontanter 1900–1999) | 1400–1999 | `omlopsmidler` | debet (+) | positiv |
| **Sum eiendeler** | anleggsmidler + omløpsmidler | `sumEiendeler` | | |
| Egenkapital (innskutt 2000–2049, opptjent 2050–2099) | 2000–2099 | `egenkapital` | kredit (−) | positiv |
| · Årets resultat (ikke disponert) | −Σ 3000–8999 fra 1.1 til balansedagen (beregnet linje) | `resultatHittil` | | positiv ved overskudd |
| · Udisponert resultat tidligere år | IB 1.1 som ikke er disponert (beregnet linje) | `udisponertTidligere` | | |
| Avsetninger og langsiktig gjeld | 2100–2299 | `langsiktigGjeld` | kredit (−) | positiv |
| Kortsiktig gjeld | 2300–2999 | `kortsiktigGjeld` | kredit (−) | positiv |
| **Sum gjeld** | langsiktig + kortsiktig | `sumGjeld` | | |
| **Sum egenkapital og gjeld** | egenkapital + sum gjeld | `sumEgenkapitalOgGjeld` | | |
| Kontroll: eiendeler − egenkapital og gjeld | skal være 0 | (lag_spec) | | OK/AVVIK |

- **Årets resultat (ikke disponert):** årets resultat er ikke overført til 2050/2080 før årsoppgjøret. Uten linjen går balansen ikke opp midt i året.
- **Udisponert resultat tidligere år ≠ 0** betyr at fjorårets resultat ikke er ført mot egenkapitalen (88xx–89xx mot 20xx). N1 er FORKLART
  til og med juni (årsoppgjøret er ikke bokført ennå) og MERKNAD fra juli. Står det en rest igjen etter de to linjene, er N1 AVVIK (IB-feil) og stopp.
- Kontoer med motsatt saldo av gruppen (bank i minus, kunde i kredit, leverandør i debet) står i sin gruppe med minus og flagges N8 når
  beløpet er minst V/10. Unntatt (normalt motsatt fortegn): 1580 avsetning tap, 2010 egne aksjer, 2080 udekket tap, 3080–3099 rabatter,
  5800–5899 refusjoner. Kassekreditt i 2380 er kortsiktig gjeld; trekk på driftskontoen (19xx negativ) flyttes ikke i rapporten, men nevnes.

## Fortegn og avvik

- Tripletex lagrer debet som + og kredit som −. Rapporten viser **presentasjonsfortegn**: inntekter, kostnader, egenkapital og gjeld positive;
  resultatlinjene regnes med ± (driftsresultat = inntekter − kostnader). Et motsatt fortegn i en linje vises med minus.
- **Avvik kr = denne perioden − sammenligning** i presentasjonsfortegn. **Avvik % = avvik / |sammenligning| × 100**, tomt når sammenligningen er 0.
- **Gunstig/ugunstig:** høyere inntekt, lavere kostnad og høyere resultat er gunstig. For kostnader er et positivt avvik ugunstig.
- Sammenligning: forrige periode (måned → forrige måned, termin → forrige termin, år → fjoråret), samme periode i fjor, og budsjett når
  `/resultbudget` har tall for kontoene. Hittil i år sammenlignes med samme månedsantall i fjor.

## Flagg i oppstillingen

| Flagg | Vilkår (mot hver sammenligning) |
|---|---|
| AVVIK | \|avvik kr\| ≥ V |
| MERKNAD | \|avvik %\| ≥ terskel og \|avvik kr\| ≥ V/2 (terskel: budsjett 10 %, i fjor 15 %, forrige periode 20 %) |
| KJENT | Kjent avvik i kundeinstruksen med samme beløp |

V er vesentlighetsgrensen fra kundeinstruksen (standard: høyeste av 5 000 kr og 0,5 % av omsetningen siste 12 måneder). Gruppe- og
sumlinjer i resultatet flagges på samme måte; balansen flagges ikke (endringer i bank og gjeld er normale). `regnskap.json` har egne
flagg («V», «pst», «ny») med én terskel; tersklene per sammenligning over brukes av `lag_spec.py`.

## Nøkkeltall (N5)

| Nøkkeltall | Beregning | Normalområde | Utenfor |
|---|---|---|---|
| Bruttomargin (%) | (driftsinntekter − varekostnad) / driftsinntekter | endring < 5 prosentpoeng mot sammenligning | MERKNAD |
| Driftsmargin (%) | driftsresultat / driftsinntekter | ≥ 0 og endring < 5 pp | MERKNAD |
| Lønn i % av inntekt | lønnskostnad / driftsinntekter | endring < 5 pp | MERKNAD |
| Likviditetsgrad 1 | omløpsmidler / kortsiktig gjeld | ≥ 1,0 | MERKNAD (< 0,5: AVVIK) |
| Egenkapitalandel (%) | egenkapital (med udisponert resultat) / sum eiendeler | ≥ 10 % | MERKNAD; negativ egenkapital i AS: AVVIK |

- Margin og lønnsandel er bransjeavhengige: sammenlign med klientens egen historikk, ikke med en fast grense.
- Negativ eller lav egenkapital i AS: styret har handleplikt (asl. § 3-5) og egenkapitalen skal være forsvarlig (asl. § 3-4). Flagges til
  regnskapsfører og oppdragsansvarlig; Claude vurderer ikke forsvarligheten.
- Driftsinntekter under V: margin og lønnsandel er ikke meningsfulle og vises som IKKE AKTUELT.

## Årsregnskap og noter (når perioden er et år)

- Små foretak (rskl. § 1-6) kan bruke forenklet oppstilling og er **unntatt fra kontantstrømoppstilling** (rskl. § 3-2).
  Rapporten lager derfor ingen kontantstrøm; endring i bank vises i balansen.
- Årsregnskapet skal ha resultatregnskap, balanse og noter (rskl. § 3-2). Notene (rskl. kap. 7, forenklede noter for små foretak) lages i årsoppgjøret
  (Maestro), ikke her. Rapporten viser til notene som berøres av vesentlige avvik: regnskapsprinsipper, lønnskostnad og antall årsverk
  (aggregert), varige driftsmidler, egenkapital, skatt, fortsatt drift ved tap.
- Fortsatt drift (rskl. § 4-5): ved tap og negativ egenkapital må forutsetningen om fortsatt drift omtales. Det flagges i avvikslisten; vurderingen gjør regnskapsfører.
- Sammenligningstall for fjoråret er påkrevd (rskl. § 6-6). Er fjorårstallene omklassifisert (ny kontoplan, flyttede kontoer), skal det stå
  i rapporten (N7).
- Midlertidige tall før årsoppgjøret er ikke årsregnskap: skattekostnad, avskrivninger, periodiseringer og varetelling kan mangle.
  Skriv det i merknaden på resultatarket.
