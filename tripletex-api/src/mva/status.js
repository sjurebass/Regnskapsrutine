// Mva-status per klient og termin: registrering, terminlengde, levert, betalt, rest, forfall, KID, saldo 2740 og
// åpne mva-krav på skattekontoen. KUN LESING, sekvensielle kall. Ingen personopplysninger (bare beløp og status).
//
//   npm run -s mva -- status (--client "klient" [--client …] | --alle) --aar 2026 --termin 4 [--json]
//
// --termin er den vanlige tomånedersterminen (1 = jan–feb … 6 = nov–des). For klienter med annen terminlengde
// (måned/år) vises terminen som slutter i terminens siste måned; slutter ingen termin der, er `aktuell` false.
// Kall: /ledger/vatSettings, /vatTermSizeSettings, /vatReturns/status (kalendernummer), /vatReturns/{id}/paymentInfo
// (internt), /balanceSheet (2740) og /claimsAndPayments (internt, skattekontoen).

import { forsok } from './felles.js';

const pad = (n) => String(n).padStart(2, '0');
const rund = (n) => (n == null ? null : Math.round(n * 100) / 100);
const MND_PER_TERMIN = { ONE_MONTH: 1, TWO_MONTHS: 2, THREE_MONTHS: 3, FOUR_MONTHS: 4, SIX_MONTHS: 6, YEAR: 12 };
const LEVERT = new Set(['RECEIPT_RECEIVED', 'MANUAL_DELIVERY']);
const BETALT = new Set(['PAYMENT_REGISTERED', 'NO_TAX_TO_PAY', 'AMOUNT_CREDITED']);

/** Lovbestemt frist når paymentInfo ikke kan leses (mval. § 15-9 / skatteforvaltningsforskriften). */
function beregnetFrist(aar, termSize, klientTermin, sluttMnd) {
  if (termSize === 'TWO_MONTHS') return { 1: `${aar}-04-10`, 2: `${aar}-06-10`, 3: `${aar}-08-31`, 4: `${aar}-10-10`, 5: `${aar}-12-10`, 6: `${aar + 1}-02-10` }[klientTermin] ?? null;
  if (termSize === 'YEAR') return `${aar + 1}-03-10`;
  // Månedlig o.l.: én måned og ti dager etter terminslutt.
  const d = new Date(Date.UTC(aar, sluttMnd + 1, 10));
  return d.toISOString().slice(0, 10);
}

export function gruppe(x) {
  if (x.feil) return 'kunne ikke leses';
  if (!x.registrert) return 'ikke registrert';
  if (!x.aktuell) return 'ingen terminslutt';
  if (!LEVERT.has(x.levert)) return x.levert === 'WAITING_FOR_REPLY' || x.levert === 'SENDING' ? 'sendt, venter på kvittering' : 'ikke levert';
  if (!BETALT.has(x.betalt)) return 'levert, ikke betalt';
  return 'levert og betalt';
}

/** Status for én klient (`b` fra connect()/bind()) og tomånedersterminen `termin` i `aar`. */
export async function mvaStatus(b, aar, termin) {
  const sluttMnd = termin * 2;
  const forsteDag = `${aar}-${pad(sluttMnd - 1)}-01`;
  const D = sluttMnd === 12 ? `${aar + 1}-01-01` : `${aar}-${pad(sluttMnd + 1)}-01`; // eksklusiv
  const vat = (await b.request('/ledger/vatSettings', { query: { fields: 'vatRegistrationStatus' } }))?.value ?? {};
  const rader = (await b.list('/vatTermSizeSettings', { query: { fields: 'reportType,fromDate,termSize', sorting: 'fromDate' } }))
    .filter((t) => t.reportType === 'GENERAL_INDUSTRY' && t.fromDate <= forsteDag);
  const termSize = rader.at(-1)?.termSize ?? null;
  const ut = {
    termin: `${termin}/${aar}`, registrering: vat.vatRegistrationStatus ?? null, terminlengde: termSize,
    registrert: vat.vatRegistrationStatus === 'VAT_REGISTERED' && termSize !== 'NOT_REGISTERED',
  };
  if (!ut.registrert) return { ...ut, aktuell: false, gruppe: gruppe({ ...ut }) };

  const mnd = MND_PER_TERMIN[termSize] ?? 2;
  const klientTermin = Math.ceil(sluttMnd / mnd);
  ut.klientTermin = klientTermin;
  ut.aktuell = klientTermin * mnd === sluttMnd;
  if (ut.aktuell) {
    const s = (await forsok(() => b.request('/vatReturns/status', { query: {
      year: aar, term: klientTermin, reportType: 'GENERAL_INDUSTRY',
      fields: 'vatReturns2022Id,voucherNumber,altinnPaymentAmount,deliveryStatus(status,time),paymentStatus(status,totalAmount,remainingAmount,paymentDate)',
    } })));
    const v = s.ok ? s.data?.value ?? {} : {};
    if (!s.ok) ut.statusFeil = s.feil.replace(/\{.*$/, '').slice(0, 160);
    ut.levert = v.deliveryStatus?.status ?? null;
    ut.levertTid = v.deliveryStatus?.time ?? null;
    ut.betalt = v.paymentStatus?.status ?? null;
    ut.betaltDato = v.paymentStatus?.paymentDate ?? null;
    ut.aaBetale = rund(v.altinnPaymentAmount ?? v.paymentStatus?.totalAmount ?? null);
    ut.rest = rund(v.paymentStatus?.remainingAmount ?? null);
    ut.oppgjorsbilag = v.voucherNumber || null;
    ut.forfall = null; ut.kid = null; ut.forfallKilde = null;
    if (v.vatReturns2022Id) {
      const p = await forsok(() => b.request(`/vatReturns/${v.vatReturns2022Id}/paymentInfo`, { query: { fields: 'kid,amount,dueDate' } }));
      if (p.ok && p.data?.value) { ut.forfall = p.data.value.dueDate ?? null; ut.kid = p.data.value.kid ?? null; ut.forfallKilde = ut.forfall ? 'paymentInfo' : null; }
    }
    if (!ut.forfall) { ut.forfall = beregnetFrist(aar, termSize, klientTermin, sluttMnd); ut.forfallKilde = 'beregnet (lovbestemt frist)'; }
  }

  const s2740 = await b.list('/balanceSheet', { query: { dateFrom: `${aar}-01-01`, dateTo: D, accountNumberFrom: 2740, accountNumberTo: 2740, fields: 'account(number),balanceOut' } });
  ut.saldo2740 = rund(s2740.find((x) => x.account?.number === 2740)?.balanceOut ?? 0);

  const krav = await forsok(() => b.list('/claimsAndPayments', { query: { year: aar, fields: 'claimType,periodDescription,outstandingAmount,dueDate' } }));
  if (krav.ok) {
    const mva = krav.data.filter((x) => /mva|merverdi/i.test(`${x.claimType} ${x.periodDescription}`) && Math.abs(x.outstandingAmount ?? 0) >= 1);
    ut.skattekonto = { aapneMvaKrav: mva.length, sum: rund(mva.reduce((s, x) => s + (x.outstandingAmount ?? 0), 0)),
      krav: mva.map((x) => ({ type: x.claimType ?? null, periode: x.periodDescription ?? null, utestaaende: rund(x.outstandingAmount), forfall: x.dueDate ?? null })) };
  } else {
    ut.skattekonto = { feil: krav.feil.replace(/\{.*$/, '').slice(0, 160) };
  }
  ut.gruppe = gruppe(ut);
  return ut;
}
