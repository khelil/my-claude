---
name: generatepress-polylang-export
description: >-
  Produce bilingual XLIFF translation files from a Polylang (Pro) WordPress site
  — including sites built with GeneratePress / GenerateBlocks or any block-based
  (Gutenberg) content — with the EXISTING translations pre-filled into the
  <target> fields (a true source+translation file, not source-only). Use
  whenever someone on a WordPress + Polylang site wants their translated content
  OUT as XLIFF: exporting pages, posts, custom post types, or GP Elements
  (header, footer, mega-menus) for a translation agency, translator, or CAT
  tool; making one XLIFF per language (en, de, fr…); or backing up / migrating
  existing Polylang translations before a site move. ESPECIALLY reach for this
  skill when a Polylang XLIFF export comes back with the page body / post_content
  targets empty or blank while the titles look fine — that is a known, deliberate
  Polylang behavior (the has_blocks guard) this skill works around by filling
  those targets with the real existing translation. Works in any language and
  fires on French requests too (e.g. « exporter les pages pour l'agence de
  traduction », « le corps des pages est vide »). Do NOT use for importing an
  XLIFF back into the site, translating a short snippet, generating .pot/gettext
  files, or CSV / WooCommerce exports.
---

# GeneratePress / Polylang XLIFF export

Generate **re-importable XLIFF files** from a Polylang-Pro WordPress site with
each `<target>` already carrying the existing translation, so the user gets a
true **bilingual** file (source + translation) rather than the source-only file
Polylang produces for block-based content.

## The core problem this solves

Polylang Pro's exporter **intentionally empties the `post_content` `<target>`**
whenever the source *or* the translation contains Gutenberg / GenerateBlocks
blocks. It is a hardcoded guard (`has_blocks()`), not a bug or a mis-config:

```
polylang-pro/src/services/exporter/export-posts.php
  // The translated post content isn't exported when source or translated posts have blocks.
  $translation = has_blocks( $translation ) || has_blocks( $post->post_content ) ? '' : $translation;
```

On GeneratePress/GenerateBlocks sites `has_blocks()` is essentially always true,
so **every** `post_content` target exports empty. Crucially, **everything else
is filled by Polylang natively** — `post_title`, ACF fields (`x:acf`), post meta
(`x:postmeta`), taxonomy term names (`x:name`). So the only gap to close is
`post_content`, and that is exactly what the bundled scripts do. See
`references/internals.md` for the full mechanism.

## Prerequisites

- **Polylang Pro** active (with the import/export module) and **wp-cli** access.
- Confirm before running: `wp plugin list --status=active | grep -i polylang`
  and `wp eval 'var_dump( class_exists("PLL_Xliff_Format") );'`.
- The scripts read live translations from the DB, so run them against the
  environment that actually holds the content (usually local/staging).

### Running wp-cli
Use the site's normal `wp`. On **Local by Flywheel**, DB commands fail with
"Error establishing a database connection" unless `PHPRC` points at Local's PHP
config — if the user has a documented wp-cli invocation (e.g. in CLAUDE.md or
memory), use it. Always pass file paths to `wp eval-file` as **absolute paths**;
wp-cli does not reliably resolve relative ones.

## Workflow

### 1. Decide what to export and pick a granularity
Decide two things:
- **Which objects** — a whole post type (`page`, `post`, a CPT like `vehicle`),
  a set of `gp_elements` (Header/Footer/mega-menus), specific IDs, etc.
- **File granularity** — the natural default is **one file per post-type × per
  target language** (mirrors Polylang's own bulk export, which bundles all
  selected posts into one file per source→target pair). Offer **one file per
  object per language** only if the user's CAT tool wants that. XLIFF is
  inherently bilingual: one target language per file, so N target languages ⇒ N
  files.

### 2. Inventory sources + coverage
Run `scripts/list_sources.php` to see, per source post, its content length and
which languages it is translated into. This both surfaces the IDs to export and
lets you report honestly on coverage (what is untranslated).

```
wp eval-file /abs/path/scripts/list_sources.php <post_type> [source_slug]
```

The final `IDS (with body): a,b,c` line is copy-paste ready for step 3. Skip
zero-length entries (e.g. layout-only GP Elements have no translatable body).

### 3. Generate the bilingual file(s)
Preferred path — generate the Polylang export **and** fill it in one shot, no
wp-admin step needed:

