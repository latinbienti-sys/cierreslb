# -*- coding: utf-8 -*-
import sys, json, unicodedata
from collections import defaultdict
sys.path.insert(0, r"C:\Users\yarleyc\Desktop\crmlatinbien")
from odoo_client import OdooClient
cfg = json.load(open(r"C:\Users\yarleyc\Desktop\crmlatinbien\config.json", encoding="utf-8"))["odoo"]
oc = OdooClient(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"]).connect()
def norm(x):
    x = unicodedata.normalize("NFKD", str(x or ""))
    return "".join(c for c in x if not unicodedata.combining(c)).lower().strip()
ADMIN = "gasto administrativo y gestion de cobranza"
from datetime import datetime, timedelta, timezone
TZ = timezone(timedelta(hours=-4))
lo = datetime(2026, 9, 1, tzinfo=TZ).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
hi = datetime(2026, 10, 1, tzinfo=TZ).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
orders = oc.search_read("sale.order", [("x_status_compra", "=", "4"), ("commitment_date", ">=", lo), ("commitment_date", "<", hi)], ["order_line"])
allids = [i for o in orders for i in o["order_line"]]
lines = oc.search_read("sale.order.line", [("id", "in", allids)], ["product_id", "price_subtotal", "price_total", "product_uom_qty"])
pids = sorted({l["product_id"][0] for l in lines if l["product_id"]})
prods = {}
for i in range(0, len(pids), 300):
    for p in oc.read("product.product", pids[i:i+300], ["name", "public_categ_ids", "categ_id"]):
        prods[p["id"]] = p
cats = {c["id"]: c for c in oc.search_read("product.public.category", [], ["name", "parent_id"])}
def root_of(cid):
    c = cats.get(cid)
    while c and c.get("parent_id"): c = cats.get(c["parent_id"][0])
    return c["name"] if c else None
by_root = defaultdict(lambda: [0, 0.0, set()])
by_cat = defaultdict(lambda: [0, 0.0, set()])
sub_tot = 0.0; total_tot = 0.0
for l in lines:
    p = prods.get(l["product_id"][0]) if l["product_id"] else None
    if not p: continue
    sub = l["price_subtotal"] or 0.0
    if norm(p["name"]) == ADMIN:
        by_root["<ADMIN>"][0] += 1; by_root["<ADMIN>"][1] += sub; by_root["<ADMIN>"][2].add(p["id"])
        continue
    sub_tot += sub; total_tot += (l["price_total"] or 0.0)
    roots = sorted(set(r for r in (root_of(c) for c in (p.get("public_categ_ids") or [])) if r))
    key = roots[0] if roots else "<sin-cat-web>"
    by_root[key][0] += 1; by_root[key][1] += sub; by_root[key][2].add(p["id"])
    rc = p["categ_id"][1] if p["categ_id"] else "?"
    by_cat[rc][0] += 1; by_cat[rc][1] += sub; by_cat[rc][2].add(p["id"])
print("=== por Categoria WEB raiz ===")
for k, v in sorted(by_root.items(), key=lambda kv: -kv[1][1]):
    print(f"  {k:<22} lineas={v[0]:>3} monto={v[1]:>10.2f} productos={len(v[2])}")
print("=== por Categoria interna (CASO DE USO) ===")
for k, v in sorted(by_cat.items(), key=lambda kv: -kv[1][1]):
    print(f"  {k:<22} lineas={v[0]:>3} monto={v[1]:>10.2f} productos={len(v[2])}")
print(f"non-admin subtotal={sub_tot:.2f}  price_total={total_tot:.2f}  (target 62216.63)")
print("TARGET: Gasto Admin 30323.26 | non-admin total (precio producto) = 62216.63")
