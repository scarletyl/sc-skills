from __future__ import annotations

import argparse
import sys

from agnes_common import (
    AgnesError,
    DEFAULT_VIDEO_MODEL,
    download_file,
    generate_video,
    get_config,
    json_error,
    positive_int,
    write_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate a video from an image with Agnes Video API.")
    parser.add_argument("--prompt", required=True, help="English video prompt.")
    parser.add_argument("--image-url", required=True, help="Input image URL.")
    parser.add_argument("--negative", default=None, help="Negative prompt to exclude from generation.")
    parser.add_argument("--ratio", default="16:9", help="Video aspect ratio (e.g., 16:9, 9:16, 1:1).")
    parser.add_argument("--duration", type=positive_int, default=5, help="Video duration in seconds, default: 5.")
    parser.add_argument("--model", default=None, help="Agnes video model. Supports comma-separated fallback list.")
    parser.add_argument("--poll-interval", type=float, default=5, help="Polling interval in seconds, default: 5.")
    parser.add_argument("--timeout-seconds", type=positive_int, default=600, help="Polling timeout in seconds, default: 600.")
    parser.add_argument("--output-json", default=None, help="Optional path to save the JSON response.")
    parser.add_argument("--download-to", default=None, help="Download result video to this path.")
    parser.add_argument("--dry-run", action="store_true", help="Validate parameters only, don't call API.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result_type = "image_to_video"

    try:
        config = get_config()
        model = args.model or config.get("video_model") or DEFAULT_VIDEO_MODEL

        # Build prompt with negative if provided
        prompt = args.prompt
        if args.negative:
            prompt = f"{prompt}\n\nNegative: {args.negative}"

        if args.dry_run:
            from agnes_common import validate_ratio, _parse_model_list
            validate_ratio(args.ratio)
            models = _parse_model_list(model)
            payload = {
                "status": "success",
                "type": "dry_run",
                "message": "All parameters validated successfully.",
                "model": models[0],
                "models_fallback": models,
                "ratio": args.ratio,
                "duration": args.duration,
                "image_url": args.image_url,
                "prompt_length": len(prompt),
            }
        else:
            payload = generate_video(
                result_type=result_type,
                prompt=prompt,
                model=model,
                ratio=args.ratio,
                duration=args.duration,
                poll_interval=args.poll_interval,
                timeout_seconds=args.timeout_seconds,
                image_url=args.image_url,
            )

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
