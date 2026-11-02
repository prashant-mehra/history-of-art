#!/usr/bin/env python3
"""Find candidate Wikimedia Commons images for each work. Writes tools/candidates.json (for review)."""
import json, re, ssl, sys, time, urllib.parse, urllib.request, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from data_works import W
ctx = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
UA = {"User-Agent": "ArtHistorySiteBuilder/1.0 (educational static site; contact via repo issues)"}
API = "https://commons.wikimedia.org/w/api.php"
def api(**p):
    p["format"] = "json"
    for i in range(4):
        try:
            req = urllib.request.Request(API + "?" + urllib.parse.urlencode(p), headers=UA)
            return json.load(urllib.request.urlopen(req, context=ctx, timeout=30))
        except Exception as ex:
            time.sleep(2 * (i + 1)); err = ex
    raise err
OK = re.compile(r"public domain|^pd|cc0|cc[- ]by|cc[- ]zero|attribution", re.I)
BAD = re.compile(r"non-?commercial|\bnc\b|fair use|copyrighted", re.I)
def strip(s): return re.sub(r"<[^>]+>", "", s or "").strip()
def cands(query, limit=10):
    r = api(action="query", generator="search", gsrsearch=query, gsrnamespace=6, gsrlimit=limit,
            prop="imageinfo", iiprop="url|size|mime|extmetadata", iiurlwidth=800)
    out = []
    for pg in (r.get("query", {}).get("pages", {}) or {}).values():
        ii = (pg.get("imageinfo") or [None])[0]
        if not ii or ii["mime"] not in ("image/jpeg", "image/png", "image/webp"): continue
        if ii["width"] < 600: continue
        m = ii.get("extmetadata", {})
        lic = strip(m.get("LicenseShortName", {}).get("value"))
        if not lic or BAD.search(lic) or not OK.search(lic): continue
        out.append(dict(file=pg["title"], idx=pg.get("index", 99), license=lic, license_url=strip(m.get("LicenseUrl", {}).get("value")),
                        artist=strip(m.get("Artist", {}).get("value"))[:160], credit=strip(m.get("Credit", {}).get("value"))[:160],
                        thumb=ii.get("thumburl"), w=ii["width"], h=ii["height"], page=ii["descriptionurl"]))
    return sorted(out, key=lambda c: c["idx"])
if __name__ == "__main__":
    hints = json.load(open(pathlib.Path(__file__).parent / "hints.json")) if (pathlib.Path(__file__).parent / "hints.json").exists() else {}
    res = {}
    for w in W:
        slug, title, artist = w[0], w[1], w[2]
        q = hints.get(slug) or f"{title} {artist}".strip()
        try: res[slug] = dict(q=q, c=cands(q)[:4])
        except Exception as ex: res[slug] = dict(q=q, c=[], err=str(ex))
        print(slug, "->", [c["file"] for c in res[slug]["c"]][:2], flush=True)
        time.sleep(0.3)
    json.dump(res, open(pathlib.Path(__file__).parent / "candidates.json", "w"), indent=1, ensure_ascii=False)
