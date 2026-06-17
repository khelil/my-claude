# YouTube Research: Zig vs Rust for Systems Programming

> Notebook: [SKILLTEST] YouTube Research: zig vs rust (`165e08d7-7c9f-49df-b937-32525a5f4ff6`) · 10 video sources · 2026-06-02

## Research question

You wanted to understand the debate around **Zig vs Rust for systems programming** — the best YouTube videos on it pulled into a notebook, plus an analysis of the main arguments on each side, with view counts and the channels they came from.

## Key findings

The 10 videos converge on one thing and split sharply on everything else: **both languages are genuine C-level performers, so the debate is almost never about raw speed — it's about the safety-vs-control tradeoff and the maturity-vs-momentum bet.**

**The pro-Rust case** rests on four pillars that the high-view videos hammer repeatedly. (1) *Memory safety without a garbage collector* — Rust's borrow checker catches use-after-free, buffer overflows, and data races at compile time, so "once it compiles, it's practically immune" (ForrestKnight's *Why Everyone's Switching to Rust*; *C is 50 Years Old. Should You Learn Rust?* by Low Level). The contrast with Zig is explicit: in *Why I Chose Rust Over Zig* (The PrimeTime), the argument is that Zig makes safety opt-in (you can still segfault or leak), whereas Rust developers "learn to completely trust the borrow checker." (2) *Ecosystem maturity* — even Zig's own advocates concede Rust has "batteries out of the box," real technical books, and async documentation that Zig simply lacks (*Meet the Author* on Manning). (3) *Tooling* — Cargo is repeatedly named as the feature that makes people fall in love with Rust over C++/Zig, with error messages that guide you to the fix (*P99 CONF*, ForrestKnight). (4) *Adoption / industry backing* — Microsoft advising no new C/C++ projects, a 152K-line Windows font engine rewrite with 70% fewer vulnerabilities, Rust in the Linux kernel, Discord's 10x improvement. Rust is framed as the "safe and boring option" for long-term infrastructure.

**The pro-Zig case** is built around control and clarity. (1) *No hidden behavior* — Jared (creator of Bun) in *P99 CONF* argues Zig is ideal "when every detail matters": no operator overloading, no hidden constructors/destructors, no macros obscuring what the machine does. Its standard library is readable, versus Rust's std needing "a PhD in Rust" to navigate (*Why I Chose Rust Over Zig*). (2) *comptime* — compile-time execution that "is just Zig," so you avoid learning a separate macro sub-language; used for things like compile-time JSON parsing and perfect hash functions (*Meet the Author*, *P99 CONF*). (3) *Explicit manual memory control via allocators* — you keep control instead of redesigning how you think about code, and Zig handles out-of-memory gracefully rather than crashing, which matters in constrained environments (*Zig in Production*, Zig SHOWTIME). (4) *Cross-compilation* — fully self-contained binaries and `zig cc` make targeting obscure ARM "10 seconds" of work versus days of custom toolchains; Rust's OpenSSL/shared-lib distribution pain is the foil. (5) *Frictionless C interop* — Zig effortlessly wraps huge C/C++ libraries (even Clang). (6) *Gentler mental model* — Rust's "concept fatigue" (ownership, lifetimes, traits, async) stalls even senior devs for months, while experienced systems programmers onboard to Zig fast.

**Where the videos disagree most sharply:**
- *comptime vs. a strong type system.* In *P99 CONF* / *Why I Chose Rust Over Zig*, the dissenter (Pekka) calls comptime a "rabbit hole of magic" and prefers Rust's generics/traits; Jared, Glauber Costa, and The Primeagen defend it fiercely as superior to procedural macros. This is the single hottest point of contention.
- *Cross-compilation: dealbreaker or one-time annoyance?* Glauber Costa frames Zig's self-contained binaries as a game-changer; Pekka counters that Rust's build pain is just a one-time setup cost, not a reason to choose a language.

**Rough consensus on when to pick which:**
- **Rust** — long-lived infrastructure, secure network services, large corporate codebases where preventing memory vulnerabilities is paramount, and anything that benefits from a rich crate ecosystem (CLIs, etc.). The low-risk, "here for decades" choice.
- **Zig** — polyglot projects gluing/wrapping crusty C/C++ libraries, constrained embedded systems needing graceful OOM handling, WebAssembly, and extreme-performance projects (game engines, the Bun runtime, databases) where every allocation matters and hidden behavior is unacceptable. The tradeoff is pre-1.0 risk: a shifting compiler, missing features (async rework), thin learning materials, and a small ecosystem.

