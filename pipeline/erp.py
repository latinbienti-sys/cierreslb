# -*- coding: utf-8 -*-
"""Acceso al ERP de forma portatil (tarea Windows local y GitHub Actions).

Resolucion de credenciales, en orden:
  1) Variables de entorno: ODOO_URL, ODOO_DB, ODOO_USER, ODOO_API_KEY  (usadas en Actions)
  2) Archivo ODOO_CONFIG (ruta a config.json)
  3) config.json local de Windows (tarea programada de la laptop)

SOLO LECTURA en Odoo (OdooClient bloquea toda escritura).
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))

# Prioridad para importar odoo_client: copia dentro del repo > carpeta local de Windows.
if os.path.isfile(os.path.join(HERE, "odoo_client.py")):
    sys.path.insert(0, HERE)
LOCAL_DIR = r"C:\Users\yarleyc\Desktop\crmlatinbien"
if os.path.isdir(LOCAL_DIR) and LOCAL_DIR not in sys.path:
    sys.path.append(LOCAL_DIR)

from odoo_client import OdooClient  # noqa: E402

DEFAULT_LOCAL_CONFIG = os.path.join(LOCAL_DIR, "config.json")


def odoo_config():
    env = {k: (os.environ.get(k) or "").strip()
           for k in ("ODOO_URL", "ODOO_DB", "ODOO_USER", "ODOO_API_KEY")}
    if all(env.values()):
        return {"url": env["ODOO_URL"], "db": env["ODOO_DB"],
                "user": env["ODOO_USER"], "api_key": env["ODOO_API_KEY"]}
    for path in (os.environ.get("ODOO_CONFIG"), DEFAULT_LOCAL_CONFIG):
        if path and os.path.isfile(path):
            return json.load(open(path, encoding="utf-8"))["odoo"]
    raise SystemExit("Credenciales Odoo no encontradas: exporta ODOO_URL, ODOO_DB, ODOO_USER, "
                     "ODOO_API_KEY o define ODOO_CONFIG=<ruta a config.json>.")


def connect():
    cfg = odoo_config()
    return OdooClient(cfg["url"], cfg["db"], cfg["user"], cfg["api_key"]).connect()
