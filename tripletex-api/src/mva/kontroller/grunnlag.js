// Forutsetninger og bilag som gjelder alle klienter: ubehandlet i Tripletex (F1), dubletter (MD1) og
// leverandørbilag uten dokumentasjon. Ingen fritekst i funnene – bilagsnummer, konto og beløp.

import { lagFunn, kr } from '../felles.js';

const normFaktura = (s) => String(s ?? '').toUpperCase().replace(/[^A-Z0-9]/g, '').replace(/^0+/, '');

export function grunnlag(d, { t }) {
  const funn = [];
  const levById = new Map(d.leverandorer.map((l) => [l.id, l]));
  const levNavn = (id) => levById.get(id)?.navn ?? '[leverandør]';

  // F1 – ubehandlet: ikke bokførte bilag og dokumenter i innboksen. /ledger/voucher/>nonPosted gir ikke alt:
  // leverandørfakturaer som er registrert men ikke bokført (bilagsnummer 0) tas med fra /supplierInvoice.
  const ikkeBokfortLf = (d.leverandorfakturaer ?? []).filter((f) => f.voucher?.id && !(Number(f.voucher.number) > 0))
    .map((f) => ({ id: f.voucher.id, tempNumber: f.voucher.tempNumber, date: f.invoiceDate, vendorInvoiceNumber: f.invoiceNumber,
      postings: [{ account: { number: 2400 }, amountGross: -Math.abs(f.amount ?? 0), supplier: f.supplier }] }));
  const ikkeBokfort = [...new Map([...(d.ikkeBokfort ?? []), ...ikkeBokfortLf].map((v) => [v.id, v])).values()];
  if (ikkeBokfort.length) {
    const iTerminen = ikkeBokfort.filter((v) => v.date >= t.start && v.date < t.D);
    const sum = ikkeBokfort.reduce((s, v) => s + (v.postings ?? []).filter((p) => p.account?.number >= 2400 && p.account?.number <= 2499).reduce((a, p) => a - (p.amountGross ?? 0), 0), 0);
    funn.push(lagFunn({ kontroll: 'F1.3', alvor: iTerminen.length ? 'FORKLAR' : 'INFO', nivaa: 'klient', belop: sum,
      bilag: ikkeBokfort.map((v) => `T${v.tempNumber ?? v.id}`),
      tittel: `${ikkeBokfort.length} bilag er ikke bokført (${iTerminen.length} med dato i terminen)`,
      detalj: `Leverandørgjeld i bilagene: ${kr(sum)} kr. Bilag som ikke er bokført, ser ingen av posteringskontrollene.`,
      handling: 'Bokfør, avvis eller slett i Tripletex. Sjekk dublettfunnene under først.' }));
  }
  if (d.innboks?.antall > 0) {
    funn.push(lagFunn({ kontroll: 'F1.1', alvor: 'FORKLAR', nivaa: 'klient', tittel: `${d.innboks.antall} dokumenter ligger i innboksen`,
      handling: 'Behandle innboksen før terminen avsluttes.' }));
  }

  // MD1 – samme leverandør og fakturanummer mer enn én gang (bokført mot bokført, eller ikke bokført mot bokført).
  // Leverandøren identifiseres via leverandørindeksen (org.nr.), ikke bare Tripletex-id: samme leverandør kan
  // ligge som to poster (f.eks. én med skrivefeil og uten org.nr.), og piloten fant en purring på den andre posten.
  const levNokkel = (id, orgnr) => levById.get(id)?.nokkel ?? (String(orgnr ?? '').replace(/\D/g, '').length === 9 ? `NO:${String(orgnr).replace(/\D/g, '')}` : `id:${id}`);
  const kandidater = [];
  for (const f of d.leverandorfakturaer) {
    if (!f.voucher?.id || !normFaktura(f.invoiceNumber)) continue;
    const bokfort = Number(f.voucher.number) > 0;
    kandidater.push({ lev: levNokkel(f.supplier?.id, f.supplier?.organizationNumber), levId: f.supplier?.id, faktura: normFaktura(f.invoiceNumber), bokfort,
      bilag: bokfort ? String(f.voucher.number) : `ikke bokført (T${f.voucher.tempNumber ?? f.voucher.id})`, belop: Math.abs(f.amount ?? 0), kreditnota: !!f.isCreditNote });
  }
  for (const v of ikkeBokfort) {
    const levId = (v.postings ?? []).find((p) => p.supplier?.id)?.supplier?.id;
    if (!levId || !normFaktura(v.vendorInvoiceNumber)) continue;
    const belop = Math.abs((v.postings ?? []).filter((p) => p.account?.number >= 2400 && p.account?.number <= 2499).reduce((s, p) => s + (p.amountGross ?? 0), 0));
    kandidater.push({ lev: levNokkel(levId), levId, faktura: normFaktura(v.vendorInvoiceNumber), bokfort: false, bilag: `ikke bokført (T${v.tempNumber ?? v.id})`, belop, kreditnota: false });
  }
  const grupper = new Map();
  for (const k of kandidater) {
    const n = `${k.lev}|${k.faktura}|${k.kreditnota}`;
    grupper.set(n, [...(grupper.get(n) ?? []), k]);
  }
  for (const g of grupper.values()) {
    const unike = [...new Map(g.map((k) => [k.bilag, k])).values()];
    if (unike.length < 2) continue;
    const bokforte = unike.filter((k) => k.bokfort);
    const beggeBokfort = bokforte.length >= 2;
    funn.push(lagFunn({
      kontroll: 'MD1', alvor: beggeBokfort ? 'BLOKK' : 'FORKLAR', bilag: unike.map((k) => k.bilag), belop: unike[0].belop, trengerSkjonn: !beggeBokfort,
      tittel: beggeBokfort ? `Samme faktura bokført ${bokforte.length} ganger (${levNavn(unike[0].levId)})` : `Ikke bokført bilag har samme fakturanummer som et bokført bilag (${levNavn(unike[0].levId)})`,
      detalj: `Bilag ${unike.map((k) => `${k.bilag} (${kr(k.belop)} kr)`).join(', ')}.${beggeBokfort ? '' : ' Ofte en purring eller kopi som ikke skal bokføres – den gir dobbel kostnad.'}`,
      handling: beggeBokfort ? 'Tilbakefør dubletten etter ja.' : 'Kontroller dokumentet. Er det en purring eller kopi: avvis det i Tripletex i stedet for å bokføre.',
      hjemmel: 'bokf.f. § 5-5-1',
    }));
  }

  // MD1 – dokumenter i innboksen med samme selger og fakturanummer som et bokført bilag (purring, kopi),
  // eller som Tripletex selv har merket som dublett.
  const bokfortePaaOrgnr = new Map();
  for (const f of d.leverandorfakturaer) {
    const org = String(f.supplier?.organizationNumber ?? '').replace(/\D/g, '');
    if (f.voucher?.id && org && normFaktura(f.invoiceNumber)) bokfortePaaOrgnr.set(`${org}|${normFaktura(f.invoiceNumber)}`, f);
  }
  for (const x of d.innboks?.elementer ?? []) {
    const org = String(x.vatNumber ?? '').replace(/\D/g, '').slice(-9);
    const treff = org && normFaktura(x.invoiceNumber) ? bokfortePaaOrgnr.get(`${org}|${normFaktura(x.invoiceNumber)}`) : null;
    if (!treff && !x.duplicateVoucherNumberAsString) continue;
    const mot = treff ? String(treff.voucher.number ?? treff.voucher.id) : x.duplicateVoucherNumberAsString;
    funn.push(lagFunn({
      kontroll: 'MD1', alvor: 'FORKLAR', bilag: [`innboks ${x.id}`, mot], belop: x.invoiceAmount ?? null, trengerSkjonn: true, hjemmel: 'bokf.f. § 5-5-1',
      tittel: `Dokument i innboksen ser ut som en dublett av bilag ${mot}${x.supplierName ? ` (${x.supplierName})` : ''}`,
      detalj: `Mottatt ${x.receivedDate ?? '?'}, fakturadato ${x.invoiceDate ?? '?'}, ${kr(x.invoiceAmount)} kr.${treff ? ' Samme selger og fakturanummer som bokført faktura.' : ' Tripletex har selv merket det som dublett.'} Ofte en purring eller kopi – bokføres den, blir kostnaden dobbel.`,
      handling: 'Kontroller dokumentet. Er det en purring eller kopi: avvis det i innboksen (renter og gebyr føres når de betales).',
    }));
  }

  // Leverandørbilag i terminen uten vedlegg eller EHF.
  const perBilag = new Map();
  for (const p of d.posteringer) {
    const x = perBilag.get(p.voucher?.id) ?? { lev: 0, kost: false, bank: false };
    const n = p.account.number;
    if (n >= 2400 && n <= 2499) x.lev += p.amount;
    if ((n >= 4000 && n <= 7999) || (n >= 1100 && n <= 1499)) x.kost = true;
    if (n >= 1900 && n <= 1999) x.bank = true;
    perBilag.set(p.voucher?.id, x);
  }
  const levBilag = new Set([...perBilag].filter(([, x]) => x.lev < -0.5 && x.kost && !x.bank).map(([id]) => id));
  const uten = d.bilag.filter((v) => levBilag.has(v.id) && !v.reverseVoucher?.id && !v.attachment?.id && !v.ediDocument?.id && v.date >= t.start);
  if (uten.length) {
    funn.push(lagFunn({ kontroll: 'F1.6', alvor: 'FORKLAR', nivaa: 'klient', bilag: uten.map((v) => String(v.number)),
      tittel: `${uten.length} leverandørbilag uten vedlegg`,
      detalj: `Bilag ${uten.slice(0, 20).map((v) => v.number).join(', ')}${uten.length > 20 ? ' …' : ''}. Uten salgsdokument er det ikke dokumentasjon for kostnaden (bokf.f. § 5-5-1).`,
      handling: 'Be kunden om fakturaene, eller legg ved fra innboksen.' }));
  }
  return funn;
}
