# -*- coding: utf-8 -*-
"""Lineas de credito activadas en el mes (res.partner.x_fecha_activacion) vs lo facturado en el mes.

SOLO LECTURA en Odoo (search_read/read). No escribe nada en Odoo.
Mes por zona America/Caracas (UTC-4), igual que build_mes.py.
Facturado = mismas reglas que build_mes: x_status_compra=4 y commitment_date en el mes.
El cruce se hace por ID del contacto del pedido (no por nombre: hay homonimos).

Uso:
  python build_activaciones.py 2026 10           -> guarda activaciones_2026-10.json
  python build_activaciones.py 2026 10 --inject  -> ademas reemplaza/inserta `const ACT_OCT = ...;` en index.html
"""
import io, os, re, sys, json, argparse
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import erp

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(os.path.dirname(HERE), "index.html")
TZ = timezone(timedelta(hours=-4))
FMT = "%Y-%m-%d %H:%M:%S"


def to_local(dt_str):
    if not dt_str:
        return None
    return datetime.strptime(dt_str, FMT).replace(tzinfo=timezone.utc).astimezone(TZ)


def build(oc, year, month):
    lo = datetime(year, month, 1, tzinfo=TZ)
    hi = datetime(year + (month // 12), (month % 12) + 1, 1, tzinfo=TZ)
    lg, hg = lo.astimezone(timezone.utc).strftime(FMT), hi.astimezone(timezone.utc).strftime(FMT)

    # 1) Pedidos facturados del mes (misma regla que build_mes)
    orders = oc.search_read("sale.order",
        [("x_status_compra", "=", "4"), ("commitment_date", ">=", lg), ("commitment_date", "<", hg)],
        ["name", "amount_total", "partner_id", "user_id", "campaign_id", "commitment_date"])

    # 2) Contactos de esos pedidos (y su empresa) con las dos fechas:
    #    Activacion = x_fecha_activacion con x_activacion_linea = True
    #    Aprobacion = x_fecha_resolucion_final
    PF = ["name", "x_fecha_activacion", "x_activacion_linea", "x_fecha_resolucion_final",
          "x_status_expediente", "commercial_partner_id", "user_id"]
    pids = sorted({o["partner_id"][0] for o in orders if o["partner_id"]})
    partners = {p["id"]: p for p in oc.read("res.partner", pids, PF)} if pids else {}
    cids = sorted({p["commercial_partner_id"][0] for p in partners.values()
                   if p.get("commercial_partner_id") and p["commercial_partner_id"][0] not in partners})
    if cids:
        for p in oc.read("res.partner", cids, PF):
            partners[p["id"]] = p

    def ficha(pid):
        """Registro con datos de linea: el contacto, o su empresa si el contacto no tiene."""
        p = partners.get(pid) or {}
        if not (p.get("x_activacion_linea") or p.get("x_fecha_activacion")) and p.get("commercial_partner_id"):
            c = partners.get(p["commercial_partner_id"][0]) or {}
            if c.get("x_activacion_linea") or c.get("x_fecha_activacion"):
                return c
        return p

    # 3) Activadas en el mes (fecha activacion en el mes + linea activa) y aprobadas en el mes
    dom_act = [("x_fecha_activacion", ">=", lg), ("x_fecha_activacion", "<", hg)]
    act = oc.search_read("res.partner", dom_act + [("x_activacion_linea", "=", True)], PF)
    act_ids = {a["id"] for a in act}
    fecha_sin_linea = oc.search_read("res.partner", dom_act + [("x_activacion_linea", "=", False)], PF)
    apr = oc.search_read("res.partner",
        [("x_fecha_resolucion_final", ">=", lg), ("x_fecha_resolucion_final", "<", hg)], PF)

    facturas = {}
    pedidos_de = {}  # partner id (contacto o empresa) -> [ordenes]
    for o in orders:
        pid = o["partner_id"][0] if o["partner_id"] else None
        p = ficha(pid) if pid else {}
        fa, fr = to_local(p.get("x_fecha_activacion")), to_local(p.get("x_fecha_resolucion_final"))
        activa = bool(p.get("x_activacion_linea"))
        facturas[o["name"]] = {"partner_id": pid,
                               "linea_activa": activa,
                               "status": p.get("x_status_expediente") or "",
                               "fecha_act": fa.date().isoformat() if fa else "",
                               "act_mes": bool(activa and fa and lo <= fa < hi),
                               "fecha_aprob": fr.date().isoformat() if fr else "",
                               "aprob_mes": bool(fr and lo <= fr < hi)}
        cpid = (partners.get(pid) or {}).get("commercial_partner_id")
        for k in {pid, cpid[0] if cpid else pid, p.get("id")} - {None}:
            pedidos_de.setdefault(k, [])
            if o["name"] not in pedidos_de[k]:
                pedidos_de[k].append(o["name"])
    by_partner = {k: {"pedidos": v, "monto": sum((o["amount_total"] or 0.0) for o in orders if o["name"] in v)}
                  for k, v in pedidos_de.items() if k in act_ids}

    # 4) Calidad del dato (solo lectura): historial de compras previas, fechas y homonimos
    fact_pids = sorted({v["partner_id"] for v in facturas.values() if v["partner_id"]})
    fam = {}  # pid -> ids de la misma ficha (contacto + empresa)
    for pid in fact_pids:
        cp = (partners.get(pid) or {}).get("commercial_partner_id")
        fam[pid] = sorted({pid, cp[0]} if cp else {pid})
    all_ids = sorted({i for v in fam.values() for i in v})
    prev = oc.search_read("sale.order",
        [("x_status_compra", "=", "4"), ("commitment_date", "<", lg), ("partner_id", "in", all_ids)],
        ["partner_id", "commitment_date"]) if all_ids else []
    prev_by = {}
    for o in prev:
        k = o["partner_id"][0]
        d = to_local(o["commitment_date"]).date().isoformat() if o["commitment_date"] else ""
        x = prev_by.setdefault(k, {"n": 0, "primera": None})
        x["n"] += 1
        if d and (not x["primera"] or d < x["primera"]):
            x["primera"] = d
    names = sorted({(partners.get(p) or {}).get("name") for p in fact_pids} - {None})
    homo = {}
    if names:
        for p in oc.search_read("res.partner", [("name", "in", names)], ["name", "x_fecha_activacion"]):
            h = homo.setdefault(p["name"], {"n": 0, "con_fecha": 0})
            h["n"] += 1
            h["con_fecha"] += 1 if p.get("x_fecha_activacion") else 0
    calidad = {}
    for pid in fact_pids:
        pv = [prev_by[i] for i in fam[pid] if i in prev_by]
        nm = (partners.get(pid) or {}).get("name")
        calidad[str(pid)] = {"compras_previas": sum(x["n"] for x in pv),
                             "primera_compra": min([x["primera"] for x in pv if x["primera"]], default=""),
                             "homonimos": (homo.get(nm) or {}).get("n", 1),
                             "homonimos_con_fecha": (homo.get(nm) or {}).get("con_fecha", 0)}
    for o in orders:
        if o["name"] in facturas:
            facturas[o["name"]]["fecha_pedido"] = to_local(o["commitment_date"]).date().isoformat() if o["commitment_date"] else ""

    def fila(a):
        fa, fr = to_local(a.get("x_fecha_activacion")), to_local(a.get("x_fecha_resolucion_final"))
        ped = pedidos_de.get(a["id"], [])
        return {"id": a["id"], "cliente": a["name"],
                "fecha_act": fa.date().isoformat() if fa else "",
                "fecha_aprob": fr.date().isoformat() if fr else "",
                "linea_activa": bool(a.get("x_activacion_linea")),
                "act_mes": bool(a.get("x_activacion_linea") and fa and lo <= fa < hi),
                "status": a.get("x_status_expediente") or "",
                "ejecutivo": a["user_id"][1] if a.get("user_id") else "Sin asignar",
                "facturado": bool(ped), "pedidos": ped,
                "monto": round(sum((o["amount_total"] or 0.0) for o in orders if o["name"] in ped), 2)}

    activados = sorted((fila(a) for a in act), key=lambda x: (not x["facturado"], x["fecha_act"], x["cliente"]))
    aprobadas = sorted((fila(a) for a in apr), key=lambda x: (not x["act_mes"], not x["facturado"], x["fecha_aprob"], x["cliente"]))
    sin_linea = sorted((fila(a) for a in fecha_sin_linea), key=lambda x: (x["status"], x["cliente"]))
    try:
        sel = dict(oc.execute_kw("res.partner", "fields_get", [["x_status_expediente"]],
                                 {"attributes": ["selection"]})["x_status_expediente"]["selection"])
    except Exception:
        sel = {}

    return {"mes": f"{year:04d}-{month:02d}",
            "generado": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
            "criterio": {"activacion": "x_fecha_activacion en el mes y x_activacion_linea = True",
                         "aprobacion": "x_fecha_resolucion_final en el mes"},
            "status_labels": sel,
            "total_activados": len(activados),
            "activados_facturados": sum(1 for a in activados if a["facturado"]),
            "total_aprobadas": len(aprobadas),
            "facturas": facturas,
            "activados": activados,
            "aprobadas": aprobadas,
            "fecha_sin_linea": sin_linea,
            "calidad": calidad}


def inject(data, var):
    line = f"const {var} = " + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";"
    s = io.open(HTML, encoding="utf-8", newline="").read()
    m = re.search(rf"^const {var} = .*?;[ \t]*\r?$", s, re.M)
    if m:
        s = s[:m.start()] + line + ("\r" if m.group(0).endswith("\r") else "") + s[m.end():]
    else:
        m2 = re.search(r"^const MES_OCT = ", s, re.M)
        if not m2:
            raise SystemExit("No se encontro `const MES_OCT = ` para insertar antes")
        nl = "\r\n" if "\r\n" in s else "\n"
        s = s[:m2.start()] + line + nl + s[m2.start():]
    io.open(HTML, "w", encoding="utf-8", newline="").write(s)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int); ap.add_argument("month", type=int)
    ap.add_argument("--inject", action="store_true")
    ap.add_argument("--var", default="ACT_OCT")
    a = ap.parse_args()
    d = build(erp.connect(), a.year, a.month)
    out = os.path.join(HERE, f"activaciones_{a.year:04d}-{a.month:02d}.json")
    json.dump(d, io.open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    fx = d["facturas"]
    print(f"{d['mes']}: activados={d['total_activados']} activados_facturados={d['activados_facturados']} "
          f"pedidos={len(fx)} pedidos_de_activados_mes={sum(1 for v in fx.values() if v['act_mes'])} -> {out}")
    if a.inject:
        inject(d, a.var)
        print(f"index.html: const {a.var} actualizado")
