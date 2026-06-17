#!/usr/bin/env python3
"""
build_notebook.py — Deterministic first half of the YouTube → NotebookLM pipeline.

Given a research topic, this:
  1. Searches YouTube (via the youtube-search skill's script) for ranked candidates.
  2. Creates a fresh NotebookLM notebook.
  3. Adds the top videos as sources, BACKFILLING from lower-ranked candidates
     whenever NotebookLM rejects one, so the notebook ends up with `--count`
     successful sources (or as many as the candidate pool allows).
  4. Waits for sources to finish processing.
  5. Writes a machine-readable manifest.json + a human-readable sources table
     into the output directory, and prints a summary to stdout.

The *analysis* (asking the notebook questions, writing the report) is intentionally
NOT done here — that needs the model's judgment about what to ask and how to
synthesize. This script just gets the notebook reliably built and hands back
every piece of metadata the report needs.

Why a script for this part: the search→create→add→backfill→wait loop is fiddly,
deterministic, and identical every run. Pinning it down here means each pipeline
invocation behaves the same instead of re-improvising shell glue.

Usage:
  build_notebook.py "<topic>" --output-dir DIR [--count 10] [--title TEXT]
                    [--months 0] [--pool 25] [--wait-timeout 180]

Exit codes: 0 ok, 2 missing dependency, 3 no candidates, 4 notebook create failed.
"""

import argparse
import json
import os
import shutil
import subprocess
import sys
import time


def log(msg):
    print(msg, file=sys.stderr, flush=True)


def resolve_binary(name, extra_dirs):
    """Find an executable, falling back to common user-local install dirs."""
    found = shutil.which(name)
    if found:
        return found
    for d in extra_dirs:
        cand = os.path.join(os.path.expanduser(d), name)
        if os.path.isfile(cand) and os.access(cand, os.X_OK):
            return cand
    return None


