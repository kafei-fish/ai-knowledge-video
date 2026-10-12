"""根据配音时长排时间线：每段配音放在哪、每行字幕何时出现、每个镜头何时切。

用法：
  python3 scripts/timeline.py EP [--align]

--align  用 faster-whisper 逐字对齐字幕（更准，需要 pip install faster-whisper，首次会下载模型）。
         不加时按字数比例估算，误差一般在 0.3 秒内，够用。
产出：EP/build/timeline.json
"""
import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from common import die, duration, ep_dir, lines_of, load_json, save_json, size_of  # noqa: E402

PUNCT = r"[，。？！；：、—…\s\"“”‘’（）()《》【】|A-Za-z·]"


def weight(line):
    chars = len(re.sub(PUNCT, "", line))
    pauses = len(re.findall(r"[，、；：]", line)) * 0.8 + len(re.findall(r"[。？！…]", line)) * 1.2
    return max(chars + pauses, 1)


def estimate(lines, dur):
    lead, trail = 0.05, 0.15
    usable = max(dur - lead - trail, 0.5)
    ws = [weight(l) for l in lines]
    tot = sum(ws)
    t = lead
    res = []
    for l, w in zip(lines, ws):
        d = usable * w / tot
        res.append({"t": l, "s": round(t, 3), "e": round(t + d, 3)})
        t += d
    return res


def whisper_align(model, path, lines, dur):
    """逐字时间戳对齐（沿用已发布作品的做法）。"""
    import subprocess
    import numpy as np
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-f", "s16le", "-ac", "1", "-ar", "16000", "-"], capture_output=True).stdout
    audio = np.frombuffer(raw, np.int16).astype(np.float32) / 32768
    segs, _ = model.transcribe(audio, language="zh", word_timestamps=True, initial_prompt="".join(lines))
    chars = []
    for s in segs:
        for w in s.words:
            cs = [c for c in w.word if not re.match(PUNCT, c)]
            step = (w.end - w.start) / max(len(cs), 1)
            for i, c in enumerate(cs):
                chars.append((w.start + i * step, w.start + (i + 1) * step))
    if not chars:
        return estimate(lines, dur)
    counts = [max(len(re.sub(PUNCT, "", l)), 1) for l in lines]
    tot, n, acc, res = sum(counts), len(chars), 0, []
    for l, c in zip(lines, counts):
        i0 = min(round(acc / tot * n), n - 1)
        i1 = max(min(round((acc + c) / tot * n) - 1, n - 1), 0)
        res.append({"t": l, "s": round(chars[i0][0], 3), "e": round(chars[i1][1], 3)})
        acc += c
    for i in range(len(res) - 1):
        res[i]["e"] = round(max(res[i]["e"], res[i + 1]["s"] - 0.05), 3)
    res[-1]["e"] = round(min(dur, res[-1]["e"] + 0.3), 3)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--align", action="store_true")
    a = ap.parse_args()
    ep = ep_dir(a.ep)
    brief = load_json(ep / "brief.json")
    script = load_json(ep / "script.json")
    sb = load_json(ep / "storyboard.json")

    model = None
    if a.align:
        try:
            from faster_whisper import WhisperModel
            model = WhisperModel("small", device="cpu", compute_type="int8")
        except Exception as e:  # noqa: BLE001
            print(f"[提示] faster-whisper 不可用（{e}），改用字数估算")

    t = 0.0
    segs, lines_abs, line_index = [], [], {}
    for i, seg in enumerate(script["segments"]):
        f = ep / "assets" / "vo" / f"{seg['id']}.mp3"
        if not f.exists():
            die(f"缺少配音 {f}，先运行 tts.py")
        d = duration(f)
        t += seg.get("gap_before", 0.4 if i == 0 else 0.7)
        ls = lines_of(seg["text"])
        rel = whisper_align(model, f, ls, d) if model else estimate(ls, d)
        segs.append({"id": seg["id"], "at": round(t, 3), "dur": round(d, 3), "file": str(f.relative_to(ep))})
        for j, r in enumerate(rel):
            item = {"seg": seg["id"], "i": j, "t": r["t"].replace("【", "").replace("】", ""),
                    "emph": "【" in r["t"], "s": round(t + r["s"], 3), "e": round(t + r["e"], 3)}
            lines_abs.append(item)
            line_index[f"{seg['id']}:{j}"] = item["s"]
        t += d
    total = round(t + script.get("tail", 3.0), 3)

    shots = []
    for k, s in enumerate(sb["shots"]):
        at = s.get("at", "")
        if k == 0:
            start = 0.0
        elif at in line_index:
            start = line_index[at] + s.get("offset", 0)
        elif at.endswith(":end") and any(g["id"] == at[:-4] for g in segs):
            g = next(g for g in segs if g["id"] == at[:-4])
            start = g["at"] + g["dur"] + s.get("offset", 0)
        else:
            die(f"镜头 {s['id']} 的 at「{at}」找不到对应字幕行，格式是 段号:行号（从 0 数），如 s2:3")
        shots.append({**s, "start": round(start, 3)})
    shots.sort(key=lambda x: x["start"])
    for k, s in enumerate(shots):
        s["end"] = shots[k + 1]["start"] if k + 1 < len(shots) else total
        if s["end"] - s["start"] < 0.8:
            print(f"[提示] 镜头 {s['id']} 只有 {s['end'] - s['start']:.1f} 秒，太短，考虑合并")

    w, h = size_of(brief)
    save_json(ep / "build" / "timeline.json", {"total": total, "w": w, "h": h, "fps": 30,
                                                 "segments": segs, "lines": lines_abs, "shots": shots})
    print(f"时间线完成：全片 {total:.1f} 秒，{len(segs)} 段配音，{len(lines_abs)} 行字幕，{len(shots)} 个镜头")


if __name__ == "__main__":
    main()
