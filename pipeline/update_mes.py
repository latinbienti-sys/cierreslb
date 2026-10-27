# -*- coding: utf-8 -*-
"""Regenera la pestana dinamica 'Mes en curso' desde Odoo.

- Calcula el mes (por defecto el mes actual en America/Caracas, o el que se pase).
- Genera la estructura con build_mes.build_month.
- Reemplaza la linea `const MES = {...};` en index.html (sin tocar el resto).
- Guarda copia en pipeline/mes_YYYY-MM.json.

Uso:
  python update_mes.py            -> mes actual
  python update_mes.py 2026 10    -> octubre 2026
"""
import io, os, re, json, sys, argparse
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_mes as B

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
HTML = os.path.join(REPO, "index.html")
TZ = timezone(timedelta(hours=-4))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int, nargs="?")
    ap.add_argument("month", type=int, nargs="?")
    a = ap.parse_args()
    now = datetime.now(TZ)
    year = a.year or now.year
    month = a.month or now.month
    oc = B.connect()
    data = B.build_month(oc, year, month)
    json.dump(data, io.open(os.path.join(REPO, "pipeline", f"mes_{year:04d}-{month:02d}.json"),
                            "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    new_json = "const MES = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"
    s = io.open(HTML, encoding="utf-8", newline="").read()
    m = re.search(r"^const MES = .*?;\s*$", s, re.M)
    if m:
        s = s[:m.start()] + new_json + s[m.end():]
    else:
        s = s.replace("// ===== TAB SWITCH =====", new_json + "\n// ===== TAB SWITCH =====", 1)
    io.open(HTML, "w", encoding="utf-8", newline="").write(s)
    print(f"MES -> {year}-{month:02d}: facturas={data['total_facturas']} facturado={data['total_facturado']} "
          f"admin={data['total_admin']} costo={data['total_costo']}")

if __name__ == "__main__":
    main()
