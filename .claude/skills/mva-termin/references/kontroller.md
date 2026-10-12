# Mva-avstemming: kontrollkatalog

> **Merk (oktober 2026):** Designdokument fra september 2026. `klientprofil.md`, `kjente-avvik.md`, `logg.md` og kundemappene `<Kunde>/<år>/…` er erstattet av kundeinstruksen i Tally (skillen `kundeinstruks`), og leveranser lagres i Tally eller avstemmingsmodulen. `npm run mva`/`modul` og `%LOCALAPPDATA%\silfer-mva` gjelder bare CLI-hurtigveien. Driftsflyten står i `SKILL.md`.

Katalogen samler kontrollene fra de sju områdene. Rettelsene fra verifiseringen og kritikerens manglende kontroller (MX) er innarbeidet. Endepunktene står i `endepunkter.md`, og orkestreringen står i `arbeidsflyt.md`.

## Felles definisjoner

**Datoer:**
- **T_start / T_slutt**: terminens første og siste dag, fra terminobjektet (F3.3). Ingen område regner termin selv.
- **D** = T_slutt + 1 dag. Tripletex bruker eksklusiv til-dato.
- For BALANCE er D = periodens endDate fra periodsOverview. endDate er allerede eksklusiv (K0). BALANCE er **månedlig**, så én mva-termin har to BALANCE-perioder. D for den siste er lik terminens D.
- **Termintilhørighet** avgjøres av `posting.date`, ikke `voucher.date` (K0).
- **Beløp fra Tripletex' mva-beregning** (vatTermAmount, `>vatTerm`, `/vatReturns/{id}`, overview) er hele kroner **avkortet mot null per kode**, ikke avrundet (K0). Egne summer avkortes på samme måte før sammenligning.

**Vesentlighet** (én definisjon, lagres i klientprofil.md og sendes med terminobjektet til alle agentene):

| Grense | Standard | Bruk |
|---|---|---|
| `vesentlighet_mva` (V_mva) | max(1 000 kr, 1 % av \|netto mva i T\|) | Portbeslutning (blokk) |
| `mva_grense_bilag` | 100 kr | Én post. Beløp under grensen summeres per kontroll, og summen vurderes mot V_mva. |
| `stoygrense` | 100 kr | Lister i reskontro og bank |
| `merknad_grense_tilgode` | 50 000 kr | N3 |
| `vesentlighet` (omsetning) | Klientprofilens tall | Bare F2.9, T7 og saldoavstemming i reskontro og bank |

- Bankposter uten kjent mva: mva oppgis som intervall 0–25/125 av beløpet. Profilens hovedsats gir punktestimatet.

**Alvor:**
- **STOPP**: hard stopp for klienten. Kan ikke overstyres.
- **BLOKK**: blokkerer opprettelse av meldingen til posten er rettet, akseptert av Sjur med begrunnelse, eller flyttet til neste termin eller korrigert melding. Krever at funnet er bekreftet (se arbeidsflyt, verifisering).
- **FORKLAR**: skal ha kommentar i modulen eller linje i kjente-avvik.md.
- **INFO**: vises bare som antall.

Faste BLOKK-kategorier uansett beløp (når bekreftet):
- ensidig omvendt avgiftsplikt (MO3)
- bekreftet dublett (MD1)
- endring i levert termin (ET1–ET3)
- kode 52 mot norsk kunde (EX1/EX4)
- fradrag hos leverandør uten mva-rett (MF5)
- fradragsforbud (MF1/MF2)
- uforklart bankdifferanse (BK2)
- hull i kontoutskrift (BK6)
- mva på periodiseringsbilag (MX8)
- mva på diett og km-godtgjørelse (MX10)
- fradrag på husleie uten mva (MX6)

**Utføres av:** S = deterministisk skript, A = skjønnsagent (bare på flaggede poster), M = Sjur/menneske.

**Modul:**
- *VAT-linje* = kommentar eller vedlegg på linjen i mva-avstemmingen. referenceId er trolig vatTypeId, men ikke verifisert. Skrives etter synk i pakke 2.
- *BALANCE-linje* = documentedBalance, status, kommentar og vedlegg på kontoens linje i terminens balanseavstemming (pakke 1).
- *Del A* = regnskapskorrigering i pakke 1.
- *Excel* = arkfanen i fallback-arbeidsboken.

**Id-prefiks** (hindrer nøkkelkollisjon med bank.py og reskontro.py i kjente-avvik.md):

| Prefiks | Område |
|---|---|
| F | Forutsetninger |
| RK | Reskontro |
| BK | Bank |
| M0/MK/MS/MT/MD/MI/MO/MF | Bilag A |
| KN/TP/UT/KV/ET/EX | Bilag B |
| T | Terminavstemming |
| SK | Skattekonto |
| N | Merknader |
| IN | Innsending, betaling og etterarbeid |
| MX | Nye kontroller fra kritikeren |

Eksisterende nøkler i kjente-avvik.md (B1–B5, R1–R6) må migreres med et eget skript før bank.py og reskontro.py erstattes.

**Felles funnformat** (utvider `tools/modeller.Funn`):

```
{nokkel, kontroll, omraade, punkt, termin_berort, retning (UTG|INNG|GRUNNLAG|BALANSE),
 mva_effekt (+ = mer å betale), grunnlag_effekt, bilag[] (voucherId, nr/år), vatTypeNr, konto,
 kilde_endepunkt[], alvor_foreslatt, alvor_endelig, verifisering (BEKREFTET|SANNSYNLIG|AVVIST),
 kjent (ja/nei), eier, modul_ref {type VAT|BALANCE|BANK, referenceId}, forslag (RETT|FORKLAR|
 NESTE_TERMIN|KORRIGERT_MELDING|KUNDE), kommentarutkast (≤1 setning, uten navn)}
```

- `nokkel` = sha1(kontroll|konto|referanse|round(beløp)).
- Et funn der beløpet endres, får ny nøkkel og dukker opp igjen.
- Kjente avvik kan dempe BLOKK bare når linjen har akseptert_av=Sjur og gyldig_til er innen 12 måneder.

---

## Eierskap og sammenslåtte kontroller

Samme forhold rapporteres én gang. Ved dedup er nøkkelen (voucherId/banktransaksjon, kontrollfamilie). De andre områdene leser eierens resultat.

| Forhold | Eier | Sammenslått / leverer data |
|---|---|---|
| Datagrunnlaget = Tripletex' beregning | M0 | IN5 (inngår) |
| Hovedbok = beregnet melding per kode | T1 | IN5, M3 i mva.py (erstattes) |
| Tripletex' forhåndssjekk (validateCreate) | T0 | IN4. F1.3 bruker incompleteVouchers. |
| Manuelle føringer på mva-kontoene | T3 | MK2 |
| Oppgjørsbilag = melding | T5 | IN9 |
| Validering av utkast | T14 | IN8 |
| Tre-veis etter synk og klar til :complete | T12/T15 | IN12 |
| Endringer i levert termin | ET1 (ET2, ET3) | T13, IN23, RK10 |
| Faktura datert i tidligere termin, bokført i T | MT2 | ET4, RK10 del 1 |
| Dublett-leverandørfaktura | MD1 | RK6 leverer bare 2400-effekten |
| Kreditnota (mva og kobling) | KN1/KN3 | RK11 leverer bare saldoeffekten |
| Tap på krav (mva) | TP1–TP3 | RK13 leverer bare reskontroeffekten |
| Levert ikke fakturert / sen fakturering | F2.1 | RK17 |
| Ubehandlet innboks/attestering | F1.1/F1.4 | RK9 del C, BK18 (bare forslag) |
| Fradrag før fakturadato | MT3 | RK9 del B |
| Bankposter uten bilag | BK3 | F1.6 |
| Betaling av forfalte terminer bokført mot 2740 | T10 | BK11 (datakilde), M1 i mva.py |
| Paymentstatus for tidligere terminer | SK1 | M6 i mva.py |
| Åpne mva-krav på skattekontoen | SK2 | BK13 |
| Tilbakebetaling mottatt | IN20 | BK12 |
| Kontonummer for tilbakebetaling bekreftet | IN19 | MX20 (regel lagt inn i IN19) |
| Dekning og betalingskonto | IN15 | BK19 |
| Stor tilbakebetaling (merknad) | N3 | IN7, SB1 (grunnlag) |
| Fortegn og spesifikasjonslinjer | N1/N2 | SB2 |
| Uvanlige linjer | N4 | SB1 |
| Termin og tilstand før opprettelse | F3.3/F3.7 | IN2 |
| A konto og forskuddsfaktura | MX1 | RK14 (kundeside, bare info) |
| Fingerprint og endringer etter kontroll | F0.3 | MT5 |
| Forfalte leverandørfakturaer | RK5 | MT6 |

---

## A. Forutsetninger (punkt 1, 2, 3 og port)

