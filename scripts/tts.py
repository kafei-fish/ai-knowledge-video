"""配音：把 script.json 的每一段旁白生成一个音频文件 EP/assets/vo/<段号>.mp3。

用法：
  python3 scripts/tts.py EP [--provider volc|edge|manual] [--seg s2] [--force]

provider：
  volc    火山引擎豆包语音合成（音色和即梦配音同源）。环境变量：
          VOLC_TTS_APPID、VOLC_TTS_TOKEN，可选 VOLC_TTS_VOICE（默认 BV701_streaming）、VOLC_TTS_CLUSTER（默认 volcano_tts）
  edge    免费的微软语音（pip install edge-tts），音色默认 zh-CN-YunjianNeural，适合试做
  manual  不生成，只检查：在即梦里用「配音」逐段生成并下载，命名为 <段号>.mp3 放进 assets/vo/
不传 --provider 时按 brief.json 里 voice.provider，默认 volc。
"""
import argparse
import base64
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import clean_text, die, ep_dir, load_json  # noqa: E402


def chunks(text, limit=280):
    """按句号切成不超过 limit 字的块（接口单次长度有限）。"""
    parts = re.split(r"(?<=[。！？；])", text)
    out, cur = [], ""
    for p in parts:
        if len(cur) + len(p) > limit and cur:
            out.append(cur)
            cur = ""
        cur += p
    if cur:
        out.append(cur)
    return out


def concat(files, dst):
    lst = Path(tempfile.mktemp(suffix=".txt"))
    lst.write_text("".join(f"file '{f}'\n" for f in files), encoding="utf-8")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c:a", "libmp3lame", "-q:a", "2", str(dst)], check=True)


def volc(text, dst, voice_cfg):
    import requests
    appid, token = os.environ.get("VOLC_TTS_APPID"), os.environ.get("VOLC_TTS_TOKEN")
    if not appid or not token:
        die("缺少 VOLC_TTS_APPID / VOLC_TTS_TOKEN。没有接口时用 --provider edge 试做，或 --provider manual 用即梦网页配音")
    tmp = []
    for i, part in enumerate(chunks(text)):
        body = {
            "app": {"appid": appid, "token": token, "cluster": os.environ.get("VOLC_TTS_CLUSTER", "volcano_tts")},
            "user": {"uid": "ai-knowledge-video"},
            "audio": {"voice_type": voice_cfg.get("voice") or os.environ.get("VOLC_TTS_VOICE", "BV701_streaming"),
                      "encoding": "mp3", "speed_ratio": voice_cfg.get("speed", 1.0)},
            "request": {"reqid": str(uuid.uuid4()), "text": part, "text_type": "plain", "operation": "query"},
        }
        r = requests.post("https://openspeech.bytedance.com/api/v1/tts", json=body,
                          headers={"Authorization": f"Bearer;{token}"}, timeout=120)
        j = r.json()
        if j.get("code") not in (None, 3000) or "data" not in j:
            die(f"配音失败：{j.get('code')} {j.get('message')}")
        f = Path(tempfile.mktemp(suffix=f"_{i}.mp3"))
        f.write_bytes(base64.b64decode(j["data"]))
        tmp.append(f)
    concat(tmp, dst)


def edge(text, dst, voice_cfg):
    exe = shutil.which("edge-tts")
    if not exe:
        die("没装 edge-tts：pip install edge-tts")
    speed = voice_cfg.get("speed", 1.0)
    rate = f"{int(round((speed - 1) * 100)):+d}%"
    voice = voice_cfg.get("edge_voice", "zh-CN-YunjianNeural")
    subprocess.run([exe, "--voice", voice, f"--rate={rate}", "--text", text, "--write-media", str(dst)], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--provider")
    ap.add_argument("--seg")
    ap.add_argument("--force", action="store_true")
    a = ap.parse_args()
    ep = ep_dir(a.ep)
    brief = load_json(ep / "brief.json")
    script = load_json(ep / "script.json")
    vcfg = brief.get("voice", {})
    prov = a.provider or vcfg.get("provider", "volc")
    vo = ep / "assets" / "vo"
    vo.mkdir(parents=True, exist_ok=True)
    missing = []
    for seg in script["segments"]:
        if a.seg and seg["id"] != a.seg:
            continue
        dst = vo / f"{seg['id']}.mp3"
        if dst.exists() and not a.force:
            print(f"跳过 {seg['id']}（已存在）")
            continue
        text = clean_text(seg["text"])
        if prov == "manual":
            missing.append(seg["id"])
            continue
        (volc if prov == "volc" else edge)(text, dst, vcfg)
        print(f"配音完成 {dst.name}")
    if missing:
        print("还缺这些段的配音，请在即梦「配音」里生成后放进 assets/vo/：")
        for sid in missing:
            seg = next(s for s in script["segments"] if s["id"] == sid)
            print(f"  {sid}.mp3：{clean_text(seg['text'])}")
        sys.exit(2)


if __name__ == "__main__":
    main()
