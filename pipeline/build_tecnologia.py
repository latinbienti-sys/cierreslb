# -*- coding: utf-8 -*-
"""Genera la facturacion por tecnologia (pestana Cartera/Tecnologia) para un mes.
Regla: orden x_status_compra=4, mes por commitment_date tz Caracas (UTC-4).
Tecnologia = categoria web raiz (product.public.category) del producto NO-admin de mayor monto;
fallback por palabra clave del nombre; si nada -> Otros. Solo lectura.
Uso: python build_tecnologia.py 2026 10
"""
import sys, json, io, unicodedata, argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import erp
TZ = timezone(timedelta(hours=-4))
ADMIN = "gasto administrativo y gestion de cobranza"

def norm(x):
    x = unicodedata.normalize("NFKD", str(x or ""))
    return "".join(c for c in x if not unicodedata.combining(c)).lower().strip()

FALLBACK = [
    ("Computación", ["laptop", "portatil", "computadora", " all in one", "pc desktop", "monitor", "impresora", "printer", "desktop", "teclado", "mouse", "cpu ", "pc gamer", "workstation", "tablet pc"]),
    ("Hogar", ["congelador", "nevera", "refrigerador", "refriger", "cocina", "lavadora", "aire acondicionado", "split", "colchon", "calentador", "microondas", "freezer", "exhibidor"]),
    ("Telefonos", ["smartphone", "galaxy", "iphone", "celular", "redmi", "infinix", "honor "]),
    ("Televisores", ["televisor", "smart tv", "tv "]),
    ("Tablets", ["tablet", "ipad"]),
    ("Consolas", ["playstation", "xbox", "nintendo", "consola"]),
    ("Audio", ["audifono", "bocina", "parlante", "altavoz", "soundbar", "altavoces"]),
    ("Router", ["router", "modem", "repetidor", "access point"]),
    ("Refrigeración", ["refrigeracion", "nevera comercial"]),
]

def connect():
    return erp.connect()

def load_cats(oc):
    cats = {c["id"]: c for c in oc.search_read("product.public.category", [], ["name", "parent_id"])}
    def root_of(cid):
        c = cats.get(cid)
        while c and c.get("parent_id"):
            c = cats.get(c["parent_id"][0])
        return c["name"] if c else None
    return root_of

def fallback(nm):
    n = norm(nm)
    for tech, kws in FALLBACK:
        for k in kws:
            if k.strip() and k in n:
                return tech
    return "Otros"

def month_orders(oc, year, month):
    lo = datetime(year, month, 1, tzinfo=TZ)
    hi = datetime(year + (month // 12), (month % 12) + 1, 1, tzinfo=TZ)
    lg, hg = lo.astimezone(timezone.utc), hi.astimezone(timezone.utc)
    return oc.search_read("sale.order", [
        ("x_status_compra", "=", "4"),
        ("commitment_date", ">=", lg.strftime("%Y-%m-%d %H:%M:%S")),
        ("commitment_date", "<", hg.strftime("%Y-%m-%d %H:%M:%S"))],
        ["name", "amount_total", "order_line", "partner_id", "user_id", "commitment_date"])

def build(oc, year, month):
    root_of = load_cats(oc)
    orders = month_orders(oc, year, month)
    allids = [i for o in orders for i in o["order_line"]]
    lines = oc.search_read("sale.order.line", [("id", "in", allids)],
        ["order_id", "product_id", "product_uom_qty", "price_subtotal", "purchase_price"])
    pids = sorted({l["product_id"][0] for l in lines if l["product_id"]})
    prods = {}
    for i in range(0, len(pids), 300):
        for p in oc.read("product.product", pids[i:i+300], ["name", "public_categ_ids"]):
            prods[p["id"]] = p
    oid2lines = defaultdict(list)
    for l in lines:
        if l["order_id"]:
            oid2lines[l["order_id"][0]].append(l)

    agg = defaultdict(lambda: {"sf": 0, "sm": 0.0, "sk": 0.0, "sa": 0.0, "se": []})
    for o in orders:
        monto = round(o["amount_total"], 2)
        admin = 0.0; costo = 0.0; best = (None, -1.0)
        for l in oid2lines.get(o["id"], []):
            p = prods.get(l["product_id"][0]) if l["product_id"] else None
            nm = p["name"] if p else "Producto"
            sub = l["price_subtotal"] or 0.0
            if norm(nm) == ADMIN:
                admin += sub
            else:
                costo += (l["purchase_price"] or 0.0) * (l["product_uom_qty"] or 0.0)
                if sub > best[1]:
                    best = (p, sub)
        tech = None
        if best[0] is not None:
            roots = [root_of(c) for c in (best[0].get("public_categ_ids") or [])]
            roots = [r for r in roots if r]
            tech = roots[0] if roots else fallback(best[0]["name"])
        else:
            tech = "Otros"
        a = agg[tech]
        a["sf"] += 1
        a["sm"] += monto
        a["sk"] += round(costo, 2)
        a["sa"] += round(admin, 2)
        cdt = o["commitment_date"]
        d = datetime.fromisoformat(cdt).replace(tzinfo=timezone.utc).astimezone(TZ).date().isoformat() if cdt else ""
        a["se"].append({"o": o["name"], "c": o["partner_id"][1] if o["partner_id"] else "Cliente",
                        "e": o["user_id"][1] if o["user_id"] else "Sin asignar", "f": d,
                        "m": monto, "k": round(costo, 2), "a": round(admin, 2)})
    out = []
    for t, v in sorted(agg.items(), key=lambda kv: -kv[1]["sm"]):
        sm = round(v["sm"], 2); sa = round(v["sa"], 2); sk = round(v["sk"], 2)
        se = sorted(v["se"], key=lambda x: x["f"], reverse=True)
        out.append({"t": t, "sf": v["sf"], "sc": v["sf"], "sm": sm, "sp": round(sm - sa, 2), "sk": sk, "sa": sa, "sg": round(sm - sk, 2), "se": se})
    tot = {"oct_facturas": sum(r["sf"] for r in out), "oct_facturado": round(sum(r["sm"] for r in out), 2),
           "oct_precio": round(sum(r["sp"] for r in out), 2), "oct_costo": round(sum(r["sk"] for r in out), 2),
           "oct_admin": round(sum(r["sa"] for r in out), 2)}
    return {"por_tecnologia": out, "totales": tot}

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("year", type=int); ap.add_argument("month", type=int)
    ap.add_argument("--out", default=None); a = ap.parse_args()
    oc = connect()
    d = build(oc, a.year, a.month)
    out = a.out or f"tecnologia_{a.year:04d}-{a.month:02d}.json"
    json.dump(d, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(d["totales"], ensure_ascii=False))
    for r in d["por_tecnologia"]:
        print(f"   {r['t']:<20} sf={r['sf']:>3} sm={r['sm']:>10.2f} sk={r['sk']:>9.2f} sa={r['sa']:>9.2f}")
