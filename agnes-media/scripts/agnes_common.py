from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://apihub.agnes-ai.com/v1"
DEFAULT_IMAGE_MODEL = "agnes-image-2.0-flash"
DEFAULT_VIDEO_MODEL = "agnes-video-2.0"
DEFAULT_TIMEOUT = 60

# Strict whitelist for image sizes
ALLOWED_SIZES = {"1792x1024", "1024x1024", "1024x1792", "1024x768", "768x1024"}

# Size presets (ratio -> size)
SIZE_PRESETS = {
    "16:9": "1792x1024",
    "9:16": "1024x1792",
    "1:1": "1024x1024",
    "4:3": "1024x768",
    "3:4": "768x1024",
}

# Strict whitelist for video ratios
ALLOWED_RATIOS = {"16:9", "9:16", "1:1", "4:3", "3:4"}

# Heartbeat interval for long-running operations (seconds)
HEARTBEAT_INTERVAL = 10


class AgnesError(Exception):
    def __init__(self, message: str, detail: Any | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.detail = detail or {}


def _ensure_dependencies() -> None:
    """Auto-install dependencies if missing. Retries once after install."""
    required = {"openai": "openai", "requests": "requests", "dotenv": "python-dotenv"}
    missing = []
    for module, package in required.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)

    if not missing:
        return

    requirements_path = Path(__file__).resolve().parent.parent / "requirements.txt"
    if not requirements_path.exists():
        raise AgnesError(
            f"Missing dependencies: {', '.join(missing)}.",
            {"hint": f"Run: python -m pip install {' '.join(missing)}"},
        )

    print(f"[agnes-media] Auto-installing missing dependencies: {', '.join(missing)}", file=sys.stderr)
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-r", str(requirements_path)],
            stdout=subprocess.DEVNULL,
        )
        print("[agnes-media] Dependencies installed successfully.", file=sys.stderr)
    except subprocess.CalledProcessError as exc:
        raise AgnesError(
            f"Failed to install dependencies: {', '.join(missing)}.",
            {"hint": f"Run manually: python -m pip install -r {requirements_path}", "error": str(exc)},
        ) from exc


def normalize_model_name(model: str) -> str:
    """Normalize model name to lowercase for API compatibility."""
    return model.strip().lower()


def _parse_model_list(model_str: str) -> list[str]:
    """Parse comma-separated model list for fallback support."""
    return [normalize_model_name(m) for m in model_str.split(",") if m.strip()]


def validate_size(size: str) -> str:
    """Validate size against strict whitelist.

    Accepts:
    - Aspect ratio presets: "16:9", "1:1", etc. (converted to WxH)
    - Direct size format: "1792x1024" (must be in ALLOWED_SIZES)

    Raises AgnesError if not in whitelist.
    """
    # Check if it's a preset ratio
    if size in SIZE_PRESETS:
        return SIZE_PRESETS[size]

    # Check against whitelist
    if size not in ALLOWED_SIZES:
        raise AgnesError(
            f"Invalid size: '{size}'.",
            {
                "hint": "Use an allowed size or aspect ratio preset.",
                "allowed_sizes": sorted(ALLOWED_SIZES),
                "allowed_presets": SIZE_PRESETS,
            },
        )
    return size


def validate_ratio(ratio: str) -> str:
    """Validate video ratio against strict whitelist.

    Raises AgnesError if not in ALLOWED_RATIOS.
    """
    if ratio not in ALLOWED_RATIOS:
        raise AgnesError(
            f"Invalid ratio: '{ratio}'.",
            {
                "hint": "Use one of the allowed ratios.",
                "allowed_ratios": sorted(ALLOWED_RATIOS),
            },
        )
    return ratio


def load_environment() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError as exc:
        raise AgnesError(
            "Missing python-dotenv dependency.",
            {"hint": "Run: python -m pip install -r requirements.txt", "class": exc.__class__.__name__},
        ) from exc

    current = Path.cwd().resolve()
    candidates = [current / ".env", *[parent / ".env" for parent in current.parents]]
    script_root = Path(__file__).resolve().parents[1]
    candidates.append(script_root / ".env")

    seen: set[Path] = set()
    for candidate in candidates:
        if candidate in seen:
            continue
        seen.add(candidate)
        if candidate.exists():
            load_dotenv(candidate, override=False)


def get_config() -> dict[str, str]:
    load_environment()
    api_key = os.getenv("AGNES_API_KEY", "").strip()
    if not api_key:
        raise AgnesError(
            "Missing AGNES_API_KEY.",
            {"hint": "Set AGNES_API_KEY in the environment or in a .env file."},
        )

    return {
        "api_key": api_key,
        "base_url": os.getenv("AGNES_BASE_URL", DEFAULT_BASE_URL).rstrip("/"),
        "image_model": os.getenv("AGNES_IMAGE_MODEL", DEFAULT_IMAGE_MODEL),
        "video_model": os.getenv("AGNES_VIDEO_MODEL", DEFAULT_VIDEO_MODEL),
    }


