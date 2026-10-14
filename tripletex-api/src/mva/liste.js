// S5/S6: kjente avvik, port, bilagsutvalg til agenten (overlevering.json), dokumentasjonsplan og beslutningsliste 1.
// Ingen fritekst fra Tripletex i lista – bare tekst vi lager selv, bilagsnummer, konto, beløp og firmanavn.

import { kr, lagNoekkel, normAlvor } from './felles.js';
import { redactText } from '../privacy.js';

const REKKEFOLGE = { STOPP: 0, BLOKK: 1, 'SPØR_REGNSKAPSFØRER': 2, FORKLAR: 3, INFO: 4 };

// Bilagsvurderingsagentens konklusjoner (bilagsvurdering.md seksjon 4) → alvor i beslutningslista.
const KONKLUSJON = {
  feil_kode: ['BLOKK', 'Feil mva-kode'], avskaaret_fradrag: ['BLOKK', 'Fradrag uten fradragsrett'], feil_termin: ['BLOKK', 'Feil termin'],
  omvendt_avgiftsplikt_mangler: ['BLOKK', 'Omvendt avgiftsplikt mangler'], maa_avklares: ['SPØR_REGNSKAPSFØRER', 'Må avklares'],
  manglende_dokumentasjon: ['FORKLAR', 'Mangler dokumentasjon'], ikke_salgsdokument: ['FORKLAR', 'Ikke et salgsdokument'], tapt_fradrag: ['FORKLAR', 'Tapt fradrag'],
};

/**
 * Gjør vurdering.json fra bilagsvurderingsagentene om til funn. Bilag som allerede har et deterministisk funn
 * (f.eks. MD1), får agentens vurdering lagt til der i stedet for et nytt funn. Teksten er skrevet av agenten
 * uten personopplysninger, men kjøres likevel gjennom redactText().
 */
export function fraVurdering(vurdering, funn) {
  funn = funn.map((f) => ({ ...f, alvor: normAlvor(f.alvor) }));
  if (!vurdering?.vurderinger?.length) return { funn, sammendrag: null };
  const ut = funn.map((f) => ({ ...f }));
  const formmerknader = [];
  for (const v of vurdering.vurderinger) {
    const bilag = v.bokfort === false || !v.bilagsnr || String(v.bilagsnr).startsWith('0') ? `T${v.temp_nr ?? v.voucher_id}` : String(v.bilagsnr).split('-')[0];
    if (v.konklusjon === 'ok') continue;
    if (v.konklusjon === 'ok_formmerknad') { formmerknader.push(`${bilag}: ${redactText(v.vurdering ?? '')}`); continue; }
    const [alvor, tekst] = KONKLUSJON[v.konklusjon] ?? ['SPØR_REGNSKAPSFØRER', v.konklusjon];
    // Eksakt treff på bilagsnummeret som eget ord («T87» skal ikke treffe «T874»).
    const erSammeBilag = (b) => String(b) === bilag || String(b).split(/[^0-9A-Za-z]+/).includes(bilag);
    const eksisterende = ut.find((f) => f.bilag.some(erSammeBilag));
    if (eksisterende) {
      eksisterende.detalj = `${eksisterende.detalj} Bilagsvurdering: ${redactText(v.vurdering ?? '')}`.trim();
      // Er agentens konklusjon ikke strengere enn funnet, holder det med teksten. Ellers blir den et eget funn under.
      if (REKKEFOLGE[alvor] >= REKKEFOLGE[eksisterende.alvor]) continue;
    }
    ut.push({
      kontroll: 'BV', alvor, tittel: `${tekst}: bilag ${bilag}${v.leverandor ? ` (${v.leverandor})` : ''}`,
      detalj: `${redactText(v.vurdering ?? '')}${v.sikkerhet ? ` Sikkerhet: ${v.sikkerhet}.` : ''}`, belop: v.anbefalt_korreksjon?.mva_belop_endring ?? v.belop_brutto ?? null,
      konto: v.konto ?? null, bilag: [bilag], nivaa: 'bilag', trengerSkjonn: !!(v.trenger_regnskapsforer ?? Object.entries(v).find(([k]) => k.startsWith('trenger_'))?.[1]), hjemmel: v.hjemmel ?? null, regel: (v.regel_treff ?? []).join(', ') || null,
      handling: v.anbefalt_korreksjon?.tekst ? redactText(v.anbefalt_korreksjon.tekst) : null, noekkel: lagNoekkel(v.kjent_avvik_nokkel ?? `BV|${bilag}|${v.konklusjon}`), noekkelTekst: v.kjent_avvik_nokkel ?? `BV|${bilag}|${v.konklusjon}`, data: null,
    });
  }
  if (formmerknader.length) {
    ut.push({ kontroll: 'BV', alvor: 'INFO', tittel: `${formmerknader.length} bilag med formmerknad (ingen mva-effekt)`, detalj: formmerknader.join(' | '),
      belop: null, konto: null, bilag: [], nivaa: 'klient', trengerSkjonn: false, hjemmel: null, regel: null, handling: 'Be leverandøren rette neste gang.', noekkel: lagNoekkel('BV|formmerknad'), noekkelTekst: 'BV|formmerknad', data: null });
  }
  const s = vurdering.sammendrag ?? {};
  for (const x of s.til_andre_agenter ?? []) {
    ut.push({ kontroll: 'BV', alvor: 'FORKLAR', tittel: `Funnet under bilagsvurderingen (${x.agent ?? 'annet'}): bilag ${x.bilagsnr ?? '?'}`, detalj: redactText(x.funn ?? ''),
      belop: null, konto: null, bilag: [String(x.bilagsnr ?? '')], nivaa: 'bilag', trengerSkjonn: false, hjemmel: null, regel: null, handling: null, noekkel: lagNoekkel(`BV|annet|${x.bilagsnr}`), noekkelTekst: `BV|annet|${x.bilagsnr}`, data: null });
  }
  return { funn: ut, sammendrag: s };
}

