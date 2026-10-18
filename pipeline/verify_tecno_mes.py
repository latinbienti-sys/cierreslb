# -*- coding: utf-8 -*-
import io, json
HTML = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html"
s = io.open(HTML, encoding="utf-8").read()
def grab(a, b):
    i = s.index(a); i = s.index("{", i); j = s.index(b, i)
    return json.loads(s[i:j].strip().rstrip(";").strip())
TECNO = grab("const TECNO =", "const TECNO_OCT =")
TECNO_OCT = grab("const TECNO_OCT =", "const FLUJO =")

def view(seg, cartera, mes):
    mesRow = {r["t"]: r for r in seg}
    techs = list(dict.fromkeys([r["t"] for r in cartera] + [r["t"] for r in seg]))
    rows = []
    for t in techs:
        m = mesRow.get(t) or {}
        rows.append({"t": t, "sm": m.get("sm", 0), "sk": m.get("sk", 0), "sa": m.get("sa", 0), "sp": m.get("sp", 0), "sf": m.get("sf", 0)})
    tot = {k: round(sum(r[k] for r in rows), 2) for k in ("sm", "sk", "sa", "sp", "sf")}
    motos = next((r for r in rows if r["t"] == "Motos"), {"sm": 0, "sk": 0, "sa": 0})
    print(f"[{mes}] facturas={tot['sf']} facturado={tot['sm']} precio={tot['sp']} costo={tot['sk']} admin={tot['sa']}")
    print(f"       sin Motos -> facturado={round(tot['sm']-motos['sm'],2)} costo={round(tot['sk']-motos['sk'],2)} admin={round(tot['sa']-motos['sa'],2)}; Motos={motos['sm']}")

view(TECNO["por_tecnologia"], TECNO["por_tecnologia"], "Septiembre")
view(TECNO_OCT["por_tecnologia"], TECNO["por_tecnologia"], "Octubre")
print("esperado Sept: 89 / 92539.89 / 62216.63 / 48913.95 / 30323.26")
print("esperado Oct : 47 / 34524.42 / 24964.69 / 17882.68 / 9559.73")
filtro = ("setTecMes('sep'" in s) and ("setTecMes('oct'" in s)
print("filtro sep/oct presente:", filtro)
print("tec-chart-mes:", 'id="tec-chart-mes"' in s, "| th ids:", all(x in s for x in ('id="th-tec-sf"', 'id="th-tec-sm"', 'id="th-tec-sa"')))
print("cartera intacta (totales TECNO):", TECNO["totales"])
