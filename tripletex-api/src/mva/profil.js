// Valgfri lokal klientprofil og kjente avvik (styrer kontoer, vesentlighet og demping i mva-flyten).
//
// Leses bare når miljøvariabelen AVSTEMMINGER_ROT er satt: klientmappa finnes på navn («<Firmanavn> (<nr>)»)
// under den mappa, med klientprofil.md og kjente-avvik.md. Uten AVSTEMMINGER_ROT brukes standardprofilen
// (klientregler står i kundeinstruksen i Tally). Filene leses bare – endringer skrives først etter ja.

import { readdirSync, readFileSync, existsSync } from 'node:fs';
import { join } from 'node:path';
import { norm } from '../leverandor.js';

export const AVSTEMMINGER_ROT = process.env.AVSTEMMINGER_ROT?.trim() || null;

const kjerne = (navn) => norm(String(navn).replace(/\(.*?\)/g, '')).replace(/\b(as|asa)\b/g, '').replace(/\s+/g, '');

/** Finn klientmappa for et firmanavn. null hvis AVSTEMMINGER_ROT ikke er satt, eller ingen eller flere passer. */
export function finnKlientmappe(firmanavn) {
  if (!AVSTEMMINGER_ROT || !existsSync(AVSTEMMINGER_ROT)) return null;
  const k = kjerne(firmanavn);
  const treff = readdirSync(AVSTEMMINGER_ROT, { withFileTypes: true })
    .filter((d) => d.isDirectory() && kjerne(d.name) === k)
    .map((d) => join(AVSTEMMINGER_ROT, d.name));
  return treff.length === 1 ? treff[0] : null;
}

/** Leser alle «| felt | verdi |»-rader fra markdown-tabeller til et objekt. */
function tabellFelt(md) {
  const ut = {};
  for (const linje of md.split('\n')) {
    const m = linje.match(/^\|\s*([a-z_æøå0-9]+)\s*\|\s*(.*?)\s*\|\s*$/i);
    if (m && m[1] !== 'Felt' && !/^-+$/.test(m[1])) ut[m[1]] = m[2];
  }
  return ut;
}

const tall = (v, standard) => { const n = Number(String(v ?? '').replace(/\s/g, '').replace(',', '.')); return Number.isFinite(n) && v !== '' && v !== '-' ? n : standard; };
const liste = (v) => (!v || v === '-' ? [] : String(v).split(/[,;]/).map((s) => s.trim()).filter(Boolean));

/** Kontointervaller fra tekst som «4500-4599, 1130» → [[4500,4599],[1130,1130]]. */
export function kontoIntervaller(v) {
  return liste(v).map((s) => s.split(/[-–]/).map(Number)).filter(([a]) => Number.isFinite(a)).map(([a, b]) => [a, Number.isFinite(b) ? b : a]);
}
export const iIntervall = (nr, intervaller) => intervaller.some(([a, b]) => nr >= a && nr <= b);

/**
 * Profilen med standardverdier. Nye felt for mva-flyten (alle valgfrie):
 *   konto_prosjekt            prosjekt-/byggekostnadskontoer, f.eks. «4500-4599» (§ 3-26)
 *   inntekt_klassifisering    «3200-3299: unntatt; 3900: utenfor» (UR3). Klasser: avgiftspliktig, unntatt, utenfor
 *   s3_26_vurdering           «2026-09-24: ingen plikt – bare administrasjon» (UR4)
 *   periodelaas_etter_mva     ja/nei
 */
export function lesProfil(klientmappe) {
  const fil = klientmappe && join(klientmappe, 'klientprofil.md');
  const f = fil && existsSync(fil) ? tabellFelt(readFileSync(fil, 'utf8')) : {};
  const inntekt = liste(f.inntekt_klassifisering).map((s) => {
    const [kontoer, klasse] = s.split(':').map((x) => x.trim());
    return { intervaller: kontoIntervaller(kontoer), klasse: (klasse ?? '').toLowerCase() };
  }).filter((x) => x.intervaller.length && x.klasse);
  return {
    funnet: !!Object.keys(f).length,
    felt: f,
    vesentlighet: tall(f.vesentlighet, 5000),
    kontoKunde: kontoIntervaller(f.konto_kunde).length ? kontoIntervaller(f.konto_kunde) : [[1500, 1500]],
    kontoLeverandor: kontoIntervaller(f.konto_leverandor).length ? kontoIntervaller(f.konto_leverandor) : [[2400, 2400]],
    kontoProsjekt: kontoIntervaller(f.konto_prosjekt),
    inntektKlassifisering: inntekt,
    s326: f.s3_26_vurdering && f.s3_26_vurdering !== '-' ? f.s3_26_vurdering : null,
    deaktiverte: liste(f.deaktiverte_kontroller),
  };
}

/** Kjente avvik: nøkkel → { kontroll, forklaring, gyldigTil }. Utløpte linjer tas ikke med. */
export function lesKjenteAvvik(klientmappe, idag = new Date().toISOString().slice(0, 10)) {
  const fil = klientmappe && join(klientmappe, 'kjente-avvik.md');
  if (!fil || !existsSync(fil)) return new Map();
  const ut = new Map();
  for (const linje of readFileSync(fil, 'utf8').split('\n')) {
    const celler = linje.split('|').slice(1, -1).map((c) => c.trim());
    if (celler.length < 3 || celler[0] === 'Nøkkel' || /^-+$/.test(celler[0]) || !celler[0]) continue;
    const [noekkel, kontroll, forklaring, gyldigTil = ''] = celler;
    if (gyldigTil && gyldigTil < idag) continue;
    ut.set(noekkel, { kontroll, forklaring, gyldigTil });
  }
  return ut;
}
