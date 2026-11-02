#!/usr/bin/env python3
"""Generates the Art History site. Run from anywhere: python3 tools/build.py"""
import json, html, pathlib, sys, datetime, re
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from data_works import W
from data_artists import A
from data_eras import ERAS
from data_misc import MOV, REG, THEMES, TECH, GLOSS, QUIZ

OUT = pathlib.Path(__file__).resolve().parent.parent
e = lambda s: html.escape(str(s), quote=True)

# ---------- images (Wikimedia Commons, see tools/images.json) ----------
IMG = json.load(open(OUT / "tools/images.json")) if (OUT / "tools/images.json").exists() else {}
def credit_html(k):
    c = IMG[k]
    who = c["artist"] if c["artist"] and c["artist"].lower() not in ("unknown", "unknown author", "anonymous") else "Unknown author"
    who = e(who[:110])
    lic = f'<a href="{e(c["license_url"])}">{e(c["license"])}</a>' if c["license_url"] else e(c["license"])
    return f'Image: <a href="{e(c["page"])}">{e(c["file"][:70])}</a> by {who}, {lic}, via Wikimedia Commons.'
def fig(k, r, alt):
    if k not in IMG: return ""
    return (f'<figure class="pic"><img src="{r}/assets/img/{k}.jpg" alt="{e(alt)}" loading="lazy">'
            f'<figcaption>{credit_html(k)}</figcaption></figure>')

# ---------- lookups ----------
WORKS = [dict(zip("slug title artist date sort kind medium loc region era mov text".split(), w if len(w)==12 else w[:-1]+("",)+w[-1:])) for w in W]
ARTISTS = [dict(zip("slug name years nat mov bio".split(), a)) for a in A]
ERA = {x[0]: dict(slug=x[0], title=x[1], dates=x[2], start=x[3], intro=x[4], secs=x[5]) for x in ERAS}
MOVS = {m[0]: dict(slug=m[0], title=m[1], dates=m[2], era=m[3], text=m[4], ideas=m[5]) for m in MOV}
ERA_ORDER = ["prehistoric"] + [x[0] for x in ERAS]
ERA_TITLE = {"prehistoric": "Prehistoric art", **{k: v["title"] for k, v in ERA.items()}}
ERA_DATES = {"prehistoric": "~100,000–2000 BCE", **{k: v["dates"] for k, v in ERA.items()}}
ERA_URL = lambda s: "eras/prehistoric/" if s == "prehistoric" else f"eras/{s}/"
ALIAS = {
 "Jan van Eyck":"van-eyck","Leonardo da Vinci":"leonardo","Michelangelo":"michelangelo","Albrecht Dürer":"durer",
 "Pieter Bruegel the Elder":"bruegel","Artemisia Gentileschi":"artemisia","Gian Lorenzo Bernini":"bernini",
 "Diego Velázquez":"velazquez","Rembrandt van Rijn":"rembrandt","Johannes Vermeer":"vermeer",
 "Jean-Honoré Fragonard":"fragonard","Jacques-Louis David":"david","Francisco Goya":"goya","Eugène Delacroix":"delacroix",
 "Katsushika Hokusai":"hokusai","J. M. W. Turner":"turner","Gustave Courbet":"courbet","Édouard Manet":"manet",
 "Claude Monet":"monet","Georges Seurat":"seurat","Vincent van Gogh":"van-gogh","Paul Cézanne":"cezanne",
 "Gustave Eiffel's company":"eiffel","Henri Matisse":"matisse","Pablo Picasso":"picasso","Wassily Kandinsky":"kandinsky",
 "Kazimir Malevich":"malevich","Marcel Duchamp":"duchamp","Salvador Dalí":"dali","Frank Lloyd Wright":"wright",
 "Frida Kahlo":"kahlo","Edward Hopper":"hopper","Piet Mondrian":"mondrian","Jackson Pollock":"pollock",
 "Andy Warhol":"warhol","Damien Hirst":"hirst","Yayoi Kusama":"kusama","Jean-Michel Basquiat":"basquiat",
 "Frank Gehry":"gehry","Louise Bourgeois":"bourgeois","Ai Weiwei":"ai-weiwei","Banksy":"banksy","Beeple":"beeple",
 "Thutmose":"thutmose","Caravaggio":"caravaggio","Fan Kuan":"fan-kuan","Phidias":"phidias","Myron":"myron","Sandro Botticelli":"botticelli","Giotto":"giotto","Raphael":"raphael",
}
AMAP = {a["slug"]: a for a in ARTISTS}
WMAP = {w["slug"]: w for w in WORKS}
for w in WORKS:
    w["aslug"] = ALIAS.get(w["artist"], "")
    if w["artist"] and not w["aslug"] and w["artist"] not in ("Anthemius of Tralles and Isidore of Miletus","Clifford Possum Tjapaltjarri and Tim Leura"):
        print("WARN no artist match:", w["artist"])
REGION_PAGES = {"Africa":"africa","Asia":"asia","Americas":"americas","Oceania":"oceania"}
for w in WORKS:
    assert w["era"] == "" or w["era"] in ERA, w["slug"]
    assert w["mov"] == "" or w["mov"] in MOVS, (w["slug"], w["mov"])
for a in ARTISTS:
    assert a["mov"] == "" or a["mov"] in MOVS, (a["slug"], a["mov"])
