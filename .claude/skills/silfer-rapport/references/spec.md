# spec.json – fullt skjema

Én spec gir både Excel og PDF/HTML. Nøklene er norske; ukjente felt avvises med sti til feilen. Filen er UTF-8 (BOM tåles).
Eksempler: `scripts/eksempler/*.json` (fiktive data, «Eksempel AS»).

```
{ "versjon": 1, "dokument": {…}, "seksjoner": [ {…}, … ] }
```

## dokument

| Felt | Type | Standard | Bruk |
|---|---|---|---|
| `hva` | tekst, påkrevd | – | Første del av filnavnet og bunnteksten, f.eks. «Bankavstemming åpne poster» |
| `tittel` | tekst | `hva` | h1 i PDF, D2 i Excel (ark med én seksjon bruker seksjonens `overskrift`) |
| `klient` | tekst, påkrevd | – | Firmanavn i undertittel og filnavn |
| `orgnr` | tekst | – | Vises som «Org.nr. …» slik det er skrevet |
| `under` | [tekst] | [] | Ekstra felt i undertittelen, f.eks. «Kunde: Eksempel Kunde AS (kundenr. 10023)» |
| `periode` | tekst, påkrevd | – | `ÅÅÅÅ-MM`, `ÅÅÅÅ-T<n>` eller `ÅÅÅÅ` – i filnavnet |
| `periode_tekst` | tekst | `periode` | Visning: «Periode 01.01.2026–30.09.2026» |
| `utarbeidet` | dd.mm.åååå (ISO tåles) | i dag | «Utarbeidet …» |
| `utarbeidet_av` | tekst | – | Initialer: «Utarbeidet av AB» |
| `bunntekst` | tekst | «Silfer AS · <hva> · <utarbeidet>» | Sentrert grå linje nederst i PDF |
| `sidetall` | bool | true | «Side n av N» stemples på hver PDF-side |
| `personvern.redact` | bool | true | Maskering av tekst, se under |

Undertittel: `klient | Org.nr. … | <under…> | Periode … | Utarbeidet … [| Utarbeidet av …]` (Excel bruker `   |   `).

## seksjoner[]

| Felt | Type | Standard | Bruk |
|---|---|---|---|
| `id` | tekst | `s1`, `s2` … | Brukes av `sammendrag.av` |
| `ark` | tekst ≤ 31, uten `[]:*?/\` | «Rapport» | Excel-fane. Seksjoner med samme `ark` stables i rekkefølge |
| `overskrift` | tekst | – | PDF: h2/h3. Excel: grønn seksjonslinje når fanen har flere seksjoner (eller `bar: true`) |
| `nivaa` | 2 \| 3 | 2 | h2 (mørk) eller h3 (grønn) |
| `bar` | bool | auto | Tving/skjul grønn seksjonslinje i Excel |
| `sideskift` | bool | false | Ny PDF-side før seksjonen |
| `tekst` | tekst | – | Avsnitt før tabellen |
| `tabell` / `kontroller` / `sammendrag` / `oppstilling` | objekt | – | Høyst én per seksjon |
| `boks` | `{"type": "konkl"\|"varsel", "tekst": …}` | – | Grønn (konklusjon) eller oransje (varsel/tiltak) boks etter tabellen |
| `punkter` | [tekst] | – | Nummerert liste |
| `merknad` | tekst | – | Liten grå tekst til slutt (kilde, forbehold) |

I `tekst`, `boks`, `punkter`, `merknad` og `kontrollsum` gir `**fet**` fet skrift i PDF (Excel viser ren tekst).

## kolonne

`{"id", "tekst", "type", "bredde", "just", "vis", "lopende", "redact"}` – eller bare `"id"` som kortform.

| Felt | Standard | Bruk |
|---|---|---|
| `id` | påkrevd | Nøkkel i radene |
| `tekst` | id med stor forbokstav | Kolonneoverskrift |
| `type` | `tekst` (`belop` når `lopende` er satt) | `tekst`, `heltall` (konto, bilag), `dato`, `belop` (kr), `antall`, `prosent` (12.5 = 12,5 %), `status` |
| `bredde` | tekst 24, heltall 9, dato 12, belop 14, antall 10, prosent 9, status 13 | Excel-bredde (tegn) |
| `just` | tekst/heltall/dato `l`, tall `r`, status `c` | `l`, `r`, `c` |
| `vis` | `begge` | `excel` = bare i Excel (f.eks. tomme kolonner kunden fyller ut), `pdf` = bare i PDF |
| `lopende` | – | `{"start": IB, "pluss": kolonne-id, "minus": kolonne-id}` – løpende saldo; minst én av pluss/minus |
| `redact` | `dokument.personvern.redact` | Overstyr maskering per kolonne (`false` for f.eks. bilagsnummer i tekst) |

Visning: `belop` → `1 234,50` (hardt mellomrom, komma, ASCII-minus), Excel-format `#,##0.00;[RED]\-#,##0.00`;
`antall` → `#,##0`; `dato` → `dd.mm.åååå` (ISO eller dd.mm.åååå inn); `status` → farget celle.

