#!/usr/bin/env python3
"""Motory – zverejnenie stránok motorov na projektargo.com.

Zdroj: tabuľka public.motor_pages v Supabase (zapisuje ju naplánovaná úloha „Motory – spúšťač“).
Pre každý riadok so stavom live zapíše <slug>/index.html, potom vygeneruje sitemap-motory.xml
a .github/motory-status.json (ok / chyba pre každý slug).

Bezpečnostné pravidlá:
- Nikdy nič nemaže (ani priečinky, ani riadky v sitemape motorov).
- Nikdy neprepíše priečinok hlavného webu: zapisuje len do priečinkov, ktoré ešte neexistujú
  alebo ktorých index.html už nesie značku MARK (stránka motora).
- Nedostupné Supabase = žiadna zmena (zverejnené stránky ostávajú), ale beh skončí chybou
  (::error:: + exit 1), aby GitHub poslal e-mail. To isté pri prázdnej odpovedi, keď v repozitári
  stránky motorov už sú, a keď neprejde kontrolou ani jedna live stránka. Tichá porucha je neprípustná.
- Do každej stránky motora vloží Content-Security-Policy s hashmi jej inline skriptov
  (script-src bez 'unsafe-inline') a referrer policy. Počíta sa pri každom zverejnení, takže
  hashe nemôžu zostarieť; nová stránka motora ju dostane automaticky. Nový externý host treba
  doplniť do CSP_* nižšie – skript naň upozorní (::warning::), inak ho prehliadač zablokuje.
- Do každej stránky motora vloží pred </body> plávajúce tlačidlo Projektu Argo (NAV_TAG → /argo-nav.js,
  zdroj zdroj/static/argo-nav.js hlavného webu). Dizajn stránky nemení: tlačidlo žije vo vlastnom shadow DOM.

Použitie:  python3 .github/motory_sync.py [--fixture rows.json] [--changed-out subor.txt]
"""
import argparse, datetime, json, pathlib, re, sys, time, urllib.request
from xml.sax.saxutils import escape

SUPABASE_URL = "https://asnpyrrdeauhkskkkmuc.supabase.co"
PUBLISHABLE_KEY = "sb_publishable_9Nwzk4Ql2WH1PCQZbNe5BQ_-8eVhBve"  # verejný kľúč, rovnaký ako na webe
SITE = "https://projektargo.com/"
MARK = '<meta name="generator" content="projektargo-motor">'
NAV_TAG = '<script src="/argo-nav.js" defer></script>'  # plávajúce tlačidlo „A“: domov, všetky motory, rovnaký trh, jazyk, kontakt
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

# --- Content Security Policy -------------------------------------------------
# Politika sa počíta pri každom zverejnení z finálneho HTML, takže hashe inline
# skriptov nemôžu zostarieť a každá nová stránka motora ju dostane automaticky.
# script-src je bez 'unsafe-inline': vykonať sa smie len skript s uvedeným hashom
# alebo z uvedeného hostu. style-src 'unsafe-inline' je nutné pre atribúty style="".
# Hosty podľa dokumentácie PostHog (EU: eu-assets.i.posthog.com) a Google Fonts.
CSP_SCRIPT = ["'self'", "https://*.posthog.com"]
CSP_STYLE = ["'self'", "'unsafe-inline'", "https://fonts.googleapis.com"]
CSP_FONT = ["'self'", "https://fonts.gstatic.com"]
CSP_IMG = ["'self'", "data:", "https://*.posthog.com"]
CSP_CONNECT = ["'self'", "https://*.posthog.com", SUPABASE_URL]
CSP_ALLOWED_HOSTS = {"fonts.googleapis.com", "fonts.gstatic.com", "eu.i.posthog.com",
                     "eu-assets.i.posthog.com", "us.i.posthog.com", "projektargo.com",
                     SUPABASE_URL.split("//")[1]}
REFERRER_META = '<meta name="referrer" content="strict-origin-when-cross-origin">'
INLINE_SCRIPT_RE = re.compile(r"<script(?![^>]*\ssrc=)[^>]*>(.*?)</script>", re.S | re.I)
CSP_META_RE = re.compile(r'[ \t]*<meta[^>]+http-equiv=["\']?Content-Security-Policy["\']?[^>]*>\n?', re.I)
REFERRER_META_RE = re.compile(r'[ \t]*<meta[^>]+name=["\']?referrer["\']?[^>]*>\n?', re.I)
CHARSET_RE = re.compile(r"<meta[^>]+charset=[^>]*>", re.I)
HEAD_RE = re.compile(r"<head[^>]*>", re.I)
EXT_RES_RE = re.compile(r'<(?:script|link|img|source|video|audio|iframe)\b[^>]*(?:src|href)=["\']https://([a-z0-9.\-]+)', re.I)