| ID | Pkt | Ser etter | Logikk | Terskel | Falske pos. / filter | Alvor | Utf. | Modul |
|---|---|---|---|---|---|---|---|---|
| F0.1 | 1–3 | Hva de navngitte klientene har i innboks, attestering, reiser/utlegg og til gjennomgang, pluss status og frist | /clientTasks/* (+remits) og /todoList/vatReturnsSection med `clientCompanyIds`. Står telleren på 0, hoppes detaljkallene over, men inboxCount dobbeltsjekkes. | – | Tellerne er ikke datoavgrenset og kan henge etter. De er aldri alene grunnlag for grønt. | INFO | S | – |
| F3.1 | 3 | Feil klient eller byrå, feil id-kobling, manglende tilgang, modul eller Excel | connect-id = Client.id (kunde-id), org.nr. stemmer, customerCompanyId = klientkontekstens companyId. Deretter permissions, verifyModule (cache per byrå) og periodsOverview for VAT og BALANCE. Utfall MODUL / DELVIS / EXCEL / STOPP. | Binær | permissions gjelder API-brukeren. En COMPLETED avstemming er ikke feil, men krever :unlock (egen bekreftelse). | STOPP | S | Avgjør modus |
| F3.2 | 3 | Slettet fra Mva-registeret, VAT_APPLICANT, VAT_COMPENSATION, profil ulik registrene | Sammenligner vatSettings.vatRegistrationStatus, clientOverview.vatRegistered og Brreg (`registrertIMvaregisteret` og dato, via leverandor.js) med profilen. Ulikt resultat gir STOPP. APPLICANT eller COMPENSATION gir STOPP og annen flyt. | Binær | Brreg oppdateres sent. Sjur oppgir dato, som føres i kjente-avvik. | STOPP | S | logg.md, klientprofil |
| F3.3 | 3 | Feil termintype, termin som ikke finnes, termintype endret i året | vatTermSizeSettings (alle termSize-verdier) mot Skatteetatens `dueDate` og start/slutt i vatReturnsOverview og periodsOverview, og mot profilen. Avvik gir STOPP. Gir terminobjektet {reportType[], term, start, sluttEksklusiv, dueDate, fase}. | Binær. Info når avgiftspliktig grunnlag (3/31/33/5/52) siste 12 mnd > 1 mill. og klienten har årstermin, eller er under grensen og kan søke. | Feilregistrerte rader. Sjur bekrefter én gang, og svaret lagres i profilen. | STOPP | S | – |
| F3.4 | 3 | Alminnelig næring og primærnæring, der én melding glemmes | multipleIndustries, reportTypes, clientOverview og salesmodules mot profilens `mva_meldinger`. Hver reportType kjøres som eget løp. | Binær | Primærflagg som står igjen etter at primærnæringen er avsluttet | STOPP | S | vatReportType i context |
| F3.5 | 3 | Aktiverte koder passer ikke med virksomheten | Flaggkart fra VatSettings (hasVatInImport = 14/15/20/21, ikke 81–85). Kodene slås opp i /ledger/vatType. Profil ja og flagg av gir avvik. Flagg på, bruk siste 12 mnd og profil nei gir avvik. Flagg på uten bruk gir INFO. | Binær per område | Engangstransaksjoner | FORKLAR | S | Forslag til klientprofil |
| F3.6 | 3 | Utleie med mva uten frivillig registrering, forholdsmessig fradrag ikke satt opp | Brreg `frivilligMvaRegistrertBeskrivelser` mot profilen. 3600–3699 med kode 3 uten registrering gir funn. Relative koder mot profilens nøkkel. | Utleie: alle beløp. Nøkkel ±1 pp. | Boligutleie (unntatt) | FORKLAR (BLOKK for utleie med mva uten registrering) | S | VAT-linje kode 3 / fradrag |
| F3.7 | 3 | Terminen er allerede levert, meldingen er opprettet, forrige termin er ikke levert | Faseparameter. **FØR_INNSENDING**: RECEIPT_RECEIVED eller MANUAL_DELIVERY gir STOPP og ruting til punkt 9. INSTANCE_CREATED uten kvittering gir avvik (meldingen må beregnes på nytt). Forrige termin ikke levert gir avvik. **ETTER_INNSENDING**: kvittering er forutsetningen. | Binær | Manuell levering i Altinn | STOPP (fase FØR) | S | – |
| F3.8 | 3 | Konkurs, avvikling, tvangsoppløsning eller sletting | Brreg-svaret. Org.form ≠ AS gir INFO. | Binær | – | STOPP | S | – |
| F3.9 | 3 | Perioder som mangler eller allerede er låst | /ledger/accountingPeriod, matchet på start. Låst betyr `isClosed=true`. K0 viste at klienter låser per år: isClosed=false for leverte terminer i inneværende år er normalt og gir INFO. isClosed=false i et tidligere, avsluttet år gir varsel. | Binær | Låst med vilje | INFO | S | – |
| F1.1 | 1 | Ubehandlede dokumenter i innboksen: fradrag mangler, salgsgrunnlag mangler, udaterte dokumenter, duplikater | inboxCount = 0 gir OK. Ellers blas **hele** inboxFiltered. Dato = invoiceDate ?? voucher.date ?? receivedDate. Klassene er I_TERMIN, FØR (til MT2/ET), ETTER og UKJENT. INVOICE og REPLAYABLE_VOUCHER tas med. Spam, REMINDER_SPECIFICATION og duplikater holdes utenfor. Utenlandsk leverandør med vatAmount 0 gir grunnlag for omvendt avgiftsplikt (til MO1). Dokumentdato i T og mottatt før innsending betyr at dokumentet skal bokføres før innsending. | ≥1 gir avvik. Σ mva ≥ V_mva gir BLOKK. | Ikke-bilag, EHF+PDF, `innboks_ignorer`, kjente-avvik på voucherInboxId | BLOKK | S | VAT-linje fradrag/utgående |
| F1.2 | 1 | Feilet EHF-import, EHF som ikke er sendt til hovedbok | filterType ERROR_EHF_IMPORT med dato ≤ T_slutt gir BLOKK. canBeSentToLedger i T gir avvik. | ERROR: alle | Duplikat EHF | BLOKK | S | Handlingsliste til Sjur |
| F1.3 | 1 | Kladder, ikke godkjente bilag, direkteposteringsutkast | validateCreate.incompleteVouchers (fra T0) er primærtellingen. >nonPosted (T_start−12 mnd til T_slutt+1 mnd) og directposting/draft gir detaljene. Mva per vatType.number, delt inn og ut. Snudd avregning netto. | ≥1 gir avvik. Mva ≥ V_mva gir BLOKK. | Periodiseringskladder frem i tid, kladd som er duplikat av bokført bilag | BLOKK | S | VAT-linje |
| F1.4 | 1 | Fakturaer til attestering som ikke er bokført | /attestation/companyModules og voucherInbox/context (eksplisitte fields). forApproval(showAll), attestations(ATTESTATION_DELIVERED) og inboxAttestationCount, **dedup på voucherId**. | Ikke bokført mva ≥ V_mva gir BLOKK | Bevisst holdt tilbake ved tvist | BLOKK | S | VAT-linje, utkast til kundebeskjed |
| F1.5 | 1 | Utlegg og reiser med mva som er levert men ikke godkjent, eller godkjent men ikke bokført | Bare når telleren > 0. /travelExpense per state uten personfelt. Bare antall og summer. | DELIVERED+APPROVED ubokført ≥ V_mva gir BLOKK. OPEN gir INFO. | accountingPeriodVATClosed, diett uten mva | FORKLAR | S | VAT-linje (uten persondata) |
| F1.7 | 1 | Fakturaer i dokumentmottaket, bilag til gjennomgang | documentReception(onlyUnread, endDate inkl.) og forReviews | – | Kontrakter og brev | INFO | A | Nevnes i melding |
| F2.1 | 2 | Levert, ikke fakturert. Faktura utstedt for sent. | Ordre med isClosed=false og **deliveryDate + 1 mnd ≤ T_slutt**: faktura skulle vært utstedt i T (mval. § 15-9). Levering i siste måned gir INFO og sjekkes mot fakturaer til og med T+45 d. Faktura i T med levering mer enn 1 mnd før T_start: mva hører til leveringsterminen, og saken går til ET-eier (punkt 9). | Mva ≥ V_mva gir BLOKK. Ordre > 1 000 kr gir avvik. | deliveryDate=orderDate, tilbud/mal, samlefaktura, `ordre_leveringsdato_paalitelig=nei` gir INFO | BLOKK | S | VAT-linje 3/31/33 |
| F2.2 | 2 | Fakturautkast, prosjekt klar til fakturering | preliminaryInvoice og isReadyForInvoicing. invoiceReserve brukes som ruting først. | ≥1 i T gir avvik | Utkast for neste termin | FORKLAR | S | VAT-linje utgående |
| F2.3 | 2 | Abonnement eller husleie ikke fakturert | Forventede mot faktiske fakturaer. For pilot sjekkes hasMigratedSubscriptions (dobbelttelling). | Manglende periode gir avvik | Oppsagt, forskudd | FORKLAR | S | VAT-linje utgående |
| F2.4 | 2 | Opptjent, ikke fakturert på prosjekt | invoicingReserveByProjectIds (ikke /timesheet) | Reserve ≥ V gir avvik. Mva ≥ V_mva uten fastpris gir BLOKK. | Fastpris, interne prosjekter | FORKLAR | A | VAT-linje. 1530 på BALANCE-linje. |
| F2.5 | 2 | Oppgjørskonto (Vipps, Stripe, Zettle, kasse) med feil saldo | Kontoer fra profil og navne-regex. IB, bevegelse, UB og dager uoppgjort. | Negativ UB ≥ V gir BLOKK | Helg, Stripe-reserve, månedsoppgjør | FORKLAR | S | BALANCE-linje + oppgjørsrapport som vedlegg |
| F2.6 | 2 | Hull i oppgjørene, nettoføring | Kalender over 26 uker. Utbetaling ført direkte mot 3xxx. Gebyrkonto uten bevegelse. | Anslått manglende mva ≥ V_mva gir BLOKK | Ferie, sesong, samleutbetaling | BLOKK | S | BALANCE-linje, VAT-linje ved aksept |
| F2.7 | 2 | Dager uten kasseoppgjør, kasse i minus | Bare når profilen har kassesystem=ja | Anslått ≥ V | Ukentlig Z-rapport | FORKLAR | S | BALANCE kasse + Z-rapport |
| F2.8 | 2 | Nye salgskanaler profilen ikke kjenner | clientsModules, /company/modules, regex og bankinnbetalinger fra formidlere. K0: addon gir bare katalogen og salesmodules gir 403, så ingen av dem brukes. | Ny kilde med bevegelse | Addons som ikke brukes | FORKLAR | S | Forslag til profil |
| F2.9 | 2, 13 | Måned uten omsetning, uforklart endring | balanceSheet 3000–3999 for T, T−1, fjoråret og per måned. Hovedbok minus fakturert minus oppgjør. | 30 % og V | Sesong | INFO | A | Grunnlag for N-merknad |
| F0.2 | port | Portbeslutning | Se arbeidsflyt (P2) | – | – | – | S+A | – |
| F0.3 | 1 | Endringer etter kontroll | Fingerprint: Σ grunnlag og Σ mva per vatType.number, incompleteVouchers, nonPosted changedSince, inboxCount, siste changes-tid og bankdekning. Kjøres ved P3, rett før Opprett og før :complete. | ≥1 kr eller nytt bilag i T | Bilag datert i neste termin | BLOKK | S | Stopper skriving |

## B. Reskontro (Sjurs «kunde-/leverandørreskontro avstemt» og punkt 7)

| ID | Pkt | Ser etter | Logikk | Terskel | Falske pos. / filter | Alvor | Utf. | Modul |
|---|---|---|---|---|---|---|---|---|
| RK0 | Resk. | Reskontrokonti utenfor 1500/2400, poster uten motpart, motpart på annen balansekonto | Reskontrokonti = isCloseable ∪ postingRules ∪ ledgerAccount (ikke ledgerType). Motpartsløse linjer. IB- og konverteringsposter merkes automatisk (otherPostingOverview OPENING_BALANCE). | ≥1 kr | Åpningsbalanse, øreavrunding | FORKLAR | S | BALANCE 1500/2400 |
| RK1 | Resk. | Kundereskontro ≠ hovedbok per D | Σ openPost(date=D, accountId) mot balanceSheet UB (dateTo=D), der D = BALANCE-periodens endDate. Det gir én D per måned. K0: openPost er et historisk snitt, og summen skal gi diff 0. Kontofilter er påkrevd. Diagnose: RK0, closeGroup.date ≥ D (lukket senere), /ledger/openPost som kryssjekk. | \|diff\| < 1 kr | Faktoring (isFactoring), konvertering | FORKLAR | S | BALANCE 1500: documentedBalance = Σ åpne, status, vedlegg |
| RK2 | Resk. | Leverandørreskontro ≠ hovedbok | Som RK1. **supplierSubLedger er ikke fasit** (K0: openAmount er dagens restbeløp). Den brukes bare som sekundær diagnose, med `openPostingsAsOfDate=D`, `endDate=D−1` og totalDebit − totalCredit, og et avvik der gir ikke funn alene. >supplierBalance med dateFrom = årets start. | < 1 kr | Konsernleverandør på egen konto | FORKLAR | S | BALANCE 2400 |
| RK3 | Resk., 7 | Kunde i kredit, leverandør i debet | Klassifiser først med otherPostingOverview.type (UNKNOWN_PAYMENT, ADVANCED_VOUCHER). Dobbeltbetaling bare ved samme KID eller fakturanummer. | Listes ved ≥100 kr. Avvik ved ≥ V eller eldre enn 60 d. | Avtalte forskudd | FORKLAR | S | Kommentar per vesentlig motpart |
| RK4 | Resk., 7 | Forfalte kundefordringer, poster eldre enn 12 mnd | Aldersfordeling. Hovedkilde er /reminder med type NOTICE_OF_DEBT_COLLECTION/DEBT_COLLECTION. /voucherStatus er tillegg. Oppgi hvilken kilde som ble brukt. | >365 d ≥100 kr gir avvik. >90 d ≥ V går til tapsvurdering. | Purrestopp, offentlige kunder | FORKLAR | S | BALANCE 1500 |
| RK5 | Resk. | Forfalte leverandørposter, betalt utenom reskontro (dobbel kostnad), leverandør i konkurs med debet | Samme leverandør og KID på bankposteringen (ikke bare samme beløp). Brreg-status fra leverandørindeksen. Dekker MT6. | >60 d ≥ V | Tvist, autotrekk | FORKLAR | S | BALANCE 2400 |
| RK7 | Resk., 7 | Ukoblede innbetalinger, utbetalinger og kreditnotaer | Eksakte 1:1-par med samme KID/fakturanummer eller beløp. 1:n foreslås bare. | Alle eksakte | Delbetaling, valuta | INFO | S | Utligningsforslag i del A |
| RK8 | Resk. | Dubletter i kunde- og leverandørregisteret | Grupper på orgnr. Privatpersoner sammenlignes aldri på navn. | Alle | Bevisst separate kort | INFO | S | – |
| RK9 | Resk. | Cut-off-effekt på 2400 | Faktura med fakturadato ≤ T_slutt som ikke er bokført gir for lav 2400. Mva-delen eies av MT3 og F1.1/F1.4. | ≥ V | Sent mottatt | FORKLAR | S | BALANCE 2400 |
| RK12 | 7 | Kandidater for konstatert tap | Forfalt >90 d, purring/inkasso. Konkurs: internal invoiceOverview.brregStatus (kodene er ikke dokumentert), deretter leverandor.js-hjelperen (bare orgnr, **lagres ikke i indeksen**). Konstatert tap etter mvaforskr. § 4-7-1. | Konkurs ≥ V uten tapsføring | Betalingsavtale, betalt etter D | FORKLAR | A | BALANCE 1500. Tapsføring går via TP1 og del A. |
| RK14 | Resk. | Kundeforskudd og leverandørforskudd | Kundeforskudd uten faktura: INFO (ADVANCED_VOUCHER). Leverandørforskudd med fradrag uten faktura: BLOKK. A konto-faktura uten mva: se MX1. | Forskudd ≥ V eller eldre enn 60 d | Depositum, årsabonnement | FORKLAR | A | Kommentar |
| RK15 | Resk. | Mva-kode på reskontrolinje, gjeld med leverandør på annen balansekonto | vatType.number ∉ {0, null} på reskontrokonti. Kontrollen blokkerer først når en grunnlinje er etablert på første klient. | Alle | Systemgenererte linjer, 2960 med leverandørdimensjon | BLOKK | S | Del A |
| RK16 | Resk. | Tripletex' egne avvik | Bare når profilen har `anomalies_aktiv=ja` (K0: clientsOverview og context gir 403). Da hentes /anomalies/aggregate per status (UNRESOLVED, UNDER_REVIEW) fra T_start til kjøredato, filtrert på voucher.date. Uten flagget betyr 0 eller tomt «ukjent». Inkluderer VENDOR_VAT_NUMBER og CUSTOMER_VAT_NUMBER. | Alle | Allerede dekket av R-kontrollene | INFO | S | Anomali lukkes bare etter ja |
| RK18 | Resk. | Åpne poster i valuta | amount mot amountCurrency × kurs per T_slutt. Rest med amountCurrency=0. | Kursdiff ≥ V (årsslutt). Rest ≥100 kr. | Normal kursbevegelse | INFO | S | Kommentar ved årsslutt |

## C. Bank (Sjurs «bankkonto avstemt»)

| ID | Pkt | Ser etter | Logikk | Terskel | Falske pos. / filter | Alvor | Utf. | Modul |
|---|---|---|---|---|---|---|---|---|
| BK1 | Bank | Måneder til og med T_slutt som ikke er lukket, avstemming som mangler, ny konto, måned klar til lukking | Ett GET /bank/reconciliation (alle konto- og periode-id-er, med approvable) + /balanceSheet. state hentes bare for åpne eller manglende måneder. K0: `isReadOnly` betyr at en senere måned er lukket, og `isApprovableIncomplete` er også true uten avstemming og med saldo 0, så ingen av dem er avviksflagg alene. Kontoutvalget kan ikke bygge på `requireReconciliation`, fordi den kan være false på alle kontoer. «Klar til lukking» gir et skriveforslag. | Alle måneder lukket | Statisk saldo, `bank_arlig`, skattetrekkskonto (BK14) | FORKLAR | S | Lukking i klientens bankavstemming (pakke 1). BALANCE 19xx. |
| BK2 | Bank | Saldo i bank ≠ saldo i hovedbok | diff = ledgerAccountOutBalance − bankStatementOutBalance (state, = balanceOutDifference, verifisert i K0). bankOut=null betyr at diff = saldo i hovedboken (ingen kontoutskrift). En BALANCE-linje på 19xx med documentedBalance ≠ null og difference = 0 betyr «bank lukket og stemmer». Forklart del = Σ uavstemte hovedboksposter − Σ uavstemte banktransaksjoner, kumulativt til og med T_slutt. Fallback: kontoutskrift eller bankAccountClosingBalanceCurrency mot /balanceSheet (NOK) eller /ledger (valuta). >balance brukes bare når bookedDate = onDate. | \|uforklart\| ≥ 0,01 | Valuta målt i NOK, transaksjoner siste dag | BLOKK | S | BALANCE 19xx + Tripletex' PDF-eksport |
| BK3 | Bank, 1, 2, 5, 7 | Banktransaksjoner i T uten bilag | CSV filtrert på dato og deduplisert. Klasser: overføring, finans, skatt, NAV, **betaling av åpen kundefaktura** (±1 kr mot 1500 / OUTGOING_INVOICE_WITHOUT_KID), **betaling av åpen leverandørfaktura** (INCOMING_INVOICE_MANUALLY_PAID), mulig omsetning, refusjon, tjeneste fra utlandet (flagg VOEC-mva: verken fradrag eller 86), mangler bilag, lønn/privat, ukjent. Mva oppgis som intervall. | Mulig omsetning + ukjent med mva ≥ V_mva, eller én post ≥ 10 000 kr, gir BLOKK | Klareringskonti (`bank_motparter`), timing ved månedsskifte | BLOKK | S (+A for ukjent) | VAT-linje. Kundeliste = Tripletex' OPEN_TRANSACTIONS-eksport. |
| BK4 | Bank, 6 | Uavstemte hovedboksposter på bank (dobbelt fradrag, dobbel betaling) | Match beløp ±1 kr og dato ±30 d mot 2400 og fakturaer, uavhengig av om leverandør er satt | Poster med mva: alle. Øvrige ≥ V. | Betaling siste dag, AutoPay som venter | FORKLAR | S | Del A **før** banklukking |
| BK5 | Bank, 9 | Måned lukket med umatchede transaksjoner | Lukkede måneder fra BK1 hentes med /bank/reconciliation/{id} og sjekkes for matched=false. closedWithUnmatched brukes bare som ja/nei per konto. | ≥1 kr | TRANSFER_ENTRIES | FORKLAR | S | BALANCE 19xx |
| BK6 | Bank | Hull i kontoutskrifter, overlapp, utløpt samtykke | /bank/statement: hull >4 d, dekning mangler, overlapp. agreements (updateBalance=false), ztl lastUpdated og hasValidConsent. Ved 403 regnes kontrollen som delvis kjørt. | Hull eller manglende dekning gir BLOKK | Helg, vedlikehold. Kjøres tidligst 2–3 bankdager etter T_slutt. | BLOKK | S | Samtykke fornyes med BankID av Sjur |
| BK7 | Bank | Konto uten feed (kredittkort, sparekonto, depositum) | Krever MANUAL-avstemming eller BALANCE-linje med kontoutskrift | Kort- eller transaksjonskonto med bevegelse gir BLOKK | `bank_arlig`, sperret depositum | FORKLAR | M | BALANCE-linje + kontoutskrift |
| BK9 | 9 | Åpne bankposter i en rapportert termin, avstemming gjenåpnet etter levering | Rapportert = RECEIPT_RECEIVED eller MANUAL_DELIVERY. changelog REOPENED/UPDATE/DELETE etter deliveryStatus.time. | Mva-kategori, alle beløp | LOCKED eller CREATE alene gir INFO | FORKLAR | S | VAT-linje i T, punkt 9 |
| BK10 | Bilag, 6, 11 | Direkte- og autoposteringer med mva | (a) fradrag uten dokument, (b) kode på konto uten mva, (c) bilagsdato ≠ fakturadato i en annen termin (fakturadato styrer, ikke bankdato), (d) ADJUSTMENT ≥1 000 kr | (a)–(c): alle | Gebyr med kode 0 | FORKLAR | S | VAT-linje, rettes før banklukking |
| BK14 | 12 | Skattetrekkskonto | Saldo mot 2600 (fra lønnsområdet). Feilbruk, f.eks. mva betalt fra skattetrekkskontoen. | Saldo < skyldig trekk | Bankgaranti | FORKLAR | S | BALANCE-linje |
| BK15 | Bank, 4, 5 | Valutakonto | Differanse målt i kontoens valuta. Utgående betalinger sendes til MO- og MI-kontrollene. | 0,01 i valuta | Kursdifferanse i NOK | FORKLAR | S | BALANCE 19xx |
| BK16 | 2 | Interimskonto eller ukjent innbetaling som kan være omsetning | defaultInterimAccount, profil og INTERMEDIATE_ACCOUNT. otherPostingOverview blas og filtreres på UNKNOWN_PAYMENT/OPEN. | Mva ≥ V_mva gir BLOKK | Bevisst klareringskonto | BLOKK | S | BALANCE interim + VAT kode 3 |
| BK17 | Bank | Tripletex-forslag som venter, direktepostering-utkast | internal/match (approved=false), autoposting PENDING, directposting/draft | Alle | Feil motkonto | INFO | S | Gruppert i pakke 1 |
| BK18 | 1 | Åpne bankposter der bilaget allerede ligger i innboksen | ±1 kr, ±7 d og samme leverandør | – | Abonnement | INFO | A | Kortere kundeliste |
| BK20 | Bank | Negativ banksaldo | UB < 0 | < −1 000 kr uten kassekreditt | Kassekreditt | INFO | S | BALANCE 19xx |

**Implementert i `npm run mva` (24.09.2026):** BK7 tar bare med måneder bankavstemmingen selv regner som åpne. Kontoer med bevegelse gir BLOKK, og kontoer med statisk saldo gir FORKLAR. Negativ banksaldo er BK20. Bank hittil i år kjøres bare med `--aarlig`: BK21 gjelder det som må hentes fra kunden, og BK22 internt arbeid. Kontoer som allerede står under BK7, tas ikke med der.


## D. Bilagskontroll A (Sjurs «riktig mva-behandling», punkt 4, 5, 6)

| ID | Pkt | Ser etter | Logikk | Terskel | Falske pos. / filter | Alvor | Utf. | Modul |
|---|---|---|---|---|---|---|---|---|
| M0 | Alle bilag, 11 | Datagrunnlaget er ufullstendig eller avviker fra Tripletex | (a) Bla til en side gir færre enn count, og tell radene selv. **fullResultSize er ikke et totalantall** (K0). (b) Per vatType: grunnlag = Σ amount og mva = Σ(amountGross − amount) på kodede linjer (vatType.number ≠ `'0'`, som er en streng) utenfor 27xx, tilordnet termin etter posting.date. For snudd avregning: grunnlag × sats. (c) Σ mva = Σ 27xx-linjer med **systemGenerated=true** (row 0), **uten 2740**. Filtrer ikke bare på kontonummer, fordi manuelle 27xx-linjer finnes (de går til T3). (d) Σ per kode, avkortet mot null, = vatTermAmount, og = Σ overview.ledgerData når VAT-avstemmingen finnes. Valider term (1–6) og reportType før kallet, fordi vatTermAmount svarer 0 ved feil parametere. Er svaret 0, kryssjekk mot `>vatTerm`. (e) validateCreate: incompleteVouchers, helpAccountPostedOn, accountsRequiringHarmonization, beforeStartBalance, invalidDate. | 0 kr per kode etter avkorting mot null (under 1 kr per linje mot hovedboken) | Bilag registrert mens kjøringen pågikk: hentes på nytt | STOPP | S | – |
| MK1 | Kode | Ulovlig, deaktivert eller utgått kode | legalVatTypes (`vatTypeIds`) per dato og konto, vatLocked, flaggkart per kodegruppe | Mva ≥ bilagsgrense gir BLOKK | Historiske bilag | BLOKK | S | VAT-linje |
| MK3 | Kode, salg | Feil kode på inntektskonto, salgskode på kostnadskonto | 3000–3699 skal ha {3, 31, 33, 5, 52, 6 med flagg, 32 med hasVatOutFish, 51 med ReverseDuty}. Hopp over når status ≠ VAT_REGISTERED. | ≥ bilagsgrense | Tilskudd (MX9), viderefakturering som kostnadsreduksjon | BLOKK | S | VAT 3/6 |
| MK4 | Kode, 6 | Mva-kode på konto der mva ikke hører hjemme | Eksplisitt standardliste som profilen kan overstyre: 1500–1599, 2400–2499, 19xx, 2000–2399, 2600–2699, 2770–2799, 5000–5899, 6000–6099, 7500–7599, 7770, 7800–7899, 8000–8999. 27xx holdes utenfor (T3). Leverandørvurderingen overstyrer. | ≥ bilagsgrense gir BLOKK | Terminalleie og kontingent med mva (leverandørindeks) | BLOKK | S | VAT kode 1 |
| MK5 | Kode | Avvik fra kontoens eller leverandørens vanlige kode | Normer fra 12 mnd (type ≠ WAGE), inkrementelt i mva-normer.json. /anomalies med ett kall per status. | Andel <10 % i norm med ≥3 poster | Blandede konti (profil) | FORKLAR | A | Anomali RESOLVED eller Funn |
| MK6 | 6 | Tapt fradrag | Kode uten fradrag der EHF viser S-kategori med mva, eller leverandøren er norsk og mva-registrert | ≥ bilagsgrense | Forholdsmessig fradrag, unntatt virksomhet | FORKLAR | S | VAT kode 1 |
| MS1 | Sats | Mva ≠ grunnlag × sats per bilag | Relative koder beregnes med deductionPercentage. Netto registrert som brutto. | 1 kr per bilag. BLOKK når Σ ≥ bilagsgrense. | Øreavrunding, valuta | BLOKK | S | VAT-linje |
| MS2 | Sats, 6 | Fradrag høyere enn fakturert mva, fradrag på E/Z/O/AE/K/G, feil sats, **faktura adressert til annen enhet** | EHF-XML: TaxSubtotal, IssueDate, selger «MVA», AccountingCustomerParty = klientens org.nr. ROUND_OFF holdes utenfor. Uten EHF: supplierInvoice eller incomingInvoice. | 1 kr. Kjøper ≠ klient og mva ≥ grense gir BLOKK. | Kreditnota, valuta | BLOKK | S | VAT-linje |
| MS3 | Sats, 11 | Satsrimelighet per kode (erstatter M3) | overview eller kube per kode. Parlinjer skal gå i null. | max(1 kr × bilag, 0,1 %) | Relative koder | FORKLAR | S | VAT-linje |
| MS4 | Sats | Feil sats for ytelsen, for det som gjenstår etter MX4 | Skjønn på EHF eller PDF innenfor budsjettet | ≥ bilagsgrense eller ≥3 like | Hotell med blandet ytelse | FORKLAR | A | VAT kode 1/13 |
| MT1 | Termin | Linjedato og bilagsdato i ulike terminer | **Aktiveres først etter K0-testen** (hvilken dato som styrer) | ≥ bilagsgrense | Periodisering | FORKLAR | S | Funn |
| MT2 | Termin, 9 | Faktura datert i tidligere termin, bokført i T (dekker ET4) | Fakturadato hentes fra supplierInvoice, EHF, incomingInvoice/{voucherId} (ny flyt) eller connector. Mottaksdato fra changes CREATE eller EHF-mottak. Mottatt etter fristen for utstedelsesterminen: lovlig i T (mval. § 15-10, INFO). Ellers: er terminen åpen, flyttes datoen (voucherDate). Er den levert, går saken til punkt 9. | Mva per bilag ≥ grense. Sum per termin. | Faste sene leverandører bare som Sjurs policy. **Ytelsesperiode er ikke et unntak.** | FORKLAR | S | VAT kode 1 |
| MT3 | Termin | Fradrag før fakturadato, bilag datert frem i tid | invoiceDate > voucher.date eller > T_slutt, verifisert mot EHF IssueDate | ≥ grense gir BLOKK | Tolkningsfeil (MT4) | BLOKK | S | Del A |
| MT4 | Termin | Urimelige datoer | Datoregler + OLD_DATE | – | Lang kreditt | INFO | S | Funn |
| MD1 | Alle bilag | Dublettfaktura med dobbelt fradrag (eier) | supplierInvoice + 2400-posteringer (+ connector) som standard. incomingInvoice brukes bare der den ikke gir 403 (K0: 403). Normalisert fakturanummer, orgnr-nøkkel (RK8), KID, checkForDuplicateInvoiceNumber, DUPLICATE_POSTINGS. Tilbakeførte par holdes utenfor. | Eksakt: alle. Nær-dublett ≥1 000 kr. | Faste like beløp (`faste_leverandorer`) | BLOKK | S | Del A tilbakeføring. VAT kode 1. |
| MI1 | 4 | Varekjøp fra utlandet uten innførselsmva | Utenlandske varekjøp mot grunnlag på 81–85/14/15. (c) er fjernet, fordi hasVatInImport ikke gjelder 81–85. | ≥5 000 kr per leverandør | Brukt i utlandet, norsk importør | FORKLAR | S | VAT 81/83. Excel «Innførsel». |
| MI2 | 4 | 81–85 mot Tolletatens oversikt | Fil fra Sjur i `<klient>/<år>/Mva/`: grunnlag per sats matches (dato ±5 d, beløp ±1 %). Uten fil merkes kontrollen «ikke avstemt mot Tolletaten». | Diff ≥1 000 kr grunnlag eller ≥ bilagsgrense mva | Terminskifte | BLOKK | S (fil fra M) | Vedlegg på 81/83-linjen |
| MI3 | 4 | Speditørfaktura: innførselsmva med kode 1, toll med kode | Speditør identifiseres via leverandørindeks eller næringskode | ≥ grense | Innenlands frakt med 25 % | FORKLAR | A | VAT 14/81 |
| MI4 | 4, 5 | Importkoder på tjenester, eller omvendt | Kontointervall × kodeklasse (isReverseIn*) mot `innforsel_metode` | ≥1 000 kr grunnlag | Blandet faktura | FORKLAR | S | VAT-linje |
| MO1 | 5 | Tjenester fra utlandet uten 86–89 | Leverandørindeks (vurdering fra Sjur overstyrer). Kortkjøp identifiseres med nøkkelord. Ukjente vurderes av agent og lagres i indeksen. | ≥500 kr grunnlag | Tjenester brukt i utlandet, VOEC eller norsk mva, finansielle gebyrer (Sjurs vurdering) | FORKLAR | S | VAT 86 |
| MO2 | 5 | Omvendt avgiftsplikt brukt der den ikke gjelder | Snudd kode på norsk mva-registrert leverandør eller EHF med mva. 86 på konto med fradragsforbud. | ≥ grense | NUF som fakturerer fra utlandet | FORKLAR | S | VAT 86/87 |
| MO3 | 4, 5 | Snudd avregning der én side mangler | Per bilag: utgående = −inngående. Fallback via kontopar. | 1 kr | Korreksjonsbilag med én side (kjente-avvik) | BLOKK | S | VAT-par |
| MO4 | 5 | Gull og klimakvoter (51/91/92) | All bruk og nøkkelord | Alle | Smykker | INFO | A | VAT 51/91 |
| MO5 | 5, 6 | Utenlandsk mva eller VOEC-mva fradragsført | Valuta eller land ≠ NO med fradragskode, utenlandske mva-begreper i teksten | ≥ grense | Norsk leverandør som fakturerer i EUR | BLOKK | S | VAT kode 1 |
| MF1 | 6 | Fradrag på representasjon, gaver, velferd og bolig (§ 8-3) | Profilens forbudskontoer (7350, 7360, 7420, 7430 osv.) og bolig. **5990 går til MF3.** | ≥ bilagsgrense, eller sum ≥ min(5 000 kr, 25 % av V) | Møtemat, reklameartikler | BLOKK | S | VAT kode 1 |
| MF2 | 6 | Fradrag på personbil (§ 8-4) | Profilens `kjoretoy` (type, dimensjon, unntak etter annet ledd). **Alle bilkostnader**: 1230, 6440, 7000–7099, leasing, per dimensjon. Ukjent kjøretøy gir ett spørsmål til Sjur. | ≥ grense | Varebil klasse 2, yrkestransport, bom og parkering | BLOKK | S | VAT kode 1 |
| MF3 | 6 | Velferd og representasjon på vanlige konti (inkl. 5990) | Tekst- og næringskodesøk. Agenten leser PDF innenfor budsjettet. | ≥ grense | Møtemat, kundearrangement | FORKLAR | A | VAT kode 1 |
| MF4 | 6 | Forholdsmessig fradrag | Relative koder mot profil. Fellekostnader med full kode. Nøkkel mot faktisk fordeling. | Mva ≥ grense; nøkkel 5 pp | Direkte henførbare kostnader | FORKLAR | S | VAT relativ kode |
| MF5 | 6 | Fradrag fra privatperson, ikke-registrert, konkurs eller slettet leverandør | isPrivateIndividual, `mvaRegistrertPaa(rec, fakturadato)`, status, EHF «MVA», anomalies (**ikke anomalyExport**) | ≥50 kr | Tilbakevirkende registrering | BLOKK | S | VAT kode 1 |
| MF6 | 6 | Fradrag uten dokumentasjon | attachment ELLER document ELLER ediDocument. Ny flyt sjekkes med incomingInvoice/{voucherId}. | ≥ grense | Systembilag | BLOKK | S | Funn |

## E. Bilagskontroll B (punkt 7, 8, 9, 10)

| ID | Pkt | Ser etter | Logikk | Terskel | Falske pos. / filter | Alvor | Utf. | Modul |
|---|---|---|---|---|---|---|---|---|
| KN1 | 7 | Utgående kreditnota med annen kode enn originalen, overkreditering, uten henvisning | creditedInvoice (heltall) gir originalens linjer. Overkreditering sjekkes med originalens amountOutstanding og Σ kreditnotaer med samme invoiceNumber på 1500. **creditedInvoice=null gir avvik** (henvisningskrav, bokføringsforskriften kap. 5). | Kodeavvik ≥100 kr mva, >1 kr | Integrasjon uten kobling (profil), satsendring | BLOKK | S | VAT 3/31/33 |
| KN2 | 7 | Kreditnota brukt i stedet for tap på krav | Hele beløpet kreditert, forfalt >60 d, ikke betalt | ≥1 000 kr mva | Reklamasjon, isFactoring | FORKLAR | A | VAT kode 3 |
| KN3 | 7 | Inngående kreditnota uten mva, med feil fortegn eller dobbelt | Kandidat: debet 24xx og kostnads- eller mva-linje uten banklinje, eller isCreditNote eller negativt beløp. EHF CreditNote uten BillingReference gir avvik. | ≥100 kr mva | Utenlandske (86), bonus | BLOKK | S | VAT fradragslinje |
| TP1 | 7 | Mva tilbakeført uten konstatert tap | Tapskonti og LOSS_OF_CLAIM. Kundefordring og vedlegg. Agenten vurderer dokumentasjonen (mvaforskr. § 4-7-1). | Alle | Factoring (isFactoring) | BLOKK | A | LOSS_OF_CLAIM-linje + vedlegg. N2 |
| TP2 | 7 | Mva på avsetning, konstatert tap uten tilbakeføring, feil beløp | a) avsetning med kode, b) 7830 uten tilbakeføring, c) sats | a) alle, b) ≥1 000 kr, c) ≥100 kr | Fordring fra fritatt salg | FORKLAR | S | VAT kode 3 |
| TP3 | 7 | Innbetaling på tidligere avskrevet fordring uten ny mva | Kunder med tapsbilag + INCOMING_PAYMENT | ≥100 kr | Tap ført uten tilbakeføring | FORKLAR | S | VAT kode 3 |
| UT1 | 7 | Registrerte uttak: grunnlag, sats, dokumentasjon | WITHDRAWAL-koder og -linjer | ≥100 kr | – | INFO | S | WITHDRAWAL-linje. N2 |
| UT2 | 7 | Mulig uttak uten uttaksmva | Lager eller inntekt mot mellomregning, personal, gaver. Egenregi. hasWithdrawalVat. | ≥1 000 kr | Små gaver, ansattsalg med kode 3 | FORKLAR | A | VAT kode 3 |
| KV1 | 8 | Nye kapitalvarer | Inngående mva ≥ 50 000 kr (driftsmidler, 5 år) eller ≥ 100 000 kr (fast eiendom, ny-, på- og ombygging, 10 år). Omvendt: grunnlag × sats × fradragsprosent. Gruppering: asset.id, deretter prosjekt fra start, deretter linje. Personkjøretøy gir INFO. | Lovens grenser. Varsel ved 80 %. | Varer til videresalg | FORKLAR | S | BALANCE 11xx/12xx: vedlegg kapitalvarer.md |
| KV2 | 8 | Kapitalvare kostnadsført | 6500–6699 (og 6300 ved påkostning på leide lokaler). Inngående mva ≥ grense. | Lovens grenser | Reelt vedlikehold | FORKLAR | A | VAT kode 1 |
| KV3 | 8 | Avgang innenfor justeringsperioden | Fast eiendom er **alltid unntatt** (§ 3-11). Da kreves engangsjustering (§ 9-3) eller avtale om at kjøper overtar. Driftsmiddel krever utgående mva, og justering bare ved unntatt salg. Utrangering vurderes av menneske. | Alle innenfor perioden | Virksomhetsoverdragelse med avtale | BLOKK | A | ADJUSTMENT-linje + vedlegg |
| KV4 | 8 | Endret bruk: nøkkel, frivillig registrering, avregistrering | Relative koder endret. Leieandel. vatRegistrationStatus. | 10 pp (må verifiseres) | Sesong, ledig areal | FORKLAR | A | ADJUSTMENT i siste termin |
| KV5 | 8 | Årlig justering i siste termin | siste termin = 12 / antall måneder per termin. Forventet justering mot ADJUSTMENT-linjer. | ≥1 000 kr, avvik > max(100 kr, 1 %) | Uendret bruk | BLOKK | S | ADJUSTMENT + vedlegg. N2 |
| KV6 | 8 | Anlegg som mangler i kapitalvareoversikten | /asset (overview) mot kapitalvarer.md | Kost ≥200 000 kr / ≥400 000 kr | Kjøpt uten mva | INFO | S | BALANCE vedlegg |
| ET1 | 9 | Hovedbok for leverte terminer ≠ rapportert (eier; dekker T13, IN23) | For hver levert termin siden 2022 (RECEIPT_RECEIVED/MANUAL_DELIVERY): /vatReturns/{vatReturns2022Id}-linjer per standardCode (hent uten fields eller med `fields=*`, og slå opp vatType.id → number) mot kuben aggregert per termin, avkortet mot null per kode. Fanger også slettinger. Ikke vatTermAmount, fordi det er uavklart om den er lagret eller beregnet på nytt. Modulens overview brukes der den finnes (ledgerData ≠ reportedData, eller ≠ ledgerDataAtPreviousReconciliation, som bare er fylt ut på COMPLETED). | ≥1 kr. ≥ V_mva gir BLOKK. | Ikke synket (reportedData null), primærnæring | BLOKK | S | VAT-linje i T. :unlock på gammel termin ved korrigert melding. |
| ET2 | 9 | Bilag ført i levert termin etter innsending | Primært: kodet linje (vatType ≠ `'0'`, utenfor 27xx) i levert termin med `isAmountVatClosed=false`. K0 viste at alle kodede linjer i leverte terminer har true, men false er ikke observert i praksis (middels sikkerhet). Bekreftelse: `voucher.changes` med **changeType=CREATE** > deliveryStatus.time. UPDATE-hendelser finnes også og vurderes separat. Mangler CREATE, blir status «ukjent», ikke funn. Full skanning bare for terminer ET1 har flagget. | ≥ V_mva, eller underrapportert utgående mva, gir BLOKK | Oppgjørsbilag, bilag uten kode | BLOKK | S | Som ET1 |
| ET3 | 9 | Reverseringer som flytter mva fra rapportert termin (reverseringsmønsteret) | reverseVoucher med original før T_start. Summert per termin og kode. | ≥100 kr. ≥ V gir BLOKK. | Omkontering med netto 0 | BLOKK | A | VAT kode 1/3. N5 |
| EX1 | 10 | Kode 52 mot norsk kunde eller levering i Norge | Kundeland og deliveryAddress. **Svalbard (9170–9179) og Jan Mayen (8099) vurderes særskilt.** | ≥1 000 kr | Norsk kunde med levering til utlandet | BLOKK | S | VAT 52 |
| EX2 | 10 | Utenlandsk kunde fakturert med norsk mva | Kode 3/31/33 og land ≠ NO | ≥5 000 kr per kunde | Levert i Norge, fast eiendom, NUF | FORKLAR | A | VAT kode 3 |
| EX3 | 10 | Mangler dokumentasjon for fritak | Eget vedlegg, dokumentarkiv på kunde, lokal mappe `Dokumentasjon/Eksport/` | ≥10 000 kr enkeltvis | `eksportdok: <sted>` | FORKLAR | M | Vedlegg på 52-linjen |
| EX4 | 10 | Kode 52 brukt feil | 52 på 4xxx–7xxx/1xxx i debet og/eller supplierVoucherType (ikke posting.type). Grunnlag i kuben mot 52-fakturaer. | ≥100 kr | Nettbutikkbilag | BLOKK | S | VAT 52 |
| EX5 | 10 | Kode 5 (innenlands nullsats) uten grunnlag | All bruk av kode 5. Agenten vurderer ytelsen. | Grunnlag ≥5 000 kr | Profilens `mva_omraader` | FORKLAR | A | VAT kode 5 |

## F. Terminavstemming (punkt 11), skattekonto (punkt 12) og merknader (punkt 13)

| ID | Pkt | Ser etter | Logikk | Terskel | Falske pos. / filter | Alvor | Utf. | Modul |
|---|---|---|---|---|---|---|---|---|
| T0 | 11, 1, 3 | Kan terminen beregnes? (eier av validateCreate) | validateCreate-flagg. Én kjøring per reportType. VAT_APPLICANT stopper. | 0 | alreadyExists (ikke feil), bevisst låst periode | BLOKK | S | Pakke 1 |
| T1 | 11 | Mva per kode: hovedbok mot beregnet melding | Primært Σ(amountGross − amount) per vatType.id utenfor 27xx (snudd: grunnlag × sats), avkortet mot null per kode. **Allerede før Opprett** (K0): = `>vatTerm`-utkastets `lines.vatAmount` per standardCode (id=0, hentes uten fields; vatType.id → number via /ledger/vatType), og total = vatTermAmount. Etter Opprett: samme mot det opprettede utkastet og totalAmountVatToPay. Σ overview.ledgerData (når avstemmingen finnes) og systemgenererte 27xx er kryssjekker. Kode 86/87/88/89 har negativ rate, så bruk abs(rate). | 0 kr per kode etter avkorting | Parkoder netto | BLOKK | S | Kommentar etter synk |
| T2 | 11 | Grunnlag per kode ≠ melding | Σ amount per kode mot lines.basis (`>vatTerm`, også før Opprett) og overview.basis. Fortegn: basis for kode 1/3 = −Σ amount. | max(1 kr, 0,5 kr × poster) | Spesifikasjonslinjer, 86-par | FORKLAR | S | VAT-linje |
| T3 | 11 | Manuelle føringer på mva-kontoene (eier; dekker MK2) | Fra kuben, minus oppgjørsbilaget (voucherId): 27xx-linjer med `systemGenerated=false` (K0: finnes på 2700/2703/2710), vatType null/`'0'` eller bilagstype som ikke er faktura, bank eller oppgjør. Mva-kode på 27xx-linje. Betaling ført mot 2700/2710. | ≥1 kr | IB, kjente omposteringer | BLOKK | S | Del A |
| T4 | 11 | IB på 2700–2739 ≠ 0, UB ≠ 0 etter oppgjør | /balanceSheet, forrige termins voucherNumber > 0 | 1 kr | Egen kontoplan (profil) | BLOKK | S | Pakke 1 |
| T5 | 11 | Oppgjørsbilag ≠ melding (eier; dekker IN9) | voucherId fra overview gir /ledger/voucher/{id}. Oppgjørskonto og accountRoundDiffId fra postingRules. | 1 kr | Øreavrunding | BLOKK | S | Kontroll etter Opprett |
| T6 | 11 | Sats og parlinjer per utkastlinje | basis × rate (× deductionPercentage) ± 1 kr per linje. Antall poster fra kuben. | max(1 kr, 0,5 kr × poster) | Spesifikasjonslinjer | FORKLAR | S | – |
| T7 | 11, 2 | Omsetning på 3xxx ≠ utgående grunnlag | −Δ3000–3999 mot Σ basis for utgående koder. Differansen forklares per vatType. | V (omsetning) | Periodiseringer, tilskudd, `omsetning_uten_mva_konti` | FORKLAR | S | Kjente-avvik |
| T8 | 11, 1, 6 | Inngående mva uvanlig mot kostnadsnivå | Mot samme termin i fjor og snittet av 4 terminer | ±40 % og ≥ V | Sesong, investering | INFO | A | – |
| T9 | 11, 12 | 2740 IB ≠ forventet | **Forventet IB = −Σ A(t) for terminer med oppgjørsbilag før start og dueDate ≥ start** (Skatteetatens dueDate). Gjelder også månedstermin og flyttet frist. | 1 kr | Renter på 2740, motregning | FORKLAR | S | 2740-linje (referenceId ikke verifisert) |
| T10 | 11, 12 | Betaling eller tilbakebetaling ikke bokført mot 2740 (eier; BK11 er datakilde) | Per termin med dueDate i [T_start − 10 d, i dag]: bankpost (tekst- eller KID-søk, KID fra paymentInfo) og 2740-bevegelse. paymentHistory og /bank/ztl/payment/internal er bare hint. **K0: for tilgodeterminer viser Tripletex ofte isPaid=false, remainingAmountVatToPay og OPEN_POST selv når Skatteetaten har gjort opp og 2740 er 0.** Tilgode avgjøres derfor av claimsAndPayments (konteringTilgodeMva med outstandingAmount = 0) + 2740 + bankpost. vatPaymentStatusUpdate. | 1 kr. Mva-kode på betalingen gir BLOKK. | Betalt fra annen konto (profil), samlet innbetaling | FORKLAR | S | 2740 |
| T11 | 11 | 2740 UB ≠ forventet | Forventet UB = −Σ A(t) for oppgjør ≤ T_slutt med dueDate > T_slutt | 1 kr | Ikke forfalt | FORKLAR | S | 2740 |
| T12 | 11 | Etter synk: tre-veis likhet | RECEIPT_RECEIVED/MANUAL_DELIVERY. overview: ledger − reported og **reported − taxAdmin regnes begge selv**. `difference` brukes ikke, fordi den er null før levering og det er uavklart om den tar med taxAdmin (K0). taxAdmin null gir beskjed om at Sjur må synke. isFeedbackProvided. | 1 kr per linje | Skatteetaten har ikke behandlet ennå | FORKLAR | S | Hovedsteget i modulen |
| T14 | 11, 13 | Utkastet vil bli avvist (eier; dekker IN8) | POST /vatReturns/{id}/validate. 401/403 betyr at valideringen skjer i Sjurs økt. | INVALID gir BLOKK | Advarsler som allerede er forklart | BLOKK | S | Pakke 1 / økt |
| T15 | 11 | Modulen er klar for :complete | validations-referenceId matchet mot overview.vatTypeId. K0: /validations er tom før levering, og referenceId for mva er ikke verifisert (K0 test 2), så kommentarer skrives bare på et verifisert format. Kode 86 har to linjer med samme vatTypeId. En tom liste betyr ikke «avstemt». GET comments/attachments før POST. comments/list. Ved 422: én ny runde. requiresControl gir venting på CONTROLLED. | Ingen åpne validations | Feil referenceId (201, usynlig) | FORKLAR | S | :complete |
| T16 | 11, 13 | Linje med fortegn motsatt av `expectedSign` (ny etter K0) | `>vatTerm`-utkastet (også før Opprett): vatAmount-fortegnet ≠ expectedSign, f.eks. netto positiv kode 1 fordi kreditnotaer er større enn kjøpene, eller feilført fortegn. Topp bilag etter \|mva\| på koden. | Alle | Ekte netto kreditnota, forklart | FORKLAR | S + A | Merknadskandidat, del A ved feilføring |
| SK1 | 12 | Tidligere terminer ikke betalt eller tilbakebetalt (erstatter M6) | Terminer med forfall passert: PAYMENT_REGISTERED, NO_TAX_TO_PAY eller AMOUNT_CREDITED og remainingAmount = 0. NOT_PAID med bankbetaling funnet i T10 gir INFO: «ikke registrert i mva-modulen». K0: AMOUNT_CREDITED med remainingAmount lik hele tilgodebeløpet er vanlig selv når beløpet er utbetalt. Når claimsAndPayments viser konteringTilgodeMva oppgjort og 2740 stemmer, blir det INFO og ikke funn. | 1 kr | Manuelt bilag oppdaterer ikke paymentStatus (`mva_betaling_registreres=manuell`) | FORKLAR | S | 2740 |
| SK2 | 12 | Åpne eller forfalte mva-krav på skattekontoen (dekker BK13) | /claimsAndPayments i **klientkontekst** (K0: byClient gir 403 KB-005). Hent terminens år og året etter, og dedupliser på claimIdentifier + claimType. Filtrer **lokalt** på claimGroup = «Merverdiavgift», uten hvitliste over claimType. Både mvaMelding og konteringMvaÅBetale er krav å betale. Åpent krav: outstandingAmount ≠ 0. Termin fra periodDescription. En endringsmelding gir flere krav per termin, og renter er egne krav med egen KID. For tilgode er dueDate utbetalingsdato. Ved 500: 3 nye forsøk. hasSystemUser=false, eller feil etter nye forsøk, gir «ukjent» og SK5. Åpen T−1 etter betaling tyder på eldre krav eller motregning (dekningsrekkefølge), ikke «feil KID», og gir gul status. | 1 kr | Ikke forfalt, registreringsforsinkelse | FORKLAR | S | 2740 + vedlegg |
| SK3 | 12 | Skattekontoens mva ≠ 2740 | Forventet utestående = Σ A(t) for leverte terminer med dueDate > dato. Samlet saldo på skattekontoen rapporteres som INFO. | 1 kr | Tidsforskyvning | FORKLAR | S | 2740 |
| SK4 | 12 | Renter, gebyr og ufordelt innbetaling som ikke er bokført | rent > 0 mot 81xx. Ufordelt eller tilgode som fordring. | Renter ≥100 kr. Rødt hvis ført på 2740. | – | INFO | A | Forslag til bilag |
| SK5 | 12 | Skattekontoutskrift (fallback) | Bes om bare ved SK/T9/T10-avvik, termin 6, eller profil `skattekonto_kilde=utskrift`. Leses lokalt. | Som SK2–SK4 | – | INFO | M | Vedlegg på 2740 |
| N1 | 13 | Fortegnsavvik (dekker SB2) | sign(vatAmount, basis) mot expectedSign. Kandidater fra /vatReturns/comment filtrert på vatCode. Agenten velger merknad og skriver én setning. | ≥1 kr | Parlinjer | BLOKK | A | Merknad på meldingen (:modifyComment eller UI) |
| N2 | 13, 7, 8 | Spesifikasjonslinjer (tap, uttak, justering, tilbakeføring) uten dokumentasjon eller merknad | Bilag med vedlegg, kobling til TP, UT og KV | Alle | Faste uttak (profil) | FORKLAR | A | Merknad + vedlegg i modulen |
| N3 | 13 | Stor tilbakebetaling (dekker IN7) | Til gode ≥ `merknad_grense_tilgode` eller > 2 × median av \|A\| siste 4 terminer. Driverne (bilagsnummer, firmanavn bare med orgnr, konto) brukes i merknad og eventuelt vedlegg. | Profilgrense | Sesong, fast tilgode-klient | FORKLAR | A | Merknad + vedlegg (Sjur ser det først) |
| N4 | 13, 11 | Uvanlig stor linje, ny kode, eller fast kode som forsvinner (dekker SB1) | Historikk per standardCode (>vatTerm eller reportedData). Topp 10 bilag etter \|mva\|. Bilag uten vedlegg blant dem. | >3 × median og ≥ V | Sesong | INFO | A | Merknadskandidat |
| N5 | 13, 9 | Negativt grunnlag fra tilbakeføringer (beslutningen tas i ET3) | reverseVoucher mot rapportert termin | ≥ V eller >10 % | Vanlig kreditnota | FORKLAR | A | Beslutning i pakke 1 |
| N6 | 13, 3 | Oppstart, opphør, termin-endring, VAT_APPLICANT | vatTermSizeSettings og vatSettings | Hendelse | – | INFO | S | Merknad |
| N7 | 13 | Merknader som alt ligger på utkastet og er feil eller inneholder personopplysninger | userComment og structuredComment per linje | Alle | – | INFO | S | Pakke 1 |

## G. Innsending, betaling og etterarbeid (Sjurs «sendt inn», «betaling opprettet», punkt 14–17)

| ID | Pkt | Ser etter | Logikk | Terskel | Falske pos. / filter | Alvor | Utf. | Modul |
|---|---|---|---|---|---|---|---|---|
| IN1 | Sendt | Gate: alle områder er ferdige | Åpne BLOKK uten gyldig kjent avvik stopper før pakke 1, eller gir port gul eller rød | 0 åpne BLOKK | – | BLOKK | S | – |
| IN3 | Sendt, 12 | Tidligere terminer ikke levert, eller gjenåpnet | status/list og overview. voucherNumber=0 på tidligere levert termin betyr gjenåpnet. | Alle | Før registrering, før 2022 | FORKLAR | S | logg.md |
| IN6 | Sendt | Mangler innsendingsrett i Altinn | DELIVERY_FORBIDDEN/USER_FORBIDDEN gir blokk. Bekreftelsesdato i profilen (datoen for tilgangspakker skal ikke hardkodes, den er ikke verifisert). | – | Kunden sender selv | INFO | S | Huskeliste til økta |
| IN10 | Sendt | Sendt, men ikke kvittert | Poll /vatReturns/status hvert 30. sekund. RECEIPT_RECEIVED + time. FAILED gir beskjed til Sjur om «Send på nytt». WAITING_FOR_REPLY i mer enn 30 min gir isFeedbackProvided/getFeedback. Levert etter frist gir INFO. | 60 min | Treg Altinn | BLOKK | S | logg.md |
| IN11 | Betaling, 11 | Skatteetatens beløp ≠ meldingen | altinnPaymentAmount = totalAmountVatToPay = paymentInfo.amount = Σ reportedData (K0: paymentInfo.amount = totalAmountVatToPay er verifisert, også for tilgode) | 1 kr | Avrunding | BLOKK | S | – |
| IN13 | Betaling | Feil KID, konto, beløp eller forfall | `paymentInfo` (kid, account, amount, dueDate) er grunnlaget. Kontroller den mot KID og beløp på mvaMelding- eller konteringMvaÅBetale-kravet i claimsAndPayments når kravet finnes (bare terminer med beløp å betale). K0: KID er unik per termin, så det finnes ikke noe profilfelt `mva_kid`. Widget gir 403. isKidUpdatable=false. | Eksakt | claimsAndPayments utilgjengelig eller krav ikke opprettet ennå: merkes | BLOKK | S | logg.md |
| IN14 | Betaling | Dobbeltbetaling | paymentHistory (ikke reversert), /bank/payment VAT med isSalary=false, PAYMENT_REGISTERED, utestående 0, banktransaksjon med paymentId eller KID | Ethvert treff | Kansellerte eller avviste | BLOKK | S | Pakke 2 |
| IN15 | Betaling, 17 | Ingen integrasjon, feil fra-konto, manglende rett, manglende dekning (dekker BK19) | /bank/globals remitPaymentType=OFF gir bare kundetekst. **K0: paymentWidget, /bank/payment og autoPayStatus gir 403 for API-brukeren, så vei B (kundetekst) gjelder til Sjur har avklart betalingsrollen.** AUTOPAY eller ZTL, **aldri POSTING_RULE/NOT_PAID**. Dekning fra agreements (updateBalance=true bare her) eller ZTL. | Dekning ≥ beløp | Kassekreditt | FORKLAR | S | Pakke 2 |
| IN16 | Betaling | Feil forfall eller betalingsdato | Skatteetatens dueDate (overview, todoList customDueDate, paymentInfo) er primærkilde. K0: dueDate flyttes ved helg (10.10 på lørdag blir 12.10), og claim.dueDate for tilgode er utbetalingsdato, ikke frist. Fristtabell med virkedag er fallback. | Dato = forfall | Utsatt frist | FORKLAR | S | – |
| IN17 | Betaling | Opprettet betaling finnes ikke, eller er feil | Øyeblikksbilde av betalingslisten før POST, sammenlignet med listen etter. Beløp, KID og dato kontrolleres. statuslog REJECTED eller INSUFFICIENT_FUNDS gir rødt. | Eksakt | – | FORKLAR | S | logg.md |
| IN18 | 17 | Ikke godkjent før forfall | remits og /bank/payment ved forfall − 2 virkedager. Etter forfall: NOT_PAID. | 2 virkedager | Kunden har betalt utenom (IN14) | INFO | S | Varsel |
| IN19 | 16 | Til gode: fordring ikke ført, kontonummer ikke bekreftet (dekker MX20) | Oppgjørsbilagets 2740-postering = \|A\| (ikke saldo). Kontonummer hos Skatteetaten bekreftet innen 12 mnd og etter siste nye bankkonto. Ellers blir det et steg for Sjur i økta. | 1 kr | Motregning | FORKLAR | S+M | Kommentar total |
| IN20 | 16, 12 | Tilbakebetaling ikke mottatt, eller feilført (dekker BK12) | Innbetaling fra Skatteetaten innen +35 d. Motkonto 2740 (renter på 8050). Delbeløp: finn motregnet krav. | 21 d | Samlet utbetaling | FORKLAR | S | Neste termins VAT |
| IN21 | 14 | Mva-terminen er ikke låst | voucherNumber > 0 og advancedVoucher metadata.vatLockedThroughDate ≥ T_slutt | 0 | – | FORKLAR | S | – |
| IN22 | 14 | Regnskapsperioden er ikke låst | **Sjur låser i UI** etter at bankmånedene er lukket. Kontroll av isClosed og accountingLockedThroughDate. :check er ikke en lås. | Alle måneder | `periodelaas_etter_mva=nei` | INFO | M | – |
| IN24 | 15 | Arkivet er ufullstendig | PDF fra modulen (document), XML og kvittering finnes i `<klient>/<år>/Mva/` og er > 0 byte. Linje i logg.md. Ved requiresControl ventes det på CONTROLLED. | Alle filer | Kvittering ikke tilgjengelig: merkes | INFO | S | – |
| IN25 | 15 | Kjente avvik er utdatert | Utløpte linjer med samme nøkkel vises igjen. Nye linjer foreslås etter godkjenning. | – | – | INFO | A | – |
| IN26 | 17 | Kunden vet ikke at betalingen venter | Vei A: betaling venter på godkjenning, «ikke betal separat». Vei B: beløp, KID, konto og forfall. Til gode: tekst. Bare tekst i chat, og utkast bare etter ja. | – | Silfer godkjenner selv (profil) | INFO | A | logg.md (dato og kanal) |

## H. Nye kontroller fra kritikeren (MX)

| ID | Pkt | Ser etter | Logikk | Terskel | Falske pos. / filter | Alvor | Utf. | Modul |
|---|---|---|---|---|---|---|---|---|
| MX1 | Alle bilag, 2 | A konto- eller forskuddsfaktura uten utgående mva | Ordre med totalInvoicedOnAccount > 0, invoiceOnAccountVatHigh=false og linjer med 3/31/33. Fakturabilag med 29xx og kode 0. Innbetaling uten faktura: INFO. | ≥ V_mva gir BLOKK | Unntatt ytelse, depositum | BLOKK | S | Del A. VAT kode 3. |
| MX2 | Kode, 7 | Purregebyr eller rente med mva. Fakturagebyr uten mva. | /reminder, /invoice/settings og /product mot fakturalinjer | Sum ≥100 kr | Gebyr på fritatt faktura | FORKLAR | S | Produktoppsett. VAT kode 3. |
| MX3 | Sats, salg | Fakturalinje med annen kode enn produktet. Sats mot vareslag. | orderLine.vatType ≠ product.vatType. Produktet ≠ produktkontoens kode. Endring i satsfordeling >20 pp går til agent. | ≥100 kr per linje | `satsunntak_produkter` | FORKLAR | S | VAT 31/33/3 |
| MX4 | 6, sats | Hotell, reise, transport, bom og parkering med feil sats eller fradrag | Forventet sats-sett per næringskode (55.1, 49–51, 52.21, 56). EHF-satser. Utenlandsk leverandør med norsk kode. | ≥ bilagsgrense | Blandet hotell | FORKLAR | S | VAT kode 1/13 |
| MX5 | 6 | Faktura til andre enn klienten, privat bruk (mobil, bredbånd, PC, dagligvare) | (a) EHF-kjøper ≠ klient (samme tolking som MS2), (b) utlegg på 69xx, (c) privat næringskode. PDF innenfor budsjettet. «Ansatt n», aldri navn. | (a) ≥ grense gir BLOKK. (b)/(c) sum ≥500 kr. | Klienten er kontraktspart, `fradrag_ok_leverandorer` | FORKLAR | A | Del A. VAT kode 1. |
| MX6 | 6, 3 | Fradrag på husleie når utleier ikke fakturerer mva | 6300–6399 med fradragskode mot Brreg-registrering for utleier og EHF TaxAmount | Alle ≥1 kr | Registrert i konsern | BLOKK | S | Del A. Tidligere terminer går til punkt 9. |
| MX7 | 3 | Feil kode på leieinntekt per leietaker | 3600–3699 per kunde mot frivillig registrering og leietakers registrering. Parkering og lager uten mva. | (a)/(b) ≥ V_mva gir BLOKK | Arealandel (profil) | FORKLAR | S | VAT 3/6 |
| MX8 | Termin, 9 | Periodiserings- eller avsetningsbilag med mva | Bilag uten supplierVoucherType eller fakturatype med 17xx/29xx og kode. Reversering som flytter mva mellom terminer. | ≥1 kr | Tripletex' egen periodisering på fakturabilag | BLOKK | S | Del A |
| MX9 | Kode, 2 | Tilskudd, refusjon, forsikring eller finansinntekt med mva, eller vederlag uten mva | 3400–3499, 5800–5899, 8000–8199 med utgående kode. Offentlig kunde med tilskudd går til agent. | A: alle. B: ≥50 000 kr. | `konto_unntak` | FORKLAR | S | VAT kode 3 |
| MX10 | 1, 6 | Diett, km- eller nattillegg med mva-kode | Bilagstype reiseregning/utlegg på profilens diettkonti med kode ≠ 0. Ingen personendepunkt. | Alle | `konto_diett` | BLOKK | S | Del A |
| MX11 | 2, alle bilag | Omsetning uten salgsdokument | 3000–3699 med bilag som ikke er faktura og uten vedlegg | ≥1 000 kr eller sum ≥ V_mva | Integrasjonsbilag (profil), MX8 | FORKLAR | S | Handlingsliste til kunden |
| MX12 | Kode, salg | Viderefakturering som «mva-fritt utlegg» | Faktura med 3/31/33 og 0/5/6-linjer med utleggsord. Agenten vurderer om det er et rent utlegg. | ≥100 kr per faktura | `rene_utlegg_produkter` | FORKLAR | A | VAT kode 3 |
| MX13 | 10, 7 | Privatkunde med fritakskode, salg til nærstående under pris (§ 4-9) | isPrivateIndividual med 52/5/6. `naerstaende_kunder` (bare id) med rabatt >20 %. | A: alle | Personalrabatt som andre kunder får | FORKLAR | S | VAT 3/52 |
| MX14 | 2 | Gavekort (mva ved salg og ved innløsning) | Profilens `konto_gavekort` og produktet «gavekort» | Bare klienter med profil | Avklart rutine | INFO | A | – |
| MX15 | 5, 6 | Kurs, konferanse, webinar | Utenlandsk leverandør uten 86/87, eller med norsk kode. Sosialt program. | ≥100 kr | VOEC/norsk registrering | FORKLAR | A | VAT 86/1 |
| MX16 | 2, termin | Cut-off i omsetning fra betalingsløsning eller kasse ved terminskifte | Vindu [T_slutt − 7 d, T_slutt + 14 d]. Oppgjørsbilag etter T_slutt med salgsperiode som starter ≤ T_slutt. Mangler salg de siste dagene. Kundens rapport avgjør. | ≥ V_mva gir BLOKK | Daglig bokføring med salgsdato | FORKLAR | S | BALANCE oppgjørskonto + VAT 3/31 |
| MX17 | 11, 13 | Årlig grunnlag i meldingene ≠ omsetning i regnskapet og skattemeldingen | Bare i siste termin. Σ basis for året mot 3000–3999 (+ 8xxx gevinst). Differansen dekomponeres. | Uforklart > max(10 000 kr, 1 %) | Opptjent ikke fakturert | FORKLAR | S | VAT kode 3 (siste termin) |
| MX18 | 6, kode | Fradrag på ytelser som er unntatt eller utenfor (bank, forsikring, helse, undervisning, offentlige gebyrer) | A: konto (MK4-listen). B: næringskode 64–66, 84, 85.1–85.4, 86 eller 94.1 med fradrag. | A: alle. B: ≥ grense. | Avgiftspliktige tjenester (EHF TaxAmount > 0) | BLOKK | S | Del A |
| MX19 | Alle bilag, sats | Blandet faktura ført på én kode | Antall distinkte (kategori, sats) i EHF > antall vatType i bilaget, eller Σ per sats avviker >1 kr | ≥ bilagsgrense | Ikke-fradragsdel på egen konto uten kode | FORKLAR | S | Del A |

## I. Klienter som ikke er mva-registrert (UR)

Gjelder når S1 setter modus `UREGISTRERT` (UR0). Faglig grunnlag: `fradragsregler.md` kapittel 7. Regel-id-ene står i `regelbase.json`. Pilotert lesende på en eiendomsutvikler, T4 2026.

**Kontroller som fortsatt gjelder:** A (forutsetninger, særlig F1 innboks og ikke bokførte bilag), B (reskontro), C (bank), MD1 (dublett), dokumentasjonskontrollene (salgsdokument, purring registrert som faktura, kreditnota uten referanse) og MK4/MK5 bare for å finne koder som ikke hører hjemme.
**Kontroller som ikke gjelder:** terminavstemming (T), skattekonto for mva (SK), merknader (N), innsending og betaling (IN), endringer i leverte terminer (ET), innførsel (MI), fradragsbegrensninger (MF) og kapitalvarer (KV). Alvoret BLOKK betyr her «må rettes i regnskapet», siden det ikke finnes noen melding å blokkere.

| ID | Pkt | Ser etter | Logikk | Terskel | Falske pos. / filter | Alvor | Utf. | Modul |
|---|---|---|---|---|---|---|---|---|
| UR0 | 3 | Riktig modus | `vatSettings.vatRegistrationStatus` = VAT_NOT_REGISTERED **og** Brreg `registrertIMvaregisteret` = false (leverandørindeksen). Uenighet mellom Tripletex og Brreg, eller VAT_APPLICANT (tilbakegående oppgjør, § 8-6), gir STOPP med melding til Sjur. | – | – | STOPP ved uenighet | S | – |
| UR1 | Alle bilag | Fradrag eller utgående mva hos en klient som ikke er registrert | R-UREG-FRADRAG, R-UREG-UTGAAENDE, R-UREG-27XX, R-UREG-BRUTTO: ingen fradrags- eller utgående koder, 2700–2749 tomme (unntatt skyldig mva ved omvendt avgiftsplikt, kode 87/89/92), `amount = amountGross` på kostnads- og aktiveringslinjer. 2770/2785 er arbeidsgiveravgift, ikke mva. | 1 kr | – | BLOKK | S | Del A |
| UR2 | 3 | Kontoplanen har fradragskode som standard | R-UREG-KONTOPLAN: kostnadskontoer med `account.vatType` = 1/11/13. Rapporteres **én gang per konto** (antall bilag og sum), ikke per bilag. | – | Kontoer uten bevegelse holdes utenfor | INFO | S | Profil (forslag om å endre standardkoden krever ja) |
| UR3 | 3 | Registreringsplikt (mval. § 2-1) | Avgiftspliktig omsetning og uttak siste 12 måneder, rullerende. Inntektskontoene klassifiseres én gang (agent, Sjur bekrefter) og lagres i klientprofilen som `inntekt_klassifisering` (unntatt salg av fast eiendom, unntatt utleie, avgiftspliktig, utenfor). Varsel ved 80 % av grensen. | 50 000 kr (varsel 40 000 kr) | Salg av fast eiendom (§ 3-11), utleie uten frivillig registrering | BLOKK over grensen, INFO ved varsel | S + A | Beslutningsliste |
| UR4 | 3 | Byggearbeid i egen regi (mval. § 3-26) | R-UREG-3-26, **én gang per klient** og ikke per bilag: lønn > 0 **og** bevegelse på aktivering eller prosjektkontoer (1130, 1400–1499 og profilens `konto_prosjekt`, f.eks. 45xx). Agenten samler fakta (hva de ansatte gjør, byggeadministrasjon, byggherreombud, innleid administrasjon) og Sjur avgjør. Svaret lagres i profilen (`s3_26_vurdering`: dato og konklusjon). Kontrollen kommer bare tilbake ved nytt prosjekt eller når lønnen endres mer enn 30 %. | Klientnivå | Tekst i entreprenørens egen faktura («byggherre», «innleide») er ikke bevis | FORKLAR (BLOKK hvis Sjur konkluderer med plikt) | A + Sjur | Beslutningsliste |
| UR5 | 5 | Omvendt avgiftsplikt for kjøper som ikke er registrert | R-UREG-OMVENDT-2000 og R-UREG-OMVENDT-86: fjernleverbare tjenester fra utlandet (leverandørindeksen: `UT:` eller vurdert med `--omvendt`), og klimakvoter eller gull, summert per **kalenderkvartal**. Over grensen: egen mva-melding for omvendt avgiftsplikt (frister 10.5, 31.8, 10.11 og 10.2), kode 87/89/92. Kodene 86 og 88 skal aldri forekomme. | Grunnlag over 2 000 kr eks. mva per kvartal | Utenlandske leverandører med norsk VOEC- eller mva-registrering (leverandørindeksen) | BLOKK over grensen | S + A (klassifisering av leverandør) | Beslutningsliste. Sjur leverer meldingen |
| UR6 | 2 | Salg som kan være avgiftspliktig | R-UREG-SALG-AVGIFTSPLIKTIG og R-TILVALG-BOLIGSALG: tilvalg og endringsarbeid ved boligsalg, viderefakturering, utleie av utstyr og lignende. Tilvalg til samme kjøper som kjøper eiendommen følger normalt det unntatte salget (BFU 15/13). Ulike kjøpere, eller levering etter overtakelse, kan gjøre tilvalget avgiftspliktig. | ≥ 5 000 kr per forhold | Ordinært eiendomssalg | SPØR_SJUR | A | Beslutningsliste |
| UR7 | 3 | Innførsel ført med kode | R-UREG-IMPORTKODE: mva betalt til Tolletaten eller speditør er ren kostnad hos en klient som ikke er registrert. Kodene 14/15/81–85 skal ikke brukes. | 1 kr | – | BLOKK | S | Del A |

Punkt 1–3 og Sjurs «reskontro, bank, alle bilag» dekkes som for registrerte klienter. Punkt 4–17 erstattes av UR1–UR7.

---

## Dekningsmatrise

**Delvis maskinelt** betyr at et menneskesteg eller en fil fra Sjur er nødvendig for full dekning.

| Punkt | Kontroller | Merknad |
|---|---|---|
| Sjur: Leverandørreskontro avstemt | RK0, RK2, RK3, RK5, RK7, RK8, RK9, RK15, RK16, RK18, MD1 | BALANCE 2400 |
| Sjur: Kundereskontro avstemt | RK0, RK1, RK3, RK4, RK7, RK8, RK12, RK14 | BALANCE 1500 |
| Sjur: Bankkonto avstemt | BK1–BK10, BK14–BK18, BK20 | Klientens bankavstemming + BALANCE 19xx |
| Sjur: Alle bilag kontrollert for mva (kode, termin, sats) | M0, MK1, MK3–MK6, MS1–MS4, MT1–MT4, MD1, MF5, MF6, BK10, RK15, T3, MX1–MX4, MX8, MX11, MX12, MX19 | |
| Sjur: Mva-terminen avstemt i Tripletex | T0–T8, T12, T14, T15 | Fase A mot utkastet, fase B i modulen |
| Sjur: Meldingen sendt inn | IN1, IN3, IN6, IN10, IN11, F3.7, T14 | Sjur sender med ID-porten |
| Sjur: Betaling opprettet | IN13–IN18 | Claude oppretter etter ja. Godkjenning i bank med BankID. |
| 1 Alt ubehandlet tomt | F0.1, F1.1–F1.5, F1.7, F0.3, T0, BK18 | |
| 2 All omsetning bokført | F2.1–F2.9, BK3, BK16, T7, MX1, MX9, MX11, MX14, MX16 | Vipps/Stripe/kasse delvis maskinelt (krever kundens oppgjørsrapport) |
| 3 Mva-oppsett | F3.1–F3.9, T0, N6, MX7 | Profilfelt i klientprofil.md |
| 4 Innførselsmva | MI1–MI4 | Delvis maskinelt: MI2 krever Tolletaten-fil |
| 5 Omvendt avgiftsplikt | MO1–MO5, MX15 | |
| 6 Fradragsbegrensninger og forholdsmessig fradrag | MF1–MF6, MK6, MS2, MX4–MX6, MX10, MX18, MX19 | Kjøretøy hentes fra profilen |
| 7 Kreditnota, tap, uttak | KN1–KN3, TP1–TP3, UT1–UT2, RK12, MX2, MX13 | |
| 8 Kapitalvarer | KV1–KV6 | kapitalvarer.md i klientmappa |
| 9 Endringer i rapporterte terminer | ET1–ET3, MT2, BK9, MX8 | Sjur avgjør korrigert melding |
| 10 Eksport | EX1–EX5, MX13 | Delvis maskinelt: EX3 dokumentasjon |
| 11 Mva-konti mot melding, 2740, sats | M0, T1–T6, T9, T11, T16, MS3, MX17 | |
| 12 Skattekontoen | SK1–SK5, T10, BK14 | Delvis maskinelt: saldohistorikk mangler i API. /claimsAndPayments er testet i K0 og gir krav med status. |
| 13 Merknader | N1–N7, F2.9, T16 | Bare på linjenivå. Meldingsnivå settes i UI. |
| 14 Lås perioden | IN21, IN22 | Delvis maskinelt: regnskapsperioden låses av Sjur i UI |
| 15 Arkiv og logg | IN24, IN25 | |
| 16 Tilbakebetaling | IN19, IN20 | Delvis maskinelt: kontonummeret sjekker Sjur hos Skatteetaten |
| 17 Beskjed til kunden | IN26, IN18 | Delvis maskinelt: bare tekst eller utkast, Sjur sender |

## Kodefeil som må rettes før eksisterende kontroller gjenbrukes

| Fil | Feil | Konsekvens |
|---|---|---|
| tools/hent.py (l. ~127, 160, 168, 171, 180, 191, 202, 259) | Siste dag i perioden sendes som `dateTo`, men dateTo er eksklusiv | Siste dag faller ut. M0 stopper alt. |
| tools/hent.py (l. 31, 64, 65, 275, 294, 296) | `employee(firstName,lastName)` og `fields=*` på /vatReturns/status | GDPR-brudd |
| tools/kontroller/mva.py (l. 62–67, 105, 298–312) | deliveryStatus og paymentStatus (objekter) sammenlignes med strengene DELIVERED/PAID | M1 kjører aldri, og M6 er rød for alle terminer |
| tools/kontroller/mva.py / modeller.py:57 | Tomånedlig termin og frister er hardkodet | Feil for måneds- og årsklienter |
| tools/kontroller/mva.py M3 | Tar trolig med de systemgenererte 27xx-linjene i grunnlaget | Falske satsavvik |
| tools/kontroller/mva.py M4 | Flagger 7790/7400 | Falske positiver |
| tools/kontroller/reskontro.py (l. 27, 65, 69) | Filtrerer på ledgerType, og bruker «SUPPLIER» (enum er VENDOR) | R1–R5 blir stille tomme |
| tools/kontroller/bilag.py D3 | posting.date sammenlignes med voucher.date (nesten alltid like) | Slår aldri ut. Erstattes av ET2. |
| tools/kontroller/bilag.py D4 | `end` sammenlignes med siste dag i måneden | Falsk negativ |
| C:/Users/Sjur/Tripletex API/src/tripletex.js | Ingen 429/backoff og ingen felles tokencache | Struping og risiko ved rotasjon av refresh-token når flere prosesser kjører parallelt |
