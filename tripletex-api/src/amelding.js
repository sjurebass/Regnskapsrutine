// A-melding: status, oversikt og innsending.
//
//   npm run -s amelding -- status   (--client "klient" [--client …] | --alle) --maned 2026-08 [--json]
//   npm run -s amelding -- oversikt (--client "klient" [--client …] | --alle) --ar 2026 [--json]
//   npm run -s amelding -- send     --client "klient" --maned 2026-08 [--kun-arbeidsforhold] [--bilagsdato 2026-08-31] [--bekreft]
//
// Bruker Tripletex sine interne kall (samme som Tripletex-UI-et), funnet i GET /v2/openapi.json?internal=true –
// de står ikke i den offentlige specen:
//   GET  /salary/tskinternal/amelding/ameldingStatus?date=   (kjøres i klientens kontekst)
//   (GET /tsk/salaryv2/overview/amessage finnes, men gir 403 med API-nøkkel – oversikt spør derfor per måned)
//   POST /salary/tskinternal/amelding/send  {date, voucherDate?, employmentInformationOnly?}
//
// Grupper (status): ikke sendt · venter · godkjent · avvist · endret etter innsending · kunne ikke leses.
// «Kunne ikke leses» (feil, manglende lønnsmodul eller rettighet) er aldri det samme som «ikke sendt».
//
// Innsending er en lovpålagt innlevering til Skatteetaten som ikke kan trekkes tilbake. Uten --bekreft
// vises bare status og hva som ville blitt sendt. --bekreft brukes bare etter ja fra brukeren for akkurat den klienten og måneden.
// Utskriften inneholder bare beløp per klient (aggregater) – ingen ansattdata.

import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { connect, bind } from './tripletex.js';
import { redact } from './privacy.js';
import { argumenter, klientutvalg, perKlient, erMaaned, kortFeil } from './valg.js';

const [command, ...rest] = process.argv.slice(2);
const a = argumenter(rest);

const STATUS_TEXT = {
  noAmeldingExists: 'Ingen a-melding registrert for måneden – må sendes (også uten lønn, for arbeidsforhold).',
  ameldingExistsNotSent: 'A-melding er registrert, men ikke sendt.',
  ameldingRejected: 'Forrige innsending ble avvist av Skatteetaten – rett feilen før ny innsending.',
  nonReportedWageinfo: 'Det finnes lønn/pensjon som ikke er rapportert – ny a-melding trengs.',
  ameldingSentAwaitingReturnMessage: 'Sendt – venter på tilbakemelding fra Skatteetaten.',
  ameldingCancelledAwaitingReturnMessage: 'Sletting sendt – venter på tilbakemelding fra Skatteetaten.',
  okReturnMessage: 'Godkjent av Skatteetaten.',
  nonBlockingReturnMessage: 'Godkjent med avvik som ikke stopper meldingen – les tilbakemeldingen.',
  blockingReturnMessage: 'Avvist: tilbakemeldingen har avvik som stopper meldingen.',
  unknown: 'Ukjent status fra Tripletex.',
};

/** Gruppen i a-melding-skillen for én status. Usendt lønn etter en tidligere innsending = «endret etter innsending». */
export function gruppe(s) {
  if (!s) return 'kunne ikke leses';
  switch (s.ameldingDetailedStatus) {
    case 'noAmeldingExists':
    case 'ameldingExistsNotSent': return 'ikke sendt';
    case 'nonReportedWageinfo': return s.lastAmeldingActionTime ? 'endret etter innsending' : 'ikke sendt';
    case 'ameldingRejected':
    case 'blockingReturnMessage': return 'avvist';
    case 'ameldingSentAwaitingReturnMessage':
    case 'ameldingCancelledAwaitingReturnMessage': return 'venter';
    case 'okReturnMessage':
    case 'nonBlockingReturnMessage': return 'godkjent';
    default:
      if (s.ameldingSummaryStatus === 'completed') return 'godkjent';
      if (s.ameldingSummaryStatus === 'awaitingResponse') return 'venter';
      return 'kunne ikke leses';
  }
}

