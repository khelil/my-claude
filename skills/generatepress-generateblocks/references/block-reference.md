# GenerateBlocks 2.x — Block & Markup Reference

This is the technical ground truth for generating valid GenerateBlocks 2.x
markup. It targets **GenerateBlocks 2.x** (the unified `element`/`text`/`media`
architecture) and **GenerateBlocks Pro 2.x**. It does **not** describe the
legacy 1.x blocks (Container / Grid / Headline / Button-Container) — those no
longer exist in 2.x, yet most web tutorials still show them. Ignore that advice.

## The one rule that breaks everything if you get it wrong

The front end is styled **only** by the precomputed `css` attribute inside each
block delimiter — not by the `styles` object. (GB source: `class-block.php`
returns `$attributes['css']` for front-end CSS.) The `styles` object exists for
the editor. So:

- Markup with `styles` but no/incorrect `css` → **renders unstyled** on the live page.
- The CSS selector must be `.gb-<block>-<uniqueId>` and the **same uniqueId**
  must appear in the inner-HTML `class`.

Compiling that by hand for every block is exactly what `scripts/gb_build.py`
exists to do. **Prefer the script.** Only hand-write markup for tiny tweaks, and
when you do, obey the rules below.

Second rule: WordPress forbids `--` inside HTML comments. Every `--` in the
delimiter JSON — above all CSS custom properties like `var(--accent)` — must be
written as `--`. The script handles this; by hand you must too.

## Block delimiter anatomy

```
<!-- wp:generateblocks/element {"uniqueId":"a1b2c3d4","tagName":"section","styles":{...},"css":".gb-element-a1b2c3d4{...}"} -->
<section class="gb-element-a1b2c3d4">…inner blocks…</section>
<!-- /wp:generateblocks/element -->
```

Common attributes on every GB block: `uniqueId` (8 hex chars), `tagName`,
`styles` (object), `css` (string, when styled), `globalClasses` (array),
`htmlAttributes` (object).

### Inner-HTML class pattern (verified against real exports)

| Block       | Class when styled                | Notes |
|-------------|----------------------------------|-------|
| `element`   | `gb-element-<id>`                | **No base class.** Plain `<tag>` if unstyled. |
| `text`      | `gb-text gb-text-<id>`           | base + id |
| `media`     | `gb-media gb-media-<id>`         | base + id; `<img>` void element |
| `shape`     | `gb-shape gb-shape-<id>`         | inner HTML is the SVG |
| `looper`    | `gb-looper gb-looper-<id>`       | base + id |
| `loop-item` | `gb-loop-item gb-loop-item-<id>` | base + id |
| `query`     | `gb-query gb-query-<id>`         | base + id |

`globalClasses` are appended to the class list: `class="gb-element-<id> card hover-lift"`.

## Core blocks

**element** — the layout primitive (replaces Container *and* Grid; build grids
with `display:grid`/`flex` in `styles`). `tagName`: div, section, article,
aside, header, footer, nav, main, figure, a, ul, ol, li, dl, dt, dd. Holds inner blocks.

**text** — all text (replaces Headline *and* Buttons; a button is a `text`
block with `tagName:"a"` styled as a button). `tagName`: p, span, div, h1–h6, a,
button, figcaption, li. The visible text is the inner HTML content.

**media** — a responsive `<img>` (only valid `tagName` is `img`). `src`, `alt`,
`loading`, etc. live in `htmlAttributes`; `mediaId` (attachment ID) and an
optional `linkHtmlAttributes` (to wrap the image in `<a>`) go in block attrs.

**shape** — inline SVG (dividers, icons, blobs). The SVG markup is the content.

**looper / loop-item / query / query-no-results / query-page-numbers** —
dynamic content. `query` runs a WP_Query and provides context; `looper` iterates;
`loop-item` is the repeated template; the others handle empty states and
pagination. Inside a loop, fill text/media with **dynamic tags** (see below).
For anything data-driven, hand-building is fragile — generate the structure with
the script and bind dynamic data in the editor, or read GB's dynamic-tags docs.

## Pro blocks (interactive)

`generateblocks-pro/{tabs, accordion, carousel, navigation, site-header, menu-*}`.
These ship JS and have required parent/child structures (e.g. `tabs` →
`tabs-menu` → `tab-menu-item` + `tab-items` → `tab-item`).

**Accordion and Tabs ARE reliably hand-authorable** (as a `raw` node or pasted
markup) — they're dynamic blocks that preserve your saved classes and enqueue
their JS by block name. Full verified, paste-ready recipes (structure, classes,
open-state attrs, the show/hide-CSS gotcha for tabs, a11y/keyboard contract) live
in **`references/accordion-tabs.md`** — read it before building either. The
accordion is self-sufficient (base CSS handles show/hide); tabs need you to ship
the panel show/hide CSS yourself. Carousel/Navigation/site-header are heavier and
still safer from the inserter unless you have a tested snippet.

The **required nesting** for all of them (block names, verified against GB Pro
2.5.x `dist/blocks/*/block.json`) is:

