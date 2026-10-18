# -*- coding: utf-8 -*-
"""Actualizacion HORARIA del tablero Cierre LB (mes en curso).

Regenera, para el mes actual (America/Caracas):
  - const MES        (pestana "Mes en curso")        -> update_mes.py
  - const TECNO_OCT  (Cartera/Tecnologia, facturacion) -> update_tecnologia.py
  - const CATS_OCT   (Categorias)                    -> update_categorias.py
y, si hubo cambios, hace commit + push a origin/main.

SOLO LECTURA en Odoo. Pensado para ejecutarse desde el Programador de tareas.

Uso:
  python update_hourly.py
"""
import os, sys, subprocess
from datetime import datetime, timezone, timedelta

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
PY = sys.executable
TZ = timezone(timedelta(hours=-4))

def log(msg):
    print(f"[{datetime.now(TZ).strftime('%Y-%m-%d %H:%M:%S')}] {msg}", flush=True)

def run(script, *args):
    log(f"-> {script} {' '.join(args)}")
    r = subprocess.run([PY, "-X", "utf8", os.path.join(HERE, script), *args],
                       cwd=REPO, capture_output=True, text=True)
    if r.stdout.strip():
        log(r.stdout.strip())
    if r.returncode != 0:
        log(f"ERROR en {script} (rc={r.returncode}): {r.stderr.strip()}")
        return False
    return True

def git(*args):
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True)

def main():
    ok = True
    ok &= run("update_mes.py")
    ok &= run("update_tecnologia.py")
    ok &= run("update_categorias.py")
    if not ok:
        log("Actualizacion Odoo incompleta; no se hace commit.")
        return 1

    st = git("status", "--porcelain")
    if not st.stdout.strip():
        log("Sin cambios; nada que commitear.")
        return 0

    git("add", "-A")
    ts = datetime.now(TZ).strftime("%Y-%m-%d %H:%M")
    c = git("commit", "-m", f"auto: actualizacion horaria {ts}")
    log((c.stdout or c.stderr).strip())
    p = git("push", "origin", "HEAD")
    log(f"push rc={p.returncode} {(p.stdout or p.stderr).strip()}")
    return 0 if p.returncode == 0 else 1

if __name__ == "__main__":
    raise SystemExit(main())
