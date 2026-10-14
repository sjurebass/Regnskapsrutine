# PBC-liste – typiske punkter, kilde og eier

PBC («prepared by client») er lista over det revisor ber klienten om. Byrået fører den på vegne av klienten. Hvert punkt har eier, frist og
status, og hver saldo i dokumentasjonen er kontrollert mot hovedboken (U12) før den sendes. Kontrollene U11–U14 står i `docs/stikkprover.md`.

## Kolonner

| Kolonne | Innhold |
|---|---|
| # | Revisors nummer når forespørselen har det, ellers løpenummer |
| Punkt | Kort, med revisors ord omskrevet (ikke sitat) |
| Område/konto | Kontonummer eller -intervall, eller «–» |
| Dato/periode | `ÅÅÅÅ-12-31`, `ÅÅÅÅ-MM` eller `ÅÅÅÅ` |
| Type | Spesifikasjon · Avstemming · Bilag · Avtale/protokoll · Rapport · Bekreftelse · Forklaring |
| Eier | Byrå (rolle: regnskapsfører) eller kunden |
| Kilde | Tally-dokument (filnavn), Tripletex (modul, «Dokumenter», bilag), revisors egen tilgang, eller «lages i <skill>» |
| Frist | Revisors frist; byråets interne frist to virkedager før |
| Status | Klar · Lages · Venter kunde · Ikke aktuelt (med grunn) |
| Saldo kontrollert | UB i hovedbok, saldo i dokumentet, differanse (U12) |

## Typiske punkter

| Punkt | Konto | Finnes i | Lages i | Eier |
|---|---|---|---|---|
| Saldobalanse og hovedbok 31.12 | alle | saldobalanse: `regnskap`; hovedbok: SAF-T (`/saft/exportSAFT`) | – | byrå |
| Bankavstemming 31.12, kontoutskrifter og årsoppgaver | 19xx | Tally `Bankavstemming ÅÅÅÅ`; `modul -- bankpdf` | `bankavstemming` | byrå; årsoppgaver: kunden |
| Kundereskontro med aldersfordeling og tapsvurdering | 1500, 1580 | Tally `Reskontro ÅÅÅÅ`; `modul -- reskontro-vurdering` | `reskontroavstemming` | byrå |
| Leverandørreskontro | 2400 | Tally `Reskontro ÅÅÅÅ` | `reskontroavstemming` | byrå |
| Mva per termin og oppgjørskonto | 2700–2799 | Tally `Mva ÅÅÅÅ` (2740-notat), Altinn-kvitteringer i Tally | `mva-kontroll`, `mva-innlevering` | byrå |
| Lønn mot A07, trekk, AGA og feriepenger | 2600, 2770, 2940, 5000–5999 | Tally `Lønn ÅÅÅÅ` | `lonnsavstemming` | byrå |
| Balansespesifikasjon: periodiseringer, lån, mellomregning, egenkapital, skatt | 17xx, 29xx, 22xx, 2000–2099, 2500/1570 | Tally `Årsoppgjør ÅÅÅÅ` (Balansespesifikasjon), avstemmingsmodulen, Tripletex «Dokumenter» per konto | `balanseavstemming` | byrå |
| Anleggsregister og avskrivninger | 1000–1299, 6000–6099 | `/asset`, Tally `Årsoppgjør ÅÅÅÅ` | `balanseavstemming` (A4) | byrå |
| Periodiseringer med grunnlag | 17xx, 29xx | bilagene og planen i `periodisering` | `periodisering`, `balanseavstemming` | byrå |
| Varetelling 31.12 | 14xx | Tally `Årsoppgjør ÅÅÅÅ` (lagerliste) | – | kunden |
| Låneavtaler og årsoppgaver fra långiver | 22xx | Tally `KONTRAKT` | – | kunden |
| Protokoller, aksjeeierbok, vesentlige avtaler | – | Tally `KONTRAKT`; `aksjonaerregister` | – | kunden |
| Utvalgte bilag med vedlegg | etter revisors utvalg | Tripletex | `dokument --bilag` | byrå |
| Skattekonto og forskuddsskatt | 1570, 2500 | `/claimsAndPayments`, Altinn-brev i Tally | `balanseavstemming` (S6) | byrå |
| Hendelser etter balansedagen, tvister, garantier, ufakturert | – | – | – | kunden |
| Fullstendighetserklæring | – | – | signeres av ledelsen | kunden |
| Saldobekreftelser fra bank og motparter | – | – | revisor innhenter; byrået kan gi motpartsliste | revisor |

## Hva byrået ikke sender

- Byråets interne arbeidspapirer, vurderinger og kvalitetskontroll (bare etter ja fra oppdragsansvarlig).
- Persondata utover forespørselen: lønn per ansatt bare når revisor spør om det, og aldri i e-postteksten.
- Opplysninger om andre klienter, eller noe byrået skulle signert for klienten.

## Svarmal (Missive-utkast, punktliste)

```
Hei,

Status for forespørselen datert ÅÅÅÅ-MM-DD om Eksempel AS, regnskapsåret ÅÅÅÅ:

1. Saldobalanse 31.12 – lagt i dokumentarkivet: «<filnavn>».
2. Bankavstemming 31.12 – lagt i dokumentarkivet; kontoutskrift fra banken kommer fra kunden innen ÅÅÅÅ-MM-DD.
3. Lønn mot A07 – ligger i Tripletex; dere har tilgang under <sti i Tripletex>.
4. Hendelser etter balansedagen – kunden svarer direkte.

Gi beskjed hvis noe mangler.
```

Utkastet sendes aldri av Claude. Punktene som kunden eier, går som eget utkast til kundens hovedkontakt.
