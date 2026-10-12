# Mva-termin – designgrunnlag

`SKILL.md` er driftsflyten. Filene under er designreferanse fra september 2026 og leses bare med grep ved konkrete oppslag, eller når flyten
skal videreutvikles. Unntaket er `references/fradragsregler-kort.md`, som agenten på unntakslista leser.

| Fil | Innhold |
|---|---|
| `references/fradragsregler-kort.md` | Kortversjonen av fradragsreglene. Brukes i drift. |
| `references/fradragsregler.md` | Faglig grunnlag for bilagsvurderingen (mval. kap. 8 m.m.), med hjemmel og kilde. Usikre regler i kapittel 8. |
| `references/bilagsvurdering.md` | Fremgangsmåten for agenten som vurderer bilag: uttrekk, utvalg, sjekkliste, utdataformat, eskalering, GDPR. |
| `references/arbeidsflyt.md` | Orkestrering, porter, Sjurs berøringspunkter, betaling, etterarbeid, ikke-registrerte klienter (1a). Praksis fra første fulle kjøring i §0a. |
| `references/kontroller.md` | Kontrollkatalogen per område med dekningsmatrise. Seksjon I gjelder ikke-registrerte klienter. |
| `references/endepunkter.md` | Tripletex-endepunktene per stadium, med status testet / ikke testet og kalibreringen fra 25.09.2026. |
| `references/kalibrering.md` | Kalibreringsresultater (K0). |
| `references/regelbase.json` | Maskinlesbar forhåndssjekk for posteringer (brukes av CLI-skriptet). |

Der designdokumentene nevner `klientprofil.md`, `kjente-avvik.md`, `logg.md` eller kundemapper, gjelder nå kundeinstruksen i Tally
(skillen `kundeinstruks`). Leverandørindeksen ligger i `data/leverandorer.json` (skillen `leverandorindeks`).

Ingen kundenavn eller kundedata i denne mappa.
