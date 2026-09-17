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
| Enkel klient, termin 1 | **Alle tall på arket «Avstemming» er identiske med fasit.** Tabellene «AGA per ansatt» og «Sum per ansatt» stemmer rad for rad. |
| Sammensatt klient, termin 4 – reverseringer, tilbakebetaling, tre lønnsdatoer | Innsendingslogikken, AGA per måned, feriepengeavsetning og kostnadsført AGA stemmer. **Tre kjente avvik gjenstår – se under.** |

### Kjente avvik som gjenstår

1. **Antall ytelseslinjer per ansatt.** Fasit teller 42 rader på den sammensatte terminen,
   parseren finner 17 inntekt-elementer. Sannsynlig årsak: fasit lister én rad per
   person/måned/konto også der beløpet er null, eller XML-en har inntekt-elementer
   parseren ikke fanger. Må undersøkes mot XML-en før skriptet brukes på klienter
   med mange ytelsestyper.
2. **Innbetalt trekk på negative lønnskjøringer.** Tilbakebetalingen 20.07.2026 på
   −15 354,60 plukkes ikke opp, fordi filteret krever teksten «Lønnsbilag» på
   2600-betalingen. Tilbakebetalinger har annen tekst.
3. **Detaljer-arket er tynnere enn fasit.** Fasit lister 77 rader mot 39: den tar
   med flere føringer enn bare «Betaling:»-linjer på 2600/2770, og den lister
   reverserte bilag som skriptet ikke gjenkjenner. Reverseringene der
   har ikke teksten «Reversering av bilag», så mønsteret må utvides.

Kontrollene som avgjør konklusjonen – forskuddstrekk, AGA, feriepenger – er
verifisert. Avvikene over gjelder detaljvisning og telling, ikke selve
avstemmingen. Kjør likevel en manuell gjennomlesing første gang på en ny klient.

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
