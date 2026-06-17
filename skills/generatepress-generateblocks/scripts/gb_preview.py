#!/usr/bin/env python3
"""
gb_preview.py — Render GenerateBlocks 2.x markup into a standalone, viewable HTML
page so you can sanity-check a layout in a browser before handing it off.

GB markup can't be opened directly: it's WordPress block markup whose styling
lives in `css` attributes and relies on GeneratePress palette variables
(var(--accent), var(--gb-container-width), …) that only exist inside WordPress.
This script strips the wp:* comment delimiters (leaving the inner HTML),
collects every block's compiled `css`, and wraps it all in a full HTML document
with a stub :root palette so it renders close to how it will look live.

The preview is an approximation (fonts and exact palette come from the live
theme), but it's faithful enough to catch layout, spacing, hierarchy, and
responsive problems.

Usage:
    python3 gb_preview.py page.html                 # -> page.preview.html
    python3 gb_preview.py page.html -o preview.html
"""

import json
import re
import sys

# Stub palette + base styles approximating a clean GeneratePress install.
SHELL = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GenerateBlocks preview</title>
<style>
:root{{
  --base:#ffffff; --base-2:#f5f7fa; --base-3:#e4e8ee;
  --contrast:#15181d; --contrast-2:#3a3f47; --contrast-3:#6b7280;
  --accent:#2563eb; --accent-2:#7c3aed;
  --gb-container-width:1100px;
}}
*{{box-sizing:border-box;}}
body{{margin:0;font-family:system-ui,-apple-system,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
  color:var(--contrast);background:var(--base);line-height:1.6;}}
h1,h2,h3,h4,h5,h6{{line-height:1.15;margin:0;}}
p{{margin:0;}}
img{{max-width:100%;height:auto;display:block;}}
a{{color:inherit;text-decoration:none;}}
ul{{margin:0;padding:0;list-style:none;}}
/* ---- compiled block CSS ---- */
{css}
</style></head>
<body>
{html}
</body></html>
"""

DELIM = re.compile(r"<!--\s*/?wp:[^>]*?-->", re.DOTALL)
ATTR_JSON = re.compile(r"<!--\s*wp:[\w/-]+\s+(\{.*?\})\s*-->", re.DOTALL)


def main():
    args = sys.argv[1:]
    out = None
    if "-o" in args:
        i = args.index("-o")
        out = args[i + 1]
        del args[i:i + 2]
    if not args:
        sys.exit("usage: gb_preview.py <markup.html> [-o preview.html]")

    src_path = args[0]
    raw = open(src_path).read()

    # Collect every block's compiled css from the delimiter JSON.
    css_chunks = []
    for m in ATTR_JSON.finditer(raw):
        blob = m.group(1)
        try:
            attrs = json.loads(blob)          # json handles - -> '-'
        except json.JSONDecodeError:
            continue
        if isinstance(attrs, dict) and attrs.get("css"):
            css_chunks.append(attrs["css"])

    css = "\n".join(css_chunks)

    # Inner HTML = markup minus the wp:* comment delimiters.
    html = DELIM.sub("", raw).strip()

    doc = SHELL.format(css=css, html=html)
    out = out or re.sub(r"\.html?$", "", src_path) + ".preview.html"
    with open(out, "w") as f:
        f.write(doc)
    print(f"Wrote {out}  ({len(css_chunks)} block style rules)")


if __name__ == "__main__":
    main()
