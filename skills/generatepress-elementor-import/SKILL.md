---
name: generatepress-elementor-import
description: |
  Import and convert Elementor pages into GeneratePress + GenerateBlocks 2.x. Use this whenever migrating an Elementor-built page or site to GeneratePress, importing a WordPress WXR/XML export whose pages were built with Elementor, or turning `_elementor_data` into native GenerateBlocks blocks. It parses the Elementor tree (sections → columns → widgets), rebuilds it with the project's GeneratePress design system, publishes the page via WP-CLI, then drives Playwright to screenshot, verify, and refine the result. Pairs with the `generatepress-generateblocks` skill (for the gb_build.py compiler and GP knowledge).
---

# Elementor → GeneratePress import

Convert Elementor pages into **clean, native GenerateBlocks 2.x** — content + layout
faithful, restyled with the target site's design tokens. Not a pixel-perfect Elementor
clone: it extracts the real content (headings, text, buttons, lists, dividers, icons,
forms) and the column/section structure, and rebuilds it with `element`/`text`/`media`/
`shape` blocks so the result is editable, lightweight, and on-brand.

This skill **depends on the `generatepress-generateblocks` skill** — invoke it (Skill
tool) to load `scripts/gb_build.py` (the block-tree → markup compiler) and the GP design
guidance. This skill adds the Elementor *parser* (`scripts/el2gb.py`) and the
import + verify workflow on top.

## Prerequisites

- WordPress with **GeneratePress + GenerateBlocks 2.x** active (GB Pro optional). The
  target site should already have its global colors/typography set (see the
  `generatepress-generateblocks` skill) so converted blocks inherit the brand via
  `var(--accent)` etc.
- **WP-CLI** access to the site. On Local by WP Engine, run via the site's env (set
  `WP_CLI_CONFIG_PATH`, `PHPRC`, `PATH` from the site's `ssh-entry` script).
- The Elementor source as a **WXR/XML export** (`_elementor_data` lives in postmeta).
- **Playwright** (MCP browser tools) for the verify/refine pass against the live URL.

## Workflow

### 1. Inventory the export
Find the pages and which are Elementor. From the WXR XML:
```bash
grep -oE "<wp:post_type><!\[CDATA\[[^]]*\]\]></wp:post_type>" export.xml | sort | uniq -c
```
Then list page items (id, title, slug, status, whether `_elementor_data` is present).
Confirm with the user *which* pages to import if it's not all of them.

### 2. Convert each page: Elementor tree → gb_build JSON
`scripts/el2gb.py` parses one page's `_elementor_data` and emits a `gb_build` block
tree restyled with the design system:
```bash
python3 scripts/el2gb.py <export.xml> <post_id> > page.gb.json
```
It maps (see **Widget mapping** below), detects the hero (the section containing an
`h1`) and gives it a gradient band, alternates section backgrounds, and swaps the
**WPForms** widget for a site form shortcode. Edit `page.gb.json` for any page-specific
tweaks before compiling.

### 3. Compile to GenerateBlocks markup
Use the **`generatepress-generateblocks`** skill's compiler (invoke that skill to get its
base dir; `<gpgb>` below is that path):
```bash
python3 <gpgb>/scripts/gb_build.py page.gb.json -o page.html
```
This produces paste-ready markup with the precomputed `css` inside each delimiter and
all `--` escaped. Sanity check: `grep -oE "<!-- wp:[^>]*--[^>]*-->" page.html | grep -v u002d | wc -l` must be `0`.

### 4. Publish via WP-CLI
Create or update the page from the compiled file, and apply the full-width layout meta
GeneratePress uses for landing pages:
```bash
PID=$(wp post create page.html --post_type=page --post_status=publish \
      --post_title="<Title>" --post_name="<slug>" --porcelain)
wp post meta update "$PID" _generate-full-width-content true
wp post meta update "$PID" _generate-sidebar-layout-meta no-sidebar
wp post meta update "$PID" _generate-disable-headline true   # hero supplies the title
```
(Re-running: look up the page by slug and `wp post update <id> page.html` instead.)

