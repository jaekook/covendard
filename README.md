# Jetendard

[Research and work records (Korean)](docs/README.md)

This project is heavily inspired by
[Yeomil Mono](https://github.com/taevel02/yeomil-mono) and reuses much of its
implementation with minimal changes. Compared with
[Yeomil Mono](https://github.com/taevel02/yeomil-mono), Jetendard uses
JetBrainsMono Nerd Font Mono instead of
[Geist Mono](https://github.com/vercel/geist-font/tree/main/fonts/GeistMono)
and applies a `1.15` scale to
[Pretendard](https://github.com/orioncactus/pretendard). Slightly enlarging
Pretendard reduces unnecessary spacing around Korean glyphs, making Korean word
spacing feel more visually stable while improving the clarity and precision of
Hangul rendering.

Jetendard is a reproducible font build project that combines
[JetBrainsMono Nerd Font Mono](https://github.com/ryanoasis/nerd-fonts) with
[Pretendard](https://github.com/orioncactus/pretendard) Korean glyphs.

The generated family is named `Jetendard`. Latin glyphs, programming ligatures,
and Nerd Font symbols come from the ligature-enabled `JetBrainsMonoNerdFontMono`
files. Korean and CJK glyphs come from Pretendard and are fitted into exactly two
Latin monospace advances.

CaskaydiaCove Nerd Font Mono is also supported as an alternative Latin source,
producing the `Jetendard Cove` family. Both sources retain programming ligatures.

**Zed Editor (font size 13.5)**
![screenshot](assets/screeshots/screenshot-2026-07-06-at-3.38.07-pm.png)

**Zed Editor (Korean comments)**
![screenshot](assets/screeshots/screenshot-2026-07-07-at-10.59.35-am.png)

**Ghostty Terminal (Text Output)**
![screenshot](assets/screeshots/screenshot-2026-07-06-at-4.59.31-pm.png)

**Ghostty Terminal (Codex)**
![screenshot](assets/screeshots/screenshot-2026-07-06-at-10.44.13-pm.png)


## Build

```bash
uv sync --all-groups
make download
make run
make test
```

`make run` builds the full 16-variant family. 

Generated files are written to:

- `fonts/ttf/Jetendard-*.ttf`
- `fonts/otf/Jetendard-*.otf`
- `fonts/webfont/Jetendard-*.woff2`
- `fonts/webfont/jetendard.css`

Generated outputs and upstream downloads are intentionally ignored by git.

### CaskaydiaCove build

To build Regular, Italic, Bold, and BoldItalic with the CaskaydiaCove base:

```bash
make download LATIN_FAMILY=caskaydiacove
uv run jetendard --latin-family caskaydiacove --variants Regular Italic Bold BoldItalic
```

Outputs use `JetendardCove-*.ttf`, `JetendardCove-*.otf`,
`JetendardCove-*.woff2`, and `jetendardcove.css` in the usual output directories.
Select **Jetendard Cove** in the editor or terminal after installing the fonts.
`--family-name` can override the output family name. Korean remains upright at
the default `1.15` scale, with an advance of exactly two Latin cells.

`make run LATIN_FAMILY=caskaydiacove` builds all ten supported variants:
ExtraLight, Light, Regular, SemiBold, and Bold, each upright and italic. The
pinned CascadiaCode archive also contains SemiLight, but it is excluded because
Pretendard has no same-named static source. Thin, Medium, and ExtraBold are not
available in this Latin source. Unsupported selections fail before generating
output. Downloads are placed in `upstream/caskaydiacove` and use Nerd Fonts
v3.4.0; the source note is `upstream/SOURCES-caskaydiacove.md`.

## CLI

For a comparison Regular with wider Korean outlines at the same two-cell
advance and unchanged Latin glyphs:

```bash
uv run jetendard --latin-family caskaydiacove --variants Regular \
  --family-name "Jetendard Cove Compact" --korean-scale-x 1.20 --korean-scale-y 1.15
```

Install `fonts/ttf/JetendardCoveCompact-Regular.ttf` and select
`Jetendard Cove Compact`. Either axis option enables independent fitting;
an unspecified axis inherits `--korean-scale` (default `1.15`). Without axis
options the existing uniform scaling and proportional clipping behavior is
preserved. Wider outlines reduce side space but do not shorten the text advance.

```bash
uv run jetendard --help
```

Important options:

- `--latin-family`: `jetbrainsmono` (default) or `caskaydiacove`
- `--latin-dir`: source directory override (default: `upstream/<latin-family>`)
- `--cjk-dir`: directory containing `Pretendard-*.ttf`
- `--all`: build all supported variants (16 for JetBrains Mono, 10 for CaskaydiaCove)
- `--variants`: explicit output variants such as `Regular`, `Italic`, or `BoldItalic`
- `--weights`: weights to build; without `--styles`, this selects upright variants
- `--styles`: `normal`, `italic`, or both
- `--korean-italic-mode`: Korean/CJK policy for italic variants, currently `upright`
- `--korean-scale`: visual scale for Korean/CJK glyph fitting
- `--scale`: compatibility alias for `--korean-scale`
- `--korean-scale-x`, `--korean-scale-y`: independent horizontal/vertical overrides

The default Korean scale is `1.15`.

Examples:

```bash
uv run jetendard --all
uv run jetendard --weights Regular Bold --styles normal italic
uv run jetendard --variants Regular Light Bold
```

## Variant Coverage

Jetendard builds every ligature-enabled `JetBrainsMonoNerdFontMono` Mono TTF
variant present in the pinned Nerd Fonts archive:

| Weight | Upright | Italic | Pretendard Korean/CJK source |
| --- | --- | --- | --- |
| Thin | `Jetendard-Thin` | `Jetendard-ThinItalic` | `Pretendard-Thin` |
| ExtraLight | `Jetendard-ExtraLight` | `Jetendard-ExtraLightItalic` | `Pretendard-ExtraLight` |
| Light | `Jetendard-Light` | `Jetendard-LightItalic` | `Pretendard-Light` |
| Regular | `Jetendard-Regular` | `Jetendard-Italic` | `Pretendard-Regular` |
| Medium | `Jetendard-Medium` | `Jetendard-MediumItalic` | `Pretendard-Medium` |
| SemiBold | `Jetendard-SemiBold` | `Jetendard-SemiBoldItalic` | `Pretendard-SemiBold` |
| Bold | `Jetendard-Bold` | `Jetendard-BoldItalic` | `Pretendard-Bold` |
| ExtraBold | `Jetendard-ExtraBold` | `Jetendard-ExtraBoldItalic` | `Pretendard-ExtraBold` |

Pretendard does not provide true static italic Korean/CJK fonts in the pinned
archive, so italic Jetendard variants use italic JetBrainsMono Latin glyphs and
upright Pretendard Korean/CJK glyphs. The generated font metadata and CSS still
identify those variants as italic.

## Scope

The default source uses `JetBrainsMonoNerdFontMono`. It does not use
`JetBrainsMonoNerdFont`, `JetBrainsMonoNerdFontPropo`, or `JetBrainsMonoNL`
no-ligature variants. Because the base font is already Nerd Font patched, this
project does not run a second Nerd Fonts patching step.

The alternative source uses `CaskaydiaCoveNerdFontMono`, not the
ligature-free `CaskaydiaMono` family or the Propo variant.

`Pretendard-Black` is not built by default because the confirmed
`JetBrainsMonoNerdFontMono` archive does not contain a matching Black source.
The downloader also extracts `PretendardVariable.ttf` when available for future
custom-weight work.

## Visual Check Samples

Use the same renderer, point size, and line height when comparing Jetendard
against yeomil-mono or another monospace baseline:

```text
Jetendard 테스트 ABC abc 0123456789
가각간갇갈감갑값같꿇뷁힣
한글과 English가 섞인 source comment
if (상태 === "완료") return "성공";
ㄱㄴㄷㅏㅑㅓㅕㅗㅛㅜㅠㅡㅣ
（）［］｛｝，．：；！？
```

## Release Packaging

The build writes installable files under `fonts/ttf`, `fonts/otf`, and
`fonts/webfont`. Release archives can be prepared from those directories after a
manual visual pass confirms the default Korean scale across upright and italic
variants. The OTF files are OTF-compatible outputs using the same TrueType
outlines as the generated TTFs.

## Project Analysis

Source review recorded on 2026-09-11. This describes the current implementation;
rendering behavior still needs verification with generated fonts.

### Architecture

| Component | Responsibility |
| --- | --- |
| `download_upstream.py` | Download pinned Nerd Fonts v3.4.0 and Pretendard 1.3.9 archives and extract expected fonts |
| `src/jetendard/builder.py` | Define variants, fit and copy glyphs, add Hangul composition, and update font metadata |
| `src/jetendard/cli.py` | Select variants and produce TTF, TrueType-outline OTF, WOFF2, and CSS outputs |
| `tests/` | 31 test functions covering helpers and optional font integration checks |

The project uses Python 3.12, `uv`, `fontTools`, and Brotli. The build retains
the Latin base font and copies selected Pretendard Korean/CJK outlines into it.
It normalizes units per em, applies the requested Korean scale, caps each
glyph to fit horizontal and vertical limits, and centers it within a two-cell
advance. The `FontVariant` model keeps the 16 weight/style combinations and
their filenames and metadata together. Small helper functions and pinned
dependency/source inputs make the implementation straightforward to inspect.

### Findings and verification gaps

- **Conditional GSUB feature-reference issue:** when a base font has GSUB but
  no `ccmp` feature, `add_hangul_ccmp_features` inserts and sorts a new feature
  without updating existing Script/LangSys feature indices or attaching the
  new feature to those language systems. That path can leave composition
  inactive or existing references incorrect. Whether the pinned base fonts
  take this path was not verified during the initial review.
- **Shaping coverage:** integration tests inspect feature presence, selected
  metrics, and metadata, but do not shape decomposed Hangul or programming
  ligatures to verify their resulting glyphs. The full 16-variant test requires
  `JETENDARD_RUN_FULL_INTEGRATION=1`; source-dependent tests skip when fonts
  are missing. No repository CI workflow is currently present.
- **Download recovery:** any non-empty cached archive is reused without a
  checksum check. `make ensure-upstream` checks directories rather than the
  required files in the original implementation. The source-family update now
  checks required files and retries extraction for missing or empty files;
  corrupt cached archives still need additional recovery handling.
- **Output consistency:** variants and formats are written directly to their
  final paths. A failure partway through can leave a mixture of old and new
  outputs; staging and replacing a completed build would avoid this.

Prioritize GSUB reference handling and actual shaping tests, then download
recovery and consistent output publication.

Initial verification: all seven Python files passed AST parsing using the
Python 3.12 grammar. Tests, lint, and font builds were not run because the
review environment lacked `uv`, `pytest`, `ruff`, `fontTools`, and upstream
fonts. Syntax parsing alone does not establish runtime correctness.

### Alternative Latin fonts and Korean spacing

Follow-up research on 2026-09-11 used the version-tagged Regular TTF files from
[Nerd Fonts v3.4.0](https://github.com/ryanoasis/nerd-fonts/tree/v3.4.0/patched-fonts)
and [Pretendard v1.3.9](https://github.com/orioncactus/pretendard/tree/v1.3.9/packages).
The comparison included `PretendardGOV-Regular.ttf` because the supplied visual
reference was a Pretendard GOV specimen. Jetendard currently uses ordinary
Pretendard, not GOV. The referenced NamuWiki page could not be inspected, and
its downloaded specimen rendered black in the inspection tool, so its exact
layout and displayed spacing were not measured.

**Initial finding, before the source-family implementation:** replacing the
Latin base was feasible, but not exposed as a family selector.
`merge_fonts` accepts a Latin font path and derives its metrics from the file.
However, `make_font_variant` hardcodes `JetBrainsMonoNerdFontMono-*` filenames,
and the downloader and default matrix are also specific to JetBrains Mono.
Changing `--latin-dir` alone does not select another family.

The Cascadia Code family in Nerd Fonts is named
[CaskaydiaCove Nerd Font](https://github.com/ryanoasis/nerd-fonts/tree/v3.4.0/patched-fonts/CascadiaCode).
Its `CaskaydiaCoveNerdFontMono-*.ttf` files are suitable candidates for the
current TrueType-based merger. In v3.4.0 it has ExtraLight, Light, SemiLight,
Regular, SemiBold, and Bold, each upright and italic. This differs from the
current eight-weight matrix: Thin, Medium, and ExtraBold are absent, and
SemiLight has no same-named Pretendard source. Supporting the family properly
requires source/download profiles and an explicit weight mapping or a supported
subset. Test glyph coverage, composition, programming ligatures, style metadata,
and vertical fitting for the selected family; arbitrary Nerd Fonts are not
automatically compatible.

**The build changes Korean spacing, independently of the renderer.** The table
below gives unshaped horizontal advances normalized by units per em, measured
from Regular source fonts and two temporary merged TTFs:

| Font | Units per em | `A` advance / em | `가` advance / em |
| --- | --- | --- | --- |
| Pretendard Regular | 2048 | 1322 / 2048 = 0.6455 | 1770 / 2048 = 0.8643 |
| Pretendard GOV Regular | 2048 | 1322 / 2048 = 0.6455 | 1770 / 2048 = 0.8643 |
| Current JetBrains Mono merge | 1000 | 600 / 1000 = 0.6000 | 1200 / 1000 = 1.2000 |
| Experimental CaskaydiaCove merge | 2048 | 1200 / 2048 = 0.5859 | 2400 / 2048 = 1.1719 |

For `가`, the original outline width is approximately `0.8066em`; at the default
scale it becomes `0.9276em` in both merges without hitting the fitting cap.
The remaining horizontal space within the advance is therefore approximately
`0.0576em` in the source, `0.2724em` in Jetendard, and `0.2442em` in the
CaskaydiaCove experiment. This is the combined side space for that glyph, not
a universal gap for every pair of characters.

At the same font size, Jetendard's Korean advance is about 38.9% wider than the
source's. When font sizes are adjusted to match the 1.15-scaled outline size,
the advance remains about 20.7% wider: `1.2 / (0.8642578125 * 1.15) - 1`.
This provides a concrete explanation for a perceived 10–20% spacing difference,
but is not a pixel measurement of the supplied specimen. The sampled characters
`가나다한글머신` have identical advances and bounds in Pretendard and GOV Regular;
changing to GOV alone would not fix those gaps. Word spaces are a separate
metric: the merge retains the Latin base's space width.

Commit `1b1b693` raised the default Korean outline scale from `1.08` to `1.15`
to reduce visual whitespace. It did not reduce the two-cell advance. Increasing
`--korean-scale` further, for example comparing `1.20` and `1.25`, can reduce
side space, but also increases glyph height and may hit per-glyph limits.
For Cove Regular, follow-up measurements show that most Hangul syllables hit
vertical limits at those uniform scales. Independent horizontal/vertical scaling
is implemented by the Compact experiment described in the
[Korean spacing research](docs/korean-spacing-research.ko.md).
Reducing only Korean advance would violate the two-cell alignment invariant.
CaskaydiaCove reduces that advance by only about 2.34% relative to JetBrains Mono,
so changing Latin families alone is not a complete spacing adjustment.

Web and terminal layout can add differences: CSS
[`letter-spacing`](https://www.w3.org/TR/css-text-3/#letter-spacing-property)
can alter spacing, while Ghostty exposes
[`adjust-cell-width`](https://ghostty.org/docs/config/reference#adjust-cell-width)
to adjust the terminal grid. Compare the same generated font, text, weight,
effective font size, and default spacing before attributing a remaining
difference to rendering. A specimen image's spacing is baked into the image;
the surrounding webpage's text CSS does not change gaps inside it.

Follow-up verification used the lockfile's hash-verified `fontTools 4.63.0`
wheel in a temporary directory with the available Python 3.14.7. Direct calls
to the unchanged `merge_fonts` successfully saved and reopened Regular TTFs for
both Latin families. Each copied 11,469 glyphs; fitting capped 0 glyphs for
JetBrains Mono and 25 for CaskaydiaCove. Both passed checks for two-cell Korean
width, `ccmp`/`calt` presence, and the U+E0B0 Powerline symbol. Both Regular base
fonts already contain `ccmp`, so they do not take the missing-feature path
described above. These experiments do not verify shaping, GUI rendering, other
weights/styles, WOFF2 output, or the pinned Python 3.12 test suite. No builder
code, default font selection, or scale setting was changed.

### Build verification in the current environment

The initial environment limitations above were resolved later on 2026-09-11.
Using `uv 0.11.19` and managed Python 3.12.13, `uv sync --locked --all-groups`
installed the committed dependencies into `.venv` without changing `uv.lock`.

- `make lint` passed formatting and lint checks.
- `make build` produced the Python source distribution and wheel.
- `make download` prepared the pinned upstream sources.
- `make test` passed 30 tests; the opt-in full-matrix test was skipped.
- `make run` successfully built all 16 default JetBrains Mono variants, producing
  16 TTFs, 16 TrueType-outline OTFs, 16 WOFF2s, and CSS with 16 `@font-face` rules.
- All 48 font files were reopened and checked for two-cell Korean advance,
  italic flags, weight metadata, and the U+E0B0 symbol.

Actual GUI rendering and shaping were not verified in that initial full build,
which used the existing default family. CaskaydiaCove CLI/downloader support was
added subsequently; see the CaskaydiaCove build instructions above.
Locally, `uv` is installed at `~/.local/bin/uv`; if needed, add
`~/.local/bin` to `PATH` before running the Makefile commands.

### CaskaydiaCove implementation verification

After deleting the previous build outputs, upstream downloads, and temporary
experiments, the source-family implementation built Regular, Italic, Bold, and
BoldItalic as `Jetendard Cove`. All 12 TTF/OTF/WOFF2 files were reopened and
checked for family names, weight/style metadata, the two-cell Korean advance
(2400 units versus 1200 for Latin), and U+E0B0 coverage. The CSS contains four
matching font-face rules. The Korean scale remains `1.15`.

Formatting and lint passed. The suite passed 36 tests; three legacy JetBrains
Mono integration tests were skipped because its sources were removed or the
full-matrix opt-in was unset. A separate HarfBuzz check using `uharfbuzz 0.53.0`
compared 12 programming-operator sequences per variant against the original
CaskaydiaCove font: glyph IDs and positions matched, and disabling `calt`
changed the shaping results. NFC and NFD forms of `가각간한글값힣` also produced
identical non-missing glyphs with two-cell advances in each output TTF.
GUI rendering and the other six supported Cove variants remain unverified.

Further analysis of the Monatendard discussion, terminal cell widths, space
padding, and independent Korean scaling is recorded in
[Korean spacing research](docs/korean-spacing-research.ko.md).

## License

Jetendard is distributed under the [SIL Open Font License 1.1](LICENSE). Review
the upstream JetBrains Mono, Nerd Fonts, Pretendard, and Yeomil Mono projects for
their full copyright and reserved-name notices.
