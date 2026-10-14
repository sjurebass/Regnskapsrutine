# Kontrollogikk – lønnsavstemming A07

Skriptene i `scripts/` gjør kontrollene deterministisk. Dette dokumentet forklarer
hva de regner ut, hvilket format `ledger.json` har, og – viktigst – **hva som er
verifisert mot ferdige avstemminger og hva som ikke er det.**

---

## Status per 17.09.2026

Generatoren er bygget ved å reverse-engineere de ferdige rapportene i
kundemappene, og verifisert mot dem.

| Klient / termin | Resultat |
|---|---|
| Enkel klient, termin 1 | Arket «Avstemming» **identisk med fasit** – alle radetiketter og alle tall. Detaljer, Forskuddstrekk og Arbeidsgiveravgift har samme radeantall og samme tall. |
| Sammensatt klient, termin 4 – reverseringer, tilbakebetaling, tre lønnsdatoer, negativ lønnskjøring | Arket «Avstemming» **identisk med fasit**. Detaljer 77 rader mot fasits 77. |
| Tredje klient, termin 2 | «Avstemming» stemmer på alle rader unntatt tellingen «Ytelser per ansatt», som avhenger av `ytelse_konto` – se under. |

`scripts/hent_tripletex.js` (datauttrekket i `tripletex_run_script`) er nyere (oktober 2026) og må kontrolleres mot ett ekte uttrekk
første gang det brukes på en klient.

### Verifiser selv etter endringer

Fra repo-rota:

```bash
uv run --with openpyxl python .claude/skills/lonnsavstemming/scripts/ledger_fra_rapport.py "<godkjent rapport>.xlsx" <scratch>/ledger.json
uv run --with openpyxl --with pillow python .claude/skills/lonnsavstemming/scripts/lonnsavstemming_a07.py <scratch>/a07.xml <scratch>/ledger.json <scratch>/ny.xlsx
uv run --with openpyxl python .claude/skills/lonnsavstemming/scripts/sammenlign.py "<godkjent rapport>.xlsx" <scratch>/ny.xlsx
```

Regnskapssiden hentes ut av en rapport du allerede har godkjent, generatoren
kjøres på nytt, og resultatet sammenlignes ark for ark. Endrer du kontrollogikken,
kjør dette på minst to klienter før du bruker den på noe nytt.

Formelceller i den nye filen har ingen bufret verdi før Excel har vært innom, så
avvikskolonnene ser tomme ut i sammenligningen. Det er normalt.

### Det som fortsatt avhenger av riktig oppsett

**`ytelse_konto` må stemme.** Tellingen «Ytelser per ansatt» er antall
kombinasjoner av person × måned × konto i bruk. Mapper to ytelser til hver sin
konto der klienten bruker samme, blir tallet for høyt – og motsatt. Fri telefon
er det vanlige tilfellet: naturalytelse føres på 5210, utgiftsgodtgjørelse på
5390. Les `fordel` i A07 og sett `ytelse_konto` deretter.

Går fordelingen ikke opp, står det «Koblingsproblemer» i kolonnen Regnskap på
arket «Per ansatt». Det betyr nesten alltid feil `ytelse_konto`, eller at et
tillegg er ført utenfor lønnsbilaget.

**`pensjon_historikk` må dekke hele året.** Uten den regnes AGA per måned uten
pensjonsgrunnlag, og ytelser uten opptjeningsperiode havner i feil måned.

---

## Arkene i Excel-fila

Filnavn: `Lønnsavstemming <Klient> termin <n> <år>.xlsx`.

| Ark | Innhold |
|---|---|
| Avstemming | rent sammendrag: post · A07/beregnet · regnskap · avvik · status, i tre blokker (forskuddstrekk, AGA, feriepenger) + antall avvik |
| Detaljer | kilde, bilag og merknad per kontroll, innsendingshistorikk, reverserte bilag, merknader |
| Forskuddstrekk | trekk per lønnsdato og for terminen, innbetalt, saldokontroll, 1950 |
| Arbeidsgiveravgift | Sticos pkt. 1–5 + pensjon hittil i år + bevegelse 2770 |
| Per ansatt | ytelser, AGA og trekk per person mot lønnsbilagslinjene |
| Ytelser A07 | ytelsene fra A07 per person og måned |
| Posteringer | posteringene fra ledger.json |