# fix movement slug aliases used in artist data
for a in ARTISTS:
    pass

# ---------- page shell ----------
written = []
def root_of(path):  # path like "works/x/index.html"
    depth = path.count("/")
    return "/".join([".."] * depth) if depth else "."

def write(path, title, desc, body, crumbs=None, extra_head=""):
    r = root_of(path)
    c = ""
    if crumbs:
        parts = ['<a href="%s/">Home</a>' % r] + [
            (f'<a href="{r}/{u}">{e(t)}</a>' if u else e(t)) for t, u in crumbs]
        c = '<p class="crumbs">' + " › ".join(parts) + "</p>"
    doc = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc)}">
<link rel="stylesheet" href="{r}/assets/style.css"><script src="{r}/assets/site.js" defer></script>{extra_head}
</head><body data-root="{r}"><main class="wrap">
{c}
{body}
</main></body></html>
"""
    p = OUT / path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(doc, encoding="utf-8")
    written.append((path, title, desc))

def L(r, url, text):
    return f'<a href="{r}/{url}">{e(text)}</a>'

def work_card(w, r):
    img = f'<img src="{r}/assets/img/{w["slug"]}.jpg" alt="" loading="lazy">' if w["slug"] in IMG else ""
    q = e((w["title"] + " " + w["artist"] + " " + w["text"]).lower())
    return (f'<a class="card" href="{r}/works/{w["slug"]}/" data-era="{w["era"]}" data-kind="{e(w["kind"])}" data-q="{q}">'
            + img + f'<span class="tag">{e(w["date"])}</span><h3>{e(w["title"])}</h3><p>{e(w["artist"] or "Unknown artist")} · {e(w["kind"])}</p></a>')

def sec_list(secs):
    out = ""
    for h, t in secs:
        out += f"<h2>{e(h)}</h2><p>{e(t)}</p>"
    return out

def pager(prev, nxt, r):
    p = f'<a href="{r}/{prev[1]}">← {e(prev[0])}</a>' if prev else "<span></span>"
    n = f'<a href="{r}/{nxt[1]}">{e(nxt[0])} →</a>' if nxt else "<span></span>"
    return f'<div class="pager">{p}{n}</div>'

# ---------- ERAS ----------
def build_eras():
    for i, s in enumerate(ERA_ORDER):
        if s == "prehistoric": continue
        x = ERA[s]; r = root_of(f"eras/{s}/index.html")
        ws = sorted([w for w in WORKS if w["era"] == s], key=lambda w: w["sort"])
        ms = [m for m in MOVS.values() if m["era"] == s]
        arts = []
        for w in ws:
            if w["aslug"] and w["aslug"] not in arts: arts.append(w["aslug"])
        body = f'<h1>{e(x["title"])}</h1><p class="meta">{e(x["dates"])}</p><div class="prose">'
        body += "".join(f"<p>{e(p)}</p>" for p in x["intro"]) + sec_list(x["secs"]) + "</div>"
        if ws:
            body += '<h2>Key works</h2><div class="grid">' + "".join(work_card(w, r) for w in ws) + "</div>"
        if ms:
            body += '<h2>Movements and styles</h2><div class="grid">' + "".join(
                f'<a class="card" href="{r}/movements/{m["slug"]}/"><span class="tag">{e(m["dates"])}</span><h3>{e(m["title"])}</h3><p>{e(m["text"])}</p></a>' for m in ms) + "</div>"
        if arts:
            body += "<h2>Artists</h2><p>" + " · ".join(L(r, f"artists/{a}/", AMAP[a]["name"]) for a in arts) + "</p>"
        if any(q[0] == s for q in QUIZ):
            body += f'<div class="callout">Test yourself: <a href="{r}/learn/quizzes/{s}/">take the {e(x["title"])} quiz</a>.</div>'
        pv = ERA_ORDER[i-1]; nx = ERA_ORDER[i+1] if i+1 < len(ERA_ORDER) else None
        body += pager((ERA_TITLE[pv], ERA_URL(pv)), (ERA_TITLE[nx], ERA_URL(nx)) if nx else None, r)
        write(f"eras/{s}/index.html", f'{x["title"]} — Art History', f'{x["title"]} ({x["dates"]}): overview, key works, movements and artists.', body,
              [("Eras", "eras/"), (x["title"], None)])
    r = "."  # index
    r = root_of("eras/index.html")
    body = '<h1>Eras</h1><p class="prose">Western and Mediterranean eras in order. Regional traditions run in parallel on the <a href="../regions/">regions pages</a>.</p><div class="grid">'
    for s in ERA_ORDER:
        n = len([w for w in WORKS if w["era"] == s])
        body += f'<a class="card" href="{r}/{ERA_URL(s)}"><span class="tag">{e(ERA_DATES[s])}</span><h3>{e(ERA_TITLE[s])}</h3><p>{n} featured works</p></a>' if s != "prehistoric" else \
                f'<a class="card" href="{r}/{ERA_URL(s)}"><span class="tag">{e(ERA_DATES[s])}</span><h3>{e(ERA_TITLE[s])}</h3><p>Paleolithic, Mesolithic, Neolithic</p></a>'
    body += "</div>"
    write("eras/index.html", "Eras — Art History", "All eras of art history, from the Stone Age to today.", body, [("Eras", None)])

# ---------- REGIONS ----------
def build_regions():
    r = root_of("regions/index.html")
    body = '<h1>Regions</h1><p class="prose">Art traditions that run alongside the main timeline, from Africa, Asia, the Americas and Oceania.</p><div class="grid">'
    for s, t, intro, secs in REG:
        body += f'<a class="card" href="{r}/regions/{s}/"><h3>{e(t)}</h3><p>{e(intro)}</p></a>'
    body += "</div>"
    write("regions/index.html", "Regions — Art History", "Art traditions of Africa, Asia, the Americas and Oceania.", body, [("Regions", None)])
    for s, t, intro, secs in REG:
        r = root_of(f"regions/{s}/index.html")
        name = {v: k for k, v in REGION_PAGES.items()}[s]
        ws = sorted([w for w in WORKS if w["region"] == name], key=lambda w: w["sort"])
        body = f'<h1>{e(t)}</h1><div class="prose"><p>{e(intro)}</p>{sec_list(secs)}</div>'
        body += "<h2>Featured works</h2><div class=\"grid\">" + "".join(work_card(w, r) for w in ws) + "</div>"
        write(f"regions/{s}/index.html", f"{t} — Art History", f"Art of {t}: traditions, key works and history.", body, [("Regions", "regions/"), (t, None)])

# ---------- MOVEMENTS ----------
def build_movements():
    r = root_of("movements/index.html")
    body = '<h1>Movements and styles</h1><p class="prose">Art is often grouped into movements: shared aims, styles or ideas. The groupings are a convenience, and many artists crossed them.</p><div class="grid">'
    for m in MOV:
        body += f'<a class="card" href="{r}/movements/{m[0]}/"><span class="tag">{e(m[2])}</span><h3>{e(m[1])}</h3><p>{e(m[4])}</p></a>'
    write("movements/index.html", "Movements — Art History", "A–Z style of art movements with key works and artists.", body + "</div>", [("Movements", None)])
    for m in MOVS.values():
        r = root_of(f"movements/{m['slug']}/index.html")
        ws = [w for w in WORKS if w["mov"] == m["slug"]]
        ars = [a for a in ARTISTS if a["mov"] == m["slug"]]
        body = f'<h1>{e(m["title"])}</h1><p class="meta">{e(m["dates"])} · <a href="{r}/{ERA_URL(m["era"])}">{e(ERA_TITLE[m["era"]])}</a></p><div class="prose"><p>{e(m["text"])}</p><h2>Key ideas</h2><ul>' + "".join(f"<li>{e(i)}</li>" for i in m["ideas"]) + "</ul></div>"
        if ars: body += "<h2>Artists</h2><p>" + " · ".join(L(r, f"artists/{a['slug']}/", a["name"]) for a in ars) + "</p>"
        if ws: body += '<h2>Works</h2><div class="grid">' + "".join(work_card(w, r) for w in ws) + "</div>"
        write(f"movements/{m['slug']}/index.html", f'{m["title"]} — Art History', f'{m["title"]} ({m["dates"]}): {m["text"]}', body, [("Movements", "movements/"), (m["title"], None)])

# ---------- ARTISTS ----------
def build_artists():
    r = root_of("artists/index.html")
    body = '<h1>Artists</h1><div class="filters"><label>Search<input type="search" id="f" placeholder="Name or movement"></label></div><div class="grid" id="g">'
    for a in sorted(ARTISTS, key=lambda a: a["name"]):
        m = MOVS[a["mov"]]["title"] if a["mov"] else ""
        body += f'<a class="card" href="{r}/artists/{a["slug"]}/" data-q="{e((a["name"]+" "+m+" "+a["nat"]).lower())}"><span class="tag">{e(a["years"])}</span><h3>{e(a["name"])}</h3><p>{e(a["nat"])}</p></a>'
    body += """</div><script>var f=document.getElementById('f');f.addEventListener('input',function(){var q=f.value.toLowerCase();document.querySelectorAll('#g .card').forEach(function(c){c.hidden=c.dataset.q.indexOf(q)<0})})</script>"""
    write("artists/index.html", "Artists — Art History", "Profiles of artists across art history.", body, [("Artists", None)])
    for a in ARTISTS:
        r = root_of(f"artists/{a['slug']}/index.html")
        ws = sorted([w for w in WORKS if w["aslug"] == a["slug"]], key=lambda w: w["sort"])
        mv = f'<a href="{r}/movements/{a["mov"]}/">{e(MOVS[a["mov"]]["title"])}</a>' if a["mov"] else ""
        body = f'<h1>{e(a["name"])}</h1><p class="meta">{e(a["years"])} · {e(a["nat"])}' + (f" · {mv}" if mv else "") + f'</p><div class="prose"><p>{e(a["bio"])}</p></div>'
        if ws: body += "<h2>Works on this site</h2><div class=\"grid\">" + "".join(work_card(w, r) for w in ws) + "</div>"
        write(f"artists/{a['slug']}/index.html", f'{a["name"]} — Art History', f'{a["name"]} ({a["years"]}), {a["nat"]}: {a["bio"]}', body, [("Artists", "artists/"), (a["name"], None)])

# ---------- WORKS ----------
def build_works():
    r = root_of("works/index.html")
    eras_used = [s for s in ERA_ORDER if any(w["era"] == s for w in WORKS)]
    kinds = sorted({w["kind"] for w in WORKS})
    body = '<h1>Works</h1><div class="filters"><label>Era<select id="era"><option value="">All</option>' + "".join(f'<option value="{s}">{e(ERA_TITLE[s])}</option>' for s in eras_used) + '<option value="-">Outside the era pages</option></select></label>'
    body += '<label>Type<select id="kind"><option value="">All</option>' + "".join(f'<option>{e(k)}</option>' for k in kinds) + '</select></label>'
    body += '<label>Search<input type="search" id="q" placeholder="Title, artist, idea"></label></div><p class="meta" id="n"></p><div class="grid" id="g">'
    for w in sorted(WORKS, key=lambda w: w["sort"]):
        body += work_card(w, r)
    body += """</div><script>
