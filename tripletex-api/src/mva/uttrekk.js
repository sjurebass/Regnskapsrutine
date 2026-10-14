// S1 oppsett og S2 felles uttrekk: Tripletex leses én gang per klient og termin, og alt lagres i arbeidsmappa.
// Kontrollene leser bare filene. Kun lesende kall.

import { hentAlle, hentEn, forsok, leggTilMnd, leggTilDager } from './felles.js';
import { brregOrgnr, importer, kanVærePerson } from '../leverandor.js';
import { hentEhf } from './ehf.js';
import { hentKlient, vurder, slåSammen } from '../bankavstemming.js';

/** S1: registreringsstatus i Tripletex og Brreg, terminlengde → modus. */
export async function oppsett(b) {
  const vat = await hentEn(b, '/ledger/vatSettings', { fields: 'vatRegistrationStatus,hasVatInHighForeignServices,hasVatInLowForeignServices,hasVatInImport,hasVatInAndOutReverseDuty' });
  const terminer = await hentAlle(b, '/vatTermSizeSettings', { sorting: 'fromDate', fields: 'reportType,fromDate,termSize' });
  const orgnr = b.company.organizationNumber;
  const brreg = orgnr ? await forsok(() => brregOrgnr(orgnr)) : { ok: false, feil: 'org.nr. mangler i Tripletex' };
  const iBrreg = brreg.ok && brreg.data ? brreg.data.mva_registrert : null;
  const status = vat?.vatRegistrationStatus ?? null;
  let modus = 'UKLAR';
  if (status === 'VAT_NOT_REGISTERED' && iBrreg === false) modus = 'UREGISTRERT';
  else if (status === 'VAT_REGISTERED' && iBrreg === true) modus = 'REGISTRERT';
  return {
    klient: { id: b.company.id, navn: b.company.name, orgnr },
    mvaStatusTripletex: status,
    mvaRegistrertBrreg: iBrreg,
    mvaRegistrertFraBrreg: brreg.ok ? brreg.data?.mva_registrert_fra ?? null : null,
    naeringskode: brreg.ok ? brreg.data?.naeringskode ?? null : null,
    brregFeil: brreg.ok ? null : brreg.feil,
    vatFlagg: vat,
    terminlengder: terminer,
    modus,
  };
}

/** Gjeldende terminlengde for alminnelig næring på terminstart. */
export function gjeldendeTermSize(terminlengder, dato) {
  const rader = terminlengder.filter((t) => t.reportType === 'GENERAL_INDUSTRY' && t.fromDate <= dato);
  const s = rader.at(-1)?.termSize;
  return !s || s === 'NOT_REGISTERED' ? 'TWO_MONTHS' : s;
}

