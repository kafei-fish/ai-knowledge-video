# 工程文件说明与分镜写法

一期工程目录（`new_episode.py` 生成）：

```
<工程目录>/
  brief.json        这一期的基本信息和风格
  script.json       分段旁白
  storyboard.json   镜头列表
  assets/img/       即梦首帧图   <镜号>.png
  assets/clips/     即梦视频片段 <镜号>.mp4
  assets/vo/        配音        <段号>.mp3
  assets/ref/       角色定妆照（可选）
  assets/music.mp3  自备配乐（可选）
  build/            中间文件，可随时删
  out/              成片和封面
```

## brief.json

| 字段 | 说明 | 例 |
| --- | --- | --- |
| account | 账号名 | Leo的反常识课 |
| series | 合集名 | 博弈论 |
| episode | 期数 | EP.04 |
| title | 概念名，片头和封面大字 | 智猪博弈 |
| orientation | `landscape` 横屏 1920×1080 / `portrait` 竖屏 1080×1920 | landscape |
| signature | 右上角小字署名，可留空 | |
| badge | 是否加左上角「AI生成」角标。即梦素材本身带标识时可设为 false，避免重复 | true |
| header.hook | 片头第三行钩子，≤12 字 | 大猪干活，小猪躺赢 |
| header.start / end | 片头显示的起止秒数 | 0.2 / 3.4 |
| style.look | 画风词，拼到每条图片提示词最前面 | 电影感写实，暖棕低饱和，侧逆光，35mm 胶片颗粒，浅景深 |
| style.clip_seconds | 即梦视频时长（秒），按所用模型支持的值填 | 5 |
| style.clip_resolution | 即梦视频分辨率 | 720p |
| style.font_file / font_name | 指定字体（可选） | |
| characters | 角色卡列表：id、desc（外貌描述）、ref（定妆照路径，可选） | |
| voice.provider | `volc` / `edge` / `manual` | volc |
| voice.voice | 豆包语音音色 ID，留空用环境变量或默认 | |
| voice.speed | 语速，1.0 为正常 | 1.0 |
| music.mood | `tense` 推理悬疑 / `warm` 温情 | tense |
| cover.shot | 封面用哪个镜头的首帧图 | s04 |
| cover.hook | 封面第三行，留空用 header.hook | |

## script.json

```json
{"segments": [
  {"id": "p1", "text": "猪圈里有一大一小两头猪。|一头有个踏板，|……|谁去踩？"},
  {"id": "p2", "text": "先看小猪。|……|小猪的最优解都是：|【等。】"}
 ],
 "tail": 3.5}
```
- `|` 分隔字幕行；`【】` 标强调（字幕变金色，配音时自动去掉符号）
- `gap_before`（可选）：这一段前空几秒，默认第一段 0.4、其余 0.7
- `tail`：最后一句后留几秒收尾

## storyboard.json

```json
{"shots": [
  {"id": "s01", "type": "clip", "at": "p1:0", "characters": ["大猪", "小猪"],
   "image_prompt": "全景，……", "motion_prompt": "镜头缓慢推近，……"},
  {"id": "s05", "type": "card", "at": "p1:7", "lines": ["谁去踩？"], "gold": [0]}
]}
```

通用字段：`id` 镜号；`type` 类型；`at` 挂在哪行字幕（`段号:行号`，行号从 0 数；也可写 `p2:end` 表示这段说完）；`offset` 相对那行提前（负数）或推后的秒数；`push` 推近幅度（默认片段 0.08、图 0.035）；`hide_subs: true` 这个镜头期间不显示字幕（字卡已经写了同样的话时用）。

第一个镜头总是从 0 秒开始，`at` 只作说明。

| type | 用途 | 专属字段 |
| --- | --- | --- |
| clip | 即梦视频片段 | `image_prompt`、`motion_prompt`、`characters`；复用已有片段写 `src`（如 `assets/clips/s03.mp4`）和 `trim`（跳过开头几秒）；`max_slow` 最多慢放倍数，默认 1.6，超过就循环 |
| image | 静态图片（截图、照片） | `src` |
| card | 字卡 | `lines`（每行一句）、`gold`（哪几行用金色，从 0 数）、`sub`（下方小字）、`size`（字号，默认 110） |
| number | 大数字 | `big`（如 "300 天"）、`caption`、`title` |
| matrix | 收益矩阵 | `rows`、`cols`、`cells`（二维，每格如 "5 / 1"）、`highlight`（要点亮的格 [[行,列]]）、`dim`（变暗的格）、`title`、`note` |
| bars | 条形对比 | `items`（[{label, value}]）、`unit`、`highlight`（点亮的 label）、`title` |

矩阵要"逐格亮起"时，连续写几个 matrix 镜头，每个点亮不同的格子，`at` 挂在对应的字幕行上（见 examples/智猪博弈 的 s06–s10）。

## 分镜节奏

- 开头 0–4 秒：最好看的一个即梦片段 + 片头三行字
- 每个镜头 2–8 秒；超过 8 秒观众会走神
- 一期 `clip` 5–6 个就够；推理部分用信息图连续讲，情绪部分用片段
- 金句、概念名用 card，配 `hide_subs: true`，不要让字卡和字幕说同一句话
- 结尾最后一个镜头留到片尾，配音结束后还有 `tail` 秒，让观众回味

## 即梦提示词写法

**画风词**写在 brief.style.look，自动加到每条图片提示词最前面；**角色卡**写在 brief.characters，镜头里列出 `characters` 就自动加上。所以 `image_prompt` 只写：

（景别），（在做什么，一个动作），（场景与光线），（情绪）

例：特写，小猪低头在石槽边吃玉米粒，背景虚化的大猪，侧面暖光勾出毛发边缘，悠闲

`motion_prompt` 只写：（镜头运动），（主体一个动作），节奏缓慢
例：镜头缓慢推近，小猪低头吃食，节奏缓慢

规则：
- 一段只做一个动作、一种运镜，越简单越不容易崩
- 画面里不出现文字（脚本会自动加"画面中不要出现任何文字"）
- 有人物时尽量中景、远景或背影，特写手部和正脸容易崩
- 不用真实名人、品牌 logo、影视动漫角色
