# Lukkekalender – avhengigheter, status og nøkkeltall

Byråets månedsavslutning per klient, bygget på månedshjulet i `README.md` («Månedshjulet») og Tally-oppgavene. M = måneden som avsluttes;
datoene er i måneden etter M. Avstemmingsmetoden står i `docs/avstemmingsmetodikk.md`, gate-punktene i `references/kontroller.md`.

## Avhengighetsnivåer

Et nivå kan starte når nivået under er ferdig for de samme kontoene. Arbeid på samme nivå kan gå parallelt.

| Nivå | Arbeid | Skill | Tally-oppgave | Frist | Avhenger av |
|---|---|---|---|---|---|
| 1 | Bilagsføring mot bank og bilagsmottak | `bilagsforing` | Bilagsbehandling | 5.–20. | – |
| 1 | Mangelliste til kunden | `tally-gjoremal` | Oversendelse mangelliste | 5.–12. | – |
| 1 | Lønn og a-melding | `lonnskjoring`, `a-melding` | Kjør lønn, Send lønnsslipper, A-melding | lønnsdato, 5. | – |
| 1 | Faste periodiseringer og avskrivninger | `periodisering` | – (del av Ferdigstillelse perioderegnskap) | før 16. | – |
| 2 | Bankavstemming | `bankavstemming` | Bankavstamming | 15. | bilagsføring |
| 2 | Kontroll av bilag | `bilagskontroll` | Kontroll av bilag | 15. | bilagsføring |
| 2 | Reskontroavstemming | `reskontroavstemming` | Avstemming kundereskontro, Avstemming leverandørreskontro | 20. | bilagsføring, bank |
| 2 | AGA og forskuddstrekk (oddetallsmåneder) | `lonnsavstemming` | Avstemming av AGA og forskuddstrekk | 10. | a-melding |
| 2 | Mva-kontroll (terminmåneder) | `mva-kontroll` | MVA-kontroll | 25. i måneden før mva-fristen | bank, reskontro, bilagskontroll |
| 3 | Balanseavstemming | `balanseavstemming` | Avstemming balansekontoer | 16. | bank, reskontro, a-melding; i terminmåneder mva levert |
| 3 | Korrigeringer fra avstemmingene (kategori 2) | `periodisering`, `bilagsforing` | – | før nivå 4 | avstemmingene på nivå 2 |
| 3 | Mva-innlevering (terminmåneder) | `mva-innlevering` | MVA-innlevering | mva-fristen | mva-kontroll |
| 4 | Resultat og balanse med sammenligning | `regnskapsrapport` | – | – | nivå 3 |
| 4 | Forklaring av avvik over V (drill-down fra A1–A3) | `avviksanalyse` | – | – | nivå 3 |
| 4 | Rimelighet A1–A3 og hovedtall | `periodeavslutning` | Ferdigstillelse perioderegnskap | – | nivå 3 |
| 5 | Månedsrapport i Tally (utkast; regnskapsfører publiserer) | `periodeavslutning` | Ferdigstillelse perioderegnskap | – | nivå 4 |
| 5 | Periodelås i Tripletex (UI) og månedsavslutning i Tally | `periodeavslutning` | Lukking av regnskapsperiode | – | nivå 4, stoppene |
| 5 | Lukking av Tally-oppgavene | `tally-gjoremal` | alle månedsoppgaver | – | arbeidet er gjort |

Fristen for balanse (16.) kommer før reskontrofristen (20.): en balanse som venter på reskontro, er **Blokkert**, ikke **I fare**.

## Kritisk vei

```
bilagsføring (+ bilag fra kunden) → bankavstemming → reskontroavstemming → balanseavstemming
  → (terminmåned: mva-kontroll → mva-innlevering) → regnskapsrapport og avviksanalyse → månedsrapport → periodelås
```

Den kritiske veien venter som regel på kunden (bilag og kontoutskrifter). Den kortes ned med løpende bilagsføring og bankavstemming
gjennom måneden, faste periodiseringer i kundeinstruksen, mangelliste tidlig (5.–12.) og kjente avvik registrert med «Gyldig til».

## Statusdefinisjoner

