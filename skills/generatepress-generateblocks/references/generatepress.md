# GeneratePress integration

GenerateBlocks builds the *content*; GeneratePress (free + GP Premium) controls
the *frame* (global colors, typography, header/footer, layout) and exposes the
CSS variables your block `styles` should lean on. Using the theme's own
variables — instead of hardcoded hex and px — is what makes a site feel coherent
and stay re-themable.

## Global CSS variables (use these in `styles`)

GeneratePress 3.x outputs a global color palette as CSS custom properties on the
front end. Reference them in block styles so the whole site shifts when the
palette changes:

| Variable           | Typical role                                  |
|--------------------|-----------------------------------------------|
| `var(--base)`      | Lightest base / page background               |
| `var(--base-2)`    | Slightly tinted background (alternating bands) |
| `var(--base-3)`    | Subtle borders / dividers / muted surfaces     |
| `var(--contrast)`  | Primary text / strongest foreground            |
| `var(--contrast-2)`| Secondary text                                 |
| `var(--contrast-3)`| Muted text / quiet surfaces                    |
| `var(--accent)`    | Brand accent — buttons, links, highlights      |
| `var(--accent-2)`  | Secondary accent (use sparingly)               |

(The exact set depends on the palette configured in **Appearance → Customize →
Colors → Global Color Palette**. These are the GeneratePress defaults; confirm
names in the live palette if a variable doesn't resolve.)

Layout width:
- `var(--gb-container-width)` — the GenerateBlocks content container width. Cap
  inner content with `maxWidth:"var(--gb-container-width)"` + `marginLeft/Right:"auto"`
  so it lines up with the theme's global content width.

Set the palette and global typography **once** in the Customizer, then build
everything against the variables. Don't scatter raw hex values through blocks —
that's what makes a site impossible to re-skin and visually inconsistent.

## Where global design decisions live

- **Colors:** Appearance → Customize → Colors (global palette + element colors).
- **Typography:** Appearance → Customize → Typography (font family, base size,
  heading sizes). Set the type scale here so it's consistent site-wide.
- **Layout / container width:** Appearance → Customize → Layout (content width,
  sidebar layout, header/footer).
- **GenerateBlocks Global Styles:** register reusable style classes (e.g. a
  `.btn-primary`, `.card`) once, then apply them via `globalClasses` on blocks.
  This is the GB equivalent of a component library — prefer it over repeating the
  same `styles` object on every button.

## Configuring globals programmatically (WP-CLI / no Customizer)

All theme settings live in **one WordPress option, `generate_settings`** (an
option, not a theme_mod). The Customizer is just a UI over it. For scripted setup:

- **Global colors** → `generate_settings['global_colors']`: an array of
  `{ name, slug, color }`. The `slug` is what becomes the `--<slug>` CSS variable.
  Stock slugs: `contrast`, `contrast-2`, `contrast-3`, `base`, `base-2`, `base-3`,
  `accent` (defaults `#222222`, `#575760`, `#b2b2be`, `#f0f0f0`, `#f7f8f9`,
  `#ffffff`, `#1e73be`). Define a brand palette here and every block `var(--slug)`
  + the Gutenberg editor palette follow.
- **Dynamic typography** (when `generate_settings['use_dynamic_typography']` is
  `true`, the default): `generate_settings['font_manager']` lists available fonts
  (`{ fontFamily, googleFont, googleFontCategory, googleFontVariants }`); 
  `generate_settings['typography']` is an array of rules, each assigning a font +
  responsive sizes to a selector (preset keys like `body`, `all-headings`,
  `buttons`, `primary-menu-items`, or `custom` + `customSelector`, with
  `fontSize`/`fontSizeTablet`/`fontSizeMobile`, `lineHeight`, `fontWeight`, …).
  Prefer hosting fonts locally via the GP Premium **Font Library** over `@import`.
- **Layout** keys (same option): `container_width` (default `1200`),
  `layout_setting`/`blog_layout_setting`/`single_layout_setting` (sidebar:
  `right-sidebar`|`left-sidebar`|`no-sidebar`|`both-sidebars`|…),
  `nav_position_setting`, `footer_widget_setting`, `content_layout_setting`.
- **Per-post overrides** are post meta: `_generate-sidebar-layout-meta`,
  `_generate-footer-widget-meta`, `_generate-full-width-content` (`true`|`contained`),
  `_generate-disable-headline`.

> **⚠️ Cache gotcha:** the theme caches its compiled dynamic CSS in the option
> `generate_dynamic_css_output`. After writing colors/fonts/settings outside the
> Customizer, **invalidate it** — `wp option update generate_dynamic_css_output ''`
> (or `POST /wp-json/generatepress/v1/reset/`) — or stale CSS keeps rendering.
> Read the live values first: `wp option get generate_settings --format=json`.

## Child theme PHP (`.partikuls` or any GeneratePress child)

The child theme's `functions.php` is where custom PHP belongs — never edit the
GeneratePress parent. GeneratePress is hook-rich; common patterns:

```php
// Enqueue child theme styles/scripts.
add_action( 'wp_enqueue_scripts', function () {
    wp_enqueue_style( 'partikuls-style', get_stylesheet_uri(), array(), wp_get_theme()->get( 'Version' ) );
} );

// Insert custom markup at GeneratePress hook locations.
add_action( 'generate_after_header', function () {
    // e.g. a promo bar, breadcrumb, etc.
} );
```

Prefer hooks over editing templates so updates stay safe. The full set of
`generate_*` action hooks (these are also the placement targets a GP Premium
**Hook/Block Element** uses via `_generate_hook` — see `elements-dynamic-data.md`):

- **Document/page:** `generate_before_header`, `generate_after_header`,
  `generate_inside_site_container`, `generate_inside_container`,
  `generate_before_footer`, `generate_before_footer_content`,
  `generate_after_footer_content`, `generate_after_footer`. (`wp_head`,
  `wp_body_open`, `wp_footer` are core.)
- **Header:** `generate_header` (builds the header —
  `remove_action('generate_header','generate_construct_header')` to replace it),
  `generate_before_header_content`, `generate_after_header_content`,
  `generate_before_logo`, `generate_after_logo`.
- **Navigation:** `generate_before_navigation`, `generate_inside_navigation`,
  `generate_after_primary_menu`, `generate_after_navigation`,
  `generate_menu_bar_items`, `generate_inside_mobile_menu`.
- **Content/entry:** `generate_before_main_content`, `generate_before_loop`,
  `generate_before_content`, `generate_before_entry_title`,
  `generate_after_entry_title`, `generate_after_entry_header`,
  `generate_after_entry_content`, `generate_after_content`, `generate_after_loop`,
  `generate_after_main_content`, `generate_after_primary_content_area`.
- **Archive/search:** `generate_before_archive_title`, `generate_after_archive_title`,
  `generate_after_archive_description`, `generate_paging_navigation`.
- **Sidebars:** `generate_before_left_sidebar_content`,
  `generate_after_left_sidebar_content`, `generate_before_right_sidebar_content`,
  `generate_after_right_sidebar_content`.
- **Footer:** `generate_after_footer_widgets`, `generate_footer` (builds the footer),
  `generate_before_copyright`, `generate_credits`.

Add a class/attribute to any theme element with the `generate_parse_attr` filter
(contexts include `body`, `header`, `inside-header`, `navigation`, `content`,
`main`, `entry-header`, `page-header`, `left-sidebar`, `right-sidebar`,
`site-info`):

```php
add_filter( 'generate_parse_attr', function ( $attr, $context ) {
    if ( 'header' === $context ) { $attr['class'] .= ' my-header'; }
    return $attr;
}, 10, 2 );
```

Useful layout/output filters: `generate_sidebar_layout`, `generate_footer_widgets`,
`generate_navigation_location`, `generate_show_title`, `generate_show_excerpt`,
`generate_copyright`, `generate_logo`.

## GP Premium "Elements" (no-code header/footer/hooks/blocks/templates)

GP Premium ships the **Elements** module — build headers, footers, hook
placements, page-layout settings, and **dynamic block-based templates** in the
admin (Appearance → Elements), with display-rule targeting (whole site, a post
type, specific pages). For site-wide chrome (custom header/footer, a CTA before
the footer on all posts), an Element beats a per-page paste or PHP.

The most powerful kind is a **Content Template** (`block` element with
`_generate_block_type = content-template`): it **replaces the loop output** for
matching posts, so it's the right way to design **single posts, CPT singles, and
archive cards** using **dynamic-data blocks** — *without* a child-theme
`the_content` filter or template file. Pair it with a **Layout element** for
full-width and to suppress the native title/featured.

> Reach for a Content Template Element (not a hook or `the_content` filter)
> whenever you need to render **live post data** in a template.

Full details — element meta model, Content Templates, the GP/GB dynamic-data
blocks (`generatepress/dynamic-content`, `generatepress/dynamic-image`,
`generateblocks/headline` + `gpDynamicTextType`), the `query`/`looper`/`loop-item`
loop, a WP-CLI creation recipe, and gotchas — are in
[`elements-dynamic-data.md`](elements-dynamic-data.md).

## GP Premium modules — current vs legacy

GP Premium is a bundle of toggleable modules (Appearance → GeneratePress; each is
the option `generate_package_<name>` set to `'activated'`). Reach for the modern
path, not the deprecated modules:

- **Current:** **Elements** (the big one — headers/footers/hooks/templates/layout;
  see `elements-dynamic-data.md`), **Site Library** (starter sites), **Font
  Library** (local Google/custom fonts; CPT `gp_font`), **Menu Plus** (sticky nav,
  off-canvas/slideout, mobile header, nav logo), **Spacing**, **Backgrounds**,
  **Blog**, **Secondary Nav**, **Copyright**, **Disable Elements**, **WooCommerce**.
- **Legacy / superseded — avoid for new work:**
  - **Colors** and **Typography** modules → replaced by the **theme 3.x** global
    colors + dynamic typography above (they only even load on old theme versions).
  - **Hooks**, **Page Header**, **Sections** modules → replaced by the **Elements**
    module (Hook element, Header/Hero element, GenerateBlocks content).

## theme.json / Global Styles

GeneratePress is a classic (non-FSE) theme but is block-editor-first. You can
still influence editor color/spacing presets via Global Styles where exposed,
but the primary, reliable controls are the Customizer (above) for globals and
GenerateBlocks Global Styles for component classes.

## Performance (a real selling point of this stack)

GeneratePress + GenerateBlocks is lightweight by design. Keep it that way:
- GB only loads each block's CSS when the block is present — don't fight that by
  dumping global CSS for one-off needs; use block `styles`.
- Always set `alt`, and let WordPress handle responsive `srcset` via the `media`
  block / proper attachment IDs rather than hardcoding huge images.
- Prefer CSS (`styles`) over JavaScript for layout and simple motion. Reserve Pro
  interactive blocks (carousel/tabs/accordion) for when interaction is genuinely
  needed.
- Reuse `globalClasses` instead of duplicating large `styles` objects across many
  blocks — smaller markup, fewer redundant rules.
