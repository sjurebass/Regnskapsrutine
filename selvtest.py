"""Selvtest uten API-tilgang.

    uv run --system-certs python selvtest.py

Kjører hele katalogen mot et konstruert datasett der vi vet fasiten, og skriver
en rapport til status/. Brukes til å sjekke at kontrollene og rapporten virker
etter endringer – ikke som erstatning for en ekte kjøring.
"""

from __future__ import annotations

import os
import sys
import tempfile

from tools import rapport
from tools.hent import Kontekst
from tools.kontroller import KATALOG, kjor
from tools.modeller import GUL, INFO, ROD, Klient, Periode, Resultat
from tools.profil import Klientprofil

P = Periode(2026, 8)


def konto(nummer, navn, **ekstra):
    rad = {"id": nummer, "number": str(nummer), "name": navn, "isInactive": False}
    rad.update(ekstra)
    return rad


KONTOER = [
    konto(1099, "Observasjonskonto"),
    konto(1500, "Kundefordringer", ledgerType="CUSTOMER"),
    konto(1920, "Bankinnskudd drift", isBankAccount=True),
    konto(1921, "Skattetrekkskonto", isBankAccount=True),
    konto(2400, "Leverandørgjeld", ledgerType="SUPPLIER"),
    konto(2600, "Forskuddstrekk"),
    konto(2700, "Utgående mva", vatType={"id": 3, "number": "3", "percentage": 25}),
    konto(2710, "Inngående mva", vatType={"id": 1, "number": "1", "percentage": 25}),
    konto(2740, "Oppgjørskonto mva"),
    konto(2770, "Skyldig arbeidsgiveravgift"),
    konto(2910, "Mellomregning aksjonær"),
    konto(2930, "Skyldig lønn"),
    konto(2940, "Skyldige feriepenger"),
    konto(3000, "Salgsinntekt", vatType={"id": 3, "number": "3", "percentage": 25}),
    konto(6020, "Avskrivning driftsmidler"),
    konto(6300, "Leie lokaler", vatType={"id": 1, "number": "1", "percentage": 25}),
    konto(6560, "Datautstyr", vatType={"id": 1, "number": "1", "percentage": 25}),
    konto(7350, "Representasjon"),
    konto(1380, "Gammel fordring"),
]


def ledger(nummer, ib, bevegelse):
    k = next(k for k in KONTOER if int(k["number"]) == nummer)
    return {
        "account": k,
        "openingBalance": ib,
        "sumAmount": bevegelse,
        "closingBalance": ib + bevegelse,
    }


# Hittil i år: 1500 har 240 000 ute, åpne poster summerer til 235 000 -> R1 slår ut.
SALDO_HITTIL = [
    ledger(1099, 0, 4500),            # D2
    ledger(1500, 180000, 60000),
    ledger(1920, 300000, -205000),    # UB 95 000, banken sier 100 000 -> B2
    ledger(1921, 0, 0),               # B3: ingen avstemming
    ledger(2400, -150000, -30000),
    ledger(2600, 0, -101000),
    ledger(2700, 0, -420000),
    ledger(2710, 0, 180000),
    ledger(2740, 0, -12500),          # M2
    ledger(2770, 0, -96000),
    ledger(2910, -20000, 65000),      # UB +45 000 -> E1 lån til aksjonær
    ledger(2930, 0, -18000),          # L5
    ledger(2940, 0, -140000),
    ledger(3000, 0, -1680000),
    ledger(6020, 0, 0),               # A4: ingen avskrivning
    ledger(6300, 0, 210000),
    ledger(6560, 0, 62000),
    ledger(7350, 0, 9000),
    ledger(1380, 38000, 0),           # A5: sovende
]

