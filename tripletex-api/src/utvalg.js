// Stikkprøveuttrekk av bilag – KUN LESING.
//
//   npm run -s utvalg -- --client "Klient" --fra ÅÅÅÅ-MM-DD --til ÅÅÅÅ-MM-DD [--antall N] [--metode tilfeldig|systematisk|maalrettet]
//                        [--seed <tall>] [--konto 4000-7999[,1500]] [--over <beløp>] [--risiko lav|middels|hoy] [--ut <mappe>] [--json]
//
// Populasjon: alle bokførte bilag med dato fra og med --fra til og med --til (GET /ledger/voucher), valgfritt filtrert:
//   --konto  bare bilag med minst én postering i kontointervallet (kommaseparert, «4000-7999» eller «1500»).
//   --over   (tilfeldig/systematisk) bare bilag med beløp ≥ grensen. I målrettet utvalg er --over i stedet kriteriet «stort beløp».
// Bilag uten posteringer utelates (telles i populasjon.utelatt).
// Beløp per bilag = sum debet i hovedboken (positive `amount`, inkl. mva-linjer).
//
// Metoder (fra finance-pluginens audit-support/sox-testing, oversatt til byråets praksis):
//   tilfeldig    (standard) seedet PRNG (mulberry32) og delvis Fisher–Yates over populasjonen sortert på dato, år, nummer, id.
//                Samme seed og samme populasjon gir samme utvalg. Uten --seed lages et seed, og det står i utdata.
//   systematisk  intervall k = populasjon / antall, seedet start i [0, k), hvert k-te bilag i samme sortering.
//   maalrettet   bilag med risikokjennetegn, rangert på antall kriterier og så beløp:
//                stort beløp (≥ --over, standard 5 000 = minste V), uten vedlegg (bare bilagstyper som skal ha vedlegg),
//                runde beløp (≥ 1 000 og delelig med 1 000), siste 3 dager i perioden, helg, manuelle bilag, ny leverandør.
//
// Standard --antall (audit-support-tabellen, per risiko og populasjonsstørrelse; aldri mer enn populasjonen):
//   risiko      populasjon < 250   populasjon ≥ 250
//   lav (std)          20                25
//   middels            30                40
//   hoy                40                60
//
// Heuristikker (Tripletex):
//   manuell   = bilaget har ingen bilagstype. Manuelle bilag (avansert bilag/hovedboksføring) får ingen type i Tripletex; alle
//               systemflyter (utgående faktura, leverandørfaktura, betaling, remittering, OCR, lønn, mva, reise, utlegg,
//               åpningsbalanse, øreavrunding, bankavstemming osv.) har type. Kalibrert mot én klient 14.10.2026.
//   vedlegg   = attachment, document (faktura-PDF) eller ediDocument (EHF) finnes på bilaget.
//   «uten vedlegg» teller ikke for systembilag der flyten selv er dokumentasjonen (SYSTEMTYPER under).
//   ny leverandør = leverandør-id på en postering i bilaget som ikke har postering på 2400–2499 de 12 månedene før --fra
//               (ett ekstra kall, bare ved maalrettet).
//
// Utdata: sammendrag på konsollen (populasjon antall/sum, metode, seed, antall valgt) og <ut>/utvalg.json
// (standard %TEMP%\rr\utvalg-<fra>_<til>). --json uten --ut: JSON-en på stdout i stedet for fil og sammendrag.
// --json med --ut: fil og sammendrag som uten --json.
//
// utvalg.json (versjon 1):
// { versjon: 1, kommando: "utvalg", klient, orgnr, klientId, laget: ISO-tid,
//   periode: { fra: "ÅÅÅÅ-MM-DD", til: "ÅÅÅÅ-MM-DD" },                       // begge inklusive
//   filter: { konto: "4000-7999" | null, over: <beløp> | null },              // populasjonsfilter (over bare ved tilfeldig/systematisk)
//   populasjon: { antall, sum, utelatt: { utenPosteringer, utenforKonto, underBelop } },
//   metode: "tilfeldig" | "systematisk" | "maalrettet", seed: <heltall>, seedKilde: "angitt" | "generert",
//   risiko: "lav" | "middels" | "hoy", antallForespurt, antallKilde: "angitt" | "tabell (…)", antallValgt,
//   systematisk: { intervall, start } | null,
//   kriterier: { over, overKilde, rundeBelop, sisteDager, helg, manuell, utenVedlegg, nyLeverandor } | null,   // bare maalrettet
//   kandidater: <antall bilag som traff minst ett kriterium> | null,
//   heuristikk: { manuell, vedlegg, belop },
//   utvalg: [ { nr, id, bilag: "<nummer>-<år>", nummer, aar, dato, belop, vedlegg, bilagstype, manuell, tekst, kontoer: [<nr>],
//               begrunnelse: ["tilfeldig"] | ["systematisk, posisjon 9"] | ["stort beløp ≥ 5 000", "uten vedlegg", …] } ],
//   merknader: [] }
// `tekst` er bilagsbeskrivelsen maskert (se tekstFor): redactText(), motpart i systemtekster som «kunde <nr>»/«leverandør <id>», ord med
// stor forbokstav etter første ord som «…»; personbilag (reise, utlegg, lønn, pensjon, sykepenger) får bare bilagstypen.
// Navn kan likevel stå i fritekst: siter aldri `tekst` i chat – bruk bilagsnummer, dato, konto og beløp.

import { writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { randomInt } from 'node:crypto';
import { connect } from './tripletex.js';
import { redactText } from './privacy.js';
import { argumenter, utmappe, kortFeil, rund } from './valg.js';

const METODER = ['tilfeldig', 'systematisk', 'maalrettet'];
const TABELL = { lav: [20, 25], middels: [30, 40], hoy: [40, 60] };
// Systembilag der flyten selv er dokumentasjonen – «uten vedlegg» er ikke et funn for disse.
const SYSTEMTYPER = new Set(['Betaling', 'Remittering', 'OCR giro', 'Lønnsbilag', 'Terminoppgave', 'Mva-melding', 'Åpningsbalanse',
  'Øreavrunding', 'Purring', 'Obligatorisk tjenestepensjon', 'Refusjon av sykepenger']);
// Bilag som gjelder én person – teksten erstattes med bilagstypen.
const PERSONTYPER = new Set(['Reiseregning', 'Ansattutlegg', 'Lønnsbilag', 'Obligatorisk tjenestepensjon', 'Refusjon av sykepenger']);
const STD_OVER = 5000; // minste vesentlighetsgrense i CLAUDE.md

const erDato = (s) => /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/.test(s ?? '') && !Number.isNaN(Date.parse(`${s}T00:00:00Z`));
const plussDager = (d, n) => { const x = new Date(`${d}T00:00:00Z`); x.setUTCDate(x.getUTCDate() + n); return x.toISOString().slice(0, 10); };
const plussMnd = (d, n) => { const x = new Date(`${d}T00:00:00Z`); x.setUTCMonth(x.getUTCMonth() + n); return x.toISOString().slice(0, 10); };
const kr = (n) => { const s = Math.round(Math.abs(n)).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ' '); return n < 0 ? `-${s}` : s; };
const tall = (s) => { const n = Number(String(s).replace(/\s/g, '').replace(',', '.')); return Number.isFinite(n) ? n : NaN; };

/** Seedet PRNG (mulberry32): samme seed gir samme tallrekke i [0, 1). */
export function mulberry32(seed) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/** «4000-7999,1500» → [[4000, 7999], [1500, 1500]]. */
function kontointervall(s) {
  if (s === undefined) return null;
  const ut = String(s).split(',').map((d) => d.trim()).filter(Boolean).map((d) => {
    const m = d.match(/^(\d{4})(?:\s*[-–]\s*(\d{4}))?$/);
    if (!m) throw new Error(`--konto «${d}» er ikke et kontonummer eller intervall (f.eks. 4000-7999). Ingenting er gjort.`);
    const a = Number(m[1]), b = Number(m[2] ?? m[1]);
    return [Math.min(a, b), Math.max(a, b)];
  });
  if (!ut.length) throw new Error('--konto mangler verdi. Ingenting er gjort.');
  return ut;
}

/**
 * Bilagstekst uten personopplysninger: redactText() (kontonr., e-post, tlf. osv.), motpart i faste systemtekster byttes med
 * «kunde <nr>»/«leverandør <id>», og ord med stor forbokstav etter første ord (mulige navn) blir «…». Forkortelser i
 * bare store bokstaver beholdes. Personbilag (reise, utlegg, lønn, pensjon, sykepenger) får bare bilagstypen.
 */
