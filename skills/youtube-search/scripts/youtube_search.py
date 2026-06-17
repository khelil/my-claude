#!/usr/bin/env python3
"""
youtube_search.py — Search YouTube via yt-dlp and return structured, ranked results.

Two-stage strategy (fast + complete):
  1. A flat search (`ytsearchN:`) fetches candidate video IDs in YouTube's
     native relevance order. This is one cheap network call (~1-2s for dozens).
  2. Full metadata for each candidate is extracted in PARALLEL. This is where
     subscriber count, view count, duration and upload date come from — fields
     a flat search does not include. Parallelism is what keeps this from being
     painfully slow (sequential extraction is ~3-6s *per video*).

Then results are filtered to a recency window, the engagement ratio
(views ÷ subscribers) is computed, relevance order is preserved, and the top N
are formatted for the terminal and/or saved as a Markdown note.

Usage:
  youtube_search.py "<query>" [--count 20] [--months 6] [--scan 60]
                              [--save PATH.md] [--json]

Exit codes: 0 = ok, 2 = yt-dlp missing, 3 = no results at all.
"""

import argparse
import concurrent.futures
import datetime as dt
import json
import shutil
import subprocess
import sys


def log(msg):
    """Progress to stderr so it never pollutes stdout / piped JSON."""
    print(msg, file=sys.stderr, flush=True)


def run_yt_dlp(args):
    """Run yt-dlp and return stdout text (empty string on failure)."""
    try:
        proc = subprocess.run(
            ["yt-dlp", *args],
            capture_output=True, text=True, timeout=120,
        )
        return proc.stdout
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def fetch_candidate_ids(query, scan):
    """Stage 1: flat search → list of video IDs in relevance order."""
    out = run_yt_dlp([
        f"ytsearch{scan}:{query}",
        "--flat-playlist", "--print", "%(id)s", "--no-warnings",
    ])
    return [line.strip() for line in out.splitlines() if line.strip()]


def extract_one(video_id):
    """Stage 2: full metadata for one video. Returns a normalized dict or None."""
    out = run_yt_dlp([
        f"https://www.youtube.com/watch?v={video_id}",
        "--dump-json", "--skip-download", "--no-warnings",
    ])
    if not out.strip():
        return None
    try:
        d = json.loads(out.splitlines()[0])
    except (json.JSONDecodeError, IndexError):
        return None
    return {
        "id": video_id,
        "title": d.get("title") or "(untitled)",
        "channel": d.get("channel") or d.get("uploader") or "(unknown channel)",
        "subscribers": d.get("channel_follower_count"),
        "views": d.get("view_count"),
        "duration": d.get("duration"),
        "timestamp": d.get("timestamp"),
        "upload_date": d.get("upload_date"),  # YYYYMMDD
        "url": d.get("webpage_url") or f"https://www.youtube.com/watch?v={video_id}",
        "channel_url": d.get("channel_url"),
    }


def extract_all(ids, workers=10):
    """Extract metadata for all ids in parallel, preserving input (relevance) order."""
    results = [None] * len(ids)
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(extract_one, vid): i for i, vid in enumerate(ids)}
        done = 0
        for fut in concurrent.futures.as_completed(futures):
            results[futures[fut]] = fut.result()
            done += 1
            if done % 10 == 0 or done == len(ids):
                log(f"  ...extracted {done}/{len(ids)} videos")
    return [r for r in results if r is not None]


# ---------- formatting helpers ----------

def human_count(n):
    """5060000 -> '5.06M', 47858825 -> '47.9M', 1234 -> '1,234'."""
    if n is None:
        return "N/A"
    if n < 1_000:
        return str(n)
    if n < 1_000_000:
        return f"{n/1_000:.1f}K"
    if n < 1_000_000_000:
        return f"{n/1_000_000:.2f}M" if n < 10_000_000 else f"{n/1_000_000:.1f}M"
    return f"{n/1_000_000_000:.2f}B"


def human_duration(seconds):
    if not seconds:
        return "N/A"
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def human_date(item, now):
    """'2025-02-12 (3 months ago)'."""
    ts = item.get("timestamp")
    ud = item.get("upload_date")
    when = None
    if ts:
        when = dt.datetime.fromtimestamp(ts, dt.timezone.utc)
    elif ud and len(ud) == 8:
        try:
            when = dt.datetime.strptime(ud, "%Y%m%d").replace(tzinfo=dt.timezone.utc)
        except ValueError:
            when = None
    if when is None:
        return "unknown date"
    days = (now - when).days
    if days < 1:
        rel = "today"
    elif days < 30:
        rel = f"{days}d ago"
    elif days < 365:
        rel = f"{days // 30}mo ago"
    else:
        rel = f"{days // 365}y ago"
    return f"{when.strftime('%Y-%m-%d')} ({rel})"


def engagement(item):
    """views / subscribers. Returns float or None."""
    v, s = item.get("views"), item.get("subscribers")
    if v is None or not s:
        return None
    return v / s


def engagement_str(ratio):
    if ratio is None:
        return "N/A"
    if ratio >= 10:
        return f"{ratio:.0f}x"
    return f"{ratio:.2f}x"