### 5. Verify & refine with Playwright
Load the published URL, **scroll the whole page first** (lazy-loaded images don't decode
in a full-page screenshot until scrolled into view), then screenshot full-page and read
it back. Refine by editing `page.gb.json` → recompile → `wp post update` → re-screenshot.
Things to check and typically fix:
- **Hero text overlapping a background graphic** → cap the hero text column `maxWidth`.
- **Forms**: the WPForms→site-form swap rendered the right form; style its button/inputs
  to brand (often needs `!important` to beat a form plugin's own theme).
- **Icons**: Elementor icon fonts become feather equivalents — confirm they read sensibly
  per card; extend the `_F` map in `el2gb.py` for better matches.
- **Unmapped widgets** (see Limitations) leave gaps — add a mapping or hand-author that block.
- **Responsive**: resize to ~390px; every grid should collapse cleanly (the converter sets
  mobile/tablet breakpoints, but verify).

## Widget mapping (`el2gb.py`)

| Elementor | → GeneratePress / GenerateBlocks |
|---|---|
| `section` (top-level) | full-width `element` `section`; H1-bearing → gradient hero, others alternate `var(--base)`/`var(--base-2)`, `.section` class + 1080 container |
| `section` (nested) / `column` | `element` grid (`repeat(N,1fr)`, responsive → 2 then 1 col) |
| `heading` | `text` h1–h6 (h2/h3 → `var(--accent)`; `header_size:p` → bold label) |
| `text-editor` | `text` `div` with the inner HTML preserved (`var(--contrast-2)`) |
| `button` (with link) | `text` `a` + `.btn-primary` (`.btn-dark` in hero) |
| `button` (no link) | pill **badge** (eyebrow / category label) |
| `icon-list` | `ul` → `li` items |
| `divider` | thin rule `element` |
| `icon` | inline **feather** SVG (`shape`), keyword-matched, brand-palette colored |
| `wpforms` | site form shortcode (default `[gravityform id="1" …]` — adjust per site) |

## Methodology & gotchas (carry these in)

- **`_elementor_data` is the source of truth**, not `content:encoded` (which is only the
  rendered text/shortcodes). Parse the JSON tree.
- The live page is styled **only** by the `css` attribute the compiler emits — never hand-
  edit `styles` without recompiling. WordPress forbids `--` in HTML comments; `gb_build.py`
  escapes it. Don't bypass the compiler.
- **`gp_elements` and page content render through `do_blocks()`** regardless of editor
  validation, so hand-authored/compiled markup renders fine even if not byte-perfect.
- **Project-specific values** in `el2gb.py` to review per site: the form-swap shortcode
  (`wpforms` branch) and any absolute image URLs. The form id and brand palette
  (`_PALETTE`) are the usual edits.
- **Full-page screenshots miss lazy images** — scroll top→bottom in the browser before
  capturing, or check `img.complete`/`naturalWidth` via `browser_evaluate`.
- Keep the per-page `*.gb.json` and compiled `*.html` as version-controlled build sources
  (e.g. under the child theme's `build/`), so a page can be regenerated deterministically.

## Limitations / extension points

- **Accordion / toggle / tabs** Elementor widgets aren't mapped — only nearby headings
  render. Add cases in `conv_widget()` (map to GB Pro accordion/tabs, or a static
  `<details>`). 
- **Stat / counter** widgets render as plain text — add a `counter`/`number` case for the
  large-number styling.
- **Images/galleries**: `el2gb.py` focuses on text/layout; for `image` widgets add a
  `media` node (import the asset first with `wp media import` and pass the attachment id).
- Elementor per-widget colors/spacing are intentionally dropped in favor of the target
  design system; re-add specific overrides in the emitted `styles` if a page needs them.

## Bundled files
- `scripts/el2gb.py` — the Elementor `_elementor_data` → `gb_build` JSON converter.
- Compiler lives in the **`generatepress-generateblocks`** skill (`scripts/gb_build.py`).
