#!/usr/bin/env python3
"""Check local HTML links and bilingual navigation using only Python's stdlib.

Run: python3 scripts/check_links.py [SITE_ROOT]
External URLs, assets, and browser/JavaScript behavior are outside this check.
"""

import argparse
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import parse_qs, unquote, urljoin, urlsplit


SITE_URL = "https://kawasakidaik.github.io/"


@dataclass
class Link:
    line: int
    href: str
    attrs: dict
    in_nav: bool
    text: str = ""

    @property
    def is_language_switch(self):
        return "data-language-switch" in self.attrs or self.text.strip() in {"EN", "JP"}


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids = set()
        self.targets = set()
        self.sections = set()
        self.duplicates = []
        self.links = []
        self.language = None
        self.has_nav = False
        self.in_nav = False
        self.active_link = None
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        identifier = attrs.get("id")
        if identifier:
            if identifier in self.ids:
                self.duplicates.append((self.getpos()[0], identifier))
            self.ids.add(identifier)
            self.targets.add(identifier)
            if tag == "section" or identifier == "publication":
                self.sections.add(identifier)
        if tag == "html":
            self.language = attrs.get("lang")
        if tag == "nav":
            self.in_nav = self.has_nav = True
        if tag == "a":
            if attrs.get("name"):
                self.targets.add(attrs["name"])
            if "href" in attrs:
                self.active_link = Link(self.getpos()[0], attrs["href"] or "", attrs, self.in_nav)
                self.links.append(self.active_link)

    def handle_data(self, text):
        if self.active_link:
            self.active_link.text += text

    def handle_endtag(self, tag):
        if tag == "nav":
            self.in_nav = False
        elif tag == "a":
            self.active_link = None


def counterpart(path):
    stem = path.stem
    return path.with_name((stem[:-3] if stem.endswith("_en") else stem + "_en") + path.suffix)


def language(path):
    return "en" if path.stem.endswith("_en") else "ja"


def local_target(source, href):
    """Resolve relative, root-relative, query-only and same-origin absolute URLs."""
    url = urlsplit(urljoin(SITE_URL + source.as_posix(), href))
    if url.scheme not in {"http", "https"} or url.netloc.lower() != urlsplit(SITE_URL).netloc:
        return None
    path = unquote(url.path).lstrip("/")
    if not path or path.endswith("/"):
        path += "index.html"
    return Path(path), unquote(url.fragment), parse_qs(url.query, keep_blank_values=True)


def check(root):
    pages = {p.relative_to(root): Page(p.read_text(encoding="utf-8"))
             for p in sorted(root.rglob("*.html")) if ".git" not in p.relative_to(root).parts}
    errors = []
    checked = 0

    def error(source, line, message):
        errors.append(f"{source.as_posix()}:{line}: {message}")

    for source, page in pages.items():
        for line, identifier in page.duplicates:
            error(source, line, f"duplicate id: {identifier!r}")
        other = counterpart(source)
        if page.has_nav:
            if page.language != language(source):
                error(source, 1, f"expected html lang={language(source)!r}, got {page.language!r}")
            switches = [link for link in page.links if link.is_language_switch and link.in_nav]
            if len(switches) != 2:
                error(source, 1, f"expected desktop and mobile language switches, found {len(switches)}")
            if other not in pages:
                error(source, 1, f"missing language counterpart: {other}")
            else:
                for anchor in sorted(page.sections - pages[other].targets):
                    error(source, 1, f"content anchor #{anchor} missing from counterpart {other}")

        for link in page.links:
            try:
                target = local_target(source, link.href)
            except ValueError as exc:
                error(source, link.line, f"invalid URL {link.href!r}: {exc}")
                continue
            if target is None:
                continue
            destination, anchor, query = target
            checked += 1
            if link.href.count("#") > 1:
                error(source, link.line, f"multiple fragment delimiters: {link.href!r}")
            if "skiploading" in query and query["skiploading"] != ["true"]:
                error(source, link.line, f"invalid skiploading value: {link.href!r}")
            if destination not in pages:
                if destination.suffix.lower() in {".html", ".htm"} or not (root / destination).is_file():
                    error(source, link.line, f"missing local target: {link.href!r}")
                continue
            if anchor and anchor not in pages[destination].targets:
                error(source, link.line, f"missing fragment target: {link.href!r}")
            if link.is_language_switch:
                if destination != other:
                    error(source, link.line, f"language switch must target {other}, got {link.href!r}")
            elif page.has_nav and language(source) != language(destination):
                error(source, link.line, f"cross-language link outside language switch: {link.href!r}")
    return pages, checked, errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    root = args.root.resolve()
    if not root.is_dir():
        parser.error(f"site root is not a directory: {root}")
    pages, checked, errors = check(root)
    if not pages:
        parser.error(f"no HTML files found under {root}")
    for message in errors:
        print(message)
    print(f"{'FAIL' if errors else 'OK'}: {len(pages)} HTML files, {checked} local links, {len(errors)} problems")
    return bool(errors)


if __name__ == "__main__":
    raise SystemExit(main())
