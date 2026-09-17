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

### Verifiser selv etter endringer

```bash
python scripts/ledger_fra_rapport.py "<godkjent rapport>.xlsx" ledger.json
python scripts/lonnsavstemming_a07.py a07.xml ledger.json ny.xlsx
python scripts/sammenlign.py "<godkjent rapport>.xlsx" ny.xlsx
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
| `ytelse_konto` | overstyrer kontomapping per ytelse, f.eks. `{"elektroniskKommunikasjon": 5390}` når EK er utgiftsgodtgjørelse |
| `balanser` | `[{a: konto, n: navn, ib, ch, ub}]` |
| `posteringer` | `[[dato, bilag, konto, kontonavn, tekst, beløp]]` |
| `pensjon_historikk` | `[["YYYY-MM", tekst, bokført 594x, tekst, innrapportert grunnlag]]` for hele året |
| `forklart` | prefikser på kontrollrader som skal vise FORKLART i stedet for AVVIK |
| `merknader` | fritekst til Excel |
| `merknader_kort` | én setning per punkt til PDF |
| `trekkmodell`, `trekkmodell_1950` | kommentartekst på de to trekkradene |

**Pensjonshistorikken er ikke valgfri.** Uten den kan ytelser uten
opptjeningsperiode havne i feil måned – se «Fordeling av ytelser uten periode».

---

## Klassifisering av bilag

| Type | Kjennetegn |
|---|---|
| Betaling | teksten starter med `Betaling:` |
| Avrundingsbilag | teksten inneholder `A-melding lønn` (ører på 2770/2600 mot 7740) |
| Lønnsbilag | teksten inneholder `Lønnsbilag`, og er verken betaling eller avrunding |
| Feriepengebilag | lønnsbilag uten lønnslinjer (5000–5099 utenom 5020) og med 2940-debet |
| Reversert | teksten matcher `Reversering av bilag N` – både reverseringen og originalen holdes utenfor |

Skillet mellom feriepengebilag og ordinære lønnsbilag er avgjørende: 2785-debet på
et feriepengebilag er frigjort AGA, mens 2785-debet i en ordinær kjøring er noe
annet. Det samme gjelder 2940.

## Gjeldende innsendinger

En melding er **erstattet** hvis en annen melding oppgir den i `erstatterMeldingsId`.
Alt annet er gjeldende, og gjeldende meldinger **summeres**.

Statusfeltet avgjør ikke. En melding med `MAA_KONTROLLERES` som ingen har erstattet
er gjeldende og teller med. Dette er verifisert mot den sammensatte terminen, der
juli har tre innsendinger (tlx-61 erstattet av tlx-64, pluss tlx-65) og de to
gjeldende summerer til 35 944 i AGA og 66 404 i trekk – som i fasit.

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
måned og konto har vi ett mål per person fra A07 og en liste med linjer fra
regnskapet, og linjene fordeles slik at hver persons sum treffer målet innenfor
toleransen. Én person kan ha flere linjer på samme konto.

Toleranser: ytelser ±0,02 · AGA ±0,06 · trekk ±1 kr.

## Kontrollene på «Avstemming»

**Forskuddstrekk (2600)**

- Per lønnsdato: A07 `sumForskuddstrekkPerLoennsutbetalingsdato` = −Σ 2600 i lønnsbilag samme dato
- Termin: A07 Σ per person = −Σ 2600 lønnsbilag − avrundingsbilag
- Innbetalt: Σ 2600-debet «Betaling: Lønnsbilag»
- Saldokontroll: `−IB + a-meldt − innbetalt − andre føringer` mot `−UB`. Vises som residual mot 0
- 1950: UB skal være ≥ skyldig 2600

**Arbeidsgiveravgift**

- Grunnlag lønn: bevegelse 5000–5399 (utenom 5020 og 5290) + 5500–5599 + utbetalte feriepenger
- Grunnlag pensjon: bevegelse på pensjonskontoen, mot A07 `tilskuddOgPremieTilPensjon`
- Per måned: `ROUNDDOWN((INT(grunnlag) + pensjon) × sats, 0)` – Tripletex runder ned per måned, 0–1 kr avvik er normalt
- Kostnadsført: 5400 + frigjort AGA fra feriepengebilag
- Kreditert 2770: alle 2770-poster utenom betalinger, netto etter avrundingsbilag
- UB 2770 skal være lik innrapportert termin; rest er gammel saldo

**Feriepenger**

- 5020 = sats × 5000
- 5401 = AGA-sats × 5020
- Avsetning 2940 = −Σ 2940-linjer i lønnsbilag utenom feriepengebilagene (negative kjøringer nettes inn)
- Utbetalte feriepenger = 2940-debet på feriepengebilag = A07 `feriepenger`

## Kjøring

```bash
python scripts/lonnsavstemming_a07.py a07.xml ledger.json "Lønnsavstemming <Klient> termin <n> <år>.xlsx"
```

Krever `openpyxl` og `pillow` (logoen). Kjør deretter `recalc` fra xlsx-skillen
for å få formelverdier inn i filen før PDF-en lages.
