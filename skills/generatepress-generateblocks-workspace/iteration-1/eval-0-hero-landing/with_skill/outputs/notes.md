# LedgerLoop hero — notes

## How to paste it in
1. Edit the homepage in the WordPress block editor.
2. Click the ⋮ (Options) menu top-right → **Code editor** (or ⌘⇧Alt+M).
3. Paste the entire contents of `hero.html` at the top of the content.
4. Switch back to **Visual editor** and **Save/Update**.

It renders fully styled the moment you paste it — the CSS is baked into each
block — so you don't need any extra stylesheet. If you tweak a block in the
visual editor afterward, GenerateBlocks just recomputes the CSS, which is fine.

## What's in it
- **Eyebrow pill:** "Automated invoice reconciliation" — orients the visitor in one glance.
- **Headline (H1):** "Close the books in hours, not weeks." — outcome-led, the single page H1.
- **Subheadline:** one sentence naming the product, the audience (small accounting
  firms), and the payoff. Capped at ~54ch so it stays readable.
- **Two CTAs:** primary **Start free trial** (accent fill) + secondary **Book a demo**
  (ghost/outline). Update the `href`s — currently `/signup` and `/demo`.
- **Trust microcopy:** "No card required · 14-day free trial · SOC 2 ready."
- **Supporting visual:** a lightweight, CSS-only "reconciliation" card mockup
  (matched rows + one flagged discrepancy) instead of a stock photo — it shows
  the product's value and never blocks the headline for contrast.

## Design rationale
- **Tone:** calm and trustworthy, appropriate for accounting/finance buyers — no
  gradients or busy imagery.
- **Layout:** asymmetric 60/40 split (copy left, product card right) reads more
  intentional than dead-centred. It collapses to a single stacked, centred column
  at ≤1024px, and the buttons go full-width below 767px.
- **Type:** fluid `clamp()` headline so it scales down cleanly on mobile; one H1,
  muted secondary/tertiary text for hierarchy via contrast, not bulk bolding.
- **Color:** everything is driven by the GeneratePress global palette variables
  (`--base`, `--base-2/3`, `--contrast`, `--contrast-2/3`, `--accent`, `--accent-2`).
  The accent appears only on the primary button, links, and the matched/flagged
  status labels — the one secondary accent (`--accent-2`) marks the flagged row.
  Set/adjust these in **Appearance → Customize → Colors → Global Color Palette**
  and the hero re-themes itself.
- **Spacing:** all values come from a 4/8 scale (8/12/16/24/28/48/64) plus fluid
  section padding (`clamp(64px,9vw,128px)`).
- **Accessibility/polish:** buttons have both `:hover` (subtle 2px lift) and
  `:focus-visible` states, ≥44px tap targets, logical heading order.

## Quick edits
- Swap the copy by editing the visible text inside each `<h1>/<p>/<span>`.
- Change button links via the `href` in the two `<a>` blocks.
- Don't like the card mockup? Delete that second inner `div` (the one whose first
  child says "Reconciliation — March") and change the grid to one column, or drop
  a GenerateBlocks Media block / screenshot in its place.

## Tip
If this hero (or a CTA/header) should appear on more than one page, build it once
as a **GP Premium Element** or a reusable pattern instead of pasting it per page.
