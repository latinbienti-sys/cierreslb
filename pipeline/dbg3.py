# -*- coding: utf-8 -*-
import io
p = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html"
s = io.open(p, encoding="utf-8").read()
print("count '\"tendencia\"':", s.count('"tendencia"'))
print("count '\"rows\"':", s.count('"rows"'))
print("count '\"acumulado\"':", s.count('"acumulado"'))
import re
idx = [m.start() for m in re.finditer(re.escape("431184.04"), s)]
print("431184.04 idxs (first 5):", idx[:5], "... total", len(idx))
print("around first:", s[idx[0]-80:idx[0]+30])
print("around last:", s[idx[-1]-60:idx[-1]+30])
