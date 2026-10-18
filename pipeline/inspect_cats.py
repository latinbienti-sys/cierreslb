# -*- coding: utf-8 -*-
import io, json
HTML = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html"
s = io.open(HTML, encoding="utf-8").read()
def find_obj(t, start):
    i, depth, instr, esc = start, 0, False, False
    while i < len(t):
        c = t[i]
        if instr:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"': instr = False
        else:
            if c == '"': instr = True
            elif c in "{[" : depth += 1
            elif c in "}]":
                depth -= 1
                if depth == 0: return i + 1
        i += 1
    return -1
i = s.index("const DATA =")
b = s.index("{", i)
DATA = json.loads(s[b:find_obj(s, b)])
print("DATA keys:", list(DATA.keys()))
cats = DATA.get("categorias")
print("categorias tipo:", type(cats).__name__)
if isinstance(cats, dict):
    print("  keys:", list(cats.keys()))
    for k, v in cats.items():
        print("   ", k, "->", (list(v[0].keys()) if isinstance(v, list) and v else v))
    arr = cats.get("categorias") or cats.get("rows") or next((v for v in cats.values() if isinstance(v, list)), [])
else:
    arr = cats or []
print("n=", len(arr))
tot = sum(float(x.get("monto", 0)) for x in arr)
print("suma monto:", round(tot, 2))
for x in arr[:15]:
    print("   ", x)
# tambien buscar const CATS
if "const CATS" in s:
    j = s.index("const CATS"); jb = s.index("{", j); je = s.index(";", jb)
    print("const CATS def:", s[jb:je][:200])
