# Avstemmingsmetodikk

Referanse, ikke en skill. Felles metode for `bankavstemming`, `reskontroavstemming` og `balanseavstemming`; `periodeavslutning` leser resultatet.
Avstemmingen viser at saldoen i hovedboken er riktig og dokumentert: hver forskjell mot kilden er forklart, klassifisert og fulgt opp.
Grunnlag: bokf.l. § 11 (dokumentasjon og avstemming av balansen), bokf.l. § 7 (ajourhold), bokf.l. § 13 (oppbevaring) og GRFS.
Claude stiller opp, klassifiserer og foreslår. Regnskapsfører avgjør kategori 3, oppdragsansvarlig poster over V.

V er vesentlighetsgrensen fra kundeinstruksen (seksjon «Regnskapssystem og byrå»; standard i `CLAUDE.md`). S er siste dag i perioden.
Kontroll-ID-ene står i `docs/kontrollkatalog.md`: B1–B8 (bank), R1–R15 (reskontro), S1–S13 (balanse).

## Avstemmingstyper

| Type | Hovedbok mot | Skill | Kilde (API) | Vanlige årsaker til forskjell |
|---|---|---|---|---|
| Bank mot kontoutskrift | 19xx mot bankens sluttsaldo per S | `bankavstemming` | `npm run -s bankavstemming` (`status.json`: `ub`, `bankSaldo`, `bank[]`, `tx`); kontoutskrift for kontoer uten bankfeed | poster i transitt, gebyr og renter ikke bokført, bankpost uten bilag, feil beløp |
| Reskontro mot hovedbok | 1500/2400 mot Σ åpne poster per S, og vurdering av hver åpen post | `reskontroavstemming` | `npm run -s modul -- reskontro-vurdering`, `/ledger/posting/openPost`, `/balanceSheet` | føring på 1500/2400 uten motpart, utligning på tvers av S, ompostering uten reskontro |
| Balansekonto mot spesifikasjon eller tredjepart | UB mot anleggsregister, periodiseringsliste, a-melding, mva-melding, skattekonto, låneoppgave | `balanseavstemming` | `/balanceSheet`, `/asset`, `amelding status`, `mva status`, `/claimsAndPayments`, dokument fra kunden | periodisering ikke ført eller ikke reversert, avskrivning mangler, betaling ført på feil konto |
| Mellomværende i konsern | fordring hos selskap A mot gjeld hos selskap B, motsatt fortegn | `balanseavstemming` (S13) | `/balanceSheet` per klient; saldobekreftelse når motparten ikke er klient | ført bare hos den ene (timing), ulik kurs, ført som ekstern motpart, omtvistet beløp, ulik periodeavgrensning |

Mellomværende i konsern: begge selskapene må være navngitt av brukeren. Er motparten ikke klient hos byrået, er kilden en saldobekreftelse
fra motparten via kunden; mangler den, er status IKKE AVKLART.

## Standardoppstilling (NOK)

Bank, med eksempel:

```
Saldo i banken per kontoutskrift S                         125 000,00
+ Innbetalinger i transitt (bokført, ikke i banken)          5 000,00
− Utbetalinger i transitt (bokført, ikke trukket)           −3 200,00
± Feil i banken                                                  0,00
= Justert saldo bank                                       126 800,00

Saldo i hovedboken 1920 per S                              127 150,00
+ Renter og innbetalinger i banken, ikke bokført               150,00
− Gebyr og trekk i banken, ikke bokført                       −500,00
± Feil i regnskapet                                              0,00
= Justert saldo hovedbok                                   126 800,00

Differanse                                                       0,00
```

Reskontro og andre balansekontoer:

```
Saldo i hovedboken <konto> per S                           X
± Føringer i hovedboken som ikke er i spesifikasjonen      (per post)
= Justert saldo hovedbok                                   A
Saldo i spesifikasjonen (Σ åpne poster, register, tredjepart) Y
± Poster i spesifikasjonen som ikke er ført                (per post)
= Justert saldo spesifikasjon                              B
Differanse A − B                                           0,00
```

Hver linje mellom saldo og justert saldo er en avstemmingspost med dato, beløp, kategori og alder. Det som står igjen etter postene,
er **uforklart differanse**. Tolerert avrunding: under 1 kr for reskontro og balanse; bank skal gå i 0,00.

## Kategorier for avstemmingsposter

| Kategori | Hva | Eksempler | Tiltak | Status · Krever |
|---|---|---|---|---|
| **1 Tidsforskjell** | Går av seg selv i neste periode uten føring | innbetaling eller utbetaling i transitt, korttrekk 1–3 dager etter kjøp, betalt eller utlignet etter S, faktura ikke forfalt, trekk og mva som forfaller den 15. | Ingen føring. Sjekk at posten er gått av ved neste avstemming; er den ikke det, blir den kategori 3. | FORKLART · – |
| **2 Krever føring** | Posten mangler eller er feil i regnskapet, og årsaken er kjent | gebyr og renter ikke bokført, bankpost uten bilag, feil beløp eller konto, dublett, periodisering eller reversering som mangler, avskrivning, småbeløp og nullgrupper som skal utlignes | Bankpost med dokument: `bilagsforing`. Periodiseringer, avsetninger, korreksjoner og omposteringer: `periodisering`, som fører med `bilag manuell` gjennom føringskontrollen (`docs/foringskontroll.md`), tørrkjøring og ja. Utligning: `modul utlign` i `reskontroavstemming`. Bilag mangler: kunden (mangelliste). | AVVIK til ført · ja i chat, kunden eller bare i UI |
| **3 Må undersøkes** | Kan ikke forklares nå | uforklart beløp, omtvistet beløp, post over 60 dager uten forklaring, samme type forskjell hver periode, ufordelt innbetaling, post uten motpart | Finn rotårsaken, dokumenter undersøkelsen, eskaler etter tabellen under. Blir årsaken kjent, flyttes posten til kategori 1 eller 2. | AVVIK eller IKKE AVKLART · regnskapsfører eller oppdragsansvarlig |

