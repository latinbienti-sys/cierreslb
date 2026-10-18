# -*- coding: utf-8 -*-
import sys, json, re
sys.path.insert(0, r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\pipeline")
import build_mes as B
s = open(r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html", encoding="utf-8").read()
DATA = json.loads(re.search(r"const DATA =(\{.*?\});\n", s, re.DOTALL).group(1))
emb = DATA["septiembre"]
oc = B.connect()
got = B.build_month(oc, 2026, 9)
for k in ("total_facturado","total_admin","total_costo","total_clientes","total_facturas","total_productos","total_margen","cancelaciones_count","cancelaciones_monto"):
    print(f"  {k:<20} emb={emb.get(k)}  got={got[k]}  {'OK' if abs((emb.get(k) or 0)-(got[k] or 0))<0.02 else 'DIF'}")
print("\nejecutivos (emb vs got):")
em = {e['nombre']: e for e in emb['ejecutivos']}
for e in got['ejecutivos']:
    o = em.get(e['nombre'])
    if o: 
        d1=abs(o['facturado']-e['facturado']); d2=abs(o['costo']-e['costo']); d3=o['unidades']-e['unidades']
        print(f"  {e['nombre'][:30]:<30} fact {o['facturado']} vs {e['facturado']} | und {o['unidades']} vs {e['unidades']} {'OK' if d1<1 and d3==0 else 'DIF'}")
    else: print(f"  {e['nombre']}: no en embed")
print("\ntop_productos (emb vs got) top6:")
em2 = {p['nombre']: p for p in emb['top_productos']}
for p in got['top_productos'][:6]:
    o = em2.get(p['nombre'])
    print(f"  {p['nombre'][:40]:<40} got q={p['cantidad']} m={p['monto']}" + (f" | emb q={o['cantidad']} m={o['monto']}" if o else " | (no en embed)"))
