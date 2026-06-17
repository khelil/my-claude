# "Why Choose Us" Feature Grid — Notes

## How to use
1. In the WordPress block editor, open the page where you want the section.
2. Add a block, switch the editor to **Code Editor** mode (top-right three-dot menu → "Code editor"), or use the list view.
3. Paste the full contents of `section.html`.
4. Switch back to Visual editor. The block is built with native **GenerateBlocks 2.x** blocks (`generateblocks/element` + `generateblocks/text`), so it stays fully editable — text, colors, spacing, and icons can all be changed in the UI.

> Requires GenerateBlocks 2.x. The markup uses the 2.x `styles` + `css` schema (`gb-element-*` / `gb-text-*` class names). It does not need GenerateBlocks Pro.

## Structure
- `section` → outer band with soft padding and a light blue background (`#f6fafd`).
- `container` → max-width 1100px, centered, holds the heading block and the grid.
- Intro: eyebrow label ("Why Choose Us") + H2 + supporting paragraph, all centered.
- `grid` → CSS Grid with 4 equal columns on desktop.
- 4 cards, each = icon chip + H3 title + description paragraph.

## Responsive behavior
The grid uses media queries baked into the block's `css`:
- **Desktop (> 1024px):** 4 columns.
- **Tablet (601–1024px):** 2 columns.
- **Mobile (≤ 600px):** 1 column (full-width stacked cards).

This degrades cleanly without horizontal scroll. Adjust the breakpoints in each card/grid `css` field if your theme uses different ones.

## Design rationale
- **Dental-appropriate palette:** clinical, trustworthy blues (`#0a9bd6` accent, `#0f2a3d` dark text, `#5b7385` muted body) on near-white. Reads clean and medical rather than flashy.
- **Icon chips** (rounded square with tinted background) give each card a clear focal point and consistent rhythm. Icons are inline SVG (tooth, shield-check, clock, heart) using `currentColor` so they inherit the accent color — recolor by changing the chip `color` value.
- **Cards** use a subtle border + soft shadow + 16px radius for a modern, approachable feel, plus a gentle hover lift for interactivity (desktop).
- **Vertical type scale** (eyebrow → H2 → sub → cards) creates clear hierarchy and scannability.

## Easy customizations
- **Accent color:** replace `#0a9bd6` (icon color) and `#e6f6fc` (chip background) throughout.
- **Copy:** edit the H2, subheading, and each card's title/description directly in the editor.
- **Icons:** swap the inline `<svg>` inside each `wcu-ico-*` element, or replace with the GenerateBlocks icon picker if you prefer managing icons in the UI.
- **Columns:** change `repeat(4, 1fr)` in the grid `css` to `repeat(3, 1fr)` etc. if you add/remove cards.