| Status | Betyr | Avgjøres av |
|---|---|---|
| Ikke startet | Ingenting er gjort; kan vente på et nivå under | Tally-oppgaven åpen uten kommentar, og `status`-punktet ikke berørt (for eksempel ingen bankavstemming opprettet) |
| Pågår | Arbeid i gang og innenfor fristen | Delvis grønt i `status` (noen måneder lukket), kommentar på oppgaven, utkast lagret |
| Ferdig | Kontrollen er OK eller forklart, og Tally-oppgaven er fullført | `status`-punktet `ok: true` og oppgaven `FERDIG` i `list_tasks` |
| Blokkert | Kan ikke gå videre: nivået under er ikke ferdig, det venter på kunden, eller et stopp står åpent | Avhengigheten i tabellen over; `Krever: kunden`; stopp i en avstemming |
| I fare | Ikke ferdig, og fristen i månedshjulet er passert eller nås ikke | `list_tasks` med `scope: overdue`, eller frist innen to virkedager og nivået under ikke ferdig |

Statustavle per klient: Nivå · Arbeid · Skill · Frist · Status · Blokkert av · Neste steg. På tvers av klienter: én linje per klient
(Klient · Høyeste ferdige nivå · Blokkert/I fare · Neste skill), sortert med I fare først, så Blokkert. Data:
`npm run -s status -- --alle --maaned ÅÅÅÅ-MM --json` og Tally `list_tasks` (`title`, `scope: overdue`, `group_by: klient`).

## Blokkeringer

1. Navngi blokkeringen: hva, nivå, eier (kunden, regnskapsfører, oppdragsansvarlig eller Tripletex-UI) og hva som løser den.
2. Kunden: mangelliste eller Missive-utkast etter ja; kunden purres ikke av Claude.
3. Internt: pek på skillen som løser den, på nivået der den står.
4. Oppdragsansvarlig: stopp fra en avstemming (uforklart differanse, kategori 3 over V) vises med posten og ventes på i chatten.
5. Tally: én kort kommentar med årsaken på oppgaven (`tally-gjoremal`, etter ja). Oppgaven fullføres ikke.
6. Blokkert forbi fristen blir I fare, og løftes til oppdragsansvarlig.

## Avslutningsnøkkeltall

Måles ved hver lukking og står i kommentaren på «Lukking av regnskapsperiode», så trenden kan leses neste måned.

| Nøkkeltall | Definisjon | Kilde | Mål |
|---|---|---|---|
| Dager til lukket | Kalenderdager fra siste dag i M til «Lukking av regnskapsperiode» ble fullført | Tally `get_task` (`handlinger`: tidspunktet oppgaven ble fullført) | ned over tid |
| Føringer etter lukking | Bilag datert i M opprettet etter at M ble lukket | `npm run -s api -- GET /ledger/voucher dateFrom=ÅÅÅÅ-MM-01 dateTo=<D> "fields=number,date,changes(timestamp,changeType)" --sider --client "<klient>"` (CREATE etter lukkedato) | 0 |
| Gjenåpnede perioder | Perioder eller bankmåneder som var lukket ved forrige lukking og er åpne nå | `/ledger/accountingPeriod` (`isClosed`), `status` (bank) mot forrige kommentar | 0 |
| Uforklarte poster | Avstemmingsposter i kategori 3 og uforklarte differanser per S, summert over bank, reskontro og balanse | kommentarene på avstemmingsoppgavene, ellers skillene | ned over tid |
| Forsinkede oppgaver | Månedsoppgaver for M fullført etter fristen | Tally `list_tasks` (frist) og `get_task` (fullført) | 0 |

## Retrospektiv

Etter lukking, høyst fem linjer. Hvert svar som gjelder klienten varig, blir et forslag til kundeinstruksen (`kundeinstruks`, etter ja).

| # | Spørsmål | Typisk endring i kundeinstruksen |
|---|---|---|
| 1 | Hva gikk bra og bør fortsette? | – |
| 2 | Hva tok lengre tid enn ventet, og hvorfor? | «Bilagsføringsregler» (fast konto per leverandør), «Periodiseringer» |
| 3 | Hvilke blokkeringer oppsto, og hvordan unngår vi dem neste måned? | «Mangelliste» (frist, mottaker), «Bank» (kontoutskrift for kontoer uten feed) |
| 4 | Var det overraskelser i tallene som burde vært fanget tidligere? | «Kjente avvik» (med «Gyldig til»), «Periodiseringer» |
| 5 | Hva kan automatiseres eller standardiseres? | fast periodisering, bankregel, frekvens i «Reskontro og balanse» |
