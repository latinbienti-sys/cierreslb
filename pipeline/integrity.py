# -*- coding: utf-8 -*-
import io, re, json
s = io.open(r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html", encoding="utf-8").read()
DATA = json.loads(re.search(r"const DATA =(\{.*?\});\n", s, re.DOTALL).group(1))
TECNO = json.loads(re.search(r"const TECNO = (.*?);\n", s, re.DOTALL).group(1))
FLUJO = json.loads(re.search(r"const FLUJO = (.*?);\n", s, re.DOTALL).group(1))
MES = json.loads(re.search(r"const MES = (.*?);\n", s, re.DOTALL).group(1))
sep = DATA["septiembre"]; ago = DATA["facturacion_agosto"]; T = DATA["tendencia"]
print("Septiembre:", sep["total_facturado"], sep["count"], "| Ago:", ago["total_facturado"], ago["total_facturas"])
print("Tendencia rows:", [r["key"] for r in T["rows"]], "actual", T["actual"]["label"], "mejor", T["mejor"]["label"])
print("MES:", MES["mes"], MES["total_facturado"])
print("TECNO sept_facturado:", TECNO["totales"]["sept_facturado"])
print("FLUJO monto/cobrado/moroso:", FLUJO["totales"]["monto"], FLUJO["totales"]["cobrado"], FLUJO["totales"]["moroso"])
print("Categorias:", len(DATA["categorias"]), "suma", round(sum(c["monto"] for c in DATA["categorias"]),2))
print("tabs:", s.count('class="tab-content'))
