"""Command-line interface for Covendard."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from fontTools.ttLib import TTFont

from covendard.builder import (
    DEFAULT_KOREAN_SCALE,
    LATIN_SOURCES,
    SUPPORTED_STYLES,
    SUPPORTED_WEIGHTS,
    FontVariant,
    get_source_variants,
    make_font_variant,
    merge_fonts,
)

logger = logging.getLogger(__name__)


def family_file_stem(family_name: str) -> str:
    """Return the output filename stem for a family name."""
    return "".join(family_name.split())


def write_css(output_web_dir: Path, family_name: str, variants: list[FontVariant]) -> Path:
    """Generate @font-face rules for compiled web fonts."""
    css_content: list[str] = []
    stem = family_file_stem(family_name)
    for variant in variants:
        font_filename = f"{stem}-{variant.output_suffix}.woff2"
        css_content.append(
            "\n".join(
                [
                    "@font-face {",
                    f"  font-family: '{family_name}';",
                    f"  src: url('./{font_filename}') format('woff2');",
                    f"  font-weight: {variant.css_weight};",
                    f"  font-style: {variant.style};",
                    "  font-display: swap;",
                    "}",
                    "",
                ]
            )
        )

    css_path = output_web_dir / f"{stem.lower()}.css"
    css_path.write_text("\n".join(css_content), encoding="utf-8")
    logger.info("Wrote web font CSS to %s", css_path)
    return css_path


def build_parser() -> argparse.ArgumentParser:
    """Build the Covendard CLI parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Build Covendard from a supported ligature-enabled Nerd Font Mono "
            "and Pretendard Korean glyphs."
        )
    )
    parser.add_argument(
        "--latin-family",
        choices=tuple(LATIN_SOURCES),
        default="caskaydiacove",
        help="Latin source family (default: caskaydiacove).",
    )
    parser.add_argument(
        "--latin-dir",
        default=None,
        help="Source TTF directory (default: upstream/<latin-family>).",
    )
    parser.add_argument(
        "--cjk-dir",
        default="upstream/pretendard",
        help="Directory containing Pretendard TTF files.",
    )
    parser.add_argument(
        "--output-dir",
        default="fonts",
        help="Directory to save generated fonts.",
    )
    parser.add_argument(
        "--family-name",
        default=None,
        help="Generated font family name (default: Covendard or Covendard JB).",
    )
    parser.add_argument(
        "--korean-scale",
        "--scale",
        dest="korean_scale",
        type=float,
        default=None,
        help=(
            "Visual scale factor for Korean/CJK glyphs after UPM normalization "
            "(without scale options: horizontal 1.20, vertical 1.15)."
        ),
    )
    parser.add_argument(
        "--korean-scale-x",
        type=float,
        default=None,
        help="Independent Korean/CJK horizontal scale (overrides --korean-scale on this axis).",
    )
    parser.add_argument(
        "--korean-scale-y",
        type=float,
        default=None,
        help="Independent Korean/CJK vertical scale (overrides --korean-scale on this axis).",
    )
    parser.add_argument(
        "--weights",
        nargs="+",
        default=None,
        help=(
            "Weights to generate. With no --styles, this builds upright variants only. "
            "Available weights depend on --latin-family."
        ),
    )
    parser.add_argument(
        "--styles",
        nargs="+",
        default=None,
        choices=SUPPORTED_STYLES,
        help="Styles to generate with --weights, or across all weights when --weights is omitted.",
    )
    parser.add_argument(
        "--variants",
        nargs="+",
        default=None,
        help=(
            "Explicit output variants to generate, for example Regular Italic BoldItalic. "
            "Cannot be combined with --weights or --styles."
        ),
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Build all supported variants of the selected Latin family.",
    )
    parser.add_argument(
        "--korean-italic-mode",
        choices=("upright",),
        default="upright",
        help=("Korean/CJK glyph policy for italic variants. Currently only upright is supported."),
    )
    return parser


def dedupe_preserving_order(values: list[str]) -> list[str]:
    """Remove duplicates while preserving user-specified order."""
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        if value in seen:
            continue
        deduped.append(value)
        seen.add(value)
    return deduped


def validate_weights(weights: list[str]) -> list[str]:
    """Validate requested weight names."""
    deduped = dedupe_preserving_order(weights)
    unsupported = [weight for weight in deduped if weight not in SUPPORTED_WEIGHTS]
    if unsupported:
        supported = ", ".join(SUPPORTED_WEIGHTS)
        msg = f"Unsupported weight(s): {', '.join(unsupported)}. Supported: {supported}"
        raise ValueError(msg)
    return deduped


def validate_styles(styles: list[str]) -> list[str]:
    """Validate requested style names."""
    deduped = dedupe_preserving_order(styles)
    unsupported = [style for style in deduped if style not in SUPPORTED_STYLES]
    if unsupported:
        supported = ", ".join(SUPPORTED_STYLES)
        msg = f"Unsupported style(s): {', '.join(unsupported)}. Supported: {supported}"
        raise ValueError(msg)
    return deduped