var $=function(i){return document.getElementById(i)};
function go(){var a=$('era').value,k=$('kind').value,q=$('q').value.toLowerCase(),n=0;
document.querySelectorAll('#g .card').forEach(function(c){var ea=c.dataset.era;var ok=(!a||(a==='-'?ea==='':ea===a))&&(!k||c.dataset.kind===k)&&(!q||c.dataset.q.indexOf(q)>-1);c.hidden=!ok;if(ok)n++});
$('n').textContent=n+' works'}
['era','kind'].forEach(function(i){$(i).addEventListener('change',go)});$('q').addEventListener('input',go);go();</script>"""
    write("works/index.html", "Works — Art History", "Gallery of featured artworks across history.", body, [("Works", None)])
    th = {}
    for t in THEMES:
        for s in t[4]: th.setdefault(s, []).append(t)
    tc = {}
    for t in TECH:
        for s in t[3]: tc.setdefault(s, []).append(t)
    for w in WORKS:
        r = root_of(f"works/{w['slug']}/index.html")
        rows = []
        if w["artist"]:
            rows.append(("Artist", L(r, f"artists/{w['aslug']}/", w["artist"]) if w["aslug"] else e(w["artist"])))
        rows += [("Date", e(w["date"])), ("Type", e(w["kind"])), ("Medium", e(w["medium"])), ("Location", e(w["loc"]))]
        if w["region"] in REGION_PAGES: rows.append(("Region", L(r, f"regions/{REGION_PAGES[w['region']]}/", w["region"])))
        else: rows.append(("Region", e(w["region"])))
        if w["era"]: rows.append(("Era", L(r, ERA_URL(w["era"]), ERA_TITLE[w["era"]])))
        if w["mov"]: rows.append(("Movement", L(r, f"movements/{w['mov']}/", MOVS[w["mov"]]["title"])))
        facts = '<table class="facts">' + "".join(f"<tr><th>{k}</th><td>{v}</td></tr>" for k, v in rows) + "</table>"
        body = f'<h1>{e(w["title"])}</h1><p class="meta">{e(w["artist"] or "Unknown artist")} · {e(w["date"])}</p>{facts}{fig(w["slug"], r, w["title"] + (" by " + w["artist"] if w["artist"] else ""))}<div class="prose"><p>{e(w["text"])}</p></div>'
        tags = [f'<a class="tag" href="{r}/themes/{t[0]}/">{e(t[1])}</a>' for t in th.get(w["slug"], [])] + \
               [f'<a class="tag" href="{r}/techniques/{t[0]}/">{e(t[1])}</a>' for t in tc.get(w["slug"], [])]
        if tags: body += "<p>" + " ".join(tags) + "</p>"
        rel = [x for x in WORKS if x["slug"] != w["slug"] and ((w["aslug"] and x["aslug"] == w["aslug"]) or (w["era"] and x["era"] == w["era"]))]
        rel.sort(key=lambda x: (x["aslug"] != w["aslug"], abs(x["sort"] - w["sort"])))
        if rel: body += "<h2>Related works</h2><div class=\"grid\">" + "".join(work_card(x, r) for x in rel[:4]) + "</div>"
        if w["slug"] not in IMG:
            body += '<p class="meta">No image is shown: this work is either under copyright or no suitable openly licensed image was found. Search the title in a museum collection to see it.</p>'
        write(f"works/{w['slug']}/index.html", f'{w["title"]} — Art History', f'{w["title"]}, {w["artist"] or "unknown artist"}, {w["date"]}. {w["text"][:120]}', body,
              [("Works", "works/"), (w["title"], None)])

# ---------- THEMES / TECHNIQUES ----------
def build_themes():
    for kind, items in (("themes", THEMES), ("techniques", TECH)):
        r = root_of(f"{kind}/index.html")
        label = kind.capitalize()
        intro = "Cross-era essays that follow one idea through art history." if kind == "themes" else "How art is made: materials, tools and methods."
        body = f'<h1>{label}</h1><p class="prose">{intro}</p><div class="grid">'
        for it in items:
            blurb = it[2] if kind == "themes" else it[2]
            body += f'<a class="card" href="{r}/{kind}/{it[0]}/"><h3>{e(it[1])}</h3><p>{e(blurb)[:140]}…</p></a>' if len(blurb) > 140 else f'<a class="card" href="{r}/{kind}/{it[0]}/"><h3>{e(it[1])}</h3><p>{e(blurb)}</p></a>'
        write(f"{kind}/index.html", f"{label} — Art History", intro, body + "</div>", [(label, None)])
        for it in items:
            r = root_of(f"{kind}/{it[0]}/index.html")
            if kind == "themes":
                slug, title, lead, paras, wk = it
                body = f'<h1>{e(title)}</h1><div class="prose"><p><b>{e(lead)}</b></p>' + "".join(f"<p>{e(p)}</p>" for p in paras) + "</div>"
            else:
                slug, title, text, wk = it
                body = f'<h1>{e(title)}</h1><div class="prose"><p>{e(text)}</p></div>'
            ws = [WMAP[s] for s in wk]
            body += "<h2>Examples</h2><div class=\"grid\">" + "".join(work_card(w, r) for w in ws) + "</div>"
            write(f"{kind}/{slug}/index.html", f"{title} — Art History", (lead if kind == "themes" else text)[:150], body, [(label, f"{kind}/"), (title, None)])

# ---------- LEARN ----------
def build_learn():
    r = root_of("learn/index.html")
    body = f"""<h1>Learn</h1><div class="grid">
