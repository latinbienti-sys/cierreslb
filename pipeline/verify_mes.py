# -*- coding: utf-8 -*-
import io
s = io.open(r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html", encoding="utf-8").read()
ids = ['btn-mes','tab-mes','kpi-mes','ops-mes-grid','mes-dscto-card','dscto-mes-kpis','dscto-mes-table',
       'ejec-mes-table','top-prod-mes-table','facturas-mes-table','chartMesResumen','chartMesOps',
       'chartMesProdQty','chartMesProdMonto','chartMesDist','chartMesTopMonto']
miss = [i for i in ids if ('id="' + i + '"') not in s]
print("faltan:", miss if miss else "ninguno")
print("tab-content count:", s.count('class="tab-content'))
print("tab buttons count:", s.count('tab-btn"'))
print("const MES:", "const MES =" in s)
print("Sept intacto:", ("kpi-sept" in s) and ('id="tab-septiembre"' in s))
for t in ('tab-dashboard','tab-septiembre','tab-mes','tab-categorias','tab-tecnologia','tab-flujo','tab-dashfacturacion'):
    print("  ", t, 'id="'+t+'"' in s)
