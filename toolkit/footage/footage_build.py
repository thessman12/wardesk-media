#!/usr/bin/env python3
"""WARDESK footage opener (carousel slide 1).
usage: python3 footage_build.py spec.json
spec = {"date_label": "SAT · OCT 17, 2026", "out": "footage.mp4",
        "clips": [{"src": "clip1.mp4", "start": 0.4, "dur": 7.0,
                   "kicker": "Iran war · Hormuz", "headline": "Short headline",
                   "credit": "Oct 10, 2026: what it shows. Video: U.S. Central Command"}, ...]}
Rules: 1-3 clips, each dur <= 10 s (hard-capped). Output 1080x1350 MP4 with original music.
Writes two files: "out" (Instagram carousel item, bottom bar "SWIPE FOR TODAY'S BRIEF") and
"out_fb" (default: <out>_fb.mp4; standalone Facebook video, bar "FOLLOW WARDESK FOR THE DAILY WAR BRIEF" -
Facebook videos can't be swiped). Scratch files go to a temp dir outside the repo.
Optional "today": one line (~60 chars) summing up the day's top story, shown above the bottom bar on every clip,
e.g. "Ukraine strikes St Petersburg oil terminal; Iran says 2 tankers hit mines".
Needs fonts/Anton.ttf + fonts/Oswald.ttf next to this file (or in toolkit/fonts) and music.py."""
import os, sys, json, shutil, subprocess, tempfile
from PIL import Image, ImageDraw, ImageFont
D = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, D)
import music
W, H, FPS = 1080, 1350, 30
BG = (11, 13, 16); RED = (229, 55, 43); AMBER = (255, 176, 32); TXT = (242, 240, 234); MUTED = (138, 143, 152)
FD = next(p for p in [f"{D}/fonts", f"{D}/toolkit/fonts", f"{D}/../toolkit/fonts"] if os.path.exists(f"{p}/Anton.ttf"))
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
CTA_IG = "SWIPE FOR TODAY'S BRIEF  »"
CTA_FB = "FOLLOW WARDESK FOR THE DAILY WAR BRIEF"
def overlay(out, date, kicker, headline, credit, cta, today=""):
    o = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(o)
    grad = Image.new("RGBA", (W, 420), (0, 0, 0, 0)); g = ImageDraw.Draw(grad)
    for y in range(420): g.line([0, y, W, y], fill=(11, 13, 16, int(240 * max(0, 1 - y / 420) ** 0.5)))
    o.alpha_composite(grad, (0, 0))
    f = A(46); d.text((50, 40), "WAR", font=f, fill=TXT); d.text((50 + f.getlength("WAR"), 40), "DESK", font=f, fill=RED)
    f2 = O(28); d.text((W - 50 - f2.getlength(date), 54), date, font=f2, fill=MUTED)
    f = O(30); kw = f.getlength(kicker.upper()) + 36
    d.rectangle([50, 120, 50 + kw, 170], fill=RED); d.text((68, 123), kicker.upper(), font=f, fill=TXT)
    fh = A(78); y = 190
    for ln in wrap(headline.upper(), fh, W - 100)[:2]: d.text((50, y), ln, font=fh, fill=TXT); y += 90
    vb = (H + 608) // 2 + 24; fc = O(32); lines = wrap(credit, fc, W - 140)[:3 if today else 4]
    d.rectangle([50, vb, 57, vb + 46 * len(lines) - 8], fill=AMBER)
    for i, ln in enumerate(lines): d.text((76, vb + i * 46), ln, font=fc, fill=TXT)
    if today:
        lab = "TODAY  "; ty = H - 92 - 66
        for size in (34, 31, 28):
            ft = O(size)
            if ft.getlength(lab) + ft.getlength(today) <= W - 100: break
        while ft.getlength(lab) + ft.getlength(today) > W - 100: today = today[:-2].rstrip() + "…"
        d.text((50, ty), lab, font=ft, fill=AMBER); d.text((50 + ft.getlength(lab), ty), today, font=ft, fill=TXT)
    fs = O(34)
    d.rectangle([0, H - 92, W, H], fill=RED); d.text(((W - fs.getlength(cta)) / 2, H - 80), cta, font=fs, fill=TXT)
    o.save(out)
def render_video(sp, clips, cta, T, tag, music_wav, total, out_path):
    outs = []
    for i, c in enumerate(clips):
        ov = f"{T}/{tag}_o{i}.png"; overlay(ov, sp["date_label"], c["kicker"], c["headline"], c["credit"], cta, sp.get("today", ""))
        out = f"{T}/{tag}_s{i}.mp4"; n = int(round(c["dur"] * FPS))
        fc = (f"[0:v]trim=start={c['start']}:duration={c['dur']},setpts=PTS-STARTPTS,fps={FPS},split[a][b];"
              f"[a]scale=-2:{H},crop={W}:{H},boxblur=30:4,eq=brightness=-0.3[bg];[b]scale={W}:-2[fg];"
              f"[bg][fg]overlay=(W-w)/2:(H-h)/2[v];[v][1:v]overlay=0:0,format=yuv420p")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", c["src"], "-i", ov, "-filter_complex", fc, "-frames:v", str(n),
                        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "18", out], check=True)
        outs.append(out)
    open(f"{T}/{tag}_l.txt", "w").write("".join(f"file '{p}'\n" for p in outs))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", f"{T}/{tag}_l.txt", "-c", "copy", f"{T}/{tag}_v.mp4"], check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", f"{T}/{tag}_v.mp4", "-ss", str(music.HOOK_S - 0.15), "-i", music_wav,
                    "-af", "afade=t=out:st=%.2f:d=1.2,loudnorm=I=-14:TP=-1.5:LRA=11" % (total - 1.2),
                    "-c:v", "libx264", "-b:v", "3500k", "-preset", "slow", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", out_path], check=True)
def main():
    sp = json.load(open(sys.argv[1]))
    out_fb = sp.get("out_fb") or os.path.splitext(sp["out"])[0] + "_fb.mp4"
    T = tempfile.mkdtemp(prefix="wardesk_footage_")
    try:
        clips = sp["clips"][:3]
        for c in clips: c["dur"] = min(float(c["dur"]), 10.0)
        total = sum(c["dur"] for c in clips); cuts = []; t = music.HOOK_S
        for c in clips[:-1]: t += c["dur"]; cuts.append(t)
        music.render(f"{T}/m.wav", cuts=cuts, end_start=music.HOOK_S + total, total_len=music.HOOK_S + total + 0.6)
        render_video(sp, clips, CTA_IG, T, "ig", f"{T}/m.wav", total, sp["out"])
        render_video(sp, clips, CTA_FB, T, "fb", f"{T}/m.wav", total, out_fb)
    finally:
        shutil.rmtree(T, ignore_errors=True)
    print(sp["out"], out_fb, round(total, 2), "s")
if __name__ == "__main__": main()
