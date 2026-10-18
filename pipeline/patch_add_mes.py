# -*- coding: utf-8 -*-
"""Inserta en index.html una pestana dinamica del mes en curso (const MES),
replicando la pestana 'Septiembre 2026'. No modifica el resto."""
import io, json, sys

HTML = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html"
JSON = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\mes_2026-10.json"

s = io.open(HTML, encoding="utf-8").read()
mes = json.load(io.open(JSON, encoding="utf-8"))
mes_js = "const MES = " + json.dumps(mes, ensure_ascii=False, separators=(",", ":")) + ";\n"

# 1) Boton de pestana (despues de Septiembre 2026)
btn_anchor = '  <button class="tab-btn active" onclick="switchTab(\'septiembre\', this)">\U0001F4C5 Septiembre 2026</button>\n'
assert btn_anchor in s, "anchor boton no encontrado"
btn_new = btn_anchor + '  <button class="tab-btn" id="btn-mes" onclick="switchTab(\'mes\', this)">\U0001F4C5 Mes</button>\n'
s = s.replace(btn_anchor, btn_new, 1)

# 2) Contenido de la pestana (antes de CATEGORIAS)
cat_anchor = '<!-- ===== CATEGOR\u00cdAS TAB ===== -->'
assert cat_anchor in s, "anchor categorias no encontrado"
tab_html = '''<div class="tab-content" id="tab-mes">
  <div class="kpi-grid" id="kpi-mes"></div>
  <div class="grid-2">
    <div class="chart-box">
      <div class="section-title">\U0001F4B0 Resumen General</div>
      <div style="position:relative;height:320px"><canvas id="chartMesResumen"></canvas></div>
    </div>
    <div class="chart-box">
      <div class="section-title">\U0001F4CB Estado de Operaciones</div>
      <div class="ops-grid" id="ops-mes-grid"></div>
      <div style="position:relative;height:260px"><canvas id="chartMesOps"></canvas></div>
    </div>
  </div>
  <div class="grid-2">
    <div class="chart-box" id="box-mes-prodqty">
      <div class="section-title">\U0001F4E6 Productos M\u00e1s Vendidos \u2014 Por Cantidad</div>
      <div style="position:relative;height:320px"><canvas id="chartMesProdQty"></canvas></div>
    </div>
    <div class="chart-box" id="box-mes-prodmonto">
      <div class="section-title">\U0001F4B0 Productos M\u00e1s Vendidos \u2014 Por Monto</div>
      <div style="position:relative;height:320px"><canvas id="chartMesProdMonto"></canvas></div>
    </div>
  </div>
  <div class="grid-2">
    <div class="chart-box">
      <div class="section-title">\U0001F4CA Distribuci\u00f3n de Productos</div>
      <div style="position:relative;height:320px"><canvas id="chartMesDist"></canvas></div>
    </div>
    <div class="chart-box">
      <div class="section-title">\U0001F3C6 Top Producto por Monto</div>
      <div style="position:relative;height:320px"><canvas id="chartMesTopMonto"></canvas></div>
    </div>
  </div>
  <div class="warning-card" id="mes-dscto-card" style="display:none">
    <div class="section-title">\u26A0\uFE0F Facturas con Descuento en Gasto Administrativo</div>
    <div class="dscto-kpis" id="dscto-mes-kpis"></div>
    <div class="scroll-table">
      <table><thead><tr><th>#</th><th>Cliente</th><th>Factura</th><th>Ejecutivo</th><th class="text-right">Admin Esperado</th><th class="text-right">Dscto %</th><th class="text-right">Admin Real</th><th class="text-right">Ahorro</th><th>Fecha</th><th>Status</th></tr></thead><tbody id="dscto-mes-table"></tbody></table>
    </div>
  </div>
  <div class="section">
    <div class="section-title">\U0001F4C8 Desempe\u00f1o por Ejecutivo de Ventas</div>
    <div class="scroll-table"><table><thead><tr><th>#</th><th>Ejecutivo</th><th class="text-right">Facturas</th><th class="text-right">Unidades</th><th class="text-right">Monto Vendido</th><th class="text-right">Costo</th><th class="text-right">Margen</th><th>Desempe\u00f1o</th></tr></thead><tbody id="ejec-mes-table"></tbody></table></div>
  </div>
  <div class="section">
    <div class="section-title">\U0001F4E6 Detalle Top Productos</div>
    <div class="scroll-table" style="max-height:420px"><table><thead><tr><th>#</th><th>Producto</th><th class="text-right">Cantidad</th><th class="text-right">Monto</th></tr></thead><tbody id="top-prod-mes-table"></tbody></table></div>
  </div>
  <div class="section">
    <div class="section-title">\U0001F4CB Detalle Facturas</div>
    <div class="scroll-table" style="max-height:550px"><table><thead><tr><th>#</th><th>Orden</th><th>Cliente</th><th>Ejecutivo</th><th class="text-right">Monto</th><th class="text-right">Costo</th><th class="text-right">Admin</th><th>Fecha</th><th>Status</th></tr></thead><tbody id="facturas-mes-table"></tbody></table></div>
  </div>
</div>
'''
s = s.replace(cat_anchor, tab_html + cat_anchor, 1)

