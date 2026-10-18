# -*- coding: utf-8 -*-
import sys, json, unicodedata
from datetime import datetime, timedelta, timezone
sys.path.insert(0, r"C:\Users\yarleyc\Desktop\crmlatinbien")
from odoo_client import OdooClient
from build_categorias import classify, norm, TZ, ADMIN

year, month = 2026, 9
cfg = json.load(open(r"C:\Users\yarleyc\Desktop\crmlatinbien\config.json", encoding="utf-8"))["odoo"]
oc = OdooClient(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"]).connect()
lo = datetime(year, month, 1, tzinfo=TZ).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
hi = datetime(year, month + 1, 1, tzinfo=TZ).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
orders = oc.search_read("sale.order", [("x_status_compra", "=", "4"), ("commitment_date", ">=", lo), ("commitment_date", "<", hi)], ["order_line"])
ids = [i for o in orders for i in o["order_line"]]
lines = oc.search_read("sale.order.line", [("id", "in", ids)], ["product_id", "price_total", "product_uom_qty"])
pids = sorted({l["product_id"][0] for l in lines if l["product_id"]})
names = {}
for i in range(0, len(pids), 300):
    for p in oc.read("product.product", pids[i:i+300], ["name"]):
        names[p["id"]] = p["name"]
focus = sys.argv[1] if len(sys.argv) > 1 else None
rows = []
for l in lines:
    nm = names.get(l["product_id"][0]) if l["product_id"] else "?"
    cat = classify(nm)
    if focus and cat != focus:
        continue
    rows.append((cat, norm(nm), l["product_uom_qty"], l["price_total"] or 0.0))
rows.sort(key=lambda r: (r[0], -r[3]))
cur = None
for cat, nm, q, pt in rows:
    if cat != cur:
        cur = cat
        print(f"\n### {cat}")
    print(f"  q={q:<3} {pt:>9.2f}  {nm[:58]}")