On **benchmarks**, the one head-to-head data point comes from Dave Plummer with Lex Fridman (*Fastest programming language*): in his 100-language GitHub "Primes" project, Zig consistently sits at the very top of the leaderboard, edging out Rust, Nim, and C++ — though all are treated as top-tier and the broader point is that the choice isn't decided on raw speed.

## Notable points by source

- **Lex Clips — *Fastest programming language: C++ vs Rust vs Zig*** (91.4K views): the benchmark anchor — Zig topping a 100-language primes leaderboard, above Rust and C++.
- **The PrimeTime — *Why I Chose Rust Over Zig*** (329.3K views): the most balanced pro-Rust-but-fair piece — Rust's borrow-checker trust and learning resources vs. Zig's readable std and comptime; home of the sharpest comptime disagreement.
- **The PrimeTime — *P99 CONF - Zig vs Rust*** (99.0K views): the deepest technical debate, featuring Bun's creator and Glauber Costa — comptime, Cargo, and cross-compilation arguments all originate here.
- **ForrestKnight — *Why Everyone's Switching to Rust (And Why You Shouldn't)*** (480.9K views, highest raw views): the GC-free safety case plus the "concept fatigue" critique that doubles as a pro-Zig argument.
- **Low Level — *C is 50 Years Old. Should You Learn Rust?*** (435.5K views): frames Rust against C's legacy; borrow checker as guardrails.
- **TheTechyShop — *Zig vs C: The Next Systems Language?*** (engagement 9.46x, by far the highest): "precision without hidden magic," explicit allocators, `zig cc`.
- **Manning / Zig SHOWTIME conference talks** (*Meet the Author*, *Zig in Production*, *Zig loves WASI!*, *The Rust Website Redesign Debacle*): the practitioner Zig perspective — graceful OOM, C interop, WASM, ecosystem honesty.

## Sources

| # | Video | Channel | Subs | Views | Engagement | Uploaded |
|---|-------|---------|------|-------|------------|----------|
| 1 | [Fastest programming language: C++ vs Rust vs Zig / Dave Plummer and Lex Fridman](https://www.youtube.com/watch?v=ydzq9P8vI5Y) | Lex Clips | 1.62M | 91.4K | 0.06x | 2025-09-04 |
| 2 | [Why I Chose Rust Over Zig](https://www.youtube.com/watch?v=Vxq6Qc-uAmE) | The PrimeTime | 1.13M | 329.3K | 0.29x | 2024-07-17 |
| 3 | [Zig vs C: The Next Systems Language?](https://www.youtube.com/watch?v=gqsObMTgUPk) | TheTechyShop | 2.1K | 20.0K | 9.46x | 2025-10-22 |
| 4 | [P99 CONF - Zig vs Rust](https://www.youtube.com/watch?v=7czcewOnaYg) | The PrimeTime | 1.13M | 99.0K | 0.09x | 2024-07-16 |
| 5 | [Meet the Author: Garrison Hinson-Hasty on Systems Programming with Zig](https://www.youtube.com/watch?v=eysGKWQ_oBg) | Manning Publications | 16.5K | 2.1K | 0.12x | 2025-12-16 |
| 6 | [Zig loves WASI! - Jakub Konka](https://www.youtube.com/watch?v=g_Degmqfo4Q) | Zig SHOWTIME | 17.0K | 2.6K | 0.16x | 2020-06-23 |
| 7 | [C is 50 Years Old. Should You Learn Rust?](https://www.youtube.com/watch?v=NtYHC1KNGoc) | Low Level | 1.12M | 435.5K | 0.39x | 2023-04-26 |
| 8 | [Why Everyone's Switching to Rust (And Why You Shouldn't)](https://www.youtube.com/watch?v=meEXag1XCFw) | ForrestKnight | 695.0K | 480.9K | 0.69x | 2025-08-19 |
| 9 | [The Rust Website Redesign Debacle](https://www.youtube.com/watch?v=23JCY0SQGIA) | Zig SHOWTIME | 17.0K | 1.6K | 0.09x | 2020-11-15 |
| 10 | [Zig in Production - Jens Goldberg](https://www.youtube.com/watch?v=124wdTckHNY) | Zig SHOWTIME | 17.0K | 15.9K | 0.94x | 2020-09-21 |

All 10 candidate videos were accepted by NotebookLM; none were rejected or backfilled. Engagement ratio = views / subscribers; above ~1x means the video reached well beyond its channel's base (note the standout: TheTechyShop at 9.46x).

## Notebook

Open in NotebookLM to go deeper, generate an audio overview, mind map, etc.
Notebook ID: `165e08d7-7c9f-49df-b937-32525a5f4ff6`