def _model_not_found_error(model: str, model_type: str) -> AgnesError:
    """Create a helpful error when a model is not found."""
    script_dir = Path(__file__).resolve().parent
    return AgnesError(
        f"Model '{model}' not found on this channel.",
        {
            "hint": (
                f"Run `python {script_dir / 'list_models.py'}` to see what's available.\n"
                f"Or set AGNES_{model_type.upper()}_MODEL in .env to one of the IDs it returns."
            ),
            "model": model,
            "model_type": model_type,
        },
    )


def _heartbeat_thread(stop_event: Any, label: str) -> None:
    """Print heartbeat messages to stderr while a long operation runs."""
    start = time.monotonic()
    while not stop_event.is_set():
        stop_event.wait(HEARTBEAT_INTERVAL)
        if not stop_event.is_set():
            elapsed = int(time.monotonic() - start)
            print(f"[agnes-media] {label} still generating... (elapsed: {elapsed}s)", file=sys.stderr)


def _start_heartbeat(label: str) -> tuple[Any, Any]:
    """Start a heartbeat thread. Returns (thread, stop_event)."""
    import threading

    stop_event = threading.Event()
    thread = threading.Thread(target=_heartbeat_thread, args=(stop_event, label), daemon=True)
    thread.start()
    return thread, stop_event


def _stop_heartbeat(thread: Any, stop_event: Any) -> None:
    """Stop the heartbeat thread."""
    stop_event.set()
    thread.join(timeout=1)


def json_success(
    result_type: str,
    model: str,
    prompt: str,
    result_url: str | None,
    raw_response: Any,
) -> dict[str, Any]:
    return {
        "status": "success",
        "type": result_type,
        "model": model,
        "prompt": prompt,
        "result_url": result_url,
        "raw_response": raw_response,
    }


def json_error(result_type: str, message: str, detail: Any | None = None) -> dict[str, Any]:
    return {
        "status": "error",
        "type": result_type,
        "message": message,
        "detail": detail or {},
    }


def write_json(payload: dict[str, Any], output_json: str | None = None) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    if output_json:
        Path(output_json).write_text(text + "\n", encoding="utf-8")
    sys.stdout.write(text + "\n")


def openai_image_client() -> tuple[Any, dict[str, str]]:
    """Create OpenAI client and return (client, config) tuple."""
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise AgnesError(
            "Missing openai dependency.",
            {"hint": "Run: python -m pip install -r requirements.txt", "class": exc.__class__.__name__},
        ) from exc

    config = get_config()
    client = OpenAI(api_key=config["api_key"], base_url=config["base_url"])
    return client, config


def response_to_dict(response: Any) -> dict[str, Any]:
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if isinstance(response, dict):
        return response
    return json.loads(json.dumps(response, default=str))


def extract_image_url(raw_response: dict[str, Any]) -> str | None:
    data = raw_response.get("data")
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            return first.get("url") or first.get("b64_json")
    return raw_response.get("url") or raw_response.get("result_url")


def _call_with_fallback(func: Any, models: list[str], *args: Any, **kwargs: Any) -> Any:
    """Call a function with model fallback support.

    Tries each model in order. If a model returns 503, tries the next one.
    """
    last_exc = None
    for model in models:
        try:
            return func(*args, model=model, **kwargs)
        except AgnesError as exc:
            last_exc = exc
            # Check if it's a 503 or model-not-found error
            if "503" in str(exc.detail) or "not found" in exc.message.lower():
                if model != models[-1]:
                    print(f"[agnes-media] Model '{model}' unavailable, trying next...", file=sys.stderr)
                    continue
            raise
    raise last_exc


def generate_image(prompt: str, model: str, size: str) -> dict[str, Any]:
    """Generate image with validation, fallback, and heartbeat."""
    size = validate_size(size)
    models = _parse_model_list(model)

    # Ensure dependencies before trying
    _ensure_dependencies()

    thread, stop_event = None, None
    try:
        client, config = openai_image_client()
        thread, stop_event = _start_heartbeat("Image generation")

        def _do_generate(model: str = model) -> dict[str, Any]:
            response = client.images.generate(model=model, prompt=prompt, size=size)
            return response_to_dict(response)

        raw = _call_with_fallback(lambda model: _do_generate(model), models)
        result_url = extract_image_url(raw)
        return json_success("image", models[0], prompt, result_url, raw)

    except Exception as exc:
        if isinstance(exc, AgnesError):
            raise
        error_msg = str(exc)
        if "not_found" in error_msg or "model" in error_msg.lower():
            raise _model_not_found_error(models[0], "image") from exc
        raise AgnesError(
            f"Image generation failed: {exc}",
            {"model": models[0], "size": size, "error_type": exc.__class__.__name__},
        ) from exc
    finally:
        if thread and stop_event:
            _stop_heartbeat(thread, stop_event)


