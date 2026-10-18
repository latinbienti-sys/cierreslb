# -*- coding: utf-8 -*-
"""Patch one-shot: agrega facturacion de Octubre + filtro de mes a la pestana Cartera/Tecnologia.
No toca cartera ni Flujo de Cuotas."""
import io, json, sys

PATH = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html"
s = io.open(PATH, encoding="utf-8").read()
oct_data = json.load(open(r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\pipeline\tecnologia_2026-10.json", encoding="utf-8"))
tec_oct_json = json.dumps({"por_tecnologia": oct_data["por_tecnologia"], "totales": oct_data["totales"]}, ensure_ascii=False, separators=(",", ":"))

# 1) Insertar const TECNO_OCT antes de const FLUJO
anchor = "\nconst FLUJO = "
assert anchor in s, "no const FLUJO"
s = s.replace(anchor, "\nconst TECNO_OCT = " + tec_oct_json + ";" + anchor, 1)

# 2) Filtro de mes dentro de la pestana tecnologia
tab_open = '<div class="tab-content" id="tab-tecnologia">'
assert tab_open in s
filter_html = tab_open + '\n  <div style="display:flex;gap:8px;align-items:center;margin-bottom:14px;flex-wrap:wrap">\n' \
    '    <span style="font-size:12px;color:#64748B;font-weight:600">Mes de facturaci\u00f3n:</span>\n' \
    '    <button class="tab-btn active tec-mes-btn" onclick="setTecMes(\'sep\', this)">\U0001F4C5 Septiembre 2026</button>\n' \
    '    <button class="tab-btn tec-mes-btn" onclick="setTecMes(\'oct\', this)">\U0001F4C5 Octubre 2026</button>\n' \
    '  </div>'
s = s.replace(tab_open, filter_html, 1)

# 3) Titulo del grafico dinamico
old_title = 'Facturado Septiembre vs Precio Producto, Costo y G. Admin por Tecnolog\u00eda'
assert old_title in s
s = s.replace(old_title, 'Facturado <span id="tec-chart-mes">Septiembre</span> vs Precio Producto, Costo y G. Admin por Tecnolog\u00eda', 1)

# 4) ids en cabeceras de mes de la tabla
rep = [('<th class="text-right">Fact. Sept</th>', '<th class="text-right" id="th-tec-sf">Fact. Sept</th>'),
       ('<th class="text-right">Facturado Sept</th>', '<th class="text-right" id="th-tec-sm">Facturado Sept</th>'),
       ('<th class="text-right">G. Admin Sept</th>', '<th class="text-right" id="th-tec-sa">G. Admin Sept</th>')]
for a, b in rep:
    assert a in s, a
    s = s.replace(a, b, 1)

# 5) Reemplazar el bloque de render de tecnologia
START = "// ===== CARTERA / TECNOLOG\u00cdA TAB ====="
END = "// ===== MODAL DETALLE POR TECNOLOG\u00cdA ====="
i, j = s.index(START), s.index(END)

NEW = r'''// ===== CARTERA / TECNOLOGÍA TAB =====
let tecMesActual = 'sep';
const tecDestroy = id => { const p = Chart.getChart(id); if (p) p.destroy(); };
const TECNO_CARTERA = {};
if (typeof TECNO !== 'undefined' && TECNO && TECNO.por_tecnologia) TECNO.por_tecnologia.forEach(r => { TECNO_CARTERA[r.t] = r; });

function renderTecnologia(mes) {
  if (typeof TECNO === 'undefined' || !TECNO || !TECNO.por_tecnologia) {
    document.getElementById('kpi-tec').innerHTML = '<div style="grid-column:1/-1;text-align:center;color:#8892a6;padding:20px">Sin datos de cartera por tecnología</div>';
    return;
  }
  const oct = (mes === 'oct') && (typeof TECNO_OCT !== 'undefined') && TECNO_OCT;
  const seg = oct ? (TECNO_OCT.por_tecnologia || []) : TECNO.por_tecnologia;
  const mesNombre = oct ? 'Octubre' : 'Septiembre';
  const mesRow = {}; seg.forEach(r => { mesRow[r.t] = r; });
  const techs = [...new Set([...TECNO.por_tecnologia.map(r => r.t), ...seg.map(r => r.t)])];
  const rows = techs.map(t => {
    const m = mesRow[t] || {sf:0,sm:0,sp:0,sk:0,sa:0,sg:0};
    const c = TECNO_CARTERA[t] || {};
    return {
      t, sf:m.sf||0, sm:m.sm||0, sp:m.sp||0, sk:m.sk||0, sa:m.sa||0,
      sg:(m.sg!=null?m.sg:(m.sm||0)-(m.sk||0)),
      cf:c.cf||0, cm:c.cm||0, ga:c.ga||0, cb:c.cb||0, mo:c.mo||0, co:c.co||0, pcmb:c.pcmb||0, pmo:c.pmo||0,
      se:(oct ? (m.se || []) : (c.se || [])), ca:(c.ca || [])
    };
  }).sort((a,b) => b.sm - a.sm);

  const TEtot = TECNO.totales || {};
  const fmtPctv = v => Number(v).toFixed(1)+'%';
  const sum = k => rows.reduce((s,r) => s + r[k], 0);
  const motos = rows.find(r => r.t === 'Motos') || {sm:0,sk:0,sa:0};

  const kpiTec = document.getElementById('kpi-tec'); kpiTec.innerHTML = '';
  [{icon:'💰', value:fmt(sum('sm')), label:'Facturado '+mesNombre+' (Entregado + Canc. Total)', cls:'accent'},
   {icon:'🧮', value:fmt(sum('sm')-(motos.sm||0)), label:'Facturado '+mesNombre+' Tecnología (sin Motos)', cls:'green'},
   {icon:'🏍️', value:fmt(motos.sm||0), label:'Facturado '+mesNombre+' Motos', cls:''},
   {icon:'🏷️', value:fmt(sum('sp')), label:'Precio Producto '+mesNombre, cls:''},
   {icon:'📦', value:fmt(sum('sk')-(motos.sk||0)), label:'Costo '+mesNombre+' Tecnología (sin Motos)', cls:''},
   {icon:'📦', value:fmt(motos.sk||0), label:'Costo '+mesNombre+' Motos', cls:''},
   {icon:'🧾', value:fmt(sum('sa')-(motos.sa||0)), label:'G. Admin '+mesNombre+' Tecnología (sin Motos)', cls:'green'},
   {icon:'🧾', value:fmt(motos.sa||0), label:'G. Admin '+mesNombre+' Motos', cls:''},
   {icon:'🛒', value:fmt(TEtot.car_monto||0), label:'Cartera Facturada', cls:''},
   {icon:'🧾', value:fmt(TEtot.car_admin||0), label:'G. Admin Cartera', cls:''},
   {icon:'💵', value:fmt(TEtot.car_cobrado||0), label:'Cobrado Cartera', cls:'green'},
   {icon:'⏰', value:fmt(TEtot.car_moroso||0), label:'Moroso Cartera', cls:'accent'},
   {icon:'🚨', value:TEtot.car_cuotas||0, label:'Cuotas Vencidas', cls:''}].forEach(k => {
      const div = document.createElement('div'); div.className = 'kpi-card';
      div.innerHTML = '<div class="icon">'+k.icon+'</div><div class="value '+k.cls+'">'+k.value+'</div><div class="label">'+k.label+'</div>';
      kpiTec.appendChild(div);
  });

  [['tec-chart-mes',mesNombre],['th-tec-sf','Fact. '+mesNombre],['th-tec-sm','Facturado '+mesNombre],['th-tec-sa','G. Admin '+mesNombre]].forEach(p => {
    const el = document.getElementById(p[0]); if (el) el.textContent = p[1];
  });

  const tecSorted = rows.filter(r => r.sf > 0).slice(0,8);
  tecDestroy('chartTecSept');
  new Chart(document.getElementById('chartTecSept'), { type:'bar', data:{labels:tecSorted.map(r=>r.t),datasets:[{label:'Facturado '+mesNombre,data:tecSorted.map(r=>r.sm),backgroundColor:'#00205B',borderRadius:6,barPercentage:0.45},{label:'Precio Producto',data:tecSorted.map(r=>r.sp||0),backgroundColor:'#7C3AED',borderRadius:6,barPercentage:0.45},{label:'Costo',data:tecSorted.map(r=>r.sk),backgroundColor:'#FF6600',borderRadius:6,barPercentage:0.45},{label:'G. Admin',data:tecSorted.map(r=>r.sa||0),backgroundColor:'#F59E0B',borderRadius:6,barPercentage:0.45}]}, options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top',labels:{font:{size:11}}},datalabels:{display:true,anchor:'end',align:'top',color:'#1E293B',font:{weight:'bold',size:9},formatter:v=>fmtShort(v)},tooltip:{callbacks:{label:ctx=>ctx.dataset.label+': '+fmt(ctx.raw)}}},scales:{y:{beginAtZero:true,ticks:{callback:v=>fmtShort(v),font:{size:10}},grid:{color:'#E2E8F0'}},x:{ticks:{font:{size:10},maxRotation:30,minRotation:25},grid:{display:false}}}}});

  const tecCar = [...rows].sort((a,b) => b.mo - a.mo).slice(0,8);
  tecDestroy('chartTecCartera');
  new Chart(document.getElementById('chartTecCartera'), { type:'bar', data:{labels:tecCar.map(r=>r.t),datasets:[{label:'Cobrado',data:tecCar.map(r=>r.cb),backgroundColor:'#10B981',borderRadius:6,barPercentage:0.45},{label:'Moroso',data:tecCar.map(r=>r.mo),backgroundColor:'#EF4444',borderRadius:6,barPercentage:0.45}]}, options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{position:'top',labels:{font:{size:11}}},datalabels:{display:true,anchor:'end',align:'top',color:'#1E293B',font:{weight:'bold',size:9},formatter:v=>fmtShort(v)},tooltip:{callbacks:{label:ctx=>ctx.dataset.label+': '+fmt(ctx.raw)}}},scales:{y:{beginAtZero:true,ticks:{callback:v=>fmtShort(v),font:{size:10}},grid:{color:'#E2E8F0'}},x:{ticks:{font:{size:10},maxRotation:30,minRotation:25},grid:{display:false}}}}});

  const tecTb = document.getElementById('tec-table'); tecTb.innerHTML = '';
  rows.forEach((r,i) => {
    const tr = document.createElement('tr'); tr.style.cursor = 'pointer'; tr.title = 'Ver clientes de '+r.t; tr.onclick = () => openTecModal(r);
    const moCls = r.pmo >= 10 ? 'badge-cancel' : (r.pmo >= 5 ? 'badge-aprobado' : 'badge-entregado');
    tr.innerHTML = '<td>'+(i+1)+'</td><td><strong>'+r.t+'</strong></td><td class="text-right">'+(r.sf||0)+'</td><td class="text-right money">'+fmt(r.sm||0)+'</td><td class="text-right money">'+fmt(r.sp||0)+'</td><td class="text-right money">'+fmt(r.sk||0)+'</td><td class="text-right money">'+fmt(r.sa||0)+'</td><td class="text-right money green">'+fmt(r.sg||0)+'</td><td class="text-right">'+(r.cf||0)+'</td><td class="text-right money">'+fmt(r.cm||0)+'</td><td class="text-right money">'+fmt(r.ga||0)+'</td><td class="text-right money green">'+fmt(r.cb||0)+'</td><td class="text-right money">'+fmt((r.cm||0)-(r.cb||0))+'</td><td class="text-right money red">'+fmt(r.mo||0)+'</td><td class="text-right">'+(r.co||0)+'</td><td class="text-right">'+fmtPctv(r.pcmb||0)+'</td><td class="text-right"><span class="badge '+moCls+'">'+fmtPctv(r.pmo||0)+'</span></td>';
    tecTb.appendChild(tr);
  });

  if (!window.__tecMorDone) {
    window.__tecMorDone = true;
    const tecMorTb = document.getElementById('tec-mor-cli-table');
    (TECNO.top_clientes_morosos || []).forEach((x,i) => { const tr = document.createElement('tr'); tr.innerHTML = '<td>'+(i+1)+'</td><td><strong>'+x.cliente+'</strong></td><td class="text-right money red">'+fmt(x.monto)+'</td><td class="text-right">'+x.cuotas+'</td><td class="text-right">'+x.facturas.length+'</td><td style="max-width:280px;font-size:11px;color:#64748B;word-break:break-word">'+x.facturas.join(', ')+'</td>'; tecMorTb.appendChild(tr); });
  }
}
function setTecMes(mes, el) {
  tecMesActual = mes;
  document.querySelectorAll('#tab-tecnologia .tec-mes-btn').forEach(b => b.classList.remove('active'));
  if (el) el.classList.add('active');
  renderTecnologia(mes);
}
renderTecnologia('sep');

'''
s = s[:i] + NEW + s[j:]

io.open(PATH, "w", encoding="utf-8").write(s)
print("patched. len:", len(s))
