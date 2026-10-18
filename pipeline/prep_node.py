# -*- coding: utf-8 -*-
"""Extrae el <script> inline principal de index.html y valida con node --check."""
import io, re, subprocess, sys

HTML = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\index.html"
JS = r"C:\Users\yarleyc\AppData\Local\Temp\opencode\cierreslb\main_script.js"
s = io.open(HTML, encoding="utf-8").read()
blocks = re.findall(r"<script>(.*?)</script>", s, re.DOTALL)
inline = max(blocks, key=len)
io.open(JS, "w", encoding="utf-8").write(inline)
print(f"bloques={len(blocks)} mayor={len(inline)} chars -> {JS}")
r = subprocess.run(["node", "--check", JS], capture_output=True, text=True)
print("node --check:", "SYNTAX OK" if r.returncode == 0 else "ERROR")
if r.returncode != 0:
    print(r.stdout); print(r.stderr); sys.exit(1)
