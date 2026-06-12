from __future__ import annotations

import argparse
import sys

from agnes_common import (
    AgnesError,
    DEFAULT_IMAGE_MODEL,
    download_file,
    edit_image,
    get_config,
    json_error,
    write_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Edit or transform images with Agnes Image API.")
    parser.add_argument("--prompt", required=True, help="English edit prompt.")
    parser.add_argument("--image-url", action="append", required=True, help="Input image URL. Repeat for multiple images.")
    parser.add_argument("--negative", default=None, help="Negative prompt to exclude from generation.")
    parser.add_argument("--size", default="1792x1024", help="Image size (e.g., 1792x1024) or ratio preset (e.g., 16:9).")
    parser.add_argument("--model", default=None, help="Agnes image model. Supports comma-separated fallback list.")
    parser.add_argument("--output-json", default=None, help="Optional path to save the JSON response.")
    parser.add_argument("--download-to", default=None, help="Download result image to this path.")
    parser.add_argument("--dry-run", action="store_true", help="Validate parameters only, don't call API.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result_type = "edit_image"

    try:
        config = get_config()
        model = args.model or config.get("image_model") or DEFAULT_IMAGE_MODEL

        # Build prompt with negative if provided
        prompt = args.prompt
        if args.negative:
            prompt = f"{prompt}\n\nNegative: {args.negative}"

        if args.dry_run:
            from agnes_common import validate_size, _parse_model_list
            validate_size(args.size)
            models = _parse_model_list(model)
            payload = {
                "status": "success",
                "type": "dry_run",
                "message": "All parameters validated successfully.",
                "model": models[0],
                "models_fallback": models,
                "size": args.size,
                "image_count": len(args.image_url),
                "prompt_length": len(prompt),
            }
        else:
            payload = edit_image(prompt, args.image_url, model, args.size)

            # Auto-download if requested
            if args.download_to and payload.get("status") == "success" and payload.get("result_url"):
                try:
                    local_path = download_file(payload["result_url"], args.download_to)
                    payload["local_path"] = local_path
                    print(f"[agnes-media] Downloaded to: {local_path}", file=sys.stderr)
                except AgnesError as exc:
                    payload["download_error"] = exc.message
                    print(f"[agnes-media] Download failed: {exc.message}", file=sys.stderr)

    except AgnesError as exc:
        payload = json_error(result_type, exc.message, exc.detail)
    except Exception as exc:
        payload = json_error(result_type, str(exc), {"class": exc.__class__.__name__})

    write_json(payload, args.output_json)


if __name__ == "__main__":
    main()