<a class="card" href="{r}/learn/how-to-read-an-artwork/"><h3>How to read an artwork</h3><p>A six-step method for looking closely.</p></a>
<a class="card" href="{r}/learn/glossary/"><h3>Glossary</h3><p>{len(GLOSS)+15} terms, filterable.</p></a>
<a class="card" href="{r}/learn/quizzes/"><h3>Quizzes</h3><p>One short quiz for each era.</p></a></div>"""
    write("learn/index.html", "Learn — Art History", "Guides, glossary and quizzes.", body, [("Learn", None)])
    body = """<h1>How to read an artwork</h1><div class="prose"><p>You do not need prior knowledge. A practiced way of looking helps.</p>
<h2>1. Look slowly</h2><p>Spend a full minute before reading any label. What do you notice first? What is easy to miss?</p>
<h2>2. Describe</h2><p>Say what you see in plain words: subject, colors, lines, textures, scale. Describing comes before interpreting.</p>
<h2>3. Ask how it was made</h2><p>What is the medium? Is the surface smooth or built up? Material choices carry meaning, and techniques limit what is possible.</p>
<h2>4. Place it</h2><p>When and where was it made, and for whom? A painting for a church altar and one for a private collector do different jobs.</p>
<h2>5. Interpret</h2><p>What might it mean? Use evidence in the image first, then context. Several readings can be valid.</p>
<h2>6. Compare</h2><p>Put it next to another work: an earlier one it learns from, or a later one that answers it. Compare Botticelli's Venus with Manet's Olympia, for instance.</p>
<div class="callout">Try it on <a href="../../works/starry-night/">The Starry Night</a> or <a href="../../works/guernica/">Guernica</a>.</div></div>"""
    write("learn/how-to-read-an-artwork/index.html", "How to read an artwork — Art History", "A six-step method for looking at art.", body, [("Learn", "learn/"), ("How to read an artwork", None)])
    # glossary
    base = [("BCE / CE","Before Common Era / Common Era; equivalents of BC / AD."),("Bitumen","Natural tar, used in Neolithic art to outline eyes and as an adhesive."),("Chronology (relative vs absolute)","Relative dating orders things before/after; absolute dating gives calendar ages, e.g. radiocarbon."),("Engraving","Lines cut into a surface with a hard point."),("Figurine","A small sculpture, usually of a human or animal."),("Hunter-gatherer","A way of life based on wild foods; all humans lived this way before farming."),("Megalith","A large stone used in a prehistoric monument."),("Ochre","Natural iron-oxide earth pigment, red to yellow; the main colour of early art."),("Parietal art","Art on cave walls or rock surfaces, as opposed to portable objects."),("Passage tomb","A burial chamber reached by a stone-lined passage, covered by a mound."),("Petroglyph","Image carved or pecked into rock. A painted image is a pictograph."),("Portable art (mobiliary art)","Small art objects that can be carried."),("Radiocarbon dating","Measures the decay of carbon-14 in organic material (works to roughly 50,000 years)."),("Uranium-series dating","Dates mineral crusts that formed over paintings, giving a minimum age."),("Venus figurine","Modern name for Paleolithic female statuettes; the name is a later invention.")]
    allg = sorted({t: d for t, d in base + GLOSS}.items(), key=lambda x: x[0].lower())
    body = '<h1>Glossary</h1><div class="filters"><label>Filter terms<input type="search" id="f" placeholder="Type to filter"></label></div><dl class="gloss" id="g">' + "".join(f"<dt>{e(t)}</dt><dd>{e(d)}</dd>" for t, d in allg) + """</dl><script>