SALDO_AUGUST = [
    ledger(3000, 0, -150000),
    ledger(6300, 0, 0),               # A3: husleie mangler
    ledger(6560, 0, 62000),           # A1/A2: hopp
    ledger(6020, 0, 0),
    ledger(1920, 0, -40000),
]
SALDO_JULI = [ledger(3000, 0, -195000), ledger(6300, 0, 30000), ledger(6560, 0, 3000)]
SALDO_AUGUST_IFJOR = [ledger(3000, 0, -160000), ledger(6300, 0, 28000), ledger(6560, 0, 2500)]
SALDO_HITTIL_IFJOR = [ledger(1380, 38000, 0), ledger(3000, 0, -1400000)]

# Mva per termin: termin 3 er bokført 59 500 mot melding 62 000 -> M1 slår ut.
SALDO_TERMIN = {
    1: [ledger(2700, 0, -100000), ledger(2710, 0, 40000)],
    2: [ledger(2700, 0, -98000), ledger(2710, 0, 40000)],
    3: [ledger(2700, 0, -95000), ledger(2710, 0, 35500)],
    4: [ledger(2700, 0, -70000), ledger(2710, 0, 30000)],
}


def postering(id_, dato, konto_nr, belop, tekst, **ekstra):
    k = next(k for k in KONTOER if int(k["number"]) == konto_nr)
    rad = {
        "id": id_,
        "date": dato,
        "description": tekst,
        "amount": belop,
        "amountGross": belop,
        "account": k,
        "voucher": {"id": 900 + id_, "number": 900 + id_, "date": dato},
    }
    rad.update(ekstra)
    return rad


MVA25 = {"id": 1, "number": "1", "percentage": 25, "name": "Inngående 25 %"}
SALGSMVA = {"id": 3, "number": "3", "percentage": 25, "name": "Utgående 25 %"}

POSTERINGER_AUG = [
    postering(1, "2026-08-05", 6560, 62000, "Bærbare maskiner", vatType=MVA25, amountGross=77500),
    postering(2, "2026-08-12", 7350, 9000, "Kundemiddag", vatType=MVA25, amountGross=11250),
    postering(3, "2026-08-20", 3000, -150000, "Salg august", vatType=SALGSMVA, amountGross=-187500),
    postering(4, "2026-08-31", 2910, 45000, "Uttak eier", voucher={"id": 951, "number": 951, "date": "2026-06-02"}),
    postering(5, "2026-08-31", 1099, 4500, "Uidentifisert innbetaling"),
    postering(6, "2026-08-15", 2600, -12500, "Forskuddstrekk august"),
    postering(7, "2026-08-15", 2770, -11800, "AGA august"),
]

POSTERINGER_HITTIL = POSTERINGER_AUG + [
    postering(10 + i, f"2026-{m:02d}-05", 6300, 30000, "Husleie", vatType=MVA25, amountGross=37500)
    for i, m in enumerate(range(1, 8))
] + [
    postering(30 + i, f"2026-{m:02d}-15", 2600, -12500, "Forskuddstrekk")
    for i, m in enumerate(range(1, 8))
] + [
    postering(50 + i, f"2026-{m:02d}-15", 2770, -11800, "AGA")
    for i, m in enumerate(range(1, 8))
]

APNE_POSTER = [
    {
        "account": KONTOER[1],  # 1500
        "postings": [
            {
                "id": 1,
                "date": "2026-02-01",
                "amount": 120000,
                "invoiceNumber": "1042",
                "termOfPayment": "2026-02-15",
                "customer": {"id": 1, "name": "Gammel Kunde AS"},
            },
            {
                "id": 2,
                "date": "2026-08-10",
                "amount": 130000,
                "invoiceNumber": "1099",
                "termOfPayment": "2026-09-09",
                "customer": {"id": 2, "name": "Ny Kunde AS"},
            },
            {
                "id": 3,
                "date": "2026-07-02",
                "amount": -15000,
                "invoiceNumber": "",
                "termOfPayment": "2026-07-02",
                "customer": {"id": 3, "name": "Forskudd Kunde AS"},
            },
        ],
    },
    {
        "account": KONTOER[4],  # 2400
        "postings": [
            {
                "id": 4,
                "date": "2026-06-01",
                "amount": -95000,
                "termOfPayment": "2026-06-30",
                "supplier": {"id": 10, "name": "Sen Leverandør AS"},
            },
            {
                "id": 5,
                "date": "2026-08-20",
                "amount": -85000,
                "termOfPayment": "2026-09-19",
                "supplier": {"id": 11, "name": "Vanlig Leverandør AS"},
            },
        ],
    },
]

