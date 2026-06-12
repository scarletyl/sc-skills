# Usage Examples

Use these examples from the `skills/agnes-media` directory.

## 0. Health Check

```bash
python scripts/test_smoke.py
```

Validates dependencies, environment, API key, and model connectivity.

## 1. List Available Models

```bash
python scripts/list_models.py
```

Show size presets and ratio whitelist:

```bash
python scripts/list_models.py --show-presets
```

Output:

```json
{
  "status": "success",
  "type": "size_presets",
  "size_presets": {
    "16:9": "1792x1024",
    "9:16": "1024x1792",
    "1:1": "1024x1024",
    "4:3": "1024x768",
    "3:4": "768x1024"
  },
  "allowed_sizes": ["1024x1024", "1024x1792", "1792x1024"],
  "allowed_ratios": ["1:1", "16:9", "3:4", "4:3", "9:16"]
}
```

## 2. Text to Image

Using explicit size:

```bash
python scripts/generate_image.py \
  --prompt "A 16:9 cinematic poster for an AI-powered creative studio, elegant composition, premium studio lighting, space for a bold title, high-end editorial design" \
  --size 1792x1024
```

Using aspect ratio preset:

```bash
python scripts/generate_image.py \
  --prompt "A cinematic poster for an AI-powered creative studio, elegant composition, premium studio lighting" \
  --size 16:9
```

With negative prompt:

```bash
python scripts/generate_image.py \
  --prompt "A product hero shot, clean background, professional lighting" \
  --negative "blurry, distorted, low quality, watermark, text"
```

With model fallback:

```bash
python scripts/generate_image.py \
  --prompt "A product hero shot" \
  --model "agnes-image-2.0-flash,agnes-image-1.5-flash"
```

With auto-download:

```bash
python scripts/generate_image.py \
  --prompt "A product hero shot" \
  --download-to ./output/product.png
```

Dry run (validate only):

```bash
python scripts/generate_image.py \
  --prompt "test" \
  --dry-run
```

Expected output:

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

## 3. Image Editing / Image to Image

```bash
python scripts/edit_image.py \
  --prompt "Transform the input into a polished social media product hero image. Keep the product geometry unchanged, improve lighting, add a clean neutral background, 16:9 composition." \
  --image-url "https://example.com/product.png" \
  --size 1792x1024
```

Multiple input images:

```bash
python scripts/edit_image.py \
  --prompt "Combine these images into a side-by-side comparison" \
  --image-url "https://example.com/before.png" \
  --image-url "https://example.com/after.png"
```

## 4. Text to Video

```bash
python scripts/generate_video.py \
  --prompt "A 5 second cinematic product reveal, slow dolly-in camera movement, soft studio reflections, premium technology commercial style" \
  --ratio 16:9 \
  --duration 5 \
  --poll-interval 5 \
  --timeout-seconds 600
```

## 5. Image to Video

```bash
python scripts/image_to_video.py \
  --prompt "Animate the image with a subtle camera push-in, gentle parallax, natural light shimmer, no distortion of the main subject" \
  --image-url "https://example.com/cover.png" \
  --ratio 16:9 \
  --duration 5 \
  --poll-interval 5 \
  --timeout-seconds 600
```

## Prompt Workflow for Agents

1. Read the user's request.
2. Convert it into a concise, specific English prompt.
3. Preserve requested style, subject, brand, dimensions, duration, and constraints.
4. Add `--negative` if the user specifies things to avoid.
5. Choose the matching script.
6. Use `--download-to` if the user wants a local file.
7. Parse the JSON response from stdout.
