// Bank (BK): bruker resultatet fra npm run bankavstemming (status per konto og måned, samme vurdering som
// bankavstemming-skillen). Banktekster ligger i arbeidsmappa og brukes aldri i funnene – bare antall og beløp.

import { lagFunn, kr } from '../felles.js';

export function bank(d, { t, aarlig = false }) {
  const funn = [];
  if (!d.bank || !Array.isArray(d.bank.kontoer)) {
    return [lagFunn({ kontroll: 'BK0', alvor: 'FORKLAR', nivaa: 'klient', tittel: 'Bankavstemmingen kunne ikke leses', detalj: String(d.bank?.feil ?? 'ingen data').slice(0, 200) })];
  }
  const manuell = [];
  // BK1 – banktransaksjoner uten bilag i terminens måneder: kan skjule kostnader eller inntekter.
  for (const k of d.bank.kontoer) {
    const mnd = k.maaneder.filter((m) => t.maaneder.includes(m.maaned));
    const umatchet = mnd.filter((m) => m.aapen).reduce((s, m) => s + (m.bank?.length ?? 0), 0);
    if (umatchet) {
      const sum = mnd.flatMap((m) => m.bank ?? []).reduce((s, x) => s + (x.belop ?? 0), 0);
      funn.push(lagFunn({ kontroll: 'BK1', alvor: 'BLOKK', nivaa: 'konto', konto: k.nummer, belop: sum,
        tittel: `${umatchet} banktransaksjoner uten bilag på ${k.nummer} i terminen`, detalj: `Netto ${kr(sum)} kr.`,
        handling: 'Be kunden om bilag (Excel fra bankavstemmingen), og bokfør før terminen avsluttes.' }));
    } else if (aarlig && mnd.length && mnd.every((m) => m.lukket)) {
      funn.push(lagFunn({ kontroll: 'BK1', alvor: 'INFO', nivaa: 'konto', konto: k.nummer, tittel: `Bankkonto ${k.nummer} er avstemt for terminen` }));
    }
    // BK8 – konto uten bankintegrasjon: det må finnes en lukket manuell avstemming for hver måned i terminen.
    // Samles til ett funn for alle kontoene (under løkka).
    const ub = mnd.at(-1)?.ub;
    if (!k.bankfeed) {
      // Bare måneder bankavstemmingen selv regner som åpne (ikke lukket, og avstemming, bevegelse eller saldo ≠ 0).
      const mangler = mnd.filter((m) => !m.lukket && m.aapen);
      if (mangler.length) {
        const bevegelse = mangler.some((m) => Math.abs(m.bev) >= 0.005);
        manuell.push({ konto: k.nummer, bevegelse, tekst: `${k.nummer} (${mangler.map((m) => m.maaned.slice(5)).join('+')}, ${bevegelse ? `bevegelse ${kr(mangler.reduce((s, m) => s + m.bev, 0))}` : 'statisk'}, saldo ${kr(ub)})` });
      } else if (aarlig && mnd.length) {
        funn.push(lagFunn({ kontroll: 'BK7', alvor: 'INFO', nivaa: 'konto', konto: k.nummer, tittel: `Manuell bankavstemming er lukket for ${k.nummer} i terminen` }));
      }
    }
    if (String(k.nummer).startsWith('19') && ub !== undefined && ub < -0.5) {
      funn.push(lagFunn({ kontroll: 'BK20', alvor: 'FORKLAR', nivaa: 'konto', konto: k.nummer, belop: ub, tittel: `Negativ banksaldo på ${k.nummer}`, detalj: `${kr(ub)} kr per ${t.sisteDag}.` }));
    }
  }
  // BK7 (kontroller.md) – konto uten bankintegrasjon uten lukket manuell avstemming i terminen.
  // Med bevegelse kan transaksjoner mangle i regnskapet (BLOKK). Statisk saldo må bare dokumenteres (FORKLAR).
  for (const [bev, alvor, tekst] of [[true, 'BLOKK', 'med bevegelse'], [false, 'FORKLAR', 'med statisk saldo']]) {
    const x = manuell.filter((m) => m.bevegelse === bev);
    if (!x.length) continue;
    funn.push(lagFunn({ kontroll: 'BK7', alvor, nivaa: 'klient', konto: x.map((m) => m.konto).join(','),
      tittel: `Manuell bankavstemming mangler for ${x.length} konto(er) uten bankintegrasjon ${tekst}`, detalj: `${x.map((m) => m.tekst).join('; ')}.`,
      handling: 'Hent kontoutskriftene, avstem manuelt i Tripletex og lukk månedene. Kontoutskriftene legges som vedlegg på kontoene i balanseavstemmingen.' }));
  }
  const dekket = new Set(manuell.map((m) => String(m.konto)));
  // Bankavstemmingens egen vurdering for året hittil – bare i årlig kjøring (bankavstemming-skillen dekker den løpende).
  const utenDekket = (liste) => (liste ?? []).filter((s) => !dekket.has(String(s).match(/^\d+/)?.[0] ?? ''));
  const v = aarlig ? { kunde: utenDekket(d.bank.vurdering?.kunde), intern: utenDekket(d.bank.vurdering?.intern) } : {};
  if (v.kunde?.length) {
    funn.push(lagFunn({ kontroll: 'BK21', alvor: 'FORKLAR', nivaa: 'klient', konto: v.kunde.join('|'), tittel: 'Bank hittil i år: dette må hentes fra kunden', detalj: v.kunde.join('; '),
      handling: 'Send kundeforespørselen fra bankavstemmingen (npm run bankavstemming -- --excel).' }));
  }
  if (v.intern?.length) {
    funn.push(lagFunn({ kontroll: 'BK22', alvor: 'FORKLAR', nivaa: 'klient', konto: v.intern.join('|'), tittel: 'Bank hittil i år: internt arbeid i bankavstemmingen', detalj: v.intern.join('; '),
      handling: 'Match og lukk månedene i bankavstemmingen (etter ja), eller dokumenter statiske saldoer.' }));
  }
  for (const f of d.bank.feil ?? []) funn.push(lagFunn({ kontroll: 'BK0', alvor: 'INFO', nivaa: 'klient', tittel: 'Feil i bankuttrekket', detalj: String(f).slice(0, 200) }));
  return funn;
}
