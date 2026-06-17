# Designing stunning sites — the principles behind the markup

Great GenerateBlocks output is 20% knowing the block format and 80% design
judgment. The format is solved by the build script; this file is the judgment.
The goal is work that looks like a senior designer made deliberate choices — not
"AI slop": even spacing everywhere, three competing accent colors, centered text
walls, and stock-photo gradients.

These are principles, not a single look. Adapt the *specifics* to each brief
(a law firm and a techno label want opposite energy) while keeping the
*discipline* constant.

## 1. Establish a system first, then build

Before emitting a single block, decide the system and reuse it everywhere.
Inconsistency is the #1 tell of amateur work.

- **Spacing scale.** Pick one scale and only use values from it. A good default
  is a 4/8-based ramp: `4, 8, 12, 16, 24, 32, 48, 64, 96, 128px`. Section
  vertical padding lives at the top of the ramp (e.g. 96–128px desktop, 48–64px
  mobile); intra-component gaps lower down. Never invent `37px`.
- **Type scale.** One ratio (≈1.25 minor third or 1.333 perfect fourth). E.g.
  `14, 16, 18, 20, 25, 31, 39, 49, 61px`. Body 16–20px. Exactly one page-level
  H1. Don't bold-and-enlarge everything — hierarchy comes from *contrast*, so
  most things are quiet and few things shout.
- **Line length & leading.** Body copy 60–75ch max width (`maxWidth:"65ch"`),
  line-height ~1.5–1.7. Headings tighter (1.05–1.2). Long full-width paragraphs
  are a readability and aesthetic failure.
- **Color.** Drive everything from the GeneratePress global palette variables
  (`var(--base)`, `--base-2`, `--base-3`, `--contrast`, `--contrast-2`,
  `--contrast-3`, `--accent`, `--accent-2`). See `generatepress.md`. This keeps
  the whole site coherent and re-themable. Rule of thumb: a neutral
  foreground/background pair carries ~90% of the page; the accent appears on
  maybe 10% (primary buttons, links, one highlight) so it actually *means*
  something. Avoid more than one accent unless the brief is deliberately playful.
- **Radius & borders.** One corner radius (e.g. 8–12px) reused on cards, inputs,
  images, buttons. Prefer subtle borders (`1px solid var(--base-3)`) or soft
  shadows over heavy lines — rarely both on the same element.

## 2. Composition: rhythm, not uniformity

- **Vertical rhythm.** A page is a stack of full-width `section` elements with
  generous, *consistent* vertical padding. Alternate background tone
  (`--base` ↔ `--base-2`) to separate sections without hard rules.
- **Constrain content width.** Sections go edge-to-edge; their inner content is
  capped (`maxWidth:"var(--gb-container-width)"`, `marginLeft/Right:"auto"`).
  Don't let text run the full viewport on large screens.
- **Asymmetry beats dead-center.** A 60/40 or 7/5 split (image one side, text the
  other) reads more designed than everything centered. Reserve centered layouts
  for short hero statements and CTAs.
- **Whitespace is the feature.** When unsure, add space, remove elements. Crowded
  is the most common failure. Let a few elements breathe rather than filling
  every pixel.
- **Alignment & grids.** Everything aligns to a shared edge or grid. Use
  `display:grid` with `gridTemplateColumns:"repeat(auto-fit,minmax(260px,1fr))"`
  and a `gap` from the scale for card rows — it's responsive without media queries.

## 3. Responsive by default

Every layout must hold up on mobile. With GB, that means adding the mobile
breakpoint inside `styles`:
- Multi-column flex/grid → stack: `"@media (max-width:767px)":{"flexDirection":"column"}`
  or drop grid columns to `1fr`.
- Reduce section padding on mobile (e.g. 128px → 56px) and step display type
  down (use `clamp()` for fluid headings: `fontSize:"clamp(2rem,5vw,3.75rem)"`).
- Never rely on fixed widths that overflow narrow screens; prefer `%`, `fr`,
  `minmax`, `clamp`.

## 4. Motion & interactivity — restrained

- Add a `transition` on anything that changes on hover, and keep hover effects
  subtle: a slight lift (`transform:"translateY(-4px)"`), shadow deepen, or color
  shift. Fast (150–250ms), eased. No bouncing, no spinning.
- Buttons and links must have a visible hover **and** focus state
  (`&:focus-visible`) — it's both UX and polish.
- Reserve scroll/entrance animation for at most one or two moments; pervasive
  animation feels cheap and hurts performance.

## 5. Accessibility = quality

Not optional, and it improves the design:
- Real heading order (one H1, then H2/H3 nested logically) — also helps SEO.
- Color contrast ≥ 4.5:1 for body text. The neutral palette usually handles this;
  verify accent-on-color combos.
- Every `media` image needs meaningful `alt` (empty `alt=""` only for purely
  decorative shapes).
- Interactive targets ≥ ~44px tall; visible focus states.

## 6. Section patterns (starting points, not templates)

Reach for these shapes, then adapt proportions, color, and copy to the brief:

- **Hero:** one tight value-proposition H1, a one-line subhead (muted color,
  capped width), one primary + optional secondary (ghost/outline) button. Lots of
  space. Optional supporting image or subtle background — never a busy photo
  behind small text without an overlay for contrast.
- **Feature grid:** auto-fit card grid; each card = icon/shape + short heading +
  2–3 lines. Identical card padding and radius; consistent gap.
- **Alternating feature rows:** image + text in a 50/50 (or 60/40) split, the
  side alternating row to row; stacks on mobile.
- **Logo / social proof strip:** muted, evenly spaced, smaller than surrounding
  content — supporting, not shouting.
- **Stats band:** 3–4 big numbers (display type) with small muted labels, on an
  accent or contrast background for a deliberate punch.
- **Testimonial:** generous quote, attribution smaller/muted; one per view or a
  Pro carousel.
- **CTA section:** the one place to use the accent background full-width — short
  imperative headline + a single button. High contrast, lots of padding.
- **Footer:** quiet, organized columns; smaller muted text; clear link grouping.

## 7. Self-check before delivering

- Does every spacing/size value come from the scale?
- Is the accent used sparingly and consistently?
- One H1? Logical heading order? Body capped to a readable measure?
- Does it stack cleanly at 767px? Display type scaled down?
- Hover **and** focus states on interactive elements?
- Could you remove an element or add whitespace and improve it? (Usually yes.)
- Does it look like a specific, intentional brand — or like a generic template?
