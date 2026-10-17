#!/usr/bin/env python3
"""WARDESK evening Reel (9:16, ~20-30 s): real-footage hook + text cards + end card, original music.
usage: python3 evening_reel.py spec.json
spec = {"date_label": "SAT · OCT 18, 2026", "out": "reel.mp4",
        "segments": [
          {"type": "clip", "src": "c.mp4", "start": 1.0, "dur": 6.0, "kicker": "Iran war · Hormuz",
           "headline": "Short headline", "credit": "Oct 17, 2026: what it shows. Video: U.S. Central Command"},
          {"type": "card", "dur": 4.8, "kicker": "What happened", "headline": "Short headline",
           "body": ["Line one (Reuters)", "Line two (AP)"], "source": "Sources: Reuters, AP"}]}
Rules: first segment should be a clip; clips <= 10 s each (hard-capped); 2-5 segments; an end card is added automatically.
Fonts: toolkit/fonts/Anton.ttf + Oswald.ttf (or fonts/ next to this file). Needs music.py (same folder) + pedalboard."""
import os, sys, json, subprocess
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import music
W, H, FPS = 1080, 1920, 30
BG = (11, 13, 16); RED = (229, 55, 43); AMBER = (255, 176, 32); TXT = (242, 240, 234); MUTED = (138, 143, 152); LINE = (32, 36, 44)
FD = next(p for p in [f"{D}/fonts", f"{D}/../fonts", f"{D}/toolkit/fonts", f"{D}/../toolkit/fonts"] if os.path.exists(f"{p}/Anton.ttf"))
END_S = music.END_S
def A(s): return ImageFont.truetype(f"{FD}/Anton.ttf", s)
def O(s): return ImageFont.truetype(f"{FD}/Oswald.ttf", s)
def wrap(text, font, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if font.getlength(t) <= maxw: cur = t
        else: lines.append(cur); cur = w
    if cur: lines.append(cur)
    return lines
def fit(text, maker, sizes, maxw, maxlines):
    for s in sizes:
        f = maker(s); ls = wrap(text, f, maxw)
        if len(ls) <= maxlines: return f, ls, s
    return f, ls[:maxlines], s
def chrome(d, date, handle=True):
    f = A(54); d.text((60, 80), "WAR", font=f, fill=TXT); d.text((60 + f.getlength("WAR"), 80), "DESK", font=f, fill=RED)
    f2 = O(30); d.text((W - 60 - f2.getlength(date), 98), date, font=f2, fill=MUTED)
    if handle: d.text((60, H - 150), "@wardesk_daily", font=O(34), fill=MUTED)
def pill(d, x, y, text, size=34):
    f = O(size); kw = f.getlength(text.upper()) + 40
    d.rectangle([x, y, x + kw, y + 56], fill=RED); d.text((x + 20, y + 4), text.upper(), font=f, fill=TXT)
def clip_overlay(out, date, kicker, headline, credit):
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    grad = Image.new("RGBA", (W, 760), (0, 0, 0, 0)); g = ImageDraw.Draw(grad)
    for y in range(760): g.line([0, y, W, y], fill=(11, 13, 16, int(235 * max(0, 1 - y / 760) ** 0.6)))
    o.alpha_composite(grad, (0, 0)); chrome(d, date, handle=False)
    pill(d, 60, 250, kicker)
    fh, ls, s = fit(headline.upper(), A, [96, 84, 74], W - 120, 3); y = 340
    for ln in ls: d.text((60, y), ln, font=fh, fill=TXT); y += int(s * 1.17)
    vb = (H + 608) // 2 + 30; fc = O(38); cl = wrap(credit, fc, W - 160)[:4]
    d.rectangle([60, vb, 68, vb + 54 * len(cl) - 10], fill=AMBER)
    for i, ln in enumerate(cl): d.text((90, vb + i * 54), ln, font=fc, fill=TXT)
    o.save(out)
def card_png(out, date, kicker, headline, body, source):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img)
    for x in range(0, W, 90): d.line([x, 0, x, H], fill=(16, 19, 24))
    for y in range(0, H, 90): d.line([0, y, W, y], fill=(16, 19, 24))
    chrome(d, date); d.rectangle([0, 0, W, 10], fill=RED)
    y = 400; pill(d, 60, y, kicker); y += 100
    fh, ls, s = fit(headline.upper(), A, [110, 96, 84, 74], W - 120, 3)
    for ln in ls: d.text((60, y), ln, font=fh, fill=TXT); y += int(s * 1.15)
    y += 40; d.rectangle([60, y, W - 60, y + 3], fill=LINE); y += 50
    fb = O(46)
    for b in body[:4]:
        bl = wrap(b, fb, W - 170)[:3]
        d.rectangle([60, y + 22, 76, y + 38], fill=AMBER)
        for ln in bl: d.text((100, y), ln, font=fb, fill=TXT); y += 64
        y += 26
    if source: d.text((60, min(y + 20, H - 260)), source, font=O(32), fill=MUTED)
    img.save(out)
