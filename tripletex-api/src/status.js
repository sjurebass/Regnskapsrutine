// Port per klient: er perioden klar til å avsluttes? KUN LESING, sekvensielle kall.
//
//   npm run -s status -- (--client "klient" [--client …] | --alle) --maaned 2026-08 [--json]
//   npm run -s status -- (--client "klient" | --alle) --aar 2026 [--json]          (hele året: 12 måneder, 6 terminer)
//
// Sjekker per klient (ok = true/false, null = kunne ikke avgjøres):
//   bilagsmottak       antall dokumenter i bilagsmottaket (nå)
//   ikkeBokfort        ikke bokførte bilag med dato i perioden (inkl. ikke godkjente)
//   bank               per bankkonto: lukkede og åpne måneder, bankens sluttsaldo og differanse siste måned
//   reskontro          1500/2400: sum åpne poster mot saldo i hovedboka per periodeslutt
//   amelding           gruppe per måned (ikke sendt / venter / godkjent / avvist / endret etter innsending / kunne ikke leses)
//   observasjonskonti  saldo 1370, 1960 og 7799 per periodeslutt
//   perioder           lukkede regnskapsperioder hittil i året
//   mva                levert/betalt for siste termin som slutter i perioden (alle seks med --aar)
// Utskriften har bare antall, summer og status per klient – ingen fritekst eller personopplysninger.

import { bind } from './tripletex.js';
import { hentKlient } from './bankavstemming.js';
import { status as ameldingStatus, gruppe as ameldingGruppe } from './amelding.js';
import { mvaStatus } from './mva/status.js';
import { argumenter, klientutvalg, perKlient, erMaaned, nesteMnd, maanederMellom, rund, kortFeil } from './valg.js';

const OBSERVASJON = [1370, 1960, 7799];
const MVA_OK = new Set(['levert og betalt', 'ikke registrert', 'ingen terminslutt']);

async function sjekk(navn, sj, fn) {
  try { sj[navn] = await fn(); } catch (e) { sj[navn] = { ok: null, feil: kortFeil(e) }; }
}

