---
name: wechat-formatter
description: "Convert Markdown, HTML, or plain text into WeChat Official Account-ready HTML with inline styles and validation. Use when the user asks for 微信排版, 公众号推文, 微信公众号样式, 推文格式化, 公众号文章排版, wechat format, or when they paste article content and ask to format, generate HTML, or make it ready for WeChat."
---

# wechat-formatter

Convert user-provided article content into a WeChat Official Account HTML fragment that can be pasted into the editor.

## Core Rules

- Output an HTML fragment only: no `<!DOCTYPE>`, `<html>`, `<head>`, or `<body>`.
- Put every visual rule in inline `style` attributes.
- Do not use `<style>`, `class`, or external stylesheets.
- Default to strict mode, which allows only: `<section>`, `<p>`, `<span>`, `<strong>`, `<em>`, `<ul>`, `<ol>`, `<li>`, `<br>`, `<hr>`.
- Use media mode only when the user explicitly wants images or live links preserved. Media mode additionally allows `<img>` and `<a>`.
- Do not set fixed content widths such as `width: 600px` or `max-width: 600px`. Font size, margin, padding, borders, and icon dimensions may use px.
- Body-like text should use justified alignment with `text-align: justify; text-justify: inter-ideograph;`. Do not justify headings, labels, code blocks, or attribution lines.
- Heading text must use the article accent color, default `#077ba9`, unless the user explicitly requests another theme color. Level-one headings from Markdown `#` should use 17.6px size, bold weight, left alignment, and generous vertical spacing.
- Escape user text before placing it into HTML.
- Do not include HTML comments in final output.

For exact visual styles and element patterns, read `references/style-system.md` only when you need to manually inspect or modify the design system.

## Preferred Workflow

1. Read the user's file or pasted content.
2. Run the formatter script whenever possible:

   ```bash
   python3 scripts/format_wechat.py input.md
   ```

   Useful options:

   ```bash
   python3 scripts/format_wechat.py input.md --output wechat_ready.html --accent-color "#077ba9"
   python3 scripts/format_wechat.py input.html --input-format html --mode media
   python3 scripts/format_wechat.py input.md --lead "一句话导读内容"
   python3 scripts/format_wechat.py input.md --no-auto-lead
   python3 scripts/format_wechat.py input.md --accent-color "#077ba9"
   python3 scripts/format_wechat.py --from-stdin --output wechat_ready.html
   ```

3. Run validation on the generated file:

   ```bash
   python3 scripts/validate_wechat_html.py wechat_ready.html
   ```

   Use `--mode media` if the output intentionally contains `<img>` or `<a>`.

4. If the user did not opt out of leads, confirm the output contains the `导读` lead block. If validation fails or the lead block is missing, fix the HTML or update the source and rerun the formatter.
5. Tell the user where the generated HTML was written and mention any intentional degradations, such as table-to-list conversion or link text expansion.

## Input Handling

- Markdown: support headings, bold, italic, inline code, fenced code blocks, ordered and unordered lists, blockquotes, horizontal rules, links, and images.
- Lead opening: when the source contains `导读：...` near the beginning, render it as a WeChat opening block with no top margin, an accent-colored `导读` label, a short accent `<hr>` underline directly beneath it, body-size gray lead text, and a bottom divider. Do not bold the lead paragraph.
- If the source does not contain a lead opening and the user has not asked to omit it, include a lead block. Prefer writing a concise agent-generated lead with `--lead`; if no `--lead` is passed, the formatter script will automatically add a basic lead from the first substantial paragraph, then fall back to the title, then to a generic lead. Use `--no-auto-lead` only when the user explicitly does not want a lead.
- Keep lead opening colors coordinated with the whole article. Use `--accent-color` for the article theme color; use `--lead-accent-color` only when the lead needs a separate but compatible accent.
- HTML: clean scripts, styles, classes, document wrappers, and unsupported tags; preserve semantic content where possible.
- Plain text: infer headings from leading `#`, lists from `-`, `*`, or numbered lines, quotes from `>`, and paragraphs from blank-line separation.
- Tables are rendered as card-style layouts: each data row becomes a card with header-value pairs. See `references/style-system.md` for the Table Card pattern.
- In strict mode, links become `text（链接：URL）`; images become `[图片：alt 或 URL]`.
- In media mode, preserve links and images as styled `<a>` and `<img>` when safe URLs are present.

## Output Naming

- If the user gives an explicit output path, use it.
- Otherwise write `wechat_ready.html` in the current working directory.
- If overwriting an existing article would be surprising, prefer `<input-basename>.wechat.html`.

## Manual Fallback

If script execution is unavailable, manually produce HTML using the same rules:

- Convert `#`/`##`/`###` headings into styled `<p>` elements, not `<h1>`-`<h6>`.
- Convert `导读：...` into the lead opening pattern from `references/style-system.md`.
- If no lead exists, create a concise lead paragraph from the article's substance before formatting, unless the user explicitly asks for no lead.
- Convert quotes into a styled `<section>` containing `<p>` children.
- Convert tables into card-style layouts from `references/style-system.md`, where each data row becomes a `<section>` card with header-value pairs.
- Convert code blocks into the Mac-window code block pattern from `references/style-system.md`.
- Convert inline code into styled `<span>`.
- Convert ordered lists into `<ol>` with styled `<li>` and a leading number `<span>`.
- Validate mentally against the checklist in `scripts/validate_wechat_html.py`.

Always prefer deterministic script output plus validation over hand-written HTML for non-trivial articles.