---

## ledger.json

Regnskapssiden. Hentes fra Tripletex og lagres som JSON. Et utfylt eksempel ligger
i `scripts/ledger_eksempel.json`.

| Felt | Forklaring |
|---|---|
| `selskap`, `orgnr`, `tripletex_id` | vises i overskriften og under Kilder |
| `periode` | `{termin, forfall}` – forfall er 15. i måneden etter terminslutt |
| `aga_sats` | f.eks. `14.1`. Faller tilbake til satsen i A07 |
| `feriepenger_sats` | `0.12`, `0.125` eller `0.143` – leses av 5020/5000 i et lønnsbilag |
| `konto` | `{"pensjon": 5945}` – autodetekteres blant 5945/5950/5946/5940 |
| `ytelse_konto` | overstyrer kontomapping per ytelse, bare der klienten avviker fra standard, f.eks. `{"elektroniskKommunikasjon": 5390}` når EK er utgiftsgodtgjørelse |
| `balanser` | `[{a: konto, n: navn, ib, ch, ub}]` |
| `posteringer` | `[[dato, bilag, konto, kontonavn, tekst, beløp]]` |
| `pensjon_historikk` | `[["YYYY-MM", tekst 594x, bokført beløp, tekst pensjonsbilag, innrapportert grunnlag]]` for hele året; grunnlag = AGA i pensjonsbilaget / sats |
| `forklart` | prefikser på kontrollrader som skal vise FORKLART i stedet for AVVIK – bare når merknaden forklarer avviket fullt ut |
| `merknader` | fritekst til Excel, kan være utfyllende |
| `merknader_kort` | én setning per punkt med beløp, bilag og tiltak (til PDF) |
| `trekkmodell`, `trekkmodell_1950` | kommentartekst på de to trekkradene |

**Pensjonshistorikken er ikke valgfri.** Uten den kan ytelser uten
opptjeningsperiode havne i feil måned – se «Fordeling av ytelser uten periode».

KID for AGA og trekk leses fra A07 (`kidForArbeidsgiveravgift`, `kidForForskuddstrekk`), ikke fra ledger.json.

---

## Klassifisering av bilag

| Type | Kjennetegn |
|---|---|
| Betaling | teksten starter med `Betaling:` |
| Avrundingsbilag | teksten inneholder `A-melding lønn` (f.eks. «A-melding lønn <mnd>»: ører på 2770/2600 mot 7740) |
| Lønnsbilag | teksten inneholder `Lønnsbilag` («Lønnsbilag N-ÅÅÅÅ»), og er verken betaling eller avrunding |
| Feriepengebilag | lønnsbilag uten lønnslinjer (5000–5099 utenom 5020) og med 2940-debet |
| Reversert | teksten matcher `Reversering av bilag N` – reverseringen og originalen nettes til null, holdes utenfor alle kontroller og listes i egen tabell |

Skillet mellom feriepengebilag og ordinære lønnsbilag er avgjørende: 2785-debet på
et feriepengebilag er frigjort AGA, mens 2785-debet i en ordinær kjøring er noe
annet. Det samme gjelder 2940.

## A07: gjeldende innsendinger

`parse_a07()` leser innsendinger per måned (status, `erstatterMeldingsId`, levert, AGA, trekk per lønnsdato, KID),
AGA-grunnlag (lønn, pensjon, fradrag, sats, sone), inntektsmottakere med ytelser per opptjeningsperiode og trekk, og
betalingsinformasjon.

En melding er **erstattet** hvis en annen melding oppgir den i `erstatterMeldingsId`.
Alt annet er gjeldende, og gjeldende meldinger **summeres** (erstatninger erstatter, tillegg summeres).

Statusfeltet avgjør ikke. En melding med `MAA_KONTROLLERES` som ingen har erstattet
er gjeldende og teller med. Dette er verifisert mot den sammensatte terminen, der
juli har tre innsendinger (tlx-61 erstattet av tlx-64, pluss tlx-65) og de to
gjeldende summerer til 35 944 i AGA og 66 404 i trekk – som i fasit.

