"""Font merging and fitting logic for Covendard."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

from fontTools.feaLib.builder import addOpenTypeFeaturesFromString
from fontTools.otlLib.builder import buildLigatureSubstSubtable, buildLookup
from fontTools.pens.boundsPen import BoundsPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from fontTools.pens.transformPen import TransformPen
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables import otTables

logger = logging.getLogger(__name__)

Bounds = tuple[float, float, float, float]

DEFAULT_KOREAN_SCALE = 1.15
ASCII_WIDTH_SAMPLE = tuple(ord(char) for char in " A0Hinmw")


CHOSEONG_MAP = {
    0x1100: 0x3131,
    0x1101: 0x3132,
    0x1102: 0x3134,
    0x1103: 0x3137,
    0x1104: 0x3138,
    0x1105: 0x3139,
    0x1106: 0x3141,
    0x1107: 0x3142,
    0x1108: 0x3143,
    0x1109: 0x3145,
    0x110A: 0x3146,
    0x110B: 0x3147,
    0x110C: 0x3148,
    0x110D: 0x3149,
    0x110E: 0x314A,
    0x110F: 0x314B,
    0x1110: 0x314C,
    0x1111: 0x314D,
    0x1112: 0x314E,
}
JUNGSEONG_MAP = {code: 0x314F + (code - 0x1161) for code in range(0x1161, 0x1175 + 1)}
JONGSEONG_MAP = {
    0x11A8: 0x3131,
    0x11A9: 0x3132,
    0x11AA: 0x3133,
    0x11AB: 0x3134,
    0x11AC: 0x3135,
    0x11AD: 0x3136,
    0x11AE: 0x3137,
    0x11AF: 0x3139,
    0x11B0: 0x313A,
    0x11B1: 0x313B,
    0x11B2: 0x313C,
    0x11B3: 0x313D,
    0x11B4: 0x313E,
    0x11B5: 0x313F,
    0x11B6: 0x3140,
    0x11B7: 0x3141,
    0x11B8: 0x3142,
    0x11B9: 0x3144,
    0x11BA: 0x3145,
    0x11BB: 0x3146,
    0x11BC: 0x3147,
    0x11BD: 0x3148,
    0x11BE: 0x314A,
    0x11BF: 0x314B,
    0x11C0: 0x314C,
    0x11C1: 0x314D,
    0x11C2: 0x314E,
}
JAMO_COMPATIBILITY_MAP = CHOSEONG_MAP | JUNGSEONG_MAP | JONGSEONG_MAP


@dataclass(frozen=True)
class FittedGlyphTransform:
    """A safe transform for one copied Korean/CJK glyph."""

    scale: float
    shift_x: float
    left_side_bearing: int
    capped: bool
    transformed_bounds: Bounds | None
    scale_y: float


@dataclass(frozen=True)
class MergeStats:
    """Summary of a font merge."""

    copied_count: int
    capped_count: int
    latin_advance: int
    korean_advance: int
    requested_total_scale: float


@dataclass(frozen=True)
class FontVariant:
    """One buildable Covendard output variant."""

    weight_name: str
    css_weight: int
    style: str
    latin_filename: str
    cjk_weight_name: str
    output_suffix: str
    subfamily_name: str
    typographic_subfamily_name: str
    is_italic: bool


WEIGHT_TO_CSS = {
    "Thin": 100,
    "ExtraLight": 200,
    "Light": 300,
    "Regular": 400,
    "Medium": 500,
    "SemiBold": 600,
    "Bold": 700,
    "ExtraBold": 800,
}
SUPPORTED_WEIGHTS = tuple(WEIGHT_TO_CSS)
DEFAULT_WEIGHTS = SUPPORTED_WEIGHTS
SUPPORTED_STYLES = ("normal", "italic")


@dataclass(frozen=True)
class LatinSource:
    """A supported Nerd Fonts source and its matching Pretendard weights."""

    prefix: str
    archive_name: str
    weights: tuple[str, ...]
    family_name: str


LATIN_SOURCES = {
    "jetbrainsmono": LatinSource(
        "JetBrainsMonoNerdFontMono", "JetBrainsMono", SUPPORTED_WEIGHTS, "Covendard JB"
    ),
    "caskaydiacove": LatinSource(
        "CaskaydiaCoveNerdFontMono",
        "CascadiaCode",
        ("ExtraLight", "Light", "Regular", "SemiBold", "Bold"),
        "Covendard",
    ),
}


def get_source_variants(latin_family: str) -> list[FontVariant]:
    """Return variants with same-weight Pretendard sources for a Latin family."""
    source = LATIN_SOURCES[latin_family]
    return [
        make_font_variant(weight, style, latin_family=latin_family)
        for weight in source.weights
        for style in SUPPORTED_STYLES
    ]


def new_ot_table(class_name: str) -> Any:
    """Create a fontTools OpenType table class generated at import time."""
    table_class = getattr(cast("Any", otTables), class_name)
    return table_class()


def make_font_variant(
    weight_name: str, style: str, *, latin_family: str = "caskaydiacove"
) -> FontVariant:
    """Create a build variant for a supported weight/style pair."""
    source = LATIN_SOURCES[latin_family]
    if weight_name not in source.weights:
        supported = ", ".join(source.weights)
        msg = f"Unsupported weight {weight_name!r}. Supported: {supported}"
        raise ValueError(msg)
    if style not in SUPPORTED_STYLES:
        supported = ", ".join(SUPPORTED_STYLES)
        msg = f"Unsupported style {style!r}. Supported: {supported}"
        raise ValueError(msg)

    is_italic = style == "italic"
    if is_italic:
        latin_suffix = "Italic" if weight_name == "Regular" else f"{weight_name}Italic"
        output_suffix = latin_suffix
        subfamily_name = "Italic" if weight_name == "Regular" else f"{weight_name} Italic"
    else:
        latin_suffix = weight_name
        output_suffix = weight_name
        subfamily_name = weight_name

    return FontVariant(
        weight_name=weight_name,
        css_weight=WEIGHT_TO_CSS[weight_name],
        style=style,
        latin_filename=f"{source.prefix}-{latin_suffix}.ttf",
        cjk_weight_name=weight_name,
        output_suffix=output_suffix,
        subfamily_name=subfamily_name,
        typographic_subfamily_name=subfamily_name,
        is_italic=is_italic,
    )


DEFAULT_VARIANTS = tuple(
    make_font_variant(weight_name, style)
    for weight_name in LATIN_SOURCES["caskaydiacove"].weights
    for style in SUPPORTED_STYLES
)
VARIANTS_BY_SUFFIX = {variant.output_suffix: variant for variant in DEFAULT_VARIANTS}


def get_variants_by_names(variant_names: list[str] | tuple[str, ...]) -> list[FontVariant]:
    """Resolve output suffix names to variants, preserving request order."""
    variants: list[FontVariant] = []
    seen: set[str] = set()
    unsupported: list[str] = []

    for name in variant_names:
        variant = VARIANTS_BY_SUFFIX.get(name)
        if variant is None:
            unsupported.append(name)
            continue
        if variant.output_suffix in seen:
            continue
        variants.append(variant)
        seen.add(variant.output_suffix)

    if unsupported:
        supported = ", ".join(VARIANTS_BY_SUFFIX)
        msg = f"Unsupported variant(s): {', '.join(unsupported)}. Supported: {supported}"
        raise ValueError(msg)

    return variants


def get_variants_by_weights_and_styles(
    weights: list[str] | tuple[str, ...],
    styles: list[str] | tuple[str, ...],
) -> list[FontVariant]:
    """Resolve weight/style selectors to variants."""
    return [make_font_variant(weight, style) for weight in weights for style in styles]


def is_cjk(code: int) -> bool:
    """Return whether a Unicode codepoint belongs to supported Korean/CJK ranges."""
    return (
        0xAC00 <= code <= 0xD7A3
        or 0x1100 <= code <= 0x11FF
        or 0x3130 <= code <= 0x318F
        or 0xA960 <= code <= 0xA97F
        or 0xD7B0 <= code <= 0xD7FF
        or 0x4E00 <= code <= 0x9FFF
        or 0x3000 <= code <= 0x303F
        or 0xFF00 <= code <= 0xFFEF
    )


def collect_cjk_codepoints(cmap: dict[int, str]) -> list[int]:
    """Collect CJK codepoints and required Hangul Jamo codepoints."""
    codepoints = {code for code in cmap if is_cjk(code)}
    codepoints.update(JAMO_COMPATIBILITY_MAP)
    return sorted(codepoints)


def calculate_korean_target_width(latin_advance: int) -> int:
    """Calculate the exact two-cell Korean/CJK advance width."""
    if latin_advance <= 0:
        msg = f"Latin advance must be positive, got {latin_advance}"
        raise ValueError(msg)
    return latin_advance * 2


def derive_latin_advance(
    font: TTFont,
    sample_codepoints: tuple[int, ...] = ASCII_WIDTH_SAMPLE,
) -> int:
    """Derive the Latin monospace advance from representative ASCII glyphs."""
    cmap = font.getBestCmap()
    if not cmap:
        msg = "Base font has no usable cmap table"
        raise ValueError(msg)
    hmtx = font["hmtx"]

    widths: dict[str, int] = {}
    for codepoint in sample_codepoints:
        glyph_name = cmap.get(codepoint)
        if glyph_name is None or glyph_name not in hmtx.metrics:
            continue
        widths[chr(codepoint)] = hmtx.metrics[glyph_name][0]

    if not widths:
        msg = "Could not derive a Latin advance from the base font"
        raise ValueError(msg)

    unique_widths = set(widths.values())
    if len(unique_widths) != 1:
        details = ", ".join(f"{char}={width}" for char, width in sorted(widths.items()))
        msg = f"Base font is not monospaced across the ASCII sample: {details}"
        raise ValueError(msg)

    return unique_widths.pop()


def default_side_bearing_guard(latin_advance: int) -> int:
    """Return a modest guard that keeps fitted glyphs off cell edges."""
    return max(8, round(latin_advance * 0.02))


def get_vertical_safe_bounds(font: TTFont) -> tuple[int, int]:
    """Return conservative vertical bounds from the base font metrics."""
    hhea = cast("Any", font["hhea"])
    os2 = cast("Any", font["OS/2"])
    safe_ymax = min(int(hhea.ascent), int(os2.sTypoAscender))
    safe_ymin = max(int(hhea.descent), int(os2.sTypoDescender))
    if safe_ymin >= safe_ymax:
        safe_ymin = int(hhea.descent)
        safe_ymax = int(hhea.ascent)
    return safe_ymin, safe_ymax


def get_glyph_bounds(glyph_set: Any, glyph_name: str) -> Bounds | None:
    """Measure glyph bounds with fontTools pens."""
    bounds_pen = BoundsPen(glyph_set)
    glyph_set[glyph_name].draw(bounds_pen)
    return bounds_pen.bounds


def calculate_fitted_transform(
    bounds: Bounds | None,
    *,
    target_width: int,
    requested_scale: float,
    safe_ymin: int,
    safe_ymax: int,
    side_bearing_guard: int,
    vertical_guard: int = 0,
    requested_scale_y: float | None = None,
) -> FittedGlyphTransform:
    """Fit uniformly unless an independent vertical scale is supplied."""
    independent_axes = requested_scale_y is not None
    requested_y = requested_scale if requested_scale_y is None else requested_scale_y
    if any(not math.isfinite(value) or value <= 0 for value in (requested_scale, requested_y)):
        msg = f"Scales must be finite and positive, got {requested_scale}, {requested_y}"
        raise ValueError(msg)
    if bounds is None:
        return FittedGlyphTransform(
            scale=requested_scale,
            shift_x=0,
            left_side_bearing=0,
            capped=False,
            transformed_bounds=None,
            scale_y=requested_y,
        )

    xmin, ymin, xmax, ymax = bounds
    scale = requested_scale

    source_width = xmax - xmin
    horizontal_limit = target_width - (side_bearing_guard * 2)
    if source_width > 0 and horizontal_limit > 0:
        scale = min(scale, horizontal_limit / source_width)

    scale_y = requested_y
    if ymax > 0:
        scale_y = min(scale_y, (safe_ymax - vertical_guard) / ymax)
    if ymin < 0 and safe_ymin + vertical_guard < 0:
        scale_y = min(scale_y, (safe_ymin + vertical_guard) / ymin)

    if not independent_axes:
        scale = scale_y = min(scale, scale_y)

    if scale <= 0 or scale_y <= 0:
        msg = f"Could not fit glyph bounds {bounds} into target width {target_width}"
        raise ValueError(msg)

    scaled_xmin = xmin * scale
    scaled_xmax = xmax * scale
    current_center = (scaled_xmin + scaled_xmax) / 2
    shift_x = (target_width / 2) - current_center
    transformed_bounds = (
        scaled_xmin + shift_x,
        ymin * scale_y,
        scaled_xmax + shift_x,
        ymax * scale_y,
    )
    capped = scale < requested_scale - 0.000001 or scale_y < requested_y - 0.000001

    return FittedGlyphTransform(
        scale=scale,
        shift_x=shift_x,
        left_side_bearing=round(transformed_bounds[0]),
        capped=capped,
        transformed_bounds=transformed_bounds,
        scale_y=scale_y,
    )


def update_font_names(
    font: TTFont,
    family_name: str,
    subfamily_name: str,
    typographic_subfamily_name: str | None = None,
) -> None:
    """Update family, subfamily, full, PostScript, and typographic names."""
    logger.info("Updating font names to %s %s", family_name, subfamily_name)
    name_table = font["name"]

    typographic_subfamily = typographic_subfamily_name or subfamily_name
    ps_family = "".join(family_name.split())
    ps_subfamily = "".join(typographic_subfamily.split())
    ps_name = f"{ps_family}-{ps_subfamily}"
    full_name = f"{family_name} {typographic_subfamily}"
    head_table = cast("Any", font["head"])
    unique_id = f"{ps_name};{head_table.fontRevision:.3f}"

    values = {
        1: family_name,
        2: subfamily_name,
        3: unique_id,
        4: full_name,
        6: ps_name,
        16: family_name,
        17: typographic_subfamily,
    }

    for name_id, value in values.items():
        name_table.setName(value, name_id, 3, 1, 0x409)
        name_table.setName(value, name_id, 1, 0, 0)

    for record in name_table.names:
        value = values.get(record.nameID)
        if value is None:
            continue
        try:
            record.string = value.encode(record.getEncoding())
        except Exception as exc:
            logger.warning("Failed to update name record %d: %s", record.nameID, exc)


def update_style_metadata(
    font: TTFont,
    *,
    is_italic: bool,
    css_weight: int | None = None,
    is_regular: bool = False,
) -> None:
    """Set style bits and weight metadata that identify upright and italic variants."""
    head_table = cast("Any", font["head"])
    os2_table = cast("Any", font["OS/2"])

    mac_bold = 1 << 0
    mac_italic = 1 << 1
    fs_italic = 1 << 0
    fs_bold = 1 << 5
    fs_regular = 1 << 6

    if is_italic:
        head_table.macStyle |= mac_italic
        os2_table.fsSelection |= fs_italic
    else:
        head_table.macStyle &= ~mac_italic
        os2_table.fsSelection &= ~fs_italic

    if css_weight is not None:
        os2_table.usWeightClass = css_weight
        if css_weight >= 700:
            head_table.macStyle |= mac_bold
            os2_table.fsSelection |= fs_bold
        else:
            head_table.macStyle &= ~mac_bold
            os2_table.fsSelection &= ~fs_bold

    if is_regular and not is_italic:
        os2_table.fsSelection |= fs_regular
    else:
        os2_table.fsSelection &= ~fs_regular


def enforce_monospace_flags(font: TTFont) -> None:
    """Set common fixed-pitch indicators."""
    post_table = cast("Any", font["post"])
    post_table.isFixedPitch = 1
    os2_table = cast("Any", font["OS/2"])
    os2_table.panose.bProportion = 9


def merge_os2_ranges(target_font: TTFont, source_font: TTFont) -> None:
    """OR CJK Unicode/codepage range bits into the base font."""
    target_os2 = target_font["OS/2"]
    source_os2 = source_font["OS/2"]
    for field in (
        "ulUnicodeRange1",
        "ulUnicodeRange2",
        "ulUnicodeRange3",
        "ulUnicodeRange4",
        "ulCodePageRange1",
        "ulCodePageRange2",
    ):
        target_value = int(getattr(target_os2, field, 0))
        source_value = int(getattr(source_os2, field, 0))
        setattr(target_os2, field, target_value | source_value)


def update_unicode_cmaps(font: TTFont, codepoint: int, glyph_name: str) -> None:
    """Add a cmap entry to Unicode subtables that can carry normal mappings."""
    for table in font["cmap"].tables:
        if table.format == 14 or not table.isUnicode():
            continue
        table.cmap[codepoint] = glyph_name


def sync_glyph_order(font: TTFont, glyf_table: Any, preferred_order: list[str]) -> list[str]:
    """Synchronize TTFont and glyf glyph order with duplicate names removed."""
    seen: set[str] = set()
    normalized_order: list[str] = []
    for glyph_name in preferred_order:
        if glyph_name in seen or glyph_name not in glyf_table.glyphs:
            continue
        normalized_order.append(glyph_name)
        seen.add(glyph_name)

    for glyph_name in glyf_table.glyphs:
        if glyph_name in seen:
            continue
        normalized_order.append(glyph_name)
        seen.add(glyph_name)

    font.setGlyphOrder(normalized_order)
    glyf_table.glyphOrder = normalized_order
    return normalized_order


def source_glyph_for_codepoint(
    codepoint: int,
    cjk_cmap: dict[int, str],
) -> str | None:
    """Find the Pretendard glyph name for a target CJK/Jamo codepoint."""
    source_codepoint = JAMO_COMPATIBILITY_MAP.get(codepoint, codepoint)
    return cjk_cmap.get(source_codepoint)


def build_hangul_ccmp_features() -> str:
    """Build GSUB ccmp feature text for decomposed Hangul Jamo composition."""
    fea_lines = [
        "languagesystem DFLT dflt;",
        "languagesystem latn dflt;",
        "languagesystem hang dflt;",
        "",
        "feature ccmp {",
    ]

    choseong_list = sorted(CHOSEONG_MAP)
    jungseong_list = sorted(JUNGSEONG_MAP)
    jongseong_list = sorted(JONGSEONG_MAP)

    for c_idx, c_code in enumerate(choseong_list):
        for v_idx, v_code in enumerate(jungseong_list):
            for t_idx, t_code in enumerate(jongseong_list):
                syllable_code = 0xAC00 + (c_idx * 21 * 28) + (v_idx * 28) + (t_idx + 1)
                fea_lines.append(
                    f"    sub uni{c_code:04X} uni{v_code:04X} "
                    f"uni{t_code:04X} by uni{syllable_code:04X};"
                )

    for c_idx, c_code in enumerate(choseong_list):
        for v_idx, v_code in enumerate(jungseong_list):
            syllable_code = 0xAC00 + (c_idx * 21 * 28) + (v_idx * 28)
            fea_lines.append(f"    sub uni{c_code:04X} uni{v_code:04X} by uni{syllable_code:04X};")

    fea_lines.append("} ccmp;")
    return "\n".join(fea_lines)


def build_hangul_ccmp_mapping() -> dict[tuple[str, ...], str]:
    """Build glyph-name mappings for decomposed Hangul Jamo composition."""
    mapping: dict[tuple[str, ...], str] = {}
    choseong_list = sorted(CHOSEONG_MAP)
    jungseong_list = sorted(JUNGSEONG_MAP)
    jongseong_list = sorted(JONGSEONG_MAP)

    for c_idx, c_code in enumerate(choseong_list):
        for v_idx, v_code in enumerate(jungseong_list):
            for t_idx, t_code in enumerate(jongseong_list):
                syllable_code = 0xAC00 + (c_idx * 21 * 28) + (v_idx * 28) + (t_idx + 1)
                mapping[(f"uni{c_code:04X}", f"uni{v_code:04X}", f"uni{t_code:04X}")] = (
                    f"uni{syllable_code:04X}"
                )

    for c_idx, c_code in enumerate(choseong_list):
        for v_idx, v_code in enumerate(jungseong_list):
            syllable_code = 0xAC00 + (c_idx * 21 * 28) + (v_idx * 28)
            mapping[(f"uni{c_code:04X}", f"uni{v_code:04X}")] = f"uni{syllable_code:04X}"

    return mapping


def add_hangul_ccmp_features(font: TTFont) -> None:
    """Compile Hangul ccmp substitutions into the merged font."""
    logger.info("Adding GSUB ccmp lookups for Hangul Jamo support")
    if "GSUB" not in font:
        addOpenTypeFeaturesFromString(font, build_hangul_ccmp_features(), tables=["GSUB"])
        return

    gsub = font["GSUB"].table
    if getattr(gsub, "LookupList", None) is None or getattr(gsub, "FeatureList", None) is None:
        addOpenTypeFeaturesFromString(font, build_hangul_ccmp_features(), tables=["GSUB"])
        return

    subtable = buildLigatureSubstSubtable(build_hangul_ccmp_mapping())
    lookup = buildLookup([subtable], table="GSUB")
    if lookup is None:
        return

    lookup_index = gsub.LookupList.LookupCount
    gsub.LookupList.Lookup.append(lookup)
    gsub.LookupList.LookupCount = len(gsub.LookupList.Lookup)

    ccmp_records = [
        record for record in gsub.FeatureList.FeatureRecord if record.FeatureTag == "ccmp"
    ]
    if not ccmp_records:
        feature = new_ot_table("Feature")
        feature.FeatureParams = None
        feature.LookupListIndex = []
        feature.LookupCount = 0

        record = new_ot_table("FeatureRecord")
        record.FeatureTag = "ccmp"
        record.Feature = feature
        gsub.FeatureList.FeatureRecord.append(record)
        gsub.FeatureList.FeatureRecord.sort(key=lambda item: item.FeatureTag)
        gsub.FeatureList.FeatureCount = len(gsub.FeatureList.FeatureRecord)
        ccmp_records = [record]

    for record in ccmp_records:
        record.Feature.LookupListIndex.append(lookup_index)
        record.Feature.LookupCount = len(record.Feature.LookupListIndex)

    logger.info("Appended Hangul ccmp lookup at GSUB lookup index %d", lookup_index)


def merge_fonts(
    latin_path: str | Path,
    cjk_path: str | Path,
    output_path: str | Path,
    family_name: str,
    subfamily_name: str,
    korean_scale: float = DEFAULT_KOREAN_SCALE,
    *,
    korean_scale_x: float | None = None,
    korean_scale_y: float | None = None,
    typographic_subfamily_name: str | None = None,
    is_italic: bool = False,
    css_weight: int | None = None,
) -> MergeStats:
    """Merge JetBrainsMono Nerd Font Mono with Pretendard CJK glyphs."""
    logger.info("Merging %s + %s -> %s", latin_path, cjk_path, output_path)
    latin_font = TTFont(str(latin_path))
    cjk_font = TTFont(str(cjk_path))

    latin_head = cast("Any", latin_font["head"])
    cjk_head = cast("Any", cjk_font["head"])
    upm_scale = latin_head.unitsPerEm / cjk_head.unitsPerEm
    independent_axes = korean_scale_x is not None or korean_scale_y is not None
    requested_total_scale = upm_scale * (korean_scale if korean_scale_x is None else korean_scale_x)
    requested_total_scale_y = upm_scale * (
        korean_scale if korean_scale_y is None else korean_scale_y
    )

    latin_advance = derive_latin_advance(latin_font)
    korean_advance = calculate_korean_target_width(latin_advance)
    side_guard = default_side_bearing_guard(latin_advance)
    safe_ymin, safe_ymax = get_vertical_safe_bounds(latin_font)

    logger.info(
        "Metrics: latin UPM=%d, cjk UPM=%d, latin advance=%d, korean advance=%d",
        latin_head.unitsPerEm,
        cjk_head.unitsPerEm,
        latin_advance,
        korean_advance,
    )
    logger.info(
        "Korean fitting: total_scale_x=%.6f, total_scale_y=%.6f, independent_axes=%s, "
        "side_guard=%d, y_bounds=(%d,%d)",
        requested_total_scale,
        requested_total_scale_y,
        independent_axes,
        side_guard,
        safe_ymin,
        safe_ymax,
    )

    cjk_cmap = cjk_font.getBestCmap()
    if not cjk_cmap:
        msg = "Pretendard font has no usable cmap table"
        raise ValueError(msg)

    cjk_glyph_set = cjk_font.getGlyphSet()
    glyf_table = latin_font["glyf"]
    hmtx_table = latin_font["hmtx"]
    glyph_order = latin_font.getGlyphOrder()
    glyph_order_set = set(glyph_order)
    codepoints = collect_cjk_codepoints(cjk_cmap)

    copied_count = 0
    capped_codepoints: list[int] = []

    for codepoint in codepoints:
        cjk_glyph_name = source_glyph_for_codepoint(codepoint, cjk_cmap)
        if cjk_glyph_name is None or cjk_glyph_name not in cjk_glyph_set:
            continue

        target_glyph_name = f"uni{codepoint:04X}"
        bounds = get_glyph_bounds(cjk_glyph_set, cjk_glyph_name)
        fitted = calculate_fitted_transform(
            bounds,
            target_width=korean_advance,
            requested_scale=requested_total_scale,
            requested_scale_y=requested_total_scale_y if independent_axes else None,
            safe_ymin=safe_ymin,
            safe_ymax=safe_ymax,
            side_bearing_guard=side_guard,
        )

        if fitted.capped:
            capped_codepoints.append(codepoint)

        decomposed_pen = DecomposingRecordingPen(cjk_glyph_set)
        cjk_glyph_set[cjk_glyph_name].draw(decomposed_pen)

        glyph_pen = TTGlyphPen(None)
        transform_pen = TransformPen(
            glyph_pen,
            (fitted.scale, 0, 0, fitted.scale_y, fitted.shift_x, 0),
        )
        decomposed_pen.replay(transform_pen)

        glyf_table[target_glyph_name] = glyph_pen.glyph()
        hmtx_table.metrics[target_glyph_name] = (
            korean_advance,
            fitted.left_side_bearing,
        )
        update_unicode_cmaps(latin_font, codepoint, target_glyph_name)

        if target_glyph_name not in glyph_order_set:
            glyph_order.append(target_glyph_name)
            glyph_order_set.add(target_glyph_name)
        copied_count += 1

    glyph_order = sync_glyph_order(latin_font, glyf_table, glyph_order)
    merge_os2_ranges(latin_font, cjk_font)
    enforce_monospace_flags(latin_font)
    add_hangul_ccmp_features(latin_font)
    glyph_order = sync_glyph_order(latin_font, glyf_table, glyph_order)
    update_style_metadata(
        latin_font,
        is_italic=is_italic,
        css_weight=css_weight,
        is_regular=subfamily_name == "Regular",
    )
    update_font_names(
        latin_font,
        family_name,
        subfamily_name,
        typographic_subfamily_name=typographic_subfamily_name,
    )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    glyph_names = set(glyph_order)
    glyf_names = set(glyf_table.glyphs)
    if len(glyph_order) != len(glyf_table.glyphs):
        logger.warning(
            "Glyph bookkeeping mismatch: order=%d unique_order=%d glyf=%d "
            "missing_glyf=%d extra_glyf=%d",
            len(glyph_order),
            len(glyph_names),
            len(glyf_table.glyphs),
            len(glyph_names - glyf_names),
            len(glyf_names - glyph_names),
        )
    latin_font.save(str(output))

    if capped_codepoints:
        preview = ", ".join(f"U+{code:04X}" for code in capped_codepoints[:12])
        if len(capped_codepoints) > 12:
            preview += ", ..."
        logger.info("Capped %d glyphs to avoid clipping: %s", len(capped_codepoints), preview)
    logger.info("Copied %d CJK glyphs into %s", copied_count, output)

    latin_font.close()
    cjk_font.close()

    return MergeStats(
        copied_count=copied_count,
        capped_count=len(capped_codepoints),
        latin_advance=latin_advance,
        korean_advance=korean_advance,
        requested_total_scale=requested_total_scale,
    )
