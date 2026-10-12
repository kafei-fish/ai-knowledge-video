"""合成成片：镜头 → 转场 → 调色暗角 → 字幕和片头 → 配音 + 配乐混音 → mp4，并导出检查用的缩略图。

用法：
  python3 scripts/compose.py EP [--no-music] [--draft]

--draft  540p 快速预览，几十秒出片，用来检查节奏；满意后去掉它出正式版。
需要先跑完：tts.py → timeline.py →（music.py，可选）→ 即梦素材到位
产出：EP/out/<文件名>.mp4，EP/build/check/contact.jpg（每 5 秒一帧的拼图，交付前自己看一遍）
"""
import argparse
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).parent))
from cards import render  # noqa: E402
from common import die, duration, ep_dir, find_font, load_json, run  # noqa: E402

SR = 48000
XF = 0.35  # 镜头之间的交叉淡化秒数


def ass_color(rgb):
    r, g, b = rgb
    return f"&H00{b:02X}{g:02X}{r:02X}"


def ts(t):
    t = max(t, 0)
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    return f"{h}:{m:02d}:{s:05.2f}"


def build_ass(tl, brief, fname, path):
    w, h = tl["w"], tl["h"]
    portrait = h > w
    k = w / 1920 if not portrait else w / 1080
    sub = int((54 if not portrait else 62) * k)
    mv = int(70 * k) if not portrait else int(330 * k)
    ivory, gold, dim = ass_color((237, 230, 214)), ass_color((232, 194, 119)), ass_color((190, 182, 168))
    styles = [
        f"Style: Sub,{fname},{sub},{ivory},{ivory},&H00000000,&H96000000,-1,0,0,0,100,100,2,0,1,2,3,2,80,80,{mv},1",
        f"Style: Series,{fname},{int(sub * 1.0)},{gold},{gold},&H00000000,&H80000000,-1,0,0,0,100,100,4,0,1,0,2,5,40,40,0,1",
        f"Style: Title,{fname},{int(sub * (2.6 if not portrait else 2.2))},{ivory},{ivory},&H00000000,&H80000000,-1,0,0,0,100,100,6,0,1,0,4,5,40,40,0,1",
        f"Style: Hook,{fname},{int(sub * 0.9)},{gold},{gold},&H00000000,&H80000000,-1,0,0,0,100,100,2,0,1,0,2,5,40,40,0,1",
        f"Style: Badge,{fname},{int(26 * k)},{dim},{dim},&H00000000,&H00000000,0,0,0,0,100,100,1,0,1,0,0,7,0,0,0,1",
    ]
    ev = []
    # 片头：合集名 · 期数 / 标题 / 钩子
    hd = brief.get("header", {})
    t0, t1 = hd.get("start", 0.2), hd.get("end", 3.4)
    cy = h * (0.42 if not portrait else 0.30)
    series = f"{brief.get('series', '')} · {brief.get('episode', '')}".strip(" ·")
    if series:
        ev.append(f"Dialogue: 2,{ts(t0)},{ts(t1)},Series,,0,0,0,,{{\\pos({w / 2:.0f},{cy - sub * 1.9:.0f})\\fad(300,400)}}{series}")
    if brief.get("title"):
        ev.append(f"Dialogue: 2,{ts(t0 + 0.15)},{ts(t1)},Title,,0,0,0,,{{\\pos({w / 2:.0f},{cy:.0f})\\fad(400,400)}}{brief['title']}")
    if hd.get("hook"):
        ev.append(f"Dialogue: 2,{ts(t0 + 0.5)},{ts(t1)},Hook,,0,0,0,,{{\\pos({w / 2:.0f},{cy + sub * 2.2:.0f})\\fad(300,400)}}{hd['hook']}")
    # 角标
    if brief.get("badge", True):
        ev.append(f"Dialogue: 1,{ts(0)},{ts(tl['total'])},Badge,,0,0,0,,{{\\pos({int(36 * k)},{int(30 * k)})}}AI生成")
    if brief.get("signature"):
        ev.append(f"Dialogue: 1,{ts(0)},{ts(tl['total'])},Badge,,0,0,0,,{{\\an9\\pos({w - int(36 * k)},{int(30 * k)})}}{brief['signature']}")
    # 字幕（片头显示期间不出字幕，避免叠字）
    quiet = [(x["start"], x["end"]) for x in tl["shots"] if x.get("hide_subs")]
    for ln in tl["lines"]:
        s, e = ln["s"], ln["e"]
        if any(a <= s < b for a, b in quiet):
            continue
        if e <= t1 and s < t1 and brief.get("hide_subs_under_header", False):
            continue
        tag = "{\\fad(120,80)" + (f"\\c{gold}" if ln.get("emph") else "") + "}"
        ev.append(f"Dialogue: 0,{ts(s)},{ts(e)},Sub,,0,0,0,,{tag}{ln['t']}")
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {w}\nPlayResY: {h}\nWrapStyle: 2\nScaledBorderAndShadow: yes\n\n"
            "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, "
            "Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
            + "\n".join(styles) + "\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")
    Path(path).write_text(head + "\n".join(ev) + "\n", encoding="utf-8")


