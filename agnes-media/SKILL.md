---
name: agnes-media
description: Generate image, edit image, image to video, and generate video with Agnes Image and Agnes Video APIs for posters, covers, social media image assets, product visuals, and video generation.
---

# Agnes Media

Use this skill when the user asks to create or transform visual media with Agnes, including generate image, poster, cover, social media image, product image, image editing, image-to-image, short video, image to video, or generate video requests.

This skill is intentionally platform-neutral. It does not depend on Claude Code, Codex, OpenCode, OpenClaw, WorkBuddy, CC-switch, MCP, a background service, or any private agent syntax. Any agent that can read this `SKILL.md` and run Python scripts can use it.

## When to Use This Skill

Use `agnes-media` for:

- Text to image generation.
- Image editing or image-to-image transformations from one or more image URLs.
- Text to video generation.
- Image to video generation from a starting image URL.
- Posters, thumbnails, covers, banners, product shots, social media images, marketing visuals, and short videos.

Before calling a script, rewrite the user's natural-language request into a clear English prompt. Preserve the requested style, mood, content, brand constraints, aspect ratio, duration, camera movement, and negative constraints when provided.

Defaults:

- Image size: `1792x1024` (16:9 aspect ratio). Use `--size` with either:
  - Direct size: `1792x1024`, `1024x1024`, `1024x1792`, `1024x768`, `768x1024`.
  - Aspect ratio preset: `16:9`, `1:1`, `9:16`, `4:3`, `3:4`.
- Video duration: 5 seconds.
- Video ratio: `16:9` (format: `W:H`). Allowed: `16:9`, `9:16`, `1:1`, `4:3`, `3:4`.
- Style: keep the user's requested style. If no style is specified, use a clean, production-ready visual style appropriate to the medium.

Common size presets:

| Ratio | Size |
|-------|------|
| 16:9  | 1792x1024 |
| 9:16  | 1024x1792 |
| 1:1   | 1024x1024 |
| 4:3   | 1024x768 |
| 3:4   | 768x1024 |

## Available Commands

Run commands from this skill directory or pass script paths explicitly.

### Health Check

```bash
python scripts/test_smoke.py
```

Validates dependencies, environment, API key, and model connectivity in one run.

### List Available Models

```bash
python scripts/list_models.py
```

Show size presets and ratio whitelist:

```bash
python scripts/list_models.py --show-presets
```

### Text to Image

```bash
python scripts/generate_image.py --prompt "A cinematic 16:9 poster for a futuristic productivity app, clean composition, premium lighting"
```

With negative prompt and auto-download:

```bash
python scripts/generate_image.py --prompt "A product hero shot" --negative "blurry, distorted, low quality" --download-to output.png
```

With model fallback:

```bash
python scripts/generate_image.py --prompt "A product hero shot" --model "agnes-image-2.0-flash,agnes-image-1.5-flash"
```

### Image Editing / Image to Image

```bash
python scripts/edit_image.py --prompt "Turn the product photo into a polished social media hero image, keep the product shape unchanged" --image-url "https://example.com/input.png"
```

Multiple input images:

```bash
python scripts/edit_image.py --prompt "Combine these into a collage" --image-url "https://example.com/a.png" --image-url "https://example.com/b.png"
```

### Text to Video

```bash
python scripts/generate_video.py --prompt "A five second cinematic product reveal, slow dolly-in, soft studio lighting" --duration 5 --ratio 16:9
```

### Image to Video

```bash
python scripts/image_to_video.py --prompt "Animate the image with a subtle camera push-in and floating light reflections" --image-url "https://example.com/input.png" --duration 5 --ratio 16:9
```

### Dry Run (Validate Only)

Any script supports `--dry-run` to validate parameters without calling the API:

```bash
python scripts/generate_image.py --prompt "test" --dry-run
python scripts/list_models.py --dry-run
```

All scripts support `--help`.

## Common Options

All generation scripts support these options:

| Option | Description |
|--------|-------------|
| `--prompt` | Required. English prompt describing the desired output. |
| `--negative` | Optional. Negative prompt to exclude unwanted elements. |
| `--model` | Optional. Model name. Supports comma-separated fallback list (e.g., `model-a,model-b`). |
| `--output-json` | Optional. Save JSON response to this file path. |
| `--download-to` | Optional. Auto-download result to this local path. |
| `--dry-run` | Optional. Validate parameters only, don't call API. |

Image scripts additionally support:

| Option | Description |
|--------|-------------|
| `--size` | Image size (`1792x1024`) or ratio preset (`16:9`). Must be in whitelist. |

Video scripts additionally support:

| Option | Description |
|--------|-------------|
| `--ratio` | Video ratio (e.g., `16:9`). Must be in whitelist. |
| `--duration` | Video duration in seconds. Default: 5. |
| `--poll-interval` | Polling interval in seconds. Default: 5. |
| `--timeout-seconds` | Polling timeout in seconds. Default: 600. |

## Required Environment Variables

Required:

- `AGNES_API_KEY`: the user's own Agnes API key.

Optional:

- `AGNES_BASE_URL`: defaults to `https://apihub.agnes-ai.com/v1`.
- `AGNES_IMAGE_MODEL`: defaults to `agnes-image-2.0-flash`. Supports comma-separated fallback list.
- `AGNES_VIDEO_MODEL`: defaults to `agnes-video-2.0`. Supports comma-separated fallback list.

Model names are automatically converted to lowercase for API compatibility.

The scripts read environment variables first and also load `.env` files from the current directory or parent directories. Never hardcode API keys.

## Output Format

Every script writes exactly one JSON object to stdout. Logs, progress text, and human-readable notes go to stderr.

Successful response:

```json
{
  "status": "success",
  "type": "image",
  "model": "agnes-image-2.0-flash",
  "prompt": "...",
  "result_url": "...",
  "raw_response": {}
}
```

With download:

```json
{
  "status": "success",
  "type": "image",
  "model": "agnes-image-2.0-flash",
  "prompt": "...",
  "result_url": "...",
  "local_path": "/absolute/path/to/downloaded.png",
  "raw_response": {}
}
```

Error response:

```json
{
  "status": "error",
  "type": "video",
  "message": "...",
  "detail": {}
}
```

If `--output-json` is provided, the same JSON object is also saved to that file.

## Safety and API Key Rules

- Do not print, store, commit, or expose `AGNES_API_KEY`.
- Do not place real secrets in `.env.example`, docs, prompts, or source code.
- Do not commit `.env`. A `.gitignore` is included to prevent this.
- Treat user-provided images and prompts as private user content.
- If a request is disallowed by the host agent's safety policy, do not call the API. Return or explain according to the host agent's policy.
- Keep generated prompts faithful to the user request and avoid inventing private, sensitive, or copyrighted details unless the user provided them and the host policy allows it.

## Implementation Notes

Shared logic lives in `scripts/agnes_common.py`. If the Agnes API changes field names or endpoint details, update that file first. The CLI surface is designed to be portable to MCP, OpenAPI tools, WorkBuddy skills, OpenClaw tools, or other agent tool registries later.

Dependencies are auto-installed on first run if missing (openai, requests, python-dotenv).

Long-running operations (image generation, video polling) emit heartbeat messages to stderr every 10 seconds.