/** S2: alle datasett. `am` = arbeidsmappe, `t` = terminobjekt, `profil` fra profil.js. Returnerer manifest. */
export async function uttrekk(b, am, t, profil, logg = () => {}) {
  const manifest = { tid: new Date().toISOString(), datasett: {}, profil: { kunde: profil.kontoKunde, leverandor: profil.kontoLeverandor } };
  // Et avbrutt uttrekk skal ikke kunne gjenbrukes, og en vurdering av gamle data skal ikke flettes inn i nye.
  am.fjern('manifest.json');
  am.flytt('vurdering.json', `vurdering-${manifest.tid.slice(0, 19).replace(/:/g, '')}.json`);
  const klientId = b.company.organizationNumber || b.company.name; // org.nr. er entydig, navn kan treffe flere
  const lagre = (navn, data, info = {}) => {
    am.lagre(`${navn}.json`, data);
    manifest.datasett[navn] = { rader: Array.isArray(data) ? data.length : null, ...info };
  };
  const tolv = leggTilMnd(t.D, -12);

  logg('kontoplan og koder');
  lagre('kontoer', await hentAlle(b, '/ledger/account', { fields: 'id,number,name,isInactive,isBankAccount,vatType(number),vatLocked' }));
  lagre('vatTyper', await hentAlle(b, '/ledger/vatType', { shouldIncludeSpecificationTypes: true, fields: 'id,number,name,percentage,deductionPercentage' }));

  logg('posteringer i terminen');
  const post = await hentAlle(b, '/ledger/posting', {
    dateFrom: t.start, dateTo: t.D,
    fields: 'id,date,description,amount,amountGross,currency(code),row,systemGenerated,type,account(id,number),vatType(number),supplier(id),customer(id),project(id),voucher(id)',
  });
  lagre('posteringer', post, { fra: t.start, til: t.D });

  logg('leverandørposteringer siste 12 måneder');
  lagre('leverandorposteringer12', await hentAlle(b, '/ledger/posting', {
    dateFrom: tolv, dateTo: t.D, accountNumberFrom: 2400, accountNumberTo: 2499,
    fields: 'id,date,amount,currency(code),supplier(id),voucher(id)',
  }), { fra: tolv, til: t.D });

  logg('bilag');
  const bilagFelt = 'id,number,tempNumber,year,date,description,voucherType(name),vendorInvoiceNumber,reverseVoucher(id),attachment(id),ediDocument(id)';
  const bilag = await hentAlle(b, '/ledger/voucher', { dateFrom: t.start, dateTo: t.D, fields: bilagFelt });
  // Datofilteret gir bare bilag med bilagsdato i terminen. Periodiseringer og reverseringer med tidligere
  // bilagsdato har likevel posteringer her – hent dem på id (piloten manglet 10 slike).
  const kjente = new Set(bilag.map((v) => v.id));
  const mangler = [...new Set(post.map((p) => p.voucher?.id).filter((id) => id && !kjente.has(id)))];
  for (const id of mangler) {
    const r = await forsok(() => hentEn(b, `/ledger/voucher/${id}`, { fields: bilagFelt }));
    if (r.ok && r.data) bilag.push(r.data);
  }
  lagre('bilag', bilag, { hentetPaaId: mangler.length });
  lagre('ehf', await hentEhf(b, bilag, logg));

  logg('ikke bokførte bilag og innboks');
  const ikkeBokfort = await forsok(() => hentAlle(b, '/ledger/voucher/>nonPosted', {
    includeNonApproved: true, dateFrom: `${t.aar - 1}-01-01`, dateTo: leggTilDager(t.D, 62),
    fields: 'id,number,tempNumber,date,voucherType(name),vendorInvoiceNumber,attachment(id),ediDocument(id),postings(row,amountGross,account(number),supplier(id))',
  }));
  lagre('ikkeBokfort', ikkeBokfort.ok ? ikkeBokfort.data : [], ikkeBokfort.ok ? {} : { feil: ikkeBokfort.feil });
  const innboks = await forsok(() => b.request('/voucherInbox/inboxCount'));
  // Innboksen med fakturanummer, selgers org.nr. og Tripletex' egen dublettmerking (for purringer og kopier).
  const innboksListe = await forsok(() => hentAlle(b, '/voucherInbox/inboxFiltered', {
    fields: 'id,filterType,receivedDate,voucherId,invoiceNumber,invoiceDate,dueDate,supplierName,invoiceAmount,invoiceCurrency,vatNumber,vatAmount,duplicateVoucherNumberAsString,importFailureReason,isSpam',
  }));
  lagre('innboks', {
    antall: innboks.ok ? innboks.data?.value ?? innboks.data : null,
    elementer: innboksListe.ok ? innboksListe.data.map((x) => ({ ...x, supplierName: kanVærePerson(x.supplierName) ? null : x.supplierName })) : [],
    feil: [innboks, innboksListe].filter((r) => !r.ok).map((r) => r.feil).join('; ') || null,
  });

  logg('leverandørfakturaer');
  const lf = await forsok(() => hentAlle(b, '/supplierInvoice', {
    invoiceDateFrom: leggTilMnd(t.start, -6), invoiceDateTo: leggTilDager(t.D, 62),
    fields: 'id,invoiceNumber,invoiceDate,supplier(id,organizationNumber),voucher(id,number,tempNumber),amount,isCreditNote',
  }));
  lagre('leverandorfakturaer', lf.ok ? lf.data.filter((x) => x.amount !== 0 || x.voucher) : [], lf.ok ? {} : { feil: lf.feil });

  logg('saldobalanse');
  const saldoFelt = 'account(id,number,name),balanceIn,balanceChange,balanceOut';
  lagre('saldo', await hentAlle(b, '/balanceSheet', { dateFrom: t.start, dateTo: t.D, accountNumberFrom: 1000, accountNumberTo: 8999, fields: saldoFelt }));
  lagre('saldo12', await hentAlle(b, '/balanceSheet', { dateFrom: tolv, dateTo: t.D, accountNumberFrom: 1000, accountNumberTo: 8999, fields: saldoFelt }), { fra: tolv });

  logg('åpne poster i reskontro');
  const aapne = {};
  for (const [navn, intervaller] of [['kunde', profil.kontoKunde], ['leverandor', profil.kontoLeverandor]]) {
    aapne[navn] = [];
    for (const [fra, til] of intervaller) {
      aapne[navn].push(...await hentAlle(b, '/ledger/posting/openPost', {
        date: t.D, accountNumberFrom: fra, accountNumberTo: til, sorted: false,
        fields: 'id,date,amount,account(number),customer(id),supplier(id),voucher(id)',
      }));
    }
  }
  lagre('aapnePoster', aapne);

  logg('kunder og leverandører');
  const kundeIder = [...new Set([...aapne.kunde, ...post].map((p) => p.customer?.id).filter(Boolean))];
  const kunder = [];
  for (let i = 0; i < kundeIder.length; i += 100) {
    kunder.push(...await hentAlle(b, '/customer', { id: kundeIder.slice(i, i + 100).join(','), fields: 'id,name,organizationNumber,isPrivateIndividual' }));
  }
  // Navn på privatkunder og personlignende navn lagres ikke.
  lagre('kunder', kunder.map((k) => ({ id: k.id, orgnr: k.organizationNumber || null, privat: !!k.isPrivateIndividual,
    navn: k.isPrivateIndividual || kanVærePerson(k.name) ? null : k.name })));
  const lev = await importer(klientId, tolv, t.D);
  const leverandorer = lev.poster.map((p) => ({
    id: p.tripletexId, nokkel: p.rec?.nokkel ?? null, orgnr: p.rec?.orgnr ?? p.orgnrITripletex ?? null,
    navn: p.rec?.enk ? null : p.rec?.navn ?? (kanVærePerson(p.tripletexNavn) ? null : p.tripletexNavn),
    mvaRegistrert: p.rec?.mva_registrert ?? null, status: p.rec?.status ?? null, land: p.rec?.land ?? p.land ?? null,
    valuta: p.valuta ?? [], vurdering: p.rec?.vurdering ?? null, orgnrManglerITripletex: !!p.orgnrManglerITripletex, feil: p.feil ?? null,
  }));
  // Leverandører med åpne poster eldre enn 12 måneder er ikke med i importen – hent navnet direkte.
  const kjenteLev = new Set(leverandorer.map((l) => l.id));
  const manglerLev = [...new Set(aapne.leverandor.map((p) => p.supplier?.id).filter((id) => id && !kjenteLev.has(id)))];
  for (let i = 0; i < manglerLev.length; i += 100) {
    for (const s of await hentAlle(b, '/supplier', { id: manglerLev.slice(i, i + 100).join(','), fields: 'id,name,organizationNumber,isPrivateIndividual' })) {
      leverandorer.push({ id: s.id, nokkel: null, orgnr: s.organizationNumber || null, navn: s.isPrivateIndividual || kanVærePerson(s.name) ? null : s.name,
        mvaRegistrert: null, status: null, land: null, valuta: [], vurdering: null, orgnrManglerITripletex: false, feil: null, utenforImport: true });
    }
  }
  lagre('leverandorer', leverandorer);

  logg('bankavstemming');
  // Samme logikk som `npm run bankavstemming`, kalt direkte (ingen underprosess).
  let bankStatus;
  try {
    const til = t.maaneder.at(-1);
    const r = await hentKlient(b.company, { fra: `${t.aar}-01`, til });
    const v = vurder(r, til);
    bankStatus = { ...r, vurdering: { kunde: v.kunde, intern: slåSammen(v.intern) } };
  } catch (e) {
    bankStatus = { feil: e.message.split('\n')[0].slice(0, 200) };
  }
  lagre('bank', bankStatus);

  logg('skattekonto (krav og betalinger)');
  const krav = [];
  let kravFeil = null;
  for (const aar of [t.aar - 1, t.aar, t.aar + 1]) {
    const r = await forsok(() => hentAlle(b, '/claimsAndPayments', { year: aar, fields: 'claimIdentifier,claimType,claimGroup,amount,outstandingAmount,rent,dueDate,periodDescription,claimCreatedDate' }));
    if (r.ok) krav.push(...r.data); else if (aar <= t.aar) kravFeil = r.feil;
  }
  lagre('skattekonto', { krav: [...new Map(krav.map((c) => [`${c.claimIdentifier}|${c.claimType}`, c])).values()], feil: kravFeil });

  am.lagre('manifest.json', manifest);
  return manifest;
}
