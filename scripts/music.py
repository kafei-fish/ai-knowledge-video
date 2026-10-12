"""生成无版权配乐：低频铺底 + 和弦垫音 + 段落处的冲击音和上升音。

用法：
  python3 scripts/music.py EP [--mood tense|warm]

tense 适合推理、悬疑（博弈论、认知偏差），warm 适合情感（人生刻度）。
不传时读 brief.json 的 music.mood，默认 tense。
想用自己的音乐：把文件放到 EP/assets/music.mp3（或 .wav），合成时会优先使用它，就不用运行本脚本。
产出：EP/build/music.wav
"""
import argparse
import sys
import wave
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from common import ep_dir, load_json  # noqa: E402

SR = 48000
CHORDS = {
    "tense": [[55.0, 82.4, 110.0, 130.8], [49.0, 73.4, 98.0, 116.5], [43.7, 65.4, 87.3, 104.0], [41.2, 61.7, 82.4, 98.0]],
    "warm": [[65.4, 98.0, 130.8, 164.8], [55.0, 82.4, 110.0, 130.8], [43.7, 65.4, 87.3, 110.0], [49.0, 73.4, 98.0, 123.5]],
}



def env(n, att, rel):
    e = np.ones(n)
    a, r = min(int(att * SR), n // 2), min(int(rel * SR), n // 2)
    if a:
        e[:a] = np.linspace(0, 1, a)
    if r:
        e[-r:] *= np.linspace(1, 0, r)
    return e


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ep")
    ap.add_argument("--mood")
    a = ap.parse_args()
    ep = ep_dir(a.ep)
    brief = load_json(ep / "brief.json")
    tl = load_json(ep / "build" / "timeline.json")
    mood = a.mood or brief.get("music", {}).get("mood", "tense")
    rng = np.random.default_rng(7)
    total = tl["total"]
    n = int(total * SR) + SR
    L, R = np.zeros(n), np.zeros(n)

    def put(t0, sig, g=1.0, pan=0.0):
        i = int(t0 * SR)
        j = min(n, i + len(sig))
        if i >= n or j <= i:
            return
        L[i:j] += sig[: j - i] * g * np.sqrt(0.5 * (1 - pan))
        R[i:j] += sig[: j - i] * g * np.sqrt(0.5 * (1 + pan))

    # 低频铺底
    tt = np.arange(n) / SR
    root = CHORDS[mood][0][0] / 2
    drone = np.sin(2 * np.pi * root * tt) * 0.5 + np.sin(2 * np.pi * root * 2 * tt) * 0.15
    drone *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.07 * tt) ** 2
    put(0, drone * env(n, 2.0, 3.0), 0.10)

    # 每段一个和弦垫音
    segs = tl["segments"]
    starts = [0.0] + [s["at"] - 0.3 for s in segs[1:]] + [total]
    for k in range(len(starts) - 1):
        t0, t1 = starts[k], starts[k + 1] + 0.8
        m = int((t1 - t0) * SR)
        t = np.arange(m) / SR
        x = np.zeros(m)
        for f in CHORDS[mood][k % 4]:
            for det in (-0.4, 0.0, 0.4):
                x += np.sin(2 * np.pi * (f + det) * t + rng.uniform(0, 6.28))
                x += 0.3 * np.sin(2 * np.pi * (2 * f + det) * t + rng.uniform(0, 6.28))
        x = x / 12 * env(m, 1.2, 1.5)
        last = k == len(starts) - 2
        put(t0, x, 0.09 if not last else 0.12, pan=-0.2 if k % 2 else 0.2)

    # 冲击音：开头和每段开头；上升音：最后一段之前
    def impact(d=2.0):
        t = np.arange(int(d * SR)) / SR
        fr = 35 + 70 * np.exp(-t * 7)
        return np.tanh(1.5 * np.sin(2 * np.pi * np.cumsum(fr) / SR)) * np.exp(-t * 2.2)

    def riser(d=1.4):
        t = np.arange(int(d * SR)) / SR
        x = t / d
        noise = np.diff(rng.normal(0, 1, len(t) + 1)) * 0.3
        return (noise + 0.4 * np.sin(2 * np.pi * np.cumsum(200 + 1400 * x ** 2) / SR)) * x ** 3

    put(0.0, impact(), 0.55)
    for s in segs[1:]:
        put(s["at"] - 0.05, impact(1.6), 0.28)
    if len(segs) > 1:
        put(segs[-1]["at"] - 1.4, riser(), 0.10)
        put(segs[-1]["at"] - 0.05, impact(2.2), 0.4)

    fade = int(3.0 * SR)
    for ch in (L, R):
        ch[-fade:] *= np.linspace(1, 0, fade)
    peak = max(np.abs(L).max(), np.abs(R).max(), 1e-6)
    st = np.stack([L, R], 1) / peak * 0.8
    out = ep / "build" / "music.wav"
    out.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(out), "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((st * 32767).astype(np.int16).tobytes())
    print(f"配乐完成 {out}（{mood}，{total:.1f} 秒）")


if __name__ == "__main__":
    main()
