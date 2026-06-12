#!/usr/bin/env python3
"""Validate WeChat Official Account HTML fragments."""

from __future__ import annotations

import argparse
import re
import sys
from html.parser import HTMLParser
from pathlib import Path


STRICT_TAGS = {"section", "p", "span", "strong", "em", "ul", "ol", "li", "br", "hr"}
MEDIA_TAGS = STRICT_TAGS | {"a", "img"}
GLOBAL_ALLOWED_ATTRS = {"style"}
MEDIA_ALLOWED_ATTRS = {
    "a": {"style", "href", "target", "rel"},
    "img": {"style", "src", "alt"},
}
VOID_TAGS = {"br", "hr", "img"}


class FragmentValidator(HTMLParser):
    def __init__(self, allowed_tags: set[str], mode: str) -> None:
        super().__init__(convert_charrefs=True)
        self.allowed_tags = allowed_tags
        self.mode = mode
        self.errors: list[str] = []
        self.stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._check_tag(tag, attrs)
        if tag not in VOID_TAGS:
            self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self._check_tag(tag, attrs)

    def handle_endtag(self, tag: str) -> None:
        if tag in VOID_TAGS:
            return
        if not self.stack:
            self.errors.append(f"Unexpected closing tag </{tag}>.")
            return
        open_tag = self.stack.pop()
        if open_tag != tag:
            self.errors.append(f"Mismatched closing tag </{tag}> after <{open_tag}>.")

    def handle_comment(self, data: str) -> None:
        self.errors.append("HTML comments are not allowed.")

    def _check_tag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag not in self.allowed_tags:
            self.errors.append(f"Tag <{tag}> is not allowed.")
            return

        allowed_attrs = set(GLOBAL_ALLOWED_ATTRS)
        if self.mode == "media":
            allowed_attrs |= MEDIA_ALLOWED_ATTRS.get(tag, set())

        for name, value in attrs:
            if name not in allowed_attrs:
                self.errors.append(f"Attribute '{name}' is not allowed on <{tag}>.")
            if name == "class":
                self.errors.append("class attributes are not allowed.")
            if name == "style":
                if value is None or not value.strip():
                    self.errors.append(f"Empty style attribute on <{tag}>.")
                else:
                    self._check_style(tag, value)
            if name in {"href", "src"} and value is not None:
                self._check_url(tag, name, value)

    def _check_style(self, tag: str, style: str) -> None:
        lowered = style.lower()
        if "expression(" in lowered or "javascript:" in lowered:
            self.errors.append(f"Unsafe style value on <{tag}>.")
        if re.search(r"(?:^|;)\s*max-width\s*:\s*\d+px\b", lowered):
            self.errors.append(f"Fixed px width is not allowed on <{tag}>.")
        if tag not in {"span", "img", "hr"} and re.search(r"(?:^|;)\s*width\s*:\s*\d+px\b", lowered):
            self.errors.append(f"Fixed px width is not allowed on <{tag}>.")
        if "text-indent" in lowered:
            self.errors.append(f"text-indent is not allowed on <{tag}>.")

    def _check_url(self, tag: str, attr: str, value: str) -> None:
        if re.match(r"(?i)\s*javascript:", value):
            self.errors.append(f"Unsafe {attr} URL on <{tag}>.")

    def close(self) -> None:
        super().close()
        for tag in reversed(self.stack):
            self.errors.append(f"Unclosed tag <{tag}>.")


def validate_fragment(html: str, mode: str) -> list[str]:
    errors: list[str] = []
    lowered = html.lower()
    forbidden_literals = ["<!doctype", "<html", "</html", "<head", "</head", "<body", "</body", "<style", "</style", "<script", "</script"]
    for literal in forbidden_literals:
        if literal in lowered:
            errors.append(f"Forbidden document or style/script marker found: {literal}")
    if re.search(r"\bclass\s*=", html, flags=re.IGNORECASE):
        errors.append("class attributes are not allowed.")
    if re.search(r"<\!--", html):
        errors.append("HTML comments are not allowed.")

    parser = FragmentValidator(MEDIA_TAGS if mode == "media" else STRICT_TAGS, mode)
    parser.feed(html)
    parser.close()
    errors.extend(parser.errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a WeChat-ready HTML fragment.")
    parser.add_argument("file", help="HTML fragment to validate")
    parser.add_argument("--mode", choices=["strict", "media"], default="strict")
    args = parser.parse_args()

    html = Path(args.file).read_text(encoding="utf-8")
    errors = validate_fragment(html, args.mode)
    if errors:
        print("Validation failed:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("Validation passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
