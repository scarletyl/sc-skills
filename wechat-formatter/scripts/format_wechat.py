#!/usr/bin/env python3
"""Convert Markdown, HTML, or plain text into WeChat-ready inline HTML."""

from __future__ import annotations

import argparse
import html
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse


FONT = "-apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif"
MONO = "'SF Mono', Monaco, Consolas, 'Ubuntu Mono', Consolas, 'Courier New', monospace"
DEFAULT_ACCENT = "#077ba9"
DEFAULT_LEAD_ACCENT = "#2bb9a6"

STYLES = {
    "p": f"font-family: {FONT}; font-size: 16px; color: #3f3f3f; line-height: 1.6; letter-spacing: 0; margin: 0 0 20px 0; text-align: justify; text-justify: inter-ideograph;",
    "h1": f"font-family: {FONT}; font-size: 18px; font-weight: bold; color: {DEFAULT_ACCENT}; line-height: 1.45; margin: 28px 0 28px 0; text-align: left; letter-spacing: 1px;",
    "h2": f"font-family: {FONT}; font-size: 17px; font-weight: bold; color: {DEFAULT_ACCENT}; line-height: 1.4; margin: 32px 0 16px 0; padding-left: 12px; border-left: 4px solid {DEFAULT_ACCENT}; letter-spacing: 1px;",
    "h3": f"font-family: {FONT}; font-size: 16px; font-weight: bold; color: {DEFAULT_ACCENT}; line-height: 1.4; margin: 24px 0 12px 0; letter-spacing: 1px;",
    "lead_section": f"font-family: {FONT}; margin: 0 0 28px 0; padding: 0;",
    "lead_label": f"font-family: {FONT}; font-size: 18px; font-weight: bold; color: {DEFAULT_LEAD_ACCENT}; line-height: 1.4; letter-spacing: 1px; margin: 0;",
    "lead_underline": f"width: 58px; border: none; border-top: 3px solid {DEFAULT_LEAD_ACCENT}; margin: 4px 0 18px 0;",
    "lead_p": f"font-family: {FONT}; font-size: 16px; color: #8b8b8b; line-height: 1.8; letter-spacing: 0.5px; margin: 0 0 28px 0; text-align: justify; text-justify: inter-ideograph;",
    "lead_divider": "border: none; border-top: 1px solid #d8d8d8; margin: 0;",
    "strong": f"font-weight: bold; color: {DEFAULT_ACCENT};",
    "em": "font-style: italic; color: #555555;",
    "quote_section": f"font-family: {FONT}; margin: 24px 0; padding: 16px 20px; background-color: #f7f7f7; border-left: 4px solid {DEFAULT_ACCENT}; border-radius: 0 8px 8px 0;",
    "quote_p": f"font-family: {FONT}; font-size: 15px; color: #555555; line-height: 1.8; margin: 0; text-align: justify; text-justify: inter-ideograph;",
    "quote_attr": f"font-family: {FONT}; font-style: normal; font-size: 14px; color: #888888; line-height: 1.7; margin: 8px 0 0 0; text-align: right;",
    "ul": "padding-left: 2em; margin: 0 0 20px 0;",
    "ul_li": f"font-family: {FONT}; font-size: 16px; color: #3f3f3f; line-height: 1.8; margin-bottom: 8px; list-style: disc; text-align: justify; text-justify: inter-ideograph;",
    "ol": "list-style: none; padding: 0; margin: 0 0 24px 0; counter-reset: item;",
    "ol_li": f"font-family: {FONT}; padding: 0; margin-bottom: 10px; font-size: 15px; color: #3f3f3f; line-height: 1.7; list-style: none; text-align: justify; text-justify: inter-ideograph; overflow: hidden;",
    "num": f"float: left; color: #3f3f3f; font-size: 16px; margin-right: 8px;",
    "inline_code": "font-family: Consolas, Monaco, 'Courier New', monospace; font-size: 14px; color: #e83e8c; background-color: #f5f5f5; padding: 2px 6px; border-radius: 4px;",
    "code_outer": f"margin: 18px 0 24px 0; background-color: #1E1E1E; border-radius: 12px; box-shadow: 0 12px 24px rgba(0,0,0,0.22); overflow: hidden; font-family: {MONO};",
    "code_bar": "height: 36px; padding-left: 14px; background-color: #1E1E1E; line-height: 36px;",
    "code_p": "margin: 0; padding: 0 18px 18px 18px; overflow-x: auto; white-space: pre; background-color: #1E1E1E; font-size: 14px; line-height: 1.5; color: #D4D4D4;",
    "code_span": f"font-family: {MONO};",
    "hr": "border: none; border-top: 1px solid #ebebeb; margin: 2em 0;",
    "a": f"color: {DEFAULT_ACCENT}; text-decoration: none; border-bottom: 1px solid {DEFAULT_ACCENT};",
    "img": "display: block; max-width: 100%; height: auto; margin: 20px auto; border-radius: 8px;",
    "table_section": f"font-family: {FONT}; margin: 20px 0;",
    "table_header": f"font-family: {FONT}; font-size: 15px; font-weight: bold; color: {DEFAULT_ACCENT}; margin: 0 0 10px 0; letter-spacing: 0.5px;",
    "table_card": f"font-family: {FONT}; background-color: #f8f9fa; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;",
    "table_card_label": f"font-family: {FONT}; font-size: 14px; color: {DEFAULT_ACCENT}; letter-spacing: 0.5px; margin: 0 0 8px 0;",
    "table_card_item": f"font-family: {FONT}; font-size: 15px; color: #3f3f3f; line-height: 1.7; margin: 4px 0; text-align: justify; text-justify: inter-ideograph;",
}


