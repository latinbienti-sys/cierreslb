# -*- coding: utf-8 -*-
"""Regenera la facturacion del mes en curso de la pestana Cartera/Tecnologia (const TECNO_OCT).

- Calcula por tecnologia (categoria web raiz del producto de mayor monto) el mes pedido.
- Reemplaza la linea `const TECNO_OCT = {...};` en index.html (sin tocar el resto).
- NO modifica las columnas de cartera ni Flujo de Cuotas.
- Guarda copia en pipeline/tecnologia_YYYY-MM.json.

Uso:
  python update_tecnologia.py            -> mes actual (America/Caracas)
  python update_tecnologia.py 2026 10    -> octubre 2026
"""
import io, json, sys, argparse, os
from datetime import datetime, timedelta, timezone
sys.path.insert(0, r"C:\Users\yarleyc\Desktop\crmlatinbien")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_tecnologia as BT

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(REPO, "index.html")
TZ = timezone(timedelta(hours=-4))

def find_obj(t, start):
    i, depth, instr, esc = start, 0, False, False
    while i < len(t):
        c = t[i]
        if instr:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': instr = False
        else:
            if c == '"': instr = True
            elif c in "{[" : depth += 1
            elif c in "}]":
                depth -= 1
                if depth == 0: return i + 1
        i += 1
    return -1

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int, nargs="?")
    ap.add_argument("month", type=int, nargs="?")
    a = ap.parse_args()
    now = datetime.now(TZ)
    year, month = a.year or now.year, a.month or now.month

    oc = BT.connect()
    data = BT.build(oc, year, month)
    json.dump(data, io.open(os.path.join(REPO, "pipeline", f"tecnologia_{year:04d}-{month:02d}.json"),
                            "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    payload = {"por_tecnologia": data["por_tecnologia"], "totales": data["totales"]}

    s = io.open(HTML, encoding="utf-8", newline="").read()
    i = s.index("const TECNO_OCT =")
    b = s.index("{", i)
    e = find_obj(s, b)
    new_txt = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    s = s[:b] + new_txt + s[e:]
    io.open(HTML, "w", encoding="utf-8", newline="").write(s)
    t = data["totales"]
    print(f"TECNO_OCT -> {year}-{month:02d}: facturas={t['oct_facturas']} facturado={t['oct_facturado']} "
          f"admin={t['oct_admin']} costo={t['oct_costo']}")

if __name__ == "__main__":
    main()
