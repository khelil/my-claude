#!/usr/bin/env python3
"""Lint mécanique du vault Brain (CLAUDE.md §7) : liens cassés, orphelines, tags, frontmatter,
dérive de l'index, compteurs. Lecture seule. Sortie texte, à reprendre dans le rapport de lint."""
import os, re, collections, sys

VAULT = "/Users/khelil/Library/Mobile Documents/iCloud~md~obsidian/Documents/Brain"
os.chdir(VAULT)
INDEX = "_meta/index.md"
SKIP_DIRS = ("_secrets",)
ATT = re.compile(r"\.(png|jpe?g|pdf|avif|gif|webp|svg|mp4|mov|mp3|wav|heic)$", re.I)
LINK = re.compile(r"\[\[([^\]|#^]+)")

files, allnames = {}, set()
for root, dirs, fs in os.walk("."):
    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in SKIP_DIRS]
    for f in fs:
        allnames.add(f.lower())
        if f.endswith(".md") and "_attachments" not in root:
            p = os.path.relpath(os.path.join(root, f), ".")
            files[p] = open(p, encoding="utf-8", errors="replace").read()

base = collections.defaultdict(list)
for p in files:
    base[os.path.basename(p)[:-3].lower()].append(p)
alias = {}
for p, s in files.items():
    m = re.search(r"^aliases:\s*\[(.*?)\]", s, re.M)
    if m:
        for a in re.findall(r'"([^"]+)"|\'([^\']+)\'', m.group(1)):
            alias[(a[0] or a[1]).lower()] = p

def strip_code(s):
    return re.sub(r"`[^`\n]*`", "", re.sub(r"```.*?```", "", s, flags=re.S))

# --- liens cassés + liens entrants (l'index exhaustif ne compte pas comme lien entrant)
inl, broken, missing_att = collections.Counter(), collections.defaultdict(set), collections.defaultdict(set)
REPORTS = re.compile(r"^_meta/(\d{4}-W\d{2}-|liens-a-valider|file-distillation)")
for p, s in files.items():
    if p.startswith("_meta/templates") or p == "CLAUDE.md":
        continue
    for t in LINK.findall(strip_code(s)):
        t = t.strip()
        k = os.path.basename(t).lower()
        if ATT.search(t):
            if k not in allnames: missing_att[p].add(t)
        elif k in base:
            if p != INDEX and not REPORTS.match(p):  # index et rapports listent tout : pas des liens de fond
                for q in base[k]:
                    if q != p: inl[q] += 1
        elif t.lower() in alias:
            if p != INDEX and not REPORTS.match(p): inl[alias[t.lower()]] += 1
        elif not REPORTS.match(p):
            broken[p].add(t)

print("## LIENS CASSÉS")
for p, ts in sorted(broken.items()): print(f"- {p} → {sorted(ts)}")
if not broken: print("- aucun")
print("\n## PIÈCES JOINTES INTROUVABLES")
for p, ts in sorted(missing_att.items()): print(f"- {p} → {sorted(ts)}")
if not missing_att: print("- aucune")

orph = sorted(p for p in files if inl[p] == 0 and not p.startswith(("_meta", "00_inbox", "wiki", "personalities")) and p != "CLAUDE.md")
print(f"\n## ORPHELINES (hors index) : {len(orph)} — {dict(collections.Counter(p.split('/')[0] for p in orph))}")
for p in orph: print(f"- {p}")

# --- frontmatter / tags
TAX = set(re.findall(r"#([a-z]+/[a-z0-9-]+)", files.get("_meta/taxonomie.md", "")))
off, nofm, nosrc, stale = collections.defaultdict(list), [], [], []
for p, s in files.items():
    if p.startswith(("_meta/templates", "00_inbox")) or p == "CLAUDE.md":
        continue
    if not s.startswith("---"):
        nofm.append(p + " (aucun frontmatter)"); continue
    fm = s[: s.find("\n---", 3)]
    for need in ("type", "status", "created", "updated"):
        if not re.search(rf"^{need}:\s*\S", fm, re.M): nofm.append(f"{p} (manque {need})")
    m = re.search(r"^tags:\s*\[(.*?)\]", fm, re.M)
    tags = [t.strip().strip("\"'#") for t in (m.group(1).split(",") if m else []) if t.strip()]
    tags += re.findall(r"^\s+-\s*[\"']?#?([a-z]+/[a-z0-9-]+)", fm, re.M)
    for t in tags:
        if TAX and t not in TAX: off[t].append(p)
    if p.startswith("resources/") and not re.search(r"^source:\s*[\"']?[^\"'\s]", fm, re.M): nosrc.append(p)
print("\n## TAGS HORS TAXONOMIE")
for t, ps in sorted(off.items()): print(f"- #{t} : {ps}")
if not off: print("- aucun")
print("\n## FRONTMATTER INCOMPLET")
for x in nofm: print(f"- {x}")
if not nofm: print("- aucun")
print("\n## RESOURCES SANS CHAMP source")
for x in sorted(nosrc): print(f"- {x}")
if not nosrc: print("- aucune")

# --- dérive de l'index
print("\n## INDEX")
if INDEX in files:
    indexed = {os.path.basename(t.strip()).lower() for t in LINK.findall(files[INDEX])}
    expected = {os.path.basename(p)[:-3].lower(): p for p in files if p != INDEX and not p.startswith("_meta/templates") and p != "CLAUDE.md"}
    absent = sorted(v for k, v in expected.items() if k not in indexed)
    dead = sorted(k for k in indexed if k not in base and k not in alias)
    print(f"- notes sur disque : {len(expected)} · absentes de l'index : {len(absent)} · entrées mortes : {len(dead)}")
    for p in absent: print(f"  - ABSENTE {p}")
    for k in dead: print(f"  - MORTE [[{k}]]")
else:
    print("- _meta/index.md introuvable")

# --- fiches personnalités non rafraîchies (CLAUDE.md §6quater, §7)
import datetime
cutoff = (datetime.date.today() - datetime.timedelta(days=90)).isoformat()
stale_p = []
for p, s_ in sorted(files.items()):
    if not p.startswith("personalities/"):
        continue
    if not re.search(r"^status:\s*active", s_, re.M):
        continue
    m = re.search(r"^updated:\s*(\d{4}-\d{2}-\d{2})", s_, re.M)
    if not m or m.group(1) < cutoff:
        stale_p.append(f"{p} (updated {m.group(1) if m else '?'})")
print("\n## PERSONNALITÉS NON RAFRAÎCHIES (> 90 j)")
for x in stale_p: print(f"- {x}")
if not stale_p: print("- aucune")

# --- compteurs
print("\n## COMPTEURS")
print("- par dossier :", dict(collections.Counter(p.split("/")[0] for p in files if "/" in p)))
print("- inbox :", sum(1 for p in files if p.startswith("00_inbox/")))
print("- sections « Liens suggérés » en attente :", sum(1 for p, s in files.items() if "## Liens suggérés" in s and not p.startswith("_meta")))
print("- captures #statut/a-traiter :", sum(1 for s in files.values() if "statut/a-traiter" in s[:800]))
