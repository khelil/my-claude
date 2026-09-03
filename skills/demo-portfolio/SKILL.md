---
name: demo-portfolio
description: Create a portfolio demo of a website - capture 6 key desktop screens and 6 mobile screens, then wrap each screenshot in realistic device mockups (MacBook frame for desktop, iPhone frame for mobile). Use this whenever the user asks for a "demo portfolio", "démo portfolio", "portfolio demo of a site", "device mockups", "mettre le site dans un iPhone/MacBook", "screenshots pour le portfolio", or wants presentation-ready framed captures of a website - even if they don't say the word "demo".
---

# Demo Portfolio

Produce presentation-ready device mockups of a website: 6 key screens captured
on desktop wrapped in a MacBook frame, and 6 on mobile wrapped in an iPhone
frame.

## Requirements

- A browser automation tool (Playwright MCP or claude-in-chrome) to take
  viewport screenshots.
- `python3` with Pillow (`pip install Pillow` if missing) for the framing step.

## Workflow

### 1. Identify the site and the 6 key screens

Ask for the URL only if it isn't obvious from context (a dev server already
running, the project in the working directory, or a URL the user gave). A local
build/preview server is fine and often better (no cookie banners, latest code).

Pick the 6 most representative screens. For a typical site: home, main product
or services page, a portfolio/work detail, a blog post or content page, about,
contact. Adapt to what the site actually has - the goal is variety (different
layouts, colors, content types), not completeness. Use the same 6 URLs for
desktop and mobile unless a page only makes sense on one device.

### 2. Dismiss cookie banners BEFORE capturing anything

Live sites (especially EU ones) show a cookie consent banner or floating
widget on first visit, and it will photobomb every screenshot. Before the
first capture:

1. Load the home page, take an accessibility snapshot, and look for a consent
   dialog/banner (Axeptio, Didomi, OneTrust, Cookiebot, tarteaucitron...).
2. **Click its "Accept" / "Accept all" / "Tout accepter" button** — an actual
   click on the button, which stores the consent and removes the banner for
   the whole browsing session. If the widget is collapsed, expand it first
   ("Manage preferences") to reach the accept button. Don't settle for hiding
   the element with JavaScript: the widget can re-render on the next
   navigation, and some sites overlay a backdrop that JS-hiding leaves behind.
3. Verify on the first screenshot that no banner, badge or floating cookie
   icon is visible. If one is, deal with it before capturing the remaining
   screens — every capture after the first inherits the same session, so
   fixing it once fixes it everywhere.

Some CMPs (Axeptio notably) leave a small floating badge in a corner even
after consent. It is not part of the site's design, so hide it right before
each capture with a JS evaluate such as
`document.querySelectorAll('[id^="axeptio"]').forEach(e => e.style.display = 'none')`
(re-run it after every navigation - the badge re-renders on each page load).

Local dev/preview servers usually have no banner - this step is then a no-op.

### 3. Capture 6 desktop + 6 mobile screenshots

Take **viewport** screenshots, not full-page: each capture becomes one device
screen, so it must have the aspect ratio of a screen, not a scroll of the whole
page.

- Desktop: resize the browser viewport to **1440x900** (matches the MacBook
  frame's 16:10 screen), screenshot each of the 6 URLs.
- Mobile: resize the viewport to **390x844** (iPhone screen ratio), screenshot
  the same URLs. If the browser tool supports device emulation, enable it so
  the site serves its mobile layout; a plain 390px-wide viewport also works for
  responsive sites.

For screens whose interesting content sits below the fold (e.g. a pricing
section), scroll to the section before capturing - the capture is still one
viewport tall.

Save raw captures in the project as `demo/raw/desktop-<slug>.png` and
`demo/raw/mobile-<slug>.png`, where `<slug>` names the screen (`home`,
`services`, ...).

### 4. Wrap each capture in its device frame

Run the bundled script once per screenshot (frames are in this skill's
`assets/` directory):

```bash
python3 <skill-dir>/scripts/frame_screenshot.py \
  <skill-dir>/assets/macbook-frame.png demo/raw/desktop-home.png demo/framed/desktop-home.png

python3 <skill-dir>/scripts/frame_screenshot.py \
  <skill-dir>/assets/iphone-frame.png demo/raw/mobile-home.png demo/framed/mobile-home.png
```

Use `macbook-frame.png` for the 6 desktop captures and `iphone-frame.png` for
the 6 mobile ones. The script auto-detects the transparent screen hole in the
frame, cover-fits the screenshot behind it (top-aligned) and keeps the bezel,
rounded corners and Dynamic Island on top. Output PNGs keep transparency
outside the device, so they can be placed on any background.

A simple loop works well:

```bash
for f in demo/raw/desktop-*.png; do
  python3 <skill-dir>/scripts/frame_screenshot.py \
    <skill-dir>/assets/macbook-frame.png "$f" "demo/framed/$(basename ${f#demo/raw/})"
done
```

### 5. Verify and deliver

Open at least one framed desktop and one framed mobile output and look at
them - check the screenshot is sharp, correctly aligned in the screen, and that
no cookie banner, dev overlay or error state was captured. Re-capture any bad
screen rather than shipping it.

Deliver by listing the 12 files in `demo/framed/` and showing one example of
each device.

### 6. Optional: presentation boards

When the user wants the mockups assembled on a single image ("planche",
"board", "presentation"), use the bundled board generator:

```bash
python3 <skill-dir>/scripts/make_board.py demo/framed demo/board.png --title "site.com"
```

Variants combine freely via flags:

- `--layout pairs` (default): 3x2 grid, each screen shown as a laptop with
  its iPhone overlapping the corner - the full showcase.
- `--layout desktop` / `--layout mobile`: one board per device, 3x2 grid of
  laptops only or iPhones only.
- `--layout vertical`: 1080px-wide portrait board (Instagram/LinkedIn):
  hero laptop on top, a row of three iPhones below.
- `--dark`: dark background (#17171a) instead of light gray - pick whichever
  contrasts best with the site's dominant colors (dark sites often look
  better on the light board and vice versa; when in doubt generate both and
  compare).
- `--screens home,pricing,blog`: choose and order the screens explicitly;
  by default all captures appear in capture order (home first).

Name outputs after their variant (`board.png`, `board-dark.png`,
`board-desktop.png`, `board-mobile.png`, `board-vertical.png`). Always open
the generated boards to check nothing overlaps a label and that theme
contrast works before delivering.
