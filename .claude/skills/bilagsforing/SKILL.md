---
name: "bilagsforing"
description: "Bilagsføring i Tripletex mot bank: finner dokumenter i bilagsmottaket som har motpost blant umatchede bankposter, foreslår konto, mva og leverandør ut fra tidligere føringer hos klienten, og fører etter ett samlet ja. Lukker Tally-oppgaven «Bilagsbehandling». Bruk ved «bilagsføring på <klient>», «før bilagene i mottaket», «før bilag mot bank», «bokfør bilagsmottaket», «kjør bilagsføring på alle»."
---

# Bilagsføring mot bank

«Bilagsføring på <klient>» betyr: før bare dokumentene i bilagsmottaket som har motpost blant de umatchede bankpostene. Resten blir
liggende til manuell føring eller til kunden har betalt. Bankavstemmingen styrer altså hva som føres.

Skillen lager et forslag per dokument ut fra hvordan samme leverandør er ført tidligere hos klienten, viser alt i én tabell, og fører etter
ett samlet ja. Den lukker Tally-oppgaven «Bilagsbehandling» og står mellom `mangelliste` (det kunden må levere) og `bankavstemming`.

Alt skjer i chatten.

## Faste regler

- Klienten må være navngitt, eller brukeren må nevne klientene. Gjett aldri.
- Les kundeinstruksen først (`hent_instrukser`, se `kundeinstruks`): seksjonene «Bilagsføringsregler», «Bank», «Mva» og «Kjente avvik».
  Klientreglene der går foran standardreglene under.
- **Kopier mønsteret fra forrige føring av samme leverandør hos klienten**: konto, mva-kode, bilagstype, beskrivelse, valuta. Standardreglene
  gjelder bare når det ikke finnes historikk.
- Ingen føring uten ja. Vis forslaget, få ett samlet ja, og før. Test på ett bilag før resten når det er mange.
- **Ikke opprett leverandører** uten ja. Mange finnes allerede under et annet navn; søk på org.nr., e-post og variasjoner først.
- Ubetalte fakturaer (ingen bankpost ennå) blir liggende i mottaket.
- Lukket regnskapsår røres ikke. Ompostér aldri uten at bilaget for akkurat den transaksjonen foreligger.
- «Ikke tilbakefør, korriger»: rett det eksisterende bilaget når det går. Bank- og OCR-bilag kan ikke endres via API-et (422); da lages
  korrigeringsbilag etter ja.
- Kvittering og faktura for samme kjøp legges på samme bilag.
- Forhåndsvisninger, «Upcoming»-fakturaer og proforma føres ikke.
- Ingen personnavn i chatten. Privatpersoner i bankteksten omtales som «privatperson».

## Standardregler (når kundeinstruks og historikk ikke sier noe)

| Tilfelle | Føring |
|---|---|
| Leverandørfaktura betalt fra bank | Bilagstype Leverandørfaktura: kostnad / 2400 på fakturadato, og 2400 / bank på bankdato, i samme bilag. Lukk 2400-postene. |
| Utenlandsk tjeneste (SaaS) | Kostnad med mva-kode 86 (omvendt avgiftsplikt). Ikke-registrert klient: kode 0. Leverandør som tar norsk mva (VOEC) ikke 86. |
| Valuta | Fakturalinje i fakturavaluta med Norges Bank-kurs på fakturadato, betaling med bankbeløpet, differanse til 8060 (agio) / 8160 (disagio). |
| Fysisk kvittering (butikk, kantine) | Rett på kostnadskonto mot bank uten leverandør. |
| Mat til ansatte, kaffe, lunsj | 5910/5990, ingen fradrag for mva (§ 8-3). Gaver 7791 uten mva. |
| Gebyr, renter, purregebyr | Utenfor mva: 7770 / 8150. |
| Inkassobetaling | Hovedstol mot 2400, renter og gebyr 8150, øreavrunding 7740. |
| Bank- eller korttrekk uten bilag | Kontoen for manglende bilag i kundeinstruksen (typisk 1370 eller 7799). Kommer kvitteringen etter at måneden er lukket: før kostnad mot den kontoen, ikke reverser. |
| Utstyr under 30 000 kr per enhet | Kostnadsføres. |