Kjent avvik i kundeinstruksen med samme beløp: KJENT, uansett kategori. Nytt beløp er nytt funn.
I funn-formatet (`docs/skill-mal.md`) står kategori og aldersgruppe først i Forslag, for eksempel `Kat. 2 · 31–60 · før gebyr på 7770`;
i Silfer-filen som egne kolonner Kategori og Alder. **Krever** kan i tillegg til verdiene i malen være `oppdragsansvarlig`.

## Aldersfordeling

Alder i dager per S: bankpost fra transaksjonsdatoen, reskontropost fra forfall (dager forfalt), annen post fra bilagsdatoen eller
første periode posten var åpen.

| Alder | Status | Tiltak |
|---|---|---|
| 0–30 dager | Løpende | Følg med; innenfor normal behandlingstid |
| 31–60 dager | Eldes | Undersøk hvorfor posten ikke er gått av; spør kunden |
| 61–90 dager | Forfalt | Eskaler: regnskapsfører vurderer og dokumenterer undersøkelsen |
| Over 90 dager | Gammel | Eskaler til oppdragsansvarlig: føring, tap eller avskrivning. Posten videreføres ikke uten beslutning |

Aldersrapport per konto: Nr · Dato · Konto/motpart · Beløp · Alder · Kategori · Status · Forslag · Krever, med sum per aldersgruppe og kategori.

## Eskaleringsgrenser

| Utløser | Grense | Eskalering |
|---|---|---|
| Enkeltpost | over V/2 | Regnskapsfører vurderer (Krever: `regnskapsfører`) |
| Enkeltpost | over V | Oppdragsansvarlig (Krever: `oppdragsansvarlig`) |
| Sum avstemmingsposter per konto | over V | Regnskapsfører vurderer samlet; gul port, rød når noe av det er kategori 3 |
| Alder | over 60 dager | Regnskapsfører følger opp |
| Alder | over 90 dager | Oppdragsansvarlig |
| Uforklart differanse | ethvert beløp over toleransen | Kan ikke lukkes: løs eller dokumenter først |
| Samme post eller samme type post | tre perioder på rad | Prosessavvik: rotårsak, og forslag til ny regel i kundeinstruksen |

Port (samme som i `docs/skill-mal.md`): grønn = ingen poster i kategori 2 eller 3; gul = kategori 2, eller kategori 3 under V;
rød = uforklart differanse, kategori 3 over V, eller post over 90 dager over V.

## Når en avstemming ikke kan lukkes

Lukking betyr her: lukke bankavstemmingen for måneden, sette RECONCILED i avstemmingsmodulen, fullføre avstemmingsoppgaven i Tally eller låse perioden.

**Stopp:** differansen etter oppstillingen er 0,00 (bank) eller under 1 kr (reskontro og balanse) – ellers lukkes ingenting: vis oppstillingen og let etter årsaken.
**Stopp:** ingen post i kategori 3 over V står uten beslutning – ellers lukkes ingenting: vis posten med `Krever: oppdragsansvarlig` og vent på svar i chatten.

Poster i kategori 1 og 2 under V stopper ikke lukkingen når de står i aldersrapporten med neste steg.

## Trend over perioder

Sammenlign med forrige periode for samme konto:

- Antall og sum per kategori og aldersgruppe. Flagg når summen er over V, eller antallet har økt tre perioder på rad.
- Poster som går igjen (samme motpart, samme type, samme beløp): tre perioder på rad er prosessavvik, ikke en ny avstemmingspost.
- Kilde: bank har alle måneder i `status.json` (`--fra` januar); reskontro og balanse har forrige periodes Silfer-fil i Tally-arkivet
  (samlingen for året), eller samme kommando kjørt for forrige S.

## Prinsipper

1. **Frist:** avstemmingen er ferdig innen fristen i månedshjulet (`README.md`): bank den 15., balanse den 16., reskontro den 20., i terminmåneder
   før `mva-kontroll` den 25. Rekkefølgen følger avhengighetsnivåene i `periodeavslutning`.
2. **Alle balansekonti med fast frekvens:** månedlig for bank, 1500/2400 og kontoer over V; per termin for 26xx–27xx; per 31.12 for resten.
   Kundeinstruksen («Reskontro og balanse») kan sette annen frekvens per konto; mangler den, gjelder standarden.
3. **Dokumentasjon:** hver avstemming har klient, konto, periode, saldo, kilde, oppstilling, hver post med forklaring, utført av
   (regnskapsførerens initialer) og dato. Lagres i Tally-arkivet (`docs/dokumentlagring.md`) og i avstemmingsmodulen.
4. **Gjennomgang:** poster over V gjennomgås av oppdragsansvarlig, helst en annen enn den som avstemte.
5. **Oppfølging til løst:** hver post har neste steg og eier, og følges til den er gått av, ført eller avskrevet. Ingen post videreføres i det uendelige.
6. **Rotårsak:** en gjentakende post rettes ved kilden (fast føring, bankregel, bilagsføringsregel, purrerutine), og regelen tilbys lagret i kundeinstruksen.
