# agnes-media

`agnes-media` 是一个可移植的 Agent 技能，用于调用 Agnes Image 和 Agnes Video API。支持文生图、图像编辑/图生图、文生视频和图生视频，通过直接的 Python CLI 脚本实现。

该技能专为 Claude Code、Codex、OpenCode、OpenClaw、CC-switch、WorkBuddy 等能发现 `SKILL.md` 文件并执行脚本的 Agent 环境设计。

## 安装依赖

```bash
cd skills/agnes-media
python -m pip install -r requirements.txt
```

建议使用 Python 3.10 或更高版本。

**注意：** 首次运行时会自动安装缺失的依赖。

## 配置环境

创建本地 `.env` 文件：

```bash
cp .env.example .env
```

然后设置：

```dotenv
AGNES_API_KEY=your-agnes-api-key
AGNES_BASE_URL=https://apihub.agnes-ai.com/v1
AGNES_IMAGE_MODEL=agnes-image-2.0-flash
AGNES_VIDEO_MODEL=agnes-video-2.0
```

请勿将 `.env` 提交到版本控制，项目已包含 `.gitignore` 防止此情况。

模型名称会自动转换为小写以确保 API 兼容性。支持逗号分隔的 fallback 列表：

```dotenv
AGNES_IMAGE_MODEL=agnes-image-2.0-flash,agnes-image-1.5-flash
```

## 健康检查

运行 smoke test 验证一切正常：

```bash
python scripts/test_smoke.py
```

## 本地测试命令

查看可用模型：

```bash
python scripts/list_models.py
```

显示尺寸预设和比例白名单：

```bash
python scripts/list_models.py --show-presets
```

文生图：

```bash
python scripts/generate_image.py --prompt "A 16:9 cinematic poster for a modern AI media studio, premium lighting, crisp typography space"
```

带负面词和自动下载：

```bash
python scripts/generate_image.py --prompt "A product hero shot" --negative "blurry, distorted" --download-to output.png
```

干运行（仅验证）：

```bash
python scripts/generate_image.py --prompt "test" --dry-run
```

图像编辑：

```bash
python scripts/edit_image.py --prompt "Convert this image into a polished product launch cover while preserving the original product" --image-url "https://example.com/input.png"
```

文生视频：

```bash
python scripts/generate_video.py --prompt "A 5 second cinematic product reveal with a slow push-in camera move and soft studio reflections" --duration 5 --ratio 16:9
```

图生视频：

```bash
python scripts/image_to_video.py --prompt "Animate this image with subtle parallax, gentle light movement, and a slow cinematic camera push" --image-url "https://example.com/input.png" --duration 5 --ratio 16:9
```

所有命令将一个 JSON 对象输出到 stdout，进度消息输出到 stderr。

## 通用选项

| 选项 | 说明 |
|------|------|
| `--prompt` | 必填。英文提示词。 |
| `--negative` | 可选。负面提示词，排除不需要的元素。 |
| `--model` | 可选。模型名称，支持逗号分隔的 fallback 列表。 |
| `--output-json` | 可选。将 JSON 保存到文件。 |
| `--download-to` | 可选。自动下载结果到本地路径。 |
| `--dry-run` | 可选。仅验证参数，不调用 API。 |

## Agent 使用方式

Agent 应读取 `SKILL.md`，将用户请求改写为清晰的英文提示词，然后调用相应的脚本。

- **Claude Code / CC-switch**：将此文件夹放在已识别的 `skills/` 仓库下，让 Agent 自动发现 `SKILL.md`。
- **Codex**：将此文件夹放在工作区或已配置的技能目录下；Codex 可以读取 `SKILL.md` 并运行 Python 脚本。
- **OpenCode**：将此文件夹放在已配置的 skills/tools 区域，像普通 CLI 工具一样调用脚本。
- **OpenClaw**：注册或引用此目录作为工具/技能包，将命令映射到脚本入口点。
- **WorkBuddy**：将此文件夹复制到 WorkBuddy 技能/工具仓库中，暴露 Python 命令。

无需任何平台特定语法。

## 添加到技能仓库

复制或保留完整目录：

```text
skills/agnes-media/
```

最低发现文件是 `SKILL.md`，可移植运行时位于 `scripts/` 目录。

## 注意事项

- API 密钥从环境变量或 `.env` 文件读取。
- 模型名称会自动转换为小写以确保 API 兼容性。
- 模型 fallback：使用逗号分隔的模型列表（如 `model-a,model-b`），第一个 503 会尝试下一个。
- 图像 `--size` 支持直接尺寸（如 `1792x1024`）或宽高比预设（如 `16:9`），必须在白名单内。
- 视频 `--ratio` 必须在白名单内：`16:9`、`9:16`、`1:1`、`4:3`、`3:4`。
- 网络调用使用请求超时。
- 长时间运行的操作每 10 秒向 stderr 输出心跳消息。
- 视频命令会创建任务并轮询，直到成功、失败或超时。
- 首次运行时会自动安装缺失的依赖。
- 如果 Agnes API 更改端点字段，请先更新 `scripts/agnes_common.py`。
- 请勿将 `.env` 纳入版本控制。
