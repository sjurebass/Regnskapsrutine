# Kontrollogikk – lønnsavstemming A07

Skriptene i `scripts/` gjør kontrollene deterministisk. Dette dokumentet forklarer
hvor A07 kommer fra, hva skriptene regner ut, hvilket format `ledger.json` har,
hva som ikke lenger kan kontrolleres, og hva som er verifisert.

---

## Status per 14.10.2026

A07 hentes nå fra Tally (Skatteetaten via Maskinporten/Altinn) som JSON. XML og ODS fra Altinn brukes ikke lenger,
og kontrollen per ansatt er fjernet: rapporten fra Tally har ingen personopplysninger.

| Hva | Resultat |
|---|---|
| Eksempelet (`scripts/a07_tally_eksempel.json` + `scripts/ledger_eksempel.json`) | Alle kontroller OK; «Skyldig AGA» og «Betalt forrige termin» er FORKLART (restsaldo fra året før). `silfer-rapport/scripts/sjekk.py` gir exit 0. |
| Ekte termin med Tally-A07 | **Ikke verifisert ennå.** Kjør på én termin som er godkjent med den gamle XML-versjonen før skillen brukes bredt (se under). |

Kontrollene som bare bruker regnskapet (saldokontroll 2600, 1950, kostnadsført og kreditert AGA, UB 2770, feriepenger,
pensjon hittil i år) er uendret fra versjonen som var verifisert mot tre ferdige avstemminger (17.09.2026).

Regnskapssiden hentes med `npm run -s lonn -- hent … --a07 a07.json --ut <mappe>` (API-koblingen), som er brukt på én ekte
termin. Kontroller posteringene i ledger.json første gang kommandoen brukes på en ny klient.

### Verifiser selv etter endringer

Fra repo-rota, med A07 for samme termin hentet fra Tally som `a07.json`:

```bash
uv run --with openpyxl python .claude/skills/lonnsavstemming/scripts/ledger_fra_rapport.py "<godkjent rapport>.xlsx" <scratch>/ledger.json
uv run --with openpyxl --with pillow python .claude/skills/lonnsavstemming/scripts/lonnsavstemming_a07.py <scratch>/a07.json <scratch>/ledger.json <scratch>/ny.xlsx
uv run --with openpyxl python .claude/skills/lonnsavstemming/scripts/sammenlign.py "<godkjent rapport>.xlsx" <scratch>/ny.xlsx
```

`ledger_fra_rapport.py` leser både gamle rapporter (sju ark) og nye (seks ark). Mot en gammel rapport er det
forventet at «Per ansatt» mangler, at radene per lønnsdato er byttet med rader per måned, og at «Ytelser A07» har ny
layout. Alle andre radetiketter og tall skal stemme.

`sammenlign.py` kjenner rader på teksten i kolonne A. Like etiketter (datoer i «Posteringer», månedsnavn i
«Arbeidsgiveravgift») gir derfor falske «TALL»-linjer. Formelceller i den nye filen har ingen bufret verdi før Excel
har vært innom, så avvikskolonnene ser tomme ut. Begge deler er normalt.

---

## A07 fra Tally (`a07.json`)

Hentes med `hent_amelding_rapport(client_id, start_month, end_month)` og lagres slik Tally returnerer den.
`scripts/a07.py` (`les_a07()`) leser den. Utfylt eksempel: `scripts/a07_tally_eksempel.json`.

```json
{
  "klient": "Eksempel AS", "periode": "2026-01 – 2026-02", "avstemt": "2026-03-10T09:12:41",
  "totalt": { "forskuddstrekk": 100252, "arbeidsgiveravgift": 48165, "finansskattLoenn": 0 },
  "per_maaned": [ { "kalendermaaned": "2026-01", "antallInnsendinger": 1, "forskuddstrekk": 49909, "arbeidsgiveravgift": 23865, "finansskattLoenn": 0 } ],
  "loenn_og_ytelser": [ { "fordel": "kontantytelse", "beskrivelse": "fastloenn", "utloeserArbeidsgiveravgift": true, "beloep": 333551.26 } ],
  "innsendinger": [ { "kalendermaaned": "2026-01", "status": "GODKJENT", "kildesystem": "Tripletex", "leveringstidspunkt": "2026-01-23T14:05:11",
                      "antallInntektsmottakere": 3, "erstattet": false, "forskuddstrekk": 49909, "arbeidsgiveravgift": 23865, "finansskattLoenn": 0,
                      "forfallsdato": null, "kontonummer": "00000000000",
                      "kid": { "forskuddstrekk": "…", "arbeidsgiveravgift": "…", "finansskattLoenn": "…" } } ],
  "avgiftsgrunnlag": [ { "virksomhet": "999999999", "type": "loenn", "sone": "1", "beregningskode": "generelleNaeringer", "grunnlag": 335525.63, "sats": 14.1 } ],
  "merknad": "… null betyr at kilden ikke oppga beløpet, ikke null kroner. Erstattede a-meldinger er holdt utenfor månedssummene."
}
```

