# -*- coding: utf-8 -*-
import io, re, json
s = io.open(r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html", encoding="utf-8").read()
DATA = json.loads(re.search(r"const DATA =(\{.*?\});\n", s, re.DOTALL).group(1))
T = DATA["tendencia"]
print("tendencia keys:", list(T.keys()))
print("rows:", len(T["rows"]))
for r in T["rows"]:
    print("  ", json.dumps(r, ensure_ascii=False))
print("actual:", json.dumps(T.get("actual"), ensure_ascii=False))
print("anterior:", json.dumps(T.get("anterior"), ensure_ascii=False))
print("acumulado:", json.dumps(T.get("acumulado"), ensure_ascii=False))
print("mejor:", json.dumps(T.get("mejor"), ensure_ascii=False))
