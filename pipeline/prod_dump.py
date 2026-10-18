# -*- coding: utf-8 -*-
import sys, json, unicodedata
from collections import defaultdict
from datetime import datetime, timedelta, timezone
sys.path.insert(0, r"C:\Users\yarleyc\Desktop\crmlatinbien")
from odoo_client import OdooClient
cfg = json.load(open(r"C:\Users\yarleyc\Desktop\crmlatinbien\config.json", encoding="utf-8"))["odoo"]
oc = OdooClient(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"]).connect()
def norm(x):
    x = unicodedata.normalize("NFKD", str(x or ""))
    return "".join(c for c in x if not unicodedata.combining(c)).lower().strip()
ADMIN = "gasto administrativo y gestion de cobranza"
TZ = timezone(timedelta(hours=-4))
lo = datetime(2026, 9, 1, tzinfo=TZ).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
hi = datetime(2026, 10, 1, tzinfo=TZ).astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
o = oc.search_read("sale.order", [("x_status_compra", "=", "4"), ("commitment_date", ">=", lo), ("commitment_date", "<", hi)], ["order_line"])
ids = [i for x in o for i in x["order_line"]]
ls = oc.search_read("sale.order.line", [("id", "in", ids)], ["product_id", "price_total", "product_uom_qty"])
pid = sorted({l["product_id"][0] for l in ls if l["product_id"]})
pr = {}
for i in range(0, len(pid), 300):
    for p in oc.read("product.product", pid[i:i+300], ["name", "public_categ_ids", "categ_id"]):
        pr[p["id"]] = p
cats = {c["id"]: c for c in oc.search_read("product.public.category", [], ["name", "parent_id"])}
def leaf(cid):
    c = cats.get(cid); return c["name"] if c else None
def roots(cid):
    r = []
    c = cats.get(cid)
    while c:
        r.append(c["name"])
        c = cats.get(c["parent_id"][0]) if c.get("parent_id") else None
    return r
agg = defaultdict(lambda: [0.0, 0, set()])
for l in ls:
    p = pr.get(l["product_id"][0]) if l["product_id"] else None
    if not p: continue
    pt = l["price_total"] or 0.0
    web = sorted(set(x for c in (p.get("public_categ_ids") or []) for x in roots(c)))
    key = norm(p["name"])
    agg[key][0] += pt; agg[key][1] += 1; agg[key][2].add(tuple(web))
for k, v in sorted(agg.items(), key=lambda kv: -kv[1][0]):
    webs = " | ".join(sorted({"/".join(t) for t in v[2]})[:2])
    print(f"{v[0]:>10.2f}  qty={v[1]:>2}  {k[:60]:<60} [{webs}]")
print("SUM", round(sum(v[0] for v in agg.values()), 2))
