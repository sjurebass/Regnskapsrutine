---
name: "leverandorindeks"
description: "Felles leverandørindeks for alle klienter (data/leverandorer.json): fakta fra Enhetsregisteret og byråets vurdering av mva-behandling (utenlandsk, omvendt avgiftsplikt, VOEC, kostnadstype, fradrag, sats). Slås opp før nettsøk; nye vurderinger lagres her. Ingen Tally-oppgave. Bruk ved «finn leverandøren», «er <leverandør> mva-registrert», «hvilken mva-kode for <leverandør>», «omvendt avgiftsplikt», «VOEC», «vurder leverandøren», og når bilagskontroll eller mva-kontroll møter en ukjent eller utenlandsk leverandør."
---

# Leverandørindeks

`data/leverandorer.json` i repoet er byråets felles minne om leverandører: hva Enhetsregisteret sier, og hvordan byrået har vurdert mva-behandlingen.
Når en klient har brukt en leverandør, slipper neste klient å vurdere den på nytt. Hvordan bilaget føres, avgjøres i `bilagsforing` og `bilagskontroll`.

## Når

- Når `bilagskontroll` eller `mva-kontroll` møter en ukjent eller utenlandsk leverandør, i `bilagsforing` når brukeren ber om det,
  og når brukeren spør om en leverandør.
- Krever filsystemet (Claude Code med repoet åpent). Uten repoet: slå opp i Enhetsregisteret (Tally `lookup_brreg`) og si at vurderingen ikke er lagret.

## Kundeinstruks

«Mva» (registrert ja/nei) avgjør om omvendt avgiftsplikt gjelder klienten. Indeksen selv inneholder aldri klientopplysninger.

## Steg

### 1. Slå opp (før nettsøk)

1. `npm run -s leverandor -- finn <orgnr|navn> --json` søker i indeksen (org.nr., kompaktnavn, aliaser og hash; ingen nettverkskall).
   Hele posten: `npm run -s leverandor -- vis <orgnr|nøkkel|navn> --json`.
2. Ingen treff, norsk org.nr.: `npm run -s leverandor -- oppslag <orgnr> [--alias "navn i Tripletex"] --json` henter fakta fra Enhetsregisteret og
   legger dem i indeksen (bare fakta, ingen vurdering). Bare navn: Tally `lookup_brreg` først for å finne org.nr.
3. Utenlandsk leverandør uten norsk org.nr.: sjekk om den er registrert i VOEC eller har norsk mva-nummer (da tar den norsk mva, og kode 86 skal ikke brukes).
4. Oversikt: `npm run -s leverandor -- liste [--ukjente] [--utland] [--uten-mva] [--uvurdert] [--utdatert] --json`. Alle leverandører hos én klient
   inn i indeksen (etter ja): `npm run -s leverandor -- importer --client "<klient>" --json`.

### 2. Vurder og lagre (etter ja)

1. Vurder ut fra faktura, leverandørens nettside og regelverket (`docs/fradragsregler-kort.md`). Oppgi kilde.
2. Vis brukeren posten som legges til eller endres.
3. Ved ja (utenlandsk uten norsk org.nr.: legg til `--navn "…" --land <kode>`):
   `npm run -s leverandor -- vurder <orgnr|nøkkel|navn> --omvendt <86–92|nei> --voec ja|nei --kostnadstype "…" --fradrag "…" --sats "…" --kilde "…" --sikkerhet høy|middels|lav --av agent --json`
   Kommandoen holder `aliaser` og `oppdatert` i takt, lagrer ENK og personnavn bare som hash, og overskriver ikke en vurdering fra en
   regnskapsfører (`--tving` brukes aldri av Claude). `--av` er `agent`, eller regnskapsførerens initialer når de selv har vurdert.
4. Endringer i fila er endringer i repoet: commit med en kort melding når brukeren vil.

### 3. Formatet

```json
{
  "versjon": 1, "oppdatert": "ÅÅÅÅ-MM-DD",
  "leverandorer": {
    "NO:986398929": {
      "nokkel": "NO:986398929", "aliaser": ["kompaktnavn", "h:…"], "opprettet": "ÅÅÅÅ-MM-DD",
      "orgnr": "986398929", "navn": "…", "enk": false, "organisasjonsform": "NUF", "underenhet_av": null, "land": "NO",
      "mva_registrert": false, "mva_registrert_fra": null, "naeringskode": "65.120", "naering": "Skadeforsikring",
      "status": "aktiv", "brreg_sjekket": "ÅÅÅÅ-MM-DD",
      "vurdering": {
        "omvendt_avgiftsplikt": false, "voec": false, "kostnadstype": "…", "fradrag": "…", "sats": "unntatt",
        "kilde": "lovhenvisning, faktura eller URL", "sikkerhet": "høy", "vurdert_av": "agent", "vurdert": "ÅÅÅÅ-MM-DD"
      }
    }
  },
  "aliaser": { "kompaktnavn": "NO:986398929" }
}
```

- `nokkel`: `NO:<org.nr.>` for norske, `<landkode>:<kompaktnavn>` for utenlandske uten norsk org.nr.
- Kompaktnavn: små bokstaver, æ/ä → ae, ø/ö → o, å → a, ü → u, é/è → e, «a/s» → as, og alt annet enn a–z og 0–9 fjernet
  (for eksempel «Bølgen & Moi A/S» → `bolgenmoias`). Hash: `h:` + de 16 første hex-tegnene av SHA-256 av kompaktnavnet.
- `omvendt_avgiftsplikt`: `false`, eller mva-koden som skal brukes (for eksempel `86` for tjenester kjøpt fra utlandet).
- `sikkerhet`: `høy`, `middels` eller `lav`. `vurdert_av`: `agent` eller regnskapsførerens `<initialer>`.

## Svar

Kort: registrert i Mva-registeret (fra dato), status (aktiv, konkurs, slettet), og vurderingen med kilde og sikkerhet hvis den finnes.
Ny vurdering: posten som legges til, før den lagres.

## Lever

Ingen fil og ingen Tally-oppgave. Leveransen er posten i `data/leverandorer.json`.

## Fallgruver

- Indeksen lagrer bare virksomheter: org.nr., navn, organisasjonsform, land, mva-registrering, næring, status og vurdering. Ingen adresse,
  e-post, telefon eller kontonummer, og ingen opplysninger om hvilke klienter som bruker leverandøren.
- Enkeltpersonforetak (ENK) og navn som kan være en person lagres **uten navn**, bare som hash i `aliaser` (`h:<16 hex>`).
- En vurdering med `"vurdert_av": "<initialer>"` (en regnskapsfører) overskrives aldri av en agent. Uenighet sies i chatten.
- Gjett aldri mva-behandling uten kilde.

## Referanser

- `docs/fradragsregler-kort.md` (kortversjon) og `docs/fradragsregler.md` (rettsgrunnlag).
- Brukes av `bilagsforing`, `bilagskontroll` og `mva-kontroll`.
