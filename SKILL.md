---
name: ai-knowledge-video
description: 把一段文案或一个知识点做成 AI 知识短视频成片（反常识科普、博弈论、认知偏差、人生感悟类）。全流程自动：改写脚本 → 分镜 → 调用即梦出图出视频 → 配音 → 对字幕 → 配乐 → ffmpeg 合成 mp4 → 封面。用户说"做一期视频""把这段文案做成视频""用即梦做个短片""出一期博弈论/知识科普视频"时使用。
---

# AI 知识短视频：从文案到成片

用户丢给你一段文案（或只给一个概念），你按本文件一步步执行，最后交付一个 mp4 成片和封面。
所有脚本都在本技能目录的 `scripts/` 下，下文用 `$SKILL` 表示本技能目录的绝对路径，`$EP` 表示单期工程目录。

## 第 0 步：准备（每台电脑只做一次）

```bash
python3 $SKILL/scripts/check_env.py
```

- ❌ 项按提示装好：`pip install numpy pillow requests`，ffmpeg（Mac：`brew install ffmpeg`；Windows：`winget install ffmpeg`）
- 可选能力决定第 3、4 步走哪条路，见 `references/jimeng.md`：
  - 有 `ARK_API_KEY` → 即梦接口自动出图出视频
  - 有 `VOLC_TTS_APPID` / `VOLC_TTS_TOKEN` → 自动配音
  - 都没有 → 照样能做：你导出提示词清单，用户（或你用浏览器）在即梦网页生成后放进指定文件夹

## 第 1 步：建工程，问清四件事

```bash
python3 $SKILL/scripts/new_episode.py <工作区目录> <合集名><期数>_<概念名>
```

用一条消息一次问完（用户已给的不要再问）：
1. 账号名、合集名、第几期（例：Leo的反常识课 / 博弈论 / EP.04）
2. 画幅：推理类横屏（70–90 秒），情绪类竖屏（30–45 秒）
3. 配音和即梦走接口还是网页（根据 check_env 的结果给建议）
4. 是否每一步都要确认，还是"全自动，做完给我看"

把答案写进 `$EP/brief.json`（字段说明见 `references/storyboard.md`）。

## 第 2 步：文案 → 脚本（script.json）

严格按 `references/script-rules.md` 改写用户的文案：
- 开头 3 秒抛出反直觉问题，结尾一句升华；全片只讲一个概念
- 不写"评论区""点赞关注"
- 切成 3–4 段（`p1`…`p4`），每段 15–25 秒；段内用 `|` 分隔字幕行，每行 ≤20 字
- 想加重的词用【】包起来（字幕变金色）
- 数字写成汉字，配音才读得准

写完把全文和"需核对的事实"清单发给用户。人名、年份、实验、数据查不到出处的，删掉或改成泛化说法。
不是全自动模式时，等用户确认再往下。

## 第 3 步：分镜（storyboard.json）

按 `references/storyboard.md` 写。要点：
- 镜头类型：`clip`（即梦视频）、`image`（静态图）、`card`（字卡）、`number`（大数字）、`matrix`（收益矩阵）、`bars`（条形对比）
- 每期 `clip` 5–6 个；数字、矩阵、对比一律用信息图类型，不让即梦画
- 每个镜头用 `"at": "段号:行号"` 挂在某一行字幕上（行号从 0 数），镜头从那行开始，到下一个镜头为止
- 一个 `clip` 镜头最好不超过 8 秒；超过就在这段旁白里多切一个镜头，或用 `"src"` 复用前面的片段
- 只想看信息图效果时：`python3 $SKILL/scripts/cards.py $EP s06`，再打开 `$EP/build/preview_s06.png` 看

## 第 4 步：即梦出画面

详细操作和故障处理见 `references/jimeng.md`。

接口路线：
```bash
python3 $SKILL/scripts/jimeng.py images $EP      # 出首帧图到 assets/img/
python3 $SKILL/scripts/jimeng.py videos $EP      # 图生视频到 assets/clips/，会自动轮询下载
```
出图后先自己看一遍 `assets/img/`：人物不一致、画面有字、构图不对的，改 `image_prompt` 后用 `--shot sXX --force` 重出，再做视频（视频比图贵）。

网页路线：
```bash
python3 $SKILL/scripts/jimeng.py prompts $EP     # 导出 $EP/prompts.md
```
把 prompts.md 交给用户在即梦网页里生成；如果你能操作浏览器，按 `references/jimeng.md` 的网页步骤自己做。文件按镜号命名放进 `assets/clips/<镜号>.mp4`。

