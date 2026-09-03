#!/usr/bin/env python3
"""Wrap a website screenshot inside a device frame (iPhone / MacBook mockup).

The frame PNGs have a fully transparent screen area (and transparent outside).
The script flood-fills from the center of the frame to find the screen hole,
fits the screenshot to cover it (center-crop), pastes it behind the frame, and
composites the frame on top - so rounded corners, bezels and the Dynamic
Island stay in front of the screenshot.

Usage:
    python3 frame_screenshot.py <frame.png> <screenshot.png> <output.png>

The screenshot should be a viewport capture matching the device aspect ratio
(e.g. 1440x900 for the MacBook frame, 390x844 for the iPhone frame); any
mismatch is handled with a centered cover-crop (top-aligned, since the top of
a web page matters most).
"""
import sys
from PIL import Image, ImageDraw


def screen_mask(frame: Image.Image) -> Image.Image:
    """Return an L mask (255 = screen hole) found by flood fill from center."""
    alpha = frame.getchannel("A")
    cx, cy = frame.width // 2, frame.height // 2
    if alpha.getpixel((cx, cy)) > 10:
        raise SystemExit(
            "Frame center is not transparent - this frame has no transparent "
            "screen hole. Use a frame PNG with a transparent screen area."
        )
    # Work on a binary copy: hole candidates are 0, everything else 255.
    mask = alpha.point(lambda a: 0 if a <= 10 else 255)
    ImageDraw.floodfill(mask, (cx, cy), 128)
    return mask.point(lambda v: 255 if v == 128 else 0)


def top_notch_height(mask: Image.Image, bbox: tuple) -> int:
    """Height of a camera notch that intrudes from the top edge of the hole.

    MacBook-style frames have a notch attached to the top bezel: the first rows
    of the screen hole are interrupted in the middle. iPhone Dynamic Islands
    float *inside* the screen (detached from the edge), so they yield 0 here
    and are simply left overlapping the screenshot, which looks natural.
    """
    left, top, right, bottom = bbox
    third = (right - left) // 3
    px = mask.load()
    for y in range(top, min(top + (bottom - top) // 4, bottom)):
        gap = any(px[x, y] == 0 for x in range(left + third, right - third))
        if not gap:
            return y - top
    return 0


def compose(frame_path: str, shot_path: str, out_path: str) -> None:
    frame = Image.open(frame_path).convert("RGBA")
    shot = Image.open(shot_path).convert("RGBA")

    mask = screen_mask(frame)
    bbox = mask.getbbox()
    left, top, right, bottom = bbox
    hole_w, hole_h = right - left, bottom - top

    # If the frame's notch hangs from the top bezel (MacBook), letterbox the
    # screenshot below it with a black strip - what macOS fullscreen does -
    # so no page content hides behind the notch.
    notch = top_notch_height(mask, bbox)
    content_top, content_h = top + notch, hole_h - notch

    # Cover-fit: scale so the screenshot fills the content area, then crop.
    scale = max(hole_w / shot.width, content_h / shot.height)
    shot = shot.resize((round(shot.width * scale), round(shot.height * scale)), Image.LANCZOS)
    # Center horizontally, keep the top edge (page tops carry the content).
    x = (shot.width - hole_w) // 2
    shot = shot.crop((x, 0, x + hole_w, content_h))

    canvas = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    if notch:
        black = Image.new("RGBA", (hole_w, notch), (0, 0, 0, 255))
        canvas.paste(black, (left, top), mask.crop((left, top, right, top + notch)))
    canvas.paste(shot, (left, content_top), mask.crop((left, content_top, right, bottom)))
    out = Image.alpha_composite(canvas, frame)
    out.save(out_path)
    print(f"framed: {out_path} ({out.width}x{out.height}, notch={notch}px)")


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit(__doc__)
    compose(*sys.argv[1:4])
