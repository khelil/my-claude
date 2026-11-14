#!/usr/bin/env python3
"""Contrôle des pages wiki : citations, cohérence Sources, liens, mots de jugement."""
import os, re, glob, sys

VAULT = "/Users/khelil/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain"
os.chdir(VAULT)
names = {}
for root, dirs, files in os.walk("."):
    dirs[:] = [d for d in dirs if not d.startswith(".")]
    for f in files:
        if f.endswith(".md"):
            names.setdefault(f[:-3], []).append(os.path.relpath(os.path.join(root, f), "."))

JUDG = re.compile(r"\b(intéressant|remarquable|excellent|je pense|selon moi|on devrait|nous recommandons|à mon avis)\b", re.I)
LINK = re.compile(r"\[\[([^\]|#]+)(?:[|#][^\]]*)?\]\]")
ok = True
for p in sorted(glob.glob("wiki/*.md")):
    s = open(p, encoding="utf-8").read()
    secs = {}
    cur = None
    for l in s.splitlines():
        m = re.match(r"^## (.+)", l)
        if m:
            cur = m.group(1).strip(); secs[cur] = []
        elif cur:
            secs[cur].append(l)
    issues = []
    for need in ("En bref", "Ce que disent les sources", "Contradictions et points ouverts", "Sources", "Voir aussi"):
        if need not in secs: issues.append(f"section manquante: {need}")
    if not re.search(r"^type: wiki$", s, re.M): issues.append("type != wiki")
    claims = [l for l in secs.get("Ce que disent les sources", []) if l.strip().startswith("- ")]
    uncited = [l for l in claims if not LINK.search(l)]
    bref = " ".join(secs.get("En bref", []))
    if not LINK.search(bref): issues.append("« En bref » sans citation")
    cited = set()
    for sec in ("En bref", "Ce que disent les sources", "Contradictions et points ouverts"):
        cited |= set(LINK.findall("\n".join(secs.get(sec, []))))
    listed = set(LINK.findall("\n".join(secs.get("Sources", []))))
    for c in sorted(cited | listed):
        paths = names.get(c.strip())
        if not paths: issues.append(f"lien cassé: [[{c}]]")
        elif c in listed and not any(x.startswith("resources/") for x in paths): issues.append(f"source hors resources/: [[{c}]] -> {paths}")
    for c in sorted(cited - listed):
        if not any(x.startswith("wiki/") for x in names.get(c.strip(), [])): issues.append(f"cité mais absent de Sources: [[{c}]]")
    for c in sorted(listed - cited): issues.append(f"listé dans Sources mais jamais cité: [[{c}]]")
    for c in LINK.findall("\n".join(secs.get("Voir aussi", []))):
        if c.strip() not in names: issues.append(f"Voir aussi — lien cassé: [[{c}]]")
    for l in uncited: issues.append("puce sans citation: " + l.strip()[:90])
    for l in claims:
        m = JUDG.search(LINK.sub("", l))
        if m and "selon" not in l.lower()[:40]: issues.append(f"mot de jugement « {m.group(0)} »: " + l.strip()[:80])
    contra = [l for l in secs.get("Contradictions et points ouverts", []) if l.strip().startswith("- ")]
    print(f"{p}: {len(claims)} puces · {len(listed)} sources · {len(contra)} contradictions/points ouverts · {len(issues)} problème(s)")
    for i in issues:
        ok = False; print("   ✗", i)
sys.exit(0 if ok else 1)
