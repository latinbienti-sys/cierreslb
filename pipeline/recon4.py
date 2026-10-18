# -*- coding: utf-8 -*-
import sys, json, unicodedata
from collections import defaultdict
sys.path.insert(0, r"C:\Users\yarleyc\Desktop\crmlatinbien")
from odoo_client import OdooClient
cfg = json.load(open(r"C:\Users\yarleyc\Desktop\crmlatinbien\config.json", encoding="utf-8"))["odoo"]
oc = OdooClient(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"]).connect()
s = open(r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html", encoding="utf-8").read()
import re
DATA = json.loads(re.search(r"const DATA =(\{.*?\});\n", s, re.DOTALL).group(1))
emb = {f["orden"]: f for f in DATA["septiembre"]["facturas"]}

def norm(x):
    x=unicodedata.normalize("NFKD",str(x or "")); return "".join(c for c in x if not unicodedata.combining(c)).lower().strip()

lo,hi="2026-09-01 04:00:00","2026-10-01 04:00:00"
dom=[("x_status_compra","=","4"),("commitment_date",">=",lo),("commitment_date","<",hi)]
orders=oc.search_read("sale.order",dom,["name","amount_total","order_line","partner_id","user_id","x_status_operativos","commitment_date"])
allids=[i for o in orders for i in o["order_line"]]
lines=oc.search_read("sale.order.line",[("id","in",allids)],["order_id","product_id","product_uom_qty","price_subtotal","purchase_price","price_unit","name"])
ADMIN=2563
by=defaultdict(lambda:{"costo":0.0})
prodl={}
for l in lines:
    oid=l["order_id"][0]; pid=l["product_id"][0] if l["product_id"] else None
    prodl[pid]=l["product_id"][1] if l["product_id"] else "?"
    if pid!=ADMIN: by[oid]["costo"]+=(l["purchase_price"] or 0.0)*l["product_uom_qty"]
omap={o["id"]:o for o in orders}
print("Diferencias costo por orden (calc vs embed):")
for o in orders:
    nm=o["name"]; c=round(by[o["id"]]["costo"],2)
    e=emb.get(nm)
    if not e: print(f"  {nm}: NO en embed calc={c}"); continue
    d=c-e["costo"]
    if abs(d)>0.005: print(f"  {nm}: calc={c} emb={e['costo']} dif={d:.2f} monto={o['amount_total']} embmonto={e['monto']}")
# also diff monto vs amount_total
print("Diferencias monto:")
for o in orders:
    e=emb.get(o["name"])
    if e and abs(o["amount_total"]-e["monto"])>0.005: print(f"  {o['name']} amount_total={o['amount_total']} emb={e['monto']}")
