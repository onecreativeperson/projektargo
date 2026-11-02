#!/usr/bin/env python3
"""Motory – zverejnenie stránok motorov na projektargo.com.

Zdroj: tabuľka public.motor_pages v Supabase (zapisuje ju naplánovaná úloha „Motory – spúšťač“).
Pre každý riadok so stavom live zapíše <slug>/index.html, potom vygeneruje sitemap-motory.xml
a .github/motory-status.json (ok / chyba pre každý slug).

Bezpečnostné pravidlá:
- Nikdy nič nemaže (ani priečinky, ani riadky v sitemape motorov).
- Nikdy neprepíše priečinok hlavného webu: zapisuje len do priečinkov, ktoré ešte neexistujú
  alebo ktorých index.html už nesie značku MARK (stránka motora).
- Nedostupné Supabase = žiadna zmena (zverejnené stránky ostávajú).

Použitie:  python3 .github/motory_sync.py [--fixture rows.json] [--changed-out subor.txt]
"""
import argparse, datetime, json, pathlib, re, sys, time, urllib.request
from xml.sax.saxutils import escape

SUPABASE_URL = "https://asnpyrrdeauhkskkkmuc.supabase.co"
PUBLISHABLE_KEY = "sb_publishable_9Nwzk4Ql2WH1PCQZbNe5BQ_-8eVhBve"  # verejný kľúč, rovnaký ako na webe
SITE = "https://projektargo.com/"
MARK = '<meta name="generator" content="projektargo-motor">'
ROOT = pathlib.Path(__file__).resolve().parent.parent
SITEMAP = ROOT / "sitemap-motory.xml"
STATUS = ROOT / ".github" / "motory-status.json"

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
RESERVED = {"assets", "icons", "en", "sk", "zh", "hi", "es", "fr", "ar", "ru", "de", "it", "pl",
            "rmd", "retrofit-ce", "sedne", "poriadok", "feed-factory", "github", "api", "www"}
FORBIDDEN = [(re.compile(r"\bSteve\b"), "Steve"), (re.compile(r"Poriadok", re.I), "Poriadok"),
             (re.compile(r"\bAGEL\b"), "AGEL"), (re.compile(r"\bZapo\b"), "Zapo"),
             (re.compile(r"lorem ipsum", re.I), "lorem ipsum")]
NOINDEX_RE = re.compile(r'<meta[^>]+name=["\']robots["\'][^>]+content=["\'][^"\']*noindex', re.I)
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def warn(msg):
    print(f"::warning::{msg}")


def fetch_rows():
    url = f"{SUPABASE_URL}/rest/v1/motor_pages?select=slug,html,lastmod&status=eq.live&order=slug.asc"
    req = urllib.request.Request(url, headers={"apikey": PUBLISHABLE_KEY, "Accept": "application/json",
                                               "User-Agent": "projektargo-motory-sync"})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                data = json.loads(r.read().decode("utf-8"))
            if not isinstance(data, list):
                raise ValueError(f"neočakávaná odpoveď: {str(data)[:200]}")
            return data
        except Exception as e:  # noqa: BLE001 – každá chyba siete = skús znova
            last = e
            time.sleep(10)
    raise RuntimeError(f"Supabase nedostupné: {last}")


def validate(row):
    slug = str(row.get("slug") or "")
    html = row.get("html")
    if not (2 <= len(slug) <= 24 and SLUG_RE.match(slug)):
        return None, "neplatný slug"
    if slug in RESERVED:
        return None, "slug je rezervovaný pre hlavný web"
    if not isinstance(html, str):
        return None, "chýba html"
    html = html.lstrip("﻿").replace("\r\n", "\n")
    if not re.match(r"\s*<!doctype html>", html, re.I):
        return None, "html nezačína <!DOCTYPE html>"
    if "</html>" not in html.lower():
        return None, "html nie je kompletné (chýba </html>)"
    canon = re.search(r'<link[^>]+rel=["\']canonical["\'][^>]*>', html, re.I)
    if not canon or f'href="{SITE}{slug}/"' not in canon.group(0):
        return None, f"canonical musí byť {SITE}{slug}/"
    for rx, name in FORBIDDEN:
        if rx.search(html):
            return None, f"zakázaný reťazec: {name}"
    folder = ROOT / slug
    if folder.exists():
        idx = folder / "index.html"
        if not idx.exists() or MARK not in idx.read_text(encoding="utf-8", errors="replace"):
            return None, "priečinok patrí hlavnému webu – zvoľ iný slug"
    if MARK not in html:
        m = re.search(r"<head[^>]*>", html, re.I)
        if not m:
            return None, "chýba <head>"
        html = html[:m.end()] + "\n" + MARK + html[m.end():]
    if not html.endswith("\n"):
        html += "\n"
    lastmod = str(row.get("lastmod") or "")
    return {"slug": slug, "html": html, "lastmod": lastmod if DATE_RE.match(lastmod) else None}, "ok"


def write_if_changed(path, text, changed):
    old = path.read_text(encoding="utf-8") if path.exists() else None
    if old != text:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        changed.append(path.relative_to(ROOT).as_posix())


def existing_lastmods():
    if not SITEMAP.exists():
        return {}
    txt = SITEMAP.read_text(encoding="utf-8")
    return {m.group(1): m.group(2) for m in
            re.finditer(r"<loc>" + re.escape(SITE) + r"([a-z0-9-]+)/</loc><lastmod>([\d-]+)</lastmod>", txt)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fixture", help="JSON so riadkami namiesto Supabase (test)")
    ap.add_argument("--changed-out", help="sem zapíše zoznam zmenených súborov")
    a = ap.parse_args()

    try:
        rows = json.loads(pathlib.Path(a.fixture).read_text(encoding="utf-8")) if a.fixture else fetch_rows()
    except Exception as e:  # noqa: BLE001
        warn(f"{e} – nič nemením, zverejnené stránky ostávajú.")
        return 0

    changed, status, lastmods = [], {}, {}
    for row in rows:
        page, msg = validate(row)
        slug = str(row.get("slug") or "?")
        status[slug] = msg if page else f"chyba: {msg}"
        if not page:
            warn(f"motor {slug}: {msg}")
            continue
        write_if_changed(ROOT / page["slug"] / "index.html", page["html"], changed)
        if page["lastmod"]:
            lastmods[page["slug"]] = page["lastmod"]

    # Sitemapa = všetky zverejnené stránky motorov v repozitári (nič sa z nej neodstraňuje, kým priečinok existuje).
    prev = existing_lastmods()
    today = datetime.date.today().isoformat()
    urls = []
    for idx in sorted(ROOT.glob("*/index.html")):
        txt = idx.read_text(encoding="utf-8", errors="replace")
        if MARK not in txt or NOINDEX_RE.search(txt):
            continue
        slug = idx.parent.name
        mod = lastmods.get(slug) or prev.get(slug) or today
        urls.append(f"  <url><loc>{escape(SITE + slug + '/')}</loc><lastmod>{mod}</lastmod></url>")
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">', *urls, "</urlset>", ""]
    write_if_changed(SITEMAP, "\n".join(sm), changed)
    write_if_changed(STATUS, json.dumps(dict(sorted(status.items())), ensure_ascii=False, indent=2) + "\n", changed)

    if a.changed_out:
        pathlib.Path(a.changed_out).write_text("".join(c + "\n" for c in changed), encoding="utf-8")
    print(f"Motory: {len(rows)} live riadkov, zmenené súbory: {changed or 'žiadne'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
