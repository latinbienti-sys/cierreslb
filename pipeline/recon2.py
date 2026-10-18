# -*- coding: utf-8 -*-
import sys, json
from collections import defaultdict
sys.path.insert(0, r"C:\Users\yarleyc\Desktop\crmlatinbien")
from odoo_client import OdooClient
cfg = json.load(open(r"C:\Users\yarleyc\Desktop\crmlatinbien\config.json", encoding="utf-8"))["odoo"]
oc = OdooClient(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"]).connect()

OPS = {"0":"SAV-PRESUPUESTO","1":"SAV-POR COMPLETAR","2":"SAV-ANALISIS AAC","3":"SAV-COMITE","4":"SAV-APROBADO-ESPERA",
       "5":"SAV-NEGADO-RETIRO","6":"CVG-ENTREGADO","7":"RETIRADO DEVOLUCION","8":"CANCELACION TOTAL",
       "9":"EXCLUSION MORA","10":"ANULADO","11":"CAMBIO PLAN","12":"CONGELADO"}

def pull(y, m):
    nxt = (y+1,1) if m==12 else (y,m+1)
    lo = f"{y:04d}-{m:02d}-01 04:00:00"   # Caracas UTC-4
    hi = f"{nxt[0]:04d}-{nxt[1]:02d}-01 04:00:00"
    dom = [("x_status_compra","=","4"),("commitment_date",">=",lo),("commitment_date","<",hi)]
    ids = oc.search("sale.order", dom)
    rows = oc.search_read("sale.order", dom, ["name","amount_total","x_status_operativos","commitment_date","partner_id"])
    tot = sum(r["amount_total"] for r in rows)
    by = defaultdict(lambda:[0,0.0])
    for r in rows:
        ops = r["x_status_operativos"] or "?"
        by[ops][0]+=1; by[ops][1]+=r["amount_total"]
    print(f"=== {y}-{m:02d}  ids={len(ids)}  sum amount_total={tot:.2f}")
    for ops in sorted(by):
        print(f"   ops={ops:>2} {OPS.get(ops,'?'):<22} n={by[ops][0]:>3}  monto={by[ops][1]:>11.2f}")

pull(2026,9)
pull(2026,10)
pull(2026,8)