## 第 5 步：配音

```bash
python3 $SKILL/scripts/tts.py $EP                       # 默认走 brief.voice.provider
python3 $SKILL/scripts/tts.py $EP --provider edge       # 没有火山引擎账号时的免费试做
python3 $SKILL/scripts/tts.py $EP --provider manual     # 列出每段文本，让用户在即梦「配音」里生成
```
文件放在 `assets/vo/<段号>.mp3`。改了某段文案，只重做那段：`--seg p2 --force`。

## 第 6 步：时间线、配乐、合成

```bash
python3 $SKILL/scripts/timeline.py $EP [--align]   # 装了 faster-whisper 就加 --align，字幕更准
python3 $SKILL/scripts/music.py $EP                # 生成无版权配乐；用户给了音乐就放 assets/music.mp3，跳过这步
python3 $SKILL/scripts/compose.py $EP --draft      # 先出 540p 预览，很快
```

**必须检查**：打开 `$EP/build/check/contact.jpg`（每 5 秒一帧的拼图）逐格看：
- 字幕和信息图、片头有没有叠在一起
- 有没有黑屏、画面重复太久、镜头和旁白对不上
- 金色强调是否只用在关键处

有问题改 storyboard / script，重跑 timeline 和 compose。没问题再出正式版：
```bash
python3 $SKILL/scripts/compose.py $EP
python3 $SKILL/scripts/cover.py $EP
```

### 进阶版：Remotion 动画渲染（可选）

用户要更精致的效果、或说"用进阶版 / Remotion 渲染"时，在第 6 步的 timeline、music 之后改用：
```bash
python3 $SKILL/scripts/remotion_render.py $EP --still 24     # 先导出第 24 秒的一帧看效果，几秒出图
python3 $SKILL/scripts/remotion_render.py $EP                # 全片，输出 out/<名字>_进阶版.mp4
```
和基础版的区别：收益矩阵逐格亮起、字幕逐字浮现、片头标识从中间收到角上、字卡砸字、大数字滚动、条形图逐条长出、胶片颗粒和暗角。
同一套 brief / script / storyboard 两个版本通用，不用改。分镜里可以多用两个字段：
- `"pop": "+10 份食物"`：在这个镜头上方砸出一行弹字，`"pop_color": "red"` 变红色
- `brief.header.style`：`"center"`（默认，片头大字居中后收到左上角）或 `"corner"`（第 0 帧就在角上，开场更干净）

要求：Node.js 18 以上（`check_env.py` 会检查）。第一次运行自动安装依赖，需要 1–3 分钟；全片渲染在普通笔记本上约 5–15 分钟。
检查方法：抽几个关键时间点用 `--still` 出图逐张看，确认没有叠字，再渲全片。浏览器下载失败时，设置环境变量 `REMOTION_BROWSER` 指向本机 Chrome。
Remotion 对个人和小团队免费，公司用户可能需要购买授权，以 Remotion 官网许可说明为准；用户是公司时提醒一句。

## 第 7 步：交付

告诉用户：
- 成片路径 `$EP/out/*.mp4`、封面 `$EP/out/封面_*.png`
- 3 个 ≤20 字的标题备选（写结论或冲突，不写概念名）、5 个话题标签
- 发布前检查清单（见 `references/publish.md`），尤其是勾选「AI 生成」标识

## 常见问题

| 现象 | 处理 |
| --- | --- |
| 字幕是方块 | 没找到中文字体；在 brief.json 的 style 里填 `font_file` 和 `font_name` |
| 某镜头循环播放很明显 | 那段太长，多切一个镜头，或把 `max_slow` 调到 2.0 让它慢放 |
| 字幕比声音早或晚 | 装 faster-whisper 后用 `timeline.py --align` |
| 即梦接口报 401 / 模型不存在 | 检查 ARK_API_KEY 和模型 ID（在方舟控制台「开通管理」里看），见 `references/jimeng.md` |
| 配音读错多音字 | 在 script.json 里把那个词换成同音不歧义的写法，只重做那一段 |

## 参考文件

- `references/script-rules.md`：脚本公式、标题规则、两条已发布作品的完整脚本
- `references/storyboard.md`：brief.json / script.json / storyboard.json 字段说明，镜头类型，即梦提示词写法
- `references/jimeng.md`：即梦接口开通、网页手动操作、配音的三条路线、故障处理
- `references/publish.md`：标题、封面、发布检查、复盘
- `examples/智猪博弈/`：一期已发布作品的完整工程文件（放入素材即可直接合成）
