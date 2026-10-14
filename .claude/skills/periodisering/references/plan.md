# Forslaget og planen for `bilag manuell`

Kommandoen: `npm run -s bilag -- manuell --client "<klient>" --plan <mappe>/manuell.json [--bare <ref>,<ref>] [--vesentlighet <V>] [--bekreft]`.
Uten `--bekreft` er det tørrkjøring: J-kontrollene kjøres og ingenting føres (`docs/foringskontroll.md`). Kommandoene kjøres fra repo-rota.

## Forslaget i chatten (steg 3)

**Bilag 1 – forskudd-forsikring-2026-09 · 30.09.2026 · Periodisering forsikring sep 2026**

| Linje | Konto | Navn | Debet | Kredit | Avd. | Tekst |
|---|---|---|---|---|---|---|
| 1 | 7500 | Forsikringspremie | 1 250,00 | | 100 | 1/12 av premie 15 000 |
| 2 | 1700 | Forskuddsbetalt kostnad | | 1 250,00 | | Forsikring sep 2026 |
| | | **Sum** | **1 250,00** | **1 250,00** | | |

Grunnlag: polise 2026 (bilag 214-2026), 15 000 / 12. · Tilbakeføring: nei. · Forrige periode: bilag 388-2026, 1 250,00, uendret.

## manuell.json

Én fil per kjøring (Write, UTF-8), én rad per bilag:

| Felt | Påkrevd | Innhold |
|---|---|---|
| `ref` | ja | Unik og stabil nøkkel `<type>-<post>-ÅÅÅÅ-MM`. Brukes i loggen, i dublettsjekken og når kommandoen kjøres på nytt (ferdige refs hoppes over). |
| `dato` | ja | Bilagsdato `ÅÅÅÅ-MM-DD`, normalt siste dag i perioden. |
| `beskrivelse` | ja | Hva og hvilken periode, kort (`docs/foringskontroll.md`, «Dokumentasjon per føring»). |
| `linjer[]` | ja | Minst to. `konto`, `belop` (+ debet, − kredit, NOK, to desimaler), valgfritt `mva` (Tripletex-koden; mangler = 0 eller kontoens låste kode), `avdeling`, `prosjekt`, `leverandor`, `kunde` og `tekst`. Alle linjene får bilagsdatoen. |
| `tilbakefor` | nei | Dato for tilbakeføring, normalt første dag i neste periode. Bare påløpte poster. |
| `vedlegg` | nei | PDF, PNG, JPEG eller TIFF som lastes opp på bilaget: kildedokumentet og beregningen (PDF fra `silfer-rapport`). Sti relativt til planen. |

- `avdeling`, `prosjekt`, `leverandor` og `kunde` er Tripletex-id-er, ikke avdelings- eller kundenummer: slå opp med `/department`, `/project`,
  `/supplier` eller `/customer` og `fields=id,number,name`. Ukjente gir FEIL (J5, J6).
- Én leverandør per bilag (den settes på alle linjene); kunde og leverandør i samme bilag, eller ansattreskontro, stoppes (J6) – del bilaget.
- Valuta: bare NOK. Omregn med Norges Bank-kurs og vis kursen og valutabeløpet i beregningen.

```json
[
  { "ref": "forskudd-forsikring-2026-09", "dato": "2026-09-30", "beskrivelse": "Periodisering forsikring sep 2026",
    "linjer": [ { "konto": 7500, "belop": 1250.00, "mva": 0, "avdeling": 100, "tekst": "1/12 av premie 15 000, bilag 214-2026" },
                { "konto": 1700, "belop": -1250.00, "tekst": "Forsikring sep 2026" } ],
    "vedlegg": ["Periodisering 2026-09 Eksempel AS.pdf"] },
  { "ref": "palopt-strom-2026-09", "dato": "2026-09-30", "beskrivelse": "Påløpt strøm sep 2026, faktura ikke mottatt",
    "linjer": [ { "konto": 6340, "belop": 4180.00, "mva": 0, "tekst": "Forbruk 2 090 kWh × 2,00" },
                { "konto": 2960, "belop": -4180.00, "tekst": "Påløpt strøm sep 2026" } ],
    "tilbakefor": "2026-10-01",
    "vedlegg": ["Periodisering 2026-09 Eksempel AS.pdf"] },
  { "ref": "ompost-1370-412-2026", "dato": "2026-09-30", "beskrivelse": "Ompostering fra 1370, bilag 412-2026 (kvittering mottatt)",
    "linjer": [ { "konto": 6860, "belop": 890.00, "mva": 0, "tekst": "Kurs, kvittering til bilag 412-2026" },
                { "konto": 1370, "belop": -890.00, "tekst": "Fra 1370" } ],
    "vedlegg": ["dok/412-2026.pdf"] }
]
```

Kontonumrene i eksemplene er typiske; bruk klientens egne (`references/typer.md`). Mva-kode 0 på periodiseringer og påløpte poster; en ompostering
som skal gi fradrag, får koden fra originalbilaget og vurderes i J4.

## Tørrkjøringen (steg 5)

Per bilag: linjene (konto, debet, kredit, mva, avdeling, prosjekt, part), sum, og PASS, FEIL, ADVARSEL eller INFO per kontroll; til slutt antall
uten avvik, med ADVARSEL og med FEIL (exit 1 ved FEIL). Les den mot forslaget:
- Sum debet = sum kredit = beløpet i forslaget, og samme fortegn per konto (J1, vanlig feil 3).
- Ingen FEIL. Hver ADVARSEL har en forklaring i grunnlaget (J9 over V, J7 mulig dublett, J11 uten vedlegg). INFO om runde beløp (J10) besvares med beregningen.
- `tilbakefor` står med dato i åpen periode (J8).

## Tilbakelesing (steg 7)

`<mappe>/manuell.resultat.json` har én oppføring per ref: `nummer` (bilag), `reversering` og `tilbakefor`, `vedlegg` (filene som er lastet opp),
`ok`, `feil` og `kontroll.advarsel` (ADVARSEL-ene ja-et gjaldt).
- Ferdig (`ok`): bilaget finnes, vedleggene er lastet opp, og påløpte poster har tilbakeføring.
- `feil`: ref-en er «ikke gjort» (eller delvis: bilaget finnes, resten mangler). Rett og kjør igjen med `--bare <ref>`; ferdige steg hoppes over.
- `avbrutt`: et skrivekall fikk ikke svar. Sjekk hovedboken før noe kjøres på nytt; kommandoen stopper til det er avklart.
- Konsollen viser bare konto, beløp og bilagsnummer. Kvitteringen i chatten bygges fra resultatfilen og saldoen lest på nytt.
