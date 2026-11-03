# -*- coding: utf-8 -*-
"""Flujo de cuotas de lo FACTURADO en un mes: inicial y cuotas por factura (recibido vs por cobrar).

SOLO LECTURA en Odoo (search_read/read). No escribe nada en Odoo.
Pedidos = los mismos del cierre del mes (pipeline/mes_YYYY-MM.json, regla build_mes).
Cuotas  = invoice.installment.line de la factura publicada (account.move out_invoice, state=posted).
          is_installment=False -> PAGO INICIAL ; state: paid / draft (Due) / vencido.
Si un pedido tiene mas de una factura publicada (duplicado), se toma solo la mas reciente y se reporta.

Uso:
  python build_flujo_mes.py 2026 10            -> guarda flujo_2026-10.json
  python build_flujo_mes.py 2026 10 --inject   -> ademas reemplaza/inserta `const FLUJO_OCT = ...;` en index.html
"""
import io, os, re, sys, json, argparse
from datetime import datetime, timedelta, timezone
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import erp

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(os.path.dirname(HERE), "index.html")
TZ = timezone(timedelta(hours=-4))
EST = {"paid": "P", "draft": "D", "vencido": "V"}


def build(oc, year, month):
    mes = json.load(io.open(os.path.join(HERE, f"mes_{year:04d}-{month:02d}.json"), encoding="utf-8"))
    cierre = {f["orden"]: f for f in mes["facturas"]}
    orders = oc.search_read("sale.order", [("name", "in", list(cierre))],
                            ["name", "invoice_ids", "tenure", "tenure_plan", "x_monto_inicial"])
    inv = {i["id"]: i for i in oc.read("account.move", [i for o in orders for i in o["invoice_ids"]],
                                        ["name", "state", "move_type", "amount_total", "installment_ids"])}
    lids = [x for i in inv.values() if i["state"] == "posted" and i["move_type"] == "out_invoice"
            for x in i["installment_ids"]]
    L = {l["id"]: l for l in oc.read("invoice.installment.line", lids,
                                      ["amount", "index", "payment_date", "state", "is_installment"])}
    out, duplicadas = [], []
    for o in orders:
        pos = sorted([inv[i] for i in o["invoice_ids"]
                      if inv[i]["state"] == "posted" and inv[i]["move_type"] == "out_invoice"],
                     key=lambda i: i["id"])
        if len(pos) > 1:
            duplicadas.append({"orden": o["name"], "facturas": [i["name"] for i in pos],
                               "montos": [i["amount_total"] for i in pos]})
        fac = pos[-1] if pos else None
        lines = sorted((L[x] for x in (fac["installment_ids"] if fac else []) if x in L),
                       key=lambda l: (l["index"], l["payment_date"] or ""))
        ini = [l for l in lines if not l["is_installment"]]
        cuo = [l for l in lines if l["is_installment"]]
        out.append({
            "orden": o["name"],
            "factura": fac["name"] if fac else "",
            "plan": o.get("tenure_plan") or "",
            "inicial": round(sum(l["amount"] for l in ini), 2),
            "inicial_cobrado": round(sum(l["amount"] for l in ini if l["state"] == "paid"), 2),
            "inicial_fecha": (ini[0]["payment_date"] or "") if ini else "",
            # cuotas: [fecha_vencimiento, monto, estado P/D/V]
            "cuotas": [[l["payment_date"] or "", round(l["amount"], 2), EST.get(l["state"], l["state"])] for l in cuo],
        })
    return {"mes": f"{year:04d}-{month:02d}",
            "generado": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
            "hoy": datetime.now(TZ).date().isoformat(),
            "facturas": out,
            "duplicadas": duplicadas}


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
    ap.add_argument("--var", default="FLUJO_OCT")
    a = ap.parse_args()
    d = build(erp.connect(), a.year, a.month)
    out = os.path.join(HERE, f"flujo_{a.year:04d}-{a.month:02d}.json")
    json.dump(d, io.open(out, "w", encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)
    F = d["facturas"]
    cob = sum(f["inicial_cobrado"] for f in F) + sum(c[1] for f in F for c in f["cuotas"] if c[2] == "P")
    pend = sum(c[1] for f in F for c in f["cuotas"] if c[2] != "P") + sum(f["inicial"] - f["inicial_cobrado"] for f in F)
    print(f"{d['mes']}: pedidos={len(F)} cuotas={sum(len(f['cuotas']) for f in F)} cobrado={cob:.2f} "
          f"por_cobrar={pend:.2f} duplicadas={len(d['duplicadas'])} -> {out}")
    if a.inject:
        inject(d, a.var)
        print(f"index.html: const {a.var} actualizado")