/** Alle sjekkene for én klient. `fraM`/`tilM` = første og siste måned (ÅÅÅÅ-MM) i perioden. */
export async function port(c, { aar, fraM, tilM, terminer }) {
  const b = bind(c);
  const D = nesteMnd(tilM); // eksklusiv
  const sj = {};

  await sjekk('bilagsmottak', sj, async () => {
    const r = await b.request('/voucherInbox/inboxCount');
    const n = typeof r?.value === 'number' ? r.value : r?.value?.count ?? r?.value ?? null;
    return { antall: n, ok: n == null ? null : n === 0 };
  });

  await sjekk('ikkeBokfort', sj, async () => {
    const v = await b.list('/ledger/voucher/>nonPosted', { query: { includeNonApproved: true, dateFrom: `${fraM}-01`, dateTo: D, fields: 'id' } });
    return { antall: v.length, ok: v.length === 0 };
  });

  await sjekk('bank', sj, async () => {
    const r = await hentKlient(c, { fra: fraM, til: tilM, detaljer: false });
    const kontoer = r.kontoer.map((k) => {
      const siste = k.maaneder.at(-1) ?? {};
      return {
        konto: k.nummer, bankfeed: k.bankfeed, lukket: k.maaneder.filter((m) => m.lukket).length,
        aapne: k.maaneder.filter((m) => m.aapen).map((m) => m.maaned), ub: siste.ub ?? null, bankSaldo: siste.bankSaldo ?? null, differanse: siste.differanse ?? null,
      };
    });
    return { kontoer, ok: kontoer.every((k) => !k.aapne.length) };
  });

  // Én saldobalanse dekker reskontro og observasjonskonti.
  let saldo = null;
  await sjekk('reskontro', sj, async () => {
    const rader = await b.list('/balanceSheet', { query: { dateFrom: `${aar}-01-01`, dateTo: D, accountNumberFrom: 1370, accountNumberTo: 7799, fields: 'account(number),balanceOut' } });
    saldo = new Map(rader.map((x) => [x.account?.number, x.balanceOut ?? 0]));
    const ut = {};
    for (const konto of [1500, 2400]) {
      const aapne = await b.list('/ledger/posting/openPost', { query: { date: D, accountNumberFrom: konto, accountNumberTo: konto, sorted: false, fields: 'amount' } });
      const sum = rund(aapne.reduce((s, p) => s + (p.amount ?? 0), 0));
      const ub = rund(saldo.get(konto) ?? 0);
      ut[konto] = { aapnePoster: aapne.length, sumAapne: sum, saldo: ub, differanse: rund(ub - sum), ok: Math.abs(ub - sum) < 1 };
    }
    return { ...ut, ok: ut[1500].ok && ut[2400].ok };
  });

  await sjekk('observasjonskonti', sj, async () => {
    if (!saldo) throw new Error('saldobalansen kunne ikke leses');
    const kontoer = OBSERVASJON.map((konto) => ({ konto, saldo: rund(saldo.get(konto) ?? 0) }));
    return { kontoer, ok: kontoer.every((k) => Math.abs(k.saldo) < 0.005) };
  });

  await sjekk('amelding', sj, async () => {
    const maaneder = [];
    for (const m of maanederMellom(fraM, tilM)) {
      try { maaneder.push({ maaned: m, gruppe: ameldingGruppe(await ameldingStatus(b, m)) }); } catch (e) { maaneder.push({ maaned: m, gruppe: 'kunne ikke leses', feil: kortFeil(e) }); }
    }
    const daarlige = maaneder.filter((x) => !['godkjent', 'kunne ikke leses'].includes(x.gruppe));
    const ok = daarlige.length ? false : maaneder.every((x) => x.gruppe === 'godkjent') ? true : null;
    return maaneder.length === 1 ? { ...maaneder[0], ok } : { maaneder, ok };
  });

  await sjekk('perioder', sj, async () => {
    const p = await b.list('/ledger/accountingPeriod', { query: { startFrom: `${aar}-01-01`, startTo: D, fields: 'start,isClosed' } });
    const ikkeLukket = p.filter((x) => !x.isClosed).map((x) => String(x.start).slice(0, 7)).sort();
    return { lukket: p.length - ikkeLukket.length, ikkeLukket, ok: ikkeLukket.length === 0 };
  });

  await sjekk('mva', sj, async () => {
    const ut = [];
    for (const [ar, t] of terminer) {
      try {
        const s = await mvaStatus(b, ar, t);
        ut.push({ termin: s.termin, gruppe: s.gruppe, levert: s.levert ?? null, betalt: s.betalt ?? null, rest: s.rest ?? null, forfall: s.forfall ?? null, saldo2740: s.saldo2740 ?? null });
      } catch (e) { ut.push({ termin: `${t}/${ar}`, gruppe: 'kunne ikke leses', feil: kortFeil(e) }); }
    }
    const ok = ut.some((x) => x.gruppe === 'kunne ikke leses') ? null : ut.every((x) => MVA_OK.has(x.gruppe));
    return ut.length === 1 ? { ...ut[0], ok } : { terminer: ut, ok };
  });

  const mangler = [];
  if (sj.bilagsmottak.ok === false) mangler.push(`bilagsmottak ${sj.bilagsmottak.antall}`);
  if (sj.ikkeBokfort.ok === false) mangler.push(`ikke bokførte bilag ${sj.ikkeBokfort.antall}`);
  for (const k of sj.bank.kontoer ?? []) if (k.aapne.length) mangler.push(`bank ${k.konto} åpen ${k.aapne.join(', ')}`);
  for (const konto of [1500, 2400]) if (sj.reskontro[konto]?.ok === false) mangler.push(`reskontro ${konto} differanse ${sj.reskontro[konto].differanse}`);
  for (const k of sj.observasjonskonti.kontoer ?? []) if (Math.abs(k.saldo) >= 0.005) mangler.push(`saldo ${k.konto} ${k.saldo}`);
  for (const x of sj.amelding.maaneder ?? [sj.amelding]) if (x.gruppe && !['godkjent', 'kunne ikke leses'].includes(x.gruppe)) mangler.push(`a-melding ${x.maaned} ${x.gruppe}`);
  if (sj.perioder.ok === false) mangler.push(`perioder ikke lukket ${sj.perioder.ikkeLukket.length}`);
  for (const x of sj.mva.terminer ?? [sj.mva]) if (x.gruppe && !MVA_OK.has(x.gruppe) && x.gruppe !== 'kunne ikke leses') mangler.push(`mva ${x.termin} ${x.gruppe}`);
  const uavklart = Object.entries(sj).filter(([, v]) => v.ok === null).map(([k]) => k);

  return { periode: { fra: fraM, til: tilM }, klar: mangler.length === 0 && uavklart.length === 0, mangler, uavklart, sjekker: sj };
}