## tabell

| Felt | Bruk |
|---|---|
| `kolonner` | Liste med kolonner (påkrevd) |
| `rader` | `[{id: verdi, …, "_fet": true?}]` eller posisjonslister `[[v1, v2, …]]` i kolonnerekkefølge. Ukjente id-er avvises |
| `ib` | Celler i første rad (fet), f.eks. `{"dato": "2026-01-01", "tekst": "Inngående saldo"}`. Lages automatisk når en kolonne har `lopende`. `ib.verdi` overstyrer `lopende.start` |
| `ub` | Celler i siste rad (fet). `ub.verdi` = saldo fra kilden (reskontro, bank); uten den brukes beregnet sluttsaldo |
| `sum` | `{"etikett", "kolonner": [id], "tell": id?, "tell_kol": id?, "etikett_kol": id?, "skal_vaere": tall?, "skal_vaere_kol": id?}` |
| `kontrollsum` | `{"tekst"?, "tekst_avvik"?}` – krever `lopende`. Plassholdere: `{ib} {pluss} {minus} {ub} {diff} {beregnet}` |
| `etikett_kol` | Kolonnen for «Sum», «Inngående saldo» o.l. Standard: kolonnen med id `tekst`, ellers første tekstkolonne |
| `liten` | Tett PDF-tabell (7,6 pt) |
| `filter`, `frys`, `zebra` | Excel: autofilter, frys under tabellhodet (og utskriftstittel), annenhver rad lys |
| `uthev_avvik` | Rader med AVVIK/FEIL/MANGLER får lys rød bakgrunn |

Sum-regler: `SUM` per kolonne i `kolonner`; `etikett` kan inneholde `{n}` (antall datarader); `tell` gir `COUNTA` over den kolonnen,
plassert i `tell_kol` eller første ledige kolonne; `skal_vaere` sammenlignes med første sumkolonne og gir OK/AVVIK i første ledige
kolonne. Med `filter` står én tom rad før sumraden. En tom tabell får én tom datarad, så formlene aldri peker på et tomt område.

Kontrollsum: IB + Σpluss − Σminus sammenlignes med UB. Stemmer det på øret, kommer `tekst` i grønn boks
(standard «**Kontrollert:** inngående saldo {ib} + … = utgående saldo {ub}.»), ellers `tekst_avvik` i oransje boks.
Excel får i tillegg en kontrollrad med formelen og en statuscelle.

## kontroller (lønnsformen)

```
{"etiketter": {"a": "A07 / beregnet", "b": "Regnskap"}, "antall_avvik": true,
 "rader": [{"navn", "beregning", "a", "b", "toleranse": 1, "forklart": false, "kommentar", "antall": false}]}
```

Kolonnene blir Kontroll | Beregning | A | B | Avvik (`=A−B`) | Status (`=IF(ABS(avvik)<=toleranse,"OK","AVVIK")`, `FORKLART` i stedet
for `AVVIK` når `forklart: true`) | Kommentar. `antall: true` gir heltallsformat. `antall_avvik` legger til «Antall avvik» (`COUNTIF`).

## sammendrag

```
{"av": "<seksjon-id med tabell>", "gruppe": "<kolonne-id i begge>",
 "kolonner": [{"id": "konto", …}, {"id": "antall", "tell": true}, {"id": "sum", "type": "belop", "summer": "belop"}, …],
 "rader": [{"konto": 1920, "navn": "Driftskonto"}, …], "sum": {"etikett": "Totalt", "kolonner": ["antall", "sum"]}}
```

`tell` gir `COUNTIF(<gruppe i kilden>, <gruppe i raden>)`, `summer` gir `SUMIF` over kildekolonnen. PDF viser de beregnede tallene.
Flaggene `zebra`, `filter`, `frys`, `liten`, `uthev_avvik` virker som i `tabell`.

## oppstilling (resultat og balanse)

```
{"kolonner": [{"id": "konto", "type": "heltall"}, {"id": "tekst", "tekst": "Linje"},
              {"id": "na", "tekst": "Sep 2026", "type": "belop"}, {"id": "ifjor", "tekst": "Sep 2025", "type": "belop"},
              {"id": "avvik", "tekst": "Avvik kr", "type": "belop", "avvik": ["na", "ifjor"]},
              {"id": "pst", "tekst": "Avvik %", "type": "prosent", "avvik": ["na", "ifjor"]}, {"id": "status", "type": "status"}],
 "linjer": [{"id": "inntekt", "gruppe": "Driftsinntekter", "sum": "Sum driftsinntekter", "rader": [{"konto": 3000, "tekst": "…", "na": 1, "ifjor": 2}]},
            {"id": "driftsres", "resultat": "Driftsresultat", "ledd": ["inntekt", "-driftskost"]},
            {"id": "kontroll", "resultat": "Kontroll", "ledd": ["eiendeler", "-ekgjeld"], "skal_vaere": 0}],
 "frys": true}
```