var f=document.getElementById("f");f.addEventListener("input",function(){var q=f.value.toLowerCase();document.querySelectorAll("#g dt").forEach(function(dt){var dd=dt.nextElementSibling;var s=(dt.textContent+dd.textContent).toLowerCase().indexOf(q)>-1;dt.hidden=dd.hidden=!s})});</script>"""
    write("learn/glossary/index.html", "Glossary — Art History", "Key terms in art history.", body, [("Learn", "learn/"), ("Glossary", None)])
    # quizzes
    r = root_of("learn/quizzes/index.html")
    body = '<h1>Quizzes</h1><p class="prose">Short multiple-choice quizzes, one per era. Answers are shuffled each time.</p><div class="grid">'
    for s, t, qs in QUIZ:
        body += f'<a class="card" href="{r}/learn/quizzes/{s}/"><h3>{e(t)}</h3><p>{len(qs)} questions</p></a>'
    write("learn/quizzes/index.html", "Quizzes — Art History", "Quizzes for each era of art history.", body + "</div>", [("Learn", "learn/"), ("Quizzes", None)])
    for s, t, qs in QUIZ:
        data = json.dumps([{"q": q, "o": o, "a": a} for q, o, a in qs], ensure_ascii=False)
        body = """<h1>__T__ quiz</h1><form id="quiz"></form><p><button class="btn" id="go" type="button">Check answers</button> <span id="res" class="meta" role="status"></span></p>
