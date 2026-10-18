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
import io, re, json, sys, argparse
from datetime import datetime, timedelta, timezone
sys.path.insert(0, r"C:\Users\yarleyc\Desktop\crmlatinbien")
sys.path.insert(0, __import__("os").path.dirname(__import__("os").path.abspath(__file__)))
import build_mes as B

REPO = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb"
HTML = REPO + r"\index.html"
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
    json.dump(data, io.open(f"{REPO}\\pipeline\\mes_{year:04d}-{month:02d}.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    new_line = "const MES = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    s = io.open(HTML, encoding="utf-8").read()
    if re.search(r"^const MES = .*?;\n", s, re.M):
        s = re.sub(r"^const MES = .*?;\n", new_line, s, count=1, flags=re.M)
    else:
        s = s.replace("// ===== TAB SWITCH =====", new_line + "// ===== TAB SWITCH =====", 1)
    io.open(HTML, "w", encoding="utf-8").write(s)
    print(f"MES -> {year}-{month:02d}: facturas={data['total_facturas']} facturado={data['total_facturado']} "
          f"admin={data['total_admin']} costo={data['total_costo']}")

if __name__ == "__main__":
    main()