- **Verdikolonner** er `belop`/`antall` uten `avvik`; de summeres. **Avvikskolonner** (`"avvik": [a, b]`) regnes per rad, også på sum- og
  resultatlinjer: `belop`/`antall` = a − b, `prosent` = (a − b) / |b| × 100 (tom når b = 0). Andre kolonner (tekst, status) er data.
- **Gruppe**: `gruppe` (fet overskrift), `rader` (kontolinjer med innrykk), `sum` (fet sumlinje = `SUM` over radene). Alle tre er valgfrie;
  uten `sum` brukes `SUM` over radene direkte i resultatlinjene. `innrykk: false` fjerner innrykket, `luft` gir tom rad før i Excel.
- **Resultatlinje**: `resultat` (etikett) og `ledd` – id-er til linjer over, `-id` trekkes fra. Gir formel som `=C11-C35`.
  `skal_vaere` gir OK/AVVIK i første statuskolonne når alle verdikolonnene er lik verdien (`IF(AND(ABS(…)<0.005, …))`).
- `celler` på en gruppe eller resultatlinje fyller tekst- og statuskolonner på sum-/resultatlinjen. Radene kan ikke sette verdier i avvikskolonner.
- Fortegnet er presentasjonsfortegnet: specen får tallene slik de skal vises (inntekter og kostnader positive, egenkapital og gjeld positive).
- Flagg: `liten`, `frys`, `zebra`, `uthev_avvik`. Excel: formler for summer, resultatlinjer og avvik; statusformat over hele oppstillingen.
- Eksempel: `scripts/eksempler/regnskapsrapport.json` (resultat, balanse med kontroll, nøkkeltall, avvik og bro).

Bro (waterfall) er en vanlig `tabell`: `ib.verdi` = start, rader = drivere i én `pluss`-kolonne, `lopende` = kumulativt, `ub.verdi` = slutt og
`kontrollsum` med egen tekst («Broen går opp: … {ib} + drivere {pluss} = … {ub}»). Går ikke broen opp, blir boksen oransje.

## Status og farger

| Status | Farge |
|---|---|
| OK | grønn tekst på lys grønn |
| AVVIK, FEIL, MANGLER | rød tekst på lys rød |
| FORKLART, PERIODISERT, MERKNAD, KJENT | oransje tekst på lys oransje |
| IKKE AKTUELT, IKKE AVKLART | grå tekst |

Mørk `#1B2E28` (titler, tabellhode, strek), grønn `#2D5A4A` (seksjoner, h3), grå `#6B7280`, tekst `#1A1A1A`.

## Personvern

Med `personvern.redact` (standard på) erstattes dette med «[skjult]» i tekstceller, `ib`/`ub`-tekst, avsnitt, bokser, punkter og
merknader: kontonummer (4-2-5, også uten skille), IBAN, 11-sifrede nummer, e-post, telefon med +47/0047 eller vanlig gruppering.
Løse 8-sifrede tall (KID, bilag) og navn røres ikke. Antall maskerte felt skrives ut. Toppfeltene (`dokument`) maskeres ikke.

## Utdata

- Filnavn `<hva> <periode> <klient>.<endelse>` (ulovlige tegn erstattes med «-», maks 120 tegn).
- Excel: logo A1 (150 × 46), tittel D2, undertittel D3, mørk strek i rad 5, tabeller fra rad 7, A4 tilpasset bredden, bunntekst
  «Silfer AS · <ark>» og «Side n av N». Formler med engelske navn og komma.
- PDF: HTML med notatenes CSS skrevet ut med Edge/Chrome (`--headless=new`, egen profil, venter på stabil filstørrelse),
  så «Side n av N», `/Title` og `/Author` = «Silfer AS» med pypdf. `SILFER_BROWSER` overstyrer nettleseren.
- Exit-koder for `rapport.py`: 0 ferdig, 1 feil i spec eller bygging, 2 ingen nettleser (HTML skrevet i stedet).

## Python

```python
sys.path.insert(0, "<repo>/.claude/skills/silfer-rapport/scripts")
from silfer import bygg, filnavn          # bygg(spec | sti, ut, behold_html=False) → Path; format fra endelsen
from silfer.spec import valider, SpecFeil  # valider(spec) → normalisert spec; spec["_redigert"] = antall maskerte felt
from silfer.tekst import kr, hel, dato_no, clean_tekst, parse_raw, redact
```
