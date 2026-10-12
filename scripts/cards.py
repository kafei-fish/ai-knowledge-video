"""把信息图、字卡画成图片（不交给即梦画，数字和文字才不会错）。

被 compose.py 和 cover.py 调用；也可单独预览：
  python3 scripts/cards.py EP s05      # 把镜头 s05 画到 EP/build/preview_s05.png
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, str(Path(__file__).parent))
from common import die, ep_dir, find_font, load_json, size_of  # noqa: E402

C = {"bg": (14, 13, 11), "panel": (24, 22, 19), "ivory": (237, 230, 214), "gold": (232, 194, 119),
     "goldhi": (255, 214, 140), "red": (200, 85, 61), "dim": (150, 142, 128), "line": (70, 64, 55)}


def font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        die(f"打不开字体 {path}")


def text_c(d, xy, s, f, fill, anchor="mm"):
    d.text(xy, s, font=f, fill=fill, anchor=anchor)


def backdrop(w, h):
    img = Image.new("RGB", (w, h), C["bg"])
    glow = Image.new("L", (w, h), 0)
    gd = ImageDraw.Draw(glow)
    gd.ellipse([w * 0.15, h * 0.1, w * 0.85, h * 0.9], fill=60)
    glow = glow.filter(ImageFilter.GaussianBlur(min(w, h) * 0.18))
    warm = Image.new("RGB", (w, h), (60, 46, 26))
    return Image.composite(warm, img, glow)


def title_of(d, shot, w, h, fp, s):
    if shot.get("title"):
        text_c(d, (w / 2, h * 0.13), shot["title"], font(fp, int(44 * s)), C["gold"])


def card(shot, w, h, fp):
    s = min(w, h) / 1080
    img = backdrop(w, h)
    d = ImageDraw.Draw(img)
    lines = shot.get("lines", [])
    big = int(shot.get("size", 110) * s)
    gap = big * 1.35
    y0 = h / 2 - gap * (len(lines) - 1) / 2 - (30 * s if shot.get("sub") else 0)
    for i, ln in enumerate(lines):
        col = C["gold"] if i in shot.get("gold", []) else C["ivory"]
        text_c(d, (w / 2, y0 + i * gap), ln, font(fp, big), col)
    if shot.get("sub"):
        text_c(d, (w / 2, y0 + (len(lines) - 1) * gap + big * 1.2), shot["sub"], font(fp, int(40 * s)), C["dim"])
    return img


def number(shot, w, h, fp):
    s = min(w, h) / 1080
    img = backdrop(w, h)
    d = ImageDraw.Draw(img)
    text_c(d, (w / 2, h * 0.46), shot["big"], font(fp, int(220 * s)), C["goldhi"])
    if shot.get("caption"):
        text_c(d, (w / 2, h * 0.46 + 190 * s), shot["caption"], font(fp, int(48 * s)), C["ivory"])
    title_of(d, shot, w, h, fp, s)
    return img


def matrix(shot, w, h, fp):
    """2×2（或 n×m）收益矩阵。cells 里每格写成 "5 / 1"，highlight 是要点亮的格子 [[行,列]]。"""
    s = min(w, h) / 1080
    img = backdrop(w, h)
    d = ImageDraw.Draw(img)
    rows, cols, cells = shot["rows"], shot["cols"], shot["cells"]
    hi = {tuple(x) for x in shot.get("highlight", [])}
    dim = {tuple(x) for x in shot.get("dim", [])}
    cw = min(w * 0.62, 1200 * s) / len(cols)
    ch = min(h * 0.52, 520 * s) / len(rows)
    x0 = (w - cw * len(cols)) / 2 + 90 * s
    y0 = (h - ch * len(rows)) / 2 - 10 * s
    fl, fv = font(fp, int(38 * s)), font(fp, int(84 * s))
    for j, c in enumerate(cols):
        text_c(d, (x0 + cw * (j + 0.5), y0 - 45 * s), c, fl, C["dim"])
    for i, r in enumerate(rows):
        text_c(d, (x0 - 30 * s, y0 + ch * (i + 0.5)), r, fl, C["dim"], anchor="rm")
        for j in range(len(cols)):
            box = [x0 + cw * j + 10 * s, y0 + ch * i + 10 * s, x0 + cw * (j + 1) - 10 * s, y0 + ch * (i + 1) - 10 * s]
            on = (i, j) in hi
            d.rounded_rectangle(box, radius=int(22 * s), fill=(80, 58, 18) if on else C["panel"],
                                outline=C["gold"] if on else C["line"], width=max(2, int(3 * s)))
            col = C["goldhi"] if on else (C["dim"] if (i, j) in dim else C["ivory"])
            text_c(d, ((box[0] + box[2]) / 2, (box[1] + box[3]) / 2), str(cells[i][j]), fv, col)
    title_of(d, shot, w, h, fp, s)
    if shot.get("note"):
        text_c(d, (w / 2, y0 + ch * len(rows) + 60 * s), shot["note"], font(fp, int(40 * s)), C["ivory"])
    return img


def bars(shot, w, h, fp):
    """横向条形对比。items: [{label, value}]，highlight 是要点亮的 label。"""
    s = min(w, h) / 1080
    img = backdrop(w, h)
    d = ImageDraw.Draw(img)
    items = shot["items"]
    vmax = max(abs(it["value"]) for it in items) or 1
    unit = shot.get("unit", "")
    bw = w * 0.5
    x0 = (w - bw) / 2 + 60 * s
    step = min(150 * s, h * 0.6 / len(items))
    y0 = h / 2 - step * (len(items) - 1) / 2 + 30 * s
    fl, fv = font(fp, int(46 * s)), font(fp, int(52 * s))
    for k, it in enumerate(items):
        y = y0 + k * step
        on = it["label"] == shot.get("highlight")
        col = C["gold"] if on else C["dim"]
        text_c(d, (x0 - 30 * s, y), it["label"], fl, C["ivory"], anchor="rm")
        L = max(bw * abs(it["value"]) / vmax, 6 * s)
        d.rounded_rectangle([x0, y - 26 * s, x0 + L, y + 26 * s], radius=int(12 * s), fill=col)
        text_c(d, (x0 + L + 24 * s, y), f"{it['value']}{unit}", fv, C["goldhi"] if on else C["ivory"], anchor="lm")
    title_of(d, shot, w, h, fp, s)
    return img


def photo(shot, w, h, ep):
    p = ep / shot["src"]
    if not p.exists():
        die(f"镜头 {shot['id']} 的图片不存在：{p}")
    im = Image.open(p).convert("RGB")
    k = max(w / im.width, h / im.height)
    im = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    l, t = (im.width - w) // 2, (im.height - h) // 2
    return im.crop((l, t, l + w, t + h))


def render(shot, w, h, fp, ep):
    kind = shot["type"]
    if kind == "image":
        return photo(shot, w, h, ep)
    fn = {"card": card, "number": number, "matrix": matrix, "bars": bars}.get(kind)
    if not fn:
        die(f"镜头 {shot['id']} 的 type「{kind}」不认识，可用：clip、image、card、number、matrix、bars")
    return fn(shot, w, h, fp)


if __name__ == "__main__":
    ep = ep_dir(sys.argv[1])
    brief = load_json(ep / "brief.json")
    sb = load_json(ep / "storyboard.json")
    shot = next((x for x in sb["shots"] if x["id"] == sys.argv[2]), None) or die("没有这个镜头")
    w, h = size_of(brief)
    out = ep / "build" / f"preview_{shot['id']}.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    render(shot, w, h, find_font(brief)[1], ep).save(out)
    print(out)
