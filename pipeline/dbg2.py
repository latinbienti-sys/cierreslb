# -*- coding: utf-8 -*-
import io
p = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html"
s = io.open(p, encoding="utf-8").read()
print("count 'const DATA =':", s.count("const DATA ="))
print("count 'const MES =':", s.count("const MES ="))
print("old acum 431184.04:", s.count("431184.04"))
print("new acum 336642.46:", s.count("336642.46"))
print("new tend facturado 34524.42:", s.count("34524.42"))
print("lines:", s.count(chr(10)))