Sjekk før regnskapssiden hentes:

- flere innsendinger samme måned = korrigeringer eller tillegg; forløpet skal forklares
- negative trekkbeløp = tilbakebetaling av lønn
- personer uten ansattnummer eller opptjeningsperiode = typisk feriepenger til sluttede
- `fradragIGrunnlagetForSone` = refusjon fra NAV, reduserer AGA-grunnlaget

## Fordeling av ytelser uten periode

Feriepenger til sluttede har ingen opptjeningsperiode. De plasseres i den måneden
der grunnlaget mangler omtrent dette beløpet:

```
mangler(måned) = innrapportert AGA(måned) / sats − ytelser(måned) − pensjon(måned)
velg måneden der |mangler − ytelsen| er minst
```

Pensjonsgrunnlaget må være med. Uten det traff heuristikken feil måned på den
sammensatte terminen og flyttet 11 338,80 fra august til juli, med 1 598,66 i
feil på AGA for begge månedene.

## Personkobling

Tripletex fører ikke ansatt på posteringslinjene – teksten er bare «Lønnsbilag
N-ÅÅÅÅ». Koblingen skjer derfor ved **beløpsmatching** (`kobling.py`): for hver
måned og konto har vi ett mål per person fra A07 (Σ ytelser med samme konto) og en
liste med linjer fra regnskapet, og linjene fordeles ved backtracking slik at hver
persons sum treffer målet innenfor toleransen. Én person kan ha flere linjer på samme konto.

- Ytelser: lønnsbilagslinjer per måned og konto mot A07 per person (±0,02).
- AGA per person: 2770-kreditter i lønnsbilag mot Σ AGA-pliktig × sats (±0,06).
- Trekk per person: 2600-linjene for hele terminen mot A07 (±1 kr). A07 gir trekk per person for hele terminen;
  fordelingen per måned kommer fra 2600-linjene.

## Kontrollene på «Avstemming»

**Forskuddstrekk (2600)**

- Per lønnsdato: A07 `sumForskuddstrekkPerLoennsutbetalingsdato` (gjeldende) = −Σ 2600 i lønnsbilag samme dato (±1 kr)
- Termin: A07 Σ per person = −Σ 2600 lønnsbilag − avrundingsbilag
- Innbetalt: Σ 2600-debet «Betaling: Lønnsbilag». Avvik mot a-meldt = for mye (−) eller for lite (+) innbetalt
- Saldokontroll: `−IB + a-meldt − innbetalt − andre føringer` mot `−UB`. Vises som residual mot 0 (UB − IB − innbetalt + a-meldt = 0)
- Direkte-modell (Tripletex «Betaling: Lønnsbilag» 2600/1920 på lønnsdato): 2600 = 0, 1950 ubrukt
- Skattetrekkskonto-modell: UB 1950 skal være ≥ skyldig 2600
- Negativt trekk = tilbakebetaling. Betalt trekk + reversering gir 2600-debet = tilgodehavende → motregn den 15. eller krev tilbake

**Arbeidsgiveravgift – grunnlag (pkt. 2)**

- A07 grunnlag lønn = Σ ytelser med `utloeserArbeidsgiveravgift=true`, avrundet ned per måned
- Regnskap: bevegelse 5000–5399 (utenom 5020 og 5290) + 5500–5599 + utbetalte feriepenger (2940-debet på feriepengebilag)
  + pensjonskontoen − NAV-refusjon (58xx)
- Grunnlag pensjon: bevegelse på pensjonskontoen, mot A07 `tilskuddOgPremieTilPensjon`
- Mapping: fastloenn/timeloenn/overtid/uregelmessige tillegg → 5000, bonus → 5001, sykepenger → 5030, feriepenger → 2940 debet,
  bil → 5200, elektroniskKommunikasjon → 5210 eller 5390, annet → 5260, reiseKost og trekkpliktig km → 5510;
  avgiftsfri km/passasjer/kost med overnatting → 7100/7150 (utenfor grunnlaget)
