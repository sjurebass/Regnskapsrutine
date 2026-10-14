# Typene – grunnlag, beregning og føring

Utkast – kalibreres mot første klient. Kontonumrene under er **typiske** (NS 4102). Bruk alltid klientens egne: kundeinstruksen («Periodiseringer»,
«Bilagsføringsregler»), så forrige periodes føring av samme post, så kontoplanen (`/ledger/account number=<nr>`). Finnes ingen av delene: spør.
Plus = debet, minus = kredit (som i `manuell.json`). Bilagsdato er siste dag i perioden; tilbakeføring er første dag i neste periode.
Grunnlag for alle: rskl. § 4-1 (opptjening og sammenstilling). Kontrollene står i `docs/foringskontroll.md`.

## Gjør Tripletex det selv? (sjekk først)

| Hva | Slik ser du det | Da |
|---|---|---|
| Periodisering på leverandørbilaget | Posteringer med `amortizationAccount` (`/ledger/posting … "fields=account(number),amount,amortizationAccount(number),amortizationStartDate,amortizationEndDate,voucher(number,year)"`) | Tripletex fordeler månedlig. Kontroller at månedens del er bokført og at 17xx-saldoen er resten. Ingen føring. |
| Avskrivning fra anleggsregisteret | `/asset "fields=id,name,account(number),depreciationAccount(number),acquisitionCost,lifetime,depreciationMethod,depreciationFrom,status,depreciationAmount"` og `/asset/<id>/postings dateFrom=ÅÅÅÅ-MM-01 dateToExclusive=D` | Postering finnes: kontroll (A4). Mangler: **Bare i Tripletex-UI** (SKILL.md steg 6), så les på nytt. 403: registeret kunne ikke leses – les 60xx og 12xx i hovedboken og spør om klienten bruker registeret. |
| Feriepenger og AGA av feriepenger fra lønnskjøringen | Posteringer på 2940 (og 2785) i måneden på lønnsbilag (`voucher(voucherType(name))`) | Kontroll mot grunnlag × sats (L3, `lonnsavstemming`). Ingen føring. |

## Påløpte kostnader

- **Når:** varen eller tjenesten er levert i perioden, fakturaen er ikke kommet: strøm, husleie i etterskudd, regnskap og revisjon, frakt, konsulenttimer.
- **Grunnlag:** avtale, ordre, forbruk, forrige faktura fra samme leverandør (bilagsnummer), e-post fra kunden. Først: er fakturaen allerede bokført?
  (`/supplierInvoice invoiceDateFrom=… "fields=invoiceNumber,invoiceDate,amount,supplier(id),voucher(number)"`) – da ingen avsetning (J7).
- **Beregning:** avtalt beløp × andel av perioden, forbruk × pris, eller snitt av de siste tre fakturaene (vis tallene). Aldri et rundt anslag uten formel.
- **Føring:** + kostnadskonto (som forrige faktura fra leverandøren) / − påløpt kostnad (typisk 2960). Mva-kode 0. Har klienten fradragsrett, føres
  beløpet eks. mva (fradraget kommer med fakturaen, mval. § 15-10); uten fradragsrett inkl. mva.
- **Tilbakeføring:** ja, første dag i neste periode. Fakturaen føres som vanlig (`bilagsforing`), og tilbakeføringen nuller avsetningen.

## Forskuddsbetalte kostnader

- **Når:** fakturaen dekker flere måneder: forsikring, lisenser og årsabonnement, husleie betalt forskuddsvis, serviceavtaler.
- **Grunnlag:** fakturaen (bilagsnummer) med periode fra–til; planen står i «Periodiseringer». Uvesentlige poster: spør om de skal kostnadsføres
  direkte, og lagre svaret i kundeinstruksen.
- **Beregning:** beløp eks. fradragsberettiget mva / antall måneder. Siste måned tar resten, så posten på 17xx går i null.
- **Føring:** + kostnadskonto / − forskuddsbetalt kostnad (typisk 1700–1749). Mva-kode 0. Ble fakturaen ført rett på kostnad: først
  + 17xx / − kostnad for de månedene som ikke er brukt, deretter månedlig som over.
- **Tilbakeføring:** nei. Utløpt, oppsagt eller endret avtale: kostnadsfør resten og oppdater «Periodiseringer».

## Avskrivninger

