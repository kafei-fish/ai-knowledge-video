"""公共工具：读写工程文件、探测时长、找中文字体。"""
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path


def die(msg):
    print(f"[错误] {msg}", file=sys.stderr)
    sys.exit(1)


def load_json(p):
    p = Path(p)
    if not p.exists():
        die(f"找不到 {p}")
    return json.loads(p.read_text(encoding="utf-8"))


def save_json(p, data):
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    Path(p).write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")


def ep_dir(arg):
    d = Path(arg).resolve()
    if not (d / "brief.json").exists():
        die(f"{d} 里没有 brief.json，确认传入的是单期工程目录")
    return d


def size_of(brief):
    """返回 (宽, 高)。横屏 1920x1080，竖屏 1080x1920。"""
    return (1080, 1920) if brief.get("orientation", "landscape") == "portrait" else (1920, 1080)


def ratio_of(brief):
    return "9:16" if brief.get("orientation", "landscape") == "portrait" else "16:9"


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True,
    ).stdout.strip()
    if not out:
        die(f"读不出时长：{path}")
    return float(out)


def clean_text(t):
    """去掉字幕分隔符和强调标记，得到给配音用的纯文本。"""
    return re.sub(r"[|【】]", "", t)


def lines_of(t):
    return [x.strip() for x in t.split("|") if x.strip()]


FONT_CANDIDATES = [
    # (ASS/系统里的字体名, 文件路径)
    ("Songti SC", "/System/Library/Fonts/Supplemental/Songti.ttc"),
    ("Source Han Serif SC", os.path.expanduser("~/Library/Fonts/SourceHanSerifSC-Heavy.otf")),
    ("Noto Serif CJK SC", "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc"),
    ("Noto Serif CJK SC", "/usr/share/fonts/noto-cjk/NotoSerifCJK-Bold.ttc"),
    ("SimSun", "C:/Windows/Fonts/simsun.ttc"),
    ("Microsoft YaHei", "C:/Windows/Fonts/msyhbd.ttc"),
    ("PingFang SC", "/System/Library/Fonts/PingFang.ttc"),
    ("Noto Sans CJK SC", "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc"),
]


def find_font(brief=None):
    """返回 (字体名, 字体文件)。brief.style.font_file / font_name 可覆盖。"""
    st = (brief or {}).get("style", {})
    if st.get("font_file") and Path(st["font_file"]).exists():
        return st.get("font_name", "Custom"), st["font_file"]
    for name, path in FONT_CANDIDATES:
        if Path(path).exists():
            return name, path
    if shutil.which("fc-list"):
        out = subprocess.run(["fc-list", ":lang=zh", "family", "file"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if ":" in line:
                path, fam = line.split(":", 1)
                return fam.split(",")[0].strip(), path.strip()
    die("找不到中文字体。在 brief.json 的 style 里填 font_file 和 font_name")


def run(cmd, quiet=True):
    r = subprocess.run(cmd, capture_output=quiet, text=True)
    if r.returncode != 0:
        tail = (r.stderr or "")[-2000:]
        die(f"命令失败：{' '.join(map(str, cmd[:6]))} …\n{tail}")
    return r