def find_search_script():
    """Locate the youtube-search skill's script (env override wins)."""
    env = os.environ.get("YOUTUBE_SEARCH_SCRIPT")
    if env and os.path.isfile(env):
        return env
    home = os.path.expanduser("~")
    candidates = [
        os.path.join(home, ".claude/skills/youtube-search/scripts/youtube_search.py"),
        os.path.join(home, ".agents/skills/youtube-search/scripts/youtube_search.py"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return None


def human_count(n):
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


def eng_str(r):
    if r is None:
        return "N/A"
    return f"{r:.0f}x" if r >= 10 else f"{r:.2f}x"


def slugify(text, maxlen=60):
    keep = [c.lower() if c.isalnum() else "-" for c in text.strip()]
    slug = "".join(keep)
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug.strip("-")[:maxlen] or "research"


def run(cmd, env, timeout=120):
    """Run a command, return (exit_code, stdout, stderr)."""
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        return p.returncode, p.stdout, p.stderr
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"
    except FileNotFoundError as e:
        return 127, "", str(e)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("topic", help="Research topic / search query")
    ap.add_argument("--output-dir", required=True, help="Where to write manifest + table")
    ap.add_argument("--count", type=int, default=10, help="Target successful sources (default 10)")
    ap.add_argument("--title", help="Notebook title (default derived from topic)")
    ap.add_argument("--months", type=int, default=0,
                    help="Recency window for search; 0 = no date filter (default)")
    ap.add_argument("--pool", type=int, default=None,
                    help="Candidates to fetch for backfill (default count*2.5, min 20)")
    ap.add_argument("--wait-timeout", type=int, default=180,
                    help="Max seconds to wait for sources to become ready")
    args = ap.parse_args()

    env = dict(os.environ)
    env["PATH"] = os.pathsep.join([
        os.path.expanduser("~/.local/bin"), "/opt/homebrew/bin", env.get("PATH", ""),
    ])

    nb = resolve_binary("notebooklm", ["~/.local/bin", "/opt/homebrew/bin"])
    if not nb:
        log("ERROR: notebooklm CLI not found. Install notebooklm-py and run `notebooklm login`.")
        sys.exit(2)
    search_script = find_search_script()
    if not search_script:
        log("ERROR: youtube-search script not found. Set YOUTUBE_SEARCH_SCRIPT or install the youtube-search skill.")
        sys.exit(2)

    title = args.title or f"YouTube Research: {args.topic}"
    pool = args.pool or max(20, int(args.count * 2.5))
    os.makedirs(args.output_dir, exist_ok=True)

    # --- Stage 1: search YouTube for a ranked candidate pool ---
    log(f"[1/4] Searching YouTube for \"{args.topic}\" ({pool} candidates, "
        f"{'no date filter' if args.months == 0 else f'last {args.months}mo'})...")
    code, out, err = run(
        ["python3", search_script, args.topic,
         "--count", str(pool), "--months", str(args.months), "--json"],
        env, timeout=600)
    if code != 0 or not out.strip():
        log(f"ERROR: YouTube search failed (exit {code}). {err[:300]}")
        sys.exit(3)
    try:
        candidates = json.loads(out)
    except json.JSONDecodeError:
        log("ERROR: could not parse YouTube search JSON.")
        sys.exit(3)
    if not candidates:
        log("ERROR: no YouTube candidates found for that topic.")
        sys.exit(3)
    log(f"      got {len(candidates)} candidates.")

    # --- Stage 2: create the notebook ---
    log(f"[2/4] Creating NotebookLM notebook: {title!r}")
    code, out, err = run([nb, "create", title, "--json"], env, timeout=120)
    if code != 0:
        log(f"ERROR: notebook create failed (exit {code}). {err[:300]}")
        sys.exit(4)
    try:
        notebook_id = json.loads(out)["notebook"]["id"]
    except (json.JSONDecodeError, KeyError):
        log(f"ERROR: could not parse notebook id from: {out[:300]}")
        sys.exit(4)
    log(f"      notebook_id = {notebook_id}")

    # --- Stage 3: add sources with backfill ---
    log(f"[3/4] Adding sources (target {args.count}, backfilling rejections)...")
    added, failed = [], []
    for cand in candidates:
        if len(added) >= args.count:
            break
        url = cand.get("url")
        if not url:
            continue
        code, out, err = run(
            [nb, "source", "add", url, "-n", notebook_id, "--type", "youtube", "--json"],
            env, timeout=180)
        ok = code == 0
        src_id = None
        if ok:
            try:
                src_id = json.loads(out)["source"]["id"]
            except (json.JSONDecodeError, KeyError):
                ok = bool(out.strip())  # added but unparseable JSON; treat as success
        rec = {
            "rank": cand.get("_rank"),
            "source_id": src_id,
            "title": cand.get("title"),
            "channel": cand.get("channel"),
            "subscribers": cand.get("subscribers"),
            "views": cand.get("views"),
            "engagement_ratio": cand.get("engagement_ratio"),
            "duration": cand.get("duration"),
            "upload_date": cand.get("upload_date"),
            "url": url,
        }
        if ok:
            rec["rank"] = len(added) + 1
            added.append(rec)
            log(f"      + ({len(added)}/{args.count}) {rec['title']!r}")
        else:
            rec["error"] = (err or "add failed").strip()[:200]
            failed.append(rec)
            log(f"      x rejected: {rec['title']!r} — backfilling")

    if not added:
        log("ERROR: no sources could be added to the notebook.")
        # still write a manifest so the caller can report the failure
    # --- Stage 4: wait for sources to finish processing ---
    log(f"[4/4] Waiting for {len(added)} sources to become ready (<= {args.wait_timeout}s)...")
    deadline = None
    waited = 0
    interval = 4
    while waited < args.wait_timeout and added:
        code, out, _ = run([nb, "source", "list", "-n", notebook_id, "--json"], env, timeout=60)
        if code == 0:
            try:
                srcs = json.loads(out).get("sources", [])
            except json.JSONDecodeError:
                srcs = []
            statuses = [s.get("status") for s in srcs]
            pending = [s for s in statuses if s not in ("ready", "error", "failed", None)]
            # record latest statuses back onto added records by source_id
            by_id = {s.get("id"): s.get("status") for s in srcs}
            for rec in added:
                if rec["source_id"] in by_id:
                    rec["status"] = by_id[rec["source_id"]]
            if not pending:
                log(f"      all sources settled ({statuses.count('ready')} ready).")
                break
        time.sleep(interval)
        waited += interval

    # --- write manifest + table ---
    manifest = {
        "topic": args.topic,
        "notebook_title": title,
        "notebook_id": notebook_id,
        "output_dir": os.path.abspath(args.output_dir),
        "target_count": args.count,
        "added_count": len(added),
        "failed_count": len(failed),
        "sources": added,
        "failed_sources": failed,
    }
    manifest_path = os.path.join(args.output_dir, "manifest.json")
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # human-readable sources table (Markdown)
    rows = ["| # | Video | Channel | Subs | Views | Engagement | Uploaded |",
            "|---|-------|---------|------|-------|------------|----------|"]
    for r in added:
        ud = r.get("upload_date") or ""
        ud = f"{ud[:4]}-{ud[4:6]}-{ud[6:8]}" if len(ud) == 8 else "—"
        rows.append(
            f"| {r['rank']} | [{(r['title'] or '').replace('|','/')}]({r['url']}) "
            f"| {r.get('channel') or '—'} | {human_count(r.get('subscribers'))} "
            f"| {human_count(r.get('views'))} | {eng_str(r.get('engagement_ratio'))} | {ud} |")
    table_md = "\n".join(rows)
    if failed:
        table_md += "\n\n**Could not be ingested by NotebookLM (backfilled):** " + \
            ", ".join(f"[{(r['title'] or r['url'])}]({r['url']})" for r in failed)
    with open(os.path.join(args.output_dir, "sources_table.md"), "w", encoding="utf-8") as f:
        f.write(table_md + "\n")

    # stdout summary for the calling model
    print(json.dumps({
        "notebook_id": notebook_id,
        "notebook_title": title,
        "added_count": len(added),
        "failed_count": len(failed),
        "manifest_path": manifest_path,
        "sources_table_path": os.path.join(args.output_dir, "sources_table.md"),
    }, indent=2))


if __name__ == "__main__":
    main()
