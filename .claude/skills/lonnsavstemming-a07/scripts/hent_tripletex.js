// Henter regnskapssiden til lønnsavstemmingen (ledger.json) fra Tripletex-MCP-en.
// Kjøres i tripletex_run_script: lim inn hele fila som `code` og sett de fire konstantene øverst.
// Bare lesing. Returnerer { balanser, posteringer, advarsler } i formatet lonnsavstemming_a07.py forventer
// (se ledger_eksempel.json). Resten av ledger.json (selskap, periode, satser, KID, merknader) fylles inn etterpå.
//
// Personvern: posteringstekstene i lønnsbilag har ikke ansattnavn ("Lønnsbilag N-ÅÅÅÅ"), men kontroller
// utdataene før de vises i chatten. Lagre ledger.json bare i scratch.

const KLIENT = '<klientnavn fra search_client_companies>';
const D1 = '2026-07-01';   // første dag i terminen
const D2 = '2026-09-01';   // første dag etter terminen (eksklusiv)
const Y1 = '2026-01-01';   // 1. januar samme år (pensjon og saldo hittil i år)

const OMRAADER = [
  [1920, 1920], [1950, 1950], [2600, 2600], [2770, 2799], [2900, 2999],
  [5000, 5999], [7100, 7199], [7740, 7740],
];

const advarsler = [];
const tall = (x) => (x == null || x === '' ? 0 : Number(x));
const felt = (r, ...navn) => { for (const n of navn) { const v = n.split('.').reduce((o, k) => (o == null ? o : o[k]), r); if (v != null) return v; } return null; };

async function posteringer(fra, til, kFra, kTil) {
  const ut = [];
  for (let from = 0; ; from += 100) {
    const r = await tlx.search_ledger_postings({ companyName: KLIENT, dateFrom: fra, dateTo: til, accountNumberFrom: kFra, accountNumberTo: kTil, from, count: 100 });
    const rader = r.postings ?? r.values ?? r.rows ?? (Array.isArray(r) ? r : []);
    ut.push(...rader);
    if (rader.length < 100) break;
  }
  return ut;
}

function rad(p) {
  return [
    String(felt(p, 'date', 'voucherDate', 'voucher.date') ?? '').slice(0, 10),
    String(felt(p, 'voucher.number', 'voucherNumber', 'voucher.voucherNumber') ?? ''),
    Number(felt(p, 'account.number', 'accountNumber')),
    String(felt(p, 'account.name', 'accountName') ?? ''),
    String(felt(p, 'description', 'voucher.description', 'text') ?? ''),
    tall(felt(p, 'amount', 'amountNok')),
  ];
}

// Posteringer i terminen. 1920 tas bare med for linjer som hører til lønn (betaling av lønn, trekk og AGA).
const alle = [];
for (const [fra, til] of OMRAADER) {
  try {
    const p = await posteringer(D1, D2, fra, til);
    for (const x of p) {
      const r = rad(x);
      if (fra === 1920 && !/lønn|lonn|skattetrekk|forskuddstrekk|arbeidsgiveravgift|aga|a-melding/i.test(r[4])) continue;
      alle.push(r);
    }
  } catch (e) { advarsler.push(`Posteringer ${fra}–${til}: ${e.message}`); }
}
if (alle.length && !alle[0][0]) advarsler.push('Fant ikke datofeltet i posteringene. Sjekk formen med ett kall og rett felt() i rad().');

// Saldoer i terminen (IB, bevegelse, UB) for lønnskontoene.
const balanser = [];
for (const [fra, til] of [[1950, 1950], [2600, 2600], [2770, 2799], [2900, 2999], [5000, 5999]]) {
  try {
    const b = await tlx.get_balance_sheet({ companyName: KLIENT, dateFrom: D1, dateToExclusive: D2, accountNumberFrom: fra, accountNumberTo: til });
    for (const x of (b.accounts ?? b.rows ?? b.values ?? [])) {
      balanser.push({
        a: Number(felt(x, 'account.number', 'accountNumber', 'number')),
        n: String(felt(x, 'account.name', 'accountName', 'name') ?? ''),
        ib: tall(felt(x, 'balanceIn')), ch: tall(felt(x, 'balanceChange')), ub: tall(felt(x, 'balanceOut')),
      });
    }
  } catch (e) { advarsler.push(`Saldo ${fra}–${til}: ${e.message}`); }
}
// get_balance_sheet kan utelate 2600 når IB, bevegelse og UB er 0. Da regnes 2600 fra posteringene.
if (!balanser.some((b) => b.a === 2600)) advarsler.push('2600 mangler i saldobalansen – bruk posteringene.');

// Pensjon hittil i år (594x/5950 og AGA-linjer på «Pensjon <måned>»-bilag), til pensjon_historikk.
let pensjon = [];
try {
  const p = await posteringer(Y1, D2, 5940, 5959);
  const aga = await posteringer(Y1, D2, 5400, 5400);
  pensjon = [
    ...p.map(rad),
    ...aga.map(rad).filter((r) => /^pensjon/i.test(r[4])),
  ];
} catch (e) { advarsler.push(`Pensjon hittil i år: ${e.message}`); }

return { klient: KLIENT, periode: { d1: D1, d2: D2 }, balanser, posteringer: alle, pensjon_rader: pensjon, advarsler };