<p><a href="__U__">Read about __T__</a></p>
<script>var Q=__D__;
function sh(a){a=a.slice();for(var i=a.length-1;i>0;i--){var j=Math.floor(Math.random()*(i+1));var t=a[i];a[i]=a[j];a[j]=t}return a}
var f=document.getElementById('quiz');
Q.forEach(function(x,i){var fs=document.createElement('fieldset');var lg=document.createElement('legend');lg.textContent=(i+1)+'. '+x.q;fs.appendChild(lg);
 sh(x.o.map(function(t,k){return {t:t,c:k===x.a}})).forEach(function(o){var l=document.createElement('label');var r=document.createElement('input');r.type='radio';r.name='q'+i;r.value=o.c?'1':'0';l.appendChild(r);l.append(' '+o.t);fs.appendChild(l)});f.appendChild(fs)});
document.getElementById('go').addEventListener('click',function(){var s=0;Q.forEach(function(x,i){var c=f.querySelector('input[name=q'+i+']:checked');var fs=f.querySelectorAll('fieldset')[i];fs.classList.remove('ok','bad');if(c&&c.value==='1'){s++;fs.classList.add('ok')}else fs.classList.add('bad')});
document.getElementById('res').textContent='Score: '+s+' / '+Q.length;});</script>"""
        body = body.replace("__T__", e(t)).replace("__U__", root_of("learn/quizzes/"+s+"/index.html")+"/"+ERA_URL(s)).replace("__D__", data)
        write(f"learn/quizzes/{s}/index.html", f"{t} quiz — Art History", f"Quiz on {t}.", body, [("Learn", "learn/"), ("Quizzes", "learn/quizzes/"), (t, None)])

# ---------- TIMELINE ----------
PRE = [
 ("~73,000 BCE",-73000,"Blombos Cave engraved ochre","Africa","Craft & Decorative","A piece of ochre with a deliberate cross-hatched pattern, from South Africa. Among the earliest known abstract designs.","eras/prehistoric/paleolithic/"),
 ("≥45,500 years ago",-43500,"Sulawesi warty pig painting","Asia","Painting","A life-size pig painted in red ochre in Leang Tedongnge, Indonesia: among the oldest known figurative artworks.","eras/prehistoric/paleolithic/"),
 ("~40,000 years ago",-38000,"Lion-Man of Hohlenstein-Stadel","Europe","Sculpture","A mammoth-ivory figure with a human body and a lion's head, from Germany.","eras/prehistoric/paleolithic/"),
 ("~40,000–35,000 years ago",-37000,"Venus of Hohle Fels","Europe","Sculpture","A small carved mammoth-ivory female figure, among the oldest known depictions of the human body.","eras/prehistoric/paleolithic/"),
 ("~36,000 years ago",-34000,"Chauvet Cave paintings","Europe","Painting","Lions, rhinos and horses drawn with striking skill in southern France.","eras/prehistoric/paleolithic/"),
 ("~28,000–25,000 BCE",-26000,"Venus of Willendorf","Europe","Sculpture","An 11 cm limestone figurine found in Austria, tinted with red ochre.","eras/prehistoric/paleolithic/"),
 ("~17,000 years ago",-15000,"Lascaux Cave paintings","Europe","Painting","Hundreds of painted animals, including the famous Hall of the Bulls.","eras/prehistoric/paleolithic/"),
 ("~14,000 years ago",-12000,"Earliest Jōmon pottery","Asia","Craft & Decorative","Among the world's oldest pottery, from Japan, later decorated with cord-impressed patterns.","eras/prehistoric/neolithic/"),
 ("~9500 BCE",-9500,"Göbekli Tepe","Asia","Architecture","T-shaped stone pillars carved with animals, in present-day Türkiye, built by hunter-gatherers.","eras/prehistoric/mesolithic/"),
 ("~9000 BCE onward",-9000,"Levantine rock art, Spain","Europe","Painting","Small painted figures of hunters, archers and dancers in narrative scenes.","eras/prehistoric/mesolithic/"),
 ("~7200–6500 BCE",-6850,"Ain Ghazal statues","Asia","Sculpture","Large plaster figures with bitumen-outlined eyes, found in Jordan.","eras/prehistoric/neolithic/"),
 ("~7100–5700 BCE",-6400,"Çatalhöyük","Asia","Painting","A large settlement in Türkiye with painted and plastered house interiors.","eras/prehistoric/neolithic/"),
 ("~3200 BCE",-3200,"Newgrange passage tomb","Europe","Architecture","An Irish tomb with spiral carvings, aligned so the winter solstice sunrise lights the inner chamber.","eras/prehistoric/neolithic/"),
 ("~3000–2500 BCE",-2750,"Stonehenge","Europe","Architecture","A monument built in stages in England; the large sarsen stones were raised around 2500 BCE.","eras/prehistoric/neolithic/"),
]
def build_timeline():
    ev = [dict(d=p[0], s=p[1], t=p[2], r=p[3], m=p[4], x=p[5], u=p[6]) for p in PRE]
    for w in WORKS:
        ev.append(dict(d=w["date"], s=w["sort"], t=w["title"], r=w["region"], m=w["kind"], x=w["text"].split(". ")[0].rstrip(".") + ".", u=f"works/{w['slug']}/"))
    ev.sort(key=lambda x: x["s"])
    body = """<h1>Timeline</h1>
