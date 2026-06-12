# WeChat Formatter Style System

Use these styles when manually writing or modifying generated WeChat HTML.

## Shared Font

```css
font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif;
```

## Paragraph

```css
font-size: 16px; color: #3f3f3f; line-height: 1.8; letter-spacing: 0.5px; margin: 0 0 20px 0; text-align: justify; text-justify: inter-ideograph;
```

## Level-One Title

Use for Markdown `#`.

```css
font-size: 17.6px; font-weight: bold; color: #077ba9; line-height: 1.45; margin: 42px 0 28px 0; text-align: left; letter-spacing: 1px;
```

## Section Title

Use for Markdown `##`.

```css
font-size: 17px; font-weight: bold; color: #077ba9; line-height: 1.4; margin: 32px 0 16px 0; padding-left: 12px; border-left: 4px solid #077ba9; letter-spacing: 1px;
```

## Subsection Title

Use for Markdown `###` and deeper headings.

```css
font-size: 16px; font-weight: bold; color: #077ba9; line-height: 1.4; margin: 24px 0 12px 0; letter-spacing: 1px;
```

## Lead Opening

Use for `导读：...` at the beginning of an article, or when the formatter is called with `--lead`. The visual pattern is an accent-color `导读` label, a short accent-color underline directly beneath it, body-size gray lead text, then a thin bottom divider. Keep the label and underline color coordinated with the article theme; the formatter supports `--accent-color` and optional `--lead-accent-color`. When writing HTML manually, replace `<accent-color>` with a concrete hex color such as `#077ba9`.

Outer `<section>`:

```css
font-family: -apple-system, BlinkMacSystemFont, 'Helvetica Neue', 'PingFang SC', 'Microsoft YaHei', sans-serif; margin: 0 0 32px 0; padding: 0;
```

Label `<p>`:

```css
font-size: 17.6px; font-weight: bold; color: <accent-color>; line-height: 1.4; letter-spacing: 1px; margin: 0;
```

Underline `<hr>`:

```css
width: 58px; border: none; border-top: 3px solid <accent-color>; margin: 4px 0 18px 0;
```

Lead paragraph `<p>`:

```css
font-size: 16px; color: #8b8b8b; line-height: 1.8; letter-spacing: 0.5px; margin: 0 0 32px 0; text-align: justify; text-justify: inter-ideograph;
```

Bottom divider `<hr>`:

```css
border: none; border-top: 1px solid #d8d8d8; margin: 0;
```

## Strong

```css
font-weight: bold; color: #077ba9;
```

## Emphasis

```css
font-style: italic; color: #555555;
```

## Quote Block

Outer `<section>`:

```css
margin: 24px 0; padding: 16px 20px; background-color: #f7f7f7; border-left: 4px solid #077ba9; border-radius: 0 8px 8px 0;
```

Quote paragraph:

```css
font-size: 15px; color: #555555; line-height: 1.8; margin: 0; text-align: justify; text-justify: inter-ideograph;
```

Attribution paragraph:

```css
font-style: normal; font-size: 14px; color: #888888; line-height: 1.7; margin: 8px 0 0 0; text-align: right;
```

## Unordered List

`<ul>`:

```css
padding-left: 2em; margin: 0 0 20px 0;
```

`<li>`:

```css
font-size: 16px; color: #3f3f3f; line-height: 1.8; margin-bottom: 8px; list-style: disc; text-align: justify; text-justify: inter-ideograph;
```

## Ordered List

`<ol>`:

```css
list-style: none; padding: 0; margin: 0 0 24px 0; counter-reset: item;
```

`<li>`:

```css
background-color: #f8f9fa; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px; font-size: 15px; color: #3f3f3f; line-height: 1.7; list-style: none; text-align: justify; text-justify: inter-ideograph;
```

Leading number `<span>`:

```css
display: inline-block; width: 24px; height: 24px; background-color: #077ba9; color: #ffffff; border-radius: 50%; font-size: 13px; line-height: 24px; text-align: center; margin-right: 12px;
```

## Inline Code

```css
font-family: Consolas, Monaco, 'Courier New', monospace; font-size: 14px; color: #e83e8c; background-color: #f5f5f5; padding: 2px 6px; border-radius: 4px;
```

## Code Block

Use only whitelist tags in strict mode. Do not include HTML comments in final output.

```html
<section style="margin: 18px 0 24px 0; background-color: #1E1E1E; border-radius: 12px; box-shadow: 0 12px 24px rgba(0,0,0,0.22); overflow: hidden; font-family: 'SF Mono', Monaco, Consolas, 'Ubuntu Mono', monospace;">
  <section style="height: 36px; padding-left: 14px; background-color: #1E1E1E; line-height: 36px;">
    <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #FF5F56; margin-right: 8px;"></span>
    <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #FFBD2E; margin-right: 8px;"></span>
    <span style="display: inline-block; width: 12px; height: 12px; border-radius: 50%; background-color: #27C93F;"></span>
  </section>
  <p style="margin: 0; padding: 0 18px 18px 18px; overflow-x: auto; white-space: pre; background-color: #1E1E1E; font-size: 14px; line-height: 1.5; color: #D4D4D4;"><span style="font-family: 'SF Mono', Monaco, Consolas, 'Ubuntu Mono', monospace;">escaped code</span></p>
</section>
```

## Table Card

Tables are rendered as card-style layouts. Each data row becomes a card showing header-value pairs.

Outer `<section>`:

```css
margin: 20px 0;
```

Table header `<p>` (shows column names joined by " / "):

```css
font-size: 15px; font-weight: bold; color: #077ba9; margin: 0 0 10px 0; letter-spacing: 0.5px;
```

Card `<section>` (each data row):

```css
background-color: #f8f9fa; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;
```

Card item `<p>` (each header-value pair):

```css
font-size: 15px; color: #3f3f3f; line-height: 1.7; margin: 4px 0; text-align: justify; text-justify: inter-ideograph;
```

Example output:

```html
<section style="margin: 20px 0;">
  <p style="font-size: 15px; font-weight: bold; color: #077ba9; margin: 0 0 10px 0;">姓名 / 年龄 / 城市</p>
  <section style="background-color: #f8f9fa; border-radius: 8px; padding: 14px 18px; margin-bottom: 10px;">
    <p style="font-size: 15px; color: #3f3f3f; line-height: 1.7; margin: 4px 0;"><strong style="font-weight: bold; color: #077ba9;">姓名</strong>：Alice</p>
    <p style="font-size: 15px; color: #3f3f3f; line-height: 1.7; margin: 4px 0;"><strong style="font-weight: bold; color: #077ba9;">年龄</strong>：25</p>
    <p style="font-size: 15px; color: #3f3f3f; line-height: 1.7; margin: 4px 0;"><strong style="font-weight: bold; color: #077ba9;">城市</strong>：北京</p>
  </section>
</section>
```

## Horizontal Rule

```css
border: none; border-top: 1px solid #ebebeb; margin: 2em 0;
```

## Media Mode

Link:

```css
color: #077ba9; text-decoration: none; border-bottom: 1px solid #077ba9;
```

Image:

```css
display: block; max-width: 100%; height: auto; margin: 20px auto; border-radius: 8px;
```
