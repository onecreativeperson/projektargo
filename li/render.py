#!/usr/bin/env python3
"""Projekt Argo – LinkedIn post image (1080x1350 PNG) in the projektargo.com design system.

Usage: python3 li/render.py spec.json
spec.json:
{
  "layout": "statement" | "list" | "compare",
  "kicker": "Thesis",                      # short label in the glass pill (max ~22 chars)
  "title": "Boring problems are the *best* problems.",   # hook; *word* = blue accent, \n = line break
  "sub": "optional one or two sentences",  # statement/list/compare, optional
  "items": ["point 1", "point 2", "point 3"],              # list: 2-3 items, each max ~70 chars
  "before": "...", "after": "...",                          # compare
  "before_label": "Before", "after_label": "After",         # compare labels (use SK for SK posts)
  "out": "posts/2026-11-04-thesis.png"
}
Exits 1 if fonts fail to load or the text cannot fit at the minimum size.
"""
import html, json, os, re, sys, tempfile
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

CSS = r"""
@font-face{font-family:"Inter";font-style:normal;font-weight:100 900;src:url(fonts/Inter-latin.woff2) format("woff2");
 unicode-range:U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD}
@font-face{font-family:"Inter";font-style:normal;font-weight:100 900;src:url(fonts/Inter-latinext.woff2) format("woff2");
 unicode-range:U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF}
:root{--ink:#1D1D1F;--ink2:#6A6A70;--tint:#0A5FE0;--w1:#BDB6FF;--w2:#FFC9B8;--w3:#ACEBD6;--w4:#B9DDFF;--base:#ECEEFB;--fs:120px;--ss:38px}
*{box-sizing:border-box}
html,body{margin:0;width:1080px;height:1350px;overflow:hidden;font-family:"Inter",sans-serif;-webkit-font-smoothing:antialiased;color:var(--ink);font-optical-sizing:auto}
.stage{position:relative;width:1080px;height:1350px;background:var(--base);overflow:hidden}
.wall i{position:absolute;border-radius:50%;filter:blur(120px);opacity:.95}
.b1{width:980px;height:980px;left:-300px;top:-330px;background:var(--w1)}
.b2{width:860px;height:860px;right:-320px;top:-240px;background:var(--w2)}
.b3{width:820px;height:820px;left:-160px;bottom:-380px;background:var(--w3)}
.b4{width:780px;height:780px;right:-240px;bottom:-320px;background:var(--w4)}
.grain{position:absolute;inset:0;opacity:.16;mix-blend-mode:overlay;background-image:url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='160' height='160'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='.9'/%3E%3C/svg%3E")}
.in{position:absolute;inset:88px;display:flex;flex-direction:column;overflow:hidden}
.top{display:flex;align-items:center;justify-content:space-between;gap:24px}
.pill{display:inline-flex;align-items:center;gap:12px;font:600 28px/1 "Inter";color:var(--tint);padding:16px 26px;border-radius:999px;
 background:linear-gradient(180deg,rgba(255,255,255,.97) 0%,rgba(255,255,255,.68) 46%,rgba(255,255,255,.46) 62%,rgba(255,255,255,.8) 100%);
 box-shadow:inset 0 1px 0 #fff,inset 0 -1px 0 rgba(255,255,255,.8),inset 0 -9px 14px -9px rgba(30,30,60,.14),0 0 0 .5px rgba(28,28,48,.09),0 10px 22px -12px rgba(28,28,48,.32)}
.pill b{width:12px;height:12px;border-radius:50%;background:var(--tint);box-shadow:0 0 0 5px rgba(10,95,224,.14)}
.name{font:600 30px/1 "Inter";color:var(--ink2);letter-spacing:-.01em}
.main{margin:auto 0;padding:40px 0 8px}
h1{margin:0;font-size:var(--fs);font-weight:800;line-height:1.02;letter-spacing:-.045em;
 background:linear-gradient(180deg,#1D1D1F 0%,#2E2C52 100%);-webkit-background-clip:text;background-clip:text;color:transparent}
h1 em{font-style:normal;background:linear-gradient(135deg,#2A78F4,#0A5FE0 55%,#4636D2);-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{margin:40px 0 0;font-size:var(--ss);font-weight:500;line-height:1.36;letter-spacing:-.015em;color:var(--ink2);max-width:880px}
.body{margin-top:52px;display:flex;flex-direction:column;gap:20px}
.card{display:flex;gap:26px;align-items:flex-start;padding:30px 34px;border-radius:36px;background:rgba(255,255,255,.6);
 border:1px solid rgba(255,255,255,.78);box-shadow:inset 0 1px 0 #fff,0 26px 50px -30px rgba(28,28,48,.38)}
.num{flex:0 0 56px;height:56px;border-radius:18px;display:grid;place-items:center;font:700 28px/1 "Inter";color:#fff;
 background:linear-gradient(180deg,rgba(255,255,255,.35),rgba(255,255,255,0) 55%),linear-gradient(135deg,#2A78F4,#0A5FE0 55%,#4636D2);
 box-shadow:inset 0 1px 0 rgba(255,255,255,.6),0 10px 20px -10px rgba(10,95,224,.6)}
.txt{font-size:calc(var(--ss) * .92);font-weight:600;line-height:1.3;letter-spacing:-.015em;color:var(--ink)}
.lab{font:700 22px/1 "Inter";letter-spacing:.06em;text-transform:uppercase;color:var(--ink2);margin-bottom:12px}
.card.after{background:rgba(255,255,255,.78)}
.card.after .lab{color:var(--tint)}
.card.before .txt{color:#4A4A50;text-decoration:line-through;text-decoration-color:rgba(106,106,112,.55);text-decoration-thickness:2px}
.foot{padding-top:24px;display:flex;align-items:center;gap:20px;font:600 30px/1 "Inter";color:var(--ink2)}
.foot img{width:72px;height:72px;filter:drop-shadow(0 10px 16px rgba(10,95,224,.35))}
"""

