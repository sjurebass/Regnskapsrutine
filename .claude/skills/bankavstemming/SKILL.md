---
name: "bankavstemming"
description: "Bankavstemming for Tripletex-klienter: status per bankkonto og måned (lukket, åpen, ikke startet), umatchede bankposter som mangler bilag, hva som er internt arbeid, og Silfer-Excel med åpne poster til kunden. Lukker Tally-oppgaven «Bankavstemming». Bruk ved «bankavstemming», «avstem bank», «åpne poster på bank», «uavstemte poster», «hvilke klienter har bankkontoer som ikke er lukket», «lag excel med åpne bankposter»."
---

# Bankavstemming

Skillen viser hvor langt bankavstemmingen har kommet for én eller flere Tripletex-klienter, skiller det kunden må levere fra det byrået
må gjøre, og lager en Silfer-Excel med åpne poster til kunden. Den lukker Tally-oppgaven «Bankavstemming».

Grensen mot `mangelliste`: mangellisten er den månedlige e-posten til kunden for forrige måned. Bankavstemmingen ser på alle måneder
i året, finner etterslep og kontoer uten avstemming, og gir byrået en arbeidsliste. Det byrået kan føre selv, tas med `bilagsforing`.

Alt skjer i chatten. Excel-filen lagres i klientens dokumentarkiv i Tally (`docs/dokumentlagring.md`).

## Faste regler

- Klienten må være navngitt, eller brukeren må be om «alle». Gjett aldri.
- Bare lesing i Tripletex-MCP-en. Matching, lukking og opplasting er skriving (se «Krever CLI eller UI»).
- **Bare bankside-poster går til kunden.** En linje som bare finnes på banksiden, mangler i regnskapet. Poster på Tripletex-siden
  (bokført, ikke sett i bank) er internt arbeid, ofte timing.
- Umatchet er ikke det samme som manglende: motposten ligger ofte umatchet i den andre listen med samme beløp og dato.
  Sammenlign `unmatched` med `unmatchedPostings` og `awaitingApproval` før du kaller noe en mangel.
- Internt, ikke til kunden: skattetrekkskonto (navn med «skattetrekk», typisk 1950), negativ banksaldo, statisk saldo uten bevegelse,
  måneder som bare mangler lukking, «Fylt på» (påfyll mellom egne kort) og bank- og kortgebyrer.
- En periode som er `not_started` er ikke avstemt. En lukket periode kan likevel ha umatchede linjer. Null differanse på en lukket
  periode beviser ikke samsvar med kontoutskriften.
- Har kontoen ingen bankfeed (manuell avstemming, typisk Pareto, Cultura, Folio, sparekonto), er det kontoutskriften som mangler,
  ikke enkeltposter. Si det som «kontoutskrift for <måneder>».
- Rapporter aldri «ingenting å etterlyse» for en konto du ikke har fått lest. Si hva som ikke er sjekket og hvorfor.
- Ingen banktekster eller personnavn i chatten. Excel-arket er leveransen.

## Spar tokens

- Les flere klienter i ett `tripletex_run_script`-kall, og returner bare tellinger, summer og linjene til klientene som skal ha liste.
- Bruk `return`, ikke `print`, så svaret ikke kuttes.
- Ved ny kjøring av samme klient: si bare hva som er endret.

## Steg 0 – Sjekk tilkoblingene

Kall Tally `whoami` og Tripletex `search_client_companies` (uten søkeord) i samme runde. Rapporter på én linje, for eksempel
«Tally ✓ · Tripletex ✓». Uten Tally kan avstemmingen kjøres, men oppgaven kan ikke fullføres.

## Steg 1 – Finn klientene og reglene

1. Finn klientene med `search_client_companies` (navngitt klient, eller alle når brukeren ber om det).
2. Hent kundeinstruksen (`hent_instrukser`, se `kundeinstruks`): seksjonene «Bank» (bankfeed, kontoer uten integrasjon) og «Kjente avvik».
3. Periode: «til og med» forrige måned hvis ikke annet er sagt, fra januar samme år.

## Steg 2 – Hent status

Kjør ett skript for alle klientene. Gjør ett representativt kall først hvis du er usikker på feltnavnene (`tlx.help('get_unmatched_bank_transactions')`).