| Felt | Innhold | Brukes til |
|---|---|---|
| `totalt` | trekk, AGA og finansskatt for perioden | trekk termin, innbetalt, saldokontroll 2600, AGA termin |
| `per_maaned[]` | trekk, AGA og finansskatt per måned, uten erstattede meldinger | trekk og AGA per måned |
| `loenn_og_ytelser[]` | ytelser per type for **hele perioden** (`fordel`, `beskrivelse`, AGA-pliktig, beløp) | «Ytelser A07», utbetalte feriepenger |
| `innsendinger[]` | hver a-melding: status, kildesystem, levert, antall inntektsmottakere, erstattet, beløp, forfall, konto, KID | «Detaljer», KID, kontonummer, forfall |
| `avgiftsgrunnlag[]` | grunnlag per virksomhet, type, sone og beregningskode, med sats i prosent | grunnlag lønn/pensjon/fradrag, sats, sone, beregnet AGA |
| `periode`, `avstemt`, `klient`, `merknad` | fom–tom, hentetidspunkt, klientnavn, Tallys merknad | overskrift og «Kilder» |

Regler:

- **null er ikke 0.** null betyr at kilden ikke oppga beløpet. Verdien blir `None`, vises som «ikke oppgitt», raden får
  ingen avviksformel og står som AVVIK (FORKLART bare med merknad), med kommentaren «kontroller i Altinn».
  Unntak: er `totalt` null og alle månedene oppgitt, brukes Σ `per_maaned`.
- **Måned som mangler** i `per_maaned` = ingen a-melding for måneden: 0 med kommentaren «Ingen a-melding for måneden i A07».
  Månedene i kontrollen er månedene i A07 pluss måneder med lønnsbilag på 2600/2770.
- **Erstattede a-meldinger** er holdt utenfor av Skatteetaten/Tally. `erstattet` vises i «Detaljer», og «A07 totalt mot
  innsendinger» summerer de som ikke er erstattet. Statusfeltet avgjør ingenting.
- Trekk og AGA er hele kroner. Ytelser og grunnlag kan ha øre.
- `avgiftsgrunnlag.type`: `loenn` → grunnlag lønn, `pensjon` → pensjon, typer med «fradrag» → fradrag i grunnlaget
  (alltid negativt internt). Andre typer listes under «Kilder», nevnes i kommentaren til «Beregnet AGA termin» og
  holdes utenfor beregningen.
- Sats er prosent i JSON og brøk i `a07.py`. Sats og sone tas fra lønnsraden med størst grunnlag; `aga_sats` i
  ledger.json går foran.
- KID: siste gjeldende innsending (trekk per måned, AGA for terminen). `kontonummer` er Skatteetatens innbetalingskonto.
- Forfall: `forfallsdato` når den er oppgitt (ofte null), ellers `periode.forfall` i ledger.json (15. i måneden etter terminen).
- `antallInntektsmottakere` vises bare som antall.

### Det som ikke lenger kan kontrolleres

- **Per person**: ytelser, AGA og trekk per ansatt. Rapporten har ingen personer, og det er meningen. Arket «Per ansatt»
  og beløpsmatchingen mot lønnsbilagslinjene er fjernet. Feil fordeling mellom ansatte som går i null i sum, fanges ikke her.
- **Per lønnsdato**: trekk kontrolleres per måned. To lønnskjøringer i samme måned skilles ikke.
- **Grunnlag per måned**: grunnlaget og ytelsene gjelder hele perioden. AGA kontrolleres per måned bare mot 2770, og
  beregnet AGA (grunnlag × sats) bare for terminen.

---

## Arkene i Excel-fila

Filnavn: `Lønnsavstemming <Klient> termin <n> <år>.xlsx`. Seks ark:

| Ark | Innhold |
|---|---|
| Avstemming | sammendrag: kontroll · A07/beregnet · regnskap · avvik · status, i fire blokker (forskuddstrekk, AGA, feriepenger, ytelser), antall avvik, til betaling, merknader |
| Detaljer | innsendinger (status, kildesystem, levert, antall mottakere, AGA, trekk, gjeldende/erstattet, KID), betalinger, saldoer, reverserte bilag, kilder |
| Forskuddstrekk | trekk per måned mot 2600, innbetalt, saldokontroll, 1950 |
| Arbeidsgiveravgift | pkt. 1 AGA per måned mot 2770 og avgiftsgrunnlaget i A07; pkt. 2–5; pensjon hittil i år |
| Ytelser A07 | ytelse · AGA-pliktig · konto · A07 · regnskap · avvik · status, for perioden |
| Posteringer | posteringene fra ledger.json |

---

## ledger.json

Regnskapssiden. `npm run -s lonn -- hent --client "<klient>" --aar ÅÅÅÅ --termin N --a07 <mappe>/a07.json --ut <mappe>` skriver
`<mappe>/ledger.json` med alle felt unntatt `feriepenger_sats`, `forklart`, `merknader` og `kommentarer` (og `ytelse_konto`), som fylles inn
for hånd. Kommandoen legger også ved `advarsler` (les dem først) og `kilde_a07`/`kilde_regnskap` (vises under «Kilder»).
Et utfylt eksempel ligger i `scripts/ledger_eksempel.json`.

| Felt | Forklaring |
|---|---|
| `selskap`, `orgnr`, `tripletex_id` | vises i overskriften og under Kilder |
| `periode` | `{termin, forfall}` – forfall er 15. i måneden etter terminslutt; brukes når A07 ikke oppgir forfallsdato |
| `aga_sats` | f.eks. `14.1`. Faller tilbake til satsen i A07 |
| `feriepenger_sats` | `0.12`, `0.125` eller `0.143` – leses av 5020/5000 i et lønnsbilag |
| `konto` | `{"pensjon": 5945}` – autodetekteres blant 5945/5950/5946/5940 |
| `ytelse_konto` | overstyrer kontomapping per ytelse (`beskrivelse`), bare der klienten avviker fra standard, f.eks. `{"elektroniskKommunikasjon": 5390}` når EK er utgiftsgodtgjørelse |
| `balanser` | `[{a: konto, n: navn, ib, ch, ub}]` |
| `posteringer` | `[[dato, bilag, konto, kontonavn, tekst, beløp]]` – `bilag` er `voucher.number` som streng (f.eks. «50019»); teksten har «Lønnsbilag 8-2026». De er ikke like |
| `pensjon_historikk` | `[["YYYY-MM", tekst 594x, bokført beløp, tekst pensjonsbilag, innrapportert grunnlag]]` for hele året; grunnlag = AGA i pensjonsbilaget / sats |
| `forklart` | prefikser på kontrollrader som skal vise FORKLART i stedet for AVVIK – bare når merknaden forklarer avviket fullt ut |
| `kommentarer` | `{"<kontrollrad>": "tekst"}` – overstyrer kommentaren på en rad |
| `merknader` | fritekst til Excel, kan være utfyllende |
| `merknader_kort` | én setning per punkt med beløp, bilag og tiltak (til PDF) |
| `trekkmodell`, `trekkmodell_1950` | kommentartekst på de to trekkradene |

KID og kontonummer leses fra a07.json, ikke fra ledger.json. `pensjon_historikk` trengs for «Grunnlag pensjon hittil i år»
og forklaringen av differansen i pkt. 2.

---

## Klassifisering av bilag

| Type | Kjennetegn |
|---|---|
| Betaling | teksten starter med `Betaling:`, **eller** inneholder `Overføring skattetrekk` (direkte-modellen: overføringen av trekket er en linje i selve lønnsbilaget, samme bilag og dato, f.eks. «Lønnsbilag 8-2026. Overføring skattetrekk» +30 884 mot −1 479, −13 973 og −15 432) |
| Avrundingsbilag | teksten inneholder `A-melding lønn` (f.eks. «A-melding lønn <mnd>»: ører på 2770/2600 mot 7740) |
| Lønnsbilag | teksten inneholder `Lønnsbilag` («Lønnsbilag N-ÅÅÅÅ»), og er verken betaling eller avrunding |
| Pensjonsbilag | 2770-linjer som verken er betaling, avrunding eller lønnsbilag (typisk «Pensjon <måned> …») |
| Feriepengebilag | lønnsbilag uten lønnslinjer (5000–5099 utenom 5020) og med 2940-debet |
| Reversert | teksten matcher `Reversering av bilag N` – reverseringen og originalen nettes til null, holdes utenfor alle kontroller og listes i egen tabell |

