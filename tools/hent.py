"""Datauthenting fra Tripletex, med cache per klient og periode.

Alle kontroller leser fra Kontekst, aldri direkte fra API-et. Da hentes hvert
datasett én gang uansett hvor mange kontroller som bruker det.
"""

from __future__ import annotations

from datetime import date, timedelta


from .modeller import Periode
from .tripletex import Tripletex, TripletexFeil

# Feltspesifikasjoner. Første variant forsøkes først; faller tilbake til en
# enklere variant hvis Tripletex avviser den (feltnavn kan variere mellom
# API-versjoner).
FELT_KONTO = [
    "id,number,name,type,ledgerType,isBankAccount,isInactive,requireReconciliation,"
    "bankAccountNumber,isCloseable,vatType(id,number,percentage,name)",
    "id,number,name,type,ledgerType,isBankAccount,isInactive",
]
FELT_LEDGER = [
    "account(id,number,name,type,ledgerType,isBankAccount),sumAmount,openingBalance,closingBalance",
    "account(id,number,name),sumAmount,openingBalance,closingBalance",
]
FELT_POSTERING = [
    "id,date,description,amount,amountGross,type,systemGenerated,invoiceNumber,termOfPayment,row,"
    "account(id,number,name,ledgerType,isBankAccount),vatType(id,number,percentage,name),"
    "voucher(id,number,date,voucherType(id,name)),customer(id,name),supplier(id,name),"
    "employee(id,firstName,lastName),project(id,name,number),closeGroup(id)",
    "id,date,description,amount,account(id,number,name),vatType(id,number,percentage),"
    "voucher(id,number),customer(id,name),supplier(id,name)",
]
FELT_APEN_POST = [
    "account(id,number,name,ledgerType),postings(id,date,description,amount,invoiceNumber,"
    "termOfPayment,customer(id,name),supplier(id,name),voucher(id,number))",
    "account(id,number,name),postings(id,date,description,amount)",
]
FELT_BILAG = [
    "id,number,date,description,year,voucherType(id,name),document(id,fileName),"
    "attachment(id,fileName),vendorInvoiceNumber",
    "id,number,date,description,voucherType(id,name),document(id,fileName)",
    "id,number,date,description",
]
FELT_BANKAVSTEMMING = [
    "id,account(id,number,name),accountingPeriod(id,name,start,end),isClosed,"
    "bankAccountClosingBalanceCurrency,closedDate,"
    "transactions(id,postedDate,description,amountCurrency,matched,matchType)",
    "id,account(id,number,name),isClosed,bankAccountClosingBalanceCurrency",
]
FELT_BANKUTDRAG = [
    "id,fileName,fromDate,toDate,openingBalanceCurrency,closingBalanceCurrency,bank(id,name)",
    "id,fromDate,toDate,openingBalanceCurrency,closingBalanceCurrency",
]
FELT_LEVFAKTURA = [
    "id,invoiceNumber,invoiceDate,invoiceDueDate,amount,outstandingAmount,isCreditNote,"
    "supplier(id,name,organizationNumber),voucher(id,number)",
    "id,invoiceNumber,invoiceDate,invoiceDueDate,amount,supplier(id,name)",
]
FELT_PERIODE = ["id,name,number,start,end,isClosed", "id,name,start,end,isClosed"]
FELT_TIME = [
    "id,date,hours,chargeableHours,chargeable,invoice(id),locked,"
    "employee(id,firstName,lastName),project(id,name,number),activity(id,name)",
    "id,date,hours,chargeableHours,chargeable,employee(id,firstName,lastName)",
]
FELT_ANLEGG = [
    "id,name,dateOfAcquisition,acquisitionCost,status,lifetime,accumulatedDepreciation,"
    "depreciationRemainingValue,account(id,number,name),depreciationAccount(id,number,name)",
    "id,name,dateOfAcquisition,acquisitionCost,status",
]