```js
const KLIENTER = ['<navn 1>', '<navn 2>'];         // eller alle fra search_client_companies
const AAR = 2026, TIL = '2026-09';                 // til og med
const ut = {};
for (const navn of KLIENTER) {
  try {
    const per = await tlx.get_bank_reconciliation_periods({ companyName: navn, year: AAR });
    const kontoer = {};
    for (const p of (per.periods ?? per.accounts ?? per)) {   // sjekk formen i første kall
      // behold konto, periode (ÅÅÅÅ-MM), status, bankBalance, ledgerBalance, difference
    }
    // For hver konto og åpen måned til og med TIL:
    //   const u = await tlx.get_unmatched_bank_transactions({ companyName: navn, accountNumber: '<konto>', date: '<ÅÅÅÅ-MM>-15' });
    //   behold antall og sum for u.unmatched, u.unmatchedPostings og u.awaitingApproval,
    //   og bare for u.unmatched: postedDate, amountCurrency, description
    ut[navn] = kontoer;
  } catch (e) { ut[navn] = { feil: e.message }; }
}
return ut;
```

Ett skript tåler 200 kall og 2 minutter. Mange klienter med mange åpne måneder deles i flere kjøringer. Rader som feiler på grunn av
rate limit, mangler; si det og kjør dem på nytt, aldri summer over dem.

## Steg 3 – Klassifiser per konto og måned

| Funn | Hvor |
|---|---|
| Bankside-linje uten motpost i `unmatchedPostings` eller `awaitingApproval` | **Fra kunden** (mangler bilag) |
| Linje med motpost i den andre listen | Internt: kan matches |
| Forslag i `awaitingApproval` | Internt: godkjenn forslaget |
| Konto uten bankfeed, måned etter siste lukkede med bevegelse | **Fra kunden**: kontoutskrift |
| Åpen måned uten umatchede linjer | Internt: kan lukkes |
| Konto med bevegelse og `not_started` | Internt: avstemming ikke opprettet |
| Skattetrekkskonto, negativ saldo, statisk saldo, «Fylt på», gebyr | Internt |
| Kjent avvik i kundeinstruksen med samme beløp | «Kjent, uendret» |

Sjekk også bilagsmottaket med `get_voucher_inbox_count`. Ubehandlede dokumenter kan høre til åpne linjer, og da er det `bilagsforing` først.

## Steg 4 – Oversikt

Én tabell over alle klientene, uten banktekster:

| Klient | Fra kunden | Internt |
|---|---|---|
| <Klient> | 1920: 6 poster uten bilag; 1931: kontoutskrift jan–jul | 1920 jan–feb: kan lukkes; 1950: skattetrekkskonto ikke lukket |

Nevn klienter som ikke kunne leses, som egen gruppe med grunn.

## Steg 5 – Excel til kunden

For klienter med noe under «Fra kunden»: bygg `data.json` og kjør generatoren. Filen lages i scratch.

```json
{
  "selskap": "<Klient AS>", "orgnr": "<org.nr.>", "aar": "2026", "periode": "Januar–September 2026",
  "kontoer": [
    { "nummer": "1920", "navn": "Driftskonto", "maaneder": [
        { "maaned": "September", "poster": [
            { "dato": "2026-09-03", "tekst": "<banktekst>", "belop": -347.08, "kilde": "Bankside" } ] } ] },
    { "nummer": "1931", "navn": "Kort", "merknad": "Ingen bankfeed – send kontoutskrift for januar–juli 2026.", "maaneder": [] }
  ]
}
```

```bash
uv run --with openpyxl --with pillow python .claude/skills/bankavstemming/scripts/generer_excel.py <scratch>/data.json "<scratch>/<Måned> <år> Bankavstemming åpne poster <Klient>.xlsx"
```

- Generatoren fjerner «Fylt på» og gebyrer, renser bankteksten (kortnummer, «VISA VARE», kurs, referanser) og legger utenlandsk beløp bak.
  Gi `"tekst"` i stedet for `"raw"` hvis du ikke vil at teksten skal renses.
- Kontoer uten poster tas med som tom liste; de vises med 0 i sammendraget.
- Faner: «Sammendrag» (antall og sum per konto med formler, merknad) og «Åpne poster» (filtrerbar, kolonnene Dokumentasjon og Status er tomme for kunden).
- Kontroller filen med openpyxl: antall og sum per konto skal stemme med steg 3. LibreOffice finnes ikke på maskinene; formlene beregnes når filen åpnes i Excel.
- **Lagre i Tally** etter ja (`docs/dokumentlagring.md`): kategori `BILAG`, periode `ÅÅÅÅ-MM`, samling `Bankavstemming ÅÅÅÅ`, knyttet til oppgaven «Bankavstemming».
  Erstatter filen en tidligere liste for samme måned, arkiver den gamle. Kontroller med `list_documents`, og slett filen fra scratch.
