// EHF mot bokføringen (maskinelt, erstatter agentlesing av EHF-bilag):
//   EH1 faktura stilet til annen kjøper   EH2 bokført beløp ≠ EHF   EH3 kreditnota uten henvisning (formmerknad)
//   For registrerte klienter også: EH4 fradrag ≠ mva på EHF (MS2), EH5 fradrag fra leverandør uten mva-registrering (MF5),
//   EH6 mva på EHF uten fradrag hos registrert selger (tapt fradrag, MK6).

import { lagFunn, kr } from '../felles.js';

const FRADRAG = new Set(['1', '11', '13']);

export function ehfKontroll(d, { oppsett }) {
  const ehf = d.ehf ?? {};
  if (!Object.keys(ehf).length) return [];
  const funn = [];
  const registrert = oppsett.modus === 'REGISTRERT';
  const klientOrg = String(oppsett.klient.orgnr ?? '').replace(/\D/g, '');
  const nr = new Map(d.bilag.map((v) => [String(v.id), String(v.number || (v.tempNumber ? `T${v.tempNumber}` : v.id))]));
  const levById = new Map(d.leverandorer.map((l) => [l.id, l]));
  const perBilag = new Map();
  for (const p of d.posteringer) {
    const id = String(p.voucher?.id ?? '');
    const x = perBilag.get(id) ?? { lev: 0, fradrag: 0, levId: null };
    if (p.account.number >= 2400 && p.account.number <= 2499) { x.lev += p.amount; x.levId = p.supplier?.id ?? x.levId; }
    if (FRADRAG.has(String(p.vatType?.number ?? '0'))) x.fradrag += (p.amountGross ?? p.amount) - p.amount;
    perBilag.set(id, x);
  }

  const feilKjoper = [], belopsavvik = [], utenRef = [], fradragsavvik = [], ikkeReg = [], tapt = [];
  for (const [vid, e] of Object.entries(ehf)) {
    if (e.feil) continue;
    const b = nr.get(vid) ?? vid;
    const post = perBilag.get(vid);
    if (klientOrg && e.kjoperOrgnr && e.kjoperOrgnr !== klientOrg) feilKjoper.push(b);
    if (post && post.lev !== 0 && Number.isFinite(e.aBetale) && Math.abs(Math.abs(post.lev) - Math.abs(e.aBetale)) >= 1) {
      belopsavvik.push(`${b} (bokført ${kr(Math.abs(post.lev))}, EHF ${kr(e.aBetale)})`);
    }
    if (e.type === 'kreditnota' && !e.referanse) utenRef.push(b);
    if (!registrert || !post) continue;
    const l = levById.get(post.levId);
    if (Math.abs(Math.abs(post.fradrag) - Math.abs(e.mva)) >= 1 && Math.abs(post.fradrag) >= 1) fradragsavvik.push(`${b} (fradrag ${kr(post.fradrag)}, EHF ${kr(e.mva)})`);
    if (Math.abs(post.fradrag) >= 1 && l?.mvaRegistrert === false) ikkeReg.push(`${b} (${kr(post.fradrag)})`);
    if (Math.abs(post.fradrag) < 1 && Math.abs(e.mva) >= 1 && l?.mvaRegistrert === true) tapt.push(`${b} (${kr(e.mva)})`);
  }
  const liste = (xs) => `${xs.slice(0, 12).join(', ')}${xs.length > 12 ? ` … (${xs.length})` : ''}`;
  if (feilKjoper.length) funn.push(lagFunn({ kontroll: 'EH1', alvor: 'FORKLAR', bilag: feilKjoper, nivaa: 'klient', hjemmel: 'bokf.f. § 5-1-1',
    tittel: `${feilKjoper.length} EHF-er er stilet til en annen kjøper`, detalj: `Bilag ${liste(feilKjoper)}.`, handling: 'Kostnaden tilhører trolig et annet selskap – be om ny faktura eller flytt kostnaden.' }));
  if (belopsavvik.length) funn.push(lagFunn({ kontroll: 'EH2', alvor: 'FORKLAR', bilag: belopsavvik.map((x) => x.split(' ')[0]), nivaa: 'klient',
    tittel: `${belopsavvik.length} bilag der bokført beløp avviker fra EHF`, detalj: `${liste(belopsavvik)}.`, handling: 'Kontroller og rett bokføringen.' }));
  if (utenRef.length) funn.push(lagFunn({ kontroll: 'EH3', alvor: 'INFO', bilag: utenRef, nivaa: 'klient', hjemmel: 'bokf.f. § 5-2-7',
    tittel: `${utenRef.length} kreditnotaer uten henvisning til original`, detalj: `Bilag ${liste(utenRef)}. Formmerknad uten mva-effekt.` }));
  if (fradragsavvik.length) funn.push(lagFunn({ kontroll: 'EH4', alvor: 'BLOKK', bilag: fradragsavvik.map((x) => x.split(' ')[0]), nivaa: 'klient', hjemmel: 'mval. § 11-4',
    tittel: `${fradragsavvik.length} bilag der fradraget ikke stemmer med mva på EHF`, detalj: `${liste(fradragsavvik)}.`, handling: 'Rett koden eller beløpet før innsending.' }));
  if (ikkeReg.length) funn.push(lagFunn({ kontroll: 'EH5', alvor: 'BLOKK', bilag: ikkeReg.map((x) => x.split(' ')[0]), nivaa: 'klient', hjemmel: 'mval. §§ 8-1, 11-4',
    tittel: `${ikkeReg.length} bilag med fradrag fra leverandør som ikke er mva-registrert`, detalj: `${liste(ikkeReg)}.`, handling: 'Fjern fradraget (kode 0).' }));
  if (tapt.length) funn.push(lagFunn({ kontroll: 'EH6', alvor: 'FORKLAR', bilag: tapt.map((x) => x.split(' ')[0]), nivaa: 'klient', hjemmel: 'mval. § 8-1',
    tittel: `${tapt.length} bilag med mva på EHF, men uten fradrag`, detalj: `${liste(tapt)}.`, handling: 'Tapt fradrag hvis kjøpet er til avgiftspliktig bruk – vurder kode 1/11/13.' }));
  return funn;
}