```
wp eval-file /abs/path/scripts/gen_bilingual.php <target_slug> <out.xliff> "<ids>"
```

- `<target_slug>` is the language to translate INTO (`en`, `de`, …).
- `<ids>` — **quote them as one comma-separated string** (`"19,58,77"`). zsh does
  not word-split unquoted variables, so an unquoted list arrives as a single
  argument; the script splits on commas/spaces defensively, but quoting is the
  safe habit.

Run once per (post-type, target language) pair. Example for two types × two
languages = four files:

```
wp eval-file .../gen_bilingual.php en /out/vehicles_fr-en.xliff  "$VEH_IDS"
wp eval-file .../gen_bilingual.php de /out/vehicles_fr-de.xliff  "$VEH_IDS"
wp eval-file .../gen_bilingual.php en /out/elements_fr-en.xliff  "$GPE_IDS"
wp eval-file .../gen_bilingual.php de /out/elements_fr-de.xliff  "$GPE_IDS"
```

**Alternative** — if the user already exported an XLIFF from the wp-admin bulk
"Export" action (empty `post_content` targets) and just wants it filled:

```
wp eval-file /abs/path/scripts/fill_xliff.php <in.xliff> <out.xliff>
```

`fill_xliff.php` reads the target language from the file's own `trgLang`.

### 4. Verify and report
Each script prints a summary like
`10 posts, 440/440 post_content targets filled (0 without translation, 0 divergent)`.
Then sanity-check the output:

- `xmllint --noout <out.xliff>` — must be well-formed.
- Spot-check that a `post_content` `<target>` holds real target-language text
  and that Polylang-owned fields (title/ACF/terms) are still populated.

Report coverage plainly, distinguishing the **three** reasons a target can stay
empty — only the first is expected:
1. **filled** — translation existed and aligned (the goal).
2. **no translation** — the source has no linked translation in that language;
   nothing to export. This is real missing content, not an export fault.
3. **divergent** — the translation exists but its block structure no longer
   matches the source (e.g. the source page was rebuilt in GenerateBlocks while
   the translation stayed on `core/*` blocks). The script refuses to guess and
   leaves it empty, printing a warning with the segment counts. Flag these for
   manual re-translation / resync rather than forcing a (wrong) pairing.

Never silently drop the "divergent" and "no translation" buckets — surfacing
them is often the most useful part of the result.

## How the fill stays correct (do not weaken this)

`post_content` is filled by re-running Polylang's **own** segmentation walker
(`PLL_Translation_Walker_Factory`) on both the source and the translated post to
build a **source-text → translation map**, then matching each XLIFF unit by its
own `<source>` text. Matching by text (not by position) is deliberate: Polylang
**deduplicates** repeated segments in the export (e.g. a section that appears
twice in a privacy policy / T&C), so a positional pairing would drift. The map
is only built when the two segment counts match; otherwise the structures
diverged and any pairing would be unreliable, so the post is left unfilled and
flagged. A source that maps to two *different* translations is left unresolved
for safety. These guards are what make the output trustworthy — keep them.

## Importing back
The generated files are byte-compatible with Polylang's importer (they *are*
Polylang exports, only with targets added). Import via wp-admin **Languages →
Tools → Import**, or Polylang's import flow. The `srcLang`/`trgLang` come from
the file, so filenames are cosmetic — but descriptive names
(`vehicles_fr-de_BILINGUE.xliff`) help the user.

## Gotchas (learned the hard way)
- **Load posts by ID, not `get_posts(post_type=>'any')`** — `'any'` silently
  drops non-public CPTs and anything flagged `exclude_from_search`. The scripts
  already use `array_map('get_post', $ids)`.
- **zsh vs bash word-splitting** — pass IDs as a quoted comma-separated string.
- **Absolute paths** for every `wp eval-file` argument.
- **CDATA + block CSS** — targets are written as `CDATA`, preserving the
  `var(--…)` and HTML inside GenerateBlocks markup. If you ever write block
  content back to the DB (not done here), remember GenerateBlocks needs
  `wp_slash()` or `var(--…)` CSS breaks.

## Reference
- `references/internals.md` — the Polylang export call graph, why only
  post_content is empty, the programmatic-export recipe, and the segmentation
  walker details. Read it when adapting the scripts (new field types, other
  block plugins, term-only exports) or debugging an unexpected empty target.
