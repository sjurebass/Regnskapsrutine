# Bilagskontroll – kontroller, unntaksliste og konklusjoner

Reglene er de samme som i `npm run -s mva` (CLI-id i siste kolonne), så bilagskontrollen og mva-kontrollen gir samme svar. Endres de, endres begge.
Alt gjelder posteringer i måneden, lest med `api` (se SKILL.md steg 2). Funnene inneholder bilagsnummer, konto, kode og beløp – aldri tekst fra bilaget.

## Alvor, status og port

| Alvor | Betyr | Status i funn-formatet | Del av beslutningslista |
|---|---|---|---|
| STOPP | kontrollen kan ikke kjøres videre | IKKE AVKLART | må rettes eller avklares |
| BLOKK | feil som må rettes | AVVIK | må rettes |
| SPØR | krever regnskapsførers skjønn | IKKE AVKLART | spørsmål |
| FORKLAR | må forklares eller følges opp | AVVIK → FORKLART når forklart | følg opp |
| INFO | bare til orientering | OK | (telles i Sammendrag) |

Port etter `docs/skill-mal.md`: rød = STOPP, eller BLOKK med beløp eller mva-effekt ≥ V; gul = annen BLOKK eller SPØR; grønn = resten.
Kjente avvik med samme nøkkel og beløp får status KJENT og påvirker ikke porten.

## Kontroller (registrert klient)

