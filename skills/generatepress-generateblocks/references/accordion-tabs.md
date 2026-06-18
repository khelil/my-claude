# GenerateBlocks Pro — Accordion & Tabs (hand-authorable recipes)

Docs: <https://learn.generatepress.com/blocks/block/accordion/> ·
<https://learn.generatepress.com/blocks/block/tabs/>

The block-reference says "prefer the inserter." That's the safe default, but the
Accordion **can** be reliably hand-authored / generated, and the Tabs can too if
you ship the panel show/hide CSS yourself. Both recipes below were **confirmed working on a live GB Pro 2.5.x site**
(accordion via the Elementor import; tabs via a throwaway test page — clicking a
tab switched the visible panel and moved `gb-block-is-current`/`aria-selected`),
after reverse-engineering `dist/blocks/*/block.json`, the render classes in
`includes/blocks/{accordion,tabs}/`, and the front-end `dist/accordion.js` /
`dist/tabs.js` + `dist/accordion-style.css`.

## Why these are hand-authorable

These are **dynamic blocks**: their `render_block()` takes the *saved inner
markup* and only (a) injects the per-block `css` attribute as a `<style>`,
(b) enqueues the block's JS/CSS bundle, and (c) augments a few attributes via
`WP_HTML_Tag_Processor` (e.g. adds `tabindex`/`role` to a `div` toggle, adds the
"open" state class). It does **not** rebuild the markup from attributes. So:

- **The classes you write in the saved markup are preserved** (including extra
  classes like a `syd-faq` brand hook — `supports.className` is `false`, so add
  classes directly to the element, not via a `className` attr).
- **The block name in the delimiter is what triggers the JS/CSS enqueue.** Use
  the exact names (`generateblocks-pro/accordion`, …) or the interactivity script
  never loads and nothing toggles.
- `do_blocks()` renders regardless of editor validation, so compiled markup works
  even if the editor would later show "this block contains unexpected content."
  (Opening the page in the editor may offer block recovery — harmless for the
  front end.)

Emit these as a **`type:"raw"` node** in a `gb_build` tree (or paste into the
Code editor). They are *not* node types the compiler understands natively.

---

## Accordion

Base stylesheet `dist/accordion-style.css` **fully drives show/hide** off the
structural classes, so no per-instance `css` is required — author structural
classes + correct nesting and it just works.

### Structure & contract
```
.gb-accordion                      generateblocks-pro/accordion        (wrapper)
  └ .gb-accordion__item            generateblocks-pro/accordion-item
      ├ .gb-accordion__toggle      generateblocks-pro/accordion-toggle (clickable)
      │   └ .gb-accordion__toggle-icon
      │       ├ .gb-accordion__toggle-icon-open    (shown when closed)
      │       └ .gb-accordion__toggle-icon-close   (shown when open)
      └ .gb-accordion__content     generateblocks-pro/accordion-content
```
- **Open state** = class `gb-accordion__item-open` on the *item* + `gb-block-is-current`
  on the *toggle*. `accordion.js` toggles these on click/Enter/Space (event-delegated).
- **Start open:** give the item `gb-accordion__item-open` and set block attr
  `"openByDefault":true` (the item render also adds the class from that attr).
- **Single-open (default):** the wrapper has **no** `data-accordion-multiple-open`.
  Add `data-accordion-multiple-open` (any value, even empty) to allow multiple open.
- **Animation:** add `data-transition="slide"` or `"fade"` on the wrapper or item
  (omit for instant). Base CSS: `.gb-accordion__content{max-height:0;overflow:hidden;
  visibility:hidden}` → `.gb-accordion__item-open>.gb-accordion__content` expands.
- **a11y:** `accordion.js` wires `aria-expanded` (toggle), `aria-controls`/
  `aria-labelledby` from `id`s if present. A `div` toggle gets `tabindex=0`+`role=button`
  from PHP; a `button` toggle is already focusable.

