// Pensjon (OTP): bokført pensjonskostnad mot pensjon rapportert i a-meldingene og i A07, per termin.
// Gjør KUN lesende kall – oppretter ingen avstemminger og bestiller ikke A07.
//
//   npm run -s pensjon -- --client "klient" --ar 2026 [--konto 5945]      (standard: alle kontoer 5940–5949)
//
// Kilder (testet 2026-09-23 på klient C):
//   Hovedbok:    GET /ledger/posting på kontoen(e), per måned.
//   A-melding:   pensionSum i GET /salary/payrollTax/reconciliation/{id}/overview (aggregatedZones), for AGA-avstemminger
//                som allerede finnes i byråets avstemmingsmodul (GET /accountingOffice/reconciliations, byråkontoen).
//   A07:         INTERNT GET /salary/tskinternal/amelding/reconciliation/reports/latest?contextId&fromYearMonth&toYearMonth
//                (klientens kontekst) → details.businesses[].payrollTax.pensionContributionsAndPremiums[].basisAmount.
//
// Pensjon rapporteres i hele kroner i a-meldingen, så øreavvik under 1 kr per termin regnes som likt.
// Registrering av pensjon (Lønn → Pensjon) finnes ikke i API-et – bare i Tripletex-UI (krever innlogging i nettleser).

import { connect } from './tripletex.js';
import { BASE_URL, authorization } from './auth.js';

const args = process.argv.slice(2);
const opt = (name) => {
  const i = args.indexOf(`--${name}`);
  return i >= 0 ? args[i + 1] : undefined;
};
const kr = (n) => (n == null ? '-' : n.toLocaleString('nb-NO', { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
const pad = (m) => String(m).padStart(2, '0');

// Byråkontoen (companyId 0) – tripletex.js blokkerer den med vilje, så lesekallene hit gjøres her.
async function agency(account, path) {
  const res = await fetch(BASE_URL + path, { headers: { Authorization: await authorization(0, account), Accept: 'application/json' } });
  if (!res.ok) throw new Error(`GET ${path.split('?')[0]} (${res.status}): ${(await res.text()).slice(0, 160)}`);
  return res.json();
}

try {
  const year = Number(opt('ar'));
  if (!year) throw new Error('Angi år med --ar ÅÅÅÅ.');
  const konto = opt('konto');
  const [from, to] = konto ? [Number(konto), Number(konto)] : [5940, 5949];
  const c = await connect(opt('client'));
  const contextId = (await c.request('/token/session/>whoAmI', { query: { fields: 'companyId' } })).value.companyId;

  // 1) Hovedbok per måned
  const postings = await c.list('/ledger/posting', {
    query: { dateFrom: `${year}-01-01`, dateTo: `${year + 1}-01-01`, accountNumberFrom: from, accountNumberTo: to, fields: 'date,amount,account(number)' },
  });
  const byMonth = Array(13).fill(0);
  for (const p of postings) byMonth[Number(p.date.slice(5, 7))] += p.amount;
  const accountsUsed = [...new Set(postings.map((p) => p.account?.number))].sort().join(', ') || 'ingen';

  // 2) A-melding: eksisterende AGA-avstemminger for klienten
  const recs = (
    await agency(c.company.account, '/accountingOffice/reconciliations?count=1000&fields=id,year,term,type,status,customer(id)')
  ).values.filter((r) => r.customer?.id === c.company.id && r.year === year && r.type === 'PAYROLL_TAX');

  console.log(`${c.company.name} – pensjon ${year}, konto ${accountsUsed}\n`);
  console.log('Termin  Måneder   Bokført     A-melding       A07     Avvik bokført–a-melding   Månedene (bokført)');
  const tot = { ledger: 0, amelding: 0, a07: 0 };
  for (let term = 1; term <= 6; term++) {
    const m1 = term * 2 - 1;
    const m2 = term * 2;
    const ledger = byMonth[m1] + byMonth[m2];
    const rec = recs.find((r) => r.term === term);
    let amelding = null;
    if (rec) {
      const { value } = await agency(c.company.account, `/salary/payrollTax/reconciliation/${rec.id}/overview`);
      if (value.ameldingSum != null) amelding = (value.aggregatedZones ?? []).reduce((s, z) => s + (z.pensionSum ?? 0), 0);
    }
    let a07 = null;
    const { value: rep } = await c.request('/salary/tskinternal/amelding/reconciliation/reports/latest', {
      query: { contextId, fromYearMonth: `${year}-${pad(m1)}`, toYearMonth: `${year}-${pad(m2)}` },
    });
    if (rep) a07 = (rep.details?.businesses ?? []).flatMap((b) => b.payrollTax?.pensionContributionsAndPremiums ?? []).reduce((s, b) => s + (b.basisAmount ?? 0), 0);
    if (!ledger && amelding == null && a07 == null) continue;

    const reported = amelding ?? a07;
    const diff = reported == null ? null : ledger - reported;
    const flag = diff == null ? '  (ikke rapportert/avstemt ennå)' : Math.abs(diff) >= 1 ? '  ⚠' : '  ✓';
    const a07flag = amelding != null && a07 != null && Math.abs(amelding - a07) >= 1 ? ' (a-melding ≠ A07!)' : '';
    tot.ledger += ledger;
    tot.amelding += amelding ?? 0;
    tot.a07 += a07 ?? 0;
    console.log(
      `T${term}      ${pad(m1)}–${pad(m2)}   ${kr(ledger).padStart(10)}  ${kr(amelding).padStart(10)}  ${kr(a07).padStart(10)}  ${kr(diff).padStart(12)}${flag}${a07flag}`.padEnd(95) +
        `${pad(m1)}: ${kr(byMonth[m1])}, ${pad(m2)}: ${kr(byMonth[m2])}`,
    );
  }
  console.log(`Sum               ${kr(tot.ledger).padStart(10)}  ${kr(tot.amelding).padStart(10)}  ${kr(tot.a07).padStart(10)}`);
  console.log(`\nSaldo ${accountsUsed} hittil i ${year}: ${kr(tot.ledger)} (${postings.length} posteringer).`);
  console.log('A-melding = pensjon i AGA-avstemmingen (bare terminer som finnes i avstemmingsmodulen). A07 = siste hentede A07 for terminen.');
  console.log('Avvik rettes ved å registrere/korrigere pensjon i Lønn → Pensjon for riktig måned og sende ny a-melding for den måneden.');
} catch (err) {
  console.error(`Feil: ${err.message}`);
  process.exitCode = 1;
}
