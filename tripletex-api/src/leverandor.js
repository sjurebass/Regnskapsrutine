// Leverandørindeks: leverandører som er slått opp og vurdert én gang, gjenbrukt på tvers av klienter.
//
//   npm run leverandor -- finn <orgnr|navn>                 søk i indeksen (ingen nettverkskall)
//   npm run leverandor -- vis <orgnr|nøkkel|navn>           hele posten
//   npm run leverandor -- oppslag <orgnr> [--alias "navn i Tripletex"]      Brønnøysund → indeksen
//   npm run leverandor -- importer --client "klient" [--fra ÅÅÅÅ-MM-DD] [--til ÅÅÅÅ-MM-DD]
//   npm run leverandor -- vurder <orgnr|nøkkel|navn> [--navn "navn"] [--land IE] [--omvendt 86]
//            [--voec ja|nei] [--kostnadstype ".."] [--fradrag ".."] [--sats ".."] [--notat ".."]
//            [--kilde ".."] [--sikkerhet høy|middels|lav] [--av agent|<initialer>] [--tving]
//   npm run leverandor -- liste [--ukjente] [--utland] [--uten-mva] [--uvurdert] [--utdatert]
//   npm run leverandor -- oppdater [--maks-alder 30]
//   Alle kommandoer tar --json for maskinlesbar utskrift (for agenter).
//
// Indeksen (data/leverandorer.json i repo-rota, eller LEVERANDOR_INDEKS) har to lag:
//   fakta     – fra Enhetsregisteret: org.form, land, mva-registrert (og fra dato), næringskode, status.
//               Friskes opp automatisk når de er eldre enn --maks-alder dager (standard 30).
//   vurdering – det agenten eller en regnskapsfører har vurdert: utenlandsk, omvendt avgiftsplikt (kode), VOEC,
//               kostnadstype, fradrag, sats, notat, kilde. Overskrives aldri automatisk. En vurdering gjort av en
//               regnskapsfører (--av <initialer>, alt annet enn «agent») overskrives ikke av andre uten --tving.
// Nøkler: «NO:<orgnr>» (norsk org.nr.), «UT:<navn>» (utenlandsk uten norsk org.nr.), «?:<navn>» (ikke funnet).
// Indeksen lagrer ikke hvilke klienter som bruker leverandøren – den trengs ikke for gjenbruk.
//
// GDPR: enkeltpersonforetak (ENK) og navn som kan være en person lagres uten navn – bare som hash,
// slik at de fortsatt kan gjenkjennes. Adresse, e-post og telefon fra Enhetsregisteret lagres aldri.
// Leverandører som er privatpersoner i Tripletex hoppes over.

