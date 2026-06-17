# GenerateBlocks Pro — Overlay Panels (mega-menus, modals, popups)

**Use a GenerateBlocks Pro Overlay for every mega-menu, modal dialog, and popup.**
Don't hand-roll show/hide JS, CSS `display:none` toggles, or `<dialog>` for these —
GB Pro's Overlay Panels give you the trigger wiring, backdrop, blur, scroll-lock,
focus/ARIA, ESC + click-outside close, and animations for free. This reference is
the ground truth for building one without the editor (verified against GB Pro 2.5.x).

> Requires **GenerateBlocks Pro** with the **Overlays** feature enabled
> (`generateblocks_pro_overlays_enabled()` must return true; it's on by default).

## What an overlay actually is

An overlay is **not a block** — it's a **post** of type `gblocks_overlay`
("Overlay Panels"). Its `post_content` is ordinary GenerateBlocks markup (your
panel), and its behavior is configured by `_gb_overlay_*` **post meta**. On every
front-end request `generateblocks_pro_do_overlays()` (hooked to `wp`) outputs each
active overlay — `standard` overlays render into `wp_footer`, hidden
(`aria-hidden="true"`) until a trigger opens them.

So building one = **create a `gblocks_overlay` post + set meta + wire a trigger**,
analogous to a GP Premium Element but for modal/popup/mega-menu UI.

## The rendered wrapper (what GB Pro emits around your content)

```html
<div id="gb-overlay-<post_id>"
     class="gb-overlay gb-overlay--standard gb-overlay--top-center"   <!-- type + position/width classes -->
     data-gb-overlay
     data-gb-overlay-type="standard"
     data-gb-overlay-trigger-type="click"
     data-gb-overlay-position="top-center"
     data-gb-overlay-disable-page-scroll="true"
     role="dialog" aria-modal="true" aria-hidden="true">
  <div class="gb-overlay__backdrop" style="background-color:…;backdrop-filter:blur(24px);"></div>
  <div class="gb-overlay__content">
    …your GenerateBlocks panel markup (the post_content)…
  </div>
</div>
```

You only author the **content** (the panel). GB Pro wraps it with the backdrop +
content div and the data-attributes derived from meta.

## Open / close contract (this is the whole interaction model)

- **Open:** any element on the page with `data-gb-overlay="gb-overlay-<post_id>"`
  opens that overlay on click. (Frontend JS does
  `querySelectorAll('[data-gb-overlay="<the overlay's id>"]')`.) The trigger can
  live anywhere — a header hamburger, a button in content, etc.
- **Close:** any element **inside** the overlay with the bare attribute
  `data-gb-overlay-close` closes it on click. Plus **ESC** (`close_on_esc`) and
  **click on the backdrop** (`close_on_click_outside`) — both on by default.
- When open: `aria-hidden` flips to `false` and (if `disable_page_scroll`) the
  body gets `overflow:hidden`.

## Overlay types (`_gb_overlay_type`)

| Type | Use it for | Notes |
|------|-----------|-------|
| `standard` | **modals, popups, and full-screen / hamburger mega-menus** | Fixed, full-viewport backdrop. Positioned via `_gb_overlay_position`. This is the default and the one you'll use most. |
| `anchored` | dropdowns anchored to a trigger element | Uses `_gb_overlay_placement` (e.g. `bottom-start`) + `_gb_overlay_position_to_parent` (a CSS selector). |
| `mega-menu` | a mega-menu attached to a **nav menu item** | Treated as `anchored`; rendered via a `gb-mega-menu-<id>` action and `.menu-item-has-gb-mega-menu` wiring. For a hamburger-triggered panel (not a menu item), use **`standard`** instead. |

## Meta keys & defaults (`_gb_overlay_*`)

Set only what differs from the default — `get_overlay_meta()` returns the default
when a meta is missing or an empty string.

| Meta | Default | Values / notes |
|------|---------|----------------|
| `_gb_overlay_type` | `standard` | `standard` \| `anchored` \| `mega-menu` |
| `_gb_overlay_trigger_type` | `click` | `click` \| `hover` \| `both` \| `exit-intent` \| `scroll` \| `time` \| `custom` |
| `_gb_overlay_position` | `center` | **standard only**, whitelisted: `center, top-left, top-center, top-right, center-left, center-right, bottom-left, bottom-center, bottom-right`. ⚠️ **`top`/`bottom`/`left`/`right` are NOT valid** — they silently reset to `center`. Top-anchored panel → `top-center`. |
| `_gb_overlay_width_mode` | `''` | `''` (content width) \| `full` (edge-to-edge → adds `gb-overlay--width-full`) |
| `_gb_overlay_backdrop` | `true` | show the backdrop layer |
| `_gb_overlay_backdrop_color` | `rgba(0, 0, 0, 0.5)` | any CSS color |
| `_gb_overlay_backdrop_blur` | `''` | number of px (e.g. `24`) → blurs the page behind |
| `_gb_overlay_close_on_esc` | `true` | standard only |
| `_gb_overlay_close_on_click_outside` | `true` | standard only |
| `_gb_overlay_disable_page_scroll` | `false` | lock body scroll while open (set `true` for modals/mega-menus) |
| `_gb_overlay_animation_in` / `_out` / `_duration` / `_target` / `_distance` | `''` | optional entrance/exit animation |
| `_gb_overlay_placement` | `bottom-start` | anchored only |
| `_gb_overlay_position_to_parent` | `''` | anchored only — CSS selector of the anchor |
| `_gb_overlay_trigger_type=custom` → `_gb_overlay_custom_event` | `''` | JS event name that opens it |
| `_gb_overlay_scroll_percent` / `_time_delay` / `_cookie_duration` | `''` | for scroll/time/exit-intent triggers |
| `_gb_overlay_hover_buffer` | `20` | hover trigger grace area (px) |
| `_gb_overlay_hide_if_cookies_disabled` | `false` | |
| `_gb_overlay_display_condition` | `''` | **empty = show site-wide.** Otherwise the **post ID of a GB condition post** (its `_gb_conditions` meta drives where it shows) — not a condition string. |
| `_gb_overlay_display_condition_invert` | `false` | |

**Boolean meta storage:** `get_overlay_meta()` reads booleans as `'1' === $value`.
`update_post_meta($id, $key, true)` stores `'1'` (→ true); `false` stores `''`
(→ false). Set booleans as real PHP bools.

## Build recipe (end-to-end, no editor)

1. **Author the panel** as a JSON block tree and compile with `gb_build.py`
   (`element`/`text`/`media`/`shape` — the panel root is a normal `element`; give
   it an `htmlAttributes.id` so you can target it). Put `data-gb-overlay-close` in
   `htmlAttributes` on your close button/group.
2. **Create the overlay post** and set meta, then **clear the cache**:
   ```bash
   OID=$(wp post create panel.html --post_type=gblocks_overlay \
         --post_title="Megamenu principal" --post_name="megamenu-principal" \
         --post_status=publish --porcelain)
   wp eval '
     update_post_meta('"$OID"', "_gb_overlay_type", "standard");
     update_post_meta('"$OID"', "_gb_overlay_trigger_type", "click");
     update_post_meta('"$OID"', "_gb_overlay_position", "top-center");
     update_post_meta('"$OID"', "_gb_overlay_backdrop_blur", "24");
     update_post_meta('"$OID"', "_gb_overlay_backdrop_color", "rgba(40,44,47,0.35)");
     update_post_meta('"$OID"', "_gb_overlay_disable_page_scroll", true);
     delete_option("generateblocks_active_overlays");  // ⚠️ REQUIRED — see gotcha
   '
   # the overlay DOM id is now gb-overlay-$OID
   ```
3. **Wire the trigger** — give the opener `data-gb-overlay="gb-overlay-<OID>"`.
   - If the opener is a block you author, add it via that block's `htmlAttributes`.
   - If the opener lives in an existing GP Element / header you don't want to edit
     in the DB (avoids editor block-invalidation), add it **at render** with a
     child-theme filter targeting the block's `uniqueId`:
     ```php
     add_filter( 'render_block_generateblocks/text', function ( $html, $block ) {
         if ( ( $block['attrs']['uniqueId'] ?? '' ) !== 'db6a1fd9' ) return $html;       // the hamburger
         $ids = get_posts([ 'post_type'=>'gblocks_overlay','name'=>'megamenu-principal',
                            'post_status'=>'publish','numberposts'=>1,'fields'=>'ids' ]);
         if ( ! $ids ) return $html;
         return preg_replace( '/<a\b/',
             '<a data-gb-overlay="gb-overlay-'.(int)$ids[0].'" aria-haspopup="dialog"', $html, 1 );
     }, 10, 2 );
     ```
     Resolve the overlay by **slug**, not a hard-coded numeric ID, so it survives
     a re-create.
4. **Verify on the front end** (overlays only run on the front end, not in the
   editor): trigger exists, `#gb-overlay-<id>` exists with `aria-hidden="true"`,
   click the trigger → `aria-hidden="false"` + body `overflow:hidden`, then test
   close via the close button, ESC, and backdrop click.

## Gotchas (learned the hard way)

1. **Clear the active-overlays cache.** GB Pro caches the active overlay list in
   the option `generateblocks_active_overlays`. A newly created/edited overlay
   won't appear until you `delete_option('generateblocks_active_overlays')`.
2. **`position` is whitelisted** (see table) — `top` resets to `center`; use
   `top-center`.
3. **Overlays don't render in the block editor** — only on the front end (output
   on `wp_footer`/`wp`). Verify there, not in the editor canvas.
4. **`display_condition` is a post ID, not a string.** Leave it empty for
   site-wide; otherwise point it at a GB condition post.
5. Editing the overlay content later: it's a normal post — edit in
   **wp-admin → Overlay Panels**, or `wp post update <id> panel.html` after
   re-compiling.
