# GP Premium Elements, Content Templates & dynamic data

How to build **dynamic, no-PHP templates** in GeneratePress — single-post layouts,
archive cards, author boxes, anything that pulls live post data. This is the
GP-native alternative to child-theme `the_content` filters and template files.

> Patterns below were verified against **GP Premium 2.5.6 + GenerateBlocks 2.2.1 +
> GB Pro 2.5.0**. Attribute *names* are stable across recent versions, but confirm
> the available option *values* on the live install (the editor is the source of
> truth — build one element by hand, then read its `post_content` to copy the
> exact markup).

## Elements are posts (`gp_elements`)

Every GP Premium Element is a `gp_elements` post. Two meta keys decide what it is:

- `_generate_element_type` — `block`, `header` (page hero), `hook`, or `layout`.
- `_generate_block_type` (only on `block` elements) — sets the kind of block
  element **and auto-selects the placement hook**. Verified mapping (GB Pro /
  GP Premium `elements/class-block.php`):

  | `_generate_block_type` | Auto hook | |
  |---|---|---|
  | `hook` | from `_generate_hook` (you choose; `custom` → `_generate_custom_hook`) | generic placement |
  | `site-header` | `generate_header` | replaces theme header |
  | `site-footer` | `generate_footer` | replaces theme footer |
  | `page-hero` | from `_generate_hook` | hero band; also force-disables the native title/featured image/meta |
  | `content-template` | `generate_before_do_template_part` | single/CPT item — the big one |
  | `loop-template` | `generate_before_main_content` | archive/loop |
  | `post-meta-template` | `generate_after_entry_title` (or via `_generate_post_meta_location`) | meta row |
  | `right-sidebar` / `left-sidebar` | `generate_before_{right,left}_sidebar_content` | sidebar content |
  | `search-modal` | `generate_inside_search_modal` | search overlay |

  Priority is `_generate_hook_priority` (default `10`).

Plus, on every element:

- `_generate_element_display_conditions` — **where it applies** (serialized array
  of `{rule, object}`). Example for all single posts:
  `a:1:{i:0;a:2:{s:4:"rule";s:9:"post:post";s:6:"object";s:0:"";}}`.
  Common rules: `post:post`, `post:page`, `post:<cpt>` (e.g. `post:nc_camping_car`),
  `general:front_page`, `general:site`, `archive:post_type:<cpt>`, `taxonomy:<tax>`.
- `_generate_element_exclude_conditions`, `_generate_element_user_conditions` —
  optional narrowing. Exclude uses the same `{rule, object}` shape (suppress where
  it matches). User conditions are a flat array of strings: `general:logged_in`,
  `general:logged_out`, or a role slug (`administrator`, `editor`, …).
  General location rules also include `general:archive`, `general:author`,
  `general:search`, `general:404`.
- `_generate_element_ignore_languages` — `true` to apply across Polylang/WPML
  languages (terms/templates are usually shared; set this so you don't duplicate
  per language).

### The three element shapes you'll actually build

| Goal | `_generate_element_type` | `_generate_block_type` | Notes |
|---|---|---|---|
| **Single / archive template** (replaces the loop output) | `block` | `content-template` | The big one — see below. Renders dynamic post data. |
| **Site-wide chrome** (header / footer / CTA band) | `block` | `site-header` / `site-footer` / *empty* + `_generate_hook` | An empty `block_type` + a `_generate_hook` (e.g. `generate_after_header`) injects the block content at that hook. |
| **Page-layout settings** (no content) | `layout` | — | Carries *settings only* (width, sidebar, disable title/featured). Pair it with a content-template. |

## Content Template — the native "single/archive template"

A **Content Template** (`_generate_block_type = content-template`, type `block`)
**replaces the post's loop output** wherever its display conditions match. This is
the correct way to skin single posts / CPT singles / archive cards — **no
`the_content` filter, no template file, no duplicated title/content**.

