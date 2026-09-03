# Polylang XLIFF export internals

Everything here was verified against **Polylang Pro 3.8.5**. Class/method names
are stable across recent 3.x but re-check line numbers before quoting them.

## Table of contents
- [Why only post_content is empty](#why-only-post_content-is-empty)
- [What Polylang fills by itself](#what-polylang-fills-by-itself)
- [The programmatic export recipe](#the-programmatic-export-recipe)
- [The segmentation walker](#the-segmentation-walker)
- [XLIFF shape produced](#xliff-shape-produced)
- [Adapting the scripts](#adapting-the-scripts)

## Why only post_content is empty

`PLL_Export_Posts::add_item()` exports each post field. For `post_content` it
calls `add_post_content()`, which contains the guard:

```php
// polylang-pro/src/services/exporter/export-posts.php  (~line 145)
private function add_post_content( PLL_Export_Data $export, WP_Post $post, string $translation ) {
    $content = PLL_Translation_Walker_Factory::create_from( $post->post_content );
    $translations = new Translations();
    $content->walk( array( $translations, 'add_entry' ) );

    foreach ( $translations->entries as $entry ) {
        if ( '' === $entry->singular ) { continue; }
        // The translated post content isn't exported when source or translated posts have blocks.
        $translation = has_blocks( $translation ) || has_blocks( $post->post_content ) ? '' : $translation;
        $export->add_translation_entry( /* … */, $entry->singular, $translation );
    }
}
```

The block-based content is segmented (one `<unit>` per translatable text node),
but the translation is forcibly blanked because Polylang has no built-in
per-segment mapping from the source block tree to the translated block tree.
There is **no filter** around this line, so it cannot be toggled off — the fix
must reconstruct the mapping ourselves. `post_title` and other single-value
fields take the `else` branch of `add_item()` and are filled directly from the
translated post, which is why titles come through but bodies do not.

## What Polylang fills by itself

Confirmed by generating an export for a fully-translated CPT post: only
`post_content` targets were empty. Everything else was populated:

| Unit type      | Source of the target value                          | Filled by Polylang |
|----------------|-----------------------------------------------------|--------------------|
| `x:post_title` | translated post `post_title`                        | yes                |
| `x:post_excerpt`| translated post `post_excerpt`                     | yes                |
| `x:acf`        | ACF integration (`.../integrations/ACF/Strategy`)   | yes (e.g. 22/22)   |
| `x:postmeta`   | `PLL_Export_Post_Metas` (translated post meta)      | yes (when present) |
| `x:name`       | linked translated term names                        | yes                |
| `x:post_content`| **blanked by the has_blocks guard**                | **no** ← we fill    |

Practical consequence: the fill scripts touch **only** `x:post` groups'
`x:post_content` units and leave every other unit and every `x:term` group
exactly as Polylang produced them.

## The programmatic export recipe

To produce the exact same XLIFF the wp-admin bulk "Export" action produces, but
from wp-cli (no UI), replicate `PLL_Export_Bulk_Option`:

```php
$model     = PLL()->model;
$format    = new PLL_Xliff_Format();
$container = new PLL_Export_Container( $format->get_export_class( '21' ) ); // '12','20','21'
$exporter  = new PLL_Export_Data_From_Posts( $model );

$posts = array_map( 'get_post', $ids );               // NOT get_posts(post_type=>'any')
$target = $model->get_language( 'de' );                // slug → PLL_Language

$exporter->send_to_export( $container, $posts, $target, array( 'include_translated_items' => true ) );

foreach ( $container as $export ) {                    // PLL_Export_File per source→target pair
    $xliff_string = $export->get();
    $suggested_name = $export->get_filename();         // fr-FR_de-DE_<datetime>.xliff
}
```

Notes:
- `send_to_export()` groups the posts by **source** language internally and
  emits one `PLL_Export_File` per (source, target) pair. Passing all-one-source
  posts + one target ⇒ a single file with one `<group>` per post.
- `include_translated_items => true` mirrors the UI bulk export: it also pulls in
  linked items (assigned taxonomy terms, reusable blocks) even when already
  translated, so their groups appear in the file.
- Export class version `'21'` = XLIFF 2.1 (`version="2.1"`, xmlns `…:2.0`), which
  is what the current UI emits. Use `get_export_class()` rather than hardcoding
  the class name.

## The segmentation walker

`PLL_Translation_Walker_Factory::create_from( $content )` returns a
`PLL_Translation_Walker_Blocks` when `has_blocks($content)` else a
`PLL_Translation_Walker_Classic`. `->walk( $callback )` invokes `$callback` once
per translatable segment (the callback receives a `Translation_Entry`-like object
with `->singular`, and returns the string to substitute — return it unchanged to
read without modifying).

To recover the translation per segment: run the walker on the **source** post
and on the **translated** post separately, collect both ordered `singular` lists,
and pair by index. This is exact **iff** both walks yield the same number of
segments — they do when the two posts share block structure (same block types /
same `uniqueId`s, which is the normal case when a translation was created by
Polylang duplication and then translated in place).

When counts differ, the translation diverged structurally (classic case: the
source page was rebuilt with GenerateBlocks `generateblocks/*` blocks while the
translation still uses native `core/paragraph|heading|list` — zero `uniqueId`
overlap, completely different segment counts). Index pairing would silently map
translations onto the wrong blocks, so the scripts **refuse** and flag it. A
future enhancement could align by block `uniqueId` (parse_blocks on both, match
by attrs), but only attempt that if the divergence is small and structural, and
verify each pairing.

## XLIFF shape produced

```xml
<xliff xmlns="urn:oasis:names:tc:xliff:document:2.0" version="2.1" srcLang="fr-FR" trgLang="de-DE">
  <file id="1" original="Polylang|3.8.5|https://site.tld" canResegment="no">
    <group id="1" type="x:post" name="19">           <!-- name = SOURCE post ID -->
      <unit id="1" type="x:post_title"> <segment>
        <source><![CDATA[Accueil]]></source>
        <target><![CDATA[Startseite]]></target>       <!-- filled by Polylang -->
      </segment></unit>
      <unit id="2" type="x:post_content"> <segment>
        <source><![CDATA[<h1 …>…</h1>]]></source>
        <target><![CDATA[<h1 …>…</h1>]]></target>     <!-- WE fill this one -->
      </segment></unit>
      …
    </group>
    <group id="2" type="x:term" name="18"> … </group>  <!-- linked terms, filled by Polylang -->
  </file>
</xliff>
```

Targets are written as `CDATA` sections so the block HTML / `var(--…)` CSS inside
GenerateBlocks markup survives unescaped.

## Adapting the scripts

- **Other block plugins (Kadence, native core, Greenshift…)**: the has_blocks
  guard and the walker are block-plugin agnostic; the scripts work unchanged as
  long as the source and translation share block structure.
- **Term-only or meta-only exports**: Polylang already fills those targets, so
  you usually do not need the fill step at all — a plain programmatic export is
  bilingual out of the box for non-block fields.
- **A field Polylang leaves empty that you DO want filled**: identify the unit
  `type`, find the translated value (post field, `get_post_meta`, term field),
  and fill it in the same DOM loop — mirror the `post_content` branch but source
  the value directly instead of via the walker.
- **Debugging an unexpected empty target**: check, in order, (1) does a linked
  translation exist for that source in that language (`pll_get_post_translations`),
  (2) do source/translation segment counts match (divergent?), (3) is the field
  one Polylang normally fills (then the translation itself is empty in the DB).