class Kontekst:
    """Alt en kontroll trenger for én klient i én periode."""

    def __init__(self, api: Tripletex, klient, profil, periode: Periode):
        self.api = api
        self.klient = klient
        self.profil = profil
        self.periode = periode
        self._cache: dict = {}
        self.advarsler: list[str] = []

    # -- generisk ---------------------------------------------------------

    def _hent(self, nokkel, funksjon):
        if nokkel not in self._cache:
            self._cache[nokkel] = funksjon()
        return self._cache[nokkel]

    def _liste(self, sti: str, felt_varianter: list[str], **params) -> list[dict]:
        siste: Exception | None = None
        for felt in felt_varianter:
            try:
                return self.api.liste(sti, fields=felt, **params)
            except TripletexFeil as e:
                siste = e
                if "400" not in str(e):
                    raise
        self.advarsler.append(f"{sti}: {siste}")
        raise siste  # type: ignore[misc]

    # -- kontoplan og saldi ----------------------------------------------

    def kontoer(self) -> list[dict]:
        return self._hent("kontoer", lambda: self._liste("/ledger/account", FELT_KONTO))

    def konto_etter_nummer(self) -> dict[int, dict]:
        def bygg():
            ut = {}
            for k in self.kontoer():
                try:
                    ut[int(k["number"])] = k
                except (KeyError, TypeError, ValueError):
                    continue
            return ut

        return self._hent("konto_nr", bygg)

    def saldobalanse(self, fra: date, til: date) -> list[dict]:
        """LedgerAccount per konto: openingBalance, sumAmount, closingBalance."""
        nokkel = ("saldo", fra, til)
        return self._hent(
            nokkel,
            lambda: self._liste(
                "/ledger", FELT_LEDGER, dateFrom=fra.isoformat(), dateTo=til.isoformat()
            ),
        )

    def saldo_perioden(self) -> list[dict]:
        return self.saldobalanse(self.periode.fra, self.periode.til)

    def saldo_hittil(self) -> list[dict]:
        return self.saldobalanse(self.periode.aar_fra, self.periode.til)

    def saldo_forrige_maaned(self) -> list[dict]:
        f = self.periode.forrige()
        return self.saldobalanse(f.fra, f.til)

    def saldo_samme_maaned_ifjor(self) -> list[dict]:
        f = self.periode.forrige_aar()
        return self.saldobalanse(f.fra, f.til)

    def saldo_hittil_ifjor(self) -> list[dict]:
        f = self.periode.forrige_aar()
        return self.saldobalanse(f.aar_fra, f.til)

    # -- posteringer og bilag --------------------------------------------

    def posteringer(self, fra: date | None = None, til: date | None = None) -> list[dict]:
        fra = fra or self.periode.fra
        til = til or self.periode.til
        return self._hent(
            ("post", fra, til),
            lambda: self._liste(
                "/ledger/posting",
                FELT_POSTERING,
                dateFrom=fra.isoformat(),
                dateTo=til.isoformat(),
            ),
        )

    def posteringer_hittil(self) -> list[dict]:
        return self.posteringer(self.periode.aar_fra, self.periode.til)

    def apne_poster(self, dato: date | None = None) -> list[dict]:
        dato = dato or self.periode.til
        return self._hent(
            ("apne", dato),
            lambda: self._liste("/ledger/openPost", FELT_APEN_POST, date=dato.isoformat()),
        )

    def bilag(self, fra: date | None = None, til: date | None = None) -> list[dict]:
        fra = fra or self.periode.fra
        til = til or self.periode.til
        return self._hent(
            ("bilag", fra, til),
            lambda: self._liste(
                "/ledger/voucher", FELT_BILAG, dateFrom=fra.isoformat(), dateTo=til.isoformat()
            ),
        )

    def ikke_bokforte_bilag(self) -> list[dict]:
        def hent():
            return self._liste(
                "/ledger/voucher/>nonPosted",
                FELT_BILAG,
                includeNonApproved="true",
                dateFrom=(self.periode.til - timedelta(days=365)).isoformat(),
                dateTo=self.periode.til.isoformat(),
            )

        return self._hent("ikkebokfort", hent)

    def bilagsmottak(self) -> list[dict]:
        def hent():
            return self._liste(
                "/ledger/voucher/>voucherReception",
                FELT_BILAG,
                dateFrom=(self.periode.til - timedelta(days=365)).isoformat(),
                dateTo=self.periode.til.isoformat(),
            )

        return self._hent("bilagsmottak", hent)

    # -- perioder ---------------------------------------------------------

    def regnskapsperioder(self) -> list[dict]:
        def hent():
            return self._liste(
                "/ledger/accountingPeriod",
                FELT_PERIODE,
                startFrom=date(self.periode.aar - 1, 1, 1).isoformat(),
                startTo=self.periode.til.isoformat(),
            )

        return self._hent("perioder", hent)

    # -- bank -------------------------------------------------------------

    def bankavstemminger(self) -> list[dict]:
        def hent():
            ut = []
            for p in self.regnskapsperioder():
                start = (p.get("start") or "")[:10]
                if not start or not (
                    self.periode.aar_fra.isoformat() <= start <= self.periode.til.isoformat()
                ):
                    continue
                try:
                    ut.extend(
                        self._liste(
                            "/bank/reconciliation",
                            FELT_BANKAVSTEMMING,
                            accountingPeriodId=str(p["id"]),
                        )
                    )
                except TripletexFeil as e:
                    self.advarsler.append(f"bankavstemming periode {p.get('name')}: {e}")
            return ut

        return self._hent("bankavst", hent)

    def bankutdrag(self, konto_id: int) -> list[dict]:
        return self._hent(
            ("utdrag", konto_id),
            lambda: self._liste("/bank/statement", FELT_BANKUTDRAG, accountId=str(konto_id)),
        )

    # -- reskontro og mva -------------------------------------------------

    def leverandorfakturaer(self) -> list[dict]:
        def hent():
            return self._liste(
                "/supplierInvoice",
                FELT_LEVFAKTURA,
                invoiceDateFrom=(self.periode.aar_fra - timedelta(days=365)).isoformat(),
                invoiceDateTo=self.periode.til.isoformat(),
            )

        return self._hent("levfaktura", hent)

    def mva_status(self) -> list[dict]:
        """VatStatus for alle terminer hittil i året."""

        def hent():
            ut = []
            for termin in range(1, self.periode.termin + 1):
                try:
                    v = self.api.verdi(
                        "/vatReturns/status",
                        year=self.periode.aar,
                        term=termin,
                        fields="*",
                    )
                    if v:
                        v.setdefault("term", termin)
                        ut.append(v)
                except TripletexFeil as e:
                    self.advarsler.append(f"mva-status termin {termin}: {e}")
            return ut

        return self._hent("mvastatus", hent)

    def lonnsslipper(self) -> list[dict]:
        """Lønnsslipper hittil i år."""

        def hent():
            return self._liste(
                "/salary/payslip",
                [
                    "id,date,year,month,grossAmount,amount,vacationAllowanceAmount,"
                    "employee(id,firstName,lastName),voucher(id,number)",
                    "id,year,month,grossAmount,amount,vacationAllowanceAmount,"
                    "employee(id,firstName,lastName)",
                ],
                yearFrom=self.periode.aar,
                yearTo=self.periode.aar,
                monthFrom=1,
                monthTo=self.periode.maaned,
            )

        return self._hent("lonnsslipper", hent)

    def mva_typer(self) -> list[dict]:
        return self._hent(
            "mvatyper",
            lambda: self.api.liste(
                "/ledger/vatType", fields="id,number,name,percentage,deductionPercentage"
            ),
        )

    # -- bransje ----------------------------------------------------------

    def timeregistreringer(self) -> list[dict]:
        def hent():
            return self._liste(
                "/timesheet/entry",
                FELT_TIME,
                dateFrom=self.periode.aar_fra.isoformat(),
                dateTo=self.periode.til.isoformat(),
            )

        return self._hent("timer", hent)

    def varetellinger(self) -> list[dict]:
        return self._hent(
            "telling",
            lambda: self.api.liste(
                "/inventory/stocktaking",
                fields="id,number,date,isCompleted,warehouseValue,discrepancySum,inventory(id,name)",
            ),
        )

    def anleggsmidler(self) -> list[dict]:
        return self._hent("anlegg", lambda: self._liste("/asset", FELT_ANLEGG))