def select_variants(
    *,
    latin_family: str = "caskaydiacove",
    all_variants: bool = False,
    variant_names: list[str] | None = None,
    weights: list[str] | None = None,
    styles: list[str] | None = None,
) -> list[FontVariant]:
    """Resolve CLI selectors to build variants."""
    if all_variants and (variant_names or weights or styles):
        msg = "--all cannot be combined with --variants, --weights, or --styles"
        raise ValueError(msg)
    if variant_names and (weights or styles):
        msg = "--variants cannot be combined with --weights or --styles"
        raise ValueError(msg)

    available = get_source_variants(latin_family)
    if all_variants or (variant_names is None and weights is None and styles is None):
        return available

    if variant_names:
        by_name = {variant.output_suffix: variant for variant in available}
        unsupported = [name for name in variant_names if name not in by_name]
        if unsupported:
            msg = (
                f"Unsupported variant(s) for {latin_family}: {', '.join(unsupported)}. "
                f"Supported: {', '.join(by_name)}"
            )
            raise ValueError(msg)
        return [by_name[name] for name in dedupe_preserving_order(variant_names)]

    selected_weights = dedupe_preserving_order(
        weights if weights is not None else list(LATIN_SOURCES[latin_family].weights)
    )
    selected_styles = validate_styles(styles if styles is not None else ["normal"])
    return [
        make_font_variant(weight, style, latin_family=latin_family)
        for weight in selected_weights
        for style in selected_styles
    ]


def main(argv: list[str] | None = None) -> int:
    """Run the Covendard build."""
    parser = build_parser()
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

    try:
        variants = select_variants(
            latin_family=args.latin_family,
            all_variants=args.all,
            variant_names=args.variants,
            weights=args.weights,
            styles=args.styles,
        )
    except ValueError as exc:
        parser.error(str(exc))

    if args.korean_scale is None and args.korean_scale_x is None and args.korean_scale_y is None:
        args.korean_scale_x = 1.20
        args.korean_scale_y = 1.15
    if args.korean_scale is None:
        args.korean_scale = DEFAULT_KOREAN_SCALE

    latin_dir = Path(args.latin_dir or f"upstream/{args.latin_family}")
    family_name = args.family_name or LATIN_SOURCES[args.latin_family].family_name
    cjk_dir = Path(args.cjk_dir)
    base_output_dir = Path(args.output_dir)
    ttf_dir = base_output_dir / "ttf"
    otf_dir = base_output_dir / "otf"
    web_dir = base_output_dir / "webfont"

    ttf_dir.mkdir(parents=True, exist_ok=True)
    otf_dir.mkdir(parents=True, exist_ok=True)
    web_dir.mkdir(parents=True, exist_ok=True)

    stem = family_file_stem(family_name)
    logger.info(
        "Starting Covendard build for variants: %s",
        ", ".join(variant.output_suffix for variant in variants),
    )

    for variant in variants:
        latin_path = latin_dir / variant.latin_filename
        cjk_path = cjk_dir / f"Pretendard-{variant.cjk_weight_name}.ttf"
        output_path_ttf = ttf_dir / f"{stem}-{variant.output_suffix}.ttf"
        output_path_otf = otf_dir / f"{stem}-{variant.output_suffix}.otf"
        output_path_woff2 = web_dir / f"{stem}-{variant.output_suffix}.woff2"

        if not latin_path.exists():
            logger.error("Latin font file not found: %s", latin_path)
            logger.error("Run `make download LATIN_FAMILY=%s` to fetch fonts.", args.latin_family)
            return 1
        if not cjk_path.exists():
            logger.error("CJK font file not found: %s", cjk_path)
            logger.error("Run `make download` to fetch Pretendard files.")
            return 1

        try:
            stats = merge_fonts(
                latin_path=latin_path,
                cjk_path=cjk_path,
                output_path=output_path_ttf,
                family_name=family_name,
                subfamily_name=variant.subfamily_name,
                korean_scale=args.korean_scale,
                korean_scale_x=args.korean_scale_x,
                korean_scale_y=args.korean_scale_y,
                typographic_subfamily_name=variant.typographic_subfamily_name,
                is_italic=variant.is_italic,
                css_weight=variant.css_weight,
            )
            logger.info(
                "%s: copied=%d capped=%d latin_advance=%d korean_advance=%d",
                variant.output_suffix,
                stats.copied_count,
                stats.capped_count,
                stats.latin_advance,
                stats.korean_advance,
            )

            logger.info("Saving OTF-compatible output: %s", output_path_otf)
            otf_font = TTFont(str(output_path_ttf))
            otf_font.save(str(output_path_otf))
            TTFont(str(output_path_otf)).close()
            otf_font.close()

            logger.info("Converting to WOFF2: %s", output_path_woff2)
            web_font = TTFont(str(output_path_ttf))
            web_font.flavor = "woff2"
            web_font.save(str(output_path_woff2))
            web_font.close()
        except Exception:
            logger.exception("Failed to build variant %s", variant.output_suffix)
            return 1

    write_css(web_dir, family_name, variants)
    logger.info("All requested Covendard variants built successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
