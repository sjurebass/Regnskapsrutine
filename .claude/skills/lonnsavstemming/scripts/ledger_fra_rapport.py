"""Bygger ledger.json fra en ferdig lønnsavstemming.

    python ledger_fra_rapport.py <ferdig rapport.xlsx> <ut.json>

Brukes til å verifisere generatoren mot en rapport du allerede har godkjent:
hent regnskapssiden ut av den gamle rapporten, kjør generatoren på nytt, og
sammenlign med sammenlign.py. Da vet du at en endring i skriptene ikke har
ødelagt noe.
"""

import json, re, sys, io
from pathlib import Path
import openpyxl

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "silfer-rapport" / "scripts"))
from silfer.filer import os_sti  # noqa: E402  (stier over 260 tegn i Claudes scratch)

sys.stdout.reconfigure(encoding="utf-8")
sti, ut = os_sti(sys.argv[1]), os_sti(sys.argv[2])
wb = openpyxl.load_workbook(sti, data_only=True)

d = {}

# --- overskrift
und = wb["Avstemming"]["D3"].value or ""
deler = [x.strip() for x in und.split("|") if x.strip()]
d["selskap"] = deler[0] if deler else ""
m = re.search(r"Org\.nr\.\s*(\d+)", und)
d["orgnr"] = m.group(1) if m else ""
m = re.search(r"Termin\s*(\d+)", und)
termin = int(m.group(1)) if m else 1
d["periode"] = {"termin": termin}

# --- kilder (sats + tripletex-id)
det = wb["Detaljer"]
for rad in det.iter_rows(min_col=1, max_col=1):
    v = str(rad[0].value or "")
    m = re.search(r"AGA-sats\s*([\d.,]+)\s*%.*feriepengesats\s*([\d.,]+)\s*%", v)
    if m:
        d["aga_sats"] = float(m.group(1).replace(",", "."))
        d["feriepenger_sats"] = float(m.group(2).replace(",", ".")) / 100
    m = re.search(r"selskaps-id\s*(\d+)", v)
    if m:
        d["tripletex_id"] = m.group(1)
    if v.startswith("A07:"):
        d["kilde_a07"] = v
    if v.startswith("Regnskap:"):
        d["kilde_regnskap"] = v

# --- forfall + KID fra «Til betaling»
av = wb["Avstemming"]
for rad in av.iter_rows(min_col=1, max_col=2):
    a = str(rad[0].value or "")
    b = str(rad[1].value or "")
    if a.startswith("Arbeidsgiveravgift termin") and "Forfall" in b:
        m = re.search(r"Forfall\s*(\d{2})\.(\d{2})\.(\d{4})", b)
        if m:
            d["periode"]["forfall"] = f"{m.group(3)}-{m.group(2)}-{m.group(1)}"

# --- saldoer
bal = []
i_saldo = False
for rad in det.iter_rows():
    a = str(rad[0].value or "")
    if a.startswith("Saldoer"):
        i_saldo = True
        continue
    if i_saldo and (a.startswith("Reverserte") or a.startswith("Kilder")):
        break
    if i_saldo and re.fullmatch(r"\d{4}", a):
        bal.append({"a": int(a), "n": rad[1].value or "",
                    "ib": rad[5].value or 0, "ch": rad[6].value or 0,
                    "ub": rad[7].value or 0})
d["balanser"] = bal

# --- pensjonshistorikk fra AGA-arket
hist = []
aga = wb["Arbeidsgiveravgift"]
i_hist = False
MND = ["januar","februar","mars","april","mai","juni","juli","august",
       "september","oktober","november","desember"]
for rad in aga.iter_rows():
    a = str(rad[0].value or "")
    if a.startswith("Pensjon hittil i år") or a.startswith("Pensjon hele året"):
        i_hist = True
        continue
    if i_hist and a.startswith("Sum hittil"):
        break
    if i_hist and any(a.lower().startswith(n) for n in MND):
        navn, aar = a.split()
        mnd = MND.index(navn.lower()) + 1
        hist.append([f"{aar}-{mnd:02d}", "", rad[1].value or 0, "", rad[2].value or 0])
