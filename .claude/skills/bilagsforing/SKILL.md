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
- Gjør bare dette. Ikke kjør andre skills, Tally-oppgaver eller ekstra kontroller underveis. Er en post uklar, spør i forslagstabellen.

## Kundeinstruks

«Bilagsføringsregler» (går foran alt annet), «Bank» (kontoer uten bankfeed), «Mva» (registrert, kode for utenlandske tjenester),
«Mangelliste» (konto for manglende bilag) og «Kjente avvik».

## Steg

### 1. Hent (bare lesing)

1. `hent_instrukser` (seksjonene over) og `get_voucher_inbox_count` for klienten.
2. ToolSearch etter `list_voucher_inbox`, `read_voucher_document`, `register_supplier_invoice` og `post_supplier_invoice` i denne økten.
   Leseverktøyene brukes når de finnes. Skriveverktøyene lager leverandørfaktura, ikke avansert bilag; bruk dem bare når brukeren sier det.
3. Åpne bankposter: `get_unmatched_bank_transactions` per konto og måned i perioden (som i `bankavstemming`). Behold id, konto, dato, beløp og tekst.
   Konto uten bankfeed: motposten er kontoutskriften brukeren har lagt ved.
4. Dokumentene: `list_voucher_inbox` / `read_voucher_document`, ellers `get_voucher_document` (lenke). Brukeren åpner lenken, eller du leser
   filen med Read når den er lastet ned. EHF hoppes over.
5. Historikk: `search_ledger_postings` filtrert på leverandøren, 12 måneder bakover (konto, mva-kode, beskrivelse, valuta, siste bilag).
6. Leverandører: `search_suppliers` på navn og org.nr. Mange finnes under et annet navn. Nye opprettes ikke uten ja.

### 2. Les, match og foreslå

1. **Les** hvert dokument én gang (tekst; skann og bilder med Read).
2. **Motpost:** åpen bankpost med samme beløp, nærmest i dato. Valuta: beløp × kurs ± 3 %. Ellers en linje i den vedlagte kontoutskriften.
   Kort trekkes ofte 1–3 dager etter kjøpet.
3. **Uten motpost** (blir liggende): EHF, faktura med forfall frem i tid, forhåndsvisning, «upcoming», proforma, og dublett av et bokført bilag
   (samme leverandør, beløp og fakturanr.).
4. **Konto og mva:** kundeinstruksen, deretter forrige føring av samme leverandør, deretter standardreglene under. Usikker: spør, ikke gjett.

| # | Dato | Leverandør | Beløp | Konto | Mva | Bank | Grunnlag |
|---|---|---|---|---|---|---|---|
| 1 | 03.09 | Vercel | USD 36,24 = kr 347,08 | 6552 | 86 | 1920 03.09 | som bilag 414-2026 |

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
| Kvittering og faktura for samme kjøp | Ett bilag; begge dokumentene lastes opp som vedlegg. |

### 3. Før (etter ett samlet ja)

**Krever skriving utenfor MCP: Tripletex-UI (eller API-kobling):** per dokument, i denne rekkefølgen:
1. Hent dokumentet fra bilagsmottaket.
2. Lag et nytt avansert bilag med dato, beskrivelse og linjene fra forslaget. Med leverandør: kostnad / 2400 og 2400 / bank, leverandøren på alle linjene.
3. Last opp dokumentet som vedlegg på det avanserte bilaget, og bekreft at vedlegget ligger der.
4. Lukk 2400-postene for leverandøren (sum 0).
5. Match bankposten i bankavstemmingen (manuell match; går også når posteringen ligger i forrige måned). Motpost i kontoutskrift: ingen match.
6. Slett kopien i bilagsmottaket **bare** når vedlegget er bekreftet på det førte bilaget. Er du i tvil, la kopien ligge og si det.

Er det mange dokumenter: før det første, les det tilbake, og ta resten etterpå. Et steg som feiler, kan gjøres på nytt; ferdige steg hoppes over.

## Svar

- Først forslagstabellen med det som blir liggende og spørsmålene. Ingenting føres før brukeren har svart.
- Til slutt én tabell: dokument · bilagsnummer · vedlegg bekreftet · matchet · slettet fra mottaket, og hva som blir liggende med grunn.
- Det som står igjen i UI-lista, sies som «ikke gjort».

## Lever

Fullfør i Tally: se `tally-gjoremal`. «Bilagsbehandling» fullføres når alle dokumenter med bankmotpost i perioden er ført, matchet og ryddet fra mottaket. Kommentaren inneholder periode, antall førte bilag og hva som ligger igjen (EHF, ubetalte, uten motpost).
Nedlastede dokumenter slettes fra scratch når jobben er ferdig.

## Fallgruver

- Endre bilaget i mottaket gir 422, også beskrivelsen. Derfor lages alltid et nytt avansert bilag.
- Vedlegg fra mottaket følger ikke med når bilaget lages. Dokumentet må lastes opp på nytt på det nye bilaget.
- Har én linje leverandør, må alle linjene ha den. Ellers gir Tripletex 422.
- Lukket bankavstemming eller lukket år: ikke match, ikke før. Si fra, ikke tving det.
- Før aldri ut fra hva en bankpost «ser ut til» å være. Bankpost uten dokument hører til `bankavstemming` (fra kunden).

## Referanser

- `docs/kontrollkatalog.md`: R6 (dublett før føring), D6 (ubehandlet bilagsmottak). `docs/fradragsregler-kort.md` når mva-behandlingen er uklar.
- Naboskills: `bankavstemming`, `bilagskontroll`, `kundeinstruks`, `leverandorindeks` (når brukeren ber om vurdering av en ukjent leverandør).