- **Klient med anleggsregister:** avskrivningen kjøres i Tripletex-UI og kobles til anlegget. Claude kontrollerer: lineær månedsavskrivning =
  (kostpris − restverdi) / `lifetime` (måneder); 60xx i måneden = sum per anlegg; status `CORRECTION_NEEDED` eller `MISSING_INFO` meldes.
- **Klient uten register** (står i kundeinstruksen): manuelt bilag + avskrivningskostnad (typisk 6000–6020) / − anleggskonto (12xx, eller egen konto for
  akkumulerte avskrivninger hvis klienten bruker det). Mva-kode 0. Avskrivningsplanen (kostpris, dato, levetid, restverdi) er vedlegget.
- **Tilgang i perioden:** kostpris fra 30 000 kr og levetid minst 3 år aktiveres (sktl. § 14-40; rskl. § 5-3): ompostering fra 65xx til 12xx med
  originalbilaget, og nytt anlegg i registeret (Tripletex-UI eller eget ja). Avskrivning fra måneden etter tilgang, om ikke kundeinstruksen sier annet.
- **Tilbakeføring:** nei.

## Lønnsperiodiseringer

Bare summer per konto. Ikke hent `/employee` eller `/salary`; grunnlaget er lønnsbilagene i hovedboken og samlet lønnsgrunnlag fra kunden.

- **Feriepenger** (når lønnskjøringen ikke avsetter selv): grunnlaget i perioden (lønnskontoer som gir feriepenger, typisk 5000–5099 uten
  feriepengene selv) × sats fra «Lønn» (10,2 % eller 12 % ved avtalt femte ferieuke; tillegg for ansatte over 60). + feriepenger (typisk 5020) /
  − skyldige feriepenger (typisk 2940). AGA av avsetningen × sonesats: + AGA-kostnad / − påløpt AGA av feriepenger (typisk 2785). Ingen tilbakeføring.
- **Påløpt lønn** (timelønn, overtid eller bonus for perioden som utbetales senere): + lønn (typisk 5000) / − skyldig lønn (typisk 2930), og AGA
  + 5400 / − påløpt AGA (typisk 2780). Tilbakeføres første dag i neste periode, når lønnskjøringen bokfører lønnen. Bonus bare med avtale.
- **Pensjon** (premie betalt kvartalsvis eller årlig): som forskuddsbetalt kostnad. Avstemming mot innrapportert er `lonnsavstemming`.

## Inntektsperiodisering

- **Forskuddsfakturert** (abonnement, årsavgift, forskudd på prosjekt): + inntektskonto / − forskuddsbetalt inntekt (typisk 2965 eller 2970) for den delen
  som gjelder senere perioder; deretter månedlig + 29xx / − inntekt. Mva-kode 0 (utgående mva fulgte fakturaen). Ingen tilbakeføring.
- **Opptjent, ikke fakturert** (timer, milepæl, levert vare): + opptjent inntekt (typisk 1530) / − inntektskonto. Grunnlag: fakturareserven
  (`/project/batchPeriod/invoicingReserveByProjectIds`, P1) eller kundens oversikt. Mva-kode 0. Tilbakeføres første dag i neste periode, når fakturaen kommer.

## Omposteringer og korrigeringer

- **Ompostering** (feil konto, avdeling eller prosjekt; fra observasjonskonto 1370/7799 når bilaget er kommet): + riktig konto / − feil konto, samme beløp,
  med originalbilagets nummer i beskrivelsen. Bare med bilaget for akkurat den transaksjonen (`npm run -s dokument -- --client "<klient>" --bilag <nr-år> --ut <mappe>/dok`).
- **Korrigeringsbilag** (originalen kan ikke endres: bank- og OCR-bilag gir 422, eller perioden er låst): motpostering i åpen periode med henvisning til
  originalen. Hele bilaget feil: reversering etter samme ja, tørrkjøring først (som i `bilagskontroll`):
  `npm run -s api -- PUT "/ledger/voucher/<bilag-id>/:reverse" date=ÅÅÅÅ-MM-DD --client "<klient>"`, og det riktige bilaget i planen. Lønnsbilag kan ikke reverseres.
- **Mva:** feil kode i en levert termin rettes i åpen termin, med regnskapsførerens ja og beløpet nevnt (`docs/foringskontroll.md`, «Godkjenning»).
- **Tilbakeføring:** nei.
