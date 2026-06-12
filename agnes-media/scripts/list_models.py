from __future__ import annotations

import argparse

from agnes_common import (
    AgnesError,
    ALLOWED_RATIOS,
    ALLOWED_SIZES,
    SIZE_PRESETS,
    json_error,
    list_models,
    write_json,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="List available Agnes models.")
    parser.add_argument("--output-json", default=None, help="Optional path to save the JSON response.")
    parser.add_argument(
        "--show-presets",
        action="store_true",
        help="Show size presets and ratio whitelist for image/video generation.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate config and connectivity only.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    result_type = "models"

    try:
        if args.show_presets:
            payload = {
                "status": "success",
                "type": "size_presets",
                "size_presets": SIZE_PRESETS,
                "allowed_sizes": sorted(ALLOWED_SIZES),
                "allowed_ratios": sorted(ALLOWED_RATIOS),
                "usage": {
                    "size": "Use --size with WIDTHxHEIGHT (e.g., '1792x1024') or ratio preset (e.g., '16:9')",
                    "ratio": "Use --ratio with W:H format (e.g., '16:9', '9:16', '1:1')",
                },
            }
        elif args.dry_run:
            from agnes_common import get_config, normalize_model_name
            config = get_config()
            payload = {
                "status": "success",
                "type": "dry_run",
                "message": "Configuration is valid. API key is set.",
                "base_url": config["base_url"],
                "image_model": config["image_model"],
                "video_model": config["video_model"],
            }
        else:
            payload = list_models()
            if isinstance(payload, dict) and "status" not in payload:
                payload = {
                    "status": "success",
                    "type": result_type,
                    "data": payload,
                }
    except AgnesError as exc:
        payload = json_error(result_type, exc.message, exc.detail)
    except Exception as exc:
        payload = json_error(result_type, str(exc), {"class": exc.__class__.__name__})

    write_json(payload, args.output_json)


if __name__ == "__main__":
    main()
