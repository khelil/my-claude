<?php
/**
 * fill_xliff.php — Take an XLIFF that Polylang already exported (via the
 * wp-admin bulk "Export" action) and fill the post_content <target> fields it
 * left empty for block-based content.
 *
 * Use this when the user ALREADY has a Polylang UI export (empty post_content
 * targets) and just wants the existing translations merged in. If you can run
 * wp-cli against the site freely, prefer gen_bilingual.php instead — it also
 * generates the export, so there is no manual wp-admin step.
 *
 * Everything except post_content (post_title, ACF, postmeta, term names) is
 * already filled by Polylang, so this script does not touch those.
 *
 * The target language is read from the file's own trgLang attribute, and each
 * post_content <target> is filled by re-walking source + translated post with
 * Polylang's segmentation walker and pairing segments by position. Segments are
 * only filled when the source/translation segment counts match; divergent posts
 * are left empty and flagged.
 *
 * Usage:
 *   wp eval-file fill_xliff.php <in.xliff> <out.xliff>
 */

if ( ! isset( $args ) || count( $args ) < 2 ) {
	WP_CLI::error( 'Usage: wp eval-file fill_xliff.php <in.xliff> <out.xliff>' );
}
$in  = $args[0];
$out = $args[1];

if ( ! function_exists( 'PLL' ) || ! class_exists( 'PLL_Translation_Walker_Factory' ) ) {
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
		return $singular;
	} );
	return $segs;
}

/** Resolve a Polylang language slug from an XLIFF trgLang (e.g. de-DE → de). */
function pllx_resolve_slug( $trg ) {
	$trg = strtolower( $trg );
	foreach ( PLL()->model->get_languages_list() as $lang ) {
		if ( strtolower( str_replace( '_', '-', $lang->locale ) ) === $trg || strtolower( $lang->slug ) === substr( $trg, 0, 2 ) ) {
			return $lang->slug;
		}
	}
	return substr( $trg, 0, 2 );
}

$xml = file_get_contents( $in );
if ( false === $xml ) {
	WP_CLI::error( "Cannot read $in" );
}

$dom = new DOMDocument();
$dom->preserveWhiteSpace = true;
if ( ! $dom->loadXML( $xml ) ) {
	WP_CLI::error( "Invalid XML: $in" );
}

$xliff   = $dom->getElementsByTagName( 'xliff' )->item( 0 );
$trgLang = $xliff ? $xliff->getAttribute( 'trgLang' ) : '';
$slug    = pllx_resolve_slug( $trgLang );
WP_CLI::log( 'File: ' . basename( $in ) . "  (target: $trgLang -> '$slug')" );

$t = array( 'groups' => 0, 'content_units' => 0, 'content_filled' => 0, 'no_tr' => 0, 'unsafe' => 0 );

foreach ( iterator_to_array( $dom->getElementsByTagName( 'group' ) ) as $group ) {
	if ( 'x:post' !== $group->getAttribute( 'type' ) ) {
		continue;
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
		continue;
	}

	$src_all = pllx_segments( get_post( $src_id )->post_content );
	$tr_all  = pllx_segments( get_post( $tr_id )->post_content );
	$aligned = ( count( $src_all ) === count( $tr_all ) );

	// Match XLIFF units by source TEXT (not position): Polylang deduplicates
	// repeated segments in the export, so a positional pairing would drift.
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
			$unsafe = true;
			continue;
		}
		$key = $src_el->textContent;
		if ( ! array_key_exists( $key, $map ) || null === $map[ $key ] ) {
			$unsafe = true;
			continue;
		}
		if ( '' === $map[ $key ] ) {
			continue;
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
			'  post %d -> %d: divergent segmentation (src=%d / tr=%d), content left empty.',
			$src_id, $tr_id, count( $src_all ), count( $tr_all )
		) );
	}
}

file_put_contents( $out, $dom->saveXML() );

WP_CLI::success( sprintf(
	'%s : %d posts, %d/%d post_content targets filled (%d without translation, %d divergent).',
	basename( $out ), $t['groups'], $t['content_filled'], $t['content_units'], $t['no_tr'], $t['unsafe']
) );