Typen avgjøres av teksten. Feriepengebilag og reverseringer grupperes på `bilag`-feltet, som ikke er nummeret i teksten.
Linjen «Overføring skattetrekk» telles derfor ikke som trekk i lønnsbilag, men som innbetalt.

Skillet mellom feriepengebilag og ordinære lønnsbilag er avgjørende: 2785-debet på et feriepengebilag er frigjort AGA,
mens 2785-debet i en ordinær kjøring er noe annet. Det samme gjelder 2940.

---

## Kontrollene på «Avstemming»

**Forskuddstrekk (2600)**

- Per måned: A07 `per_maaned.forskuddstrekk` = −Σ 2600 i lønnsbilag samme måned (±1 kr)
- Termin: A07 `totalt.forskuddstrekk` = −Σ 2600 lønnsbilag − avrundingsbilag
- Innbetalt: Σ 2600-debet «Betaling: Lønnsbilag» og «Overføring skattetrekk». Avvik mot a-meldt = for mye (−) eller for lite (+) innbetalt
- Saldokontroll: `−IB + a-meldt − innbetalt − andre føringer` mot `−UB`, der innbetalt er alle betalinger på 2600
  (også «Overføring skattetrekk»). Vises som residual mot 0 (UB − IB − innbetalt + a-meldt = 0)
- Direkte-modell (overføring på lønnsdato, som eget «Betaling: Lønnsbilag» eller som linje i lønnsbilaget): 2600 = 0, 1950 ubrukt
- Skattetrekkskonto-modell: UB 1950 skal være ≥ skyldig 2600
- Negativt trekk = tilbakebetaling. Betalt trekk + reversering gir 2600-debet = tilgodehavende → motregn den 15. eller krev tilbake

**Arbeidsgiveravgift – grunnlag (pkt. 2)**

- A07 grunnlag lønn = `avgiftsgrunnlag` type `loenn`, for hele perioden
- Regnskap: bevegelse 5000–5399 (utenom 5020 og 5290) + 5500–5599 + utbetalte feriepenger (2940-debet på feriepengebilag)
  + pensjonskontoen − NAV-refusjon (58xx)
- Grunnlag pensjon: bevegelse på pensjonskontoen mot `avgiftsgrunnlag` type `pensjon`; hittil i år fra `pensjon_historikk`
- Fradrag i grunnlaget (NAV-refusjon): vises når A07 har fradrag (eller det ikke er oppgitt), mot bevegelse 58xx
- Differanse forklares med: (1) pensjon periodisering = innrapportert (pensjonsbilag / sats) − 594x i perioden; hittil i år skal være 0;
  (2) konti med bevegelse uten lønnsbilag («NEI – kontroller», typisk 5320) = mulig ikke-innrapportert fordel; (3) avrunding

**Arbeidsgiveravgift (pkt. 1, 3 og 4)**

- Per måned: A07 `per_maaned.arbeidsgiveravgift` = −Σ 2770 i måneden utenom betalinger og avrundingsbilag
  (lønnsbilag + pensjonsbilag, også AGA av utbetalte feriepenger 2785/2780 → 2770), ±1 kr. Tripletex runder ned til hele
  kroner per måned; ørene ligger i avrundingsbilaget «A-melding lønn», som kan være reversert og kjørt på nytt
- Beregnet termin: Σ grunnlag × sats per rad i `avgiftsgrunnlag` (lønn + pensjon − fradrag) ≈ innrapportert, toleranse
  største av 2 kr og antall måneder
- Kostnadsført: 5400 + AGA av utbetalte feriepenger (2780/2785-debet på feriepengebilag) ≈ innrapportert (øre)
- Kreditert 2770: lønnsbilag + pensjonsbilag − avrundingsbilag, utenom betalinger = innrapportert nøyaktig
- UB 2770 skal være lik innrapportert termin; rest er gammel saldo. 2770 IB ≠ forrige termins a-meldte AGA → forklar restsaldoen
- A07 totalt mot innsendinger: `totalt.arbeidsgiveravgift` = Σ innsendinger som ikke er erstattet
- Betaling den 15. i måneden etter terminen, KID for AGA fra A07

**Feriepenger**

