#!/usr/bin/env python3
"""Outils de /brain-get-profile.

  profile_tools.py slug "Prénom Nom"                 → slug kebab-case sans accents
  profile_tools.py verify --pages DIR FICHIER...     → JSON {"verified": [...], "rejected": [...]}

Ligne de preuve attendue (les autres lignes sont ignorées sauf si elles commencent par « - [ ») :
  - [B2] affirmation :: "citation verbatim" :: https://url :: AAAA-MM-JJ|n.d. :: fichier-page.md
"""
import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

MAX_WORDS = 25
GRADE = re.compile(r"^[A-F][1-6]$")
EVIDENCE = re.compile(r'^- \[(?P<grade>[^\]]*)\]\s*(?P<claim>.+?)\s*::\s*"(?P<quote>.+)"\s*::\s*(?P<url>\S+)\s*::\s*(?P<date>\S+)\s*::\s*(?P<page>\S+)\s*$')
TRANSLATE = str.maketrans({
    "’": "'", "‘": "'", "ʼ": "'", "“": '"', "”": '"',
    "«": '"', "»": '"', " ": " ", " ": " ", "–": "-", "—": "-",
})


def slugify(name: str) -> str:
    s = unicodedata.normalize("NFKD", name)
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")


def normalize(text: str) -> str:
    s = unicodedata.normalize("NFKC", text).translate(TRANSLATE)
    s = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", s)  # [texte](url) → texte
    s = re.sub(r"[*_]+", "", s)  # emphase markdown
    s = s.replace('"', "")  # guillemets : jamais significatifs pour la comparaison
    return re.sub(r"\s+", " ", s).strip().casefold()


def parse_evidence(line: str) -> dict | None:
    m = EVIDENCE.match(line.strip())
    return m.groupdict() if m else None


def verify_one(ev: dict, pages_dir: Path) -> tuple[bool, str]:
    if not GRADE.match(ev["grade"]):
        return False, "note invalide"
    if len(ev["quote"].split()) > MAX_WORDS:
        return False, "citation trop longue"
    page = Path(pages_dir) / ev["page"]
    if not page.is_file():
        return False, "page introuvable"
    text = page.read_text(encoding="utf-8", errors="replace")
    if not text.strip():
        return False, "page vide"
    if normalize(ev["quote"]) not in normalize(text):
        return False, "citation absente de la page"
    return True, ""


def cmd_verify(pages: str, files: list[str]) -> int:
    missing = [f for f in files if not Path(f).is_file()]
    if missing:
        print(f"fichier(s) introuvable(s) : {missing}", file=sys.stderr)
        return 2
    verified, rejected = [], []
    for f in files:
        for raw in Path(f).read_text(encoding="utf-8").splitlines():
            if not raw.strip().startswith("- ["):
                continue
            ev = parse_evidence(raw)
            if ev is None:
                rejected.append({"line": raw, "reason": "ligne mal formée", "file": f})
                continue
            ok, reason = verify_one(ev, Path(pages))
            if ok:
                verified.append({**ev, "file": f})
            else:
                rejected.append({"line": raw, "reason": reason, "file": f})
    print(json.dumps({"verified": verified, "rejected": rejected}, ensure_ascii=False, indent=1))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("slug")
    s.add_argument("name")
    v = sub.add_parser("verify")
    v.add_argument("--pages", required=True)
    v.add_argument("files", nargs="+")
    a = ap.parse_args()
    if a.cmd == "slug":
        print(slugify(a.name))
        return 0
    return cmd_verify(a.pages, a.files)


if __name__ == "__main__":
    sys.exit(main())
