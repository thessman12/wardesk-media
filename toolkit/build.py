"""Render a WARDESK daily carousel from a content JSON.
Usage: python3 build.py posts/2026-10-11.json  -> out/2026-10-11/slide_01.png ...
"""
import json, os, sys, html, asyncio
from mapsvg import render as map_svg

HERE = os.path.dirname(os.path.abspath(__file__))
BRAND = json.load(open(os.path.join(HERE, "brand.json")))
W, H = 1080, 1350
E = html.escape

CSS = f"""
@font-face {{ font-family: Oswald; src: url('file://{HERE}/fonts/Oswald.ttf'); font-weight: 200 700; }}
@font-face {{ font-family: Anton; src: url('file://{HERE}/fonts/Anton.ttf'); }}
:root {{ --bg:#0B0D10; --panel:#141820; --red:#E5372B; --amber:#FFB020; --text:#F2F0EA; --muted:#8A8F98; --line:#262C35; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html,body {{ width:{W}px; height:{H}px; background:var(--bg); color:var(--text); font-family:Inter, sans-serif; overflow:hidden; }}
.slide {{ position:relative; width:{W}px; height:{H}px; display:flex; flex-direction:column; }}
.top {{ display:flex; align-items:center; justify-content:space-between; padding:38px 56px 0; height:110px; }}
.logo {{ display:flex; align-items:center; gap:14px; font-family:Anton; font-size:40px; letter-spacing:3px; }}
.logo .mark {{ width:34px; height:34px; border:4px solid var(--red); border-radius:50%; position:relative; }}
.logo .mark:before,.logo .mark:after {{ content:''; position:absolute; background:var(--red); }}
.logo .mark:before {{ left:11px; top:-10px; width:4px; height:46px; }}
.logo .mark:after {{ top:11px; left:-10px; height:4px; width:46px; }}
.logo b {{ color:var(--red); font-weight:400; }}
.meta {{ font-family:Oswald; font-weight:500; font-size:24px; letter-spacing:3px; color:var(--muted); text-transform:uppercase; text-align:right; }}
.tag {{ display:inline-flex; align-items:center; gap:12px; background:var(--red); color:#fff; font-family:Oswald; font-weight:600;
       font-size:26px; letter-spacing:3px; padding:8px 18px; text-transform:uppercase; }}
.tag.amber {{ background:var(--amber); color:#111; }}
.tag .dot {{ width:12px; height:12px; border-radius:50%; background:#fff; }}
.h1 {{ font-family:Anton; font-size:92px; line-height:.98; text-transform:uppercase; letter-spacing:.5px; }}
.h2 {{ font-family:Anton; font-size:66px; line-height:1.0; text-transform:uppercase; }}
.red {{ color:var(--red); }} .amber {{ color:var(--amber); }} .muted {{ color:var(--muted); }}
.foot {{ position:absolute; left:0; right:0; bottom:0; height:78px; display:flex; align-items:center; justify-content:space-between;
        padding:0 56px; border-top:2px solid var(--line); font-size:19px; color:var(--muted); background:var(--bg); }}
.foot .src {{ max-width:770px; font-size:17px; line-height:1.3; }}
.foot .h {{ font-family:Oswald; font-weight:600; font-size:24px; color:var(--text); letter-spacing:1px; }}
.mapwrap {{ position:relative; margin:18px 56px 0; border:2px solid var(--line); height:560px; overflow:hidden; }}
.mapwrap .day {{ position:absolute; left:18px; top:16px; }}
.mapwrap .legend {{ position:absolute; right:16px; bottom:14px; background:rgba(11,13,16,.85); padding:8px 14px; font-size:19px; color:var(--muted); display:flex; gap:18px; }}
.lg i {{ display:inline-block; width:14px; height:14px; border-radius:50%; margin-right:8px; vertical-align:-1px; }}
.body {{ padding:28px 56px 0; }}
.bul {{ list-style:none; margin-top:20px; }}
.bul li {{ position:relative; padding-left:38px; font-size:31px; line-height:1.28; font-weight:500; margin-bottom:16px; }}
.bul li:before {{ content:''; position:absolute; left:0; top:13px; width:20px; height:6px; background:var(--red); }}
.bul li b {{ font-weight:800; color:#fff; }}
.stats {{ display:grid; grid-template-columns:1fr 1fr; gap:22px; padding:30px 56px 0; }}
.stat {{ background:var(--panel); border-left:8px solid var(--red); padding:34px 30px; min-height:430px; display:flex; flex-direction:column; justify-content:center; }}
.stat.a {{ border-left-color:var(--amber); }}
.stat .n {{ font-family:Anton; font-size:118px; line-height:1; }}
.stat .l {{ font-size:30px; font-weight:600; margin-top:12px; line-height:1.25; }}
.stat .s {{ font-size:19px; color:var(--muted); margin-top:10px; }}
.cover {{ padding:20px 56px 0; }}
.cover .big {{ font-family:Anton; font-size:128px; line-height:.92; text-transform:uppercase; margin-top:26px; }}
.fronts {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:30px; }}
.front {{ background:var(--panel); padding:22px 24px; border-top:6px solid var(--red); }}
.front .k {{ font-family:Oswald; font-weight:600; font-size:24px; letter-spacing:3px; color:var(--muted); text-transform:uppercase; }}
.front .v {{ font-size:30px; font-weight:800; margin-top:8px; line-height:1.2; }}
.swipe {{ position:absolute; right:56px; bottom:104px; font-family:Oswald; font-weight:600; font-size:30px; letter-spacing:4px; color:var(--amber); }}
.watch {{ margin-top:34px; }} .watch li {{ font-size:36px; margin-bottom:34px; }}
.coverMap {{ margin:28px 0 0; border:2px solid var(--line); height:300px; overflow:hidden; }}
.cta {{ position:absolute; left:56px; right:56px; bottom:120px; background:var(--red); padding:30px 34px; }}
.cta .t {{ font-family:Anton; font-size:56px; text-transform:uppercase; line-height:1.05; }}
.cta .s {{ font-size:26px; margin-top:10px; font-weight:600; }}
"""


