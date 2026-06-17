#!/usr/bin/env python3
"""
gb_build.py — Compile a clean block tree into valid GenerateBlocks 2.x markup.

Why this exists
---------------
In GenerateBlocks 2.x the front end is styled ONLY by the precomputed `css`
attribute stored inside each block delimiter (see GB source
includes/blocks/class-block.php::get_css -> `$attributes['css']`). The `styles`
object alone drives the *editor*; if you paste markup whose `css` is missing or
inconsistent, the page renders UNSTYLED. On top of that, WordPress forbids `--`
inside HTML comments, so every `--` in the delimiter JSON (notably CSS custom
properties like var(--accent)) must be written as `\\u002d\\u002d`.

Getting both of those right by hand, for every block, every time, is busywork
that invites bugs. Describe the page as a small JSON tree and let this script
emit copy-paste-ready markup with the css compiled, the uniqueId kept in sync
between the JSON and the inner-HTML class, and the escaping handled.

Usage
-----
    python3 gb_build.py page.json            # read a file
    cat page.json | python3 gb_build.py      # or stdin
    python3 gb_build.py page.json -o out.html

The JSON is either a single node or a list of nodes (a list = a stack of
top-level sections). Node shape (all keys optional except `type`):

    {
      "type": "element",            # element|text|media|shape|looper|loop-item|query|raw
      "tagName": "section",         # defaults per type (element->div, text->p, media->img)
      "styles": { ... },            # camelCase CSS; nested selectors & @media supported (see below)
      "globalClasses": ["card"],    # global style classes added to the element
      "htmlAttributes": {"id":"hero","data-x":"y"},  # extra HTML attrs (media: src/alt live here)
      "attrs": { ... },             # extra raw block attributes (query params, mediaId, linkHtmlAttributes...)
      "content": "Heading text",    # text/shape inner content (HTML allowed)
      "innerBlocks": [ ... ],       # children (recursive)
      "rawMarkup": "<!-- wp:... -->"# type=raw: emitted verbatim (use for core blocks, p5, reusable, etc.)
    }

Styles object
-------------
  - Plain properties are camelCase strings: {"backgroundColor":"var(--base-2)","paddingTop":"80px"}
  - Nested selector: any key holding an object. "&" is the block root.
        "&:hover": {"backgroundColor":"var(--accent)"}   -> .gb-...:hover{...}
        "& a":     {"color":"var(--accent)"}             -> .gb-... a{...}
        "a":       {"color":"..."}                       -> .gb-... a{...}   (bare = descendant)
  - Responsive: a key beginning with "@media". Default GB breakpoints:
        "@media (max-width:1024px)" (tablet), "@media (max-width:767px)" (mobile)
        "@media (max-width:767px)": {"flexDirection":"column","& a":{...}}
"""

import json
import re
import sys
import uuid

# Block name + inner-HTML class behavior. element is special: it carries ONLY
# the id class (gb-element-<id>) with no base class. Every other block uses the
# pattern "gb-<x> gb-<x>-<id>".
BLOCKS = {
    "element":   {"name": "generateblocks/element",   "base": None,           "default_tag": "div", "void": False},
    "text":      {"name": "generateblocks/text",      "base": "gb-text",      "default_tag": "p",   "void": False},
    "media":     {"name": "generateblocks/media",     "base": "gb-media",     "default_tag": "img", "void": True},
    "shape":     {"name": "generateblocks/shape",     "base": "gb-shape",     "default_tag": "span","void": False},
    "looper":    {"name": "generateblocks/looper",    "base": "gb-looper",    "default_tag": "div", "void": False},
    "loop-item": {"name": "generateblocks/loop-item", "base": "gb-loop-item", "default_tag": "div", "void": False},
    "query":     {"name": "generateblocks/query",     "base": "gb-query",     "default_tag": "div", "void": False},
}


def camel_to_kebab(prop):
    # backgroundColor -> background-color ; also leaves --custom-prop and aria-* alone
    if prop.startswith("--"):
        return prop
    return re.sub(r"([A-Z])", lambda m: "-" + m.group(1).lower(), prop)


def props_to_css(props):
    return "".join(f"{camel_to_kebab(k)}:{v};" for k, v in props.items())


def selector_for(root, key):
    key = key.strip()
    if "&" in key:
        return key.replace("&", root)
    if key.startswith(":") or key.startswith("::"):
        return root + key            # pseudo-class/element appended directly
    return root + " " + key          # bare key = descendant selector


def is_media(key):
    return key.strip().startswith("@media") or key.strip().startswith("@container")