def gradient(w, h, path):
    a = np.zeros((h, w), np.float32)
    y = np.linspace(0, 1, h)[:, None]
    a += np.clip((0.30 - y) / 0.30, 0, 1) ** 1.5 * 0.45
    a += np.clip((y - 0.58) / 0.42, 0, 1) ** 1.3 * 0.70
    x = np.linspace(-1, 1, w)[None, :]
    yy = np.linspace(-1, 1, h)[:, None]
    a += np.clip((x ** 2 + yy ** 2) ** 0.5 - 0.75, 0, 1) * 0.35
    rgba = np.zeros((h, w, 4), np.uint8)
    rgba[..., 3] = (np.clip(a, 0, 0.85) * 255).astype(np.uint8)
    Image.fromarray(rgba, "RGBA").save(path)


def shot_video(ep, shot, dur, w, h, fp, out, draft):
    push = shot.get("push", 0.08 if shot["type"] == "clip" else 0.035)
    zoom = f"trunc({w}*(1.03+{push}*t/{dur:.3f})/2)*2"
    move = f"scale=w='{zoom}':h=-2:eval=frame,crop={w}:{h}"
    enc = ["-c:v", "libx264", "-preset", "ultrafast" if draft else "veryfast", "-crf", "23" if draft else "16",
           "-pix_fmt", "yuv420p", "-r", "30", "-an", str(out)]
    if shot["type"] == "clip":
        src = ep / shot.get("src", f"assets/clips/{shot['id']}.mp4")
        if not src.exists():
            die(f"缺少即梦片段 {src}（镜头 {shot['id']}）")
        sd = duration(src) - shot.get("trim", 0) - 0.05
        slow = max(1.0, dur / max(sd, 0.5))
        loop = []
        if slow > shot.get("max_slow", 1.6):  # 太慢会卡顿：改成循环播放
            slow = 1.0
            loop = ["-stream_loop", "-1"]
            print(f"[提示] 镜头 {shot['id']} 要 {dur:.1f} 秒，片段只有 {sd:.1f} 秒，只能循环播放。建议在这段旁白里多切一两个镜头")
        vf = (f"setpts={slow:.4f}*(PTS-STARTPTS),fps=30,scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},"
              f"{move},eq=saturation={shot.get('saturation', 0.92)}:contrast=1.06")
        cmd = ["ffmpeg", "-v", "error", "-y", *loop, "-ss", str(shot.get("trim", 0)), "-i", str(src), "-t", f"{dur:.3f}", "-vf", vf, *enc]
    else:
        png = out.with_suffix(".png")
        render(shot, w, h, fp, ep).save(png)
        vf = f"fps=30,{move}"
        cmd = ["ffmpeg", "-v", "error", "-y", "-loop", "1", "-i", str(png), "-t", f"{dur:.3f}", "-vf", vf, *enc]
    run(cmd)


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.float32).reshape(-1, 2).copy()


def mix(ep, tl, use_music, path):
    n = int((tl["total"] + 0.5) * SR)
    vo = np.zeros((n, 2), np.float32)
    talk = np.zeros(n, np.float32)
    for s in tl["segments"]:
        a = decode(ep / s["file"])
        i = int(s["at"] * SR)
        j = min(n, i + len(a))
        vo[i:j] += a[: j - i]
        talk[i:j] = 1
    pk = np.abs(vo).max() or 1
    vo *= 0.9 / pk
    out = vo
    if use_music:
        cand = [p for p in [ep / "assets" / "music.mp3", ep / "assets" / "music.wav", ep / "build" / "music.wav"] if p.exists()]
        if cand:
            m = decode(cand[0])[:n]
            m = np.pad(m, ((0, n - len(m)), (0, 0)))
            m *= 0.8 / (np.abs(m).max() or 1)
            k = int(0.4 * SR)  # 人声出现时把音乐压低，平滑 0.4 秒
            duck = np.convolve(talk, np.ones(k) / k, mode="same")
            gain = 0.42 - 0.24 * duck
            out = vo + m * gain[:, None]
        else:
            print("[提示] 没找到配乐（assets/music.* 或 build/music.wav），只用配音")
    out /= max(np.abs(out).max(), 1e-6) / 0.95
    import wave
    with wave.open(str(path), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())


