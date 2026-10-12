---
name: "leverandorindeks"
description: "Felles leverandørindeks for alle klienter (data/leverandorer.json): fakta fra Enhetsregisteret og byråets vurdering av mva-behandling (utenlandsk, omvendt avgiftsplikt, VOEC, kostnadstype, fradrag, sats). Slå opp her før nettsøk, og lagre nye vurderinger her så de gjenbrukes. Bruk ved «finn leverandøren», «er <leverandør> mva-registrert», «hvilken mva-kode for <leverandør>», «omvendt avgiftsplikt», «vurder leverandøren», og når bilagsforing eller mva-termin møter en ukjent eller utenlandsk leverandør."
---

# Leverandørindeks

`data/leverandorer.json` i repoet er byråets felles minne om leverandører: hva Enhetsregisteret sier, og hvordan byrået har vurdert mva-behandlingen.
Når en klient har brukt en leverandør, slipper neste klient å vurdere den på nytt. Skillene `bilagsforing` og `mva-termin` bruker den.

Skillen krever filsystemet (Claude Code med repoet åpent). I Claude Desktop uten repoet: slå opp i Brreg og si at vurderingen ikke er lagret.

## Faste regler

- **Slå opp i indeksen før du søker på nett.**
- Indeksen lagrer bare virksomheter: org.nr., navn, organisasjonsform, land, mva-registrering, næring, status og vurdering.
  Enkeltpersonforetak (ENK) og navn som kan være en person lagres **uten navn**, bare som hash i `aliaser` (`h:<16 hex>`). Ingen adresse, e-post,
  telefon eller kontonummer. Ingen opplysninger om hvilke klienter som bruker leverandøren.
- En vurdering med `"vurdert_av": "Sjur"` (eller en annen regnskapsfører) overskrives aldri av en agent. Uenighet sies i chatten.
- Endringer i fila er endringer i repoet: vis hva som legges til, og commit med en kort melding når brukeren vil.

## Formatet

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
- `sikkerhet`: `høy`, `middels` eller `lav`.

## Slå opp

1. Søk med Grep i `data/leverandorer.json` på org.nr. eller kompaktnavn (delstreng). Treff i `aliaser` peker på nøkkelen.
2. Gi svaret kort: registrert i Mva-registeret (fra dato), status (aktiv, konkurs, slettet), og vurderingen hvis den finnes.
3. Ingen treff: slå opp i Enhetsregisteret med Tripletex-MCP-en `lookup_company_in_brreg` (org.nr. eller navn), eller
   `https://data.brreg.no/enhetsregisteret/api/enheter/<orgnr>`.
4. Utenlandsk leverandør uten norsk org.nr.: sjekk om den er registrert i VOEC eller har norsk mva-nummer (da tar den norsk mva og kode 86 skal ikke brukes).

## Vurder og lagre

1. Vurder ut fra faktura, leverandørens nettside og regelverket (`mva-termin/references/fradragsregler-kort.md`). Oppgi kilde.
2. Vis brukeren posten som legges til eller endres.
3. Ved ja: oppdater fila med Edit, eller med et lite Node-skript som leser, endrer og skriver hele JSON-en (behold `aliaser`-kartet i takt med postene,
   og oppdater `oppdatert`). Skriv aldri navnet i klartekst for ENK eller personnavn; bruk hash eller la `navn` være `null`.
4. Kontroller at fila fortsatt er gyldig JSON (`node -e "JSON.parse(require('fs').readFileSync('data/leverandorer.json','utf8'))"`).

## Hurtigvei – bare Sjur

CLI-et i `C:\Users\Sjur\Tripletex API` kan lese og skrive samme fil når `LEVERANDOR_INDEKS` i `.env` der peker hit:

```powershell
npm --prefix "C:\Users\Sjur\Tripletex API" run -s leverandor -- finn <orgnr|navn>
npm --prefix "C:\Users\Sjur\Tripletex API" run -s leverandor -- importer --client "<klient>" --fra ÅÅÅÅ-MM-DD --til ÅÅÅÅ-MM-DD
npm --prefix "C:\Users\Sjur\Tripletex API" run -s leverandor -- vurder <orgnr|navn> --omvendt 86 --kostnadstype ".." --kilde ".." --sikkerhet høy
```

`importer` legger til alle leverandører med poster på 2400–2499 i perioden og slår opp de ukjente i Enhetsregisteret. Den tåler parallelle agenter
(lås og atomisk skriving).

## Det du aldri gjør

- Lagrer personnavn, adresser, e-post, telefon eller kontonummer.
- Lagrer hvilke klienter som bruker en leverandør.
- Overskriver en vurdering gjort av en regnskapsfører.
- Gjetter mva-behandling uten kilde.
