# 3-Tier Pricing Section — Notes

Built with **GenerateBlocks 2.x** (`element` / `text` blocks only — no legacy
Container/Grid/Headline/Button blocks). The markup is paste-ready: all styling
ships inside each block's precomputed `css` attribute, so it renders styled the
moment you paste it.

## How to apply it

1. Open the page/post in the block editor.
2. Options (⋮, top-right) → **Code editor** (or ⌘⇧Alt+M).
3. Paste the full contents of `pricing.html`.
4. Switch back to **Visual editor** (lets GB re-validate) → **Save**.

If you want this on several pages, paste it once, select all, and convert it to
a reusable **pattern**, or place it in a GP Premium **Element**.

## Design rationale

- **Theme variables, not hardcoded colors.** Everything uses the GeneratePress
  global palette (`var(--base)`, `--base-2`, `--base-3`, `--contrast`,
  `--contrast-2/3`, `--accent`). Re-skin the whole section by changing the
  palette in Appearance → Customize → Colors. The accent is used sparingly —
  only the badge, the Pro CTA, and the checkmarks — so it actually signals
  "this is the action."

- **Middle plan highlighted as "Most popular."** The Pro card is visually
  promoted three ways, the standard SaaS convention: (1) a dark inverted card
  (`--contrast` background) that pops against the light `--base-2` section,
  (2) a deeper shadow + slight `scale(1.04)` on desktop, and (3) a pill badge
  pinned to the top edge. An `aria-label="Pro plan, most popular"` makes the
  emphasis available to screen readers, not just sighted users.

- **Consistent system.** One spacing scale (8/16/24/32/40/64/112px), one radius
  (16px cards, 10px buttons), one type ramp. Section padding 112px desktop →
  64px mobile. Card padding is identical across tiers (Pro gets a touch more top
  padding to make room for the badge).

- **Tiered copy.** Each tier "includes everything in the one below, plus…" — the
  standard good-better-best ladder. Prices: Starter $0 (free), Pro $12/user/mo,
  Enterprise "Custom" with a *Talk to sales* CTA instead of self-serve signup,
  which is correct for the enterprise motion.

- **Responsive.** 3-column grid on desktop, collapses to a single centered
  column (max 440px) at ≤1024px so the cards never get cramped. The Pro
  `scale()` only applies ≥1025px so the stacked mobile view stays flush.

- **Accessibility & polish.** Real heading order (`h2` section title, `h3` per
  plan). Every CTA has both `:hover` and `:focus-visible` states. Hover lift on
  the outer cards is subtle (4px, 200ms). Checkmarks are CSS `::before` content
  so they need no extra markup or icon font.

## Easy customizations

- **Prices / features:** edit the `<span>`/`<li>` text directly in the editor.
- **Button links:** the CTAs point to `#signup`, `#signup-pro`, `#contact-sales`
  — repoint these `href`s to your real signup and sales pages.
- **Swap the highlighted tier:** the "most popular" treatment lives entirely on
  the middle card; move the badge span + the dark-card styles to another card if
  your hero plan changes.
