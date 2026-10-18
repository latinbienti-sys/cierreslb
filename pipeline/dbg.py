# -*- coding: utf-8 -*-
import io, re, os
p = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html"
print("size:", os.path.getsize(p), "mtime:", os.path.getmtime(p))
s = io.open(p, encoding="utf-8").read()
i = s.find('"tendencia"')
print("tendencia idx:", i)
print("snippet:", s[i:i+260])
print("count 2026-10 in file:", s.count("2026-10"))