### Paste-ready example (verified rendering live)
Brand styling goes in one `wp:html` `<style>` scoped under a wrapper class
(`syd-faq` here) so you don't need per-block `css`. `--` inside a `<style>` is
fine — it's only forbidden inside the `<!-- wp: … -->` *comment* delimiters
(none of these contain `--`).
```html
<!-- wp:html -->
<style>
.syd-faq{display:flex;flex-direction:column;gap:12px}
.syd-faq .gb-accordion__item{border:1px solid var(--base-3,#e3e7ea);border-radius:10px;background:#fff;overflow:hidden}
.syd-faq .gb-accordion__toggle{display:flex;align-items:center;justify-content:space-between;gap:16px;padding:18px 22px;font-weight:600;color:var(--contrast,#1b1b1b);font-size:17px;line-height:1.4}
.syd-faq .gb-accordion__toggle:hover{color:var(--accent,#23A1D9)}
.syd-faq .gb-accordion__content>div{padding:0 22px 20px;color:var(--contrast-2,#555)}
.syd-faq .gb-accordion__toggle-icon{color:var(--accent,#23A1D9);flex-shrink:0;display:inline-flex}
.syd-faq .gb-accordion__toggle-icon svg{width:22px;height:22px}
</style>
<!-- /wp:html -->

<!-- wp:generateblocks-pro/accordion {"uniqueId":"acc00001","tagName":"div"} -->
<div class="gb-accordion syd-faq">
  <!-- wp:generateblocks-pro/accordion-item {"uniqueId":"itm00001","tagName":"div"} -->
  <div class="gb-accordion__item">
    <!-- wp:generateblocks-pro/accordion-toggle {"uniqueId":"tgl00001","tagName":"div"} -->
    <div class="gb-accordion__toggle"><span>Question one?</span>
      <!-- wp:generateblocks-pro/accordion-toggle-icon {"uniqueId":"ico00001","tagName":"span"} -->
      <span class="gb-accordion__toggle-icon">
        <span class="gb-accordion__toggle-icon-open"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="6 9 12 15 18 9"/></svg></span>
        <span class="gb-accordion__toggle-icon-close"><svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="18 15 12 9 6 15"/></svg></span>
      </span>
      <!-- /wp:generateblocks-pro/accordion-toggle-icon -->
    </div>
    <!-- /wp:generateblocks-pro/accordion-toggle -->
    <!-- wp:generateblocks-pro/accordion-content {"uniqueId":"cnt00001","tagName":"div"} -->
    <div class="gb-accordion__content"><div><p>Answer HTML for item one.</p></div></div>
    <!-- /wp:generateblocks-pro/accordion-content -->
  </div>
  <!-- /wp:generateblocks-pro/accordion-item -->
  <!-- repeat accordion-item per Q&A, with fresh uniqueIds -->
</div>
<!-- /wp:generateblocks-pro/accordion -->
```

---

## Tabs

Same dynamic-block model, **but** the base stylesheet only ships the *editor*
hide rule (`.gb-tabs__item:not(.is-selected):not(.has-child-selected):not([data-tab-is-open]){display:none}`).
On the front end the active panel is marked with class `gb-tabs__item-open`, and
there is **no base rule that shows it** — that CSS is normally generated per
instance by the editor into the block's `css` attribute. So when you hand-author
tabs, **ship the panel show/hide CSS yourself** (one `<style>`), or nothing
appears to switch.

### Structure & contract
```
.gb-tabs                 generateblocks-pro/tabs        (wrapper; JS sets data-opened-tab)
  ├ .gb-tabs__menu       generateblocks-pro/tabs-menu   (the tab nav; flex-direction governs orientation)
  │   └ .gb-tabs__menu-item   generateblocks-pro/tab-menu-item   (one per tab; "tabItemOpen":true on active)
  └ .gb-tabs__items      generateblocks-pro/tab-items   (the panels container)
      └ .gb-tabs__item   generateblocks-pro/tab-item    (one panel; "tabItemOpen":true on active)
```
- **Positional pairing:** `tabs.js` matches a menu item to its panel by **index**
  (the Nth `.gb-tabs__menu-item` controls the Nth `.gb-tabs__item`). Keep counts equal
  and ordered.
- **Active tab:** set `"tabItemOpen":true` on **both** the active `tab-menu-item`
  *and* its `tab-item`. PHP then adds `gb-block-is-current` to the menu item and
  `gb-tabs__item-open` to the panel. Exactly one of each should start open.
