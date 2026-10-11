"""Tiny GeoJSON -> SVG map renderer (Mercator), no external deps."""
import json, math, os

HERE = os.path.dirname(os.path.abspath(__file__))
_cache = {}


def _load(name):
    if name not in _cache:
        _cache[name] = json.load(open(os.path.join(HERE, "data", name)))["features"]
    return _cache[name]


def merc(lon, lat):
    lat = max(min(lat, 85), -85)
    return lon, math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))


def _bbox_hit(geom, bb):
    lo0, la0, lo1, la1 = bb
    def walk(c):
        if isinstance(c[0], (int, float)):
            return lo0 - 15 <= c[0] <= lo1 + 15 and la0 - 15 <= c[1] <= la1 + 15
        return any(walk(x) for x in c)
    return walk(geom["coordinates"])


def render(bbox, W, H, highlight=(), highlight_admin1=(), points=(), labels=(),
           colors=None, arrows=()):
    """bbox=(lon0,lat0,lon1,lat1). highlight: country ADMIN names (red).
    highlight_admin1: list of (admin, name, color). points: dicts lon,lat,label,kind.
    labels: dicts lon,lat,text (big muted country labels)."""
    c = dict(bg="#0E1116", land="#232B36", edge="#3A4552", hi="#E5372B",
             hi_fill="#3A1714", text="#F2F0EA", muted="#7F8794", amber="#FFB020",
             sea="#0B0E12")
    if colors:
        c.update(colors)
    x0, y0 = merc(bbox[0], bbox[1])
    x1, y1 = merc(bbox[2], bbox[3])
    s = min(W / (x1 - x0), H / (y1 - y0))
    ox = (W - (x1 - x0) * s) / 2
    oy = (H - (y1 - y0) * s) / 2

    def P(lon, lat):
        x, y = merc(lon, lat)
        return ox + (x - x0) * s, H - (oy + (y - y0) * s)

    def path(geom):
        polys = geom["coordinates"] if geom["type"] == "MultiPolygon" else [geom["coordinates"]]
        d = []
        for poly in polys:
            for ring in poly:
                pts = [P(*pt[:2]) for pt in ring]
                # decimate
                out, last = [], None
                for p in pts:
                    if last is None or abs(p[0] - last[0]) + abs(p[1] - last[1]) > 0.8:
                        out.append(p); last = p
                if len(out) < 3:
                    continue
                d.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in out) + "Z")
        return "".join(d)

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">',
             f'<defs><pattern id="hatch" width="10" height="10" patternTransform="rotate(45)" patternUnits="userSpaceOnUse">'
             f'<line x1="0" y1="0" x2="0" y2="10" stroke="{c["hi"]}" stroke-width="3" stroke-opacity=".55"/></pattern>'
             f'<radialGradient id="glow"><stop offset="0" stop-color="{c["hi"]}" stop-opacity=".55"/>'
             f'<stop offset="1" stop-color="{c["hi"]}" stop-opacity="0"/></radialGradient></defs>',
             f'<rect width="{W}" height="{H}" fill="{c["sea"]}"/>']
    # graticule
    for lon in range(-180, 181, 5):
        if bbox[0] - 5 < lon < bbox[2] + 5:
            xa, _ = P(lon, 0)
            parts.append(f'<line x1="{xa:.0f}" y1="0" x2="{xa:.0f}" y2="{H}" stroke="#ffffff" stroke-opacity=".04"/>')
    for lat in range(-80, 81, 5):
        if bbox[1] - 5 < lat < bbox[3] + 5:
            _, ya = P(0, lat)
            parts.append(f'<line x1="0" y1="{ya:.0f}" x2="{W}" y2="{ya:.0f}" stroke="#ffffff" stroke-opacity=".04"/>')

    hi = set(highlight)
    for f in _load("countries.geojson"):
        if not _bbox_hit(f["geometry"], bbox):
            continue
        name = f["properties"]["ADMIN"]
        if name in hi:
            parts.append(f'<path d="{path(f["geometry"])}" fill="{c["hi_fill"]}" stroke="{c["hi"]}" stroke-width="2.5"/>')
        else:
            parts.append(f'<path d="{path(f["geometry"])}" fill="{c["land"]}" stroke="{c["edge"]}" stroke-width="1"/>')

    if highlight_admin1:
        want = {(a, n): col for a, n, col in highlight_admin1}
        for f in _load("admin1.geojson"):
            p = f["properties"]
            key = (p.get("admin"), p.get("name"))
            if key in want:
                col = want[key]
                fill = "url(#hatch)" if col == "hatch" else col
                stroke = c["hi"] if col == "hatch" else col
                parts.append(f'<path d="{path(f["geometry"])}" fill="{fill}" fill-opacity="{1 if col=="hatch" else .35}" stroke="{stroke}" stroke-width="2"/>')

    for l in labels:
        x, y = P(l["lon"], l["lat"])
        parts.append(f'<text x="{x:.0f}" y="{y:.0f}" fill="{l.get("color", c["muted"])}" font-family="Oswald" font-weight="500" '
                     f'font-size="{l.get("size", 30)}" letter-spacing="6" text-anchor="middle" opacity=".9">{l["text"].upper()}</text>')

    for a in arrows:
        xa, ya = P(*a["from"]); xb, yb = P(*a["to"])
        mx, my = (xa + xb) / 2, (ya + yb) / 2 - abs(xb - xa) * 0.25
        parts.append(f'<path d="M{xa:.0f},{ya:.0f} Q{mx:.0f},{my:.0f} {xb:.0f},{yb:.0f}" fill="none" stroke="{c["amber"]}" '
                     f'stroke-width="4" stroke-dasharray="12 8"/>')

    for pt in points:
        x, y = P(pt["lon"], pt["lat"])
        kind = pt.get("kind", "strike")
        col = c["amber"] if kind == "info" else c["hi"]
        if kind == "strike":
            parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="46" fill="url(#glow)"/>')
        parts.append(f'<circle cx="{x:.0f}" cy="{y:.0f}" r="11" fill="{col}" stroke="#0E1116" stroke-width="4"/>')
        dx = pt.get("dx", 20); dy = pt.get("dy", 8)
        anchor = "end" if dx < 0 else "start"
        lab = pt.get("label", "")
        sub = pt.get("sub", "")
        parts.append(f'<text x="{x+dx:.0f}" y="{y+dy:.0f}" fill="{c["text"]}" font-family="Inter" font-weight="800" font-size="30" '
                     f'text-anchor="{anchor}" paint-order="stroke" stroke="{c["sea"]}" stroke-width="8">{lab}</text>')
        if sub:
            parts.append(f'<text x="{x+dx:.0f}" y="{y+dy+32:.0f}" fill="{col}" font-family="Inter" font-weight="700" font-size="23" '
                         f'text-anchor="{anchor}" paint-order="stroke" stroke="{c["sea"]}" stroke-width="7">{sub}</text>')
    parts.append("</svg>")
    return "".join(parts)
