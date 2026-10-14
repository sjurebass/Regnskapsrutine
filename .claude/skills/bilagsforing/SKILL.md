---
name: "bilagsforing"
description: "Bilagsføring i Tripletex: fører alle dokumenter i bilagsmottaket som har motpost i en åpen bankpost i perioden (eller i en vedlagt kontoutskrift). Hvert dokument hentes fra mottaket, leses, føres som nytt avansert bilag, og dokumentet lastes opp som vedlegg på bilaget. EHF og fakturaer som skal betales hoppes over. Lukker Tally-oppgaven «Bilagsbehandling». Bruk ved «bilagsføring på <klient>», «før bilagene i mottaket», «før bilag mot bank», «bokfør bilagsmottaket», «hva ligger i bilagsmottaket», «før kvitteringene»."
---

# Bilagsføring

Fører dokumentene i bilagsmottaket som har motpost i en åpen bankpost, som nye avanserte bilag med dokumentet som vedlegg.
Åpne bankposter uten dokument følges opp i `bankavstemming`; kontroll av det som allerede er bokført gjøres i `bilagskontroll`.

## Når

- Tally-oppgaven «Bilagsbehandling», fra den 5. og før `bankavstemming` den 15. Brukeren oppgir klient og periode; uten periode gjelder forrige måned.
- **Hva «bilagsføring» betyr** når brukeren ber om det for en klient og en periode:
  1. **Hvilke dokumenter:** alle dokumenter i bilagsmottaket med motpost i en **åpen (umatchet) bankpost i bankavstemmingen** for perioden,
     eller i en linje i **kontoutskriften brukeren har lagt ved** (kontoer uten bankfeed).
  2. **Hopp over:** EHF og fakturaer som skal betales (ingen bankpost ennå). Dem tar brukeren selv. De blir liggende i mottaket.
  3. **For hvert dokument, hver gang:** hent det fra bilagsmottaket → les det → lag et **nytt avansert bilag** i Tripletex → **last opp
     dokumentet som vedlegg** på det avanserte bilaget. Deretter matches bankposten, og kopien i mottaket slettes bare når vedlegget er bekreftet.
- Gjør bare dette (instruksen i Tally hører med, se steg 1). Ikke kjør andre skills eller ekstra kontroller underveis. Er en post uklar, spør i forslagstabellen.

## Kundeinstruks

Les **hele** kundeinstruksen i Tally hver gang, før noe foreslås. Den er ofte fritekst utenfor malen, så se etter alt som gjelder føring:
kontoer (bank, faste leverandører, manglende bilag), mva, valuta, betalingsløsninger, hva som ikke skal føres før kunden sier fra, hvem kunden
er i mottaket, og «Kjente avvik». Instruksen går foran historikk og standardregler, men gir aldri lov til å føre uten ja.

## Steg

### 1. Hent (bare lesing)

1. **Instruks fra Tally** (samtidig med punkt 2): `list_clients` (`search` = klienten) → `client_id` → `hent_instrukser` med `client_id`.
   Viser svaret en egen instruks for regnskapstjenesten, hent den også (`service_id`). Har klienten en åpen «Bilagsbehandling»
   (`list_tasks`, `client` og `title`), hent `hent_instrukser` med `task_id` også (beskrivelse og sjekkliste).
   Trekk ut «Fra instruksen»: kontoer og regler som gjelder bilagsføringen, maks seks linjer. Ingen instruks: si det i én linje og fortsett.
2. `npm run -s bilag -- hent --client "<klient>" --til ÅÅÅÅ-MM [--fra ÅÅÅÅ-MM] --ut <mappe>` (`<mappe>` = kort arbeidsmappe, for eksempel
   `%TEMP%\rr\bilag-ÅÅÅÅ-MM`). Utskriften gir antall i mottaket (EHF hoppet over), umatchede bankposter, beløpstreff, skann og kontoer uten bankfeed:
   - `forslag.json`: per dokument `inbox` (id i mottaket), dato, fakturanr., beløp funnet i teksten og opptil fire bankposter med samme beløp.
   - `bank.json`: åpne bankposter i perioden med id, konto, dato, beløp og maskert tekst.
   - `historikk.tsv`: hvordan leverandører og tekster er ført de siste 12 månedene (lev-id, konto, mva-kode, antall, siste bilag).
   - `leverandorer.tsv`: id, navn og org.nr. Mange finnes under et annet navn. Nye opprettes ikke uten ja.
   - `docs/<id>.pdf` og maskert `docs/<id>.txt`. Skann (`"skann": true`) og bilder leses med Read.

