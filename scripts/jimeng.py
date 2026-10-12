"""即梦（火山方舟 Seedream 图片 / Seedance 视频）调用。

用法（在技能目录下运行，EP 为单期工程目录）：
  python3 scripts/jimeng.py prompts EP          # 只导出提示词清单 prompts.md（网页手动生成时用）
  python3 scripts/jimeng.py images  EP [--shot s03] [--force] [--dry-run]
  python3 scripts/jimeng.py videos  EP [--shot s03] [--force] [--dry-run]

需要环境变量（在火山方舟控制台获取）：
  ARK_API_KEY       方舟 API Key
  ARK_IMAGE_MODEL   图片模型 ID，如 doubao-seedream-4-0-250828（以控制台为准）
  ARK_VIDEO_MODEL   视频模型 ID，如 doubao-seedance-1-0-pro-250528（以控制台为准）
可选：ARK_BASE_URL（默认 https://ark.cn-beijing.volces.com/api/v3）

产出：EP/assets/img/<镜号>.png、EP/assets/clips/<镜号>.mp4
已存在的文件默认跳过，--force 重新生成。手动在即梦网页生成的文件按同样命名放进去即可。
"""
import argparse
import base64
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import die, ep_dir, load_json, ratio_of  # noqa: E402

BASE = os.environ.get("ARK_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3").rstrip("/")


def need_env(*names):
    miss = [n for n in names if not os.environ.get(n)]
    if miss:
        die("缺少环境变量：" + "、".join(miss) + "。没有 API 时改用网页手动生成：先运行 prompts 子命令导出提示词。")


def http():
    try:
        import requests
    except ImportError:
        die("缺少 requests：pip install requests")
    return requests


def headers():
    return {"Authorization": f"Bearer {os.environ['ARK_API_KEY']}", "Content-Type": "application/json"}


def data_uri(path):
    ext = Path(path).suffix.lower().lstrip(".") or "png"
    ext = "jpeg" if ext == "jpg" else ext
    return f"data:image/{ext};base64," + base64.b64encode(Path(path).read_bytes()).decode()


def full_prompt(brief, shot, kind):
    st = brief.get("style", {})
    chars = {c["id"]: c for c in brief.get("characters", [])}
    parts = []
    if kind == "image":
        parts.append(st.get("look", "电影感写实，暖棕低饱和，侧逆光，35mm 胶片颗粒，浅景深"))
        for cid in shot.get("characters", []):
            if cid in chars:
                parts.append(chars[cid]["desc"])
        parts.append(shot["image_prompt"])
        parts.append("画面中不要出现任何文字")
    else:
        parts.append(shot.get("motion_prompt", "镜头缓慢推近，主体轻微动作，节奏缓慢"))
    return "，".join(p.strip("，。 ") for p in parts if p)


def jimeng_shots(ep):
    sb = load_json(ep / "storyboard.json")
    # 带 src 的镜头是复用已有片段，不需要生成
    return [s for s in sb["shots"] if s.get("type") == "clip" and not s.get("src")]


def pick(shots, sid):
    if not sid:
        return shots
    hit = [s for s in shots if s["id"] == sid]
    if not hit:
        die(f"storyboard.json 里没有类型为 clip 的镜头 {sid}")
    return hit


def download(url, dst):
    r = http().get(url, timeout=300)
    r.raise_for_status()
    Path(dst).parent.mkdir(parents=True, exist_ok=True)
    Path(dst).write_bytes(r.content)


def cmd_prompts(ep, brief, args):
    out = ["# 即梦提示词清单", "", "在即梦网页里逐条生成。图片存为 assets/img/<镜号>.png，视频存为 assets/clips/<镜号>.mp4。", ""]
    out.append(f"画幅：{ratio_of(brief)}　视频时长：{brief.get('style', {}).get('clip_seconds', 5)} 秒")
    for c in brief.get("characters", []):
        out.append(f"- 角色「{c['id']}」：{c['desc']}（先单独出一张定妆照，后面都用它做参考图）")
    out.append("")
    for s in jimeng_shots(ep):
        out += [f"## {s['id']}", "", "图片提示词：", "", full_prompt(brief, s, "image"), "",
                "视频动作提示词（图生视频，用上面那张图做首帧）：", "", full_prompt(brief, s, "video"), ""]
    (ep / "prompts.md").write_text("\n".join(out), encoding="utf-8")
    print(f"已写出 {ep / 'prompts.md'}")


