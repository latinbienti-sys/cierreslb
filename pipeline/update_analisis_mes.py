# -*- coding: utf-8 -*-
"""Genera los datos de la pestana "Analisis por Mes" para un mes (SOLO LECTURA en Odoo).

Por mes se inyectan en index.html tres constantes (sufijo = mes en 3 letras):
  MES_<XXX>    facturas del mes (regla build_mes: x_status_compra=4, commitment_date en el mes)
  ACT_<XXX>    lineas de credito aprobadas/activadas vs facturado (build_activaciones)
  FLUJO_<XXX>  inicial y cuotas de cada factura (build_flujo_mes)

No toca `const MES` (pestana "Mes en curso") ni la tarea horaria.
Si MES_<XXX> ya existe (p. ej. MES_OCT, cierre ajustado a mano), NO se reemplaza salvo --forzar-mes;
en ese caso ACT/FLUJO se calculan contra ese cierre existente.

Uso:
  python update_analisis_mes.py 2026 11 --forzar-mes   -> noviembre desde Odoo (MES_NOV, ACT_NOV, FLUJO_NOV)
  python update_analisis_mes.py 2026 12 --forzar-mes   -> diciembre (MES_DIC, ACT_DIC, FLUJO_DIC)
  python update_analisis_mes.py 2027 1 --forzar-mes    -> enero 2027 (MES_ENE27, ...)
  Octubre 2026 esta CONGELADO: el script se niega a actualizarlo.
  La pestana "Analisis por Mes" muestra automaticamente cada mes que tenga sus 3 constantes.
"""
import io, os, re, sys, json, argparse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import erp, build_mes, build_activaciones, build_flujo_mes

HERE = os.path.dirname(os.path.abspath(__file__))
HTML = os.path.join(os.path.dirname(HERE), "index.html")
SUF = ["ENE", "FEB", "MAR", "ABR", "MAY", "JUN", "JUL", "AGO", "SEPT", "OCT", "NOV", "DIC"]


def read_const(name):
    s = io.open(HTML, encoding="utf-8", newline="").read()
    m = re.search(rf"^const {name} = (.*?);[ \t]*\r?$", s, re.M)
    return json.loads(m.group(1)) if m else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("year", type=int); ap.add_argument("month", type=int)
    ap.add_argument("--forzar-mes", action="store_true", help="regenerar MES_<XXX> aunque ya exista")
    a = ap.parse_args()
    # 2026 -> OCT, NOV, DIC ; otros años -> ENE27, FEB27, ... (la pestaña los detecta con la misma regla)
    suf = SUF[a.month - 1] + ("" if a.year == 2026 else f"{a.year % 100:02d}")
    if (a.year, a.month) == (2026, 10):
        raise SystemExit("Octubre 2026 esta congelado (MES_OCT/ACT_OCT/FLUJO_OCT). No se actualiza.")
    oc = erp.connect()

    mes_var = f"MES_{suf}"
    mes = None if a.forzar_mes else read_const(mes_var)
    if mes is None:
        mes = build_mes.build_month(oc, a.year, a.month)
        build_activaciones.inject(mes, mes_var)
        print(f"{mes_var}: generado ({mes['total_facturas']} facturas, {mes['total_facturado']})")
    else:
        print(f"{mes_var}: se respeta el existente ({len(mes['facturas'])} facturas)")

    act = build_activaciones.build(oc, a.year, a.month)
    build_activaciones.inject(act, f"ACT_{suf}")
    print(f"ACT_{suf}: aprobadas={act['total_aprobadas']} activadas={act['total_activados']}")

    fl = build_flujo_mes.build(oc, a.year, a.month, mes=mes)
    build_activaciones.inject(fl, f"FLUJO_{suf}")
    print(f"FLUJO_{suf}: facturas={len(fl['facturas'])} duplicadas={len(fl['duplicadas'])}")

    for nm, d in (("activaciones", act), ("flujo", fl)):
        json.dump(d, io.open(os.path.join(HERE, f"{nm}_{a.year:04d}-{a.month:02d}.json"), "w",
                             encoding="utf-8", newline="\n"), ensure_ascii=False, indent=1)


if __name__ == "__main__":
    main()