JS_FIT = r"""
async () => {
  await document.fonts.ready;
  const ok = document.fonts.check('800 100px "Inter"') && document.fonts.check('600 30px "Inter"');
  const inner = document.querySelector('.in');
  const root = document.documentElement;
  let fs = parseFloat(getComputedStyle(root).getPropertyValue('--fs'));
  let ss = parseFloat(getComputedStyle(root).getPropertyValue('--ss'));
  const fits = () => inner.scrollHeight <= inner.clientHeight + 1;
  while (!fits() && fs > 64) { fs -= 4; root.style.setProperty('--fs', fs + 'px'); }
  while (!fits() && ss > 28) { ss -= 2; root.style.setProperty('--ss', ss + 'px'); }
  return {fontsOk: ok, fits: fits(), fs, ss};
}
"""


def rich(t: str) -> str:
    t = html.escape(t.strip())
    t = re.sub(r"\*(.+?)\*", r"<em>\1</em>", t)
    return t.replace("\n", "<br>")


def build(spec: dict) -> str:
    layout = spec.get("layout", "statement")
    start = {"statement": 124, "list": 96, "compare": 96}.get(layout, 110)
    parts = [f'<div class="top"><span class="pill"><b></b>{html.escape(spec.get("kicker", "Projekt Argo"))}</span>'
             f'<span class="name">Štefan Toporcer</span></div>',
             '<div class="main">', f'<h1>{rich(spec["title"])}</h1>']
    if spec.get("sub"):
        parts.append(f'<p class="sub">{rich(spec["sub"])}</p>')
    if layout == "list":
        items = spec.get("items", [])[:3]
        cards = "".join(f'<div class="card"><span class="num">{i}</span><span class="txt">{rich(x)}</span></div>'
                        for i, x in enumerate(items, 1))
        parts.append(f'<div class="body">{cards}</div>')
    elif layout == "compare":
        bl, al = spec.get("before_label", "Before"), spec.get("after_label", "After")
        parts.append('<div class="body">'
                     f'<div class="card before"><div><div class="lab">{html.escape(bl)}</div><div class="txt">{rich(spec["before"])}</div></div></div>'
                     f'<div class="card after"><div><div class="lab">{html.escape(al)}</div><div class="txt">{rich(spec["after"])}</div></div></div>'
                     '</div>')
    parts.append('</div>')
    parts.append('<div class="foot"><img src="logo.svg" alt=""><span>Projekt Argo · projektargo.com</span></div>')
    return (f'<!doctype html><html lang="{html.escape(spec.get("lang", "en"))}"><head><meta charset="utf-8">'
            f'<style>{CSS}</style><style>:root{{--fs:{start}px}}</style></head><body><div class="stage">'
            '<div class="wall"><i class="b1"></i><i class="b2"></i><i class="b3"></i><i class="b4"></i></div>'
            f'<div class="grain"></div><div class="in">{"".join(parts)}</div></div></body></html>')


def main():
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = spec.get("out") or "posts/out.png"
    out = out if os.path.isabs(out) else os.path.join(ROOT, out)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".html", dir=HERE)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.write(build(spec))
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1080, "height": 1350}, device_scale_factor=1)
            pg.goto("file://" + tmp)
            res = pg.evaluate(JS_FIT)
            pg.screenshot(path=out, clip={"x": 0, "y": 0, "width": 1080, "height": 1350})
            b.close()
    finally:
        os.remove(tmp)
    print(json.dumps({"out": out, **res}))
    if not (res["fontsOk"] and res["fits"]):
        sys.exit(1)


if __name__ == "__main__":
    main()