BILAG = [
    {"id": 901, "number": 901, "date": "2026-08-05", "voucherType": {"name": "Inngående faktura"}, "document": {"id": 1}},
    {"id": 902, "number": 902, "date": "2026-08-12", "voucherType": {"name": "Inngående faktura"}},
    {"id": 903, "number": 903, "date": "2026-08-20", "voucherType": {"name": "Utgående faktura"}, "document": {"id": 2}},
    {"id": 951, "number": 951, "date": "2026-06-02", "voucherType": {"name": "Diverse bilag"}},
    {"id": 905, "number": 905, "date": "2026-08-31", "voucherType": {"name": "Bankbilag"}},
]

PERIODER = [
    {"id": 7, "name": "Juli 2026", "number": 7, "start": "2026-07-01", "end": "2026-07-31", "isClosed": False},
    {"id": 8, "name": "August 2026", "number": 8, "start": "2026-08-01", "end": "2026-08-31", "isClosed": False},
]

BANKAVSTEMMINGER = [
    {
        "id": 1,
        "account": KONTOER[2],  # 1920
        "accountingPeriod": PERIODER[1],
        "isClosed": True,
        "bankAccountClosingBalanceCurrency": 100000,
        "transactions": [
            {"id": 1, "postedDate": "2026-08-28", "description": "Innbetaling", "amountCurrency": 25000, "matched": True},
            {"id": 2, "postedDate": "2026-03-14", "description": "Ukjent innbetaling", "amountCurrency": 4500, "matched": False},
            {"id": 3, "postedDate": "2026-07-02", "description": "Gebyr", "amountCurrency": -350, "matched": False},
        ],
    }
]

LEVERANDORFAKTURAER = [
    {"id": 1, "invoiceNumber": "55123", "invoiceDate": "2026-08-04", "invoiceDueDate": "2026-09-03",
     "amount": 77500, "supplier": {"id": 10, "name": "Sen Leverandør AS"}, "voucher": {"number": 901}},
    {"id": 2, "invoiceNumber": "55123", "invoiceDate": "2026-08-19", "invoiceDueDate": "2026-09-18",
     "amount": 77500, "supplier": {"id": 10, "name": "Sen Leverandør AS"}, "voucher": {"number": 904}},
]

MVA_STATUS = [
    {"term": 1, "deliveryStatus": "DELIVERED", "paymentStatus": "PAID", "altinnPaymentAmount": 60000},
    {"term": 2, "deliveryStatus": "DELIVERED", "paymentStatus": "PAID", "altinnPaymentAmount": 58000},
    {"term": 3, "deliveryStatus": "DELIVERED", "paymentStatus": "UNPAID", "altinnPaymentAmount": 62000},
    {"term": 4, "deliveryStatus": "NOT_DELIVERED", "paymentStatus": "UNPAID", "altinnPaymentAmount": 0},
]

LONNSSLIPPER = [
    {"id": i, "year": 2026, "month": m, "grossAmount": 210000, "amount": 150000,
     "vacationAllowanceAmount": 21420, "employee": {"firstName": "Ansatt", "lastName": str(m)}}
    for i, m in enumerate(range(1, 8), start=1)
]


