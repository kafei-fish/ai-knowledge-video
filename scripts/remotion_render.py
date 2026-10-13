"""进阶版渲染：用 Remotion 出带动画的成片（逐格矩阵、逐字字幕、砸字、滚动数字、胶片质感）。

用法：
  python3 scripts/remotion_render.py EP [--draft] [--frames 0-90] [--still 12.5]

前提：
  - 已跑完 tts.py、timeline.py，即梦素材已到位（和基础版一样）
  - 配乐用 assets/music.* 或 build/music.wav（music.py 生成）；都没有就只有人声
  - 装了 Node.js 18 以上；第一次运行会自动在 remotion/ 下 npm install（约 1–3 分钟）
选项：
  --draft        半分辨率快速预览
  --frames A-B   只渲染一段帧（30 帧 = 1 秒），检查某个镜头用
  --still 秒数    只导出那一秒的一张图，最快的检查方式
环境变量：
  REMOTION_BROWSER  指定 Chrome/Chromium 可执行文件（无法自动下载浏览器时用）
产出：EP/out/<文件名>_进阶版.mp4
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import die, duration, ep_dir, load_json, save_json  # noqa: E402

ENGINE = Path(__file__).resolve().parent.parent / "remotion"


def ensure_engine():
    npm = shutil.which("npm")
    if not npm or not shutil.which("node"):
        die("没有 Node.js。安装：Mac 用 brew install node，或到 nodejs.org 下载 LTS 版")
    if not (ENGINE / "node_modules" / "remotion").exists():
        print("第一次使用，正在安装 Remotion（约 1–3 分钟）…")
        r = subprocess.run([npm, "install", "--no-audit", "--no-fund"], cwd=ENGINE)
        if r.returncode != 0:
            die("npm install 失败。网络不好时可以先运行：npm config set registry https://registry.npmmirror.com")


def build_props(ep, brief, tl):
    shots = []
    for s in tl["shots"]:
        s = dict(s)
        if s["type"] == "clip":
            s["src"] = s.get("src") or f"assets/clips/{s['id']}.mp4"
            f = ep / s["src"]
            if not f.exists():
                die(f"缺少即梦片段 {f}（镜头 {s['id']}）")
            s["srcDur"] = round(duration(f), 3)
        elif s["type"] == "image":
            if not (ep / s["src"]).exists():
                die(f"缺少图片 {ep / s['src']}（镜头 {s['id']}）")
        shots.append(s)
    music = next((str(p.relative_to(ep)) for p in [ep / "assets" / "music.mp3", ep / "assets" / "music.wav", ep / "build" / "music.wav"] if p.exists()), None)
    if not music:
        print("[提示] 没有配乐，只用配音。可先运行 music.py 生成")
    return {
        "total": tl["total"],
        "w": tl["w"],
        "h": tl["h"],
        "brief": {k: brief.get(k) for k in ["series", "episode", "title", "signature", "badge", "header"] if k in brief},
        "segments": tl["segments"],
        "lines": tl["lines"],
        "shots": shots,
        "music": music,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--frames")
    ap.add_argument("--still", type=float)
    a = ap.parse_args()
    ep = ep_dir(a.ep)
    brief = load_json(ep / "brief.json")
    tl = load_json(ep / "build" / "timeline.json")
    ensure_engine()
    props = build_props(ep, brief, tl)
    pfile = ep / "build" / "remotion_props.json"
    save_json(pfile, props)

    name = brief.get("filename") or f"{brief.get('series', '')}{brief.get('episode', '').replace('EP.', '')}_{brief.get('title', 'video')}"
    (ep / "out").mkdir(exist_ok=True)
    npx = shutil.which("npx")
    common = ["--props", str(pfile), "--public-dir", str(ep), "--log", "error"]
    if os.environ.get("REMOTION_BROWSER"):
        common += ["--browser-executable", os.environ["REMOTION_BROWSER"]]
    if a.draft:
        common += ["--scale", "0.5"]

    if a.still is not None:
        out = ep / "build" / f"still_{a.still:.1f}s.png"
        cmd = [npx, "remotion", "still", "src/index.ts", "Episode", str(out), "--frame", str(round(a.still * 30)), *common]
    else:
        out = ep / "out" / f"{name}_进阶版{'_预览' if a.draft else ''}.mp4"
        cmd = [npx, "remotion", "render", "src/index.ts", "Episode", str(out), "--concurrency", str(max(1, (os.cpu_count() or 2) // 2)), *common]
        if a.frames:
            cmd += ["--frames", a.frames]
    print("渲染中…（全片在普通笔记本上大约需要 5–15 分钟）" if a.still is None else "导出静帧…")
    r = subprocess.run(cmd, cwd=ENGINE)
    if r.returncode != 0:
        die("Remotion 渲染失败。浏览器下载失败时，设置 REMOTION_BROWSER 指向本机 Chrome 后重试")
    print(f"完成：{out}")


if __name__ == "__main__":
    main()