### 2. Les, match og foreslå

1. **Les** hvert dokument én gang (tekst; skann og bilder med Read).
2. **Motpost:** åpen bankpost i `bank.json` med samme beløp, nærmest i dato. Valuta: beløp × kurs ± 3 %. Ellers en linje i den vedlagte kontoutskriften.
   Kort trekkes ofte 1–3 dager etter kjøpet.
3. **Uten motpost** (blir liggende): EHF, forfall frem i tid, forhåndsvisning, proforma, dublett av bokført bilag (samme leverandør, beløp, fakturanr.).
4. **Konto og mva:** «Fra instruksen» først, deretter forrige føring av samme leverandør (`historikk.tsv`), deretter standardreglene under.
   Er historikken i strid med instruksen: følg instruksen og si det. Usikker: spør, ikke gjett.

| # | Dato | Leverandør | Beløp | Konto | Mva | Bank | Grunnlag |
|---|---|---|---|---|---|---|---|
| 1 | 03.09 | Vercel | USD 36,24 = kr 347,08 | 6552 | 86 | 1920 03.09 | som bilag 414-2026 |
| 2 | 05.09 | Rema 1000 | kr 412,50 | 5990 | 0 | 1920 06.09 | instruks: personalmat på 5990 |

Under tabellen: dokumentene som blir liggende (én linje hver med grunn) og nummererte spørsmål. Foreslå svarformat: «ja, 2 = 5990, 4 vent».

| Tilfelle (når kundeinstruks og historikk ikke sier noe) | Føring |
|---|---|
| Leverandørfaktura betalt fra bank | Kostnad / 2400 på fakturadato og 2400 / bank på bankdato i samme bilag. 2400-postene lukkes. |
| Utenlandsk tjeneste (SaaS) | Mva-kode 86. Ikke mva-registrert klient: 0. Leverandør som tar norsk mva (VOEC): ikke 86. |
| Valuta | Linjene i fakturavaluta med Norges Bank-kurs på fakturadato, betaling med bankbeløpet, differansen til 8060 (agio) / 8160 (disagio). |
| Fysisk kvittering (butikk, kantine) | Kostnad direkte mot bank, uten leverandør. |
| Mat til ansatte, kaffe, lunsj | 5910/5990, mva 0 (ikke fradrag, § 8-3). Gaver: 7791 uten mva. |
| Gebyr, renter, purregebyr · inkasso | 7770 / 8150, mva 0 · inkasso: hovedstol mot 2400, renter og gebyr 8150, øreavrunding 7740. |
| Bank- eller korttrekk uten bilag | Konto for manglende bilag fra kundeinstruksen (typisk 1370 eller 7799). Kommer kvitteringen etter at måneden er lukket: før kostnad mot den kontoen, ikke reverser. |
| Utstyr under 30 000 kr per enhet | Kostnadsføres. |
| Kvittering og faktura for samme kjøp | Ett bilag; begge dokumentene lastes opp som vedlegg (`flere` i planen). |

### 3. Før (etter ett samlet ja)

