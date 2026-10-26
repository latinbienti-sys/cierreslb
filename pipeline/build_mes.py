# -*- coding: utf-8 -*-
"""Genera la estructura de un mes (pestana tipo 'Septiembre 2026') desde Odoo.
Regla (favorito): x_status_compra=4, mes por commitment_date en tz Caracas (UTC-4).
Solo lectura. Uso:  python build_mes.py 2026 10  -> escribe mes_2026-10.json
"""
import sys, json, unicodedata, argparse
from datetime import datetime, timedelta, timezone
from collections import defaultdict
import erp
TZ = timezone(timedelta(hours=-4))
ADMIN_NAME = "gasto administrativo y gestion de cobranza"
STATUS_LABEL = {"6": "Entregado", "8": "Cancelación Total", "12": "Congelado (Entregado)",
                "0": "Presupuesto", "4": "Aprobado", "11": "Cambio de Plan",
                "5": "Negado - Retiro", "7": "Retirado Devolución", "9": "Exclusión por Mora",
                "10": "Anulado", "1": "Por Completar", "2": "Análisis AAC", "3": "Comité"}

def norm(x):
    x = unicodedata.normalize("NFKD", str(x or ""))
    return "".join(c for c in x if not unicodedata.combining(c)).lower().strip()

def connect():
    return erp.connect()

def build_month(oc, year, month):
    lo = datetime(year, month, 1, 0, 0, tzinfo=TZ)
    hi = datetime(year + (month // 12), (month % 12) + 1, 1, 0, 0, tzinfo=TZ)
    lg, hg = lo.astimezone(timezone.utc), hi.astimezone(timezone.utc)
    dom = [("x_status_compra", "=", "4"),
           ("commitment_date", ">=", lg.strftime("%Y-%m-%d %H:%M:%S")),
           ("commitment_date", "<", hg.strftime("%Y-%m-%d %H:%M:%S"))]
    orders = oc.search_read("sale.order", dom,
        ["name", "amount_total", "order_line", "partner_id", "user_id",
         "x_status_operativos", "commitment_date"])
    allids = [i for o in orders for i in o["order_line"]]
    lines = oc.search_read("sale.order.line", [("id", "in", allids)],
        ["order_id", "product_id", "product_uom_qty", "price_subtotal", "purchase_price"])

    # id del producto administracion
    admin_ids = set()
    for l in lines:
        if l["product_id"] and norm(l["product_id"][1]) == ADMIN_NAME:
            admin_ids.add(l["product_id"][0])

    per = defaultdict(lambda: {"admin": 0.0, "costo": 0.0})
    prod_agg = defaultdict(lambda: {"cantidad": 0.0, "monto": 0.0})
    for l in lines:
        oid = l["order_id"][0]
        pid = l["product_id"][0] if l["product_id"] else None
        nm = l["product_id"][1] if l["product_id"] else "Producto"
        sub = l["price_subtotal"] or 0.0
        qty = l["product_uom_qty"] or 0.0
        if pid in admin_ids:
            per[oid]["admin"] += sub
        else:
            per[oid]["costo"] += (l["purchase_price"] or 0.0) * qty
        prod_agg[nm]["cantidad"] += qty
        prod_agg[nm]["monto"] += sub

    facturas, ejec_agg, clientes, cancel_n, cancel_m = [], defaultdict(
        lambda: {"facturado": 0.0, "costo": 0.0, "facturas": 0, "unidades": 0}), set(), 0, 0.0
    for o in orders:
        oid = o["id"]
        ops = (o["x_status_operativos"] or "").split(".")[0].strip()
        status = STATUS_LABEL.get(ops, "Entregado")
        cdt = o["commitment_date"]
        d = datetime.fromisoformat(cdt).replace(tzinfo=timezone.utc).astimezone(TZ).date().isoformat() if cdt else ""
        cliente = o["partner_id"][1] if o["partner_id"] else "Cliente"
        ejecutivo = o["user_id"][1] if o["user_id"] else "Sin asignar"
        costo = round(per[oid]["costo"], 2)
        admin = round(per[oid]["admin"], 2)
        monto = round(o["amount_total"], 2)
        facturas.append({"orden": o["name"], "cliente": cliente, "ejecutivo": ejecutivo,
                         "monto": monto, "costo": costo, "admin": admin,
                         "status": status, "fecha": d})
        clientes.add(cliente)
        ejec_agg[ejecutivo]["facturado"] += monto
        ejec_agg[ejecutivo]["costo"] += costo
        ejec_agg[ejecutivo]["facturas"] += 1
        # unidades: cantidad de lineas no-admin
        for l in lines:
            if l["order_id"][0] == oid and (l["product_id"][0] if l["product_id"] else None) not in admin_ids:
                ejec_agg[ejecutivo]["unidades"] += l["product_uom_qty"] or 0
        if ops == "8":
            cancel_n += 1
            cancel_m += monto

    total_facturado = round(sum(f["monto"] for f in facturas), 2)
    total_admin = round(sum(f["admin"] for f in facturas), 2)
    total_costo = round(sum(f["costo"] for f in facturas), 2)
    ejecutivos = [{"nombre": k, "facturado": round(v["facturado"], 2), "costo": round(v["costo"], 2),
                   "margen": round(v["facturado"] - v["costo"], 2), "facturas": v["facturas"],
                   "unidades": v["unidades"]} for k, v in ejec_agg.items()]
    ejecutivos.sort(key=lambda e: e["facturado"], reverse=True)
    top_productos = [{"nombre": k, "cantidad": round(v["cantidad"], 2) if v["cantidad"] % 1 else int(v["cantidad"]),
                      "monto": round(v["monto"], 2)} for k, v in prod_agg.items()]
    top_productos.sort(key=lambda p: p["monto"], reverse=True)

    return {
        "mes": f"{year:04d}-{month:02d}",
        "facturas": sorted(facturas, key=lambda f: f["fecha"], reverse=True),
        "facturas_dscto": [],
        "ejecutivos": ejecutivos,
        "top_productos": top_productos,
        "total_facturado": total_facturado,
        "total_facturas": len(facturas),
        "total_clientes": len(clientes),
        "total_productos": round(total_facturado - total_admin, 2),
        "total_admin": total_admin,
        "total_admin_dscto": 0.0,
        "total_ahorro_dscto": 0.0,
        "total_costo": total_costo,
        "total_margen": round(total_facturado - total_costo, 2),
        "cancelaciones_count": cancel_n,
        "cancelaciones_monto": round(cancel_m, 2),
        "total": total_facturado,
        "count": len(facturas),
        "colaboradores": [],
    }

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int); ap.add_argument("month", type=int)
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    oc = connect()
    data = build_month(oc, a.year, a.month)
    out = a.out or f"mes_{a.year:04d}-{a.month:02d}.json"
    json.dump(data, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(f"{a.year}-{a.month:02d}: facturas={data['total_facturas']} facturado={data['total_facturado']} "
          f"admin={data['total_admin']} costo={data['total_costo']} -> {out}")