## Spar tokens

- Hent bankposter for flere klienter i ett `tripletex_run_script`-kall.
- Les PDF-ene bare for dokumenter som har en mulig bankmotpost (beløp og dato).
- Ikke les samme dokument to ganger.

## Steg 0 – Sjekk tilkoblingene

Kall Tally `whoami`, Tripletex `search_client_companies` og `get_voucher_inbox_count` for klienten i samme runde. Sjekk med ToolSearch om
Tripletex-MCP-en har `list_voucher_inbox`, `read_voucher_document`, `register_supplier_invoice` og `post_supplier_invoice` i denne økten.
Rapporter på én linje, for eksempel «Tally ✓ · Tripletex ✓ · bilagsmottak: 7 dokumenter · føring via: CLI».

## Steg 1 – Hent bankposter og bilagsmottak

1. Umatchede bankposter for perioden (`get_unmatched_bank_transactions`, se `bankavstemming`). Behold dato, beløp og tekst.
2. Dokumentene i bilagsmottaket:
   - Med `list_voucher_inbox` / `read_voucher_document` når MCP-en har dem.
   - Ellers via CLI (hurtigvei), eller i nettleseren (`tripletex.no/page/incoming/inbox?contextId=<id>`, les teksten).
   - `get_voucher_document` gir en nedlastingslenke til brukeren, ikke innholdet til deg.
3. Åpne poster i reskontro (`search_open_postings`, 1500–1599 og 2400–2499): en bankpost kan høre til en allerede bokført faktura.
   Da skal den betales mot 2400 og lukkes, ikke kostnadsføres på nytt.

## Steg 2 – Match og lag forslag

1. Match dokument mot bankpost på beløp (bankbeløp, eller valutabeløp ± kurs) og dato (kort trekkes ofte dagen etter kjøpet).
2. For hvert treff: finn tidligere føringer av samme leverandør hos klienten med `search_ledger_postings` (filtrer på leverandør og
   et halvt til ett år bakover). Kopier konto, mva-kode og beskrivelse.
3. Finnes ikke leverandøren: søk på org.nr. (`lookup_company_in_brreg`) og navnevarianter. Sjekk leverandørindeksen (`leverandorindeks`) for
   mva-behandling av utenlandske leverandører.
4. Forslagstabell, én linje per dokument:

| Dato | Leverandør | Beløp | Konto | Mva | Mot | Grunnlag | Merknad |
|---|---|---|---|---|---|---|---|
| 03.09 | Vercel | USD 36,24 (kr 347,08) | 6552 | 86 | 2400 → 1920 | som bilag 414 | disagio 8160 |

Under tabellen: dokumenter uten bankmotpost (blir liggende), og spørsmål som må avklares, nummerert.
Foreslå et kompakt svarformat, for eksempel «Svar gjerne: ja, 2 = 5990, 4 vent».

## Steg 3 – Før

**Krever CLI (Sjur) eller Tripletex-UI:** selve føringen, med mindre Tripletex-MCP-en i denne økten har `register_supplier_invoice` og
`post_supplier_invoice` (da føres leverandørfakturaer derfra etter ja, med samme forslag). Har du verken det eller CLI-et, gi brukeren
forslagstabellen som arbeidsliste for Tripletex-UI, og si at ingenting er ført.

Rekkefølgen per bilag (CLI):

1. `POST /ledger/voucher?sendToLedger=true` som avansert bilag. Leverandøren skal også stå på banklinjen; ellers gir Tripletex 422
   (alle linjer på samme rad må ha samme dimensjoner).
2. Last opp PDF-en: `POST /ledger/voucher/{id}/attachment`. Bekreft at vedlegget ligger på bilaget.
3. Match mot bankposten: `POST /bank/reconciliation/match` (MANUAL, transaksjoner og posteringer). Det går også når posteringen ligger i
   forrige måned.