<p class="prose">Prehistoric milestones and every featured work, oldest first. Dates are approximate and often revised.</p>
<div class="filters"><label>Region<select id="region"><option value="">All</option></select></label>
<label>Type<select id="medium"><option value="">All</option></select></label>
<label>Search<input type="search" id="q" placeholder="e.g. Venus"></label></div>
<p class="meta" id="count"></p><ol class="tl" id="tl"></ol>
<script>var E=""" + json.dumps(ev, ensure_ascii=False) + """;
var $=function(i){return document.getElementById(i)};
function uniq(k){return Array.from(new Set(E.map(function(e){return e[k]}))).sort()}
uniq("r").forEach(function(v){$("region").add(new Option(v,v))});uniq("m").forEach(function(v){$("medium").add(new Option(v,v))});
function render(){var r=$("region").value,m=$("medium").value,q=$("q").value.toLowerCase();
var L=E.filter(function(e){return (!r||e.r===r)&&(!m||e.m===m)&&(!q||(e.t+e.x).toLowerCase().indexOf(q)>-1)});
$("count").textContent=L.length+" of "+E.length+" events";var ol=$("tl");ol.textContent="";
L.forEach(function(e){var li=document.createElement("li");var d=document.createElement("div");d.className="date";d.textContent=e.d;
var h=document.createElement("h3");var a=document.createElement("a");a.href="../"+e.u;a.textContent=e.t;h.appendChild(a);
var p=document.createElement("p");p.textContent=e.x;var g=document.createElement("span");g.className="tag";g.textContent=e.r;
var g2=document.createElement("span");g2.className="tag";g2.textContent=e.m;li.append(d,h,p,g,g2);ol.appendChild(li)})}
["region","medium"].forEach(function(i){$(i).addEventListener("change",render)});$("q").addEventListener("input",render);render();</script>"""
    write("timeline/index.html", "Timeline — Art History", "Filterable timeline of art history from the Stone Age to today.", body, [("Timeline", None)])

# ---------- HOME / SEARCH / CONTACT ----------
def build_misc():
    r = "."
    strip = "".join(f'<a href="{ERA_URL(s)}"><b>{e(ERA_DATES[s])}</b>{e(ERA_TITLE[s])}</a>' for s in ERA_ORDER)
    feat = [WMAP[s] for s in ("great-sphinx","parthenon","mona-lisa","great-wave","starry-night","guernica")]
    body = f"""<section class="hero"><h1>Art history, from the very first image</h1>
<p>Humans were making art tens of thousands of years before writing. Start in the caves of the Stone Age and follow the story forward.</p>
<a class="btn" href="eras/prehistoric/">Begin: Prehistoric art</a><a class="btn alt" href="timeline/">Explore the timeline</a></section>
<h2>The journey</h2><div class="strip" aria-label="Eras">{strip}</div>
<h2>Featured works</h2><div class="grid">{''.join(work_card(w, r) for w in feat)}</div>
<h2>Browse</h2><div class="grid">
<a class="card" href="regions/"><h3>Regions</h3><p>Africa, Asia, the Americas, Oceania.</p></a>
<a class="card" href="movements/"><h3>Movements</h3><p>{len(MOV)} styles from Gothic to digital art.</p></a>
<a class="card" href="artists/"><h3>Artists</h3><p>{len(ARTISTS)} profiles.</p></a>
<a class="card" href="works/"><h3>Works</h3><p>{len(WORKS)} featured artworks.</p></a>
<a class="card" href="themes/"><h3>Themes</h3><p>Religion, power, nature, the body, technology.</p></a>
<a class="card" href="techniques/"><h3>Techniques</h3><p>Fresco, oil, bronze, printmaking and more.</p></a>
<a class="card" href="learn/"><h3>Learn</h3><p>Glossary, how-to guide and quizzes.</p></a></div>
<div class="callout">Did you know? A pig painted in a cave in Sulawesi has been dated to at least 45,500 years ago, among the oldest known figurative art.</div>"""
    write("index.html", "Art History — From the Stone Age Onward", "A chronological journey through art history, starting with the first images made by humans.", body)
    body = """<h1>Search</h1><div class="filters"><label>Search the site<input type="search" id="q" placeholder="e.g. Rembrandt, fresco, Egypt" autofocus></label></div><p class="meta" id="n"></p><ul class="results" id="r"></ul>