def valid_hex_color(value: str) -> bool:
    return bool(re.fullmatch(r"#[0-9a-fA-F]{6}", value.strip()))


def apply_accent_color(accent: str, lead_accent: str | None = None) -> None:
    if not valid_hex_color(accent):
        raise ValueError("--accent-color must be a 6-digit hex color, for example #077ba9")
    lead = lead_accent or accent
    if not valid_hex_color(lead):
        raise ValueError("--lead-accent-color must be a 6-digit hex color, for example #2bb9a6")

    STYLES["h2"] = STYLES["h2"].replace(DEFAULT_ACCENT, accent)
    STYLES["h1"] = STYLES["h1"].replace(DEFAULT_ACCENT, accent)
    STYLES["h3"] = STYLES["h3"].replace(DEFAULT_ACCENT, accent)
    STYLES["strong"] = STYLES["strong"].replace(DEFAULT_ACCENT, accent)
    STYLES["quote_section"] = STYLES["quote_section"].replace(DEFAULT_ACCENT, accent)
    STYLES["num"] = STYLES["num"].replace(DEFAULT_ACCENT, accent)
    STYLES["a"] = STYLES["a"].replace(DEFAULT_ACCENT, accent)
    STYLES["table_header"] = STYLES["table_header"].replace(DEFAULT_ACCENT, accent)
    STYLES["table_card_label"] = STYLES["table_card_label"].replace(DEFAULT_ACCENT, accent)
    STYLES["lead_underline"] = STYLES["lead_underline"].replace(DEFAULT_LEAD_ACCENT, lead)
    STYLES["lead_label"] = STYLES["lead_label"].replace(DEFAULT_LEAD_ACCENT, lead)


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def safe_url(value: str) -> str:
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme.lower() not in {"http", "https", "mailto"}:
        return ""
    return value


def protect(pattern: str, text: str, replacements: list[str], render) -> str:
    def repl(match: re.Match[str]) -> str:
        token = f"\u0000{len(replacements)}\u0000"
        replacements.append(render(match))
        return token

    return re.sub(pattern, repl, text)


def render_inline(text: str, mode: str) -> str:
    replacements: list[str] = []

    text = protect(r"!\[([^\]]*)\]\(([^)]+)\)", text, replacements, lambda m: render_image(m.group(1), m.group(2), mode))
    text = protect(r"\[([^\]]+)\]\(([^)]+)\)", text, replacements, lambda m: render_link(m.group(1), m.group(2), mode))
    text = protect(r"`([^`]+)`", text, replacements, lambda m: f'<span style="{STYLES["inline_code"]}">{esc(m.group(1))}</span>')

    text = esc(text)
    text = re.sub(r"\*\*([^*]+)\*\*", lambda m: f'<strong style="{STYLES["strong"]}">{m.group(1)}</strong>', text)
    text = re.sub(r"(?<!\*)\*([^*\n]+)\*(?!\*)", lambda m: f'<em style="{STYLES["em"]}">{m.group(1)}</em>', text)

    for index, value in enumerate(replacements):
        text = text.replace(esc(f"\u0000{index}\u0000"), value)
    return text