def logo():
    return '<div class="logo"><div class="mark"></div><span>WAR<b>DESK</b></span></div>'


def frame(inner, i, n, date_label, sources):
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div class="slide"><div class="top">{logo()}<div class="meta">{E(date_label)}</div></div>
{inner}
<div class="foot"><div class="src">{E(sources)}</div><div class="h">{E(BRAND['handle'])}</div></div></div></body></html>"""


def rich(t):
    # **bold** and [[red]] / {{amber}} markup
    t = E(t).replace("&lt;br&gt;", "<br>")
    import re
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"\[\[(.+?)\]\]", r'<span class="red">\1</span>', t)
    t = re.sub(r"\{\{(.+?)\}\}", r'<span class="amber">\1</span>', t)
    return t


def check_map(m, where):
    # Every point must be inside the map frame, or it silently disappears off the edge.
    lo0, la0, lo1, la1 = m["bbox"]
    for pt in m.get("points", []):
        if not (lo0 <= pt["lon"] <= lo1 and la0 <= pt["lat"] <= la1):
            print(f"WARNING: {where}: point '{pt.get('label', '?')}' ({pt['lon']}, {pt['lat']}) is outside bbox {m['bbox']} - widen the bbox")


def slide_html(s, i, n, date_label):
    k = s["type"]
    if k == "cover":
        fr = "".join(f'<div class="front"><div class="k">{E(f["k"])}</div><div class="v">{rich(f["v"])}</div></div>' for f in s["fronts"])
        cm = ""
        if s.get("map"):
            m = s["map"]
            cm = '<div class="coverMap">' + map_svg(tuple(m["bbox"]), W - 116, 296, highlight=m.get("highlight", []),
                 highlight_admin1=[tuple(x) for x in m.get("admin1", [])], points=m.get("points", []), labels=m.get("labels", [])) + '</div>'
        inner = f"""<div class="cover"><span class="tag"><span class="dot"></span>{E(s['kicker'])}</span>
<div class="big">{rich(s['title'])}</div><div class="fronts">{fr}</div>{cm}</div><div class="swipe">FULL BRIEF INSIDE</div>"""
    elif k == "map":
        m = s["map"]
        check_map(m, f"slide {i} ({s.get('tag', '')})")
        svg = map_svg(tuple(m["bbox"]), W - 112 - 4, 556, highlight=m.get("highlight", []),
                      highlight_admin1=[tuple(x) for x in m.get("admin1", [])], points=m.get("points", []),
                      labels=m.get("labels", []), arrows=[{"from": tuple(a[0]), "to": tuple(a[1])} for a in m.get("arrows", [])])
        legend = '<div class="legend"><span class="lg"><i style="background:#E5372B"></i>Attack / strike</span><span class="lg"><i style="background:#FFB020"></i>Key location</span></div>'
        bl = "".join(f"<li>{rich(b)}</li>" for b in s["bullets"])
        inner = f"""<div class="mapwrap">{svg}<div class="day"><span class="tag">{E(s['tag'])}</span></div>{legend}</div>
<div class="body"><div class="h2">{rich(s['headline'])}</div><ul class="bul">{bl}</ul></div>"""
    elif k == "stats":
        st = "".join(f'<div class="stat {"a" if x.get("amber") else ""}"><div class="n">{rich(x["n"])}</div><div class="l">{rich(x["l"])}</div><div class="s">{E(x.get("s",""))}</div></div>' for x in s["stats"])
        inner = f"""<div class="body"><span class="tag">{E(s['tag'])}</span><div class="h2" style="margin-top:22px">{rich(s['headline'])}</div></div>
<div class="stats">{st}</div>"""
    elif k == "watch":
        bl = "".join(f"<li>{rich(b)}</li>" for b in s["bullets"])
        inner = f"""<div class="body"><span class="tag amber">{E(s['tag'])}</span><div class="h2" style="margin-top:22px">{rich(s['headline'])}</div>
<ul class="bul watch">{bl}</ul></div><div class="cta"><div class="t">{rich(s['cta'])}</div><div class="s">{E(s['cta_sub'])}</div></div>"""
    else:
        raise ValueError(k)
    return frame(inner, i, n, date_label, s.get("sources", ""))


async def shoot(pages, outdir):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch(executable_path=os.environ.get("CHROME_PATH") or None, args=["--allow-file-access-from-files"])
        pg = await b.new_page(viewport={"width": W, "height": H})
        for idx, h in enumerate(pages, 1):
            f = os.path.join(outdir, f"slide_{idx:02d}.html")
            open(f, "w").write(h)
            await pg.goto("file://" + f)
            await pg.evaluate("document.fonts.ready")
            await pg.wait_for_timeout(150)
            await pg.screenshot(path=os.path.join(outdir, f"slide_{idx:02d}.png"))
            os.remove(f)
        await b.close()


def main(path):
    c = json.load(open(path))
    outdir = os.path.join(HERE, "out", c["date"])
    os.makedirs(outdir, exist_ok=True)
    n = len(c["slides"])
    pages = [slide_html(s, i, n, c["date_label"]) for i, s in enumerate(c["slides"], 1)]
    asyncio.run(shoot(pages, outdir))
    for name in ("caption_instagram", "caption_facebook"):
        open(os.path.join(outdir, name + ".txt"), "w").write(c[name])
    print(outdir)


if __name__ == "__main__":
    main(sys.argv[1])