def contact(video, total, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    for f in outdir.glob("f_*.jpg"):
        f.unlink()
    times = [round(t, 1) for t in np.arange(1.0, total, 5.0)]
    for i, t in enumerate(times):
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(t), "-i", str(video), "-frames:v", "1", "-vf", "scale=480:-2",
                        str(outdir / f"f_{i:02d}.jpg")])
    ims = [Image.open(p) for p in sorted(outdir.glob("f_*.jpg"))]
    if not ims:
        return None
    cols = 4
    tw, th = ims[0].size
    sheet = Image.new("RGB", (cols * tw, ((len(ims) + cols - 1) // cols) * (th + 28)), (20, 20, 20))
    d = ImageDraw.Draw(sheet)
    for i, (im, t) in enumerate(zip(ims, times)):
        x, y = i % cols * tw, i // cols * (th + 28)
        sheet.paste(im, (x, y + 28))
        d.text((x + 8, y + 6), f"{t:.0f}s", fill=(230, 230, 230))
    p = outdir / "contact.jpg"
    sheet.save(p, quality=85)
    return p


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--no-music", action="store_true")
    ap.add_argument("--draft", action="store_true")
    a = ap.parse_args()
    ep = ep_dir(a.ep)
    brief = load_json(ep / "brief.json")
    tl = load_json(ep / "build" / "timeline.json")
    fname, fpath = find_font(brief)
    w, h = tl["w"], tl["h"]
    if a.draft:
        w, h = (w // 2 // 2 * 2, h // 2 // 2 * 2)
        tl = {**tl, "w": w, "h": h}
    b = ep / "build"
    seg_dir = b / "shots"
    seg_dir.mkdir(parents=True, exist_ok=True)

    shots = tl["shots"]
    files = []
    for k, s in enumerate(shots):
        dur = s["end"] - s["start"] + (XF if k < len(shots) - 1 else 0)
        out = seg_dir / f"{k:02d}_{s['id']}.mp4"
        shot_video(ep, s, dur, w, h, fpath, out, a.draft)
        files.append(out)
        print(f"镜头 {k + 1}/{len(shots)} {s['id']} {s['type']} {dur:.1f}s")

    # 转场串联
    inputs = sum([["-i", str(f)] for f in files], [])
    if len(files) == 1:
        chain, last = "[0:v]null[v0]", "v0"
    else:
        parts, prev = [], "0:v"
        for k in range(1, len(files)):
            lab = f"x{k}"
            parts.append(f"[{prev}][{k}:v]xfade=transition=fade:duration={XF}:offset={shots[k]['start']:.3f}[{lab}]")
            prev = lab
        chain, last = ";".join(parts), prev
    joined = b / "joined.mp4"
    run(["ffmpeg", "-v", "error", "-y", *inputs, "-filter_complex", chain, "-map", f"[{last}]",
         "-c:v", "libx264", "-preset", "ultrafast" if a.draft else "veryfast", "-crf", "23" if a.draft else "16", "-pix_fmt", "yuv420p", str(joined)])

    # 字幕、暗角、配音配乐
    ass = b / "subs.ass"
    build_ass(tl, brief, fname, ass)
    grad = b / "gradient.png"
    gradient(w, h, grad)
    wav = b / "mix.wav"
    mix(ep, tl, not a.no_music, wav)
    name = brief.get("filename") or f"{brief.get('series', '')}{brief.get('episode', '').replace('EP.', '')}_{brief.get('title', 'video')}"
    outdir = ep / "out"
    outdir.mkdir(exist_ok=True)
    final = outdir / (name + ("_预览" if a.draft else "") + ".mp4")
    total = tl["total"]
    fonts_dir = str(Path(fpath).parent)
    ass_arg = str(ass).replace("\\", "/").replace(":", "\\:")
    vf = (f"[0:v][1:v]overlay=0:0,fade=t=in:st=0:d=0.5,fade=t=out:st={total - 1.2:.2f}:d=1.2,"
          f"ass='{ass_arg}':fontsdir='{fonts_dir}'[v]")
    run(["ffmpeg", "-v", "error", "-y", "-i", str(joined), "-i", str(grad), "-i", str(wav), "-filter_complex", vf,
         "-map", "[v]", "-map", "2:a", "-af", "loudnorm=I=-15:TP=-1.5:LRA=11", "-t", f"{total:.3f}",
         "-c:v", "libx264", "-preset", "ultrafast" if a.draft else "fast", "-crf", "23" if a.draft else "18",
         "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart", str(final)])
    sheet = contact(final, total, b / "check")
    print(f"成片：{final}（{total:.1f} 秒，{w}x{h}）")
    if sheet:
        print(f"检查拼图：{sheet}")


if __name__ == "__main__":
    main()
