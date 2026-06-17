---
name: generatepress-generateblocks
description: >-
  Expert at building stunning WordPress websites with GeneratePress and
  GenerateBlocks 2.x (+ GenerateBlocks Pro / GP Premium). Use this whenever the
  user wants to design or build a WordPress page, section, layout, hero, landing
  page, pricing/feature grid, CTA, header/footer, or component on a GeneratePress
  or GenerateBlocks site — including generating paste-ready block markup,
  improving an existing GB layout, making something responsive, or applying a
  design system. Trigger on mentions of GeneratePress, GenerateBlocks, GP
  Premium, "gb-element", or building/restyling WordPress pages with blocks, even
  if the user doesn't name the plugins explicitly. Also use for GeneratePress
  child-theme PHP/hooks and Customizer/global-style guidance.
---

# GeneratePress + GenerateBlocks expert

Build WordPress sites that look like a senior designer made them, using
GeneratePress for the frame and GenerateBlocks 2.x for the content — and deliver
**valid, paste-ready block markup**, not vague instructions.

This skill assumes **GenerateBlocks 2.x** (the unified `element`/`text`/`media`
architecture). The old 1.x Container/Grid/Headline/Button blocks are gone; most
tutorials online still describe them — disregard that. When in doubt about the
installed version, check the plugin header (`generateblocks/plugin.php`).

## The two facts that make output actually work

1. **The live page is styled only by the precomputed `css` attribute** inside
   each block delimiter — not by the `styles` object (which is editor-only).
   Markup with `styles` but missing/incorrect `css` renders **unstyled**.
2. **WordPress forbids `--` inside HTML comments**, so every `--` in the
   delimiter JSON (especially `var(--accent)` and friends) must be written
   `--`.

Both are easy to get wrong by hand and tedious to get right. So:

> **Generate markup with `scripts/gb_build.py`.** Describe the page as a JSON
> block tree; the script generates uniqueIds, compiles each block's `styles`
> into correctly-scoped `css`, escapes `--`, and keeps the inner-HTML class in
> sync. Hand-write markup only for trivial tweaks.

## Workflow

When the user asks for a page, section, or component:

1. **Understand the brief and the brand.** What is it, who's it for, what's the
   one action you want visitors to take, what tone (calm/corporate vs
   bold/editorial vs playful)? If the look is wide open, make a tasteful
   decision and say what you chose — don't stall on questions for a homepage.

2. **Set the design system before building.** Decide the spacing scale, type
   scale, and how you'll use the GeneratePress palette variables
   (`var(--base)`, `--contrast`, `--accent`, …). Read `references/design-system.md`
   for the principles that separate "stunning" from "AI slop" (spacing
   discipline, sparing accent use, whitespace, asymmetry, restrained motion,
   accessibility). Prefer the theme's CSS variables over hardcoded hex/px —
   see `references/generatepress.md` for the variable names and container width.

3. **Plan the block structure**, then build it as a JSON tree for the script:
   - Full-width `element` (`tagName:"section"`) per section; inner content
     capped with `maxWidth:"var(--gb-container-width)"` + auto side margins.
   - Layout with `display:grid`/`flex` in `styles` (there is no Grid block in
     2.x — `element` does it all).
   - All text via `text` blocks (a button is a `text` block, `tagName:"a"`,
     styled as a button). Images via `media`. Inline SVG via `shape`.
   - Add the mobile breakpoint (`@media (max-width:767px)`) to anything that
     must stack or shrink — every layout must hold up on mobile.
   - Reuse via `globalClasses` instead of repeating big `styles` objects.
   - For dynamic post lists use `query`/`looper`/`loop-item`; for Pro
     interactivity (tabs/accordion/carousel) scaffold the surround and have the
     user drop the Pro block in (see reference).
   - **Mega-menus, modals, and popups → use a GenerateBlocks Pro Overlay**, not
     custom show/hide JS or CSS. An overlay is a `gblocks_overlay` post (content =
     GB blocks) opened by any element with `data-gb-overlay="gb-overlay-<id>"`.
     Read `references/overlays.md` for the full build recipe, meta, and gotchas.
   - Read `references/block-reference.md` for exact attributes, the `styles`
     object format (nested selectors `&:hover`/`& a`, breakpoints), tagName
     allow-lists, and the script's input schema.

