# -*- coding: utf-8 -*-
"""Regenera la pestana Categorias del mes en curso (const CATS_OCT) en index.html.

- Categorias = price_total por linea agrupado por palabras clave del nombre del producto.
- Calcula el mes pedido (por defecto el mes actual en America/Caracas).
- Reemplaza la linea `const CATS_OCT = [...];` (sin tocar el resto).
- Guarda copia en pipeline/categorias_YYYY-MM.json.

SOLO LECTURA en Odoo.

Uso:
  python update_categorias.py            -> mes actual
  python update_categorias.py 2026 10    -> octubre 2026
"""
import io, re, json, sys, argparse, os
from datetime import datetime, timedelta, timezone
sys.path.insert(0, r"C:\Users\yarleyc\Desktop\crmlatinbien")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_categorias as BC

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HTML = os.path.join(REPO, "index.html")
TZ = timezone(timedelta(hours=-4))

def clean(data):
    return [{"categoria": c["categoria"], "cantidad": c["cantidad"],
             "monto": c["monto"], "productos": c["productos"]} for c in data]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int, nargs="?")
    ap.add_argument("month", type=int, nargs="?")
    a = ap.parse_args()
    now = datetime.now(TZ)
    year, month = a.year or now.year, a.month or now.month

    data = clean(BC.build(year, month))
    json.dump(data, io.open(os.path.join(REPO, "pipeline", f"categorias_{year:04d}-{month:02d}.json"),
              "w", encoding="utf-8", newline="\n"), ensure_ascii=False)

    s = io.open(HTML, encoding="utf-8", newline="").read()
    new_line = "const CATS_OCT = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n"
    if not re.search(r"^const CATS_OCT = .*?;\s*$", s, re.M):
        raise SystemExit("No se encontro la linea 'const CATS_OCT = ...;' en index.html")
    s = re.sub(r"^const CATS_OCT = .*?;\s*$", new_line, s, count=1, flags=re.M)
    io.open(HTML, "w", encoding="utf-8", newline="").write(s)

    total = sum(c["monto"] for c in data)
    print(f"CATS_OCT -> {year}-{month:02d}: filas={len(data)} total={round(total,2)}")

if __name__ == "__main__":
    main()