def end_png(out, date):
    img = Image.new("RGB", (W, H), BG); d = ImageDraw.Draw(img); chrome(d, date, handle=False)
    f = A(150); t1, t2 = "WAR", "DESK"; w = f.getlength(t1 + t2); x = (W - w) / 2
    d.text((x, 700), t1, font=f, fill=TXT); d.text((x + f.getlength(t1), 700), t2, font=f, fill=RED)
    for i, (s, c, sz) in enumerate([("THE WAR BRIEF. EVERY MORNING.", TXT, 52), ("FOLLOW @wardesk_daily", AMBER, 48)]):
        ff = O(sz); d.text(((W - ff.getlength(s)) / 2, 920 + i * 90), s, font=ff, fill=c)
    d.rectangle([(W - 160) / 2, 1140, (W + 160) / 2, 1148], fill=RED)
    img.save(out)
def run(cmd): subprocess.run(cmd, check=True)
def still(png, out, dur, zoom=0.035):
    n = int(round(dur * FPS))
    run(["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", png, "-vf",
         f"scale=2160:3840,zoompan=z='1+{zoom}*on/{n}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={n}:s={W}x{H}:fps={FPS},format=yuv420p",
         "-frames:v", str(n), "-c:v", "libx264", "-preset", "fast", "-crf", "18", out])
def clip(c, date, T, i):
    ov = f"{T}/o{i}.png"; clip_overlay(ov, date, c["kicker"], c["headline"], c["credit"]); out = f"{T}/seg{i:02d}.mp4"
    n = int(round(c["dur"] * FPS))
    fc = (f"[0:v]trim=start={c['start']}:duration={c['dur']},setpts=PTS-STARTPTS,fps={FPS},split[a][b];"
          f"[a]scale=-2:{H},crop={W}:{H},boxblur=30:4,eq=brightness=-0.25[bg];[b]scale={W}:-2[fg];"
          f"[bg][fg]overlay=(W-w)/2:(H-h)/2[v];[v][1:v]overlay=0:0,format=yuv420p")
    run(["ffmpeg", "-v", "error", "-y", "-i", c["src"], "-i", ov, "-filter_complex", fc, "-frames:v", str(n),
         "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18", out])
    return out
def main():
    sp = json.load(open(sys.argv[1])); date = sp["date_label"]
    T = os.path.join(os.path.dirname(os.path.abspath(sp["out"])), "_etmp"); os.makedirs(T, exist_ok=True)
    segs, bounds, t = [], [], 0.0
    for i, s in enumerate(sp["segments"][:5]):
        if s["type"] == "clip":
            s["dur"] = min(float(s["dur"]), 10.0); segs.append(clip(s, date, T, i))
        else:
            s["dur"] = float(s.get("dur", 4.8)); p = f"{T}/c{i}.png"
            card_png(p, date, s["kicker"], s["headline"], s.get("body", []), s.get("source", ""))
            out = f"{T}/seg{i:02d}.mp4"; still(p, out, s["dur"]); segs.append(out)
        t += s["dur"]; bounds.append(t)
    end_start = t; p = f"{T}/end.png"; end_png(p, date); out = f"{T}/seg99.mp4"; still(p, out, END_S, 0.02); segs.append(out)
    total = t + END_S
    open(f"{T}/l.txt", "w").write("".join(f"file '{x}'\n" for x in segs))
    run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{T}/l.txt", "-c", "copy", f"{T}/v.mp4"])
    hs = music.HOOK_S
    music.render(f"{T}/m.wav", cuts=[hs + b for b in bounds[:-1]], end_start=hs + end_start, total_len=hs + total + 0.6)
    run(["ffmpeg", "-v", "error", "-y", "-i", f"{T}/v.mp4", "-ss", str(hs - 0.15), "-i", f"{T}/m.wav",
         "-af", "afade=t=out:st=%.2f:d=1.4,loudnorm=I=-14:TP=-1.5:LRA=11" % (total - 1.4),
         "-c:v", "libx264", "-b:v", "4000k", "-preset", "slow", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", sp["out"]])
    print(sp["out"], round(total, 2), "s", os.path.getsize(sp["out"]) // 1024, "KB")
if __name__ == "__main__": main()
