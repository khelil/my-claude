---
name: youtube-search
description: >-
  Search YouTube and return structured, ranked video results with rich metadata
  — title, channel, subscriber count, view count, duration, upload date, URL,
  and a views-to-subscribers engagement ratio. Results are filtered to the last
  6 months by default. Use this whenever the user wants to find, discover,
  research, or survey YouTube videos on a topic, asks "what videos are out
  there about X", wants recent or trending videos, needs to compare channels or
  gauge how videos are performing, or wants to pull YouTube results into a note
  — even if they don't explicitly say "yt-dlp" or "search YouTube".
compatibility: Requires yt-dlp (brew install yt-dlp / pip install yt-dlp) and python3.
---

# YouTube Search

Search YouTube by query and return the top results as structured, human-readable
data: title, channel, subscriber count, view count, duration, upload date, URL,
and a **views-to-subscribers engagement ratio** that surfaces videos punching
above their channel's weight.

Everything is done by the bundled script — you almost never need to call yt-dlp
directly. The script handles searching, parallel metadata extraction, date
filtering, the engagement metric, and formatting.

## Quick start

```bash
python3 scripts/youtube_search.py "<query>"
```

That prints the top 20 results from the last 6 months to the terminal. To also
save a Markdown note (great for an Obsidian vault), add `--save`:

```bash
python3 scripts/youtube_search.py "mechanical keyboard review" --save ~/Documents/obsidian/Brain/youtube-mech-keyboards.md
```

Use the script's real path when invoking from another directory.

## Options

| Flag | Default | Purpose |
|------|---------|---------|
| `--count N` | 20 | How many results to return. |
| `--months N` | 6 | Recency window. `--months 0` disables the date filter entirely. |
| `--scan N` | count×3 (max 60) | How many candidates to fetch *before* filtering. Raise this when a tight window leaves too few matches. |
| `--save PATH.md` | — | Also write a Markdown version (clickable links). |
| `--json` | — | Emit raw JSON to stdout instead of formatted text (for piping/programmatic use). |

## How it works (and why it's shaped this way)

YouTube search returns videos in **relevance order**, and the script preserves
that order — it does not re-sort by views or engagement. The engagement ratio is
shown as a signal for you and the user to read, not as the sort key.

Getting subscriber and view counts requires yt-dlp to fully extract each video,
which is slow one-at-a-time. So the script works in two stages: a fast flat
search to collect candidate video IDs, then **parallel** full-metadata
extraction. Twenty videos land in well under a minute instead of several.

## Handling the recency window honestly

"Top 20" and "last 6 months" can pull against each other — the 20 most relevant
videos for a query may include older ones. The script over-scans candidates
(default `count×3`), filters to the window, and returns the top N that qualify.
It always reports **scanned X, matched Y, showing N** so the user knows whether
the window was the limiting factor.

If the user gets fewer results than they wanted, that usually means few recent
videos exist for the query. Good responses: widen the window (`--months 12`),
scan deeper (`--scan 80`), or tell the user the topic is quiet lately. Don't
silently present a short list as if it were the full picture.

## Reading the engagement ratio

`engagement = views ÷ subscribers`. A ratio above ~1 means the video pulled more
views than the channel has subscribers — it reached beyond the channel's base
(often a sign of an over-performer or something that caught an algorithm wave).
Below ~0.2 is typical for a large channel's routine upload. It's `N/A` when a
channel hides its subscriber count. Treat it as a rough signal, not gospel —
mention what stands out rather than reciting every number.

## After running

When you've saved a Markdown file, tell the user the path. When relevant,
summarize what stands out — the highest-engagement video, a recent upload from a
small channel, or whether the topic looks active or stale lately — rather than
just dumping the list back. The user asked about a topic; help them read the
landscape, don't just relay rows.

## If yt-dlp is missing

The script exits with a clear message. Offer to install it
(`brew install yt-dlp` on macOS, or `pip install yt-dlp`) and rerun.