/** Demper funn som står i kjente-avvik.md (samme nøkkel, altså samme beløp). */
export function dempKjente(funn, kjente) {
  return funn.map((f) => ({ ...f, alvor: normAlvor(f.alvor) })).map((f) => (kjente.has(f.noekkel) && f.alvor !== 'STOPP' ? { ...f, dempet: kjente.get(f.noekkel) } : f));
}

export function port(funn) {
  const aktive = funn.filter((f) => !f.dempet);
  if (aktive.some((f) => f.alvor === 'STOPP')) return 'RØD';
  if (aktive.some((f) => f.alvor === 'BLOKK' || f.alvor === 'SPØR_REGNSKAPSFØRER')) return 'GUL';
  return 'GRØNN';
}

// Kontoer der fradragsretten ofte er avskåret eller delt (fradragsregler-kort.md): personal/velferd, bil,
// representasjon, gaver og kontingenter. Bare relevant for registrerte klienter.
const SKJONNSKONTOER = [[5900, 5999], [7000, 7199], [7320, 7399], [7400, 7499]];
const FRADRAGSKODER = new Set(['1', '11', '13']);

/**
 * Unntakslista til bilagsvurdering (S4): bare bilag som reglene ikke kan avgjøre maskinelt, sortert etter
 * mva-effekt og kappet (standard 10). Koder, EHF, dubletter og dokumentasjon er allerede kontrollert i skriptet.
 * Klienter som ikke er registrert har ingen fradrag, så lista er normalt tom eller svært kort.
 */
