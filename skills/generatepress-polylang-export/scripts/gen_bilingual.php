<?php
/**
 * gen_bilingual.php — Generate a Polylang XLIFF export for a set of posts and a
 * target language, then fill the post_content <target> fields (which Polylang
 * deliberately leaves empty for block-based content) with the existing
 * translation, aligned block-by-block.
 *
 * Why this exists: Polylang Pro's exporter empties the post_content <target>
 * whenever the source OR translation contains Gutenberg/GenerateBlocks blocks
 * (hardcoded `has_blocks()` guard). Every OTHER field — post_title, ACF,
 * postmeta, taxonomy term names — is filled natively by Polylang. So this
 * script reuses Polylang's own export (identical, re-importable XLIFF 2.1) and
 * only patches post_content.
 *
 * Alignment: the exact same segmentation walker Polylang uses
 * (PLL_Translation_Walker_Factory) is run on both source and translated
 * post_content. Segments are paired by position. Filling only happens when the
 * two segment counts match; if they differ the translation has diverged
 * structurally (e.g. source rebuilt in GenerateBlocks while the translation is
 * still on core/* blocks) and the segment is left empty and flagged — never
 * mispaired.
 *
 * Usage:
 *   wp eval-file gen_bilingual.php <target_slug> <out.xliff> <ids>
 *
 *   <target_slug>  Polylang language slug to translate INTO (e.g. en, de).
 *   <out.xliff>    Output path.
 *   <ids>          Source post IDs. Accepts several args OR one comma/space
 *                  separated string (zsh does not word-split unquoted vars, so
 *                  quoting "1,2,3" is the safe form).
 *
 * Example:
 *   wp eval-file gen_bilingual.php de out.xliff "19,5638,5749"
 */

if ( ! isset( $args ) || count( $args ) < 3 ) {
	WP_CLI::error( 'Usage: wp eval-file gen_bilingual.php <target_slug> <out.xliff> <ids>' );
}
$slug     = array_shift( $args );
$out      = array_shift( $args );
// IDs may arrive as separate args or as one comma/space-separated string.
$post_ids = array_values( array_filter( array_map( 'intval', preg_split( '/[\s,]+/', trim( implode( ' ', $args ) ) ) ) ) );
if ( empty( $post_ids ) ) {
	WP_CLI::error( 'No post IDs given.' );
}

if ( ! function_exists( 'PLL' ) || ! class_exists( 'PLL_Xliff_Format' ) ) {
	WP_CLI::error( 'Polylang Pro (with import/export) does not appear to be active.' );
}

/** Segment a content string exactly like Polylang's exporter (ordered list). */
function pllx_segments( $content ) {
	if ( '' === (string) $content ) {
		return array();
	}
	$walker = PLL_Translation_Walker_Factory::create_from( $content );
	$segs   = array();
	$walker->walk( function ( $entry ) use ( &$segs ) {
		$singular = is_object( $entry ) ? $entry->singular : (string) $entry;
		$segs[]   = $singular;
		return $singular; // do not modify the content
	} );
	return $segs;
}

$model           = PLL()->model;
$target_language = $model->get_language( $slug );
if ( ! $target_language ) {
	WP_CLI::error( "Unknown target language slug: $slug" );
}

// --- 1. Generate the Polylang export (XLIFF 2.1, identical to the wp-admin UI). ---
// Load posts directly by ID: get_posts(post_type=>'any') silently drops
// non-public CPTs and post types flagged exclude_from_search.
$posts = array_values( array_filter( array_map( 'get_post', $post_ids ) ) );
if ( empty( $posts ) ) {
	WP_CLI::error( 'None of the given IDs resolved to a post.' );
}

$format    = new PLL_Xliff_Format();
$container = new PLL_Export_Container( $format->get_export_class( '21' ) );
$exporter  = new PLL_Export_Data_From_Posts( $model );
$exporter->send_to_export( $container, $posts, $target_language, array( 'include_translated_items' => true ) );

$xml = '';
foreach ( $container as $export ) {
	$xml = $export->get(); // one file per source→target language pair
	break;
}
if ( '' === $xml ) {
	WP_CLI::error( 'Export produced no file (are the posts assigned a source language?).' );
}