async function main() {
  const a = argumenter(process.argv.slice(2));
  // Med --aar tas bare avsluttede måneder med (til og med forrige måned).
  const d0 = new Date(); d0.setUTCDate(1); d0.setUTCMonth(d0.getUTCMonth() - 1);
  const naa = d0.toISOString().slice(0, 7);
  let aar, fraM, tilM, terminer;
  if (typeof a.aar === 'string' && /^\d{4}$/.test(a.aar)) {
    aar = Number(a.aar);
    fraM = `${aar}-01`;
    tilM = `${aar}-12` < naa ? `${aar}-12` : naa;
    if (tilM < fraM) throw new Error(`Ingen avsluttede måneder i ${aar} ennå. Ingenting er gjort.`);
    const sisteTermin = Math.floor(Number(tilM.slice(5, 7)) / 2);
    terminer = Array.from({ length: sisteTermin }, (_, i) => [aar, i + 1]);
  } else if (erMaaned(a.maaned)) {
    tilM = fraM = a.maaned;
    aar = Number(a.maaned.slice(0, 4));
    const t = Math.floor(Number(a.maaned.slice(5, 7)) / 2);
    terminer = [t ? [aar, t] : [aar - 1, 6]]; // siste termin som slutter i eller før måneden
  } else {
    throw new Error('Bruk: npm run -s status -- (--client "klient" | --alle) --maaned ÅÅÅÅ-MM [--json]  eller  --aar ÅÅÅÅ. Ingenting er gjort.');
  }
  const utvalg = await klientutvalg(a);
  const res = await perKlient(utvalg, (c) => port(c, { aar, fraM, tilM, terminer }));
  const rader = res.map((r) => (r.ok ? { klient: r.klient, orgnr: r.orgnr, ...r.data } : { klient: r.klient, orgnr: r.orgnr, klar: false, feil: r.feil }));
  if (a.json) { console.log(JSON.stringify(rader, null, 1)); return; }
  for (const x of rader) {
    if (x.feil) { console.log(`${x.klient}: kunne ikke leses (${x.feil})`); continue; }
    const uavklart = x.uavklart.length ? ` · kunne ikke avgjøres: ${x.uavklart.join(', ')}` : '';
    console.log(`${x.klient} ${x.periode.fra}${x.periode.fra !== x.periode.til ? `–${x.periode.til}` : ''}: ${x.klar ? 'klar' : 'ikke klar'}${x.mangler.length ? ` – ${x.mangler.join('; ')}` : ''}${uavklart}`);
  }
  if (rader.length > 1) console.log(`\n${rader.length} klienter: ${rader.filter((x) => x.klar).length} klare, ${rader.filter((x) => !x.klar).length} ikke klare.`);
}

main().catch((e) => { console.error(`Feil: ${kortFeil(e)}`); process.exitCode = 1; });