- **Tabs:** `tabs` → `tabs-menu` → `tab-menu-item`… + `tab-items` → `tab-item`…
  (a `tab-menu-item` and its `tab-item` share `"tabItemOpen":true` for the active tab).
- **Accordion:** `accordion` → `accordion-item` (`"openByDefault":bool`) →
  { `accordion-toggle` → `accordion-toggle-icon` } + `accordion-content`.
- **Carousel:** `carousel` → `carousel-items` → `carousel-item`… plus
  `carousel-control` and `carousel-pagination` (descendants of `carousel`).
- **Navigation:** `navigation` (`"subMenuType":"hover"|"click"`) → `site-header` →
  { `menu-toggle`, `menu-container` → `classic-menu` (`"menu":"<menu-id>"`) →
  `classic-menu-item` / `classic-sub-menu` }. `site-header` becomes sticky when its
  `htmlAttributes` include `data-gb-is-sticky`.

Each level serializes like a core GB block (`<!-- wp:generateblocks-pro/<name> {…} -->`
… `<!-- /wp:generateblocks-pro/<name> -->`) and the children carry the interactive
state. Still prefer the inserter unless you have a tested snippet — the JS depends
on exact attribute wiring the editor produces.

**Overlays are NOT a block.** Mega-menus, modals, and popups in GB Pro are
**Overlay Panels** — a `gblocks_overlay` **post** (content = ordinary GB blocks,
behavior = `_gb_overlay_*` post meta), opened by any element with
`data-gb-overlay="gb-overlay-<id>"`. They can be built end-to-end without the
editor. See `references/overlays.md`.

## The `styles` object

camelCase CSS properties. Three kinds of keys:

```jsonc
{
  "backgroundColor": "var(--base-2)",        // plain property
  "paddingTop": "80px",
  "&:hover":   { "backgroundColor": "var(--accent)" },  // nested selector, & = block root
  "& a":       { "color": "var(--accent)" },            // descendant via &
  "a":         { "color": "var(--accent)" },            // bare key also = descendant
  "@media (max-width:767px)": {                          // responsive
     "flexDirection": "column",
     "paddingTop": "40px"
  }
}
```

**GenerateBlocks default breakpoints** (use these exact strings so they line up
with the editor's Tablet/Mobile toggles):
- Tablet: `@media (max-width:1024px)`
- Mobile: `@media (max-width:767px)`

Compiled CSS scopes plain props to `.gb-<block>-<id>{…}`, nested-selector props
to the resolved selector, and responsive props inside the media query. Values
support `var(--…)`, `calc()`, gradients, `clamp()`, etc.

## Using the build script

`scripts/gb_build.py` turns a JSON block tree into paste-ready markup. Node shape:

```jsonc
{
  "type": "element",              // element|text|media|shape|looper|loop-item|query|raw
  "tagName": "section",           // optional; sensible default per type
  "styles": { ... },
  "globalClasses": ["card"],      // optional
  "htmlAttributes": {"id":"hero","src":"…","alt":"…","href":"…"},  // optional
  "attrs": {"mediaId": 42, "linkHtmlAttributes": {"href":"/x"}},   // optional raw block attrs
  "content": "Visible text or inline HTML",   // text/shape
  "innerBlocks": [ ... ],         // children (recursive)
  "rawMarkup": "<!-- wp:… -->"    // type:"raw" → emitted verbatim
}
```

Run it:
```bash
python3 scripts/gb_build.py page.json            # → stdout
python3 scripts/gb_build.py page.json -o out.html
cat page.json | python3 scripts/gb_build.py      # stdin
```

Pass a JSON **array** for a stack of top-level sections (a full page).

**`type:"raw"`** drops in any markup verbatim — use it to embed core blocks
(`wp:heading`, `wp:image`, `wp:columns`), the Easy p5.js block, reusable blocks,
shortcodes, or a Pro interactive block you have a verified snippet for.

## How the user applies the output

The output is post/page content. Two reliable paths:

1. **Code editor (per page):** In the block editor, ⋮ (Options) → **Code editor**
   (or `⌘⇧Alt+M`), paste the markup, then switch back to Visual editor. Reopening
   in Visual editor lets GB re-validate. Save.
2. **As a reusable pattern:** paste into a page, select all, convert to a
   synced/unsynced pattern for reuse.

After pasting, the page renders styled immediately **because** the `css` is
already in the markup. If the user later edits a block in the visual editor, GB
recomputes `css` — that's fine and expected.

## Quick hand-written sanity checklist

If you ever hand-write instead of using the script, verify every block:
- [ ] `uniqueId` in the JSON == the id in the inner-HTML class
- [ ] `css` present and scoped to `.gb-<block>-<id>` whenever `styles` is non-empty
- [ ] every `--` in the delimiter JSON written as `--`
- [ ] `tagName` is in that block's allowed list
- [ ] element uses `gb-element-<id>` (no base class); others use `gb-x gb-x-<id>`
