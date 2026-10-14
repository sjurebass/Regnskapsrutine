// Tester hvilke områder tokenet har lesetilgang til hos én klient. Gjør KUN GET-kall.
//   npm run -s probe -- --client "Klient AS"
// Leser én post fra hvert område (også /employee og /salary) og viser bare status – ingen data. Kjør ved behov, ikke rutinemessig.

import { connect } from './tripletex.js';

const today = new Date();
const iso = (d) => d.toISOString().slice(0, 10);
const tomorrow = iso(new Date(today.getTime() + 86400000)); // dateTo er eksklusiv i Tripletex
const from = `${today.getFullYear() - 1}-01-01`;
const range = { dateFrom: from, dateTo: tomorrow };

const CHECKS = [
  ['Byrå', 'Rettigheter hos klienten', '/employee/entitlement/client'],
  ['Hovedbok', 'Hovedbok', '/ledger', range],
  ['Hovedbok', 'Saldobalanse', '/balanceSheet', range],
  ['Hovedbok', 'Posteringer', '/ledger/posting', range],
  ['Hovedbok', 'Åpne poster', '/ledger/openPost', { date: iso(today) }],
  ['Hovedbok', 'Kontoplan', '/ledger/account'],
  ['Hovedbok', 'MVA-koder', '/ledger/vatType'],
  ['Hovedbok', 'MVA-innstillinger', '/ledger/vatSettings'],
  ['Hovedbok', 'Regnskapsperioder', '/ledger/accountingPeriod'],
  ['Hovedbok', 'Regnskapsår', '/ledger/annualAccount'],
  ['Hovedbok', 'Frie dimensjoner', '/ledger/accountingDimensionName'],
  ['Hovedbok', 'Konteringsregler', '/ledger/postingRules'],
  ['Hovedbok', 'Lukkegrupper', '/ledger/closeGroup', range],
  ['Bilag', 'Bilag', '/ledger/voucher', range],
  ['Bilag', 'Ikke-bokførte bilag', '/ledger/voucher/>nonPosted', { includeNonApproved: true }],
  ['Bilag', 'Bilagsmottak', '/ledger/voucher/>voucherReception'],
  ['Bilag', 'Bilagstyper', '/ledger/voucherType'],
  ['Bilag', 'Antall i innboks', '/voucherInbox/inboxCount'],
  ['Bilag', 'Bilagsstatus (integrasjon)', '/voucherStatus'],
  ['Bank', 'Kontoutskrifter', '/bank/statement'],
  ['Bank', 'Bankavstemminger', '/bank/reconciliation'],
  ['Bank', 'Avstemmingsinnstillinger', '/bank/reconciliation/settings'],
  ['Bank', 'Utbetalingstyper', '/ledger/paymentTypeOut'],
  ['Salg', 'Kunder', '/customer'],
  ['Salg', 'Kontakter', '/contact'],
  ['Salg', 'Prospekter', '/crm/prospect'],
  ['Salg', 'Ordre', '/order', { orderDateFrom: from, orderDateTo: tomorrow }],
  ['Salg', 'Fakturaer', '/invoice', { invoiceDateFrom: from, invoiceDateTo: tomorrow }],
  ['Salg', 'Innbetalingstyper', '/invoice/paymentType'],
  ['Salg', 'Purringer', '/reminder', range],
  ['Leverandør', 'Leverandører', '/supplier'],
  ['Leverandør', 'Leverandørfakturaer', '/supplierInvoice', { invoiceDateFrom: from, invoiceDateTo: tomorrow }],
  ['Leverandør', 'Til godkjenning', '/supplierInvoice/forApproval'],
  ['Produkt/lager', 'Produkter', '/product'],
  ['Produkt/lager', 'Enheter', '/product/unit'],
  ['Produkt/lager', 'Lager', '/inventory'],
  ['Produkt/lager', 'Innkjøpsordre', '/purchaseOrder'],
  ['Prosjekt', 'Prosjekter', '/project'],
  ['Prosjekt', 'Prosjektkategorier', '/project/category'],
  ['Prosjekt', 'Aktiviteter', '/activity'],
  ['Prosjekt', 'Prosjektinnstillinger', '/project/settings'],
  ['Organisasjon', 'Avdelinger', '/department'],
  ['Organisasjon', 'Virksomheter (divisjoner)', '/division'],
  ['Organisasjon', 'Salgsmoduler', '/company/salesmodules'],
  ['Organisasjon', 'Altinn-innstillinger', '/company/settings/altinn'],
  ['Ansatte/lønn', 'Ansatte', '/employee'],
  ['Ansatte/lønn', 'Arbeidsforhold', '/employee/employment'],
  ['Ansatte/lønn', 'Lønnsslipper', '/salary/payslip'],
  ['Ansatte/lønn', 'Lønnsarter', '/salary/type'],
  ['Ansatte/lønn', 'Lønnsinnstillinger', '/salary/settings'],
  ['Timer/reise', 'Timeføringer', '/timesheet/entry', range],
  ['Timer/reise', 'Timeuker', '/timesheet/week'],
  ['Timer/reise', 'Timeinnstillinger', '/timesheet/settings'],
  ['Timer/reise', 'Reiseregninger/utlegg', '/travelExpense'],
  ['Timer/reise', 'Reiseinnstillinger', '/travelExpense/settings'],
  ['Avgift/årsoppgjør', 'MVA-status', '/vatReturns/status'],
  ['Avgift/årsoppgjør', 'SAF-T-status', '/saft/status'],
  ['Avgift/årsoppgjør', 'Signering årsregnskap', '/yearEnd/penneo/signingStatus', { year: today.getFullYear() - 1 }],
  ['Budsjett/anlegg', 'Resultatbudsjett', '/resultbudget/company'],
  ['Budsjett/anlegg', 'Anleggsmidler', '/asset'],
  ['Oppsett', 'Valuta', '/currency'],
  ['Oppsett', 'Webhook-hendelser', '/event'],
  ['Oppsett', 'Webhook-abonnement', '/event/subscription'],
];

const argv = process.argv.slice(2);
const ci = argv.indexOf('--client');
const client = await connect(ci >= 0 ? argv[ci + 1] : argv.find((x) => !x.startsWith('--')));
console.log(`Tester lesetilgang hos ${client.company.name} (${CHECKS.length} områder, kun GET)\n`);

const results = [];
for (const [area, label, path, query = {}] of CHECKS) {
  let status, info;
  try {
    const r = await client.request(path, { method: 'GET', query: { count: 1, ...query } });
    status = 'OK';
    // fullResultSize er ikke pålitelig med count=1, så vi sier bare om det finnes data.
    info = Array.isArray(r?.values) ? (r.values.length ? 'har data' : 'tom') : r?.value !== undefined ? 'har data' : '';
  } catch (err) {
    const code = err.message.match(/feilet \((\d+)\)/)?.[1];
    status = { 403: 'INGEN TILGANG', 401: 'IKKE INNLOGGET', 404: 'IKKE FUNNET', 422: 'UGYLDIG FORESPØRSEL' }[code] ?? `FEIL ${code ?? ''}`.trim();
    const msg = err.message.match(/"message"\s*:\s*"([^"]+)"/)?.[1];
    info = msg ?? '';
  }
  results.push({ area, label, path, status, info });
  console.log(`${status === 'OK' ? '✓' : '✗'} ${area.padEnd(18)} ${label.padEnd(28)} ${status.padEnd(14)} ${info}`);
}

const ok = results.filter((r) => r.status === 'OK').length;
console.log(`\n${ok} av ${results.length} områder lesbare.`);
