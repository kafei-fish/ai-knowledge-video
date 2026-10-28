# AI 知识短视频技能包（ai-knowledge-video）

给 AI 一段文案，它自动做出一条知识短视频成片：改写脚本 → 分镜 → 调用即梦出图出视频 → 配音 → 对字幕 → 配乐 → 合成 mp4 → 出封面。

适用于 **WorkBuddy、Claude（Claude Code / Claude 桌面版）、Codex** 等能执行命令的 AI 助手。你不需要会写代码，只需要把文案丢给 AI。

样片：抖音「Leo的反常识课」的博弈论、认知偏差、人生刻度合集都是用这套流程做的。

## 安装

技能包就是这个文件夹，核心是 `SKILL.md`。

| 平台 | 安装方式 |
| --- | --- |
| WorkBuddy | 技能市场里选择上传技能，上传本仓库打包的 zip |
| Claude Code | 把整个文件夹放进 `~/.claude/skills/`（只在某个项目里用就放项目的 `.claude/skills/`） |
| Claude 桌面版 / 网页版 | 在技能设置里上传 zip |
| Codex | 把整个文件夹放进 `~/.codex/skills/` 或项目的 `.codex/skills/` |

打 zip：在仓库上一级目录运行 `zip -r ai-knowledge-video.zip ai-knowledge-video -x '*/.git/*'`，或在 GitHub 页面下载 ZIP。

## 两种渲染引擎

| | 基础版（ffmpeg） | 进阶版（Remotion） |
| --- | --- | --- |
| 效果 | 镜头推近、交叉转场、字幕、信息图 | 再加：矩阵逐格亮起、逐字字幕、砸字、滚动数字、胶片质感 |
| 环境 | Python + ffmpeg | 再加 Node.js 18+ |
| 80 秒成片耗时 | 约 2–5 分钟 | 约 5–15 分钟 |
| 授权 | 无限制 | Remotion 对个人和小团队免费，公司可能需买授权（以官网为准） |

两个版本用同一套工程文件，随时切换。对 AI 说"用进阶版渲染"即可。

## 第一次使用

对 AI 说：

> 用 ai-knowledge-video 技能检查一下环境

它会运行 `scripts/check_env.py`，告诉你缺什么。基础依赖：Python 3.9+、ffmpeg、`pip install numpy pillow requests`。

### 即梦和配音（三选一）

- **接口全自动**：开通火山引擎（火山方舟的 Seedream / Seedance 模型、豆包语音合成），设置 `ARK_API_KEY` 等环境变量。详见 `references/jimeng.md`
- **AI 代操作浏览器**：你的 AI 有浏览器能力、你已登录即梦网页版时，它可以替你在网页里生成和下载
- **手动**：AI 给你一份提示词清单，你在即梦里生成后放进指定文件夹，AI 接着合成

## 日常使用

> 用 ai-knowledge-video 做一期视频。账号「Leo的反常识课」，博弈论合集第 5 期，横屏。文案如下：……

AI 会按 `SKILL.md` 一步步做，每一步给你确认（也可以说"全自动，做完给我看"）。成片在工程目录的 `out/` 里。

## 目录

```
SKILL.md                  AI 执行的主流程
references/
  script-rules.md         脚本公式、标题规则、已发布作品脚本
  storyboard.md           工程文件字段说明、镜头类型、即梦提示词写法
  jimeng.md               即梦与配音的三条路线、接口开通、故障处理
  publish.md              标题、封面、发布检查、复盘
scripts/
  check_env.py            检查环境
  new_episode.py          新建一期工程
  jimeng.py               即梦出图、出视频、导出提示词
  tts.py                  配音（豆包语音 / edge-tts / 手动）
  timeline.py             按配音排时间线、对字幕
  music.py                生成无版权配乐
  cards.py                信息图和字卡（收益矩阵、条形图、大数字）
  compose.py              合成成片（基础版）
  remotion_render.py      合成成片（进阶版，调用 remotion/）
  cover.py                封面
remotion/                 进阶版渲染引擎（Remotion 工程，一般不用改）
examples/智猪博弈/          一期已发布作品的工程文件
```

## 费用参考

脚本、合成、配乐都在本机完成，不花钱。花钱的只有即梦（出图、出视频）和配音，按各平台计费；一期 5–6 个视频片段。价格以火山引擎和即梦官网为准。
