// Reskontro (RK): sum åpne poster per D = saldo i hovedboken, pluss poster som tyder på feil.
// K0: openPost(date=D) er et historisk snitt og Σ amount = /balanceSheet UB med dateTo = D.

import { lagFunn, kr, leggTilDager } from '../felles.js';
import { iIntervall } from '../profil.js';

export function reskontro(d, { t, profil, aarlig = false }) {
  const funn = [];
  const kunder = new Map(d.kunder.map((k) => [k.id, k]));
  const lev = new Map(d.leverandorer.map((l) => [l.id, l]));
  let privatNr = 0;
  const privat = new Map();
  const navnKunde = (id) => {
    const k = kunder.get(id);
    if (k?.navn) return k.navn;
    if (!privat.has(id)) privat.set(id, `privatkunde ${++privatNr}`);
    return privat.get(id);
  };

  for (const [art, intervaller, poster, motpart, navn] of [
    ['kunde', profil.kontoKunde, d.aapnePoster.kunde, 'customer', navnKunde],
    ['leverandor', profil.kontoLeverandor, d.aapnePoster.leverandor, 'supplier', (id) => lev.get(id)?.navn ?? '[leverandør]'],
  ]) {
    const tekst = art === 'kunde' ? 'Kundereskontro' : 'Leverandørreskontro';
    const ub = d.saldo.filter((s) => iIntervall(s.account.number, intervaller)).reduce((s, x) => s + x.balanceOut, 0);
    const aapent = poster.reduce((s, p) => s + p.amount, 0);
    const diff = Math.round((aapent - ub) * 100) / 100;
    const kontoTekst = intervaller.map(([a, b]) => (a === b ? a : `${a}–${b}`)).join(', ');
    // RK1/RK2 – åpne poster mot hovedbok.
    if (Math.abs(diff) >= 1 || aarlig) funn.push(Math.abs(diff) >= 1
      ? lagFunn({ kontroll: art === 'kunde' ? 'RK1' : 'RK2', alvor: 'FORKLAR', nivaa: 'konto', konto: kontoTekst, belop: diff,
        tittel: `${tekst} stemmer ikke med hovedboken per ${t.sisteDag}`,
        detalj: `Åpne poster ${kr(aapent)} kr, saldo ${kr(ub)} kr, differanse ${kr(diff)} kr.`,
        handling: 'Finn posteringer på reskontrokontoen uten motpart, eller feil utligning.' })
      : lagFunn({ kontroll: art === 'kunde' ? 'RK1' : 'RK2', alvor: 'INFO', nivaa: 'konto', konto: kontoTekst, belop: ub,
        tittel: `${tekst} stemmer med hovedboken`, detalj: `${poster.length} åpne poster, saldo ${kr(ub)} kr per ${t.sisteDag}.` }));

    // Poster på reskontrokontoen uten motpart.
    const uten = poster.filter((p) => !p[motpart]?.id);
    if (uten.length) {
      const sum = uten.reduce((s, p) => s + p.amount, 0);
      funn.push(lagFunn({ kontroll: 'RK3', alvor: 'FORKLAR', konto: kontoTekst, belop: sum, bilag: [...new Set(uten.map((p) => String(p.voucher?.id ?? '')))].slice(0, 20),
        tittel: `${uten.length} åpne poster på ${tekst.toLowerCase()} uten ${art === 'kunde' ? 'kunde' : 'leverandør'}`,
        detalj: `Sum ${kr(sum)} kr. Slike poster blir ikke med i reskontrolistene.`, handling: 'Flytt til riktig motpart eller til en annen konto.' }));
    }

    // Resten er saldokvalitet (hører til årsoppgjøret/årlig gjennomgang), ikke mva-terminen.
    if (!aarlig) continue;

    // Motparter med «feil» fortegn: kunder i kredit (forskudd/for mye betalt), leverandører i debet (forskudd/dobbeltbetaling).
    const perMotpart = new Map();
    for (const p of poster) {
      const id = p[motpart]?.id;
      if (!id) continue;
      perMotpart.set(id, (perMotpart.get(id) ?? 0) + p.amount);
    }
    const feilFortegn = [...perMotpart].filter(([, s]) => (art === 'kunde' ? s < -profil.vesentlighet / 10 : s > profil.vesentlighet / 10));
    if (feilFortegn.length) {
      funn.push(lagFunn({ kontroll: art === 'kunde' ? 'RK4' : 'RK5', alvor: 'FORKLAR', konto: kontoTekst,
        belop: feilFortegn.reduce((s, [, x]) => s + x, 0),
        tittel: art === 'kunde' ? `${feilFortegn.length} kunder står i kredit` : `${feilFortegn.length} leverandører står i debet`,
        detalj: feilFortegn.sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 15).map(([id, s]) => `${navn(id)} ${kr(s)} kr`).join(', '),
        handling: art === 'kunde' ? 'Forskudd, for mye innbetalt eller manglende faktura – avklar og tilbakebetal eller motregn.' : 'Forskudd, dobbeltbetaling eller manglende faktura – avklar.' }));
    }

    // Gamle åpne poster (> 90 dager før D).
    const grense = leggTilDager(t.D, -90);
    const gamle = poster.filter((p) => p.date < grense);
    if (gamle.length) {
      const sum = gamle.reduce((s, p) => s + p.amount, 0);
      if (Math.abs(sum) < 1) {
        // Poster som går i null, er bare ikke utlignet – ikke utestående beløp.
        funn.push(lagFunn({ kontroll: art === 'kunde' ? 'RK7' : 'RK9', alvor: 'INFO', konto: kontoTekst, belop: 0,
          tittel: `${gamle.length} gamle åpne poster i ${tekst.toLowerCase()} går i null`, detalj: `Dato før ${grense}.`,
          handling: 'Kan utlignes (lukkes) i reskontroen, etter ja.' }));
        continue;
      }
      funn.push(lagFunn({ kontroll: art === 'kunde' ? 'RK7' : 'RK9', alvor: Math.abs(sum) >= profil.vesentlighet ? 'FORKLAR' : 'INFO', konto: kontoTekst, belop: sum,
        tittel: `${gamle.length} åpne poster eldre enn 90 dager i ${tekst.toLowerCase()}`, detalj: `Sum ${kr(sum)} kr (dato før ${grense}).`,
        handling: art === 'kunde' ? 'Vurder purring, inkasso eller tap (konstatert tap gir ikke mva-effekt hos klient uten registrering).' : 'Er fakturaene betalt fra en annen konto, eller er de omtvistet?' }));
    }
  }
  return funn;
}
