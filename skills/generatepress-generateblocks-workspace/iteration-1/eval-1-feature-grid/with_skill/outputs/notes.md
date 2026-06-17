# "Why choose us" feature grid — notes

## How to paste it in
1. Open the page in the WordPress block editor.
2. Top-right ⋮ (Options) → **Code editor** (or ⌘⇧Alt+M).
3. Paste the full contents of `section.html`.
4. Switch back to **Visual editor** (so GenerateBlocks re-validates the blocks) and Save.

It renders fully styled the moment you paste it — the compiled CSS ships inside
the block markup. If you reuse this section on several pages, select it after
pasting and convert it to a synced pattern instead of pasting per page.

## What's in it
A full-width `section` (band on `var(--base-2)`) with a centered header (eyebrow +
H2 + one-line subhead) and a 4-card grid:

1. Gentle, pain-free dentistry
2. Advanced technology
3. Experienced, caring team
4. Flexible, easy scheduling

Each card has an inline SVG icon in a soft accent-tinted circle, an H3 title, and
a 2-line description.

## Design rationale
- **Theme variables, not hex.** Colors come from the GeneratePress global palette
  (`--base`, `--base-2`, `--base-3`, `--contrast`, `--contrast-2`, `--accent`).
  Re-theming the palette in the Customizer restyles this section automatically.
  The only literal color is the soft shadow (`rgba(15,23,42,.08)`), which is
  palette-agnostic by design.
- **Accent used sparingly** — eyebrow text, the icon circles, and the hover
  border. Everything else is neutral, so the brand color actually means something.
- **Spacing from one scale** (16 / 24 / 32 / 56 / 96px). Section padding is
  96px desktop, 56px mobile. Card gap 24px, card padding 32px.
- **Icons inherit color.** The SVGs use `stroke="currentColor"` and the circle
  sets `color: var(--accent)`, so changing the accent recolors the icons too.
  They're marked `aria-hidden` because the H3 already conveys meaning.
- **Hover is restrained:** 4px lift + soft shadow + accent border, 200ms eased.

## Responsiveness
- The grid is `repeat(auto-fit, minmax(240px, 1fr))`, so it naturally flows from
  4 → 2 → 1 columns as the viewport narrows, even without media queries.
- An explicit mobile breakpoint (`@media max-width:767px`) forces a single column,
  tightens the gap to 16px, and reduces section padding to 56px so it stacks
  cleanly on phones.
- The H2 uses `clamp(2rem, 4vw, 2.75rem)` so the display type scales down fluidly.

## Easy customizations
- **Swap copy/icons:** edit each card's H3, paragraph, and the `<svg>` inside the
  `shape` block. Any 24×24 stroke icon (e.g. Lucide/Feather) drops in cleanly if
  it keeps `stroke="currentColor"`.
- **Number of cards:** add or remove a card `element`; `auto-fit` handles the
  layout. For exactly 3 across, change `minmax(240px,1fr)` accordingly.
- **Accent tint strength:** the icon circle uses `color-mix(... 12% ...)`. If your
  browser-support floor predates `color-mix`, replace it with a fixed light tint
  or `var(--base-3)`.