def render_link(label: str, url: str, mode: str) -> str:
    url = safe_url(url)
    if not url:
        return esc(label)
    if mode == "media":
        return f'<a href="{esc(url)}" target="_blank" rel="noopener noreferrer" style="{STYLES["a"]}">{esc(label)}</a>'
    return f"{esc(label)}（链接：{esc(url)}）"


def render_image(alt: str, url: str, mode: str) -> str:
    url = safe_url(url)
    label = alt.strip() or url
    if mode == "media" and url:
        return f'<img src="{esc(url)}" alt="{esc(alt)}" style="{STYLES["img"]}" />'
    return f"[图片：{esc(label)}]"


def strip_inline_markup(text: str) -> str:
    text = re.sub(r"!\[([^\]]*)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = text.replace("**", "").replace("*", "")
    return re.sub(r"\s+", " ", text).strip()


def has_lead_marker(source: str) -> bool:
    return bool(re.search(r"(?m)^\s*导读\s*[:：]", source))


def extract_auto_lead(source: str, input_format: str, mode: str) -> str:
    if input_format == "html":
        semantic_parser = SemanticHTMLParser(mode)
        semantic_parser.feed(source)
        semantic_parser.close()
        source = semantic_parser.markdown()

    source = re.sub(r"```.*?```", "", source, flags=re.S)
    candidates: list[str] = []
    current: list[str] = []
    headings: list[str] = []

    for raw in source.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw.strip()
        if not line:
            if current:
                candidates.append(" ".join(current))
                current = []
            continue
        heading_match = re.match(r"^\s*#{1,6}\s+(.+)$", line)
        if heading_match:
            headings.append(strip_inline_markup(heading_match.group(1)))
            if current:
                candidates.append(" ".join(current))
                current = []
            continue
        if re.match(r"^\s*(#{1,6}\s+|[-*]\s+|\d+[.)、]\s+|>\s?|---+\s*$)", line):
            if current:
                candidates.append(" ".join(current))
                current = []
            continue
        if re.match(r"^\s*导读\s*[:：]", line):
            continue
        current.append(line)

    if current:
        candidates.append(" ".join(current))

    for candidate in candidates:
        lead = strip_inline_markup(candidate)
        if len(lead) >= 20:
            return lead[:140].rstrip("，,；;、")
    for candidate in candidates:
        lead = strip_inline_markup(candidate)
        if lead:
            return lead[:140].rstrip("，,；;、")
    if headings:
        title = headings[0][:80].rstrip("，,；;、")
        return f"本文围绕“{title}”展开，梳理核心信息、关键背景与值得关注的要点，帮助读者快速把握文章主线。"
    return "本文整理了文章中的核心信息、关键背景与主要看点，帮助读者快速把握内容主线。"


def paragraph(text: str, mode: str) -> str:
    return f'<p style="{STYLES["p"]}">{render_inline(text.strip(), mode)}</p>'


def heading(level: int, text: str, mode: str) -> str:
    key = "h1" if level <= 1 else "h2" if level == 2 else "h3"
    return f'<p style="{STYLES[key]}">{render_inline(text.strip(), mode)}</p>'


def lead_block(text: str, mode: str) -> str:
    return (
        f'<section style="{STYLES["lead_section"]}">'
        f'<p style="{STYLES["lead_label"]}">导读</p>'
        f'<hr style="{STYLES["lead_underline"]}" />'
        f'<p style="{STYLES["lead_p"]}">{render_inline(text.strip(), mode)}</p>'
        '</section>'
    )


def quote_block(lines: list[str], mode: str) -> str:
    attribution = ""
    if lines and re.match(r"^\s*(?:[-—–]|&mdash;)\s*\S+", lines[-1]):
        attribution = re.sub(r"^\s*(?:[-—–]|&mdash;)\s*", "", lines.pop()).strip()
    inner = []
    for line in lines:
        if line.strip():
            inner.append(f'<p style="{STYLES["quote_p"]}">{render_inline(line.strip(), mode)}</p>')
    if attribution:
        inner.append(f'<p style="{STYLES["quote_attr"]}">— {esc(attribution)}</p>')
    return f'<section style="{STYLES["quote_section"]}">' + "".join(inner) + "</section>"


def code_block(code: str) -> str:
    return (
        f'<section style="{STYLES["code_outer"]}">'
        f'<section style="{STYLES["code_bar"]}">'
        '<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #FF5F56; margin-right: 8px;"></span>'
        '<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #FFBD2E; margin-right: 8px;"></span>'
        '<span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #27C93F;"></span>'
        '</section>'
        f'<p style="{STYLES["code_p"]}"><span style="{STYLES["code_span"]}">{esc(code.rstrip())}</span></p>'
        '</section>'
    )


def render_list(kind: str, items: list[str], mode: str) -> str:
    if kind == "ul":
        body = "".join(f'<li style="{STYLES["ul_li"]}">{render_inline(item, mode)}</li>' for item in items)
        return f'<ul style="{STYLES["ul"]}">{body}</ul>'
    body = "".join(
        f'<li style="{STYLES["ol_li"]}"><span style="{STYLES["num"]}">{i}</span>{render_inline(item, mode)}</li>'
        for i, item in enumerate(items, 1)
    )
    return f'<ol style="{STYLES["ol"]}">{body}</ol>'


def parse_table_row(line: str) -> list[str]:
    cells = line.strip().strip("|").split("|")
    return [c.strip() for c in cells]


def is_table_separator(line: str) -> bool:
    return bool(re.match(r"^\s*\|?\s*[-:]+[-|:\s]+\s*\|?\s*$", line))


def render_table(headers: list[str], rows: list[list[str]], mode: str) -> str:
    first_col_unique = len({r[0] for r in rows if r}) == len(rows)

    cards = []
    if first_col_unique and len(headers) > 1:
        sub_headers = headers[1:]
        for row in rows:
            card_title = render_inline(row[0], mode)
            items = []
            for i, header in enumerate(sub_headers):
                value = render_inline(row[i + 1], mode) if i + 1 < len(row) else ""
                items.append(
                    f'<p style="{STYLES["table_card_item"]}">'
                    f'<strong style="{STYLES["strong"]}">{esc(header)}</strong>：{value}</p>'
                )
            cards.append(
                f'<section style="{STYLES["table_card"]}">'
                f'<p style="{STYLES["table_card_label"]}">{card_title}</p>'
                f'{"".join(items)}</section>'
            )
        title = " / ".join(sub_headers)
    else:
        for row in rows:
            items = []
            for i, header in enumerate(headers):
                value = render_inline(row[i], mode) if i < len(row) else ""
                items.append(
                    f'<p style="{STYLES["table_card_item"]}">'
                    f'<strong style="{STYLES["strong"]}">{esc(header)}</strong>：{value}</p>'
                )
            cards.append(f'<section style="{STYLES["table_card"]}">{"".join(items)}</section>')
        title = " / ".join(headers)
    return (
        f'<section style="{STYLES["table_section"]}">'
        f'<p style="{STYLES["table_header"]}">{esc(title)}</p>'
        f'{"".join(cards)}'
        f'</section>'
    )


def flush_paragraph(lines: list[str], out: list[str], mode: str) -> None:
    if lines:
        out.append(paragraph(" ".join(line.strip() for line in lines if line.strip()), mode))
        lines.clear()


def flush_list(kind: str | None, items: list[str], out: list[str], mode: str) -> None:
    if kind and items:
        out.append(render_list(kind, items, mode))
        items.clear()


def parse_markdown(source: str, mode: str) -> str:
    lines = source.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    out: list[str] = []
    paragraph_lines: list[str] = []
    list_kind: str | None = None
    list_items: list[str] = []
    quote_lines: list[str] = []
    lead_lines: list[str] | None = None
    in_code = False
    code_lines: list[str] = []
    table_headers: list[str] | None = None
    table_rows: list[list[str]] = []
    table_separator_seen = False

    def flush_quotes() -> None:
        if quote_lines:
            out.append(quote_block(quote_lines.copy(), mode))
            quote_lines.clear()

    def flush_table() -> None:
        nonlocal table_headers, table_separator_seen
        if table_headers and table_rows:
            out.append(render_table(table_headers, table_rows, mode))
        table_headers = None
        table_rows.clear()
        table_separator_seen = False

    def flush_lead() -> None:
        nonlocal lead_lines
        if lead_lines is not None:
            lead_text = " ".join(line.strip() for line in lead_lines if line.strip())
            if lead_text:
                out.append(lead_block(lead_text, mode))
            lead_lines = None

    for raw in lines:
        line = raw.rstrip("\n")

        if line.strip().startswith("```"):
            flush_paragraph(paragraph_lines, out, mode)
            flush_list(list_kind, list_items, out, mode)
            list_kind = None
            flush_quotes()
            if in_code:
                out.append(code_block("\n".join(code_lines)))
                code_lines.clear()
                in_code = False
            else:
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        table_row_match = re.match(r"^\s*\|.+\|\s*$", line)
        if table_row_match:
            if is_table_separator(line):
                if table_headers is not None:
                    table_separator_seen = True
                continue
            cells = parse_table_row(line)
            if table_headers is None:
                flush_paragraph(paragraph_lines, out, mode)
                flush_list(list_kind, list_items, out, mode)
                list_kind = None
                flush_quotes()
                table_headers = cells
            elif table_separator_seen:
                table_rows.append(cells)
            else:
                flush_table()
                flush_paragraph(paragraph_lines, out, mode)
                flush_list(list_kind, list_items, out, mode)
                list_kind = None
                flush_quotes()
                table_headers = cells
            continue
        else:
            flush_table()

        if lead_lines is not None:
            if not line.strip():
                flush_lead()
            else:
                lead_lines.append(line)
            continue

        if not line.strip():
            flush_paragraph(paragraph_lines, out, mode)
            flush_list(list_kind, list_items, out, mode)
            list_kind = None
            flush_quotes()
            continue

        if re.match(r"^\s*---+\s*$", line):
            flush_paragraph(paragraph_lines, out, mode)
            flush_list(list_kind, list_items, out, mode)
            list_kind = None
            flush_quotes()
            out.append(f'<hr style="{STYLES["hr"]}" />')
            continue

        lead_match = re.match(r"^\s*导读\s*[:：]\s*(.*)$", line)
        if lead_match:
            flush_paragraph(paragraph_lines, out, mode)
            flush_list(list_kind, list_items, out, mode)
            list_kind = None
            flush_quotes()
            first_line = lead_match.group(1).strip()
            if first_line:
                out.append(lead_block(first_line, mode))
            else:
                lead_lines = []
            continue

        quote_match = re.match(r"^\s*>\s?(.*)$", line)
        if quote_match:
            flush_paragraph(paragraph_lines, out, mode)
            flush_list(list_kind, list_items, out, mode)
            list_kind = None
            quote_lines.append(quote_match.group(1))
            continue

        heading_match = re.match(r"^\s*(#{1,6})\s+(.+)$", line)
        if heading_match:
            flush_paragraph(paragraph_lines, out, mode)
            flush_list(list_kind, list_items, out, mode)
            list_kind = None
            flush_quotes()
            out.append(heading(len(heading_match.group(1)), heading_match.group(2), mode))
            continue

        ul_match = re.match(r"^\s*[-*]\s+(.+)$", line)
        ol_match = re.match(r"^\s*\d+[.)、]\s+(.+)$", line)
        if ul_match or ol_match:
            flush_paragraph(paragraph_lines, out, mode)
            flush_quotes()
            kind = "ul" if ul_match else "ol"
            if list_kind and list_kind != kind:
                flush_list(list_kind, list_items, out, mode)
            list_kind = kind
            list_items.append((ul_match or ol_match).group(1).strip())
            continue

        flush_list(list_kind, list_items, out, mode)
        list_kind = None
        flush_quotes()
        paragraph_lines.append(line)

    if in_code:
        out.append(code_block("\n".join(code_lines)))
    flush_table()
    flush_lead()
    flush_paragraph(paragraph_lines, out, mode)
    flush_list(list_kind, list_items, out, mode)
    flush_quotes()
    return "\n".join(out) + "\n"


class SemanticHTMLParser(HTMLParser):
    BLOCK_TAGS = {"p", "div", "section", "article", "li", "blockquote", "pre", "code", "h1", "h2", "h3", "h4", "h5", "h6", "br", "hr", "tr"}

    def __init__(self, mode: str) -> None:
        super().__init__(convert_charrefs=True)
        self.mode = mode
        self.parts: list[str] = []
        self.skip_depth = 0
        self.link_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in {"script", "style", "head"}:
            self.skip_depth += 1
            return
        if self.skip_depth:
            return
        attr_map = {k: v or "" for k, v in attrs}
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")
            if tag == "hr":
                self.parts.append("\n---\n")
        if tag in {"strong", "b"}:
            self.parts.append("**")
        elif tag in {"em", "i"}:
            self.parts.append("*")
        elif tag == "a" and attr_map.get("href"):
            self.parts.append("[")
            self.link_stack.append(attr_map.get("href", ""))
        elif tag == "img":
            alt = attr_map.get("alt", "")
            src = attr_map.get("src", "")
            self.parts.append(f"![{alt}]({src})")
        elif re.fullmatch(r"h[1-6]", tag):
            self.parts.append("#" * min(int(tag[1]), 3) + " ")
        elif tag == "li":
            self.parts.append("- ")
        elif tag == "blockquote":
            self.parts.append("> ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style", "head"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth:
            return
        if tag in {"strong", "b"}:
            self.parts.append("**")
        elif tag in {"em", "i"}:
            self.parts.append("*")
        elif tag == "a":
            url = self.link_stack.pop() if self.link_stack else ""
            self.parts.append(f"]({url})")
        if tag in self.BLOCK_TAGS:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_depth:
            self.parts.append(data)

    def markdown(self) -> str:
        text = "".join(self.parts)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip() + "\n"


def parse_html(source: str, mode: str) -> str:
    parser = SemanticHTMLParser(mode)
    parser.feed(source)
    parser.close()
    return parse_markdown(parser.markdown(), mode)


def prepend_lead(output: str, lead: str, mode: str) -> str:
    if not lead.strip():
        return output
    return lead_block(lead, mode) + "\n" + output


def detect_format(path: Path | None, text: str, explicit: str) -> str:
    if explicit != "auto":
        return explicit
    if path:
        suffix = path.suffix.lower()
        if suffix in {".md", ".markdown"}:
            return "markdown"
        if suffix in {".html", ".htm"}:
            return "html"
        if suffix == ".txt":
            return "text"
    if re.search(r"<(?:html|body|p|div|h[1-6]|section|article|blockquote|ul|ol|li|pre|code|table|img|a)\b", text, re.I):
        return "html"
    if re.search(r"(^|\n)\s*#{1,6}\s+\S|```|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\)", text):
        return "markdown"
    return "text"


def default_output_path(input_path: Path | None) -> Path:
    if input_path:
        return input_path.with_suffix(".wechat.html")
    return Path("wechat_ready.html")


def main() -> int:
    parser = argparse.ArgumentParser(description="Convert article content to WeChat-ready HTML.")
    parser.add_argument("input", nargs="?", help="Input Markdown, HTML, or text file")
    parser.add_argument("--from-stdin", action="store_true", help="Read source content from stdin")
    parser.add_argument("--output", "-o", help="Output HTML file")
    parser.add_argument("--input-format", choices=["auto", "markdown", "html", "text"], default="auto")
    parser.add_argument("--mode", choices=["strict", "media"], default="strict")
    parser.add_argument("--lead", help="Add a lead/opening block at the top of the generated article")
    parser.add_argument("--no-auto-lead", action="store_true", help="Do not infer a lead block when none is provided")
    parser.add_argument("--accent-color", default=DEFAULT_ACCENT, help="Theme accent color as a 6-digit hex value")
    parser.add_argument("--lead-accent-color", help="Optional lead block accent color; defaults to --accent-color")
    args = parser.parse_args()

    try:
        apply_accent_color(args.accent_color, args.lead_accent_color)
    except ValueError as exc:
        parser.error(str(exc))

    input_path = Path(args.input) if args.input else None
    if args.from_stdin:
        source = sys.stdin.read()
    elif input_path:
        source = input_path.read_text(encoding="utf-8")
    else:
        parser.error("provide an input file or --from-stdin")

    input_format = detect_format(input_path, source, args.input_format)
    explicit_lead = args.lead.strip() if args.lead else ""
    auto_lead = ""
    if not explicit_lead and not args.no_auto_lead and not has_lead_marker(source):
        auto_lead = extract_auto_lead(source, input_format, args.mode)

    if input_format == "html":
        output = parse_html(source, args.mode)
    else:
        output = parse_markdown(source, args.mode)
    if explicit_lead or auto_lead:
        output = prepend_lead(output, explicit_lead or auto_lead, args.mode)

    output_path = Path(args.output) if args.output else default_output_path(input_path)
    output_path.write_text(output, encoding="utf-8")
    print(f"Wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
