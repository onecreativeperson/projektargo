#!/usr/bin/env python3
"""Projekt Argo – LinkedIn company page cover (2256x382 = 2x 1128x191). Usage: python3 li/cover.py light|dark out.jpg"""
import os, sys
from playwright.sync_api import sync_playwright
HERE = os.path.dirname(os.path.abspath(__file__))
theme = sys.argv[1] if len(sys.argv) > 1 else "light"
out = sys.argv[2] if len(sys.argv) > 2 else "cover.jpg"
L = dict(base="#ECEEFB", w1="#BDB6FF", w2="#FFC9B8", w3="#ACEBD6", w4="#B9DDFF", ink="#1D1D1F", ink2="#6A6A70",
         head="linear-gradient(180deg,#1D1D1F 0%,#2E2C52 100%)", acc="linear-gradient(135deg,#2A78F4,#0A5FE0 55%,#4636D2)")
D = dict(base="#08080F", w1="#3B2F9E", w2="#6E2A5E", w3="#0E5A57", w4="#1C3C8C", ink="#F5F5F7", ink2="#A1A1A8",
         head="linear-gradient(180deg,#FFFFFF 0%,#D6D3FF 100%)", acc="linear-gradient(135deg,#6FA8FF,#3D8BFF 50%,#8A6CFF)")
t = D if theme == "dark" else L
html = f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{{font-family:Inter;font-weight:100 900;src:url(fonts/Inter-latin.woff2) format("woff2");unicode-range:U+0000-00FF,U+2000-206F}}
@font-face{{font-family:Inter;font-weight:100 900;src:url(fonts/Inter-latinext.woff2) format("woff2");unicode-range:U+0100-02BA}}
html,body{{margin:0;width:2256px;height:382px;overflow:hidden;font-family:Inter,sans-serif;-webkit-font-smoothing:antialiased}}
.s{{position:relative;width:2256px;height:382px;background:{t['base']};overflow:hidden}}
.s i{{position:absolute;border-radius:50%;filter:blur(110px);opacity:.95}}
.b1{{width:1000px;height:1000px;left:-200px;top:-560px;background:{t['w1']}}}
.b2{{width:1000px;height:1000px;left:700px;top:-640px;background:{t['w2']}}}
.b3{{width:1100px;height:1100px;left:1200px;top:-120px;background:{t['w4']}}}
.b4{{width:900px;height:900px;left:200px;top:120px;background:{t['w3']}}}
.g{{position:absolute;inset:0;opacity:.14;mix-blend-mode:overlay;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.9'/%3E%3C/svg%3E")}}
.c{{position:absolute;right:150px;top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;align-items:flex-end;text-align:right}}
h1{{margin:0;font-size:104px;font-weight:800;letter-spacing:-.045em;line-height:1;background:{t['head']};-webkit-background-clip:text;background-clip:text;color:transparent}}
h1 em{{font-style:normal;background:{t['acc']};-webkit-background-clip:text;background-clip:text;color:transparent}}
p{{margin:26px 0 0;font-size:38px;font-weight:600;letter-spacing:-.01em;color:{t['ink2']}}}
</style></head><body><div class="s"><i class="b1"></i><i class="b2"></i><i class="b3"></i><i class="b4"></i><div class="g"></div>
<div class="c"><h1>From idea to <em>finished product.</em></h1><p>Product design × AI · Small engines for boring problems · projektargo.com</p></div></div></body></html>"""
tmp = os.path.join(HERE, "_cover.html"); open(tmp, "w", encoding="utf-8").write(html)
with sync_playwright() as p:
    b = p.chromium.launch(); pg = b.new_page(viewport={"width": 2256, "height": 382})
    pg.goto("file://" + tmp); pg.evaluate("document.fonts.ready")
    ok = pg.evaluate("document.fonts.check('800 100px Inter')")
    pg.screenshot(path=out, type="jpeg", quality=92); b.close()
os.remove(tmp); print(out, "fontsOk", ok)