def compile_css(root, styles):
    """Turn a styles object into a CSS string scoped to `root`."""
    main = []          # list of (selector, props)
    media = {}         # media_query -> list of (selector, props)

    def walk(sel, node, mq):
        own = {}
        for k, v in node.items():
            if isinstance(v, dict):
                if is_media(k):
                    walk(sel, v, k)          # rules inside this block go under media query k
                else:
                    walk(selector_for(sel, k), v, mq)
            else:
                own[k] = v
        if own:
            if mq:
                media.setdefault(mq, []).append((sel, own))
            else:
                main.append((sel, own))

    walk(root, styles, None)

    css = "".join(f"{sel}{{{props_to_css(props)}}}" for sel, props in main)
    for mq, rules in media.items():
        inner = "".join(f"{sel}{{{props_to_css(props)}}}" for sel, props in rules)
        css += f"{mq}{{{inner}}}"
    return css


def esc_attr(v):
    return str(v).replace("&", "&amp;").replace('"', "&quot;")


def build_class_list(btype, uid, styles, global_classes):
    cfg = BLOCKS[btype]
    classes = []
    if cfg["base"] is None:                       # element
        if styles:
            classes.append(f"gb-element-{uid}")
    else:
        classes.append(cfg["base"])
        if styles:
            classes.append(f"{cfg['base']}-{uid}")
    classes.extend(global_classes or [])
    return classes


def open_tag(tag, classes, html_attributes, void=False):
    attrs = ""
    extra = dict(html_attributes or {})
    # allow htmlAttributes.class to merge with computed classes
    if "class" in extra:
        classes = classes + extra.pop("class").split()
    if classes:
        attrs += f' class="{esc_attr(" ".join(classes))}"'
    for k, v in extra.items():
        attrs += f' {k}="{esc_attr(v)}"'
    return f"<{tag}{attrs}{' /' if void else ''}>"


def serialize(node, indent=0):
    btype = node["type"]

    if btype == "raw":
        return node.get("rawMarkup", "")

    if btype not in BLOCKS:
        raise ValueError(f"Unknown block type: {btype!r}")

    cfg = BLOCKS[btype]
    uid = node.get("uniqueId") or uuid.uuid4().hex[:8]
    tag = node.get("tagName") or cfg["default_tag"]
    styles = node.get("styles") or {}
    global_classes = node.get("globalClasses") or []
    html_attributes = node.get("htmlAttributes") or {}

    # --- block delimiter attributes ---
    attrs = {"uniqueId": uid, "tagName": tag, "styles": styles}
    if styles:
        attrs["css"] = compile_css(f".gb-{btype}-{uid}" if cfg["base"] else f".gb-element-{uid}", styles)
    if global_classes:
        attrs["globalClasses"] = global_classes
    if html_attributes:
        attrs["htmlAttributes"] = html_attributes
    for k, v in (node.get("attrs") or {}).items():
        attrs[k] = v

    attr_json = json.dumps(attrs, separators=(",", ":"), ensure_ascii=False)
    # WordPress forbids "--" inside HTML comments; it stores them as -.
    attr_json = attr_json.replace("--", "\\u002d\\u002d")

    name = cfg["name"]
    classes = build_class_list(btype, uid, styles, global_classes)

    # --- inner HTML ---
    if cfg["void"]:                                  # media (img)
        inner_html = open_tag(tag, classes, html_attributes, void=True)
        link = (node.get("attrs") or {}).get("linkHtmlAttributes") or {}
        if link.get("href"):
            la = "".join(f' {k}="{esc_attr(v)}"' for k, v in link.items())
            inner_html = f"<a{la}>{inner_html}</a>"
        body = inner_html
    else:
        content = node.get("content", "")
        children = node.get("innerBlocks") or []
        if children:
            child_markup = "\n\n".join(serialize(c) for c in children)
            body = f"{open_tag(tag, classes, html_attributes)}\n{content}\n{child_markup}\n</{tag}>"
        else:
            body = f"{open_tag(tag, classes, html_attributes)}{content}</{tag}>"

    return f"<!-- wp:{name} {attr_json} -->\n{body}\n<!-- /wp:{name} -->"


def main():
    args = [a for a in sys.argv[1:]]
    out_path = None
    if "-o" in args:
        i = args.index("-o")
        out_path = args[i + 1]
        del args[i:i + 2]

    raw = open(args[0]).read() if args else sys.stdin.read()
    data = json.loads(raw)
    nodes = data if isinstance(data, list) else [data]
    markup = "\n\n".join(serialize(n) for n in nodes)

    if out_path:
        with open(out_path, "w") as f:
            f.write(markup + "\n")
        print(f"Wrote {out_path}")
    else:
        sys.stdout.write(markup + "\n")


if __name__ == "__main__":
    main()