// --- 2. Patch post_content <target> via segment alignment. -----------------------
$dom = new DOMDocument();
$dom->preserveWhiteSpace = true;
$dom->loadXML( $xml );

$t = array( 'groups' => 0, 'content_units' => 0, 'content_filled' => 0, 'no_tr' => 0, 'unsafe' => 0 );

foreach ( iterator_to_array( $dom->getElementsByTagName( 'group' ) ) as $group ) {
	if ( 'x:post' !== $group->getAttribute( 'type' ) ) {
		continue; // term groups etc. are already filled by Polylang
	}
	$t['groups']++;
	$src_id = (int) $group->getAttribute( 'name' );

	$content_units = array();
	foreach ( $group->getElementsByTagName( 'unit' ) as $u ) {
		if ( 'x:post_content' === $u->getAttribute( 'type' ) ) {
			$content_units[] = $u;
		}
	}
	if ( empty( $content_units ) ) {
		continue;
	}

	$tr    = pll_get_post_translations( $src_id );
	$tr_id = isset( $tr[ $slug ] ) ? (int) $tr[ $slug ] : 0;
	if ( ! $tr_id ) {
		$t['no_tr']++;
		$t['content_units'] += count( $content_units );
		continue; // no translation → leave targets empty (to be translated)
	}

	$src_all = pllx_segments( get_post( $src_id )->post_content );
	$tr_all  = pllx_segments( get_post( $tr_id )->post_content );
	$aligned = ( count( $src_all ) === count( $tr_all ) );

	// Build a source→translation MAP from the parallel walk. Match each XLIFF
	// unit by its own source TEXT, not by position: Polylang deduplicates
	// repeated segments in the export (e.g. a section that appears twice in a
	// privacy policy), so a positional pairing would drift. A source that maps
	// to two DIFFERENT translations is marked unresolved (null) for safety.
	$map = array();
	if ( $aligned ) {
		for ( $i = 0, $n = count( $src_all ); $i < $n; $i++ ) {
			$s = $src_all[ $i ];
			if ( '' === $s ) {
				continue;
			}
			if ( array_key_exists( $s, $map ) && $map[ $s ] !== $tr_all[ $i ] ) {
				$map[ $s ] = null;
			} elseif ( ! array_key_exists( $s, $map ) ) {
				$map[ $s ] = $tr_all[ $i ];
			}
		}
	}

	$unsafe = false;
	foreach ( $content_units as $u ) {
		$t['content_units']++;
		$seg = $u->getElementsByTagName( 'segment' )->item( 0 );
		if ( ! $seg ) {
			continue;
		}
		$src_el = $seg->getElementsByTagName( 'source' )->item( 0 );
		$tgt_el = $seg->getElementsByTagName( 'target' )->item( 0 );
		if ( ! $src_el ) {
			continue;
		}
		if ( ! $tgt_el ) {
			$tgt_el = $seg->appendChild( $dom->createElement( 'target' ) );
		}

		if ( ! $aligned ) {
			$unsafe = true; // segment counts differ = structural divergence
			continue;
		}
		$key = $src_el->textContent;
		if ( ! array_key_exists( $key, $map ) || null === $map[ $key ] ) {
			$unsafe = true; // this source cannot be confidently resolved
			continue;
		}
		if ( '' === $map[ $key ] ) {
			continue; // segment genuinely untranslated (not an error)
		}

		while ( $tgt_el->firstChild ) {
			$tgt_el->removeChild( $tgt_el->firstChild );
		}
		$tgt_el->appendChild( $dom->createCDATASection( $map[ $key ] ) );
		$t['content_filled']++;
	}

	if ( $unsafe ) {
		$t['unsafe']++;
		WP_CLI::warning( sprintf(
			'  post %d -> %d (%s): divergent segmentation (src=%d / tr=%d), content left empty.',
			$src_id, $tr_id, $slug, count( $src_all ), count( $tr_all )
		) );
	}
}

file_put_contents( $out, $dom->saveXML() );

WP_CLI::success( sprintf(
	'%s : %d posts, %d/%d post_content targets filled (%d without translation, %d divergent).',
	basename( $out ), $t['groups'], $t['content_filled'], $t['content_units'], $t['no_tr'], $t['unsafe']
) );
