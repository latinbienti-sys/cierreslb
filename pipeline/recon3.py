# -*- coding: utf-8 -*-
import sys, json
from collections import defaultdict
sys.path.insert(0, r"C:\Users\yarleyc\Desktop\crmlatinbien")
from odoo_client import OdooClient
cfg = json.load(open(r"C:\Users\yarleyc\Desktop\crmlatinbien\config.json", encoding="utf-8"))["odoo"]
oc = OdooClient(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"]).connect()

lf = oc.execute_kw("sale.order.line", "fields_get", [], {"attributes": ["string","type"]})
print("LINE fields (cost/price/qty/product):")
for k in sorted(lf):
    if any(t in k for t in ("price","purchase","qty","product","margin","cost")):
        print(f"  {k}: {lf[k]['string']}")

lo, hi = "2026-09-01 04:00:00", "2026-10-01 04:00:00"
dom = [("x_status_compra","=","4"),("commitment_date",">=",lo),("commitment_date","<",hi)]
orders = oc.search_read("sale.order", dom, ["name","amount_total","order_line"])
allids = [i for o in orders for i in o["order_line"]]
print("orders:", len(orders), "lines:", len(allids))
lines = oc.search_read("sale.order.line", [("id","in",allids)],
    ["order_id","product_id","product_uom_qty","price_subtotal","purchase_price","price_unit"])
ADMIN_NORM = "gasto administrativo y gestion de cobranza"
def norm(s): 
    import unicodedata
    s=unicodedata.normalize("NFKD",str(s)); s="".join(c for c in s if not unicodedata.combining(c))
    return s.lower().strip()
prod_names = {l["product_id"][0]: l["product_id"][1] for l in lines if l["product_id"]}
admin_ids = {pid for pid,nm in prod_names.items() if norm(nm)==ADMIN_NORM}
print("admin product ids:", admin_ids, [prod_names[p] for p in admin_ids])
tot_admin=tot_costo=tot_monto=0.0
by_order=defaultdict(lambda:{"admin":0.0,"costo":0.0,"monto":0.0})
for l in lines:
    pid = l["product_id"][0] if l["product_id"] else None
    oid = l["order_id"][0]
    by_order[oid]["monto"] += l["price_subtotal"]
    if pid in admin_ids: by_order[oid]["admin"] += l["price_subtotal"]
    else: by_order[oid]["costo"] += (l["purchase_price"] or 0.0)*l["product_uom_qty"]
omap={o["id"]:o for o in orders}
tot_admin=sum(v["admin"] for v in by_order.values())
tot_costo=sum(v["costo"] for v in by_order.values())
tot_monto=sum(v["monto"] for v in by_order.values())
print(f"SUM monto={tot_monto:.2f} admin={tot_admin:.2f} costo={tot_costo:.2f}")
print("embedded: monto=92539.89 admin=30323.26 costo=48913.95")
# sample first order
fo = next(o for o in orders if o["name"]=="LB-ORDEN-04337")
v=by_order[fo["id"]]
print(f"LB-ORDEN-04337 amount_total={fo['amount_total']} monto={v['monto']:.2f} costo={v['costo']:.2f} admin={v['admin']:.2f} (emb: 1219.67/639/322.48)")