def edit_image(prompt: str, image_urls: list[str], model: str, size: str) -> dict[str, Any]:
    """Edit image with validation, fallback, and heartbeat."""
    size = validate_size(size)
    models = _parse_model_list(model)

    _ensure_dependencies()

    try:
        import requests
    except ImportError as exc:
        raise AgnesError(
            "Missing requests dependency.",
            {"hint": "Run: python -m pip install -r requirements.txt", "class": exc.__class__.__name__},
        ) from exc

    config = get_config()
    url = f"{config['base_url']}/images/edits"
    payload = {
        "prompt": prompt,
        "image_url": image_urls[0] if len(image_urls) == 1 else image_urls,
        "size": size,
    }

    thread, stop_event = None, None
    try:
        thread, stop_event = _start_heartbeat("Image editing")

        def _do_edit(model: str) -> dict[str, Any]:
            payload["model"] = model
            response = requests.post(
                url,
                headers=auth_headers(config["api_key"]),
                json=payload,
                timeout=DEFAULT_TIMEOUT,
            )
            return parse_response(response)

        raw = _call_with_fallback(_do_edit, models)
        return json_success("edit_image", models[0], prompt, extract_image_url(raw), raw)

    except Exception as exc:
        if isinstance(exc, AgnesError):
            raise
        error_msg = str(exc)
        if "not_found" in error_msg or "model" in error_msg.lower():
            raise _model_not_found_error(models[0], "image") from exc
        raise AgnesError(
            f"Image editing failed: {exc}",
            {"model": models[0], "size": size, "error_type": exc.__class__.__name__},
        ) from exc
    finally:
        if thread and stop_event:
            _stop_heartbeat(thread, stop_event)


def auth_headers(api_key: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }


def parse_response(response: Any) -> dict[str, Any]:
    try:
        body = response.json()
    except ValueError:
        body = {"text": response.text}
    if response.status_code >= 400:
        raise AgnesError(
            f"Agnes API request failed with HTTP {response.status_code}.",
            body,
        )
    if not isinstance(body, dict):
        return {"data": body}
    return body


def create_video_task(
    prompt: str,
    model: str,
    ratio: str,
    duration: int,
    image_url: str | None = None,
) -> dict[str, Any]:
    """Create video task with validation and normalized model name."""
    model = normalize_model_name(model)
    ratio = validate_ratio(ratio)

    try:
        import requests
    except ImportError as exc:
        raise AgnesError(
            "Missing requests dependency.",
            {"hint": "Run: python -m pip install -r requirements.txt", "class": exc.__class__.__name__},
        ) from exc

    config = get_config()
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "ratio": ratio,
        "duration": duration,
    }
    if image_url:
        payload["image_url"] = image_url

    try:
        response = requests.post(
            f"{config['base_url']}/videos",
            headers=auth_headers(config["api_key"]),
            json=payload,
            timeout=DEFAULT_TIMEOUT,
        )
        return parse_response(response)
    except Exception as exc:
        if isinstance(exc, AgnesError):
            raise
        raise AgnesError(
            f"Video task creation failed: {exc}",
            {"model": model, "ratio": ratio, "error_type": exc.__class__.__name__},
        ) from exc


def get_video_task(task_id: str) -> dict[str, Any]:
    try:
        import requests
    except ImportError as exc:
        raise AgnesError(
            "Missing requests dependency.",
            {"hint": "Run: python -m pip install -r requirements.txt", "class": exc.__class__.__name__},
        ) from exc

    config = get_config()
    response = requests.get(
        f"{config['base_url']}/videos/{task_id}",
        headers=auth_headers(config["api_key"]),
        timeout=DEFAULT_TIMEOUT,
    )
    return parse_response(response)


def extract_task_id(raw_response: dict[str, Any]) -> str | None:
    for key in ("id", "task_id", "video_id"):
        value = raw_response.get(key)
        if isinstance(value, str) and value:
            return value
    data = raw_response.get("data")
    if isinstance(data, dict):
        for key in ("id", "task_id", "video_id"):
            value = data.get(key)
            if isinstance(value, str) and value:
                return value
    return None