export function tilVurdering(d, funn, { modus, maks = 10 }) {
  const bilagById = new Map(d.bilag.map((v) => [v.id, v]));
  const nr = (id) => { const v = bilagById.get(id); return String(v?.number || (v?.tempNumber ? `T${v.tempNumber}` : id)); };
  const levById = new Map(d.leverandorer.map((l) => [l.id, l]));
  const kand = new Map();
  const leggTil = (bilag, grunn, { voucherId = null, mvaEffekt = 0, belop = null, levId = null } = {}) => {
    const k = kand.get(bilag) ?? { bilag, voucherId, grunner: [], mvaEffekt: 0, belop, levId };
    if (!k.grunner.includes(grunn)) k.grunner.push(grunn);
    k.mvaEffekt = Math.max(k.mvaEffekt, Math.abs(mvaEffekt));
    k.voucherId ??= voucherId; k.levId ??= levId; k.belop ??= belop;
    kand.set(bilag, k);
  };
  // 1) Funn på bilagsnivå som krever skjønn (alle moduser), unntatt dempede.
  for (const f of funn) {
    if (!f.trengerSkjonn || f.dempet || f.nivaa !== 'bilag') continue;
    for (const b of f.bilag) leggTil(b, `${f.kontroll}: ${f.tittel}`, { belop: f.belop });
  }
  // 2) Registrerte: fradrag på skjønnskontoer, og fradrag fra utenlandske/ukjente leverandører uten vurdering i indeksen.
  if (modus === 'REGISTRERT') {
    const perBilag = new Map();
    for (const p of d.posteringer) {
      const id = p.voucher?.id;
      const x = perBilag.get(id) ?? { fradrag: 0, skjonn: false, levId: null };
      const fr = FRADRAGSKODER.has(String(p.vatType?.number ?? '0')) ? (p.amountGross ?? p.amount) - p.amount : 0;
      x.fradrag += fr;
      if (fr && SKJONNSKONTOER.some(([a, b]) => p.account.number >= a && p.account.number <= b)) x.skjonn = true;
      if (p.supplier?.id) x.levId = p.supplier.id;
      perBilag.set(id, x);
    }
    for (const [id, x] of perBilag) {
      if (Math.abs(x.fradrag) < 1) continue;
      const l = levById.get(x.levId);
      if (x.skjonn) leggTil(nr(id), 'fradrag på konto der fradraget ofte er avskåret (§§ 8-3/8-4)', { voucherId: id, mvaEffekt: x.fradrag, levId: x.levId });
      if (l && (l.nokkel?.startsWith('UT:') || l.nokkel?.startsWith('?:')) && !l.vurdering) leggTil(nr(id), 'fradrag fra utenlandsk eller ukjent leverandør uten vurdering', { voucherId: id, mvaEffekt: x.fradrag, levId: x.levId });
    }
  }
  const alle = [...kand.values()].sort((a, b) => b.mvaEffekt - a.mvaEffekt || Math.abs(b.belop ?? 0) - Math.abs(a.belop ?? 0));
  const valgt = alle.slice(0, maks).map((k) => {
    const v = k.voucherId ? bilagById.get(k.voucherId) : null;
    const l = k.levId ? levById.get(k.levId) : null;
    return { ...k, harVedlegg: v ? !!v.attachment?.id : null, harEHF: v ? !!v.ediDocument?.id : null,
      leverandor: l ? { navn: l.navn, orgnr: l.orgnr, mvaRegistrert: l.mvaRegistrert, vurdering: l.vurdering } : null };
  });
  return { modus, maks, antallKandidater: alle.length, utelatt: Math.max(0, alle.length - maks), bilag: valgt };
}

/**
 * Dokumentasjonsplan: hva som skal lagres som vedlegg og kommentarer i avstemmingsmodulen (prinsipp:
 * «så mye dokumentasjon som mulig»). Opplasting er skrivende og skjer bare etter ja.
 */
export function dokumentasjonsplan(d, funn, { t, modus }) {
  const plan = [];
  const mnd = t.maaneder;
  const leggTil = (avstemming, linje, dokument, kilde, status) => plan.push({ avstemming, linje, dokument, kilde, status });
  for (const m of mnd) {
    leggTil(`BALANCE ${m}`, '1500', `Åpne poster kundereskontro per ${t.sisteDag}`, 'openPost + kundekart', 'lages av flyten');
    leggTil(`BALANCE ${m}`, '2400', `Åpne poster leverandørreskontro per ${t.sisteDag}`, 'openPost + leverandørindeks', 'lages av flyten');
    for (const k of d.bank?.kontoer ?? []) leggTil(`BALANCE ${m}`, String(k.nummer), `Bankavstemming ${k.nummer} ${m}`, 'PUT /bank/reconciliation/internal/export/pdf (Tripletex)', 'må testes (skrivende verb, genererer eksport)');
    leggTil(`BALANCE ${m}`, '2500/2600/2770', `Skattekonto – krav og betalinger per ${t.sisteDag}`, '/claimsAndPayments', d.skattekonto?.krav?.length ? 'lages av flyten' : 'ikke tilgjengelig');
  }
  if (modus === 'REGISTRERT') {
    leggTil(`VAT termin ${t.termin}`, 'hele terminen', 'Kvittering for innsendt mva-melding', 'vatReturns.receiptId → /document/{id}/content', 'blokkert: 403 for API-brukeren (24.09.2026)');
    leggTil(`VAT termin ${t.termin}`, 'hele terminen', 'Mva-meldingen (XML)', '/vatReturns/{id}/xml', 'blokkert: 403 for API-brukeren (24.09.2026)');
    leggTil(`BALANCE ${mnd.at(-1)}`, '2740', `Kvittering mva-melding termin ${t.termin}`, 'som over', 'blokkert: 403');
    leggTil(`ANNUAL_BALANCE ${t.aar}`, '2740', `Kvitteringer for alle årets mva-meldinger`, 'som over, alle terminer', 'blokkert: 403');
  }
  for (const f of funn.filter((x) => !x.dempet && ['BLOKK', 'FORKLAR'].includes(x.alvor) && x.konto)) {
    leggTil(`BALANCE ${mnd.at(-1)}`, String(f.konto), `Kommentar: ${f.tittel}`, `funn ${f.kontroll}`, 'kommentartekst lages etter regnskapsførerens beslutning');
  }
  return plan;
}