4. Lukk 2400-postene: `PUT /ledger/posting/:closePostings` (samme leverandør, sum 0).
5. Slett kopien i bilagsmottaket (`DELETE /ledger/voucher/<inbox-id>`) **bare** når det førte bilaget har vedlegget og inbox-bilaget er ubokført.
   Dokumentet ligger da på det førte bilaget, så ingenting går tapt. Er du i tvil, la kopien ligge og si det.

Fallgruver:

- `PUT` på et bilag i mottaket gir 422 («ikke mulig å endre dette feltet for denne bilagstypen via API-et»). Lag nytt bilag i stedet.
- `POST /ledger/voucher` med vedlegg fra mottaket ignorerer vedlegget. Last opp på nytt.
- `/voucherInbox/inboxFiltered` og `/incomingInvoice` gir 403 for API-brukeren. `/voucherInbox/sendToArchive` gir 500.
- `sendToLedger` er `true` som standard. Et bilag blir bokført med en gang.
- Beskrivelsen på et bilag i mottaket kan ikke endres etterpå (422). Forklaringer legges som kommentar (`/voucherMessage`).
- Ukjent leverandør når kunden har bedt om det: last opp i mottaket uten beskrivelse (`POST /ledger/voucher/importDocument`, behold filnavnet)
  og legg kommentaren «Fant ikke leverandør».

Etter føring: les bilaget tilbake, sjekk at bankposten er matchet og 2400 lukket, og vis en kort tabell med bilagsnummer.

## Flere klienter

- Én lesende agent per klient. Agenten får klientens kundeinstruks og standardreglene, leser bankposter, mottak og historikk,
  og returnerer forslagstabellen (og med CLI et `book.mjs` som er tørrkjøring uten `--bekreft`). Agenten skriver aldri.
- Hovedagenten viser alle forslagene samlet, tar ett svar med avgjørelser per klient, og fører.
- Kjør CLI-føringer sekvensielt per klient (tokenfornying tåler ikke parallelle kall).

## Hurtigvei – bare Sjur

Finnes `C:\Users\Sjur\Tripletex API`:

```powershell
npm --prefix "C:\Users\Sjur\Tripletex API" run -s bankavstemming -- --til ÅÅÅÅ-MM --client "<klient>" --ut "<scratch>"
npm --prefix "C:\Users\Sjur\Tripletex API" run -s api -- GET "/ledger/voucher/>voucherReception" --client "<klient>"
npm --prefix "C:\Users\Sjur\Tripletex API" run -s api -- GET "/document/<id>/content" --client "<klient>"
```

Sjekk riktig kall med `node tripletex-api/finn.js bilagsmottak` før du skriver nye kall.

## Det du aldri gjør

- Fører uten ja, eller fører dokumenter uten bankmotpost når brukeren ba om bilagsføring mot bank.
- Oppretter leverandører uten ja.
- Sletter fra bilagsmottaket før vedlegget er bekreftet på det førte bilaget.
- Ompostérer ut fra hva en banktransaksjon «ser ut til» å være.
- Endrer bilag i et lukket år eller en levert mva-termin uten å si det først.

## Fullfør i Tally

1. Foreslå tidsbruk (standard 30 minutter for løpende bilagsbehandling) og spør: «Skal jeg fullføre Bilagsbehandling for <klient> og føre <X> minutter?»
2. Ved ja: `add_task_comment` (periode, antall førte bilag, hva som ligger igjen), `log_time`, `complete_task`.
3. Avgjørelser som gjelder klienten fremover (konto, mva-kode, «vent med tilskuddet»), tilbys lagret i kundeinstruksen med `kundeinstruks`.

## Referanser

- `docs/kontrollkatalog.md` (R6, D1–D3, D6, E2)
- `mva-termin/references/fradragsregler-kort.md` – fradragsregler når mva-behandlingen er uklar
- Skillene `bankavstemming`, `leverandorindeks`, `kundeinstruks`
