# KawasakiDaik.github.io

## Link validation

Run from the repository root (Python 3.10+, no third-party dependencies):

```sh
python3 scripts/check_links.py
python3 -m unittest discover -s tests
```

If Node.js 18+ is available, test anchor preservation without a browser:

```sh
node --test tests/test_language_switch.cjs
```

The checker validates local HTML destinations, fragment IDs (including unquoted
IDs and legacy named anchors), duplicate IDs, `skiploading` values, language
consistency, and desktop/mobile language switches. It ignores commented-out
links. It exits with a nonzero status when a problem is found.

To check another source snapshot, pass its directory:

```sh
python3 scripts/check_links.py /path/to/snapshot
```

Language switches point to the corresponding page in the other language even
without JavaScript. `assets/js/language-switch.js` also preserves shared content
anchors such as `#works`, `#publication`, and `#contact`; unknown or malformed
fragments fall back to the corresponding page. The index-page switches retain
`?skiploading=true`.

These checks inspect source files locally. They do not test external URL
availability, assets, page rendering, or browser interaction.
