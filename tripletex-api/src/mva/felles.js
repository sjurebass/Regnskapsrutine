// Felles byggeklosser for mva-flyten: sikker henting, arbeidsmappe, tilstand, termin og funnformat.
//
// Arbeidsflyten er beskrevet i skillene mva-kontroll og mva-innlevering.

import { mkdirSync, writeFileSync, readFileSync, existsSync, rmSync, renameSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { createHash } from 'node:crypto';

// ── henting ───────────────────────────────────────────────────────────────────

// Felt som aldri skal hentes (personopplysninger eller hemmeligheter). Sjekkes mot fields= før kallet.
// Sjekkes per feltnavn (også nestede) uten krav om ordgrense, så f.eks. «invoiceEmail» og «employeeId» også stoppes.
const FORBUDTE_DELER = ['employee', 'createdby', 'uploadedby', 'lastupdatedby', 'reconciledby', 'controlledby', 'approvedby', 'bankaccount', 'iban', 'email', 'phone',
  'nationalidentity', 'dateofbirth', 'password', 'firstname', 'lastname', 'address', 'contact', 'username'];
const UFARLIGE_FELT = new Set(['isbankaccount']); // ja/nei-flagg, ikke et kontonummer
const PERSONSTIER = [/^\/employee/, /^\/salary/, /^\/contact/, /^\/timesheet/, /^\/travelExpense/];

/**
 * Henter alle sider fra et liste-endepunkt i klientkonteksten `b` (fra connect()).
 * Krever fields= (dataminimering) og nekter personfelt og personendepunkter.
 * Blar til en side gir færre enn count – fullResultSize er ikke et pålitelig totalantall.
 */
export async function hentAlle(b, sti, query = {}, { side = 1000 } = {}) {
  sjekkKall(sti, query);
  const ut = [];
  for (let from = 0; ; from += side) {
    const svar = await b.request(sti, { query: { ...query, from, count: side } });
    const verdier = svar?.values ?? [];
    ut.push(...verdier);
    if (verdier.length < side) return ut;
  }
}

/** Henter ett objekt (`value`) eller et rått svar. Samme regler som hentAlle. */
export async function hentEn(b, sti, query = {}) {
  sjekkKall(sti, query);
  const svar = await b.request(sti, { query });
  return svar?.value !== undefined ? svar.value : svar;
}

function sjekkKall(sti, query) {
  if (PERSONSTIER.some((re) => re.test(sti))) throw new Error(`${sti}: personendepunkt – ikke tillatt i mva-flyten.`);
  if (query.fields === undefined) throw new Error(`${sti}: fields= mangler (dataminimering).`);
  const felt = String(query.fields).split(/[,()]/).map((f) => f.trim().toLowerCase()).filter(Boolean);
  if (felt.includes('*')) throw new Error(`${sti}: fields=* er ikke tillatt (dataminimering).`);
  const forbudt = felt.find((f) => !UFARLIGE_FELT.has(f) && FORBUDTE_DELER.some((del) => f.includes(del)));
  if (forbudt) throw new Error(`${sti}: fields inneholder personfelt (${forbudt}).`);
}

/** Prøver et kall og gir { ok, data } eller { ok:false, status, feil } i stedet for å kaste (for 403/404 på interne kall). */
export async function forsok(fn) {
  try {
    return { ok: true, data: await fn() };
  } catch (e) {
    const status = Number(e.message.match(/\((\d{3})\)/)?.[1]) || null;
    return { ok: false, status, feil: e.message.split('\n')[0].slice(0, 200) };
  }
}

// ── arbeidsmappe og tilstand ─────────────────────────────────────────────────

/**
 * Arbeidsmappa for én klient og termin: %TEMP%\rr\mva-<år>-T<n>\<kunde-id>\, eller
 * <MVA_ARBEIDSMAPPE>\<år>-T<n>\<kunde-id>\ når miljøvariabelen er satt.
 * Utenfor repoet og kundemappene. Mappenavnet er kunde-id, ikke firmanavn.
 * Inneholder rådata (også fritekst), så den skal slettes når terminen er ferdig.
 */
export function arbeidsmappe(aar, termin, kundeId) {
  const mappe = process.env.MVA_ARBEIDSMAPPE?.trim()
    ? resolve(process.env.MVA_ARBEIDSMAPPE.trim(), `${aar}-T${termin}`, String(kundeId))
    : resolve(tmpdir(), 'rr', `mva-${aar}-T${termin}`, String(kundeId));
  mkdirSync(mappe, { recursive: true });
  return {
    mappe,
    fil: (navn) => join(mappe, navn),
    lagre: (navn, data) => writeFileSync(join(mappe, navn), JSON.stringify(data, null, 1)),
    les: (navn) => (existsSync(join(mappe, navn)) ? JSON.parse(readFileSync(join(mappe, navn), 'utf8')) : null),
    finnes: (navn) => existsSync(join(mappe, navn)),
    fjern: (navn) => rmSync(join(mappe, navn), { force: true, recursive: true }),
    flytt: (fra, til) => { if (existsSync(join(mappe, fra))) renameSync(join(mappe, fra), join(mappe, til)); },
  };
}

/** Oppdaterer state.json med nye felt og logger stadiet med tidspunkt. */
export function oppdaterTilstand(am, endring) {
  const gammel = am.les('state.json') ?? { historikk: [] };
  const ny = { ...gammel, ...endring, oppdatert: new Date().toISOString() };
  if (endring.stadium) ny.historikk = [...(gammel.historikk ?? []), { stadium: endring.stadium, tid: ny.oppdatert }];
  am.lagre('state.json', ny);
  return ny;
}

// ── datoer og termin ────────────────────────────────────────────────────────

export const iso = (d) => d.toISOString().slice(0, 10);
const dato = (s) => new Date(`${s}T00:00:00Z`);
export const leggTilDager = (s, n) => iso(new Date(dato(s).getTime() + n * 86_400_000));
export const leggTilMnd = (s, n) => { const d = dato(s); d.setUTCMonth(d.getUTCMonth() + n); return iso(d); };
export const kvartal = (s) => `${s.slice(0, 4)}-K${Math.floor((Number(s.slice(5, 7)) - 1) / 3) + 1}`;

const MND_PER_TERMIN = { ONE_MONTH: 1, TWO_MONTHS: 2, THREE_MONTHS: 3, FOUR_MONTHS: 4, SIX_MONTHS: 6, YEAR: 12 };

/**
 * Terminobjektet: alle datoer flyten bruker, regnet ett sted.
 * sluttEksklusiv = D = første dag etter terminen (Tripletex bruker eksklusiv til-dato).
 * Klienter som ikke er registrert har termSize NOT_REGISTERED – da brukes tomånedlig rytme.
 */
export function lagTermin(aar, termin, termSize = 'TWO_MONTHS') {
  const mnd = MND_PER_TERMIN[termSize] ?? 2;
  const antall = 12 / mnd;
  if (!Number.isInteger(termin) || termin < 1 || termin > antall) throw new Error(`Termin ${termin} finnes ikke for ${termSize} (1–${antall}).`);
  const start = `${aar}-${String((termin - 1) * mnd + 1).padStart(2, '0')}-01`;
  const D = leggTilMnd(start, mnd);
  const maaneder = Array.from({ length: mnd }, (_, i) => leggTilMnd(start, i).slice(0, 7));
  return { aar, termin, termSize, start, sluttEksklusiv: D, D, sisteDag: leggTilDager(D, -1), maaneder, kvartaler: [...new Set(maaneder.map((m) => kvartal(`${m}-01`)))] };
}

// ── funn ─────────────────────────────────────────────────────────────────────

export const ALVOR = ['STOPP', 'BLOKK', 'SPØR_REGNSKAPSFØRER', 'FORKLAR', 'INFO'];

/** Eldre lagrede filer kan ha et annet «SPØR_<navn>»-alvor – leses som SPØR_REGNSKAPSFØRER. */
export const normAlvor = (a) => (/^SPØR_/.test(a ?? '') ? 'SPØR_REGNSKAPSFØRER' : a);

/**
 * Nøkkel for kjente-avvik.md: 10 hex-tegn av en lesbar råstreng, samme format som månedskontrollen.
 * Råstrengen tar med beløpet, så et endret beløp gir nytt funn.
 * Hex fordi «|» i råstrengen ellers ødelegger markdown-tabellen.
 */
export const lagNoekkel = (raa) => createHash('sha1').update(String(raa)).digest('hex').slice(0, 10);

/**
 * Felles funnformat for alle kontroller. Ingen fritekst fra Tripletex i tittel/detalj – bruk
 * bilagsnummer, konto, beløp og firmanavn. `noekkel` er stabil så kjente-avvik.md kan dempe funnet.
 */
export function lagFunn({ kontroll, alvor, tittel, detalj = '', belop = null, konto = null, bilag = [], nivaa = 'bilag', trengerSkjonn = false, hjemmel = null, regel = null, handling = null, data = null }) {
  alvor = normAlvor(alvor);
  if (!ALVOR.includes(alvor)) throw new Error(`Ukjent alvor: ${alvor}`);
  const noekkelTekst = [kontroll, konto ?? '', bilag.slice(0, 3).join('+'), belop === null ? '' : Math.round(belop)].join('|');
  return { kontroll, alvor, tittel, detalj, belop, konto, bilag, nivaa, trengerSkjonn, hjemmel, regel, handling, noekkel: lagNoekkel(noekkelTekst), noekkelTekst, data, bilag: bilag.map(String) };
}

export const kr = (n) => (n === null || n === undefined ? '–' : Math.round(n).toLocaleString('nb-NO'));
export const rund = (n) => Math.round((n ?? 0) * 100) / 100;
