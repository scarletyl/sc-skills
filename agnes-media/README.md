# agnes-media

`agnes-media` is a portable Agent Skill for Agnes Image and Agnes Video APIs. It supports text-to-image, image editing/image-to-image, text-to-video, and image-to-video through direct Python CLI scripts.

The skill is designed for Claude Code, Codex, OpenCode, OpenClaw, CC-switch, WorkBuddy, and similar agent environments that can discover a `SKILL.md` file and run scripts.

## Install Dependencies

```bash
cd skills/agnes-media
python -m pip install -r requirements.txt
```

Python 3.10 or newer is recommended.

**Note:** Dependencies are auto-installed on first run if missing.

## Configure Environment

Create a local `.env` file:

```bash
cp .env.example .env
```

Then set:

```dotenv
AGNES_API_KEY=your-agnes-api-key
AGNES_BASE_URL=https://apihub.agnes-ai.com/v1
AGNES_IMAGE_MODEL=agnes-image-2.0-flash
AGNES_VIDEO_MODEL=agnes-video-2.0
```

Do not commit `.env`. A `.gitignore` is included to prevent this.

Model names are automatically converted to lowercase for API compatibility. Supports comma-separated fallback list:

```dotenv
AGNES_IMAGE_MODEL=agnes-image-2.0-flash,agnes-image-1.5-flash
```

## Health Check

Run a smoke test to validate everything is working:

```bash
python scripts/test_smoke.py
```

## Local Test Commands

List available models:

```bash
python scripts/list_models.py
```

Show size presets and ratio whitelist:

```bash
python scripts/list_models.py --show-presets
```

Text to image:

```bash
python scripts/generate_image.py --prompt "A 16:9 cinematic poster for a modern AI media studio, premium lighting, crisp typography space"
```

With negative prompt and auto-download:

```bash
python scripts/generate_image.py --prompt "A product hero shot" --negative "blurry, distorted" --download-to output.png
```

Dry run (validate only):

```bash
python scripts/generate_image.py --prompt "test" --dry-run
```

Image edit:

```bash
python scripts/edit_image.py --prompt "Convert this image into a polished product launch cover while preserving the original product" --image-url "https://example.com/input.png"
```

Text to video:

```bash
python scripts/generate_video.py --prompt "A 5 second cinematic product reveal with a slow push-in camera move and soft studio reflections" --duration 5 --ratio 16:9
```

Image to video:

```bash
python scripts/image_to_video.py --prompt "Animate this image with subtle parallax, gentle light movement, and a slow cinematic camera push" --image-url "https://example.com/input.png" --duration 5 --ratio 16:9
```

All commands write one JSON object to stdout. Progress messages go to stderr.

## Common Options

| Option | Description |
|--------|-------------|
| `--prompt` | Required. English prompt. |
| `--negative` | Optional. Negative prompt to exclude unwanted elements. |
| `--model` | Optional. Model name. Supports comma-separated fallback. |
| `--output-json` | Optional. Save JSON to file. |
| `--download-to` | Optional. Auto-download result to local path. |
| `--dry-run` | Optional. Validate only, don't call API. |

## Agent Usage

Agents should read `SKILL.md`, rewrite the user's request as a clear English prompt, then call the appropriate script.

- Claude Code / CC-switch: place this folder under a recognized `skills/` repository and let the agent discover `SKILL.md`.
- Codex: place this folder under a workspace or configured skill directory; Codex can read `SKILL.md` and run the Python scripts.
- OpenCode: place this folder in the configured skills/tools area and invoke the scripts as normal CLI tools.
- OpenClaw: register or reference this directory as a tool/skill package and map commands to the script entry points.
- WorkBuddy: copy this folder into the WorkBuddy skill/tool repository and expose the Python commands.

No platform-specific syntax is required.

## Add to a Skills Repository

Copy or keep the complete directory:

```text
skills/agnes-media/
```

The minimum discovery file is `SKILL.md`. The portable runtime surface is in `scripts/`.

## Notes

- API keys are read from environment variables or `.env`.
- Model names are automatically converted to lowercase for API compatibility.
- Model fallback: use comma-separated model list (e.g., `model-a,model-b`), first 503 tries next.
- Image `--size` accepts direct dimensions (e.g., `1792x1024`) or ratio presets (e.g., `16:9`). Must be in whitelist.
- Video `--ratio` must be in whitelist: `16:9`, `9:16`, `1:1`, `4:3`, `3:4`.
- Network calls use request timeouts.
- Long-running operations emit heartbeat messages to stderr every 10 seconds.
- Video commands create a task and poll until success, failure, or timeout.
- Dependencies are auto-installed on first run if missing.
- If the Agnes API changes endpoint fields, update `scripts/agnes_common.py` first.
- Keep `.env` out of version control.
