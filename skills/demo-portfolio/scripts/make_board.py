#!/usr/bin/env python3
"""Assemble framed device mockups into a presentation board.

Usage:
    python3 make_board.py <framed-dir> <output.png> --title "site.com"
        [--layout pairs|desktop|mobile|vertical] [--dark]
        [--screens home,platform,pricing]

Layouts:
    pairs    (default) 3x2 grid, each cell = laptop with its iPhone
             overlapping the bottom-right corner. The full showcase.
    desktop  3x2 grid of laptop mockups only.
    mobile   3x2 grid of iPhone mockups only.
    vertical 1080px-wide portrait board (social formats): hero laptop on
             top, a row of three iPhones below.

The framed dir must contain desktop-<slug>.png / mobile-<slug>.png files as
produced by frame_screenshot.py. Screen order defaults to file modification
time (= capture order, so the home page comes first); override with
--screens to pick and order slugs explicitly. Labels are derived from slugs
("fraud-investigation" -> "Fraud investigation").
"""
import argparse
import os
import sys
from PIL import Image, ImageDraw, ImageFont

LIGHT = {"bg": (240, 240, 242, 255), "text": (20, 20, 25, 255), "muted": (110, 110, 118, 255)}
DARK = {"bg": (23, 23, 26, 255), "text": (240, 240, 242, 255), "muted": (150, 150, 158, 255)}


def font(size, bold=True):
    names = ["/System/Library/Fonts/Supplemental/Arial Bold.ttf"] if bold else \
            ["/System/Library/Fonts/Supplemental/Arial.ttf"]
    names += ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            pass
    return ImageFont.load_default()


def label_of(slug):
    return slug.replace("-", " ").capitalize()


def discover(framed_dir, prefix, wanted):
    files = {}
    for f in os.listdir(framed_dir):
        if f.startswith(prefix + "-") and f.endswith(".png"):
            slug = f[len(prefix) + 1:-4]
            files[slug] = os.path.join(framed_dir, f)
    if wanted:
        missing = [s for s in wanted if s not in files]
        if missing:
            sys.exit(f"missing {prefix} captures for: {', '.join(missing)}")
        return [(s, files[s]) for s in wanted]
    # mtime ordering is fragile (re-framing in a loop makes it alphabetical),
    # so at least pin the home page first - it's the hero of vertical boards.
    items = sorted(files.items(), key=lambda kv: os.path.getmtime(kv[1]))
    for hero in ("home", "index", "accueil"):
        if hero in files:
            items = [(hero, files[hero])] + [kv for kv in items if kv[0] != hero]
            break
    return items


def draw_title(board, draw, title, subtitle, theme):
    t_font, s_font = font(64), font(36, bold=False)
    draw.text((70, 55), title, font=t_font, fill=theme["text"])
    if subtitle:
        x = 70 + draw.textlength(title, font=t_font) + 30
        draw.text((x, 78), subtitle, font=s_font, fill=theme["muted"])


