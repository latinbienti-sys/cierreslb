# -*- coding: utf-8 -*-
import io, re, json
s = io.open(r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html", encoding="utf-8").read()

def obj_after(key):
    i = s.index(key); b = s.index("[", i)
    depth = 0; j = b; instr = False; esc = False
    while j < len(s):
        c = s[j]
        if instr:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': instr = False
        else:
            if c == '"': instr = True
            elif c == "[": depth += 1
            elif c == "]":
                depth -= 1
                if depth == 0: return json.loads(s[b:j+1])
        j += 1
    raise SystemExit("no cerrado: " + key)

sept = obj_after('"categorias":')
oct_ = obj_after("const CATS_OCT =")
print("DATA.categorias (Sept): filas=%d suma=%.2f  [esperado 12 / 92539.89]" % (len(sept), sum(c["monto"] for c in sept)))
print("CATS_OCT (Octubre):     filas=%d suma=%.2f" % (len(oct_), sum(c["monto"] for c in oct_)))
print("filtro cat:", all(x in s for x in ('class="tab-btn active cat-mes-btn"', "setCatMes('oct'", "function renderCategorias", "id=\"cat-chart-mes\"")))
print("filtro tec:", all(x in s for x in ('class="tab-btn active tec-mes-btn"', "setTecMes('oct'", "function renderTecnologia")))
print("tabs:", s.count('class="tab-btn"') + s.count('tab-btn active'))