def cmd_images(ep, brief, args):
    if not args.dry_run:
        need_env("ARK_API_KEY", "ARK_IMAGE_MODEL")
    chars = {c["id"]: c for c in brief.get("characters", [])}
    for s in pick(jimeng_shots(ep), args.shot):
        dst = ep / "assets" / "img" / f"{s['id']}.png"
        if dst.exists() and not args.force:
            print(f"跳过 {s['id']}（已存在）")
            continue
        body = {
            "model": os.environ.get("ARK_IMAGE_MODEL", "<ARK_IMAGE_MODEL>"),
            "prompt": full_prompt(brief, s, "image"),
            "size": brief.get("style", {}).get("image_size", "2560x1440" if ratio_of(brief) == "16:9" else "1440x2560"),
            "response_format": "url",
            "watermark": False,
        }
        refs = [ep / chars[c]["ref"] for c in s.get("characters", []) if c in chars and chars[c].get("ref") and (ep / chars[c]["ref"]).exists()]
        if refs:
            body["image"] = [data_uri(p) for p in refs] if len(refs) > 1 else data_uri(refs[0])
        if args.dry_run:
            show = dict(body)
            if "image" in show:
                show["image"] = f"<{len(refs)} 张参考图>"
            print(s["id"], show)
            continue
        r = http().post(f"{BASE}/images/generations", headers=headers(), json=body, timeout=300)
        if r.status_code != 200:
            die(f"{s['id']} 出图失败 {r.status_code}：{r.text[:500]}")
        download(r.json()["data"][0]["url"], dst)
        print(f"出图完成 {dst.name}")


def cmd_videos(ep, brief, args):
    if not args.dry_run:
        need_env("ARK_API_KEY", "ARK_VIDEO_MODEL")
    st = brief.get("style", {})
    secs = st.get("clip_seconds", 5)
    res = st.get("clip_resolution", "720p")
    tasks = []
    for s in pick(jimeng_shots(ep), args.shot):
        dst = ep / "assets" / "clips" / f"{s['id']}.mp4"
        img = ep / "assets" / "img" / f"{s['id']}.png"
        if dst.exists() and not args.force:
            print(f"跳过 {s['id']}（已存在）")
            continue
        if not img.exists() and not args.dry_run:
            die(f"{s['id']} 还没有首帧图 {img}，先运行 images")
        text = f"{full_prompt(brief, s, 'video')} --ratio {ratio_of(brief)} --duration {secs} --resolution {res} --watermark false"
        body = {"model": os.environ.get("ARK_VIDEO_MODEL", "<ARK_VIDEO_MODEL>"),
                "content": [{"type": "text", "text": text},
                            {"type": "image_url", "image_url": {"url": data_uri(img) if img.exists() else "<首帧图>"}, "role": "first_frame"}]}
        if args.dry_run:
            print(s["id"], text)
            continue
        r = http().post(f"{BASE}/contents/generations/tasks", headers=headers(), json=body, timeout=120)
        if r.status_code != 200:
            die(f"{s['id']} 提交视频任务失败 {r.status_code}：{r.text[:500]}")
        tasks.append((s["id"], r.json()["id"], dst))
        print(f"已提交 {s['id']} → 任务 {r.json()['id']}")
    # 轮询
    pending = list(tasks)
    t0 = time.time()
    while pending:
        if time.time() - t0 > 3600:
            die("等待超过 1 小时，剩余任务：" + "、".join(p[0] for p in pending))
        time.sleep(15)
        for item in list(pending):
            sid, tid, dst = item
            r = http().get(f"{BASE}/contents/generations/tasks/{tid}", headers=headers(), timeout=60)
            j = r.json()
            stt = j.get("status")
            if stt == "succeeded":
                download(j["content"]["video_url"], dst)
                print(f"视频完成 {dst.name}")
                pending.remove(item)
            elif stt in ("failed", "cancelled", "expired"):
                print(f"[失败] {sid}：{j.get('error')}，换个更简单的动作提示词后用 --shot {sid} --force 重试")
                pending.remove(item)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["prompts", "images", "videos"])
    ap.add_argument("ep")
    ap.add_argument("--shot")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    ep = ep_dir(a.ep)
    brief = load_json(ep / "brief.json")
    {"prompts": cmd_prompts, "images": cmd_images, "videos": cmd_videos}[a.cmd](ep, brief, a)


if __name__ == "__main__":
    main()