import { readFileSync, writeFileSync, renameSync, existsSync, mkdirSync, openSync, closeSync, unlinkSync, statSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

// tripletex-api/src → repo-rota. Relativ LEVERANDOR_INDEKS regnes fra repo-rota.
const REPO = resolve(dirname(fileURLToPath(import.meta.url)), '..', '..');
export const INDEKS = resolve(REPO, process.env.LEVERANDOR_INDEKS?.trim() || join('data', 'leverandorer.json'));
const LAS = `${INDEKS}.lock`;
const BRREG = 'https://data.brreg.no/enhetsregisteret/api';
const STANDARD_MAKS_ALDER = 30;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const iDag = () => new Date().toLocaleDateString('sv-SE'); // ÅÅÅÅ-MM-DD i lokal tid
const alderDager = (dato) => (dato ? (Date.now() - new Date(`${dato}T00:00:00`).getTime()) / 86_400_000 : Infinity);

// ── normalisering og personvern ───────────────────────────────────────────────

export const norm = (s) => String(s ?? '').toLowerCase()
  .replace(/æ|ä/g, 'ae').replace(/ø|ö/g, 'o').replace(/å/g, 'a').replace(/ü/g, 'u').replace(/é|è/g, 'e')
  .replace(/\ba\s*\/\s*s\b/g, 'as')
  .replace(/[^a-z0-9]+/g, ' ').trim();
const kompakt = (s) => norm(s).replace(/ /g, '');
const hash = (s) => `h:${createHash('sha256').update(kompakt(s)).digest('hex').slice(0, 16)}`;

// Ord som viser at navnet er et foretak/en offentlig etat og ikke en person.
const FIRMA = /\b(as|asa|ans|da|sa|ba|ks|nuf|iks|sf|hf|stiftelse|forening|borettslag|sameie|kommune|fylkeskommune|etaten|etat|direktoratet|tilsynet|departementet|staten|skatteetaten|skatteinnkreving|innkrevingsmyndigheten|ltd|limited|inc|llc|gmbh|ag|ab|aps|oy|bv|nv|sas|sarl|srl|spa|sl|plc|pty|corp|corporation|company|group|gruppen|holding|international|norge|norway|bank|forsikring|eiendom|eiendomsmegling|service|services|entreprenor|bygg|transport|regnskap|advokatfirma)\b/;
export const serUtSomFirma = (navn) => FIRMA.test(norm(navn));
// Selskapsform eller offentlig organ i navnet – det eneste som sikkert skiller et foretak fra en person.
// Bransjeord («Service», «Bygg», «Transport») gjør det ikke: «Ola Hansen Service» er typisk et ENK.
// Testes på originalen med små bokstaver, ikke på norm(), som gjør «Ås» til «as».
const SELSKAPSFORM = /(^|[\s.,(/-])(as|asa|a\/s|ans|da|sa|ba|ks|nuf|iks|sf|hf|stiftelse|forening|borettslag|sameie|kommune|fylkeskommune|etaten|etat|direktoratet|tilsynet|departementet|staten|skatteetaten|skatteinnkreving|innkrevingsmyndigheten|ltd|limited|inc|llc|gmbh|ag|ab|aps|oy|bv|nv|sas|sarl|srl|spa|sl|plc|pty|corp|corporation|bank|forsikring)(?=$|[\s.,)/-])/;
/** Kan navnet være en person? Da lagres og vises det ikke i klartekst (bare hash). Heller for strengt enn for løst. */
// Snudd logikk (kodegjennomgang 24.09.2026): et navn uten selskapsform vises og lagres ikke i klartekst.
// Navn fra Enhetsregisteret for foretak som ikke er ENK, brukes direkte og går ikke gjennom denne testen.
export const kanVærePerson = (navn) => !!navn && !SELSKAPSFORM.test(String(navn).toLowerCase());

/** Aliaset som lagres for et navn: klartekst for foretak, hash for ENK og navn som kan være en person. */
const aliasFor = (navn, skjul) => (skjul || kanVærePerson(navn) ? hash(navn) : kompakt(navn));

export function gyldigOrgnr(s) {
  const d = String(s ?? '').replace(/\D/g, '');
  if (!/^[89]\d{8}$/.test(d)) return null;
  const v = [3, 2, 7, 6, 5, 4, 3, 2];
  const sum = v.reduce((a, w, i) => a + w * Number(d[i]), 0);
  const k = 11 - (sum % 11);
  const kontroll = k === 11 ? 0 : k;
  return kontroll !== 10 && kontroll === Number(d[8]) ? d : null;
}

// ── lesing og skriving av indeksen (lås + atomisk skriving, tåler parallelle agenter) ─────────

export function lesIndeks() {
  if (!existsSync(INDEKS)) return { versjon: 1, oppdatert: null, leverandorer: {}, aliaser: {} };
  return JSON.parse(readFileSync(INDEKS, 'utf8'));
}

/** Kjører fn(indeks) under lås og skriver resultatet atomisk. Hold fn kort – ingen nettverkskall her. */
export async function medLas(fn) {
  mkdirSync(dirname(INDEKS), { recursive: true });
  for (let i = 0; ; i++) {
    try { closeSync(openSync(LAS, 'wx')); break; } catch (e) {
      if (e.code !== 'EEXIST') throw e;
      try { if (Date.now() - statSync(LAS).mtimeMs > 60_000) { unlinkSync(LAS); continue; } } catch { /* låsen forsvant */ }
      if (i > 300) throw new Error('Leverandørindeksen er låst av en annen prosess i over 30 sekunder. Ingenting er lagret.');
      await sleep(100);
    }
  }
  try {
    const idx = lesIndeks();
    const svar = await fn(idx);
    idx.oppdatert = new Date().toISOString();
    const tmp = `${INDEKS}.${process.pid}.tmp`;
    writeFileSync(tmp, JSON.stringify(idx, null, 1));
    for (let i = 0; ; i++) {
      try { renameSync(tmp, INDEKS); break; } catch (e) {
        if (!['EPERM', 'EBUSY', 'EACCES'].includes(e.code) || i > 20) throw e;
        await sleep(100); // Windows: filen kan være åpen for lesing et øyeblikk
      }
    }
    return svar;
  } finally {
    try { unlinkSync(LAS); } catch { /* allerede borte */ }
  }
}

// ── oppslag i indeksen ────────────────────────────────────────────────────────

/** Finn nøkkelen for et org.nr., en nøkkel eller et navn (eksakt, etter normalisering). */
export function finnNokkel(idx, sok) {
  const s = String(sok ?? '').trim();
  if (idx.leverandorer[s]) return s;
  const orgnr = gyldigOrgnr(s);
  if (orgnr && idx.leverandorer[`NO:${orgnr}`]) return `NO:${orgnr}`;
  return idx.aliaser[kompakt(s)] ?? idx.aliaser[hash(s)] ?? null;
}

/** Fritekstsøk: org.nr., eksakt navn, så delstreng i navn/alias (hashede alias treffer bare eksakt). */
export function sok(idx, tekst) {
  const eksakt = finnNokkel(idx, tekst);
  if (eksakt) return [idx.leverandorer[eksakt]];
  const q = kompakt(tekst);
  if (q.length < 3) return [];
  return Object.values(idx.leverandorer).filter((r) =>
    kompakt(r.navn).includes(q) || r.aliaser.some((a) => !a.startsWith('h:') && a.includes(q)));
}

/** Var leverandøren mva-registrert på datoen? true/false, eller null når det ikke kan avgjøres. */
export function mvaRegistrertPaa(rec, dato) {
  if (!rec || rec.mva_registrert == null) return null;
  if (!rec.mva_registrert) return false; // NB: kan ha vært registrert tidligere – Enhetsregisteret viser bare nå
  if (!rec.mva_registrert_fra) return true;
  return rec.mva_registrert_fra <= dato;
}

// ── Enhetsregisteret ─────────────────────────────────────────────────────────

async function brreg(sti) {
  for (let i = 0; i < 4; i++) {
    const res = await fetch(`${BRREG}${sti}`, { headers: { accept: 'application/json' } });
    if (res.status === 404) return null;
    if (res.status === 410) return { slettet: true, ...(await res.json().catch(() => ({}))) };
    if (res.status === 429 || res.status >= 500) { await sleep(1000 * (i + 1)); continue; }
    if (!res.ok) throw new Error(`Enhetsregisteret ${sti}: HTTP ${res.status}`);
    return res.json();
  }
  throw new Error(`Enhetsregisteret ${sti}: svarer ikke`);
}

function fakta(e, hoved) {
  const kilde = hoved ?? e; // mva-registrering og org.form ligger på hovedenheten
  const enk = kilde.organisasjonsform?.kode === 'ENK';
  const adr = e.forretningsadresse ?? e.beliggenhetsadresse ?? e.postadresse ?? kilde.forretningsadresse;
  const status = e.slettet || kilde.slettet || e.slettedato ? 'slettet'
    : kilde.konkurs ? 'konkurs'
      : kilde.underAvvikling || kilde.underTvangsavviklingEllerTvangsopplosning ? 'under avvikling' : 'aktiv';
  return {
    orgnr: e.organisasjonsnummer,
    navn: enk ? null : (e.navn ?? kilde.navn ?? null),
    enk,
    organisasjonsform: kilde.organisasjonsform?.kode ?? null,
    underenhet_av: hoved ? kilde.organisasjonsnummer : null,
    land: adr?.landkode ?? null,
    mva_registrert: kilde.registrertIMvaregisteret ?? null,
    mva_registrert_fra: kilde.registreringsdatoMerverdiavgiftsregisteret ?? null,
    naeringskode: kilde.naeringskode1?.kode ?? null,
    naering: kilde.naeringskode1?.beskrivelse ?? null,
    status,
    brreg_sjekket: iDag(),
  };
}

/** Slår opp ett org.nr. i Enhetsregisteret (hovedenhet, ellers underenhet + hovedenhet). null = ikke funnet. */
export async function brregOrgnr(orgnr) {
  const e = await brreg(`/enheter/${orgnr}`);
  if (e && !e.slettet) return fakta(e);
  if (e?.slettet) return { ...fakta({ organisasjonsnummer: orgnr, ...e }), status: 'slettet' };
  const u = await brreg(`/underenheter/${orgnr}`);
  if (!u) return null;
  const hoved = u.overordnetEnhet ? await brreg(`/enheter/${u.overordnetEnhet}`) : null;
  return fakta(u, hoved ?? undefined);
}

/** Navnesøk. Returnerer {treff, kandidater}: treff bare når ett foretak har nøyaktig samme navn. */
export async function brregNavn(navn) {
  const hent = async (q) => (await brreg(`/enheter?navn=${encodeURIComponent(q)}&size=10`))?._embedded?.enheter ?? [];
  let enheter = await hent(navn);
  if (!enheter.length) {
    const utenSuffiks = norm(navn).replace(/\b(as|asa|ans|da|sa)$/, '').trim();
    if (utenSuffiks && utenSuffiks !== norm(navn)) enheter = await hent(utenSuffiks);
  }
  const like = enheter.filter((e) => kompakt(e.navn) === kompakt(navn));
  const kandidater = enheter.filter((e) => e.organisasjonsform?.kode !== 'ENK').slice(0, 3)
    .map((e) => ({ orgnr: e.organisasjonsnummer, navn: e.navn, mva: e.registrertIMvaregisteret ?? null }));
  return { treff: like.length === 1 ? fakta(like[0]) : null, kandidater };
}

// ── skriving av poster (kalles inne i medLas) ─────────────────────────────────

function leggTilAlias(idx, rec, navn) {
  if (!navn) return;
  const a = aliasFor(navn, rec.enk);
  if (!rec.aliaser.includes(a)) rec.aliaser.push(a);
  idx.aliaser[a] = rec.nokkel;
}

/** Flytt alias og vurdering fra en «?:»/«UT:»-post over til riktig post og slett den gamle. */
function slaSammen(idx, fraNokkel, tilRec) {
  const fra = idx.leverandorer[fraNokkel];
  if (!fra || fraNokkel === tilRec.nokkel) return;
  for (const a of fra.aliaser) { if (!tilRec.aliaser.includes(a)) tilRec.aliaser.push(a); idx.aliaser[a] = tilRec.nokkel; }
  if (fra.vurdering && !tilRec.vurdering) tilRec.vurdering = fra.vurdering;
  delete idx.leverandorer[fraNokkel];
}

export function lagreFakta(idx, f, navnITripletex = []) {
  const nokkel = `NO:${f.orgnr}`;
  const gammel = idx.leverandorer[nokkel];
  // Har en annen kjøring lagret nyere fakta i mellomtiden, beholdes de – bare aliasene legges til.
  const rec = gammel && gammel.brreg_sjekket > f.brreg_sjekket ? gammel
    : { nokkel, aliaser: [], vurdering: null, opprettet: iDag(), ...gammel, ...f, aliaser: [...(gammel?.aliaser ?? [])] };
  idx.leverandorer[nokkel] = rec;
  // En underenhet har samme navn som hovedenheten – navnet skal fortsatt peke på hovedenheten.
  if (rec.navn && !rec.underenhet_av) leggTilAlias(idx, rec, rec.navn);
  for (const n of navnITripletex) {
    const tidligere = idx.aliaser[kompakt(n)] ?? idx.aliaser[hash(n)];
    if (tidligere && tidligere !== nokkel && !tidligere.startsWith('NO:')) slaSammen(idx, tidligere, rec);
    leggTilAlias(idx, rec, n);
  }
  return rec;
}

function lagreUkjent(idx, navn, { utland, kandidater, valuta }) {
  const skjul = kanVærePerson(navn);
  const hale = skjul ? hash(navn) : kompakt(navn);
  const nokkel = `${utland ? 'UT' : '?'}:${hale}`;
  const motsatt = `${utland ? '?' : 'UT'}:${hale}`;
  // Samme navn under den andre prefiksen: en vurdert UT-post vinner over en ny «?:», ellers slås de sammen.
  if (idx.leverandorer[motsatt] && !utland) return idx.leverandorer[motsatt];
  const gammel = idx.leverandorer[nokkel] ?? idx.leverandorer[motsatt];
  if (idx.leverandorer[motsatt]) delete idx.leverandorer[motsatt];
  const rec = {
    aliaser: [], vurdering: null, opprettet: iDag(), ...gammel,
    nokkel, orgnr: null, navn: skjul ? null : navn, enk: false, land: gammel?.land ?? null,
    kandidater: kandidater ?? gammel?.kandidater ?? [], valuta: [...new Set([...(gammel?.valuta ?? []), ...(valuta ?? [])])],
    status: !utland ? 'ikke funnet i Enhetsregisteret' : gammel?.vurdering ? 'utenlandsk – vurdert' : 'utenlandsk – må vurderes',
    brreg_sjekket: iDag(),
  };
  rec.aliaser = [...(gammel?.aliaser ?? [])];
  idx.leverandorer[nokkel] = rec;
  for (const a of rec.aliaser) idx.aliaser[a] = nokkel;
  leggTilAlias(idx, rec, navn);
  return rec;
}

// ── utskrift ──────────────────────────────────────────────────────────────────

const visNavn = (r) => r.navn ?? (r.enk ? '[ENK – navn skjult]' : '[navn skjult]');
function linje(r) {
  const mva = r.mva_registrert == null ? 'mva: ?' : r.mva_registrert ? `mva: ja${r.mva_registrert_fra ? ` fra ${r.mva_registrert_fra}` : ''}` : 'mva: NEI';
  const v = r.vurdering;
  const vurd = v ? `vurdert (${v.vurdert_av} ${v.vurdert})${v.omvendt_avgiftsplikt ? ` omvendt ${v.omvendt_avgiftsplikt}` : ''}${v.kostnadstype ? ` – ${v.kostnadstype}` : ''}` : 'ikke vurdert';
  return [r.nokkel.padEnd(14), visNavn(r), r.organisasjonsform ?? '', r.land ? `land ${r.land}` : '', mva,
    r.naeringskode ? `${r.naeringskode} ${r.naering}` : '', r.status, vurd].filter(Boolean).join(' | ');
}

// ── kommandoer ────────────────────────────────────────────────────────────────

export async function importer(klient, fra, til, maksAlder = STANDARD_MAKS_ALDER) {
  const { connect } = await import('./tripletex.js');
  const b = await connect(klient);
  const poster = await b.list('/ledger/posting', { query: {
    dateFrom: fra, dateTo: til, accountNumberFrom: 2400, accountNumberTo: 2499, fields: 'supplier(id),currency(code)' } });
  const valuta = new Map();
  for (const p of poster) {
    if (!p.supplier?.id) continue;
    if (!valuta.has(p.supplier.id)) valuta.set(p.supplier.id, new Set());
    if (p.currency?.code && p.currency.code !== 'NOK') valuta.get(p.supplier.id).add(p.currency.code);
  }
  const ider = [...valuta.keys()];
  const levs = [];
  for (let i = 0; i < ider.length; i += 100) {
    levs.push(...(await b.list('/supplier', { query: { id: ider.slice(i, i + 100).join(','),
      fields: 'id,name,organizationNumber,isPrivateIndividual,currency(code),physicalAddress(country(isoAlpha2Code)),postalAddress(country(isoAlpha2Code))' } })));
  }

  // 1) Finn ut hva som må slås opp – uten lås, nettverkskall her.
  const idx = lesIndeks();
  const oppgaver = [];
  let privat = 0;
  for (const l of levs) {
    if (l.isPrivateIndividual) { privat++; continue; }
    const cur = new Set(valuta.get(l.id));
    if (l.currency?.code && l.currency.code !== 'NOK') cur.add(l.currency.code);
    const land = l.physicalAddress?.country?.isoAlpha2Code || l.postalAddress?.country?.isoAlpha2Code || null;
    const orgnr = gyldigOrgnr(l.organizationNumber);
    const kjent = (orgnr && finnNokkel(idx, orgnr)) || finnNokkel(idx, l.name);
    const rec = kjent ? idx.leverandorer[kjent] : null;
    const fersk = rec && alderDager(rec.brreg_sjekket) <= maksAlder;
    oppgaver.push({ l, orgnr, land, valuta: [...cur], kjent, fersk, rec });
  }
  const resultat = [];
  for (const o of oppgaver) {
    const { l, orgnr } = o;
    const r = { tripletexId: l.id, tripletexNavn: l.name, orgnrITripletex: orgnr, land: o.land, valuta: o.valuta, kjent: !!o.kjent };
    try {
      if (o.fersk && (o.rec.orgnr || !orgnr)) r.fakta = null; // alt er kjent og ferskt
      else if (orgnr) r.fakta = await brregOrgnr(orgnr);
      else if (o.rec?.orgnr) r.fakta = await brregOrgnr(o.rec.orgnr);
      else {
        const utland = (o.land && o.land !== 'NO') || o.valuta.length > 0;
        // Navn som kan være en person, sendes ikke som søk til Enhetsregisteret.
        const { treff, kandidater } = utland || kanVærePerson(l.name) ? { treff: null, kandidater: [] } : await brregNavn(l.name);
        r.fakta = treff; r.kandidater = kandidater; r.utland = utland;
        if (treff) r.orgnrManglerITripletex = true;
      }
      if (orgnr && r.fakta === null && !o.fersk) r.ikkeFunnetOrgnr = true;
    } catch (e) { r.feil = e.message; }
    resultat.push(r);
    await sleep(50); // skånsomt mot Enhetsregisteret
  }

  // 2) Lagre alt i én kort operasjon under lås.
  const poster2 = await medLas((idx2) => resultat.map((r) => {
    if (r.feil) return { ...r, rec: null };
    if (r.fakta) return { ...r, rec: lagreFakta(idx2, r.fakta, [r.tripletexNavn]) };
    const k = (r.orgnrITripletex && finnNokkel(idx2, r.orgnrITripletex)) || finnNokkel(idx2, r.tripletexNavn);
    if (k) { const rec = idx2.leverandorer[k]; leggTilAlias(idx2, rec, r.tripletexNavn); return { ...r, rec }; }
    return { ...r, rec: lagreUkjent(idx2, r.tripletexNavn, { utland: r.utland, kandidater: r.kandidater, valuta: r.valuta }) };
  }));
  return { klient: b.company.name, fra, til, leverandorer: levs.length, privat, poster: poster2 };
}

function skrivImport(res, json) {
  const kort = (p) => ({ nokkel: p.rec?.nokkel ?? null, navn: p.rec ? visNavn(p.rec) : (kanVærePerson(p.tripletexNavn) ? '[navn skjult]' : p.tripletexNavn),
    orgnr: p.rec?.orgnr ?? null, mva_registrert: p.rec?.mva_registrert ?? null, status: p.rec?.status ?? null,
    vurdert: !!p.rec?.vurdering, valuta: p.valuta, kandidater: p.kandidater ?? [], feil: p.feil ?? null,
    orgnr_mangler_i_tripletex: !!p.orgnrManglerITripletex, orgnr_ikke_funnet: !!p.ikkeFunnetOrgnr });
  const alle = res.poster.map(kort);
  const grupper = {
    ukjente: alle.filter((p) => p.nokkel?.startsWith('?:')),
    utland_ma_vurderes: alle.filter((p) => p.nokkel?.startsWith('UT:') && !p.vurdert),
    ikke_mva_registrert: alle.filter((p) => p.mva_registrert === false),
    konkurs_slettet: alle.filter((p) => ['konkurs', 'slettet', 'under avvikling'].includes(p.status)),
    orgnr_mangler_i_tripletex: alle.filter((p) => p.orgnr_mangler_i_tripletex),
    orgnr_ikke_funnet: alle.filter((p) => p.orgnr_ikke_funnet),
    feil: alle.filter((p) => p.feil),
  };
  if (json) { console.log(JSON.stringify({ ...res, poster: undefined, grupper, antall: alle.length }, null, 1)); return; }
  console.log(`${res.klient}: ${res.leverandorer} leverandører med poster ${res.fra}–${res.til} (til eksklusiv), ${res.privat} privatpersoner hoppet over.`);
  console.log(`Kjent fra før: ${res.poster.filter((p) => p.kjent).length}. Nye i indeksen: ${res.poster.filter((p) => !p.kjent && p.rec).length}.`);
  const tekst = {
    ukjente: 'Ikke funnet i Enhetsregisteret – må vurderes (vurder …)',
    utland_ma_vurderes: 'Utenlandske (valuta/land) uten vurdering – omvendt avgiftsplikt?',
    ikke_mva_registrert: 'Ikke mva-registrert i dag – fradrag for mva på faktura fra disse er feil',
    konkurs_slettet: 'Konkurs, slettet eller under avvikling',
    orgnr_mangler_i_tripletex: 'Org.nr. mangler på leverandøren i Tripletex (funnet via navn) – bør rettes i Tripletex',
    orgnr_ikke_funnet: 'Org.nr. i Tripletex finnes ikke i Enhetsregisteret – feil org.nr.?',
    feil: 'Oppslaget feilet – kjør på nytt',
  };
  for (const [k, liste] of Object.entries(grupper)) {
    if (!liste.length) continue;
    console.log(`\n${tekst[k]} (${liste.length}):`);
    for (const p of liste) {
      const kand = p.kandidater.length ? `  kandidater: ${p.kandidater.map((c) => `${c.orgnr} ${c.navn}`).join('; ')}` : '';
      console.log(`  ${p.navn}${p.orgnr ? ` (${p.orgnr})` : ''}${p.valuta.length ? ` valuta ${p.valuta.join(',')}` : ''}${p.feil ? ` – ${p.feil}` : ''}${kand}`);
    }
  }
}

const VURDERINGSFELT = { land: 'land', utenlandsk: 'utenlandsk', omvendt: 'omvendt_avgiftsplikt', voec: 'voec',
  kostnadstype: 'kostnadstype', fradrag: 'fradrag', sats: 'sats', notat: 'notat', kilde: 'kilde', sikkerhet: 'sikkerhet' };
const jaNei = (v) => (v === undefined ? undefined : /^(ja|true|1)$/i.test(v) ? true : /^(nei|false|0)$/i.test(v) ? false : v);

async function vurder(id, opt) {
  const av = typeof opt.av === 'string' ? opt.av.trim() : 'agent';
  // «agent» eller regnskapsførerens initialer (2–12 bokstaver, f.eks. «AB»). Ingen fulle navn.
  if (av !== 'agent' && !/^[\p{L}][\p{L}.-]{1,11}$/u.test(av)) throw new Error('--av må være «agent» eller initialene til regnskapsføreren (f.eks. --av AB).');
  if (opt.sikkerhet && !['høy', 'middels', 'lav'].includes(opt.sikkerhet)) throw new Error('--sikkerhet må være høy, middels eller lav.');
  if (opt.omvendt && !['86', '87', '88', '89', '91', '92', 'nei'].includes(opt.omvendt)) throw new Error('--omvendt må være 86, 87, 88, 89, 91, 92 eller nei.');
  const nytt = {};
  for (const [flagg, felt] of Object.entries(VURDERINGSFELT)) if (opt[flagg] !== undefined) nytt[felt] = jaNei(opt[flagg]);
  if (nytt.omvendt_avgiftsplikt === 'nei') nytt.omvendt_avgiftsplikt = null;
  if (!Object.keys(nytt).length) throw new Error('Ingen vurderingsfelt angitt (f.eks. --kostnadstype, --omvendt, --notat).');

  return medLas((idx) => {
    let k = finnNokkel(idx, id ?? opt.navn);
    if (!k && opt.navn) {
      const utland = (opt.land && opt.land.toUpperCase() !== 'NO') || jaNei(opt.utenlandsk) === true;
      k = lagreUkjent(idx, opt.navn, { utland }).nokkel;
    }
    if (!k) throw new Error(`Fant ikke «${id ?? opt.navn}» i indeksen. Kjør «oppslag <orgnr>» først, eller angi --navn (og --land for utenlandske).`);
    const rec = idx.leverandorer[k];
    // Alt som ikke er vurdert av «agent», er en regnskapsførers vurdering og beskyttet mot overskriving fra andre.
    const forrige = rec.vurdering?.vurdert_av;
    if (forrige && forrige !== 'agent' && av !== forrige && !opt.tving) {
      throw new Error(`${k} er vurdert av ${forrige} ${rec.vurdering.vurdert} – overskrives ikke. Bruk --tving bare etter avtale med ${forrige}.`);
    }
    if (rec.vurdering) rec.historikk = [rec.vurdering, ...(rec.historikk ?? [])].slice(0, 5);
    rec.vurdering = { ...(rec.vurdering ?? {}), ...nytt, vurdert_av: av, vurdert: iDag() };
    if (nytt.land) rec.land = String(nytt.land).toUpperCase();
    if (rec.nokkel.startsWith('?:') && (rec.land && rec.land !== 'NO')) {
      // En ukjent som viser seg å være utenlandsk flyttes til UT:
      const ny = { ...rec, nokkel: `UT:${rec.nokkel.slice(2)}`, status: 'utenlandsk – vurdert' };
      delete idx.leverandorer[rec.nokkel];
      idx.leverandorer[ny.nokkel] = ny;
      for (const a of ny.aliaser) idx.aliaser[a] = ny.nokkel;
      return ny;
    }
    if (rec.nokkel.startsWith('UT:')) rec.status = 'utenlandsk – vurdert';
    return rec;
  });
}

async function oppdater(maksAlder, json) {
  const idx = lesIndeks();
  const gamle = Object.values(idx.leverandorer).filter((r) => r.orgnr && alderDager(r.brreg_sjekket) > maksAlder);
  const nye = [];
  for (const r of gamle) {
    try { const f = await brregOrgnr(r.orgnr); if (f) nye.push(f); } catch (e) { console.error(`${r.nokkel}: ${e.message}`); }
    await sleep(50);
  }
  const endret = await medLas((idx2) => nye.filter((f) => {
    const g = idx2.leverandorer[`NO:${f.orgnr}`];
    const diff = g && (g.mva_registrert !== f.mva_registrert || g.status !== f.status);
    lagreFakta(idx2, f);
    return diff;
  }).map((f) => `NO:${f.orgnr}`));
  if (json) console.log(JSON.stringify({ sjekket: nye.length, endret }, null, 1));
  else console.log(`Friskt opp ${nye.length} av ${gamle.length} poster eldre enn ${maksAlder} dager. Endret mva-status/status: ${endret.length ? endret.join(', ') : 'ingen'}.`);
}

// ── CLI ───────────────────────────────────────────────────────────────────────

async function main() {
  const argv = process.argv.slice(2);
  const [kmd, ...rest] = argv;
  const opt = {};
  const pos = [];
  for (let i = 0; i < rest.length; i++) {
    if (rest[i].startsWith('--')) {
      const navn = rest[i].slice(2);
      const neste = rest[i + 1];
      if (neste === undefined || neste.startsWith('--')) opt[navn] = true; else { opt[navn] = neste; i++; }
    } else pos.push(rest[i]);
  }
  const json = !!opt.json;
  const maksAlder = Number(opt['maks-alder'] ?? STANDARD_MAKS_ALDER);
  const ut = (data, tekst) => console.log(json ? JSON.stringify(data, null, 1) : tekst);

  switch (kmd) {
    case 'finn': {
      const treff = sok(lesIndeks(), pos.join(' '));
      return ut(treff, treff.length ? treff.map(linje).join('\n') : `Ingen treff på «${pos.join(' ')}» i indeksen.`);
    }
    case 'vis': {
      const idx = lesIndeks();
      const k = finnNokkel(idx, pos.join(' '));
      if (!k) { process.exitCode = 1; return ut(null, `Ikke i indeksen: «${pos.join(' ')}».`); }
      const r = { ...idx.leverandorer[k], aliaser: idx.leverandorer[k].aliaser.map((a) => (a.startsWith('h:') ? '[hash]' : a)) };
      return ut(r, JSON.stringify(r, null, 1));
    }
    case 'oppslag': {
      const orgnr = gyldigOrgnr(pos[0]);
      if (!orgnr) { process.exitCode = 1; return console.error('Oppgi et gyldig org.nr. (9 siffer, kontrollsiffer stemmer).'); }
      const f = await brregOrgnr(orgnr);
      if (!f) { process.exitCode = 1; return ut(null, `${orgnr} finnes ikke i Enhetsregisteret.`); }
      const alias = typeof opt.alias === 'string' ? [opt.alias] : [];
      const rec = await medLas((idx) => lagreFakta(idx, f, alias));
      return ut(rec, linje(rec));
    }
    case 'importer': {
      const klient = typeof opt.client === 'string' ? opt.client : null;
      if (!klient) { process.exitCode = 1; return console.error('Angi --client "klient". Ingenting er gjort.'); }
      const aar = new Date().getFullYear();
      const fra = opt.fra ?? `${aar}-01-01`;
      const til = opt.til ?? iDag();
      return skrivImport(await importer(klient, fra, til, maksAlder), json);
    }
    case 'vurder': {
      const rec = await vurder(pos.join(' ') || null, opt);
      return ut(rec, linje(rec));
    }
    case 'liste': {
      let alle = Object.values(lesIndeks().leverandorer);
      if (opt.ukjente) alle = alle.filter((r) => r.nokkel.startsWith('?:'));
      if (opt.utland) alle = alle.filter((r) => r.nokkel.startsWith('UT:') || (r.land && r.land !== 'NO') || r.organisasjonsform === 'NUF');
      if (opt['uten-mva']) alle = alle.filter((r) => r.mva_registrert === false);
      if (opt.uvurdert) alle = alle.filter((r) => !r.vurdering);
      if (opt.utdatert) alle = alle.filter((r) => r.orgnr && alderDager(r.brreg_sjekket) > maksAlder);
      return ut(alle, alle.length ? `${alle.map(linje).join('\n')}\n(${alle.length} poster)` : 'Ingen poster.');
    }
    case 'oppdater':
      return oppdater(maksAlder, json);
    default:
      console.log(readFileSync(fileURLToPath(import.meta.url), 'utf8').split('\n').filter((l) => l.startsWith('//')).slice(0, 14).map((l) => l.slice(3)).join('\n'));
  }
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  main().catch((e) => { console.error(`Feil: ${e.message}`); process.exitCode = 1; });
}
