# Agnes API Notes

These scripts use a small set of implementation assumptions so the skill can stay portable across agent environments.

## Auto-Install Dependencies

On first run, the skill checks for required packages (openai, requests, python-dotenv). If any are missing, it automatically runs `pip install -r requirements.txt` and retries once. This eliminates the most common first-run failure.

## Image API Assumption

The Image API is assumed to support OpenAI-compatible `images.generate` through the configured base URL:

```text
AGNES_BASE_URL=https://apihub.agnes-ai.com/v1
```

The default image model is:

```text
agnes-image-2.0-flash
```

**Note:** Model names are automatically converted to lowercase before API calls.

### Size Parameter (Strict Whitelist)

The `--size` parameter is validated against a strict whitelist:

**Allowed sizes:** `1792x1024`, `1024x1024`, `1024x1792`, `1024x768`, `768x1024`

**Allowed ratio presets:**

| Ratio | Size |
|-------|------|
| 16:9  | 1792x1024 |
| 9:16  | 1024x1792 |
| 1:1   | 1024x1024 |
| 4:3   | 1024x768 |
| 3:4   | 768x1024 |

Invalid sizes are rejected immediately with a helpful error message listing allowed values.

### Model Fallback

Supports comma-separated model list in config or `--model` flag:

```dotenv
AGNES_IMAGE_MODEL=agnes-image-2.0-flash,agnes-image-1.5-flash
```

If the first model returns 503 or "not found", the next model is tried automatically.

### Model Not Found Error

When a model is not found, the error includes actionable guidance:

```json
{
  "message": "Model 'X' not found on this channel.",
  "detail": {
    "hint": "Run `python scripts/list_models.py` to see what's available.\nOr set AGNES_IMAGE_MODEL in .env to one of the IDs it returns."
  }
}
```

Image editing currently uses:

```text
POST /images/edits
```

with a JSON body containing:

```json
{
  "model": "...",
  "prompt": "...",
  "image_url": "...",
  "size": "1792x1024"
}
```

If Agnes requires a different field name, update `edit_image` in `scripts/agnes_common.py`.

## Video API Assumption

Video generation is assumed to use:

```text
POST /videos
```

to create a task, then:

```text
GET /videos/{task_id}
```

to poll for completion.

The default video model is:

```text
agnes-video-2.0
```

**Ratio whitelist:** `16:9`, `9:16`, `1:1`, `4:3`, `3:4`

The create payload is centralized in `create_video_task` in `scripts/agnes_common.py`.

## Heartbeat Messages

Long-running operations emit heartbeat messages to stderr every 10 seconds:

```
[agnes-media] Image generation still generating... (elapsed: 10s)
[agnes-media] Video processing... (elapsed: 30s, status: processing)
```

This prevents users from thinking the process is stuck.

## Field Names

The code tries common response fields:

- Task id: `id`, `task_id`, `video_id`.
- Result URL: `result_url`, `video_url`, `url`, `output_url`.
- Status: `succeeded`, `success`, `completed`, `complete`, `done`, `failed`, `error`, `cancelled`, `canceled`.

If official Agnes documentation changes these fields, prefer changing `scripts/agnes_common.py` instead of changing every CLI script.

## Migration Notes

The CLI scripts are intentionally thin wrappers around shared functions. This makes the skill easy to migrate to:

- MCP server tools.
- OpenAPI tool definitions.
- WorkBuddy skills.
- OpenClaw tools.
- Other agent tool registries.