function maned(value) {
  if (!erMaaned(value)) throw new Error('Angi måned som --maned ÅÅÅÅ-MM (f.eks. 2026-08). Måneden gjettes aldri.');
  return value;
}

export async function status(c, m) {
  const { value } = await c.request('/salary/tskinternal/amelding/ameldingStatus', {
    query: {
      date: `${m}-01`,
      fields:
        'ameldingSummaryStatus,ameldingDetailedStatus,lastAmeldingActionTime,lastPaymentActionTime,taxPeriodName,' +
        'taxDeductionAccrued,payrollTaxAccrued,financeTaxAccrued,mandatoryDeductionAccrued,' +
        'taxDeductionNotPaid,payrollTaxNotPaid,financeTaxNotPaid,mandatoryDeductionNotPaid',
    },
  });
  return value;
}

/** Kompakt status for JSON: gruppe, forklaring og beløp (ingen personopplysninger). */
export function kort(m, s) {
  return {
    maaned: m, gruppe: gruppe(s), status: `${s.ameldingSummaryStatus} / ${s.ameldingDetailedStatus}`,
    forklaring: STATUS_TEXT[s.ameldingDetailedStatus] ?? null, sistSendt: s.lastAmeldingActionTime ?? null, termin: s.taxPeriodName ?? null,
    paaloept: { trekk: s.taxDeductionAccrued ?? 0, aga: s.payrollTaxAccrued ?? 0, finansskatt: s.financeTaxAccrued ?? 0, utlegg: s.mandatoryDeductionAccrued ?? 0 },
    ikkeBetalt: { trekk: s.taxDeductionNotPaid ?? 0, aga: s.payrollTaxNotPaid ?? 0, finansskatt: s.financeTaxNotPaid ?? 0, utlegg: s.mandatoryDeductionNotPaid ?? 0 },
  };
}

const kr = (n) => (n ?? 0).toLocaleString('nb-NO', { minimumFractionDigits: 2, maximumFractionDigits: 2 });

function printStatus(navn, m, s) {
  console.log(`${navn} – a-melding ${m}: ${gruppe(s)}`);
  console.log(`  Status:        ${s.ameldingSummaryStatus} / ${s.ameldingDetailedStatus}`);
  if (STATUS_TEXT[s.ameldingDetailedStatus]) console.log(`                 ${STATUS_TEXT[s.ameldingDetailedStatus]}`);
  console.log(`  Sist sendt:    ${s.lastAmeldingActionTime ?? '-'}`);
  console.log(`  Termin:        ${s.taxPeriodName}`);
  console.log(`  Påløpt:        trekk ${kr(s.taxDeductionAccrued)}, AGA ${kr(s.payrollTaxAccrued)}, finansskatt ${kr(s.financeTaxAccrued)}, utlegg ${kr(s.mandatoryDeductionAccrued)}`);
  console.log(`  Ikke betalt:   trekk ${kr(s.taxDeductionNotPaid)}, AGA ${kr(s.payrollTaxNotPaid)}, finansskatt ${kr(s.financeTaxNotPaid)}, utlegg ${kr(s.mandatoryDeductionNotPaid)}`);
}

async function cmdStatus() {
  const m = maned(a.maned);
  const utvalg = await klientutvalg(a);
  const res = await perKlient(utvalg, async (c) => status(bind(c), m));
  if (a.json) {
    console.log(JSON.stringify(res.map((r) => (r.ok
      ? { klient: r.klient, orgnr: r.orgnr, ...kort(m, r.data) }
      : { klient: r.klient, orgnr: r.orgnr, maaned: m, gruppe: 'kunne ikke leses', feil: r.feil })), null, 1));
    return;
  }
  for (const r of res) {
    if (r.ok) printStatus(r.klient, m, r.data);
    else console.log(`${r.klient} – a-melding ${m}: kunne ikke leses (${r.feil})`);
  }
  if (res.length > 1) {
    const telling = {};
    for (const r of res) { const g = r.ok ? gruppe(r.data) : 'kunne ikke leses'; telling[g] = (telling[g] ?? 0) + 1; }
    console.log(`\n${res.length} klienter: ${Object.entries(telling).map(([g, n]) => `${g} ${n}`).join(', ')}`);
  }
}

