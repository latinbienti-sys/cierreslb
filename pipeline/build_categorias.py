# -*- coding: utf-8 -*-
"""Categorias = price_total por linea agrupado por palabras clave del nombre del producto.

SOLO LECTURA (search_read/read). No escribe en Odoo.

Uso:
  python build_categorias.py 2026 9            -> imprime comparacion vs targets Sept
  python build_categorias.py 2026 10 --json    -> imprime JSON categorias de Oct
  python build_categorias.py 2026 10 --save    -> guarda categorias_2026-10.json
"""
import sys, json, unicodedata, argparse
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import erp

ADMIN = "gasto administrativo y gestion de cobranza"
TZ = timezone(timedelta(hours=-4))

def norm(x):
    x = unicodedata.normalize("NFKD", str(x or ""))
    return "".join(c for c in x if not unicodedata.combining(c)).lower().strip()

# (Categoria, [substrings normalizados])  -- el orden importa
RULES = [
    ("Gasto Administrativo", None),
    ("Motos",               ["motocicleta"]),
    ("Computación",         ["laptop", "portatil", "computadora", "all in one", "monitor"]),
    ("Impresión/Oficina",   ["impresora", "silhouette", "escaner"]),
    ("Televisores",         ["televisor", "smart tv", "google tv", "led tv", " qled"]),
    ("Consolas/Gaming",     ["xbox", "playstation", "dualsense", "consola", "nintendo"]),
    ("Inversores",          ["ups", "inversor", "estacion de carga", "planta electrica"]),
    ("Router",              ["router", "starlink", "access point"]),
    ("Línea Blanca",        ["congelador", "nevera", "refrigerador", "lavadora", "secadora",
                             "microondas", "cocina", "licuadora", "aire acondicionado", "split",
                             "ventilador", "cafetera"]),
    ("Automotríz",          ["caucho", "bateria", "automotriz", "aceite", "filtro de"]),
    ("Telefonía",           ["iphone", "galaxy", "poco f", "infinix", "honor", "tecno",
                             "redmi note", "redmi 15c", "samsung power", "celular", "smartphone"]),
]

def classify(name):
    n = norm(name)
    if n == ADMIN:
        return "Gasto Administrativo"
    for cat, keys in RULES:
        if keys and any(k in n for k in keys):
            return cat
    return "Otros"

def build(year, month):
    oc = erp.connect()
    lo = datetime(year, month, 1, tzinfo=TZ).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    ny, nm = (year + 1, 1) if month == 12 else (year, month + 1)
    hi = datetime(ny, nm, 1, tzinfo=TZ).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    orders = oc.search_read("sale.order",
        [("x_status_compra", "=", "4"), ("commitment_date", ">=", lo), ("commitment_date", "<", hi)],
        ["order_line"])
    ids = [i for o in orders for i in o["order_line"]]
    lines = oc.search_read("sale.order.line", [("id", "in", ids)],
                           ["product_id", "price_total", "product_uom_qty"])
    pids = sorted({l["product_id"][0] for l in lines if l["product_id"]})
    names = {}
    for i in range(0, len(pids), 300):
        for p in oc.read("product.product", pids[i:i+300], ["name"]):
            names[p["id"]] = p["name"]
    agg = defaultdict(lambda: {"categoria": "", "cantidad": 0, "lineas": 0, "qty": 0, "monto": 0.0, "productos": set()})
    for l in lines:
        if not l["product_id"]:
            continue
        pid = l["product_id"][0]
        cat = classify(names.get(pid))
        q = int(l["product_uom_qty"] or 0)
        a = agg[cat]
        a["categoria"] = cat
        a["cantidad"] += q if q > 0 else 1
        a["lineas"] += 1
        a["qty"] += q
        a["monto"] += l["price_total"] or 0.0
        a["productos"].add(pid)
    out = []
    order = [c for c, _ in RULES] + ["Otros"]
    for c in order:
        if c in agg:
            a = agg[c]
            out.append({"categoria": c, "cantidad": a["cantidad"], "lineas": a["lineas"], "qty": a["qty"],
                        "monto": round(a["monto"], 2), "productos": len(a["productos"])})
    return out

SEPT_TARGET = {
    "Gasto Administrativo": (81, 30323.26, 1),
    "Computación": (21, 17817.79, 12),
    "Motos": (11, 17795.0, 6),
    "Telefonía": (19, 11588.45, 14),
    "Línea Blanca": (1, 5450.0, 1),
    "Televisores": (12, 1952.41, 4),
    "Impresión/Oficina": (4, 1711.85, 3),
    "Otros": (26, 1678.05, 9),
    "Inversores": (16, 1389.11, 1),
    "Consolas/Gaming": (2, 1294.13, 2),
    "Router": (4, 1106.34, 2),
    "Automotríz": (3, 433.5, 2),
}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int)
    ap.add_argument("month", type=int)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--save", action="store_true")
    a = ap.parse_args()
    data = build(a.year, a.month)
    if a.json or a.save:
        js = json.dumps([{"categoria": c["categoria"], "cantidad": c["cantidad"],
                          "monto": c["monto"], "productos": c["productos"]} for c in data], ensure_ascii=False)
        if a.save:
            path = f"categorias_{a.year}-{a.month:02d}.json"
            open(path, "w", encoding="utf-8").write(js)
            print("guardado", path)
        else:
            print(js)
        total = sum(c["monto"] for c in data)
        print(f"// total={round(total,2)} filas={len(data)}")
    else:
        print(f"{'Categoria':<22}{'lin':>5} {'qty':>5} {'tgt':>5} {'monto':>11} {'target':>11} {'prod':>5} {'tgt':>4}  ok")
        ok = 0
        for c in data:
            t = SEPT_TARGET.get(c["categoria"])
            if t:
                good = (c["cantidad"] == t[0]) and abs(c["monto"] - t[1]) < 0.01 and c["productos"] == t[2]
                ok += good
                print(f"{c['categoria']:<22}{c['cantidad']:>5} {c['qty']:>5} {t[0]:>5} {c['monto']:>11.2f} {t[1]:>11.2f} "
                      f"{c['productos']:>5} {t[2]:>4}  {'OK' if good else 'DIFF'}")
            else:
                print(f"{c['categoria']:<22}{c['cantidad']:>5} {c['qty']:>5} {'-':>5} {c['monto']:>11.2f} {'-':>11} {c['productos']:>5} {'-':>4}  EXTRA")
        for k, t in SEPT_TARGET.items():
            if not any(c["categoria"] == k for c in data):
                print(f"{k:<22}  FALTA (target {t})")
        print(f"== {ok}/12 categorias exactas ==")
        print(f"total={round(sum(c['monto'] for c in data),2)} (target 92539.89)")