- **a11y/keyboard:** `tabs.js` wires `role`/`tabindex` (div menu items get
  `role=button`,`tabindex`), `aria-selected`, `aria-controls`/`aria-labelledby`
  (from `id`s), `aria-orientation` (from the menu's `flex-direction`), and arrow/
  Home/End key navigation. URL `#<panel-id>` deep-links to a tab.
- The alt class pair `.gb-tabs__buttons` / `.gb-tabs__button` is also recognized
  by the JS (button-style tabs); `.gb-tabs__menu` / `.gb-tabs__menu-item` is the default.

### Paste-ready example (ship the show/hide CSS!)
```html
<!-- wp:html -->
<style>
.syd-tabs .gb-tabs__menu{display:flex;gap:8px;flex-wrap:wrap;border-bottom:2px solid var(--base-3,#e3e7ea);margin-bottom:20px}
.syd-tabs .gb-tabs__menu-item{cursor:pointer;padding:12px 18px;font-weight:600;color:var(--contrast-2,#555);border-bottom:2px solid transparent;margin-bottom:-2px}
.syd-tabs .gb-tabs__menu-item.gb-block-is-current{color:var(--accent,#23A1D9);border-bottom-color:var(--accent,#23A1D9)}
.syd-tabs .gb-tabs__items>.gb-tabs__item{display:none}
.syd-tabs .gb-tabs__items>.gb-tabs__item.gb-tabs__item-open{display:block}
</style>
<!-- /wp:html -->

<!-- wp:generateblocks-pro/tabs {"uniqueId":"tab00001","tagName":"div"} -->
<div class="gb-tabs syd-tabs">
  <!-- wp:generateblocks-pro/tabs-menu {"uniqueId":"tmn00001","tagName":"div"} -->
  <div class="gb-tabs__menu">
    <!-- wp:generateblocks-pro/tab-menu-item {"uniqueId":"tmi00001","tagName":"div","tabItemOpen":true} -->
    <div class="gb-tabs__menu-item gb-block-is-current">Tab one</div>
    <!-- /wp:generateblocks-pro/tab-menu-item -->
    <!-- wp:generateblocks-pro/tab-menu-item {"uniqueId":"tmi00002","tagName":"div"} -->
    <div class="gb-tabs__menu-item">Tab two</div>
    <!-- /wp:generateblocks-pro/tab-menu-item -->
  </div>
  <!-- /wp:generateblocks-pro/tabs-menu -->
  <!-- wp:generateblocks-pro/tab-items {"uniqueId":"tis00001","tagName":"div"} -->
  <div class="gb-tabs__items">
    <!-- wp:generateblocks-pro/tab-item {"uniqueId":"tit00001","tagName":"div","tabItemOpen":true} -->
    <div class="gb-tabs__item gb-tabs__item-open"><p>Panel one content.</p></div>
    <!-- /wp:generateblocks-pro/tab-item -->
    <!-- wp:generateblocks-pro/tab-item {"uniqueId":"tit00002","tagName":"div"} -->
    <div class="gb-tabs__item"><p>Panel two content.</p></div>
    <!-- /wp:generateblocks-pro/tab-item -->
  </div>
  <!-- /wp:generateblocks-pro/tab-items -->
</div>
<!-- /wp:generateblocks-pro/tabs -->
```

---

## Shared gotchas
- **Use exact block names** — they gate the JS/CSS enqueue and the render-time
  attribute augmentation. A typo = inert markup.
- **uniqueId** should be present and unique per block (used for any per-block `css`
  scoping). Any short stable string works when hand-authoring.
- **Add structural classes directly in the markup** (`supports.className:false`).
  Extra brand classes on the wrapper are preserved and are the cleanest styling hook.
- **Accordion = self-sufficient** (base CSS shows/hides). **Tabs = bring your own
  panel show/hide CSS** (base only hides in the editor).
- Put brand/show-hide CSS once in a sibling `wp:html` `<style>`; `var(--accent)` &
  other `--` tokens are safe there (the `--`-in-comments rule applies only to the
  `<!-- wp: … -->` delimiters).
- The Elementor importer (`generatepress-elementor-import` skill) maps Elementor
  `accordion`/`toggle` widgets to the accordion recipe above via a `raw` node — see
  its `el2gb.py` `gb_accordion()` for a generator.
