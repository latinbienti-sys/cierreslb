# -*- coding: utf-8 -*-
import sys, json
sys.path.insert(0, r"C:\Users\yarleyc\Desktop\crmlatinbien")
from odoo_client import OdooClient
cfg = json.load(open(r"C:\Users\yarleyc\Desktop\crmlatinbien\config.json", encoding="utf-8"))["odoo"]
oc = OdooClient(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"]).connect()
print("uid:", oc.uid)

# sale.order fields containing x_ or commitment/date
fields = oc.execute_kw("sale.order", "fields_get", [], {"attributes": ["string", "type", "selection"]})
keys = [k for k in fields if k.startswith("x_") or "commit" in k or k in ("date_order", "amount_total", "state")]
for k in sorted(keys):
    f = fields[k]
    sel = f.get("selection")
    print(f"  {k} ({f['type']}) {f['string']}" + (f"  sel={sel}" if sel else ""))
