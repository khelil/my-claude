---
name: youtube-notebook-research
description: >-
  End-to-end YouTube research pipeline. Given a topic, it finds the most
  relevant YouTube videos (via the youtube-search tool), builds a NotebookLM
  notebook from them, runs analysis on the topic against those sources, and
  returns a Markdown research report — saved to the Obsidian vault AND shown in
  chat — that includes the full source list with view counts, channel names,
  and engagement ratios. Use this whenever the user wants to research a topic
  *using YouTube videos as sources*, asks to "build a notebook / NotebookLM from
  YouTube videos about X", wants a researched briefing backed by video sources,
  or says things like "research X on YouTube and write it up" or "pull the top
  videos on Y into a notebook and analyze them". Prefer this over plain
  youtube-search or plain notebooklm when the user wants the whole chain:
  find videos → notebook → analysis → written report.
compatibility: >-
  Requires the youtube-search skill (its youtube_search.py script), the
  notebooklm CLI (notebooklm-py, authenticated via `notebooklm login`), yt-dlp,
  and python3.
---

# YouTube → NotebookLM Research Pipeline

Turn a research topic into a sourced, analyzed Markdown briefing. The chain:

```
topic → find top YouTube videos → create NotebookLM notebook → add videos as
sources (with backfill) → ask the notebook research questions → write report
(saved to vault + shown in chat, with full video metadata)
```

A bundled script does the mechanical first half deterministically; you do the
analysis and the write-up, because that's where judgment matters.

## Before you start

Confirm the pieces are wired up (fast, and the errors are otherwise cryptic):

```bash
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
notebooklm doctor          # Auth must pass. If not: `notebooklm login`
```

If `notebooklm doctor` shows Auth failing, stop and tell the user to run
`notebooklm login` — every later step depends on it.

## Step 1 — Build the notebook (one script call)

Pick a short slug for the topic and an output folder in the vault. The output
folder convention is `notebooklm/<topic-slug>/` inside the vault root
(`/Users/khelil/Documents/obsidian/Brain`), so each run is self-contained.

```bash
export PATH="$HOME/.local/bin:/opt/homebrew/bin:$PATH"
python3 scripts/build_notebook.py "<the user's research topic>" \
  --output-dir "/Users/khelil/Documents/obsidian/Brain/notebooklm/<topic-slug>" \
  --count 10
```

What it does and why you don't have to babysit it:
- Searches YouTube with **no date filter** (best videos by relevance, any age) and
  fetches a candidate pool larger than 10.
- Creates the notebook and adds videos as sources. When NotebookLM rejects a
  video (some can't be ingested), it **backfills** from the next-ranked candidate
  so you still reach 10 successful sources when the pool allows.
- Waits for sources to finish processing.
- Writes `manifest.json` (all source metadata) and `sources_table.md` (a ready-made
  Markdown table) into the output folder, and prints a JSON summary with the
  `notebook_id`.

Read the printed `notebook_id` and `manifest_path` — you need them next.

If you want a tighter or more recent search, pass `--months 12` (or `6`); if the
user asked for a different number of videos, pass `--count N`.

## Step 2 — Analyze the topic against the sources

Now use the notebook to actually answer the user's research intent. Derive your
questions from *what the user asked when they invoked the pipeline* — the goal is
their research question, not a generic summary.

Start with a broad pass, then 3–5 focused questions. Use `--json` so you get the
answer plus citation references, and target the notebook explicitly with `-n`:

```bash
notebooklm summary -n <notebook_id>
notebooklm ask "<a focused question grounded in the user's topic>" -n <notebook_id> --json
```

Good question sets are specific to the topic. For "the state of local LLMs in
2026" you might ask: what are the main approaches, where do the videos disagree,
what's the consensus on hardware, what's changed most recently, what's hyped vs.
substantiated. Read the `answer` fields; the `references` map back to sources.
Ask follow-ups if an answer is thin — you're doing research, not filling a form.

If `ask` errors or returns empty, the sources may still be processing — re-check
`notebooklm source list -n <notebook_id> --json` and retry.

## Step 3 — Write the report (vault + chat)

Assemble a single Markdown report and save it to
`<output-dir>/report.md`. Then show the same content in chat so the user sees it
without opening the file.

Read `manifest.json` for metadata and reuse the ready-made `sources_table.md`.
Use this structure:

```markdown
# YouTube Research: <Topic>

> Notebook: <notebook_title> (`<notebook_id>`) · <N> video sources · <date>

## Research question
<restate what the user actually asked, in one or two lines>

## Key findings
<your synthesis from the notebook analysis — lead with what answers their
question. Weave in where sources agree/disagree. Keep it substantive, not a
list of summaries. Attribute notable claims to the video they came from.>

## Notable points by source
<optional: a few bullets tying specific insights to specific videos>

## Sources
<paste the contents of sources_table.md — the table with view counts, channel
names, subscriber counts, and engagement ratios. This is required: the user
explicitly wants the full YouTube metadata in the output.>

## Notebook
Open in NotebookLM to go deeper, generate an audio overview, mind map, etc.
Notebook ID: `<notebook_id>`
```

Save it:

```bash
# write the assembled markdown to <output-dir>/report.md
```

Then print the full report in chat (the user wants both). Don't just say "saved
to X" — show the findings and the source table inline so it's usable immediately.

## Keeping the metadata honest

The user specifically asked for view counts, channel names, and engagement
ratios in the output — these come straight from `manifest.json`/`sources_table.md`,
so don't paraphrase or round them away. The engagement ratio is views ÷
subscribers; a value above ~1 means the video reached well beyond its channel's
base. If a video was rejected by NotebookLM and backfilled, the table notes it —
keep that note so the user knows the source set isn't silently truncated.

## Scaling the work to the request

Most runs are one search + one notebook + a handful of questions. If the user
asks for something lighter ("just pull 5 videos and give me the gist"), pass
`--count 5` and ask fewer questions. If they want depth, ask more follow-ups and
expand Key findings — but the pipeline shape stays the same.
