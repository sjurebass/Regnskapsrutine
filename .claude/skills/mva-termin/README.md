# Mva-avstemming – designgrunnlag

Status 24.09.2026: `SKILL.md` er aktiv og beskriver den lette termin-flyten (`npm run mva` i Tripletex API, unntaksliste på maks 10 bilag, tunge kontroller med `--aarlig`). Filene under er designreferanse. I drift leser agenten bare `references/fradragsregler-kort.md`.

| Fil | Innhold |
|---|---|
| `references/arbeidsflyt.md` | Anbefalt orkestrering: stadier, porter, hva som kjører parallelt, Sjurs berøringspunkter, to-fase-avstemming, betaling, etterarbeid, modus for klienter som ikke er mva-registrert (1a), og åpne spørsmål (16) |
| `references/kontroller.md` | Kontrollkatalogen per område, med dekningsmatrise for punkt 1–17 og Sjurs opprinnelige liste. Seksjon I gjelder klienter som ikke er registrert |
| `references/endepunkter.md` | Tripletex-endepunktene per stadium, verifisert mot offentlig og intern spesifikasjon, med status testet / ikke testet |
| `references/fradragsregler.md` | Faglig grunnlag for bilagsvurderingen (mval. kap. 8 m.m.), med hjemmel og kilde på hver regel. Usikre regler står samlet i kapittel 8 |
| `references/bilagsvurdering.md` | Fremgangsmåten for agenten som vurderer bilag: uttrekk, utvalg, sjekkliste, utdataformat, eskalering, GDPR, pilot |
| `references/regelbase.json` | Maskinlesbar forhåndssjekk for alle posteringer |

Leverandørindeksen som bilagsvurderingen bruker, ligger i `C:\Users\Sjur\Tripletex API` (`npm run leverandor`).

Ingen kundenavn eller kundedata i denne mappa. Resultater fra kjøringer hører hjemme i klientmappene, og de er ikke med i git.
