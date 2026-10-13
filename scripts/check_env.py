"""检查环境：Python 库、ffmpeg（要带 libass）、中文字体、即梦和配音的密钥。

用法：python3 scripts/check_env.py
"""
import importlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

ok = True


def line(flag, msg, fix=""):
    global ok
    print(("✅ " if flag else "❌ ") + msg + ("" if flag or not fix else f"\n   解决：{fix}"))
    ok = ok and flag


print(f"Python {sys.version.split()[0]}")
line(sys.version_info >= (3, 9), "Python ≥ 3.9", "安装新版 Python")
for mod, pkg in [("numpy", "numpy"), ("PIL", "pillow"), ("requests", "requests")]:
    try:
        importlib.import_module(mod)
        line(True, f"{pkg} 已安装")
    except ImportError:
        line(False, f"{pkg} 未安装", f"pip install {pkg}（系统 Python 报错时加 --break-system-packages 或用虚拟环境）")

ff = shutil.which("ffmpeg")
line(bool(ff), "ffmpeg 已安装", "Mac：brew install ffmpeg；Windows：winget install ffmpeg")
if ff:
    flt = subprocess.run([ff, "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    line(" ass " in flt, "ffmpeg 支持字幕烧录（libass）", "换成带 libass 的 ffmpeg（brew 默认带）")
    line(" xfade " in flt, "ffmpeg 支持转场（xfade）", "升级到 ffmpeg 4.3 以上")

try:
    from common import find_font
    name, path = find_font({})
    line(True, f"中文字体：{name}（{path}）")
except SystemExit:
    line(False, "没找到中文字体", "安装思源宋体，或在 brief.json 的 style 里填 font_file")

print("\n可选能力：")
print(("✅ " if os.environ.get("ARK_API_KEY") else "⚪ ") + "即梦接口 ARK_API_KEY" + ("" if os.environ.get("ARK_API_KEY") else "（没有就走网页手动生成）"))
for k in ["ARK_IMAGE_MODEL", "ARK_VIDEO_MODEL"]:
    print(("✅ " if os.environ.get(k) else "⚪ ") + k)
print(("✅ " if os.environ.get("VOLC_TTS_APPID") and os.environ.get("VOLC_TTS_TOKEN") else "⚪ ") + "豆包语音 VOLC_TTS_APPID / VOLC_TTS_TOKEN")
node = shutil.which("node")
nv = subprocess.run([node, "-v"], capture_output=True, text=True).stdout.strip() if node else ""
node_ok = bool(nv) and int(nv.lstrip("v").split(".")[0]) >= 18
print(("✅ " if node_ok else "⚪ ") + f"Node.js ≥ 18（进阶版 Remotion 渲染需要）{'：' + nv if nv else '，未安装：Mac 用 brew install node，或到 nodejs.org 下载'}")
print(("✅ " if shutil.which("edge-tts") else "⚪ ") + "edge-tts（免费配音，pip install edge-tts）")
try:
    importlib.import_module("faster_whisper")
    print("✅ faster-whisper（字幕精确对齐）")
except ImportError:
    print("⚪ faster-whisper（可选，pip install faster-whisper，字幕更准）")
print("\n结论：" + ("基础环境就绪" if ok else "先把 ❌ 的项装好"))
sys.exit(0 if ok else 1)
