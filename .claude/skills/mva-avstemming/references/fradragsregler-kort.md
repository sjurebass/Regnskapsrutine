# Fradragsregler – kortversjon for unntakslista

Les bare denne fila. Fullversjonen (`fradragsregler.md`) brukes med grep på paragraf når en sak ikke dekkes her. Satser og grenser gjelder 2026.

## Rekkefølge per bilag
1. Var klienten mva-registrert på fakturadatoen? Hvis nei, er det aldri fradrag (se «Klient ikke registrert»).
2. Er det et gyldig salgsdokument fra en registrert selger, stilet til klienten? Brreg og leverandørindeksen er fasit, ikke «MVA» på fakturaen.
3. Er kjøpet til bruk i den avgiftspliktige virksomheten (§ 8-1)? Eierforhold, aksjer, unntatt eiendomssalg og private kjøp gir ikke fradrag.
4. Er fradraget avskåret etter §§ 8-3 eller 8-4 (tabellen under)?
5. Er bruken delt? Da gis forholdsmessig fradrag (§ 8-2).
6. Stemmer sats, kode og beløp (§ 11-4)? Fradrag gis bare for mva som faktisk er beregnet.
7. Er terminen riktig? Fakturadatoen avgjør (§ 15-9).
8. Er det betalt via bank når beløpet er 10 000 kr eller mer (§ 8-8)?

## Satser
- 25 %: alminnelig sats.
- 15 %: næringsmidler, vann og avløp.
- 12 %: persontransport, hotellrom, møterom på hotell, kino og museum.
- Unntatt, altså ingen mva: bank, finans og gebyrer, forsikring, utleie av fast eiendom (med mindre utleier er frivillig registrert), helse, undervisning og salg av fast eiendom.

## Avskåret fradrag
| Hva | Regel |
|---|---|
| Servering: mat og drikke, også på reise, møtemat og catering med personale | Aldri fradrag (§ 8-3 a) |
| Representasjon: julebord og arrangementer for kunder eller ansatte | Aldri fradrag, og det gjelder hele arrangementet (e) |
| Kost og naturalytelser til eier eller ansatte: kaffe, frukt, gavekort, trening, privat mobil og bredbånd | Aldri fradrag (d). Faglige kurs, verneutstyr og lovpålagt bedriftshelsetjeneste gir fradrag |
| Gaver og reklameutdeling | Fradrag bare for gaver på 200 kr eller mindre per enhet (f) |
| Kunst og antikviteter | Aldri fradrag (c) |
| Bolig, hytte, velferdslokaler, hjemmekontor i privat bolig | Aldri fradrag (g). Bedriftskantine: fradrag for bygg og inventar, ikke for drift |
| Personbil, varebil klasse 1 og MC: kjøp, leie, leasing, drivstoff, lading, parkering, verksted, dekk og vask | Aldri fradrag (§ 8-4). Unntak: salgsvare, yrkesmessig utleie og drosje. Varebil klasse 2 og lastebil gir fradrag |

Kontonavn med «fradragsberettiget» i NS 4102 gjelder inntektsskatt, ikke mva.

## Dokumentasjon
- Salgsdokumentet må ha dette (bokføringsforskriften § 5-1-1):
  - selgers org.nr. og «MVA»
  - kjøpers navn eller org.nr.
  - dato, ytelse, beløp og mva
- Purringer, inkassovarsler, kontoutskrifter og ordrebekreftelser er ikke salgsdokumenter. Konklusjon: `ikke_salgsdokument`.
- En kreditnota skal vise til originalfakturaen (§ 5-2-7). Mangler henvisningen og originalen er entydig, er konklusjonen `ok_formmerknad`.

## Utland
- **Fjernleverbare tjenester fra utlandet** (programvare, annonser, konsulenttjenester) uten norsk mva: registrert klient bruker kode 86 (25 %) eller 88 (12 %) med fradrag. Klient som ikke er registrert, bruker kode 87 eller 89 når kjøpene i kvartalet overstiger 2 000 kr eks. mva. Det krever egen mva-melding.
- **Import av varer:** registrert klient beregner innførselsmva selv (kode 81 eller 83). For klient som ikke er registrert, er mva betalt til Tolletaten en ren kostnad.
- **Leverandørindeksen:** slå opp der først (`npm run -s leverandor -- finn <orgnr|navn>`). Lagre nye vurderinger av leverandøren (`vurder … --av agent --kilde …`).

## Klient ikke registrert
- Det er aldri fradrag. Mva er en del av kostnaden eller aktiveringen, og 27xx skal være tom.
- Se etter purringer og dubletter, manglende salgsdokument og salg som kan være avgiftspliktig.
- Tilvalg til samme kjøper som kjøper eiendommen følger det unntatte salget (BFU 15/13).
- § 3-26 og registreringsplikten vurderes årlig, ikke per bilag.

## Konklusjon per bilag
- **Verdier:** `ok`, `ok_formmerknad`, `ikke_salgsdokument`, `feil_kode`, `avskaaret_fradrag`, `manglende_dokumentasjon`, `feil_termin`, `tapt_fradrag`, `omvendt_avgiftsplikt_mangler`, `maa_avklares`.
- **Krav til avvik:** Et avvik krever en klar regel og klare fakta. Er regelen usikker eller faktaene uklare, blir konklusjonen `maa_avklares`, med et konkret spørsmål.
- **Svarformat** (lagres som `<arbeidsmappe>/vurdering.json`):
  ```json
  { "vurderinger": [{ "bilagsnr": "85", "bokfort": true, "voucher_id": 0, "konklusjon": "ok",
    "vurdering": "1–2 setninger med egne ord", "hjemmel": "mval. § …", "sikkerhet": "høy|middels|lav",
    "trenger_sjur": false, "anbefalt_korreksjon": { "tekst": "…" } }] }
  ```

## Personvern
- Ingen personnavn, e-postadresser, telefonnummer eller kontonumre i svaret.
- Ikke siter fritekst fra bilag.
- Enkeltpersonforetak omtales som «ENK-leverandør».
- Vedlegg lastes ned til arbeidsmappa og slettes etterpå.