def grid_board(desktop, mobile, title, theme, layout):
    """pairs / desktop / mobile layouts: 3x2 grid."""
    COLS = 3
    ROWS = max(1, -(-max(len(desktop), len(mobile)) // COLS))
    PAD, LABEL_H, TITLE_H = 60, 70, 160

    if layout == "mobile":
        PHONE_H = 760
        p0 = Image.open(mobile[0][1])
        phone_w = round(p0.width * PHONE_H / p0.height)
        cell_w, cell_h = phone_w + PAD * 2, PHONE_H + PAD * 2 + LABEL_H
        items = mobile
    else:
        LAPTOP_W = 900
        l0 = Image.open(desktop[0][1])
        LAPTOP_H = round(l0.height * LAPTOP_W / l0.width)
        overhang = 60 if layout == "pairs" else 0
        cell_w = LAPTOP_W + PAD * 2 + overhang
        cell_h = LAPTOP_H + PAD * 2 + LABEL_H + (40 if layout == "pairs" else 0)
        items = desktop

    W, H = cell_w * COLS, TITLE_H + cell_h * ROWS + 60
    board = Image.new("RGBA", (W, H), theme["bg"])
    draw = ImageDraw.Draw(board)
    draw_title(board, draw, title, "— demo portfolio", theme)

    mobile_by_slug = dict(mobile)
    for i, (slug, path) in enumerate(items):
        col, row = i % COLS, i // COLS
        x0, y0 = col * cell_w + PAD, TITLE_H + row * cell_h + PAD
        if layout == "mobile":
            img = Image.open(path)
            img = img.resize((round(img.width * PHONE_H / img.height), PHONE_H), Image.LANCZOS)
            board.alpha_composite(img, (x0, y0))
            label_y = y0 + PHONE_H + 25
        else:
            laptop = Image.open(path).resize((LAPTOP_W, LAPTOP_H), Image.LANCZOS)
            board.alpha_composite(laptop, (x0, y0))
            label_y = y0 + LAPTOP_H + (45 if layout == "pairs" else 25)
            if layout == "pairs" and slug in mobile_by_slug:
                ph_h = round(LAPTOP_H * 0.78)
                phone = Image.open(mobile_by_slug[slug])
                phone = phone.resize((round(phone.width * ph_h / phone.height), ph_h), Image.LANCZOS)
                board.alpha_composite(phone, (x0 + LAPTOP_W - phone.width // 2 - 40,
                                              y0 + LAPTOP_H - ph_h + 30))
        draw.text((x0 + 10, label_y), label_of(slug), font=font(34), fill=theme["text"])
    return board


def vertical_board(desktop, mobile, title, theme):
    """1080px-wide portrait board: hero laptop + a row of 3 iPhones."""
    W, PAD = 1080, 50
    laptop = Image.open(desktop[0][1])
    lw = W - PAD * 2
    laptop = laptop.resize((lw, round(laptop.height * lw / laptop.width)), Image.LANCZOS)

    # phones: the 3 screens after the hero (fall back to hero if too few)
    phone_slugs = [s for s, _ in mobile if s != desktop[0][0]][:3] or [mobile[0][0]]
    ph_w = (W - PAD * 2 - 40 * (len(phone_slugs) - 1)) // len(phone_slugs)
    phones = []
    for slug in phone_slugs:
        p = Image.open(dict(mobile)[slug])
        phones.append(p.resize((ph_w, round(p.height * ph_w / p.width)), Image.LANCZOS))

    TITLE_H = 130
    H = TITLE_H + laptop.height + 30 + max(p.height for p in phones) + PAD
    board = Image.new("RGBA", (W, H), theme["bg"])
    draw = ImageDraw.Draw(board)
    t_font = font(52)
    draw.text((PAD, 45), title, font=t_font, fill=theme["text"])
    draw.text((PAD + draw.textlength(title, font=t_font) + 20, 60),
              "— demo portfolio", font=font(28, bold=False), fill=theme["muted"])

    board.alpha_composite(laptop, (PAD, TITLE_H))
    x = PAD
    for p in phones:
        board.alpha_composite(p, (x, TITLE_H + laptop.height + 30))
        x += ph_w + 40
    return board


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("framed_dir")
    ap.add_argument("output")
    ap.add_argument("--title", required=True)
    ap.add_argument("--layout", choices=["pairs", "desktop", "mobile", "vertical"], default="pairs")
    ap.add_argument("--dark", action="store_true")
    ap.add_argument("--screens", help="comma-separated slugs in display order")
    args = ap.parse_args()

    wanted = args.screens.split(",") if args.screens else None
    desktop = discover(args.framed_dir, "desktop", wanted)
    mobile = discover(args.framed_dir, "mobile", wanted)
    if not desktop and not mobile:
        sys.exit("no framed captures found in " + args.framed_dir)
    theme = DARK if args.dark else LIGHT

    if args.layout == "vertical":
        board = vertical_board(desktop, mobile, args.title, theme)
    else:
        board = grid_board(desktop, mobile, args.title, theme, args.layout)
    board.convert("RGB").save(args.output, quality=95)
    print(f"board: {args.output} ({board.width}x{board.height}, {args.layout}, {'dark' if args.dark else 'light'})")


if __name__ == "__main__":
    main()
