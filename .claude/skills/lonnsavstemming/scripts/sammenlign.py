"""Sammenligner en generert rapport mot en godkjent, ark for ark.

    python sammenlign.py <fasit.xlsx> <ny.xlsx>

Merk: formelceller i den nye filen har ingen bufret verdi før Excel eller
recalc har vært innom, så avvikskolonner kan se ut til å mangle. Se på
radetikettene og de faste tallene.
"""

import sys, openpyxl

sys.stdout.reconfigure(encoding="utf-8")
fasit_sti, ny_sti = sys.argv[1], sys.argv[2]
f = openpyxl.load_workbook(fasit_sti, data_only=True)
n = openpyxl.load_workbook(ny_sti, data_only=True)

print("ark fasit:", f.sheetnames)
print("ark ny   :", n.sheetnames)


def rader(ws):
    """Rader som (kolonne A-tekst, [tallverdier])."""
    ut = []
    for r in ws.iter_rows():
        verdier = [c.value for c in r]
        if not any(v is not None for v in verdier):
            continue
        etikett = str(verdier[0]) if verdier[0] is not None else ""
        tall = [round(v, 2) for v in verdier if isinstance(v, (int, float))]
        tekster = [str(v) for v in verdier[1:] if isinstance(v, str)]
        ut.append((etikett, tall, tekster))
    return ut


for ark in f.sheetnames:
    if ark not in n.sheetnames:
        print(f"\n### {ark}: MANGLER i ny")
        continue
    a, b = rader(f[ark]), rader(n[ark])
    print(f"\n### {ark}: fasit {len(a)} rader, ny {len(b)} rader")
    etiketter_a = [x[0] for x in a]
    etiketter_b = [x[0] for x in b]
    mangler = [e for e in etiketter_a if e and e not in etiketter_b]
    ekstra = [e for e in etiketter_b if e and e not in etiketter_a]
    if mangler:
        print("  RADER SOM MANGLER :", mangler[:8])
    if ekstra:
        print("  RADER SOM ER NYE  :", ekstra[:8])
    # sammenlign tall på rader med lik etikett
    kart_b = {x[0]: x for x in b}
    avvik = 0
    for etikett, tall, _ in a:
        if not etikett or etikett not in kart_b:
            continue
        tall_b = kart_b[etikett][1]
        if tall and tall_b and tall != tall_b:
            felles = min(len(tall), len(tall_b))
            if tall[:felles] != tall_b[:felles]:
                avvik += 1
                if avvik <= 6:
                    print(f"  TALL  «{etikett[:46]}»")
                    print(f"        fasit {tall[:6]}")
                    print(f"        ny    {tall_b[:6]}")
    if not avvik and not mangler and not ekstra:
        print("  ✓ identisk på radetiketter og tall")
    elif not avvik:
        print("  ✓ tallene stemmer på alle felles rader")
