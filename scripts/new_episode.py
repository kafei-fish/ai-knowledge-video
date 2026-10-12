"""新建一期工程目录，生成三个待填写的文件。

用法：
  python3 scripts/new_episode.py <工作区目录> <目录名>
例：
  python3 scripts/new_episode.py ~/videos 博弈论05_枪手悖论
"""
import json
import sys
from pathlib import Path

BRIEF = {
    "account": "账号名",
    "series": "合集名",
    "episode": "EP.01",
    "title": "概念名（2–6 字）",
    "orientation": "landscape",
    "signature": "",
    "header": {"hook": "一句钩子，≤12 字", "start": 0.2, "end": 3.4},
    "style": {"look": "电影感写实，暖棕低饱和，侧逆光，35mm 胶片颗粒，浅景深", "clip_seconds": 5, "clip_resolution": "720p"},
    "characters": [{"id": "主角", "desc": "外貌描述：年龄性别、发型、衣服颜色款式、一个辨识特征", "ref": ""}],
    "voice": {"provider": "volc", "voice": "", "speed": 1.0, "edge_voice": "zh-CN-YunjianNeural"},
    "music": {"mood": "tense"},
    "cover": {"shot": "s01", "hook": ""},
}
SCRIPT = {"segments": [
    {"id": "p1", "text": "开场第一句|第二句"},
    {"id": "p2", "text": "揭示部分|……"},
    {"id": "p3", "text": "现实映射|升华结尾"},
], "tail": 3.0}
STORY = {"shots": [
    {"id": "s01", "type": "clip", "at": "p1:0", "characters": ["主角"], "image_prompt": "景别，在做什么，场景与光线，情绪", "motion_prompt": "镜头缓慢推近，一个动作，节奏缓慢"},
    {"id": "s02", "type": "card", "at": "p2:0", "lines": ["一句金句"], "sub": ""},
]}


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    d = Path(sys.argv[1]).expanduser() / sys.argv[2]
    if (d / "brief.json").exists():
        print(f"{d} 已存在，没有覆盖")
        sys.exit(1)
    for sub in ["assets/img", "assets/clips", "assets/vo", "assets/ref", "build", "out"]:
        (d / sub).mkdir(parents=True, exist_ok=True)
    for name, obj in [("brief.json", BRIEF), ("script.json", SCRIPT), ("storyboard.json", STORY)]:
        (d / name).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")
    print(d)


if __name__ == "__main__":
    main()
