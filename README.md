# Covendard

[한국어](README.ko.md) · [Website](https://jaekook.dev/covendard/) · [Research](docs/README.md)

CaskaydiaCove Nerd Font Mono meets Pretendard. Covendard preserves programming ligatures,
Nerd Font icons, and one Latin cell to two Korean cells, with fuller Korean outlines.
Its default Korean scale is **1.20 horizontally / 1.15 vertically**. This is the
Compact configuration developed and tried in Jetendard, now a separate font family.
Italic styles use italic Latin with upright Korean.

## Install

Download `Covendard.zip` from the website, extract it, install the four files in `ttf/`,
and select **Covendard** in your editor or terminal. The release includes Regular,
Italic, Bold, and BoldItalic, plus WOFF2 copies. OTF is also generated locally.
OTF files retain TrueType outlines; they are not CFF conversions.

## Build

Python 3.12 and uv are required. Versions are recorded in `uv.lock`.

```sh
uv sync --locked --all-groups
make download
make run
make lint test
make build
uv run python scripts/package_release.py
```

`make run` builds four release styles. `make run-all` or `uv run covendard --all`
builds all ten supported Cove styles: ExtraLight, Light, Regular, SemiBold, Bold,
upright and italic. SemiLight has no same-named static Pretendard source.

```sh
uv run covendard --variants Regular Italic Bold BoldItalic
uv run covendard --variants Regular --korean-scale-x 1.20 --korean-scale-y 1.15
uv run covendard --help
```

With no scale options, the CLI uses independent 1.20/1.15 scaling. Explicit
`--korean-scale 1.15` selects the original uniform fitting mode. An axis option enables
independent fitting; an omitted axis inherits `--korean-scale` (1.15 if omitted).
The advance stays two Latin cells; enlarging outlines reduces side space, not line length.

`--latin-family jetbrainsmono` retains the alternative source as **Covendard JB**.
Downloads are pinned to Nerd Fonts v3.4.0 and Pretendard 1.3.9.
Generated fonts, ZIP files and upstream sources are not tracked in Git.
The package script writes `dist/Covendard.zip` and a SHA-256 checksum; it can also
copy release assets to the site using `--site-dir ../cloudflare-pages/public/covendard`.

## Credits and license

Derived from [Jetendard](https://github.com/jaekook/jetendard), which credits
[Yeomil Mono](https://github.com/taevel02/yeomil-mono). Latin glyphs and ligatures come
from [Cascadia Code](https://github.com/microsoft/cascadia-code), patched by
[Nerd Fonts](https://github.com/ryanoasis/nerd-fonts). Korean/CJK comes from
[Pretendard](https://github.com/orioncactus/pretendard).
Original author notices and OFL terms are retained in [LICENSE](LICENSE) and `licenses/`.
Historical research intentionally retains the names used at the time.