Relevant per-template meta (mirror the editor's "Template Settings"):
`_generate_disable_title`, `_generate_disable_featured_image`,
`_generate_use_theme_post_container`, `_generate_post_meta_location`,
`_generate_post_loop_item_tagname`, `_generate_disable_post_navigation`, …

### Pair it with a Layout element

A content-template renders *inside* the normal content area. To go edge-to-edge
(full-width cover, dark related-posts band) and to suppress the theme's **native**
title/featured image, add a sibling **Layout element** with the same display
conditions:

```
_generate_element_type        = layout
_generate_content_area        = full-width
_generate_sidebar_layout      = no-sidebar
_generate_disable_content_title  = true
_generate_disable_featured_image = true
_generate_element_ignore_languages = true
_generate_element_display_conditions = a:1:{i:0;a:2:{s:4:"rule";s:9:"post:post";s:6:"object";s:0:"";}}
```

> Without the Layout element the content stays boxed and GeneratePress prints its
> own `entry-header` title → you'd see the title twice. With it: clean, full-width.

### Create both from the CLI

```bash
wp eval '
$id = wp_insert_post(["post_type"=>"gp_elements","post_status"=>"publish","post_title"=>"Single Post Content"]);
update_post_meta($id,"_generate_element_type","block");
update_post_meta($id,"_generate_block_type","content-template");
update_post_meta($id,"_generate_element_ignore_languages","true");
update_post_meta($id,"_generate_element_display_conditions",[["rule"=>"post:post","object"=>""]]);
echo $id;
'
# then set its block markup (see below):
wp post update <id> template.html
```

`gp_elements` render their stored blocks through `do_blocks()` regardless of
editor block-validation, so **hand-authored markup renders fine** even if the
saved HTML isn't byte-perfect — the block *delimiters* (attributes) drive dynamic
output.

## Dynamic-data blocks (the pieces that pull live data)

Drop these inside a content-template (or a query `loop-item`). In `gb_build.py`
trees, emit them as `type:"raw"` nodes; their inner HTML is a placeholder that the
server replaces at render. All accept `className` for styling.

**`generatepress/dynamic-content`** — text regions:
```html
<!-- wp:generatepress/dynamic-content {"contentType":"post-content"} /-->
<!-- wp:generatepress/dynamic-content {"contentType":"post-excerpt","className":"card-desc"} /-->
```
`contentType`: `post-content`, `post-excerpt`, `post-title`, `comments`,
`content-area`, … (`post-content` runs the full `the_content` pipeline).

**`generatepress/dynamic-image`** — images:
```html
<!-- wp:generatepress/dynamic-image {"imageType":"featured-image","imageSize":"large","linkTo":"single-post"} /-->
<!-- wp:generatepress/dynamic-image {"imageType":"author-avatar","avatarRounded":true} /-->
```
`imageType`: `featured-image`, `author-avatar`. `linkTo`: `single-post` (wraps the
`<img>` in an `<a>` — style `& a, & img`). Renders **nothing** when there's no
image, so give the wrapper a fallback background.

**`generateblocks/headline`** — dynamic *inline text* (title/date/author/terms).
This legacy block is the workhorse for dynamic text (the 2.x `text` block uses a
different dynamic-tags system; `headline` is what the GP dynamic UI emits):
```html
<!-- wp:generateblocks/headline {"uniqueId":"aaaa0001","element":"h1","blockVersion":3,
  "className":"post-title","gpDynamicTextType":"title","gpDynamicLinkType":"single-post",
  "gpDynamicTextReplace":"Post Title"} -->
<h1 class="gb-headline gb-headline-aaaa0001 gb-headline-text post-title">Post Title</h1>
<!-- /wp:generateblocks/headline -->
```
- `gpDynamicTextType`: `title`, `post-author`, `post-date`, `post-meta`, `terms`.
- `gpDynamicLinkType`: `single-post`, `author-archives`, `term-archives` (or omit
  for no link).
- `gpDynamicTextReplace`: the placeholder shown in the editor / fallback.
- `gpDynamicTextTaxonomy`: e.g. `category` (with `terms`).
- Date: by default shows the **published** date. Add `"dateType":"updated"` (older
  markup: `"gpDynamicDateUpdated":true`) to show the **modified** date instead.

**`generateblocks/button`** — same `gpDynamic*` attrs for a linked pill (e.g. a
category chip via `gpDynamicTextType:"terms"`, `gpDynamicLinkType:"term-archives"`,
`gpDynamicTextTaxonomy:"category"`).

## Query loop (related posts, post grids)

`generateblocks/query` → `generateblocks/looper` → `generateblocks/loop-item`.
Inside the `loop-item`, the dynamic blocks above resolve **per looped post**. Copy
the exact shape from a working query on the install; canonical structure:

```html
<!-- wp:generateblocks/query {"uniqueId":"q0000001","tagName":"div",
  "query":{"post_type":"post","per_page":3,"posts_per_page":"3","orderby":"date","order":"desc","exclude_current":true},
  "className":"gb-query"} -->
<div class="gb-query"><!-- wp:generateblocks/looper {"uniqueId":"l0000001","tagName":"div","className":"grid"} -->
<div class="gb-looper-l0000001 grid"><!-- wp:generateblocks/loop-item {"uniqueId":"i0000001","tagName":"div","className":"card"} -->
<div class="gb-loop-item gb-loop-item-i0000001 card">
  <!-- dynamic-image featured + headline title + dynamic-content excerpt -->
</div>
<!-- /wp:generateblocks/loop-item --></div>
<!-- /wp:generateblocks/looper --></div>
<!-- /wp:generateblocks/query -->
```
- `query` keys: `post_type`, `posts_per_page` (string), `per_page`, `orderby`,
  `order`, `exclude_current`. For "same taxonomy as current", add the taxonomy
  query params (set it once in the editor and copy the resulting object — the
  param shape is fiddly).
- `looper`/`loop-item` take normal GB `styles`+`css` (grid, card), so build the
  *layout* of the loop with `gb_build.py` and splice the dynamic blocks in.

## Styling strategy

Two clean options:

1. **Inline (`gb_build.py`)** — build the static layout shell (`element`/`text`/
   `media` with `styles`→`css`) via the script, and insert dynamic blocks as
   `type:"raw"`. Best when the design is self-contained.
2. **Classes + stylesheet** — give every block a `className` (`.lv-spa-*`) and ship
   a small child-theme CSS file enqueued on the matching template
   (`is_singular('post')`). Best when you want the design tokens in one editable
   place and the element markup minimal. The dynamic blocks (`headline`,
   `dynamic-content`, `dynamic-image`) all accept `className`.

## Gotchas

- **Date format** follows **Settings → General** (`date_format`); GenerateBlocks
  has no per-block date format in 2.2.x. Need `dd/mm/yyyy`? Change the site format.
- **`dateType:"updated"`** shows the *modified* date — surprising right after you
  edit a post (it'll show today). Use published date unless you mean "last
  updated".
- **Content-template duplication**: if the native title/content still appears,
  you're missing the companion **Layout element** (`disable_content_title` /
  `disable_featured_image`) or its display conditions don't match.
- **Dynamic image absent** → block outputs nothing; always give the image wrapper a
  fallback background + fixed height.
- **Breadcrumbs**: GP has no native breadcrumb block. Compose a static prefix
  (`Accueil › Blog ›`) + a `headline` dynamic `title`, or use a breadcrumb plugin's
  shortcode via a `type:"raw"` shortcode block.

## When to use what

- **Single / CPT single / archive design** → **Content Template** (+ Layout
  element). Prefer this over a child-theme `the_content` filter or template file.
- **Header / footer / promo band on many pages** → **Block element** (`site-header`
  / `site-footer`, or empty type + `_generate_hook`).
- **One-off page** → paste GB markup into the page (no element).
- **Behaviour with no element equivalent** (truly cross-cutting PHP) → child-theme
  hook. Reach for this last, not first.
