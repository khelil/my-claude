<?php
/**
 * list_sources.php — Inventory the translatable objects of a post type: for
 * each source-language post, show its content length and which languages it is
 * translated into. Use this before exporting to pick the IDs to pass to
 * gen_bilingual.php and to report translation coverage (what still needs to be
 * translated per language).
 *
 * Usage:
 *   wp eval-file list_sources.php <post_type> [source_slug]
 *
 *   <post_type>    e.g. page, post, vehicle, gp_elements, dealer, pack ...
 *   [source_slug]  Source language to list. Defaults to Polylang's default lang.
 *
 * Output is tab-separated: ID, content_length, <lang>=<tr_id|-> per language, title.
 * A trailing "IDS: a,b,c" line lists source IDs that have a body (len>0) for
 * convenient copy-paste into gen_bilingual.php.
 */

if ( ! isset( $args ) || count( $args ) < 1 ) {
	WP_CLI::error( 'Usage: wp eval-file list_sources.php <post_type> [source_slug]' );
}
if ( ! function_exists( 'PLL' ) ) {
	WP_CLI::error( 'Polylang does not appear to be active.' );
}

$post_type = $args[0];
$src_slug  = $args[1] ?? pll_default_language();
$langs     = pll_languages_list(); // e.g. ['fr','en','de']

$q = new WP_Query( array(
	'post_type'      => $post_type,
	'post_status'    => 'any',
	'posts_per_page' => -1,
	'fields'         => 'ids',
	'lang'           => $src_slug,
	'orderby'        => 'ID',
	'order'          => 'ASC',
) );

if ( empty( $q->posts ) ) {
	WP_CLI::warning( "No '$post_type' posts found in language '$src_slug'." );
	return;
}

$with_body = array();
WP_CLI::log( "post_type=$post_type  source=$src_slug  languages=" . implode( ',', $langs ) );
WP_CLI::log( str_repeat( '-', 60 ) );

foreach ( $q->posts as $id ) {
	$p    = get_post( $id );
	$len  = strlen( (string) $p->post_content );
	$tr   = pll_get_post_translations( $id );
	$cols = array();
	foreach ( $langs as $l ) {
		if ( $l === $src_slug ) {
			continue;
		}
		$cols[] = sprintf( '%s=%s', $l, $tr[ $l ] ?? '-' );
	}
	if ( $len > 0 ) {
		$with_body[] = $id;
	}
	WP_CLI::log( sprintf(
		"%-7d len=%-6d %-24s %s",
		$id, $len, implode( '  ', $cols ), mb_substr( (string) $p->post_title, 0, 40 )
	) );
}

WP_CLI::log( str_repeat( '-', 60 ) );
WP_CLI::log( 'IDS (with body): ' . implode( ',', $with_body ) );