4. **Generate and verify.**
   ```bash
   python3 scripts/gb_build.py page.json -o page.html
   ```
   Sanity-check the output: each `uniqueId` matches its inner-HTML class, `css`
   is present and scoped for every styled block, `--` is escaped, and the markup
   nesting is balanced.

5. **Hand it off.** Give the user the markup and tell them how to apply it: block
   editor → ⋮ → **Code editor** → paste → switch back to Visual editor → Save
   (or convert to a reusable pattern). It renders styled immediately because the
   `css` ships inside the markup. For site-wide chrome (header/footer/CTA on many
   pages), recommend a GP Premium **Element** instead of pasting per page.

## When it's not page markup

- **Global look (fonts, colors, container width):** that's the Customizer +
  GenerateBlocks Global Styles, not block markup — guide the user there
  (`references/generatepress.md`).
- **Dynamic templates (single post / CPT single / archive cards):** build a GP
  Premium **Content Template** Element with GeneratePress/GenerateBlocks **dynamic
  data** blocks (`generatepress/dynamic-content`, `generatepress/dynamic-image`,
  `generateblocks/headline` + `gpDynamicTextType`) and a `query`/`looper`/`loop-item`
  loop for related lists. A content-template **replaces the loop output** — no PHP,
  no `the_content` filter, no template file. Pair it with a **Layout Element** for
  full-width + to suppress the native title/featured. Read
  `references/elements-dynamic-data.md`.
- **Custom behavior / markup injection across the site:** child-theme
  `functions.php` with GeneratePress hooks (`generate_after_header`, etc.) or a
  GP Premium Element — patterns in `references/generatepress.md`. Never edit the
  GeneratePress parent theme. (For *dynamic post data*, prefer a Content Template
  Element over a hook — see above.)
- **Embedding other blocks** (core blocks, p5.js, shortcodes, reusable blocks):
  wrap them with the script's `type:"raw"` node so they sit inside your layout.
- **Mega-menu / modal / popup:** build it as a GenerateBlocks Pro **Overlay** (a
  `gblocks_overlay` post), not page markup. See `references/overlays.md`.

## Bundled resources

- `scripts/gb_build.py` — block tree (JSON) → valid GenerateBlocks 2.x markup.
  Compiles CSS, escapes `--`, syncs uniqueIds. **Use this to produce markup.**
- `references/block-reference.md` — exact block formats, `styles` object,
  class/escaping rules, script input schema, paste workflow. Read before
  hand-writing or using advanced blocks.
- `references/design-system.md` — the design judgment for "stunning": spacing &
  type scales, color discipline, composition, responsive, motion, a11y, and
  ready section patterns (hero, feature grid, CTA, stats, testimonial, footer).
- `references/generatepress.md` — GeneratePress global CSS variables, Customizer
  globals, GB Global Styles, child-theme hooks, GP Premium Elements, performance.
- `references/elements-dynamic-data.md` — GP Premium **Elements** in depth: the
  `gp_elements` meta model, **Content Templates** that replace the loop (single/
  archive design with no PHP), the GP/GB **dynamic-data blocks** and their exact
  attributes, the **query loop** shape, WP-CLI creation recipe, and gotchas. Read
  before building any single-post / CPT / archive template or anything that renders
  live post data.
- `references/overlays.md` — GenerateBlocks Pro **Overlay Panels** for mega-menus,
  modals, and popups: the `gblocks_overlay` CPT, `_gb_overlay_*` meta, the
  open/close (`data-gb-overlay` / `data-gb-overlay-close`) contract, trigger
  wiring, and gotchas. Read before building any mega-menu/modal/popup.
