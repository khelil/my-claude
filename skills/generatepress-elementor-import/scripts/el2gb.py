#!/usr/bin/env python3
"""Convert an Elementor page (_elementor_data) from a WXR export into a
gb_build.py JSON tree, restyled with the SYD GeneratePress design system.

Usage: el2gb.py <export.xml> <post_id>  > page.gb.json
Then:  gb_build.py page.gb.json -o page.html

Not a pixel-perfect Elementor clone — it extracts the content + layout
(sections, columns, headings, text, buttons, lists, dividers, icons, form)
and rebuilds it cleanly with our tokens (var(--accent), .btn-primary, etc.).
WPForms widgets are swapped for our Gravity Form (id 1).
"""
import sys, re, json

# --- Feather icons (stroke=currentColor) keyed by Elementor icon-class keyword ---
_F = {
    "money": '<line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>',
    "shield": '<path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>',
    "energy": '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>',
    "man": '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>',
    "sync": '<polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>',
    "cloud": '<path d="M18 10h-1.26A8 8 0 1 0 9 20h9a5 5 0 0 0 0-10z"/>',
    "briefcase": '<rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
    "badge": '<circle cx="12" cy="8" r="6"/><path d="M15.477 12.89 17 22l-5-3-5 3 1.523-9.11"/>',
    "database": '<ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3"/><path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5"/>',
    "headphones": '<path d="M3 18v-6a9 9 0 0 1 18 0v6"/><path d="M21 19a2 2 0 0 1-2 2h-1a2 2 0 0 1-2-2v-3a2 2 0 0 1 2-2h3zM3 19a2 2 0 0 0 2 2h1a2 2 0 0 0 2-2v-3a2 2 0 0 0-2-2H3z"/>',
    "server": '<rect x="2" y="2" width="20" height="8" rx="2"/><rect x="2" y="14" width="20" height="8" rx="2"/><line x1="6" y1="6" x2="6.01" y2="6"/><line x1="6" y1="18" x2="6.01" y2="18"/>',
    "cpu": '<rect x="4" y="4" width="16" height="16" rx="2"/><rect x="9" y="9" width="6" height="6"/><line x1="9" y1="1" x2="9" y2="4"/><line x1="15" y1="1" x2="15" y2="4"/><line x1="9" y1="20" x2="9" y2="23"/><line x1="15" y1="20" x2="15" y2="23"/><line x1="20" y1="9" x2="23" y2="9"/><line x1="20" y1="14" x2="23" y2="14"/><line x1="1" y1="9" x2="4" y2="9"/><line x1="1" y1="14" x2="4" y2="14"/>',
    "lock": '<rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/>',
    "rocket": '<path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 0 0-2.91-.09z"/><path d="M12 15l-3-3a22 22 0 0 1 2-3.95A12.88 12.88 0 0 1 22 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 0 1-4 2z"/>',
    "_default": '<polyline points="20 6 9 17 4 12"/>',
}
_PALETTE = ["#23A1D9", "#FF5860", "#1B7BAC", "#FEC10B", "#1CCCD0", "#FF9100"]

def feather(icon_class, color):
    key = "_default"
    for k in _F:
        if k != "_default" and k in (icon_class or "").lower():
            key = k; break
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 24 24" '
           'fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" '
           'stroke-linejoin="round">' + _F[key] + '</svg>')
    return {"type": "shape", "content": svg, "styles": {"color": color}}

def heading_tag(s):
    sz = s.get("header_size", "h2")
    return sz if sz in ("h1", "h2", "h3", "h4", "h5", "h6") else "p"

def text_of(html):
    return re.sub(r"<[^>]+>", " ", html or "").strip()

# running counters for variety
_icon_i = [0]

