"""Smoke test for agnes-media skill.

Validates: dependencies, environment, API key, model connectivity.
Run: python scripts/test_smoke.py
"""
from __future__ import annotations

import sys
import json
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent))


def test_imports() -> bool:
    """Test that all required dependencies are importable."""
    print("  [1/6] Testing imports...", end=" ")
    try:
        import openai
        import requests
        import dotenv
        print("OK")
        return True
    except ImportError as exc:
        print(f"FAILED: {exc}")
        return False


def test_env_file() -> bool:
    """Test that .env file exists or env vars are set."""
    print("  [2/6] Testing environment...", end=" ")
    import os

    # Check if AGNES_API_KEY is already set
    if os.getenv("AGNES_API_KEY"):
        print("OK (from env)")
        return True

    # Check for .env file
    from pathlib import Path
    current = Path.cwd().resolve()
    candidates = [current / ".env", *[p / ".env" for p in current.parents]]
    script_root = Path(__file__).resolve().parents[1]
    candidates.append(script_root / ".env")

    for candidate in candidates:
        if candidate.exists():
            print(f"OK (found {candidate})")
            return True

    print("FAILED: No .env file found and AGNES_API_KEY not set")
    return False


def test_api_key() -> bool:
    """Test that API key is configured."""
    print("  [3/6] Testing API key...", end=" ")
    try:
        from agnes_common import get_config
        config = get_config()
        if config["api_key"]:
            print("OK")
            return True
        print("FAILED: AGNES_API_KEY is empty")
        return False
    except Exception as exc:
        print(f"FAILED: {exc}")
        return False


def test_base_url() -> bool:
    """Test that base URL is reachable."""
    print("  [4/6] Testing base URL connectivity...", end=" ")
    try:
        import requests
        from agnes_common import get_config
        config = get_config()
        response = requests.get(config["base_url"], timeout=10)
        print(f"OK (HTTP {response.status_code})")
        return True
    except Exception as exc:
        print(f"FAILED: {exc}")
        return False


def test_list_models() -> bool:
    """Test that models endpoint is accessible."""
    print("  [5/6] Testing models endpoint...", end=" ")
    try:
        from agnes_common import list_models
        result = list_models()
        if isinstance(result, dict):
            print("OK")
            return True
        print("FAILED: Unexpected response format")
        return False
    except Exception as exc:
        print(f"FAILED: {exc}")
        return False


def test_validators() -> bool:
    """Test parameter validation functions."""
    print("  [6/6] Testing validators...", end=" ")
    try:
        from agnes_common import validate_size, validate_ratio, normalize_model_name

        # Test size validation
        assert validate_size("16:9") == "1792x1024"
        assert validate_size("1792x1024") == "1792x1024"

        # Test ratio validation
        assert validate_ratio("16:9") == "16:9"

        # Test model normalization
        assert normalize_model_name("Agnes-Image-2.0-Flash") == "agnes-image-2.0-flash"

        # Test invalid size raises error
        try:
            validate_size("999x999")
            print("FAILED: Should have raised error for invalid size")
            return False
        except Exception:
            pass

        print("OK")
        return True
    except Exception as exc:
        print(f"FAILED: {exc}")
        return False


def main() -> None:
    print("=" * 50)
    print("agnes-media Smoke Test")
    print("=" * 50)
    print()

    results = []
    results.append(("Imports", test_imports()))
    results.append(("Environment", test_env_file()))

    # Only run API tests if env is configured
    if results[-1][1]:
        results.append(("API Key", test_api_key()))
        results.append(("Base URL", test_base_url()))
        results.append(("Models Endpoint", test_list_models()))
    else:
        print("  [3/6] Skipping API key test (no .env)")
        print("  [4/6] Skipping base URL test (no .env)")
        print("  [5/6] Skipping models endpoint test (no .env)")
        results.append(("API Key", None))
        results.append(("Base URL", None))
        results.append(("Models Endpoint", None))

    results.append(("Validators", test_validators()))

    print()
    print("=" * 50)
    print("Results Summary")
    print("=" * 50)

    all_pass = True
    for name, result in results:
        if result is True:
            status = "[PASS]"
        elif result is False:
            status = "[FAIL]"
            all_pass = False
        else:
            status = "[SKIP]"
        print(f"  {status}  {name}")

    print()
    if all_pass:
        print("All tests passed! The skill is ready to use.")
        sys.exit(0)
    else:
        print("Some tests failed. Please fix the issues above.")
        sys.exit(1)


if __name__ == "__main__":
    main()