/** Beslutningsliste 1 (markdown): kort, med det som må gjøres først. Detaljene ligger i funn.json. */
export function beslutningsliste({ oppsett, t, funn, portStatus, utv, plan, manifest, bilagsvurdering = null }) {
  const aktive = funn.filter((f) => !f.dempet).sort((a, b) => REKKEFOLGE[a.alvor] - REKKEFOLGE[b.alvor] || Math.abs(b.belop ?? 0) - Math.abs(a.belop ?? 0));
  const dempet = funn.filter((f) => f.dempet);
  const teller = (...a) => aktive.filter((f) => a.includes(f.alvor)).length;
  const kort = (s, n) => (s && s.length > n ? `${s.slice(0, n - 1)}…` : s ?? '');
  const belop = (f) => (f.belop !== null && f.belop !== undefined ? ` – ${kr(f.belop)} kr` : '');
  const L = [];
  L.push(`# Mva termin ${t.termin} ${t.aar} – ${oppsett.klient.navn} (${oppsett.modus.toLowerCase()})`, '');
  L.push(`${t.start} – ${t.sisteDag} · port **${portStatus}** · ${teller('STOPP', 'BLOKK')} må rettes · ${teller('SPØR_REGNSKAPSFØRER')} spørsmål · ${teller('FORKLAR')} følg opp · data ${manifest.tid.slice(0, 16).replace('T', ' ')}${dempet.length ? ` · ${dempet.length} kjent(e) avvik dempet` : ''}`, '');
  const hoved = aktive.filter((f) => ['STOPP', 'BLOKK', 'SPØR_REGNSKAPSFØRER'].includes(f.alvor));
  if (hoved.length) {
    L.push('## Må rettes eller avklares', '');
    hoved.forEach((f, i) => {
      L.push(`${i + 1}. **${f.tittel}**${belop(f)} · \`${f.noekkel}\``);
      L.push(`   ${kort(f.detalj, 260)}${f.handling ? ` → ${kort(f.handling, 200)}` : ''}`);
    });
    L.push('');
  }
  const folgOpp = aktive.filter((f) => f.alvor === 'FORKLAR');
  if (folgOpp.length) {
    L.push('## Følg opp', '');
    for (const f of folgOpp) L.push(`- **${f.tittel}**${belop(f)} · \`${f.noekkel}\` – ${kort(f.detalj, 180)}`);
    L.push('');
  }
  const info = aktive.filter((f) => f.alvor === 'INFO');
  if (info.length) {
    L.push('## Info', '');
    for (const f of info.slice(0, 6)) L.push(`- ${f.tittel}${belop(f)}`);
    if (info.length > 6) L.push(`- … ${info.length - 6} til i funn.json`);
    L.push('');
  }
  L.push('## Bilagsvurdering', '');
  if (bilagsvurdering?.lest) {
    const f = bilagsvurdering.funn ?? {};
    L.push(`Vurdert ${bilagsvurdering.lest.bilag ?? '?'} bilag: ${f.ok ?? 0} ok, ${(f.feil_kode ?? 0) + (f.avskaaret_fradrag ?? 0) + (f.feil_termin ?? 0) + (f.omvendt_avgiftsplikt_mangler ?? 0)} avvik, ${(f.manglende_dokumentasjon ?? 0) + (f.ikke_salgsdokument ?? 0)} dokumentasjon, ${f.maa_avklares ?? 0} må avklares.`, '');
  } else if (utv.bilag.length) {
    L.push(`${utv.bilag.length} bilag på unntakslista (maks ${utv.maks}${utv.utelatt ? `, ${utv.utelatt} utelatt` : ''}): ${utv.bilag.map((b) => b.bilag).join(', ')}.`, '');
  } else L.push('Ingen – alt er avgjort maskinelt (koder, EHF, dubletter, dokumentasjon).', '');
  const blokkert = plan.filter((p) => /403|blokkert/.test(p.status)).length;
  L.push('## Dokumentasjon i avstemmingsmodulen', '', `${plan.filter((p) => !p.dokument.startsWith('Kommentar')).length} vedlegg og ${plan.filter((p) => p.dokument.startsWith('Kommentar')).length} kommentarer planlagt etter ja (dokumentasjon.json)${blokkert ? `, ${blokkert} blokkert av 403` : ''}.`, '');
  if (dempet.length) {
    L.push('## Kjente avvik (dempet)', '');
    for (const f of dempet) L.push(`- ${f.tittel} – ${kort(f.dempet.forklaring, 140)}`);
    L.push('');
  }
  return L.join('\n');
}