async function cmdOversikt() {
  const year = Number(a.ar);
  if (!(year > 2000)) throw new Error('Angi år med --ar ÅÅÅÅ.');
  // /tsk/salaryv2/overview/amessage gir 403 med API-nøkkel (krever nettleserinnlogging), så vi spør per måned.
  const now = new Date().toISOString().slice(0, 7);
  const maaneder = Array.from({ length: 12 }, (_, i) => `${year}-${String(i + 1).padStart(2, '0')}`).filter((m) => m <= now);
  const utvalg = await klientutvalg(a);
  const res = await perKlient(utvalg, async (c) => {
    const b = bind(c);
    const ut = [];
    for (const m of maaneder) {
      try { ut.push(kort(m, await status(b, m))); } catch (e) { ut.push({ maaned: m, gruppe: 'kunne ikke leses', feil: kortFeil(e) }); }
    }
    return ut;
  });
  if (a.json) {
    console.log(JSON.stringify(res.map((r) => (r.ok ? { klient: r.klient, orgnr: r.orgnr, maaneder: r.data } : { klient: r.klient, orgnr: r.orgnr, feil: r.feil })), null, 1));
    return;
  }
  for (const r of res) {
    console.log(`${r.klient} – a-meldinger ${year}`);
    if (!r.ok) { console.log(`  kunne ikke leses (${r.feil})`); continue; }
    for (const x of r.data) console.log(`  ${x.maaned}  ${x.gruppe.padEnd(24)} ${x.status ?? x.feil ?? ''}  ${x.termin ?? ''}`);
  }
}

async function cmdSend() {
  const m = maned(a.maned);
  if ((a.flere.client ?? []).length !== 1 || a.alle) throw new Error('send gjelder én klient: --client "klient". Ingenting er gjort.');
  const c = await connect(a.client);
  const employmentInformationOnly = !!a['kun-arbeidsforhold'];
  const voucherDate = typeof a.bilagsdato === 'string' ? a.bilagsdato : undefined;
  const s = await status(c, m);
  printStatus(c.company.name, m, s);
  console.log('');
  console.log(
    `Vil sende: ${employmentInformationOnly ? 'kun arbeidsforholdsopplysninger (ingen lønn)' : 'a-melding med lønn/pensjon'} for ${m}` +
      (voucherDate ? `, bilagsdato ${voucherDate}` : ''),
  );
  if (!a.bekreft) {
    console.log('Ikke sendt. Legg til --bekreft for å sende (lovpålagt innlevering, kan ikke trekkes tilbake).');
    return;
  }
  const { value } = await c.request('/salary/tskinternal/amelding/send', {
    method: 'POST',
    body: { date: `${m}-01`, employmentInformationOnly, ...(voucherDate ? { voucherDate } : {}) },
  });
  console.log(JSON.stringify(redact(value), null, 2));
  if (value.kind === 'NOTHING_TO_SEND') console.log('Alt for måneden er allerede rapportert – ingenting sendt.');
  else console.log(`Sendt. Sjekk tilbakemeldingen med: npm run -s amelding -- status --client "${c.company.name}" --maned ${m}`);
}

const commands = { status: cmdStatus, oversikt: cmdOversikt, send: cmdSend };
// Kjøres bare som kommando; status.js importerer status() og gruppe() herfra.
if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    if (!commands[command]) throw new Error(`Bruk: npm run -s amelding -- ${Object.keys(commands).join('|')} (--client "klient" | --alle) ...`);
    await commands[command]();
  } catch (err) {
    console.error(`Feil: ${kortFeil(err)}`);
    process.exitCode = 1;
  }
}
