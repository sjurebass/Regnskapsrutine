# Kategorier for åpne poster i reskontro

Reglene er de samme som i byråets API-kobling, så MCP og API-kobling gir samme svar for samme dato. Endres de, endres begge.
Etikettene brukes ordrett, med tankestrek (–), ikke bindestrek.

## Grunnlag

- `S` = siste dag i perioden. `D` = S + 1 dag (eksklusiv dato i `search_open_postings`). Datoer i etikettene skrives dd.mm.åååå.
- **Uttrekk 1:** åpne poster per D for 1500 og 2400, alle datoer. **Uttrekk 2:** åpne poster per i morgen, bare id → «åpen i dag».
- **Krav:** på 1500 er en post et krav når beløpet er positivt; på 2400 når beløpet er negativt. Ellers er posten innbetaling, kreditnota eller betaling.
- **Forfall:** postens forfallsdato; mangler den, posteringsdatoen. **Dager forfalt** = S − forfall i kalenderdager.
  På 2400 kommer forfallet fra `search_supplier_invoices` (bilagsnummer → forfall); `search_open_postings` har forfall bare på kunderader.
- **Motpart:** kunden på 1500, leverandøren på 2400. Mangler motpart: «Uten motpart» (R9).

## Kategori – første regel som slår til

| # | Vilkår | 1500 Kundefordringer | 2400 Leverandørgjeld |
|---|---|---|---|
| 1 | ikke åpen i dag, og krav | `Betalt etter <S>` | `Betalt etter <S>` |
| 2 | ikke åpen i dag, ikke krav | `Utlignet etter <S>` | `Utlignet etter <S>` |
| 3 | i en nullgruppe | `Kan utlignes (går i null mot andre poster)` | samme |
| 4 | \|beløp\| under 100 kr | `Småbeløp under 100 kr` | samme |
| 5 | ikke krav | `Ufordelt innbetaling/kreditnota` | `Betaling uten faktura` |
| 6 | dager forfalt ≤ 0 | `Ikke forfalt per <S>` | samme |
| 7 | 1–30 dager | `Forfalt 1–30 dager` | samme |
| 8 | 31–90 dager | `Forfalt 31–90 dager – purring` | `Forfalt 31–90 dager uten betaling` |
| 9 | over 90 dager | `Forfalt over 90 dager – tapsvurdering` | `Forfalt over 90 dager uten betaling` |

## Nullgrupper (regel 3)

Per motpart som har id og mer enn én post, bare blant postene som er åpne i dag. Beløp sammenlignes i øre.
1. Går alle disse postene til motparten i null, er hele motparten én gruppe.
2. Ellers: eksakte par (+x og −x). Hver post brukes én gang, første treff vinner.
3. Resten, når det er 3–16 poster: minste delmengde med minst 3 poster som går i null. Gjenta til ingen flere finnes.

## Visning

- Bare poster datert i periodens år vises enkeltvis og i kategoritabellen. Eldre poster blir én linje:
  `Poster datert før <år> – vurderes i årsoppgjøret` (antall og sum). De listes enkeltvis i `aarsoppgjoer-forberedelse`.
- Kategoritabell per konto: Kategori · Poster · Beløp, i den rekkefølgen kategoriene først dukker opp; samlelinjen sist.
- Under tabellen for 1500: «Betalt etter» = åpen per S og lukket i dag. Avsetning tap på kundefordringer (1580): UB.
- **Krever oppfølging:** åpen i dag, datert i året, og kategori som ikke er `Betalt etter`, `Utlignet etter`, `Ikke forfalt` eller `Kan utlignes`.
  Bare disse motpartene får Brreg-oppslag og en vurdering. Sorter motpartene etter |sum|, størst først.
- Brreg-status, i denne rekkefølgen: `Slettet/finnes ikke` (ikke funnet i registeret), `Konkurs`, `Tvangsavvikling`, `Under avvikling`, ellers `Aktiv`.
  Feilet oppslaget: `Ukjent`.
- Privatpersoner: «privatkunde n» (nummerert i rekkefølge), uten org.nr.

## Terskler og status (funn-formatet i `docs/skill-mal.md`)

| ID | Kontroll | Utslag | Status |
|---|---|---|---|
| R1/R2 | Σ åpne poster per D mot UB 1500/2400 | differanse ≥ 1 kr | AVVIK |
| R3 | Feil fortegn per motpart | kunde under −V/10, leverandør over V/10 | AVVIK til forklart |
| R4 | Kunder forfalt over 90 dager, eller motpart konkurs/under avvikling | sum ≥ V | AVVIK (tapsvurdering) |
| R5 | Leverandører forfalt uten betaling | sum ≥ V | AVVIK til forklart |
| R6 | Dubletter blant åpne poster | samme motpart + fakturanr., eller samme beløp innen ±30 dager | AVVIK |
| R7 | Nullgrupper | ≥ 1 gruppe | forslag: utlign |
| R8 | Småbeløp | ≥ 1 post | forslag: utlign mot avrundingskonto |
| R9 | Post uten motpart | ≥ 1 post | AVVIK |
| R10 | Betalt eller utlignet etter S | – | OK (timing) |
| R11 | Poster datert før året | én samlelinje | – (vurderes i årsoppgjøret) |
| R12 | 1580 mot poster til tapsvurdering | 1580 lavere enn vurdert tap | forslag: avsetning |
| R13 | Kontoutskrift: IB + fakturert − innbetalt = UB | differanse ≥ 1 kr | AVVIK – ingen PDF |

Fakturanummer normaliseres før R6: store bokstaver, bare A–Z og 0–9, uten innledende nuller.