# ---------- filtering ----------

def within_window(item, cutoff):
    """True if the upload is on/after cutoff. Keep items with unknown dates
    (better to show with a flag than silently drop them)."""
    ts = item.get("timestamp")
    if ts:
        return dt.datetime.fromtimestamp(ts, dt.timezone.utc) >= cutoff
    ud = item.get("upload_date")
    if ud and len(ud) == 8:
        try:
            d = dt.datetime.strptime(ud, "%Y%m%d").replace(tzinfo=dt.timezone.utc)
            return d >= cutoff
        except ValueError:
            return True
    return True


# ---------- rendering ----------

def render_terminal(items, query, now, scanned, matched, months):
    lines = []
    div = "─" * 64
    lines.append(div)
    lines.append(f"YouTube search: \"{query}\"")
    lines.append(f"Window: last {months} month(s)  |  scanned {scanned} candidates, "
                 f"{matched} matched  |  showing {len(items)}")
    lines.append(div)
    for i, it in enumerate(items, 1):
        ratio = engagement(it)
        lines.append("")
        lines.append(f"{i}. {it['title']}")
        lines.append(f"   Channel:    {it['channel']}  ({human_count(it['subscribers'])} subs)")
        lines.append(f"   Views:      {human_count(it['views'])}"
                     f"   |  Engagement: {engagement_str(ratio)} (views/subs)")
        lines.append(f"   Duration:   {human_duration(it['duration'])}"
                     f"   |  Uploaded: {human_date(it, now)}")
        lines.append(f"   {it['url']}")
        lines.append(div)
    return "\n".join(lines)


def render_markdown(items, query, now, scanned, matched, months):
    md = []
    md.append(f"# YouTube search: {query}")
    md.append("")
    md.append(f"> Generated {now.strftime('%Y-%m-%d')} · window: last {months} month(s) · "
              f"scanned {scanned} candidates, {matched} matched, showing {len(items)}.")
    md.append("")
    for i, it in enumerate(items, 1):
        ratio = engagement(it)
        ch = it["channel"]
        if it.get("channel_url"):
            ch = f"[{ch}]({it['channel_url']})"
        md.append(f"## {i}. [{it['title']}]({it['url']})")
        md.append("")
        md.append(f"- **Channel:** {ch} — {human_count(it['subscribers'])} subscribers")
        md.append(f"- **Views:** {human_count(it['views'])}")
        md.append(f"- **Engagement (views/subs):** {engagement_str(ratio)}")
        md.append(f"- **Duration:** {human_duration(it['duration'])}")
        md.append(f"- **Uploaded:** {human_date(it, now)}")
        md.append("")
        md.append("---")
        md.append("")
    return "\n".join(md)


def main():
    ap = argparse.ArgumentParser(description="Search YouTube and return structured results.")
    ap.add_argument("query", help="Search query")
    ap.add_argument("--count", type=int, default=20, help="Results to return (default 20)")
    ap.add_argument("--months", type=int, default=6,
                    help="Recency window in months (default 6). Use 0 for no date filter.")
    ap.add_argument("--scan", type=int, default=None,
                    help="Candidates to fetch before filtering "
                         "(default: count*3, capped 60). Raise it if few match the window.")
    ap.add_argument("--save", metavar="PATH.md", help="Also write results to a Markdown file")
    ap.add_argument("--json", action="store_true", help="Emit raw JSON to stdout instead of text")
    args = ap.parse_args()

    if shutil.which("yt-dlp") is None:
        log("ERROR: yt-dlp is not installed. Install with `brew install yt-dlp` "
            "or `pip install yt-dlp`.")
        sys.exit(2)

    scan = args.scan if args.scan else min(max(args.count * 3, args.count), 60)
    now = dt.datetime.now(dt.timezone.utc)

    log(f"Searching YouTube for \"{args.query}\" (scanning up to {scan} candidates)...")
    ids = fetch_candidate_ids(args.query, scan)
    if not ids:
        log("No videos found for that query.")
        sys.exit(3)
    log(f"Found {len(ids)} candidates. Extracting full metadata in parallel...")

    items = extract_all(ids)
    scanned = len(items)

    if args.months and args.months > 0:
        cutoff = now - dt.timedelta(days=int(args.months * 30.44))
        items = [it for it in items if within_window(it, cutoff)]
    matched = len(items)

    # Relevance order is already preserved by extract_all; just take the top N.
    items = items[:args.count]

    if not items:
        log(f"Scanned {scanned} videos but none fell within the last {args.months} month(s). "
            f"Try a larger --months or --scan value.")
        sys.exit(0)

    if args.json:
        for it in items:
            it["engagement_ratio"] = engagement(it)
        print(json.dumps(items, indent=2, ensure_ascii=False))
    else:
        print(render_terminal(items, args.query, now, scanned, matched, args.months))

    if args.save:
        md = render_markdown(items, args.query, now, scanned, matched, args.months)
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(md)
        log(f"\nSaved Markdown to {args.save}")


if __name__ == "__main__":
    main()