- Si antall poster per konto og totalsum, og gi lenken til dokumentet. Ikke lim inn listen i chatten.
- Claude kan ikke legge ved filer i Missive-utkast. Skal kunden ha listen, viser e-posten fra `mangelliste` til dokumentet i Tally, eller brukeren legger den ved.
- Kontoutskrifter og Tripletex sin bankavstemmings-PDF lagres på samme måte (samme kategori og samling).

## Krever CLI eller UI

**Krever CLI (Sjur) eller Tripletex-UI:** alt under her. Tripletex-MCP-en har ingen verktøy for å matche, opprette eller lukke avstemminger.
Gi brukeren en nummerert liste over hva som skal gjøres i Tripletex når CLI-et ikke finnes.

- **Matche** linje mot postering: `POST /bank/reconciliation/match` (type MANUAL) med transaksjoner og posteringer. Fungerer også når posteringen
  ligger i forrige måned.
- **Godkjenne forslag**: `PUT /bank/reconciliation/match/:suggest` eller i UI under «Forslag».
- **Lukke** en måned med differanse 0: `PUT /bank/reconciliation/{id}` med `isClosed=true`. Les avstemmingen før og etter.
- **Manuell avstemming** (konto uten bankfeed): før kontoutskriften som ett bankbilag per måned, datert siste dag, med én linje per bankpost
  mot reskontro, gebyr (7770) eller renter (8050). Opprett avstemmingen (`POST /bank/reconciliation`, type MANUAL) med utgående saldo fra
  kontoutskriften, legg kontoutskriften ved, og lukk når differansen er 0.
- **Senere måned allerede godkjent** gir 422 når en tidligere måned opprettes. Åpne den senere måneden (etter ja), avstem den tidlige, lukk den senere igjen.
- **Konto uten kontoutskrift og saldo 0** kan avstemmes mot 0 etter ja.
- **Vedlegg** (kontoutskrift, Tripletex' bankavstemmings-PDF) på bankavstemmingen eller på 19xx-linjen i avstemmingsmodulen.

Hvert av disse er et skrivekall: vis hva som skal gjøres per klient, få ja, les før og etter.

## Flere klienter

Kjør steg 2 som ett skript for alle. Trenger du å se på mange enkeltlinjer, gi én lesende agent per klient oppgaven å klassifisere (steg 3)
og returnere oversiktslinjen og `data.json`. Hovedagenten lager Excel-filene og skriver.

## Hurtigvei – bare Sjur

Finnes `C:\Users\Sjur\Tripletex API`, gjør ett kall hele jobben for alle klienter på rundt 40 sekunder:

```powershell
npm --prefix "C:\Users\Sjur\Tripletex API" run -s bankavstemming -- --til ÅÅÅÅ-MM --alle --excel --ut "<scratch>\bankavstemming"
```

Bruk `--client "navn"` (kan gjentas) i stedet for `--alle`. Ikke bruk `--kundemapper`. Excel-filene i `--ut` lagres så i Tally som beskrevet over.
Stdout er oversiktstabellen og kan vises direkte.

## Det du aldri gjør

- Matcher, lukker, oppretter eller sletter avstemminger uten ja.
- Sender e-post til kunden. Utkast lages i `mangelliste`.
- Bruker hovedbokssøk for å finne åpne bankposter. Hovedboken viser bare det som er bokført.
- Fjerner identiske rader. Mange like beløp er ekte.
- Lagrer Excel-filer eller banktekster på PC-en i stedet for i Tally, eller laster opp uten ja.

## Fullfør i Tally

Når avstemmingen for perioden er ferdig (alle måneder lukket, eller det som gjenstår er etterlyst):

1. Foreslå tidsbruk og spør: «Skal jeg fullføre Bankavstemming for <klient> og føre <X> minutter?»
2. Ved ja: `add_task_comment` med periode, kontoer som er lukket og hva som gjenstår, så `log_time` og `complete_task`.
3. Fullfør bare oppgaven for perioden som faktisk er avstemt. En fremtidig forekomst fullføres aldri.
4. Et ja for én klient gjelder ikke neste.

## Referanser

- `scripts/generer_excel.py` – Silfer-Excel (Sammendrag og Åpne poster). Logoen ligger i `assets/silfer_logo.png`.
- `docs/kontrollkatalog.md` – kontrollene B1–B5.