d["pensjon_historikk"] = hist
# noen klienter bruker «hele året» i stedet for «hittil i år»
for rad in av.iter_rows(min_col=1, max_col=1):
    v = str(rad[0].value or "")
    if v.startswith("Grunnlag pensjon ") and "termin" not in v:
        d["pensjon_etikett"] = v.replace("Grunnlag pensjon ", "")

# --- posteringer
poster = []
# Gammel layout har tabellhodet i rad 1, ny har topp med logo og hodet i rad 7: les bare rader med dato.
for rad in wb["Posteringer"].iter_rows(min_row=2, values_only=True):
    if not rad or not re.match(r"\d{4}-\d{2}-\d{2}", str(rad[0] or "")):
        continue
    poster.append([str(rad[0]), str(rad[1]), int(rad[2]), rad[3] or "", rad[4] or "",
                   float(rad[5] or 0)])
# reverserte bilag ligger i eget avsnitt i Detaljer, ikke i Posteringer-arket
i_rev = False
for rad in det.iter_rows(values_only=True):
    a = str(rad[0] or "")
    if a.startswith("Reverserte bilag"):
        i_rev = True
        continue
    if i_rev and (a.startswith("Kilder") or a.startswith("A07:")):
        break
    if i_rev and a and a != "Dato" and a != "Ingen":
        poster.append([str(a), str(rad[1]), int(rad[2]), "", rad[3] or "", float(rad[4] or 0)])

d["posteringer"] = poster

# kontomapping for ytelser leses av «Ytelser A07» (f.eks. EK på 5390).
# Gammel layout (før Tally-A07): Måned · Ytelse · Fordel · AGA · Konto i kolonne A–E.
# Ny layout: Ytelse (fordel) · AGA-pliktig · Konto i kolonne A–C; sumrader har ikke konto.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from a07 import YTELSE_KONTO  # noqa: E402

VISNING = {
    "fastlønn": "fastloenn", "timelønn": "timeloenn",
    "fri telefon (ek)": "elektroniskKommunikasjon",
    "elektronisk kommunikasjon": "elektroniskKommunikasjon",
    "feriepenger": "feriepenger", "bonus": "bonus", "bil": "bil",
    "sykepenger": "sykepenger", "overtid": "overtidsgodtgjoerelse",
}
VISNING.update({k.lower(): k for k in YTELSE_KONTO})
ytelse_konto = {}
if "Ytelser A07" in wb.sheetnames:
    ark = wb["Ytelser A07"]
    gammel = str(ark["A7"].value or "").strip() == "Måned"
    kol_ytelse, kol_konto = (1, 4) if gammel else (0, 2)
    for rad in ark.iter_rows(min_row=8, values_only=True):
        if len(rad) > kol_konto and rad[kol_ytelse] and rad[kol_konto]:
            navn = str(rad[kol_ytelse]).strip().lower()
            kode = VISNING.get(navn) or VISNING.get(re.sub(r"\s*\(.*\)$", "", navn))
            if kode and str(rad[kol_konto]).strip().isdigit():
                ytelse_konto[kode] = int(rad[kol_konto])
d["ytelse_konto"] = ytelse_konto

# merknader
merknader = []
i_merk = False
for rad in av.iter_rows(values_only=True):
    a = str(rad[0] or "")
    if a == "Merknader":
        i_merk = True
        continue
    if i_merk and a and rad[1]:
        merknader.append(str(rad[1]))
d["merknader"] = merknader

io.open(ut, "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=1))
print(f"{ut}: {len(bal)} saldoer, {len(poster)} posteringer, {len(hist)} pensjonsmåneder, "
      f"sats {d.get('aga_sats')} / ferie {d.get('feriepenger_sats')}")