1. Skriv `<mappe>/plan.json` (Write, UTF-8), én rad per dokument fra svaret på forslagstabellen; `docs/` fra steg 1 må ligge i samme mappe.
   Felt: `inbox` (fra `forslag.json`) · `dato` (faktura- eller kjøpsdato) · `beskrivelse` · `bankkonto` og `belop` (bankbeløpet med fortegn, ut =
   negativt) · `bankTx` (id fra `bank.json`; utelates ved kontoutskrift uten bankfeed) · valgfritt `leverandor` (id fra `leverandorer.tsv`: kostnad /
   2400 og 2400 / bank i samme bilag) · `fakturanr` · `valuta` (linjene i fakturavaluta, kurs fra Tripletex på datoen, differansen til 8060/8160)
   · `flere` (flere mottaks-id-er på samme bilag) · `linjer: [{konto, belop, mva}]` (brutto, sum = −`belop` i NOK; `mva` er Tripletex-koden, 0 = ingen).
   ```json
   [{ "inbox": 123, "dato": "2026-09-03", "beskrivelse": "Vercel – faktura 1234", "bankkonto": 1920, "belop": -347.08, "bankTx": 456,
      "fakturanr": "1234", "linjer": [{ "konto": 6552, "belop": 347.08, "mva": 86 }] }]
   ```
2. Tørrkjøring: `npm run -s bilag -- før --client "<klient>" --plan <mappe>/plan.json` sjekker kontoer, mva-koder og sum; ingenting føres. Be om ett samlet ja.

**Skriving (etter ja):** `npm run -s bilag -- før --client "<klient>" --plan <mappe>/plan.json --bekreft` gjør per dokument, i denne rekkefølgen:
1. Nytt avansert bilag med dato, beskrivelse og linjene fra planen. Med leverandør: leverandøren på alle linjene.
2. Dokumentet lastes opp som vedlegg på det avanserte bilaget, og vedlegget bekreftes.
3. 2400-postene for leverandøren lukkes (sum 0).
4. Bankposten matches i bankavstemmingen (går også når posteringen ligger i forrige måned). Motpost i kontoutskrift: ingen match.
5. Kopien i bilagsmottaket slettes **bare** når vedlegget er bekreftet på det førte bilaget.

Mange dokumenter: før det første med `--bare <inbox>`, sjekk `<mappe>/plan.resultat.json`, ta resten etterpå. Feilet steg kan kjøres på nytt.

**Bare i Tripletex-UI:**
1. Match bankposten manuelt når resultatet sier «ingen bankavstemming for måneden».

## Svar

- Først «Fra instruksen» (maks seks linjer, eller «ingen kundeinstruks i Tally»), så forslagstabellen. Ingenting føres før svar og godkjent tørrkjøring.
- Svar som gjelder klienten varig (fast konto for en leverandør, en ny regel), tilbys lagret i kundeinstruksen (`kundeinstruks`, etter ja).
- Til slutt én tabell: dokument · bilagsnummer · vedlegg · matchet · slettet fra mottaket, og hva som blir liggende med grunn. UI-punkter: «ikke gjort».

## Lever

Fullfør i Tally: se `tally-gjoremal`. «Bilagsbehandling» fullføres når alle dokumenter med bankmotpost i perioden er ført, matchet og ryddet fra mottaket. Kommentaren inneholder periode, antall førte bilag og hva som ligger igjen (EHF, ubetalte, uten motpost).
Arbeidsmappa med nedlastede dokumenter og `plan.json` slettes når jobben er ferdig.

## Fallgruver

- Endre bilaget i mottaket gir 422, også beskrivelsen. Derfor lages alltid et nytt avansert bilag.
- Vedlegg fra mottaket følger ikke med når bilaget lages. Dokumentet må lastes opp på nytt på det nye bilaget (`bilag før` gjør det).
- Har én linje leverandør, må alle linjene ha den. Ellers gir Tripletex 422.
- `bilag før` stopper for et dokument som ikke lenger ligger i mottaket, eller når linjene ikke summerer til bankbeløpet. Feilen står i `plan.resultat.json`.
- Lukket bankavstemming eller lukket år: ikke match, ikke før. Si fra, ikke tving det.
- Før aldri ut fra hva en bankpost «ser ut til» å være. Bankpost uten dokument hører til `bankavstemming` (fra kunden).

## Referanser

- `docs/kontrollkatalog.md`: R6 (dublett før føring), D6 (ubehandlet bilagsmottak). `docs/fradragsregler-kort.md` når mva-behandlingen er uklar.
- Naboskills: `bankavstemming`, `bilagskontroll`, `kundeinstruks`, `leverandorindeks` (når brukeren ber om vurdering av en ukjent leverandør).