- EK: naturalytelse (5210 + motkonto 5290) eller utgiftsgodtgjørelse (5390, kontant) – les `fordel`
- Differanse forklares med: (1) pensjon periodisering = innrapportert (pensjonsbilag / sats) − 594x i perioden; hittil i år skal være 0;
  (2) konti med bevegelse uten lønnsbilag («NEI – kontroller», typisk 5320) = mulig ikke-innrapportert fordel; (3) avrunding under 1 kr per måned

**Arbeidsgiveravgift (pkt. 1, 3 og 4)**

- Beregnet = (lønn + pensjon − refusjon) × sats
- Per måned: `ROUNDDOWN((INT(grunnlag) + pensjon) × sats, 0)` – Tripletex runder ned til hele kroner per måned; 0–1 kr avvik er normalt.
  Avrundingsbilaget «A-melding lønn» kan være reversert og kjørt på nytt
- Innrapportert = Σ gjeldende innsendinger per måned (0–1 kr per måned under beregnet)
- Kostnadsført: 5400 + AGA av utbetalte feriepenger (2780/2785-debet på feriepengebilag) ≈ beregnet (øre)
- Kreditert 2770: lønnsbilag + pensjonsbilag − avrundingsbilag, utenom betalinger = innrapportert nøyaktig
- UB 2770 skal være lik innrapportert termin; rest er gammel saldo. 2770 IB ≠ forrige termins a-meldte AGA → forklar restsaldoen
- AGA av utbetalte feriepenger går 2785/2780 → 2770, ikke via 5400
- Betaling den 15. i måneden etter terminen, KID `kidForArbeidsgiveravgift`

**Feriepenger**

- Linjerekkefølgen per konto i et lønnsbilag er samme ansatt (5000 ↔ 5020 ↔ 5401), men 2600 mangler linje når trekket er 0 → beløpsmatching
- 5020 = sats × 5000
- 5401 = AGA-sats × 5020
- Avsetning 2940 = −Σ 2940-linjer i lønnsbilag utenom feriepengebilagene (Σ 5020 = −Σ 2940-kredit; negative kjøringer nettes inn
  og gir negative 5020/5401, ikke utbetaling)
- Utbetalte feriepenger = 2940-debet på feriepengebilag = A07 `feriepenger`

**NAV-refusjon**

Sykepenger og foreldrepenger som NAV refunderer, rapporteres som `fradragIGrunnlagetForSone` – ofte i en egen
tilleggsmelding med negativ AGA. I regnskapet: 2770-debet / 5400-kredit (AGA) og 58xx/5000-kredit (grunnlag).

## Typiske funn

| Funn | Tiltak |
|---|---|
| 2600 debet = negativt trekk i A07 | motregn den 15. eller krev tilbake |
| Flere innsendinger samme måned | bruk de gjeldende (erstatninger erstatter, tillegg summeres) og forklar forløpet |
| Pensjon: avvik i perioden, men 0 hittil i år | FORKLART (periodisering) |
| Pensjon: avvik hittil i år ≠ 0 | korriger i neste a-melding; AGA-effekt = differanse × sats |
| UB 2770 ≠ innrapportert | rydd restsaldoen (gammel termin) |
| 53xx uten lønnsbilag | avklar skatteplikt (mulig ikke-innrapportert fordel) |
| Person uten ansattnummer eller periode | feriepenger til sluttet (2940-debet) |

Sticos «for året» kan mangle terminer – saldobalansen i Tripletex er fasit hittil i år.
`get_balance_sheet` utelater 2600 når IB, bevegelse og UB er 0 – bruk posteringene.

## Kjøring

```bash
uv run --with openpyxl --with pillow python .claude/skills/lonnsavstemming/scripts/lonnsavstemming_a07.py <scratch>/a07.xml <scratch>/ledger.json "<scratch>/Lønnsavstemming <Klient> termin <n> <år>.xlsx"
```

Krever `openpyxl` og `pillow`. Farger, statusregler og logo kommer fra `silfer-rapport` (`from silfer.stil import …`;
logoen er `.claude/skills/silfer-rapport/assets/silfer_logo.png`), så hele repoet må være klonet. LibreOffice finnes
ikke på maskinene: formlene beregnes først når filen åpnes i Excel. Celletekst skal aldri starte med `=`.
