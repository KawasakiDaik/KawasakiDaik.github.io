"""Regression cases for the dependency-free source link checker."""

import tempfile
import unittest
from pathlib import Path

from scripts.check_links import Page, check


class LinkChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for filename, lang, other, label in [
            ("index.html", "ja", "index_en.html", "EN"),
            ("index_en.html", "en", "index.html", "JP"),
        ]:
            switch = f'<a href="{other}?skiploading=true">{label}</a>'
            (self.root / filename).write_text(
                f'<html lang="{lang}"><nav>{switch}{switch}</nav>'
                '<section id=home></section></html>', encoding="utf-8")

    def append(self, filename, html):
        path = self.root / filename
        path.write_text(path.read_text(encoding="utf-8") + html, encoding="utf-8")

    def problems(self):
        return "\n".join(check(self.root)[2])

    def test_unquoted_ids_comments_and_switch_fragments(self):
        self.append("index.html", '<a href="index_en.html#absent">EN</a>'
                    '<!-- <a href="missing.html#absent">example</a> -->'
                    '<a href="index.html?skiploading=true#home">HOME</a>')
        # A language switch must also resolve its fragment.
        self.assertIn("missing fragment", self.problems())
        page = Page('<section id=overview></section><!-- <div id=ghost> -->')
        self.assertEqual(page.targets, {"overview"})

    def test_valid_relative_absolute_and_encoded_fragments(self):
        self.append("index.html", '<a name="日本語"></a>'
                    '<a href="/%69ndex.html#%E6%97%A5%E6%9C%AC%E8%AA%9E">named</a>'
                    '<a href="https://KawasakiDaik.github.io/index.html#home">home</a>'
                    '<a href="?skiploading=true#home">query</a>'
                    '<!-- <a href="missing.html">comment</a> -->'
                    '<a href="mailto:example@example.com">email</a>'
                    '<a href="https://example.com/#absent">external</a>')
        self.assertEqual(self.problems(), "")

    def test_missing_file_and_fragment(self):
        self.append("index.html", '<a href="missing.html">bad</a><a href="#absent">bad</a>')
        self.assertIn("missing local target", self.problems())
        self.assertIn("missing fragment target", self.problems())

    def test_home_link_typos(self):
        self.append("index.html", '<a href="index.html?skiploading=truel#home">HOME</a>'
                    '<a href="index.html?skiploading=true#contact#home">HOME</a>')
        self.assertIn("invalid skiploading", self.problems())
        self.assertIn("multiple fragment delimiters", self.problems())

    def test_cross_language_news(self):
        self.append("index_en.html", '<a href="index.html#home">news</a>')
        self.assertIn("cross-language link", self.problems())

    def test_switch_must_target_same_page_counterpart(self):
        self.append("index_en.html", '<a href="index_en.html">JP</a>')
        self.assertIn("language switch must target index.html", self.problems())

    def test_duplicate_ids_and_missing_shared_anchor(self):
        self.append("index.html", '<section id="home"></section><section id="works"></section>')
        self.assertIn("duplicate id", self.problems())
        self.assertIn("content anchor #works missing from counterpart", self.problems())

    def test_missing_switch_and_wrong_html_language(self):
        (self.root / "index_en.html").write_text('<html lang="ja"><nav></nav></html>', encoding="utf-8")
        self.assertIn("expected html lang='en'", self.problems())
        self.assertIn("language switches, found 0", self.problems())


if __name__ == "__main__":
    unittest.main()
