import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

from profile_tools import parse_evidence, slugify, verify_one  # noqa: E402

PAGE = "Il a déclaré : « Nous **baisserons** les impôts dès 2027 » au [Sénat](https://x.example)."


def line(grade="B2", quote="Nous baisserons les impôts dès 2027", page="page.md"):
    return f'- [{grade}] Promet une baisse d\'impôts :: "{quote}" :: https://x.example/a :: 2026-10-01 :: {page}'


class TestSlug(unittest.TestCase):
    def test_cases(self):
        self.assertEqual(slugify("Jean-Luc Mélenchon"), "jean-luc-melenchon")
        self.assertEqual(slugify("Dominique de Villepin"), "dominique-de-villepin")
        self.assertEqual(slugify("  Ségolène   Royal "), "segolene-royal")
        self.assertEqual(slugify("Alexandria Ocasio-Cortez"), "alexandria-ocasio-cortez")
        self.assertEqual(slugify("Olaf Schölz"), "olaf-scholz")
        self.assertEqual(slugify("Ursula von der Leyen"), "ursula-von-der-leyen")


class TestVerify(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.pages = Path(self.tmp.name)
        (self.pages / "page.md").write_text(PAGE, encoding="utf-8")
        (self.pages / "vide.md").write_text("", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, ln):
        ev = parse_evidence(ln)
        self.assertIsNotNone(ev)
        return verify_one(ev, self.pages)

    def test_parse_fields(self):
        ev = parse_evidence(line())
        self.assertEqual(ev["grade"], "B2")
        self.assertEqual(ev["quote"], "Nous baisserons les impôts dès 2027")
        self.assertEqual(ev["url"], "https://x.example/a")
        self.assertEqual(ev["date"], "2026-10-01")
        self.assertEqual(ev["page"], "page.md")

    def test_exact_quote_verified(self):
        self.assertEqual(self.check(line()), (True, ""))

    def test_typographic_variants_verified(self):
        (self.pages / "apos.md").write_text("C’est l’heure  de partir.", encoding="utf-8")
        self.assertEqual(self.check(line(quote="C'est l'heure de partir", page="apos.md")), (True, ""))

    def test_paraphrase_rejected(self):
        self.assertEqual(self.check(line(quote="Nous réduirons les impôts")), (False, "citation absente de la page"))

    def test_bad_grade_rejected(self):
        self.assertEqual(self.check(line(grade="G7")), (False, "note invalide"))

    def test_long_quote_rejected(self):
        q = " ".join(["mot"] * 26)
        self.assertEqual(self.check(line(quote=q)), (False, "citation trop longue"))

    def test_missing_page_rejected(self):
        self.assertEqual(self.check(line(page="nope.md")), (False, "page introuvable"))

    def test_empty_page_rejected(self):
        self.assertEqual(self.check(line(page="vide.md")), (False, "page vide"))

    def test_malformed_line(self):
        self.assertIsNone(parse_evidence("- [B2] juste du texte"))

    def test_cli_json(self):
        ev_file = self.pages / "evidence.md"
        ev_file.write_text(
            "# preuves\n" + line() + "\n" + line(quote="Nous réduirons les impôts") + "\n- [B2] juste du texte\n",
            encoding="utf-8",
        )
        out = subprocess.run(
            [sys.executable, str(SCRIPTS / "profile_tools.py"), "verify", "--pages", str(self.pages), str(ev_file)],
            capture_output=True, text=True, check=True,
        )
        data = json.loads(out.stdout)
        self.assertEqual(len(data["verified"]), 1)
        self.assertEqual([r["reason"] for r in data["rejected"]], ["citation absente de la page", "ligne mal formée"])

    def test_cli_missing_input_exit_2(self):
        out = subprocess.run(
            [sys.executable, str(SCRIPTS / "profile_tools.py"), "verify", "--pages", str(self.pages), "/nonexistent.md"],
            capture_output=True, text=True,
        )
        self.assertEqual(out.returncode, 2)

    def test_cli_slug(self):
        out = subprocess.run(
            [sys.executable, str(SCRIPTS / "profile_tools.py"), "slug", "Jean-Luc Mélenchon"],
            capture_output=True, text=True, check=True,
        )
        self.assertEqual(out.stdout.strip(), "jean-luc-melenchon")


if __name__ == "__main__":
    unittest.main()
