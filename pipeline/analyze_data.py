# -*- coding: utf-8 -*-
import io, re, json

p = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html"
s = io.open(p, encoding="utf-8").read()

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

m = re.search(r"const DATA =", s)
dstart = s.index("{", m.end())
dend = find_obj(s, dstart)
data_txt = s[dstart:dend]
print("DATA text len:", len(data_txt))

# escaner de claves de primer nivel
def top_keys(t):
    keys, i, depth, instr, esc = [], 0, 0, False, False
    cur_key = None; key_start = None
    while i < len(t):
        c = t[i]
        if instr:
            if esc: esc = False
            elif c == "\\": esc = True
            elif c == '"':
                instr = False
                if depth == 1 and cur_key is None:
                    cur_key = t[key_start+1:i]
        else:
            if c == '"':
                instr = True; key_start = i
            elif c == "{":
                depth += 1
                if depth == 1 and cur_key is not None: cur_key = None
            elif c == "}":
                depth -= 1
            elif c == ":" and depth == 1 and cur_key is not None:
                keys.append((cur_key, i+1))
                cur_key = None
        i += 1
    return keys

for k in ("facturacion_agosto","categorias","septiembre","segment_stats","morosidad","tendencia"):
    print(f'  "{k}":', data_txt.count('"%s":' % k))
print("json.loads keys:", list(json.loads(data_txt).keys()))
# valor de la ULTIMA tendencia (la que usa el sitio)
print("ultima tendencia rows:", [r["key"] for r in json.loads(data_txt)["tendencia"]["rows"]])