def conv_widget(w, ctx):
    s = w.get("settings", {}) or {}
    wt = w.get("widgetType", "")
    if wt == "heading":
        tag = heading_tag(s)
        title = s.get("title", "")
        st = {"marginTop": "0px", "marginBottom": "0px"}
        if tag in ("h2", "h3"):
            st["color"] = "var(--accent)"
        elif tag == "p":   # small bold label heading
            tag = "p"; st.update({"fontWeight": "700", "fontSize": "18px", "color": "var(--contrast)"})
        if ctx.get("hero"):
            st["color"] = "#ffffff"
        return {"type": "text", "tagName": tag, "content": title, "styles": st}
    if wt == "text-editor":
        st = {"marginTop": "0px", "marginBottom": "0px", "color": "var(--contrast-2)"}
        if ctx.get("hero"):
            st["color"] = "rgba(255,255,255,0.92)"
        return {"type": "text", "tagName": "div", "content": s.get("editor", ""), "styles": st}
    if wt == "button":
        link = ""
        lk = s.get("link")
        if isinstance(lk, dict):
            link = lk.get("url", "") or ""
        text = s.get("text", "")
        if not link:   # eyebrow / category badge
            return {"type": "text", "tagName": "span", "content": text,
                    "styles": {"display": "inline-block", "backgroundColor": "rgba(35,161,217,0.12)",
                               "color": "var(--accent)", "padding": "6px 14px", "borderRadius": "40px",
                               "fontWeight": "600", "fontSize": "13px", "textTransform": "uppercase",
                               "letterSpacing": "0.4px", "alignSelf": "flex-start"}}
        cls = "btn-dark" if ctx.get("hero") else "btn-primary"
        return {"type": "text", "tagName": "a", "content": text, "globalClasses": [cls],
                "htmlAttributes": {"href": link}, "styles": {"alignSelf": "flex-start"}}
    if wt == "icon-list":
        lis = []
        for i in s.get("icon_list", []) or []:
            lis.append({"type": "text", "tagName": "li", "content": i.get("text", ""), "styles": {}})
        return {"type": "element", "tagName": "ul",
                "styles": {"margin": "0px", "paddingLeft": "20px", "display": "flex",
                           "flexDirection": "column", "gap": "6px", "color": "var(--contrast-2)",
                           "li": {"listStyle": "disc"}},
                "innerBlocks": lis}
    if wt == "divider":
        return {"type": "element", "tagName": "div",
                "styles": {"height": "1px", "backgroundColor": "var(--base-3)", "margin": "6px 0"},
                "innerBlocks": []}
    if wt == "icon":
        sel = s.get("selected_icon", {})
        val = sel.get("value", "") if isinstance(sel, dict) else (sel or "")
        color = _PALETTE[_icon_i[0] % len(_PALETTE)]; _icon_i[0] += 1
        return feather(val, color)
    if wt == "wpforms":
        return {"type": "raw",
                "rawMarkup": '<!-- wp:shortcode -->\n[gravityform id="1" title="false" description="false" ajax="true"]\n<!-- /wp:shortcode -->'}
    return None

def conv_el(el, ctx):
    t = el.get("elType")
    if t == "widget":
        return conv_widget(el, ctx)
    if t == "section":      # nested section -> grid
        cols = el.get("elements", [])
        return grid(cols, ctx)
    if t == "column":
        return conv_column(el, ctx)
    return None

def conv_column(col, ctx):
    kids = [c for c in (conv_el(e, ctx) for e in col.get("elements", [])) if c]
    st = {"display": "flex", "flexDirection": "column", "gap": "14px", "minWidth": "0"}
    return {"type": "element", "tagName": "div", "styles": st, "innerBlocks": kids}

def grid(cols, ctx):
    n = max(1, len(cols))
    st = {"display": "grid", "gridTemplateColumns": "repeat(%d, 1fr)" % n, "gap": "26px"}
    if n >= 3:
        st["@media (max-width:1024px)"] = {"gridTemplateColumns": "repeat(2, 1fr)"}
    st["@media (max-width:767px)"] = {"gridTemplateColumns": "1fr"}
    return {"type": "element", "tagName": "div", "styles": st,
            "innerBlocks": [conv_column(c, ctx) for c in cols]}

def section_has_h1(sec):
    return '"header_size":"h1"' in json.dumps(sec) or '"widgetType":"heading"' in json.dumps(sec) and '"title"' in json.dumps(sec) and _h1(sec)

def _h1(el):
    if el.get("elType") == "widget" and el.get("widgetType") == "heading" and el.get("settings", {}).get("header_size") == "h1":
        return True
    return any(_h1(c) for c in el.get("elements", []))

def conv_top_section(sec, idx):
    is_hero = _h1(sec)
    ctx = {"hero": is_hero}
    cols = sec.get("elements", [])
    inner = grid(cols, ctx)
    if is_hero:
        sec_styles = {
            "backgroundImage": "linear-gradient(110deg, #145B80 0%, #1B7BAC 55%, #23A1D9 100%)",
            "paddingTop": "64px", "paddingBottom": "64px", "paddingLeft": "20px", "paddingRight": "20px",
        }
    else:
        bg = "var(--base-2)" if idx % 2 == 1 else "var(--base)"
        sec_styles = {"backgroundColor": bg, "paddingLeft": "20px", "paddingRight": "20px"}
    container = {"type": "element", "tagName": "div",
                 "styles": {"maxWidth": "var(--gb-container-width)", "marginLeft": "auto", "marginRight": "auto"},
                 "innerBlocks": [inner]}
    node = {"type": "element", "tagName": "section", "styles": sec_styles, "innerBlocks": [container]}
    if not is_hero:
        node["globalClasses"] = ["section"]
    return node

def main():
    xml = open(sys.argv[1], encoding="utf-8", errors="replace").read()
    pid = sys.argv[2]
    items = re.findall(r"<item>.*?</item>", xml, re.S)
    target = None
    for it in items:
        m = re.search(r"<wp:post_id>(\d+)</wp:post_id>", it)
        if m and m.group(1) == pid:
            target = it; break
    if not target:
        sys.exit("post %s not found" % pid)
    m = re.search(r"<wp:meta_key><!\[CDATA\[_elementor_data\]\]></wp:meta_key>\s*<wp:meta_value><!\[CDATA\[(.*?)\]\]></wp:meta_value>", target, re.S)
    data = json.loads(m.group(1))
    tree = [conv_top_section(sec, i) for i, sec in enumerate(data)]
    json.dump(tree, sys.stdout, ensure_ascii=False)

if __name__ == "__main__":
    main()