| ID | Kontroll | Utslag | Alvor | CLI-id |
|---|---|---|---|---|
| D1 | Leverandørbilag (2400 kredit + kostnad 1100–1499 eller 4000–7999, uten 19xx-linje, ikke reversert) uten vedlegg eller EHF | alle; list ≤ 20 bilagsnr. | FORKLAR | F1.6 |
| M5 | Fradrag (kode 1, 11, 13, 14, 15, 81, 83, 86, 88) på bilag fra D1-lista | mva ≥ 1 kr | BLOKK | – |
| M4 | Mva-kode ≠ 0 på konto uten mva: 1500–1599, 1900–1999, 2000–2399, 2400–2499, 2600–2699, 2770–2799, 5000–5899, 6000–6099, 7500–7599, 7770, 7800–7899, 8000–8999 | mva ≥ 100 kr → BLOKK, ellers FORKLAR | BLOKK / FORKLAR | – |
| M7 | Utland: leverandør med vurdering «omvendt avgiftsplikt» i `leverandorindeks` ført uten kode 86/88; leverandør uten norsk org.nr. og uten vurdering | grunnlag ≥ 500 kr; uten vurdering → unntakslista | BLOKK / SPØR | UR5 |
| M8 | Sats: mva ≠ grunnlag × 25/15/12 % per linje | ≥ 1 kr | FORKLAR | – |
| M8 | EHF: fradrag ≠ mva på EHF (EH4); fradrag fra leverandør uten mva-registrering (EH5) | ≥ 1 kr | BLOKK | EH4, EH5 |
| M8 | EHF: stilet til annen kjøper (EH1); bokført ≠ EHF (EH2); mva på EHF uten fradrag hos registrert selger (EH6) | ≥ 1 kr | FORKLAR | EH1, EH2, EH6 |
| M8 | EHF: kreditnota uten henvisning til original (EH3) | – | INFO | EH3 |
| D3 | Fakturadato i en annen måned enn bilagsdato; bilag datert frem i tid | annen termin og mva ≥ 100 kr → BLOKK | FORKLAR | – |
| R6 | Dublett: samme leverandør + normalisert fakturanr. + kreditnota ja/nei, bokført to ganger | alle | BLOKK | MD1 |
| R6 | Dublett: ikke bokført bilag eller dokument i mottaket mot bokført (samme org.nr. + fakturanr., eller Tripletex' dublettmerke) | alle → unntakslista | FORKLAR | MD1 |
| R6 | Nær-dublett: samme leverandør og beløp innen ±30 dager, ulikt fakturanr. | ≥ 1 000 kr → unntakslista | FORKLAR | – |
| D5 | Manuelt bilag (bilagstype fra `/ledger/voucherType`) med beløp i hele tusen, eller manuelt bilag uten vedlegg | ≥ V → unntakslista | FORKLAR | – |
| D2 | Observasjonskonto (1370, 7799, 1960 og kontoen i «Mangelliste») ≠ 0 ved månedsslutt | ≠ 0 → forslag ompostering | FORKLAR | – |
| E2 | Signalord i teksten (julebord, gave, lunsj, hotell, leiebil, parkering, lading, privat, mobil, bredbånd) på 5900–5999, 6500–6599, 6800–6899, 7100–7199, 7300–7499, 7700–7799 | ≥ 500 kr → unntakslista | FORKLAR | – |
| D7 | Ny eller ukjent leverandør: første bruk på 12 måneder, uten org.nr., ENK, utenlandsk uten vurdering, konkurs eller slettet i Brreg | per leverandør | INFO (FORKLAR ved fradrag) | – |
| D6 | Dokumenter i bilagsmottaket (F1.1); ikke bokførte bilag eller leverandørfakturaer med bilagsnummer 0 (F1.3) | ≥ 1; dato i måneden → FORKLAR | FORKLAR / INFO | F1.1, F1.3 |

Leverandøren identifiseres med org.nr. via `leverandorindeks` (nøkkel `NO:<orgnr>`, `UT:` for utenlandsk, `?:` for ukjent), ellers Tripletex-id.
Fakturanummer normaliseres: store bokstaver, bare A–Z og 0–9, uten innledende nuller. EHF som ikke kan leses: M8 «ikke kontrollert».

## Klient som ikke er registrert (i stedet for M4, M5 og M8)

| Kontroll | Utslag | Alvor | CLI-id |
|---|---|---|---|
| Mva-kode utenom 0, 6, 7, 87, 89 og 92, gruppert per konto og kode | alle | BLOKK | UR1 |
| Innførselskode (14, 15, 20, 21, 22, 81–85) | alle | BLOKK | UR7 |
| Postering på 2700–2749 uten omvendt avgiftsplikt i samme bilag | alle | BLOKK | UR1 |
| Kostnad ført netto (beløp ≠ bruttobeløp med tillatt kode) | ≥ 1 kr | BLOKK | UR1 |
| Fjernleverbare tjenester fra utlandet (vurdert omvendt, eller `UT:` uten vurdering; ikke VOEC, ikke varer), minus kreditnotaer, per kalenderkvartal | over 2 000 kr → melding med kode 87/89 | BLOKK | UR5 |
| Leverandør uten norsk org.nr. og uten vurdering | ≥ 1 | SPØR | UR5 |

Status uklar (Tripletex og Brreg er uenige, eller ikke slått opp): STOPP (UR0). Ingen andre kontroller kjøres før det er avklart.

## Unntakslista (høyst 10 bilag)

1. Funn på bilagsnivå som krever skjønn: R6 mot ikke bokført eller mottak, nær-dubletter, D5, E2, M7 uten vurdering, bilag ≥ V uten EHF.
2. Registrert klient: bilag med fradrag (kode 1, 11, 13) ≥ 1 kr på skjønnskontoer 5900–5999, 7000–7199, 7320–7399, 7400–7499.
3. Registrert klient: fradrag fra leverandør med nøkkel `UT:` eller `?:` uten vurdering i `leverandorindeks`.

Ett bilag står én gang med alle grunnene. Sorter etter |mva-effekt|, så |beløp|. Ta de 10 første; resten telles som «utelatt n». Kjente avvik tas ikke med.

## Konklusjon fra agenten → funn

| Konklusjon (`docs/fradragsregler-kort.md`) | Alvor | Tekst i lista |
|---|---|---|
| `feil_kode`, `avskaaret_fradrag`, `feil_termin`, `omvendt_avgiftsplikt_mangler` | BLOKK | må rettes |
| `maa_avklares` | SPØR | spørsmål, med agentens konkrete spørsmål |
| `manglende_dokumentasjon`, `ikke_salgsdokument`, `tapt_fradrag` | FORKLAR | følg opp |
| `ok_formmerknad` | INFO | samles i én linje: «formmerknad – be leverandøren rette neste gang» |
| `ok` | – | ingen linje |

Har bilaget allerede et maskinelt funn, legges vurderingen til der. Bare en strengere konklusjon gir et eget funn.