def bygg_kontekst() -> tuple[Kontekst, Klient]:
    klient = Klient(navn="Testklient AS", mappe=tempfile.mkdtemp(prefix="selvtest_"))
    profil = Klientprofil(navn=klient.navn, mva_pliktig=True, lonn=True, anleggsmidler=True)
    k = Kontekst(api=None, klient=klient, profil=profil, periode=P)
    forrige = P.forrige()
    ifjor = P.forrige_aar()
    k._cache.update(
        {
            "kontoer": KONTOER,
            ("saldo", P.aar_fra, P.til): SALDO_HITTIL,
            ("saldo", P.fra, P.til): SALDO_AUGUST,
            ("saldo", forrige.fra, forrige.til): SALDO_JULI,
            ("saldo", ifjor.fra, ifjor.til): SALDO_AUGUST_IFJOR,
            ("saldo", ifjor.aar_fra, ifjor.til): SALDO_HITTIL_IFJOR,
            # terminvise saldi for M1 (mva-konti 2700/2710/2740 per termin)
            **{
                ("saldo", Periode(2026, t * 2 - 1).fra, Periode(2026, t * 2).til): SALDO_TERMIN[t]
                for t in range(1, 5)
            },
            ("post", P.fra, P.til): POSTERINGER_AUG,
            ("post", P.aar_fra, P.til): POSTERINGER_HITTIL,
            ("apne", P.til): APNE_POSTER,
            ("bilag", P.fra, P.til): BILAG,
            "perioder": PERIODER,
            "bankavst": BANKAVSTEMMINGER,
            "levfaktura": LEVERANDORFAKTURAER,
            "mvastatus": MVA_STATUS,
            "lonnsslipper": LONNSSLIPPER,
            "ikkebokfort": [],
            "bilagsmottak": [{"id": 1, "number": 1, "date": "2026-05-01"}],
            "anlegg": [{"id": 1, "name": "Varebil", "status": "ACTIVE", "acquisitionCost": 350000}],
            "telling": [],
            "timer": [],
            "mvatyper": [],
        }
    )
    return k, klient


FORVENTET = {"B1", "B2", "B3", "D1", "D2", "D4", "E1", "L2", "M2", "M6", "R1", "R3", "R4", "R5", "R6"}


def main() -> int:
    kontekst, klient = bygg_kontekst()
    resultat = Resultat(klient=klient, periode=P)
    kjor(kontekst, resultat, None)

    print(f"Kjørte {len(resultat.kjorte)} kontroller av {len(KATALOG)} i katalogen")
    if resultat.hoppet_over:
        print("Hoppet over: " + ", ".join(f"{k} ({g})" for k, g in resultat.hoppet_over))
    if resultat.feil:
        print("\nFEIL:")
        for kid, melding in resultat.feil:
            print(f"  {kid}: {melding}")

    print(f"\n{len(resultat.funn)} funn:")
    for f in resultat.funn:
        belop = f"{f.belop:>12,.0f}".replace(",", " ") if f.belop is not None else " " * 12
        print(f"  {f.alvorlighet:<5} {f.kontroll:<3} {belop}  {f.tittel[:72]}")

    traff = {f.kontroll for f in resultat.funn}
    mangler = FORVENTET - traff
    print("\nKontroller som skulle gitt utslag på testdataene:")
    print(f"  traff:   {', '.join(sorted(FORVENTET & traff)) or '-'}")
    print(f"  mangler: {', '.join(sorted(mangler)) or '-'}")

    utmappe = klient.mappe  # midlertidig mappe, så ekte rapporter ikke overskrives
    sti = rapport.skriv_klientrapport(
        resultat,
        kontekst.saldo_perioden(),
        kontekst.saldo_hittil(),
        kontekst.advarsler,
        utmappe,
    )
    statussti = rapport.skriv_statusrapport([resultat], P, utmappe)
    print(f"\nSkrev {sti}\nSkrev {statussti}")
    return 1 if (resultat.feil or mangler) else 0


if __name__ == "__main__":
    sys.exit(main())
