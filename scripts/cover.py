"""封面：三行字（合集名 · 期数 / 标题 / 钩子），横版 16:9、竖版 3:4 各一张；竖屏片子再加 9:16。

用法：
  python3 scripts/cover.py EP
背景取 brief.json 里 cover.shot 那个镜头的首帧图（assets/img/<镜号>.png），没有就取成片中间一帧。
钩子取 cover.hook，没有就用 header.hook。
"""
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from common import ep_dir, find_font, load_json  # noqa: E402

GOLD, IVORY, DIM = (232, 194, 119), (237, 230, 214), (180, 172, 158)


def background(ep, brief):
    cv = brief.get("cover", {})
    sid = cv.get("shot")
    if cv.get("image") and (ep / cv["image"]).exists():
        return Image.open(ep / cv["image"]).convert("RGB")
    if sid and (ep / "assets" / "img" / f"{sid}.png").exists():
        return Image.open(ep / "assets" / "img" / f"{sid}.png").convert("RGB")
    # 没有首帧图时，从原始即梦片段（不带字幕）里取中间一帧
    clips = ([ep / "assets" / "clips" / f"{sid}.mp4"] if sid else []) + sorted((ep / "assets" / "clips").glob("*.mp4"))
    for clip in clips:
        if clip.exists():
            tmp = ep / "build" / "cover_frame.png"
            tmp.parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", "1.5", "-i", str(clip), "-frames:v", "1", str(tmp)])
            if tmp.exists():
                return Image.open(tmp).convert("RGB")
    return Image.new("RGB", (1920, 1080), (30, 26, 20))


def fit(im, w, h):
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))


def shadow_text(base, xy, s, f, fill):
    sh = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(sh)
    d.text(xy, s, font=f, fill=(0, 0, 0, 200), anchor="mm")
    sh = sh.filter(ImageFilter.GaussianBlur(max(4, f.size // 12)))
    base.alpha_composite(sh)
    ImageDraw.Draw(base).text(xy, s, font=f, fill=fill, anchor="mm")


def make(bg, w, h, brief, fp, out):
    im = fit(bg, w, h).convert("RGBA")
    dark = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    dd = ImageDraw.Draw(dark)
    for y in range(h):
        a = int(150 * max(0, (y / h - 0.35) / 0.65) ** 1.2 + 40)
        dd.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    im.alpha_composite(dark)
    title = brief.get("title", "")
    tsize = int(min(w * 0.82 / max(len(title), 1), h * 0.2))
    s = min(w, h) / 1080
    series = f"{brief.get('series', '')} · {brief.get('episode', '')}".strip(" ·")
    hook = brief.get("cover", {}).get("hook") or brief.get("header", {}).get("hook", "")
    cy = h * (0.62 if w > h else 0.50)
    shadow_text(im, (w / 2, cy - tsize * 0.95), series, ImageFont.truetype(fp, int(tsize * 0.38)), GOLD)
    shadow_text(im, (w / 2, cy), title, ImageFont.truetype(fp, tsize), IVORY)
    if hook:
        hs = int(min(tsize * 0.42, w * 0.86 / max(len(hook), 1)))
        shadow_text(im, (w / 2, cy + tsize * 0.95), hook, ImageFont.truetype(fp, hs), GOLD)
    small = ImageFont.truetype(fp, int(26 * s))
    d = ImageDraw.Draw(im)
    if brief.get("badge", True):
        d.rounded_rectangle([int(24 * s), int(24 * s), int(140 * s), int(72 * s)], radius=int(10 * s), outline=DIM, width=2)
        d.text((int(82 * s), int(48 * s)), "AI生成", font=small, fill=DIM, anchor="mm")
    if brief.get("signature"):
        d.text((w - int(30 * s), int(48 * s)), brief["signature"], font=small, fill=IVORY, anchor="rm")
    im.convert("RGB").save(out)
    print(out)


def main():
    ep = ep_dir(sys.argv[1])
    brief = load_json(ep / "brief.json")
    fp = find_font(brief)[1]
    bg = background(ep, brief)
    (ep / "out").mkdir(exist_ok=True)
    sizes = {"16x9": (1920, 1080), "3x4": (1080, 1440)}
    if brief.get("orientation") == "portrait":
        sizes["9x16"] = (1080, 1920)
    for tag, (w, h) in sizes.items():
        make(bg, w, h, brief, fp, ep / "out" / f"封面_{tag}.png")


if __name__ == "__main__":
    main()
