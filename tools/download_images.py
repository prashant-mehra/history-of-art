#!/usr/bin/env python3
"""Download selected Commons images (800px) to assets/img and write tools/images.json with credits."""
import json, ssl, time, urllib.request, pathlib, sys
here = pathlib.Path(__file__).parent; out = here.parent / "assets/img"; out.mkdir(parents=True, exist_ok=True)
ctx = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
UA = {"User-Agent": "ArtHistorySiteBuilder/1.0 (educational static site; contact via repo issues)"}
C = [json.load(open(here / n)) for n in ("candidates.json", "candidates2.json", "candidates3.json") if (here / n).exists()]
def get(slug, i):
    for c in reversed(C):
        if slug in c and len(c[slug]["c"]) > i: return c[slug]["c"][i]
SEL = json.load(open(here / "selection.json"))
done = json.load(open(here / "images.json")) if (here / "images.json").exists() else {}
for key, spec in SEL.items():
    if key in done and (out / f"{key}.jpg").exists(): continue
    src, i = spec if isinstance(spec, list) else (key, spec)
    c = get(src, i)
    if not c: print("missing", key); continue
    for attempt in range(5):
        try:
            data = urllib.request.urlopen(urllib.request.Request(c["thumb"], headers=UA), context=ctx, timeout=40).read(); break
        except Exception as ex:
            print(key, "retry", ex, flush=True); time.sleep(8 * (attempt + 1)); data = None
    if not data: continue
    ext = ".jpg"
    (out / f"{key}{ext}").write_bytes(data)
    done[key] = dict(file=c["file"][5:], artist=c["artist"], credit=c["credit"], license=c["license"], license_url=c["license_url"], page=c["page"])
    json.dump(done, open(here / "images.json", "w"), indent=1, ensure_ascii=False)
    print("ok", key, len(data), flush=True); time.sleep(1.5)
