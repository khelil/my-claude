# Pricing section — notes

## What this is
A 3-tier pricing section (Starter / Pro / Enterprise) for a project-management
app, built as GenerateBlocks 2.x markup. The **Pro** plan is highlighted as the
"Most popular" option. Paste-ready: the compiled `css` ships inside the block
delimiters, so it renders styled immediately.

## How to apply
1. Open the page/post in the WordPress block editor.
2. Options (⋮, top right) → **Code editor** (or ⌘⇧Alt+M).
3. Paste the entire contents of `pricing.html`.
4. Switch back to **Visual editor** and **Save**.

If you'll reuse it across pages, paste it once and convert to a synced/unsynced
pattern (or drop it into a GP Premium Element).

## Design rationale
- **Palette variables, not hex.** Everything is driven by the GeneratePress
  global palette (`--base`, `--base-2`, `--base-3`, `--contrast`, `--contrast-2`,
  `--contrast-3`, `--accent`). The section will re-theme automatically if you
  change the palette in Customizer → Colors. The accent appears only on the
  badge, primary CTA, links, and checkmarks — so it actually means something.
- **Highlighting the middle plan.** Pro gets a 2px accent border, a deeper
  shadow, a centered "Most popular" pill badge straddling the top edge, and is
  scaled up 4% so it visually steps forward from its neighbors. The grid uses
  `align-items:center` so the taller card balances the row.
- **Spacing & type discipline.** All values come from a 4/8 scale
  (8/12/16/24/32/40/56/112px). Section padding 112px desktop → 64px mobile.
  One H1 lives elsewhere on the page; this section starts at H2 with H3 plan
  names, so heading order stays logical.
- **Feature lists** use a custom `✓` marker (accent color) via `li::before`
  instead of default bullets, with "Everything in <lower tier>" framing to imply
  the upgrade ladder.
- **Interaction.** Cards lift on hover; buttons have both `:hover` and
  `:focus-visible` states (keyboard accessibility + polish). Transitions are
  fast (200ms) and subtle.

## Responsive
- Desktop/tablet ≥1025px: three equal columns, Pro scaled up.
- ≤1024px: collapses to a single column, max-width 440px, centered. The Pro
  card's `scale(1.04)` is removed on mobile so it doesn't clip or look oversized;
  it keeps a normal hover lift.

## Easy edits
- **Prices / period:** edit the price `<p>` text; the `/month` suffix is a
  `<span class="gb-price-period">` you can restyle.
- **Make a different plan "most popular":** move the badge span and the accent
  border/shadow/scale styles onto a different card.
- **CTA links:** update the `href` on each button (`/signup`, `/signup?plan=pro`,
  `/contact-sales`).

## If you re-generate
Source tree is `pricing.json`. Rebuild with:
`python3 scripts/gb_build.py pricing.json -o pricing.html`
(run from the skill directory). The script compiles the `css`, escapes `--`
inside comments, and keeps each `uniqueId` in sync with its inner-HTML class —
don't hand-edit those in the HTML.