- 5020 = sats × 5000
- 5401 = AGA-sats × 5020
- Avsetning 2940 = −Σ 2940-linjer i lønnsbilag utenom feriepengebilagene (Σ 5020 = −Σ 2940-kredit; negative kjøringer nettes inn
  og gir negative 5020/5401, ikke utbetaling)
- Utbetalte feriepenger = A07-ytelser med «feriepenger» i beskrivelsen (perioden) = 2940-debet på feriepengebilag

**Ytelser per konto («Ytelser A07»)**

- Hver ytelsestype i `loenn_og_ytelser` får konto fra `ytelse_konto`, ellers standardmappingen i `a07.py`:
  fastloenn/timeloenn/overtid/uregelmessige tillegg → 5000, bonus → 5001, sykepenger → 5030, feriepenger → 2940 (utbetalt),
  bil → 5200, elektroniskKommunikasjon → 5210 (5390 når utgiftsgodtgjørelse), annet og ukjent → 5260, reiseKost og trekkpliktig
  km → 5510; avgiftsfri km/passasjer/kost → 7100/7150
- Regnskap for perioden: 5000–5999 i lønnsbilag, 2940 = utbetalte feriepenger, andre konti (71xx) = alle posteringer
  (reiseregninger er ikke lønnsbilag)
- Flere ytelser på samme konto summeres i raden «Sum konto»; status per konto, ±1 kr. «Ytelser per konto» på «Avstemming»
  er antall konti som stemmer
- `kilometergodtgjoerelseBil` kan komme to ganger, med og uten AGA (den trekkpliktige delen); begge går til 7100
- «Sum AGA-pliktige ytelser» mot avgiftsgrunnlag lønn: differansen er fradrag i grunnlaget eller avrunding
- EK: naturalytelse (5210 + motkonto 5290) eller utgiftsgodtgjørelse (5390, kontant) – les `fordel` og sett `ytelse_konto`

**NAV-refusjon**

Sykepenger og foreldrepenger som NAV refunderer, kommer som fradrag i `avgiftsgrunnlag` – ofte fra en egen tilleggsmelding
med negativ AGA. I regnskapet: 2770-debet / 5400-kredit (AGA) og 58xx/5000-kredit (grunnlag).

## Typiske funn

| Funn | Tiltak |
|---|---|
| «ikke oppgitt» i A07 | se a-meldingen i Altinn eller hent rapporten på nytt; merknad på raden |
| Måned uten a-melding | send a-meldingen (`a-melding`) og hent A07 på nytt |
| 2600 debet = negativt trekk i A07 | motregn den 15. eller krev tilbake |
| Flere innsendinger samme måned | «Detaljer» viser hvilke som er erstattet; summene er allerede uten dem. Forklar forløpet |
| Trekk i måneden = 0 netto i lønnsbilag | «Overføring skattetrekk» står i lønnsbilaget med annen tekst – sjekk klassifiseringen |
| Pensjon: avvik i perioden, men 0 hittil i år | FORKLART (periodisering) |
| Pensjon: avvik hittil i år ≠ 0 | korriger i neste a-melding; AGA-effekt = differanse × sats |
| UB 2770 ≠ innrapportert | rydd restsaldoen (gammel termin) |
| 53xx uten lønnsbilag | avklar skatteplikt (mulig ikke-innrapportert fordel) |
| Ytelse per konto avviker | feil `ytelse_konto`, eller tillegg ført utenfor lønnsbilag eller reiseregning |

Sticos «for året» kan mangle terminer – saldobalansen i Tripletex er fasit hittil i år.
Saldobalansen utelater 2600 når IB, bevegelse og UB er 0. `lonn hent` regner da fra posteringene med IB 0 og gir en advarsel – sjekk IB.

## Kjøring

```bash
uv run --with openpyxl --with pillow python .claude/skills/lonnsavstemming/scripts/lonnsavstemming_a07.py <scratch>/a07.json <scratch>/ledger.json "<scratch>/Lønnsavstemming <Klient> termin <n> <år>.xlsx"
```

Krever `openpyxl` og `pillow`. Farger, statusregler og logo kommer fra `silfer-rapport` (`from silfer.stil import …`;
logoen er `.claude/skills/silfer-rapport/assets/silfer_logo.png`), så hele repoet må være klonet. LibreOffice finnes
ikke på maskinene: formlene beregnes først når filen åpnes i Excel. Celletekst skal aldri starte med `=`.
Får du «XML brukes ikke lenger» eller «Fant ingen A07 i fila», er fila ikke svaret fra `hent_amelding_rapport`.
