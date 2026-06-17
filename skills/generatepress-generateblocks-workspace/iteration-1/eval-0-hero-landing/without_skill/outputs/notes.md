# LedgerLoop hero — notes

## How to paste it in
1. Open the page in the WordPress block editor.
2. Top-right **⋮ (Options) → Code editor** (or `⌘⇧Alt+M`).
3. Paste the entire contents of `hero.html`.
4. Switch back to **Visual editor** and **Save**. It renders styled immediately
   because the CSS ships inside the block markup.

Tip: if you'll reuse this hero across pages, select it and convert it to a
synced/unsynced **pattern** rather than re-pasting.

## What's in the section
- **Eyebrow pill** — "Automated invoice reconciliation" (sets context fast).
- **H1 headline** — "Close the books faster. Let LedgerLoop match every invoice
  for you." Benefit-led, names the product, one page-level H1.
- **Subheadline** — one muted sentence, capped to ~60ch for readability.
- **Two CTAs** — primary **Start free trial** (`/signup`) + secondary outline
  **Book a demo** (`/demo`).
- **Trust line** — "No credit card required · 14-day free trial · SOC 2 compliant".

Swap the copy and the `href`s (`/signup`, `/demo`) for your real URLs.

## Design rationale
- **Colors come from the GeneratePress global palette variables**
  (`--base`, `--base-2`, `--base-3`, `--contrast`, `--contrast-2`,
  `--contrast-3`, `--accent`) — nothing hardcoded. The accent appears on exactly
  one element (the primary button + the eyebrow text), so it actually means
  "click here". Set/adjust the palette in **Appearance → Customize → Colors →
  Global Color Palette** and the hero re-themes itself. For a fintech/accounting
  tool a calm, trustworthy `--accent` (a blue or teal) reads best.
- **Spacing** is from a single 4/8 scale (8/16/24 for gaps, 64/128 for section
  padding). Nothing arbitrary.
- **Type** uses fluid `clamp()` so the H1 scales from ~2.25rem on mobile to
  3.75rem on desktop without a media query; tight `-0.02em` tracking and 1.1
  line-height on the heading, relaxed 1.6 on body.
- **Centered hero** layout — appropriate for a short, punchy value statement.
- **Section background** is `--base-2` with a `--base-3` bottom border so the
  hero separates cleanly from whatever section follows.

## Responsive & accessibility
- Mobile (`max-width:767px`): section padding drops 128px → 64px and the two
  buttons stack full-width.
- Buttons are 52px tall (>44px touch target) with both `:hover` (subtle 2px lift)
  and `:focus-visible` (visible outline) states.
- Logical heading order (single H1), body capped to a readable measure, text
  colors drawn from the neutral palette for contrast.

## If a variable doesn't resolve
These are GeneratePress 3.x defaults. If your live palette uses different slot
names, the easiest fix is to open any block in the editor and re-pick the color
from the palette UI — GB will rewrite the `css` for you.
