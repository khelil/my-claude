# YouTube Research: Zig vs Rust for Systems Programming

> Notebook: [SKILLTEST] YouTube Research: Zig vs Rust for Systems Programming (`6759650c-1247-4eb4-a9ad-b9bf0f3ab372`) · 10 video sources · 2026-06-02

## Research question
Understand the debate around Zig vs Rust for systems programming: pull together the best YouTube videos on it, and analyze the main arguments on each side — with view counts and the channels they came from.

## Key findings

The debate is not really "which language is better" but "what trade-off do you want." Across these ten videos, the same axis keeps coming up: **Rust buys you compile-time memory safety at the cost of control and a steep learning curve; Zig keeps the raw control of C and modernizes the tooling, but leaves you responsible for safety.** Almost every speaker agrees on that framing — they disagree on which side of it is worth it.

### The case for Rust
- **Memory safety without a garbage collector** is the headline argument. The borrow checker verifies ownership, borrowing, and lifetimes at compile time, eliminating use-after-free, leaks, and buffer-overflow vulnerabilities — the class of bugs behind ~70% of Microsoft's security issues — with no runtime overhead. ("Why Everyone's Switching to Rust", ForrestKnight; "C is 50 Years Old", Low Level)
- **Tooling and ecosystem maturity.** Cargo "just works" and is repeatedly called a massive advantage over C/C++ build systems; the compiler's error messages actively help you fix problems, and rust-analyzer makes the edit loop fast. Rust ships far more "batteries out of the box" via crates and has deep learning resources (books, the Async Rust book). (P99 CONF Zig vs Rust, The PrimeTime; ForrestKnight)
- **Industry adoption makes it the "safe and boring choice."** Rust is in the Linux kernel; Microsoft has said to halt new C/C++ projects and rewrote Windows font rendering (152k lines) for 5–15% gains; Discord killed GC pauses for a 10x win; Dropbox rewrote its sync engine; AWS built Firecracker in Rust. For long-term infrastructure, that backing is the argument. (ForrestKnight; P99 CONF)

### The case for Zig
- **Simplicity / no hidden control flow.** No operator overloading, no hidden constructors/destructors, no exceptions; errors are explicit values. The payoff is a standard library you can actually read — contrasted against the claim that Rust's reliance on traits, async, and macros means you "almost need a PhD" to read its stdlib. (P99 CONF, The PrimeTime; "Zig vs C", TheTechyShop)
- **comptime.** Running ordinary Zig at compile time replaces macros and build scripts — "comptime is just Zig," so there's no separate language-within-a-language to learn. (Manning "Meet the Author"; P99 CONF)
- **Manual memory control as a middle ground.** Zig rejects both the GC and the borrow checker, using explicit allocators. You *can* leak or segfault — but the debug allocator catches leaks during tests and tells you the exact line, making manual management far safer than C/C++. (P99 CONF; "Zig in Production", Zig SHOWTIME)
- **C interop and cross-compilation are best-in-class.** `zig cc` is a drop-in C/C++ compiler, so you can absorb large legacy C libraries without binding friction; producing tiny, statically linked, dependency-free binaries for quirky/embedded targets is a single command. This is repeatedly cited as where Rust struggles (e.g. OpenSSL static linking). ("Zig loves WASI!", Zig SHOWTIME; P99 CONF)
- **Performance.** With no hidden runtime overhead, Zig "fights for #1" in the GitHub Primes cross-language benchmark, often beating Rust and C++; fast compiles also keep the iteration loop tight versus Rust's notoriously slow builds. ("Zig vs C", TheTechyShop; Lex Clips)

### Where they sharply disagree
- **comptime:** loved as "just Zig" by Bun/Turso voices, dismissed as a "rabbit hole of magic" that "feels like a hack" by skeptics (Pekka, Turso CTO).
- **Binary distribution:** one camp calls Rust "terrible" for static binaries with C deps; the counter is that it just "takes setup" and isn't "insurmountable."
- **Learning curve direction:** some say Zig is *harder* to learn (small type system, no books, shifting toolchain); others say Zig is *easier* because its source is readable while Rust suffers "concept fatigue."

### Consensus on how to choose
Unanimous that **Rust is far more mature** — Zig is often described as "where Rust was in 2015" (small ecosystem, no books, moving compiler). The decision rule that emerges:
- **Choose Rust** for large-scale infrastructure, long-term enterprise services, and anywhere absolute memory safety and a deep library ecosystem matter — the "safe and boring" pick.
- **Choose Zig** when "every detail matters": extreme-performance work, polyglot codebases gluing C/C++ libraries together, and deeply embedded systems with constrained memory or unusual CPU architectures.

## Notable points by source
- **P99 CONF - Zig vs Rust** (The PrimeTime) is the richest single source — a multi-person debate that surfaces nearly every argument on both sides, including the comptime and distribution disputes.
- **Why Everyone's Switching to Rust (And Why You Shouldn't)** (ForrestKnight) supplies the production adoption case studies (Microsoft, Discord, Dropbox, AWS) and the borrow-checker pitch.
- **Fastest programming language: C++ vs Rust vs Zig** (Lex Clips, w/ Dave Plummer) anchors the benchmark/performance angle via GitHub Primes.
- **Zig in Production** and **Zig loves WASI!** (Zig SHOWTIME) ground the Zig case in real deployments, cross-compilation, and embedded/WASM use.
- **The Rust Website Redesign Debacle** (Zig SHOWTIME) is the outlier — about Rust's community/marketing shift toward enterprise decision-makers rather than a technical comparison.

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

Engagement ratio = views / subscribers; >1 means the video reached well beyond its channel's base (e.g. #3 at 9.46x punched far above its small channel). All 10 candidates were ingested by NotebookLM — none rejected, none backfilled.

## Notebook
Open in NotebookLM to go deeper, generate an audio overview, mind map, etc.
Notebook ID: `6759650c-1247-4eb4-a9ad-b9bf0f3ab372`