def extract_video_url(raw_response: dict[str, Any]) -> str | None:
    for key in ("result_url", "video_url", "url", "output_url"):
        value = raw_response.get(key)
        if isinstance(value, str) and value:
            return value
    data = raw_response.get("data")
    if isinstance(data, dict):
        return extract_video_url(data)
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            return extract_video_url(first)
    output = raw_response.get("output")
    if isinstance(output, dict):
        return extract_video_url(output)
    if isinstance(output, list) and output:
        first = output[0]
        if isinstance(first, dict):
            return extract_video_url(first)
    return None


def task_status(raw_response: dict[str, Any]) -> str:
    status = raw_response.get("status")
    if isinstance(status, str):
        return status.lower()
    data = raw_response.get("data")
    if isinstance(data, dict):
        status = data.get("status")
        if isinstance(status, str):
            return status.lower()
    return ""


def wait_for_video(task_id: str, poll_interval: float, timeout_seconds: int) -> dict[str, Any]:
    """Poll video task with heartbeat messages."""
    deadline = time.monotonic() + timeout_seconds
    last_response: dict[str, Any] = {}
    last_heartbeat = time.monotonic()

    while time.monotonic() < deadline:
        last_response = get_video_task(task_id)
        status = task_status(last_response)
        if status in {"succeeded", "success", "completed", "complete", "done"}:
            return last_response
        if status in {"failed", "error", "cancelled", "canceled"}:
            raise AgnesError("Agnes video task failed.", last_response)

        # Heartbeat
        now = time.monotonic()
        if now - last_heartbeat >= HEARTBEAT_INTERVAL:
            elapsed = int(now - (deadline - timeout_seconds))
            print(f"[agnes-media] Video processing... (elapsed: {elapsed}s, status: {status})", file=sys.stderr)
            last_heartbeat = now

        time.sleep(poll_interval)

    raise AgnesError("Timed out while polling Agnes video task.", last_response)


def generate_video(
    result_type: str,
    prompt: str,
    model: str,
    ratio: str,
    duration: int,
    poll_interval: float,
    timeout_seconds: int,
    image_url: str | None = None,
) -> dict[str, Any]:
    _ensure_dependencies()

    models = _parse_model_list(model)
    last_exc = None

    for m in models:
        try:
            normalized_model = normalize_model_name(m)
            normalized_ratio = validate_ratio(ratio)
            created = create_video_task(prompt, normalized_model, normalized_ratio, duration, image_url=image_url)
            task_id = extract_task_id(created)
            if not task_id:
                result_url = extract_video_url(created)
                if result_url:
                    return json_success(result_type, normalized_model, prompt, result_url, created)
                raise AgnesError("Agnes video response did not include a task id or result URL.", created)

            final_response = wait_for_video(task_id, poll_interval, timeout_seconds)
            return json_success(result_type, normalized_model, prompt, extract_video_url(final_response), final_response)
        except AgnesError as exc:
            last_exc = exc
            if "503" in str(exc.detail) or "not found" in exc.message.lower():
                if m != models[-1]:
                    print(f"[agnes-media] Model '{m}' unavailable, trying next...", file=sys.stderr)
                    continue
            raise

    raise last_exc


def list_models() -> dict[str, Any]:
    """List all available Agnes models from the API."""
    _ensure_dependencies()

    try:
        import requests
    except ImportError as exc:
        raise AgnesError(
            "Missing requests dependency.",
            {"hint": "Run: python -m pip install -r requirements.txt", "class": exc.__class__.__name__},
        ) from exc

    config = get_config()
    try:
        response = requests.get(
            f"{config['base_url']}/models",
            headers=auth_headers(config["api_key"]),
            timeout=DEFAULT_TIMEOUT,
        )
        return parse_response(response)
    except Exception as exc:
        if isinstance(exc, AgnesError):
            raise
        raise AgnesError(
            f"Failed to list models: {exc}",
            {"error_type": exc.__class__.__name__},
        ) from exc


def download_file(url: str, dest_path: str) -> str:
    """Download a file from URL to local path."""
    _ensure_dependencies()

    try:
        import requests
    except ImportError as exc:
        raise AgnesError(
            "Missing requests dependency.",
            {"hint": "Run: python -m pip install -r requirements.txt", "class": exc.__class__.__name__},
        ) from exc

    try:
        response = requests.get(url, stream=True, timeout=120)
        response.raise_for_status()

        dest = Path(dest_path)
        dest.parent.mkdir(parents=True, exist_ok=True)

        with open(dest, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return str(dest.resolve())
    except Exception as exc:
        raise AgnesError(
            f"Failed to download file: {exc}",
            {"url": url, "dest": dest_path, "error_type": exc.__class__.__name__},
        ) from exc


def positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise ValueError("value must be positive")
    return parsed
