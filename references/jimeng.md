# 即梦出画面与配音：三条路线

| 路线 | 适合 | 画面 | 配音 |
| --- | --- | --- | --- |
| A. 接口全自动 | 要批量做、愿意开通火山引擎 | `jimeng.py images` / `videos` | `tts.py --provider volc` |
| B. 浏览器代操作 | 你（AI）能操作用户的浏览器，用户已登录即梦 | 在即梦网页里逐条生成并下载 | 即梦网页「配音」 |
| C. 用户手动 | 都不具备 | 用户照 prompts.md 生成 | 用户在即梦配音里生成，或 `--provider edge` 免费试做 |

三条路线产出的文件命名完全一样，后面的合成步骤不用改：
- 首帧图：`assets/img/<镜号>.png`
- 视频片段：`assets/clips/<镜号>.mp4`
- 配音：`assets/vo/<段号>.mp3`

## A. 接口全自动

即梦的图片和视频模型（Seedream / Seedance）通过火山引擎「火山方舟」开放接口，配音通过火山引擎「豆包语音」开放接口。
控制台菜单名称会变，以官方文档为准：图片和视频看 https://www.volcengine.com/docs/82379 ，语音看 https://www.volcengine.com/docs/6561 。

1. 注册火山引擎并实名，进入火山方舟控制台
2. 开通一个 Seedream 图片模型和一个 Seedance 视频模型（图生视频），记下它们的模型 ID
3. 创建 API Key
4. 设置环境变量（Mac 写进 `~/.zshrc`，Windows 用「编辑系统环境变量」）：

```bash
export ARK_API_KEY="你的 API Key"
export ARK_IMAGE_MODEL="图片模型 ID"
export ARK_VIDEO_MODEL="视频模型 ID"
# 配音（豆包语音合成，在语音技术控制台创建应用后获得）
export VOLC_TTS_APPID="应用 AppID"
export VOLC_TTS_TOKEN="Access Token"
export VOLC_TTS_VOICE="音色 ID"     # 在控制台音色列表里挑一个低沉男声或温和女声
```

5. 先试一条：`python3 $SKILL/scripts/jimeng.py images $EP --shot s01`，确认能出图再批量

省钱顺序：先出全部首帧图 → 看图、改提示词、重出不满意的 → 全部满意后才跑 `videos`。视频按秒计费，比图片贵得多。

### 接口故障

| 报错 | 原因与处理 |
| --- | --- |
| 401 / AuthenticationError | API Key 错或没设置到当前终端；`echo $ARK_API_KEY` 检查 |
| 模型不存在 / 没有权限 | 模型 ID 填错，或这个模型还没在控制台开通 |
| 参数不支持（时长、分辨率） | 不同 Seedance 版本支持的时长不同；改 brief.style 的 `clip_seconds`（常见 5 或 10）和 `clip_resolution` |
| 参考图格式错误 | 改用公网可访问的图片链接，或去掉 characters 的 `ref` |
| 视频任务 failed | 多半是动作太复杂或触发审核；简化 motion_prompt，`--shot sXX --force` 重试 |
| 配音报错 | 检查 AppID、Token、音色 ID 是否属于同一个应用，音色是否已开通 |

## B. 浏览器代操作（你有浏览器工具时）

1. 先运行 `jimeng.py prompts $EP` 得到 `prompts.md`
2. 打开即梦网页版（jimeng.jianying.com），确认用户已登录；没登录就请用户自己登录，不要替用户输入账号密码
3. 先为每个角色出一张定妆照，选定后保存，后面出图都把它作为参考图
4. 进入图片生成，按 prompts.md 逐条粘贴「图片提示词」，比例选 brief 的画幅（横屏 16:9 / 竖屏 9:16），选一张最好的下载，存为 `assets/img/<镜号>.png`
5. 进入视频生成，选图生视频，上传对应首帧图，粘贴「视频动作提示词」，时长选最短档，生成后下载，存为 `assets/clips/<镜号>.mp4`
6. 配音：进入即梦的配音功能，选定一个音色，按 `tts.py --provider manual` 列出的每段文本分别生成并下载，存为 `assets/vo/<段号>.mp3`
7. 下载、付费、开会员这类操作前先问用户；遇到验证码请用户自己处理

## C. 用户手动

把 `prompts.md` 发给用户，告诉他：
- 每个镜头一张图 + 一段视频，按镜号命名放进 `assets/img/` 和 `assets/clips/`
- 配音按段号命名放进 `assets/vo/`，或者让你用 `--provider edge` 先生成试听版
- 放好后告诉你，你接着跑第 6 步

用户把文件命名错了也没关系：你按内容和顺序帮他改名。

## 配音音色建议

- 推理类（博弈论、认知偏差）：低沉、语速平稳的男声，样板用的是即梦「磁性男主播」
- 情绪类（人生刻度）：温和、语速稍慢的声音
- 同一个账号始终用同一个音色，观众听声音就能认出来
- 免费试做：`--provider edge`，男声 `zh-CN-YunjianNeural`，女声 `zh-CN-XiaoxiaoNeural`（在 brief.voice.edge_voice 里改）