<script>var IDX=[];var root='..';
fetch('../assets/search.json').then(function(r){return r.json()}).then(function(d){IDX=d;var p=new URLSearchParams(location.search).get('q');if(p){document.getElementById('q').value=p}go()});
function go(){var q=document.getElementById('q').value.toLowerCase().trim();var ul=document.getElementById('r');ul.textContent='';if(!q){document.getElementById('n').textContent='';return}
var m=IDX.filter(function(x){return (x.t+' '+x.d+' '+x.k).toLowerCase().indexOf(q)>-1}).sort(function(a,b){return (b.t.toLowerCase().indexOf(q)>-1)-(a.t.toLowerCase().indexOf(q)>-1)}).slice(0,60);
document.getElementById('n').textContent=m.length+' results';
m.forEach(function(x){var li=document.createElement('li');var a=document.createElement('a');a.href=root+'/'+x.u;a.textContent=x.t;var s=document.createElement('span');s.className='tag';s.textContent=x.k;var p=document.createElement('p');p.textContent=x.d;li.append(a,document.createTextNode(' '),s,p);ul.appendChild(li)})}
document.getElementById('q').addEventListener('input',go);</script>"""
    write("search/index.html", "Search — Art History", "Search eras, works, artists and more.", body, [("Search", None)])
    body = """<h1>Contact</h1><div class="prose"><p>This is a static site with no contact form or mailing list.</p>
<p>To suggest a correction, a new work or an image with a clear open license, open an issue in the project repository. Please include a source for any factual correction.</p>
<p>See <a href="../about/">About</a> for sources and the accuracy policy.</p></div>"""
    write("contact/index.html", "Contact — Art History", "How to suggest corrections or additions.", body, [("Contact", None)])
    write("404.html", "Page not found — Art History", "Page not found.", '<h1>Page not found</h1><p>Try the <a href="/">home page</a> or <a href="/search/">search</a>.</p>')
    # 404 uses root-relative assets; fix for depth-0 file already relative "."

def build_search_and_sitemap():
    idx = []
    kinds = lambda p: p.split("/")[0] if "/" in p else "page"
    kmap = {"eras":"Era","regions":"Region","movements":"Movement","artists":"Artist","works":"Work","themes":"Theme","techniques":"Technique","learn":"Learn","timeline":"Timeline"}
    for p, t, d in written:
        if p in ("404.html","search/index.html") : continue
        u = p[:-len("index.html")] if p.endswith("index.html") else p
        idx.append(dict(t=t.replace(" — Art History",""), u=u, d=d, k=kmap.get(kinds(p), "Page")))
    for t, u, d in [("Paleolithic art","eras/prehistoric/paleolithic/","Cave painting, Venus figurines, Lascaux, Chauvet"),("Mesolithic art","eras/prehistoric/mesolithic/","Rock art, Göbekli Tepe, Levantine art"),("Neolithic art","eras/prehistoric/neolithic/","Pottery, Çatalhöyük, Newgrange, Stonehenge"),("Prehistoric art","eras/prehistoric/","Stone Age art overview"),("About","about/","About this site, sources and credits")]:
        idx.append(dict(t=t, u=u, d=d, k="Era" if "eras" in u else "Page"))
    (OUT / "assets").mkdir(exist_ok=True)
    (OUT / "assets/search.json").write_text(json.dumps(idx, ensure_ascii=False), encoding="utf-8")
    today = datetime.date.today().isoformat()
    urls = sorted({i["u"] for i in idx} | {""})
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>https://prashant-mehra.github.io/history-of-art/{u}</loc><lastmod>{today}</lastmod></url>\n" for u in urls) + "</urlset>\n"
    (OUT / "sitemap.xml").write_text(sm)
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\nSitemap: https://prashant-mehra.github.io/history-of-art/sitemap.xml\n")

def build_credits():
    names = {w["slug"]: w["title"] for w in WORKS}
    names.update({"p-lascaux":"Lascaux cave painting","p-chauvet":"Chauvet Cave painting (replica)","p-altamira":"Altamira bison","p-willendorf":"Venus of Willendorf","p-gobekli":"Göbekli Tepe","p-newgrange":"Newgrange"})
    body = '<h1>Image credits</h1><p class="prose">All photographs and reproductions come from Wikimedia Commons and are public domain or under the open license shown. Each page with an image repeats its credit. Licenses: CC BY and CC BY-SA require attribution, which is given here and under each image.</p><ul class="credits">'
    for k in sorted(IMG, key=lambda k: names.get(k, k).lower()):
        body += f'<li><b>{e(names.get(k, k))}</b><br><span class="meta">{credit_html(k)}</span></li>'
    write("about/credits/index.html", "Image credits — Art History", "Sources, authors and licenses for every image on the site.", body + "</ul>", [("About", "about/"), ("Image credits", None)])

def inject_prehistoric():
    for rel in ("paleolithic","mesolithic","neolithic"):
        p = OUT / f"eras/prehistoric/{rel}/index.html"
        t = p.read_text(encoding="utf-8")
        def sub(m):
            k = m.group(1)
            return f"<!--fig:{k}-->" + fig(k, "../../../..", m.group(2)) + "<!--/fig-->"
        t2 = re.sub(r"<!--fig:([\w-]+) alt=\"([^\"]*)\"-->.*?<!--/fig-->", lambda m: f"<!--fig:{m.group(1)} alt=\"{m.group(2)}\"-->" + fig(m.group(1), "../../../..", m.group(2)) + "<!--/fig-->", t, flags=re.S)
        if t2 != t: p.write_text(t2, encoding="utf-8")

build_eras(); build_regions(); build_movements(); build_artists(); build_works(); build_themes(); build_learn(); build_timeline(); build_misc(); build_credits(); inject_prehistoric(); build_search_and_sitemap()
print(len(written), "pages written")