# 3) Const MES + renderer, antes de TAB SWITCH
sw = '// ===== TAB SWITCH ====='
assert sw in s, "anchor tab switch no encontrado"
render = mes_js + r'''
(function(){
  const MES_NAMES=['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre'];
  const btnM=document.getElementById('btn-mes');
  if(MES && MES.mes && btnM){ const p=MES.mes.split('-'); const nm=MES_NAMES[parseInt(p[1],10)-1]||''; btnM.innerHTML='\uD83D\uDCC5 '+nm+' '+p[0]; }
  const mesPct = MES.total_facturado ? ((MES.total_margen/MES.total_facturado)*100).toFixed(1) : 'N/D';
  const kpis=document.getElementById('kpi-mes');
  if(kpis){ [{icon:'\uD83D\uDCC4',value:MES.total_facturas,label:'Facturas',cls:''},{icon:'\uD83D\uDCB0',value:fmt(MES.total_facturado),label:'Total Facturado',cls:'accent'},{icon:'\uD83D\uDC65',value:MES.total_clientes,label:'Clientes',cls:''},{icon:'\uD83D\uDCC8',value:mesPct+'%',label:'Margen Bruto',cls:'green'}].forEach(k=>{const d=document.createElement('div');d.className='kpi-card';d.innerHTML='<div class="icon">'+k.icon+'</div><div class="value '+k.cls+'">'+k.value+'</div><div class="label">'+k.label+'</div>';kpis.appendChild(d);}); }
  const mesEnt=MES.facturas.filter(f=>f.status==='Entregado').length;
  const og=document.getElementById('ops-mes-grid');
  if(og){ [{num:mesEnt+' facturas',lbl:'Entregados',cls:'ops-entregado'},{num:MES.cancelaciones_count+' facturas',lbl:'Cancelaciones',cls:'ops-cancel'},{num:fmt(MES.cancelaciones_monto),lbl:'Monto Cancelado',cls:'ops-cancel'}].forEach(o=>{const d=document.createElement('div');d.className='ops-badge '+o.cls;d.innerHTML='<div class="num">'+o.num+'</div><div class="lbl">'+o.lbl+'</div>';og.appendChild(d);}); }
  if(MES.facturas_dscto && MES.facturas_dscto.length){
    document.getElementById('mes-dscto-card').style.display='block';
    const dk=document.getElementById('dscto-mes-kpis');
    const dm=MES.facturas_dscto.reduce((s,d)=>s+d.monto,0);
    const dr=MES.facturas_dscto.reduce((s,d)=>s+d.admin_real,0);
    [{label:'Facturas',value:MES.facturas_dscto.length},{label:'Monto Total',value:fmt(dm)},{label:'Ahorro',value:fmt(MES.total_ahorro_dscto||0)},{label:'Admin Real',value:fmt(dr)}].forEach(d=>{const el=document.createElement('div');el.className='dscto-kpi';el.innerHTML='<div class="val">'+d.value+'</div><div class="lbl">'+d.label+'</div>';dk.appendChild(el);});
    const dt=document.getElementById('dscto-mes-table');
    MES.facturas_dscto.forEach((f,i)=>{const tr=document.createElement('tr');tr.className='dscto-row';const badge=f.status==='Entregado'?'badge-entregado':'badge-aprobado';tr.innerHTML='<td>'+(i+1)+'</td><td>'+f.cliente+'</td><td>'+f.orden+'</td><td>'+f.ejecutivo+'</td><td class="text-right money">'+fmt(f.admin_esperado)+'</td><td class="text-right"><strong>'+f.descuento_pct+'%</strong></td><td class="text-right money">'+fmt(f.admin_real)+'</td><td class="text-right money green">'+fmt(f.descuento_monto)+'</td><td>'+f.fecha+'</td><td><span class="badge '+badge+'">'+f.status+'</span></td>';dt.appendChild(tr);});
  }
  const et=document.getElementById('ejec-mes-table');
  MES.ejecutivos.forEach((e,i)=>{const tr=document.createElement('tr');let b='';if(i===0)b='<span class="badge badge-leader">\uD83C\uDFC6 L\u00edder del Mes</span>';else if(e.facturas>0&&(e.facturado/e.facturas)>800)b='<span class="badge badge-perfect">\uD83C\uDFAF Alto Rendimiento</span>';const mg=e.facturado-(e.costo||0);tr.innerHTML='<td>'+(i+1)+'</td><td><strong>'+e.nombre+'</strong></td><td class="text-right">'+e.facturas+'</td><td class="text-right">'+e.unidades+'</td><td class="text-right money">'+fmt(e.facturado)+'</td><td class="text-right money">'+fmt(e.costo)+'</td><td class="text-right money green">'+fmt(mg)+'</td><td>'+b+'</td>';et.appendChild(tr);});
  const tp=document.getElementById('top-prod-mes-table');
  if(MES.top_productos.length){ MES.top_productos.forEach((p,i)=>{const tr=document.createElement('tr');tr.innerHTML='<td>'+(i+1)+'</td><td style="max-width:350px">'+p.nombre+'</td><td class="text-right">'+p.cantidad+'</td><td class="text-right money">'+fmt(p.monto)+'</td>';tp.appendChild(tr);}); }
  else { tp.innerHTML='<tr><td colspan="4" style="text-align:center;color:#8892a6;padding:20px">A\u00fan no hay productos registrados este mes</td></tr>'; }
  const ft=document.getElementById('facturas-mes-table');
  MES.facturas.forEach((f,i)=>{const tr=document.createElement('tr');let b='badge-sinasignar';if(f.status==='Entregado')b='badge-entregado';else if(f.status==='Aprobado')b='badge-aprobado';else if(f.status.indexOf('Cancelaci')>=0)b='badge-cancel';else if(f.status.indexOf('Congelado')>=0)b='badge-congelado';tr.innerHTML='<td>'+(i+1)+'</td><td>'+f.orden+'</td><td>'+f.cliente+'</td><td>'+f.ejecutivo+'</td><td class="text-right money">'+fmt(f.monto)+'</td><td class="text-right money">'+fmt(f.costo)+'</td><td class="text-right money">'+fmt(f.admin)+'</td><td>'+f.fecha+'</td><td><span class="badge '+b+'">'+f.status+'</span></td>';ft.appendChild(tr);});
  new Chart(document.getElementById('chartMesResumen'), { type:'bar', data:{labels:['Total Facturado','Total Productos','Gasto Administrativo','Costo Total'],datasets:[{data:[MES.total_facturado,MES.total_productos,MES.total_admin,MES.total_costo],backgroundColor:['#00205B','#FF6600','#F59E0B','#64748B'],borderRadius:6,barPercentage:0.60}]}, options:{responsive:true,maintainAspectRatio:false,layout:{padding:{top:30}},plugins:{legend:{display:false},datalabels:{display:true,anchor:'end',align:'top',color:'#1E293B',font:{weight:'bold',size:12},formatter:v=>fmtShort(v)},tooltip:{callbacks:{label:ctx=>fmt(ctx.raw)}}},scales:{y:{beginAtZero:true,ticks:{callback:v=>fmtShort(v),font:{size:10}},grid:{color:'#E2E8F0'}},x:{ticks:{font:{size:11}},grid:{display:false}}}}});
  new Chart(document.getElementById('chartMesOps'), { type:'doughnut', data:{labels:['Entregados','Cancelaciones'],datasets:[{data:[mesEnt,MES.cancelaciones_count],backgroundColor:['#10B981','#EF4444'],borderWidth:2,borderColor:'#fff'}]}, options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'bottom',labels:{font:{size:11},padding:12}},datalabels:{display:true,color:'#fff',font:{weight:'bold',size:13},formatter:v=>v}}} });
  if(MES.top_productos.length){
    const q=[...MES.top_productos].sort((a,b)=>b.cantidad-a.cantidad);
    new Chart(document.getElementById('chartMesProdQty'), { type:'bar', data:{labels:q.map(p=>p.nombre.length>22?p.nombre.substring(0,19)+'...':p.nombre),datasets:[{label:'Cantidad',data:q.map(p=>p.cantidad),backgroundColor:cColors.slice(0,q.length),borderRadius:4,barPercentage:0.7}]}, options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},datalabels:{display:true,anchor:'end',align:'top',color:'#1E293B',font:{weight:'bold',size:10},formatter:v=>v},tooltip:{callbacks:{label:ctx=>'Cantidad: '+ctx.raw}}},scales:{y:{beginAtZero:true,ticks:{stepSize:1,font:{size:10}},grid:{color:'#E2E8F0'}},x:{ticks:{font:{size:9},maxRotation:45,minRotation:30},grid:{display:false}}}}});
    const m=[...MES.top_productos].sort((a,b)=>b.monto-a.monto);
    new Chart(document.getElementById('chartMesProdMonto'), { type:'bar', data:{labels:m.map(p=>p.nombre.length>22?p.nombre.substring(0,19)+'...':p.nombre),datasets:[{label:'Monto',data:m.map(p=>p.monto),backgroundColor:cColors.slice(0,m.length),borderRadius:4,barPercentage:0.7}]}, options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},datalabels:{display:true,anchor:'end',align:'top',color:'#1E293B',font:{weight:'bold',size:9},formatter:v=>fmtShort(v)},tooltip:{callbacks:{label:ctx=>fmt(ctx.raw)}}},scales:{y:{beginAtZero:true,ticks:{callback:v=>fmtShort(v),font:{size:10}},grid:{color:'#E2E8F0'}},x:{ticks:{font:{size:9},maxRotation:45,minRotation:30},grid:{display:false}}}}});
    const dm=[...MES.top_productos].sort((a,b)=>b.monto-a.monto).slice(0,8);
    new Chart(document.getElementById('chartMesDist'), { type:'doughnut', data:{labels:dm.map(p=>p.nombre.length>30?p.nombre.substring(0,27)+'...':p.nombre),datasets:[{data:dm.map(p=>p.monto),backgroundColor:cColors.slice(0,8),borderWidth:2,borderColor:'#fff'}]}, options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'right',labels:{font:{size:10},boxWidth:12,padding:8}},datalabels:{display:true,color:'#fff',font:{weight:'bold',size:10},formatter:v=>fmtShort(v)},tooltip:{callbacks:{label:ctx=>fmt(ctx.raw)}}}} });
    const tm=[...MES.top_productos].sort((a,b)=>b.monto-a.monto).slice(0,8);
    new Chart(document.getElementById('chartMesTopMonto'), { type:'bar', data:{labels:tm.map(p=>p.nombre.length>25?p.nombre.substring(0,22)+'...':p.nombre),datasets:[{data:tm.map(p=>p.monto),backgroundColor:'#00205B',borderRadius:4,barPercentage:0.65}]}, options:{indexAxis:'y',responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false},datalabels:{display:true,anchor:'end',align:'right',color:'#1E293B',font:{weight:'bold',size:10},formatter:v=>fmtShort(v)},tooltip:{callbacks:{label:ctx=>fmt(ctx.raw)}}},scales:{x:{beginAtZero:true,ticks:{callback:v=>fmtShort(v),font:{size:10}},grid:{color:'#E2E8F0'}},y:{ticks:{font:{size:10}},grid:{display:false}}}}});
  } else {
    noData('chartMesProdQty','Sin productos este mes'); noData('chartMesProdMonto','Sin productos este mes');
    noData('chartMesDist','Sin productos este mes'); noData('chartMesTopMonto','Sin productos este mes');
  }
})();

'''
s = s.replace(sw, render + sw, 1)

io.open(HTML, "w", encoding="utf-8").write(s)
print("OK. Bytes:", len(s))
