// Skattekontoen (SK): krav og betalinger fra Skatteetaten via /claimsAndPayments, mot saldoene i hovedboken.
// Gjelder også klienter uten mva-registrering (skatt, forskuddstrekk, arbeidsgiveravgift, gebyrer).

import { lagFunn, kr } from '../felles.js';

// Kravgruppe → balansekontoer som skal dekke kravet.
const KONTOER = {
  Merverdiavgift: [[2740, 2740]],
  Skatt: [[2500, 2549]],
  Forskuddstrekk: [[2600, 2609]],
  Arbeidsgiveravgift: [[2770, 2789]],
};

export function skattekonto(d, { t, idag = new Date().toISOString().slice(0, 10) }) {
  const funn = [];
  const sk = d.skattekonto;
  if (!sk || (sk.feil && !sk.krav?.length)) {
    return [lagFunn({ kontroll: 'SK2', alvor: 'INFO', nivaa: 'klient', tittel: 'Skattekontoen kunne ikke leses', detalj: sk?.feil ?? 'ingen data (krever Altinn-systembruker)' })];
  }
  const aapne = sk.krav.filter((c) => Math.abs(c.outstandingAmount ?? 0) >= 1);
  const forfalt = aapne.filter((c) => c.dueDate && c.dueDate < idag && (c.outstandingAmount ?? 0) > 0);
  if (forfalt.length) {
    const sum = forfalt.reduce((s, c) => s + (c.outstandingAmount ?? 0), 0);
    funn.push(lagFunn({ kontroll: 'SK3', alvor: 'FORKLAR', nivaa: 'klient', belop: sum,
      tittel: `${forfalt.length} forfalte krav på skattekontoen`,
      detalj: forfalt.map((c) => `${c.claimGroup ?? ''} ${c.periodDescription ?? ''}: ${kr(c.outstandingAmount)} kr, forfall ${c.dueDate}${c.rent ? `, renter ${kr(c.rent)}` : ''}`.trim()).join('; '),
      handling: 'Avklar betaling med kunden. Renter løper til kravene er betalt.' }));
  }
  // Åpne krav per gruppe mot saldo i dag på tilhørende konto (saldo per D er det nærmeste vi har – betalinger etter D forklarer differanser).
  const perGruppe = {};
  for (const c of aapne) perGruppe[c.claimGroup ?? 'Andre krav'] = (perGruppe[c.claimGroup ?? 'Andre krav'] ?? 0) + (c.outstandingAmount ?? 0);
  const linjer = [];
  for (const [gruppe, utestaaende] of Object.entries(perGruppe)) {
    const kontoer = KONTOER[gruppe];
    const saldo = kontoer ? -d.saldo.filter((s) => kontoer.some(([a, b]) => s.account.number >= a && s.account.number <= b)).reduce((s, x) => s + x.balanceOut, 0) : null;
    linjer.push(`${gruppe}: ${kr(utestaaende)} kr${saldo === null ? ' (ingen konto)' : `, hovedbok ${kr(saldo)} kr per ${t.sisteDag}`}`);
  }
  funn.push(lagFunn({ kontroll: 'SK2', alvor: 'INFO', nivaa: 'klient', belop: aapne.reduce((s, c) => s + (c.outstandingAmount ?? 0), 0),
    tittel: `${aapne.length} åpne poster på skattekontoen${sk.feil ? ' (ufullstendig)' : ''}`, detalj: `${linjer.join('; ') || 'Ingen åpne krav.'}${sk.feil ? ` Ett av årene kunne ikke hentes: ${sk.feil}` : ''}`,
    data: aapne.map((c) => ({ gruppe: c.claimGroup, type: c.claimType, periode: c.periodDescription, forfall: c.dueDate, utestaaende: c.outstandingAmount, renter: c.rent })) }));
  return funn;
}