def add_csp(html, slug):
    """Vymení prípadnú starú CSP za novú, vypočítanú z tohto HTML. Vracia (html, cudzie_hosty)."""
    import base64, hashlib
    html = CSP_META_RE.sub("", html)
    html = REFERRER_META_RE.sub("", html)
    hashes = []
    for body in INLINE_SCRIPT_RE.findall(html):
        h = "'sha256-" + base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode() + "'"
        if h not in hashes:
            hashes.append(h)
    policy = "; ".join([
        "default-src 'self'",
        "base-uri 'self'",
        "object-src 'none'",
        "frame-src 'none'",
        "form-action 'none'",
        "script-src " + " ".join(CSP_SCRIPT + hashes),
        "style-src " + " ".join(CSP_STYLE),
        "font-src " + " ".join(CSP_FONT),
        "img-src " + " ".join(CSP_IMG),
        "connect-src " + " ".join(CSP_CONNECT),
        "worker-src 'self' blob: data:",
    ])
    meta = f'<meta http-equiv="Content-Security-Policy" content="{policy}">\n{REFERRER_META}'
    # CSP musí byť pred prvým skriptom a štýlom; charset musí zostať v prvých 1024 bajtoch,
    # preto ide meta hneď za charset (a len ak charset chýba, tak za <head>).
    m = CHARSET_RE.search(html) or HEAD_RE.search(html)
    if not m:
        return html, []
    html = html[:m.end()] + "\n" + meta + html[m.end():]
    foreign = sorted({h for h in EXT_RES_RE.findall(html) if h not in CSP_ALLOWED_HOSTS})
    return html, foreign


def warn(msg):
    print(f"::warning::{msg}")


def err(msg):
    """Chyba, ktorá musí byť viditeľná: beh padne a GitHub pošle e-mail."""
    print(f"::error::{msg}")


def published_slugs():
    """Stránky motorov, ktoré už sú v repozitári (podľa značky MARK)."""
    out = []
    for idx in sorted(ROOT.glob("*/index.html")):
        try:
            if MARK in idx.read_text(encoding="utf-8", errors="replace"):
                out.append(idx.parent.name)
        except OSError:
            continue
    return out


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
    if "/argo-nav.js" not in html:
        end = html.lower().rfind("</body>")
        if end >= 0:
            html = html[:end] + NAV_TAG + "\n" + html[end:]
        else:
            warn(f"motor {slug}: chýba </body> – tlačidlo Projektu Argo nevložené")
    html, foreign = add_csp(html, slug)
    if foreign:
        warn(f"motor {slug}: stránka načítava z hostov mimo CSP ({', '.join(foreign)}) – "
             f"doplň ich do CSP_* v .github/motory_sync.py, inak ich prehliadač zablokuje")
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
        err(f"{e} – nič nemením, zverejnené stránky ostávajú. Skontroluj Supabase a práva verejného "
            f"kľúča (anon potrebuje SELECT na stĺpce slug, html, status, lastmod tabuľky motor_pages).")
        return 1

    # Prázdna odpoveď nie je chyba siete: odobrané práva alebo zmenená RLS politika vrátia []
    # bez chybovej správy. Ak v repozitári stránky motorov už sú, ide o poruchu – nahlás ju.
    if not rows:
        live = published_slugs()
        if live:
            err(f"Supabase vrátilo 0 live stránok, hoci v repozitári ich je {len(live)} – nič nemením. "
                f"Skontroluj tabuľku motor_pages (status, RLS politiku a práva anon).")
            return 1
        warn("Supabase vrátilo 0 live stránok a v repozitári žiadna nie je – nie je čo zverejniť.")

    changed, status, lastmods, ok = [], {}, {}, 0
    for row in rows:
        page, msg = validate(row)
        slug = str(row.get("slug") or "?")
        status[slug] = msg if page else f"chyba: {msg}"
        if not page:
            warn(f"motor {slug}: {msg}")
            continue
        ok += 1
        write_if_changed(ROOT / page["slug"] / "index.html", page["html"], changed)
        if page["lastmod"]:
            lastmods[page["slug"]] = page["lastmod"]

    # Ani jedna live stránka neprešla kontrolou = systémová chyba (šablóna, canonical, zakázaný reťazec).
    if rows and not ok:
        err(f"Žiadna z {len(rows)} live stránok neprešla kontrolou – nič nemením, dôvody sú vyššie.")
        return 1

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
