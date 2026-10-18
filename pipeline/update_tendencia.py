# -*- coding: utf-8 -*-
"""Actualiza DATA.tendencia (Dash Facturacion) de forma robusta.

- Reconstruye el objeto DATA completo (colapsa claves 'tendencia' duplicadas
  que dejaba el pipeline anterior; solo debe quedar una).
- Agrega/actualiza el mes pedido (por defecto el mes actual) desde Odoo.
- Desliza la ventana a los ultimos N meses (default 5, segun el titulo).
- Recalcula delta / actual / anterior / mejor / acumulado.
- NO regenera meses existentes (respeta Ago/Sep tal cual).

Uso: python update_tendencia.py            -> mes actual
     python update_tendencia.py 2026 10    -> octubre 2026
"""
import io, re, json, sys, argparse, os
from datetime import datetime, timedelta, timezone
sys.path.insert(0, r"C:\Users\yarleyc\Desktop\crmlatinbien")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_mes as B

REPO = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb"
HTML = REPO + r"\index.html"
TZ = timezone(timedelta(hours=-4))
MES_ABBR = {1:"Ene",2:"Feb",3:"Mar",4:"Abr",5:"May",6:"Jun",7:"Jul",8:"Ago",9:"Sep",10:"Oct",11:"Nov",12:"Dic"}

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

def month_row(data):
    return {"key": data["mes"], "label": f"{MES_ABBR[int(data['mes'][5:7])]} {data['mes'][2:4]}",
            "facturado": data["total_facturado"], "facturas": data["total_facturas"],
            "clientes": data["total_clientes"], "costo": data["total_costo"],
            "admin": data["total_admin"], "margen": data["total_margen"], "delta": None}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int, nargs="?")
    ap.add_argument("month", type=int, nargs="?")
    ap.add_argument("--window", type=int, default=5)
    a = ap.parse_args()
    now = datetime.now(TZ)
    year, month = a.year or now.year, a.month or now.month

    s = io.open(HTML, encoding="utf-8").read()
    dm = re.search(r"const DATA =", s)
    dstart = s.index("{", dm.end())
    dend = find_obj(s, dstart)
    DATA = json.loads(s[dstart:dend])   # colapsa duplicados (last-wins)
    T = DATA["tendencia"]

    newrow = month_row(B.build_month(B.connect(), year, month))
    rows = [r for r in T["rows"] if r["key"] != newrow["key"]] + [newrow]
    rows.sort(key=lambda r: r["key"])
    rows = rows[-a.window:]
    for i, r in enumerate(rows):
        r["delta"] = None if i == 0 else round((r["facturado"] / rows[i-1]["facturado"] - 1) * 100, 1)
    T["rows"] = rows
    T["actual"] = dict(rows[-1])
    T["anterior"] = dict(rows[-2]) if len(rows) >= 2 else None
    T["mejor"] = dict(max(rows, key=lambda r: r["facturado"]))
    T["acumulado"] = {k: (sum(r[k] for r in rows) if k in ("facturas", "clientes")
                          else round(sum(r[k] for r in rows), 2))
                      for k in ("facturado", "facturas", "clientes", "costo", "admin", "margen")}

    new_txt = json.dumps(DATA, ensure_ascii=False, separators=(", ", ": "))
    s = s[:dstart] + new_txt + s[dend:]
    io.open(HTML, "w", encoding="utf-8").write(s)
    print(f"tendencia +{newrow['key']}: rows={[r['key'] for r in rows]} actual={T['actual']['label']} "
          f"delta={T['actual']['delta']} mejor={T['mejor']['label']} acum={T['acumulado']['facturado']} "
          f"| tendencia keys ahora=1")

if __name__ == "__main__":
    main()