export function tekstFor(v) {
  const type = v.voucherType?.name ?? null;
  if (type && PERSONTYPER.has(type)) return type;
  const lev = [...new Set((v.postings ?? []).map((p) => p.supplier?.id).filter(Boolean))];
  let s = redactText(String(v.description ?? '')).replace(/\s+/g, ' ').trim();
  s = s.replace(/^((?:Betaling: )?(?:Faktura|Kreditnota) nummer \d+ til ).*?(?:\((\d+)\).*)?$/i, (m, pre, nr) => `${pre.replace(/^Betaling: F/, 'Betaling: f').replace(/^Betaling: K/, 'Betaling: k')}kunde${nr ? ` ${nr}` : ''}`);
  s = s.replace(/^((?:Faktura|Kreditnota) nummer \d+ fra ).+$/i, (m, pre) => `${pre}leverandør${lev.length === 1 ? ` ${lev[0]}` : ''}`);
  s = s.split(' ').map((w, i) => (i > 0 && /^[«"'(]?[A-ZÆØÅÄÖÜ][a-zæøåäöüéè]/.test(w) ? '…' : w)).join(' ').replace(/…(?: …)+/g, '…');
  return s.slice(0, 120);
}

function bruk(melding) {
  return Object.assign(new Error(`${melding ? `${melding}\n` : ''}Bruk: npm run -s utvalg -- --client "Klient" --fra ÅÅÅÅ-MM-DD --til ÅÅÅÅ-MM-DD [--antall N] ` +
    '[--metode tilfeldig|systematisk|maalrettet] [--seed <tall>] [--konto 4000-7999] [--over <beløp>] [--risiko lav|middels|hoy] [--ut <mappe>] [--json]\nIngenting er gjort.'), { bruk: true });
}

async function main() {
  const a = argumenter(process.argv.slice(2));
  if (typeof a.client !== 'string') throw bruk('Angi --client "klient".');
  if (!erDato(a.fra) || !erDato(a.til) || a.fra > a.til) throw bruk('Angi --fra og --til som ÅÅÅÅ-MM-DD (fra ≤ til).');
  const metode = typeof a.metode === 'string' ? a.metode.toLowerCase().replace('å', 'aa') : 'tilfeldig';
  if (!METODER.includes(metode)) throw bruk(`Ukjent --metode «${a.metode}».`);
  const risiko = typeof a.risiko === 'string' ? a.risiko.toLowerCase().replace('ø', 'o') : 'lav';
  if (!TABELL[risiko]) throw bruk(`Ukjent --risiko «${a.risiko}» (lav, middels, hoy).`);
  let antallAngitt = null;
  if (a.antall !== undefined) {
    antallAngitt = Number(a.antall);
    if (!Number.isInteger(antallAngitt) || antallAngitt < 1) throw bruk('--antall må være et heltall ≥ 1.');
  }
  let seed, seedKilde;
  if (a.seed !== undefined) {
    seed = Number(a.seed);
    if (!Number.isInteger(seed) || seed < 0 || seed > 4294967295) throw bruk('--seed må være et heltall 0–4294967295.');
    seedKilde = 'angitt';
  } else { seed = randomInt(1, 2 ** 31); seedKilde = 'generert'; }
  const konto = kontointervall(a.konto);
  let over = null;
  if (a.over !== undefined) { over = tall(a.over); if (!(over >= 0)) throw bruk('--over må være et beløp ≥ 0.'); }

  const c = await connect(a.client);
  const merknader = [];

  // ── Populasjon ────────────────────────────────────────────────────────────
  const bilag = await c.list('/ledger/voucher', { query: { dateFrom: a.fra, dateTo: plussDager(a.til, 1),
    fields: 'id,number,year,date,description,voucherType(id,name),attachment(id),document(id),ediDocument(id),' +
      'postings(row,amount,account(number),supplier(id))' } });
  const utelatt = { utenPosteringer: 0, utenforKonto: 0, underBelop: 0 };
  const iKonto = (n) => konto.some(([x, y]) => n >= x && n <= y);
  const filterOver = metode !== 'maalrettet' ? over : null;
  const pop = [];
  for (const v of bilag) {
    const p = v.postings ?? [];
    if (!p.length) { utelatt.utenPosteringer++; continue; }
    const kontoer = [...new Set(p.map((x) => x.account?.number).filter(Boolean))].sort((x, y) => x - y);
    if (konto && !kontoer.some(iKonto)) { utelatt.utenforKonto++; continue; }
    const belop = rund(p.reduce((s, x) => s + Math.max(x.amount ?? 0, 0), 0));
    if (filterOver !== null && belop < filterOver) { utelatt.underBelop++; continue; }
    const type = v.voucherType?.name ?? null;
    pop.push({
      id: v.id, bilag: `${v.number}-${v.year}`, nummer: v.number, aar: v.year, dato: v.date, belop,
      vedlegg: Boolean(v.attachment?.id || v.document?.id || v.ediDocument?.id), bilagstype: type, manuell: !type,
      tekst: tekstFor(v), kontoer,
      _lev: [...new Set(p.map((x) => x.supplier?.id).filter(Boolean))],
    });
  }
  pop.sort((x, y) => String(x.dato).localeCompare(String(y.dato)) || (x.aar - y.aar) || (x.nummer - y.nummer) || (x.id - y.id));
  const popSum = rund(pop.reduce((s, x) => s + x.belop, 0));

  const tabell = TABELL[risiko][pop.length >= 250 ? 1 : 0];
  const antallForespurt = antallAngitt ?? tabell;
  const antallKilde = antallAngitt ? 'angitt' : `tabell (risiko ${risiko}, populasjon ${pop.length >= 250 ? '≥ 250' : '< 250'})`;
  const n = Math.min(antallForespurt, pop.length);
  if (antallForespurt > pop.length) merknader.push(`Forespurt ${antallForespurt}, men populasjonen har bare ${pop.length} bilag – alle er valgt.`);

  // ── Utvalg ───────────────────────────────────────────────────────────────
  const rng = mulberry32(seed);
  let valgt = [];
  let systematisk = null, kriterier = null, kandidater = null;
  if (metode === 'tilfeldig') {
    const idx = pop.map((_, i) => i);
    for (let i = 0; i < n; i++) {
      const j = i + Math.floor(rng() * (idx.length - i));
      [idx[i], idx[j]] = [idx[j], idx[i]];
    }
    valgt = idx.slice(0, n).map((i) => ({ ...pop[i], begrunnelse: ['tilfeldig'], _pos: i }));
  } else if (metode === 'systematisk') {
    if (n > 0) {
      const k = pop.length / n;
      const start = rng() * k;
      systematisk = { intervall: Math.round(k * 100) / 100, start: Math.round(start * 100) / 100 };
      for (let i = 0; i < n; i++) {
        const pos = Math.min(pop.length - 1, Math.floor(start + i * k));
        valgt.push({ ...pop[pos], begrunnelse: [`systematisk, posisjon ${pos + 1}`], _pos: pos });
      }
    }
  } else {
    const grense = over ?? STD_OVER;
    const sisteFra = plussDager(a.til, -2);
    // Ny leverandør: leverandører i populasjonen uten postering på 2400–2499 de 12 månedene før --fra.
    const levIPop = new Set(pop.flatMap((x) => x._lev));
    let tidligere = null;
    if (levIPop.size) {
      try {
        const post = await c.list('/ledger/posting', { query: { dateFrom: plussMnd(a.fra, -12), dateTo: a.fra, accountNumberFrom: 2400, accountNumberTo: 2499, fields: 'supplier(id)' } });
        tidligere = new Set(post.map((p) => p.supplier?.id).filter(Boolean));
      } catch (e) { merknader.push(`Ny leverandør kunne ikke avgjøres (${kortFeil(e)}).`); }
    }
    kriterier = {
      over: grense, overKilde: over !== null ? 'angitt' : 'standard (minste V i CLAUDE.md)',
      rundeBelop: 'beløp ≥ 1 000 og delelig med 1 000', sisteDager: `dato ${sisteFra}–${a.til}`, helg: 'lørdag eller søndag',
      manuell: 'bilag uten bilagstype (manuelt bilag)', utenVedlegg: 'ingen vedlegg, dokument eller EHF (ikke systembilag)',
      nyLeverandor: tidligere ? `ingen postering på 2400–2499 ${plussMnd(a.fra, -12)}–${plussDager(a.fra, -1)}` : 'ikke avgjort',
    };
    const treff = [];
    for (const [i, x] of pop.entries()) {
      const g = [];
      if (x.belop >= grense) g.push(`stort beløp ≥ ${kr(grense)}`);
      if (!x.vedlegg && !(x.bilagstype && SYSTEMTYPER.has(x.bilagstype))) g.push('uten vedlegg');
      if (x.belop >= 1000 && Math.abs(x.belop % 1000) < 0.005) g.push('rundt beløp');
      if (x.dato >= sisteFra) g.push('siste 3 dager i perioden');
      const dag = new Date(`${x.dato}T00:00:00Z`).getUTCDay();
      if (dag === 0 || dag === 6) g.push('helg');
      if (x.manuell) g.push('manuelt bilag');
      if (tidligere && x._lev.some((l) => !tidligere.has(l))) g.push('ny leverandør');
      if (g.length) treff.push({ ...x, begrunnelse: g, _pos: i });
    }
    kandidater = treff.length;
    merknader.push('Målrettet utvalg bruker ikke seed: rangeringen er fast (antall kriterier, så beløp).');
    treff.sort((x, y) => (y.begrunnelse.length - x.begrunnelse.length) || (y.belop - x.belop) || (x._pos - y._pos));
    valgt = treff.slice(0, n);
    if (treff.length > n) merknader.push(`${treff.length} bilag traff minst ett kriterium; de ${n} med flest kriterier (så høyest beløp) er valgt.`);
  }
  valgt.sort((x, y) => x._pos - y._pos);
  const utvalg = valgt.map((x, i) => {
    const { _lev, _pos, ...rest } = x;
    return { nr: i + 1, ...rest };
  });

  const res = {
    versjon: 1, kommando: 'utvalg', klient: c.company.name, orgnr: c.company.organizationNumber ?? '', klientId: c.company.id,
    laget: new Date().toISOString(),
    periode: { fra: a.fra, til: a.til },
    filter: { konto: konto ? konto.map(([x, y]) => (x === y ? `${x}` : `${x}-${y}`)).join(',') : null, over: filterOver },
    populasjon: { antall: pop.length, sum: popSum, utelatt },
    metode, seed, seedKilde, risiko, antallForespurt, antallKilde, antallValgt: utvalg.length,
    systematisk, kriterier, kandidater,
    heuristikk: {
      manuell: 'manuelt = bilaget har ingen bilagstype (avansert bilag/hovedboksføring); systemflytene har alltid type',
      vedlegg: 'vedlegg = attachment, document eller ediDocument på bilaget',
      belop: 'beløp = sum debet (positive posteringer i hovedboken, inkl. mva-linjer)',
    },
    utvalg,
    merknader,
  };

  if (a.json && typeof a.ut !== 'string') { console.log(JSON.stringify(res, null, 1)); return; }
  const fil = join(utmappe(a.ut, 'utvalg', `${a.fra}_${a.til}`), 'utvalg.json');
  writeFileSync(fil, JSON.stringify(res, null, 1));

  console.log(`${res.klient} ${a.fra}–${a.til}: populasjon ${pop.length} bilag, sum ${kr(popSum)} kr` +
    `${res.filter.konto ? ` (konto ${res.filter.konto})` : ''}${filterOver !== null ? ` (beløp ≥ ${kr(filterOver)})` : ''}.`);
  const ut = Object.entries(utelatt).filter(([, v]) => v).map(([k, v]) => `${v} ${k}`);
  if (ut.length) console.log(`Utelatt: ${ut.join(', ')}.`);
  console.log(`Metode ${metode}, seed ${seed} (${seedKilde}), risiko ${risiko}: ${utvalg.length} valgt av ${antallForespurt} forespurt (${antallKilde})` +
    `${systematisk ? `, intervall ${systematisk.intervall}, start ${systematisk.start}` : ''}${kandidater !== null ? `, ${kandidater} kandidater` : ''}.`);
  const telle = (f) => utvalg.filter(f).length;
  console.log(`Utvalget: sum ${kr(utvalg.reduce((s, x) => s + x.belop, 0))} kr · uten vedlegg ${telle((x) => !x.vedlegg)} · manuelle ${telle((x) => x.manuell)}.`);
  for (const x of utvalg) console.log(`  ${String(x.nr).padStart(3)}  ${x.bilag.padEnd(10)} ${x.dato}  ${kr(x.belop).padStart(12)}  ${x.begrunnelse.join(', ')}`);
  if (merknader.length) console.log(`Merknader:\n- ${merknader.join('\n- ')}`);
  console.log(`Skrevet: ${fil}`);
}

main().catch((e) => { console.error(e.bruk ? e.message : `Feil: ${redactText(kortFeil(e))}`); process.exitCode = 1; });