# -- småhjelpere som kontrollene bruker -----------------------------------


def saldo_map(ledger: list[dict]) -> dict[int, dict]:
    """LedgerAccount-liste -> {kontonummer: rad}."""
    ut = {}
    for rad in ledger:
        konto = rad.get("account") or {}
        try:
            ut[int(konto.get("number"))] = rad
        except (TypeError, ValueError):
            continue
    return ut


def ub(ledger_map: dict[int, dict], numre) -> float:
    """Utgående balanse for ett eller flere kontonumre."""
    if isinstance(numre, int):
        numre = [numre]
    return sum(float(ledger_map.get(n, {}).get("closingBalance") or 0) for n in numre)


def bevegelse(ledger_map: dict[int, dict], numre) -> float:
    if isinstance(numre, int):
        numre = [numre]
    return sum(float(ledger_map.get(n, {}).get("sumAmount") or 0) for n in numre)


def kontonavn(ledger_map: dict[int, dict], nummer: int) -> str:
    return ((ledger_map.get(nummer) or {}).get("account") or {}).get("name") or ""


def navn_av(obj: dict | None) -> str:
    if not obj:
        return ""
    if obj.get("name"):
        return obj["name"]
    fornavn = obj.get("firstName") or ""
    etternavn = obj.get("lastName") or ""
    return (fornavn + " " + etternavn).strip()
