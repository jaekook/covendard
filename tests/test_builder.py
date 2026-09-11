"""Unit tests for Covendard builder logic."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from fontTools.ttLib import TTFont, newTable
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

from covendard.builder import (
    DEFAULT_VARIANTS,
    calculate_fitted_transform,
    calculate_korean_target_width,
    collect_cjk_codepoints,
    derive_latin_advance,
    enforce_monospace_flags,
    get_variants_by_names,
    is_cjk,
    make_font_variant,
    merge_fonts,
    update_font_names,
    update_style_metadata,
)


class DummyPanose:
    """Minimal Panose object for fixed-pitch flag tests."""

    bProportion = 0


def make_width_font(widths: dict[str, int]) -> TTFont:
    """Create a minimal font with cmap and hmtx tables for metric tests."""
    font = TTFont()
    cmap = newTable("cmap")
    cmap.tableVersion = 0
    subtable = CmapSubtable.newSubtable(4)
    subtable.platformID = 3
    subtable.platEncID = 1
    subtable.language = 0
    subtable.cmap = {ord(char): char for char in widths}
    cmap.tables = [subtable]
    font["cmap"] = cmap

    hmtx = newTable("hmtx")
    hmtx.metrics = {char: (width, 0) for char, width in widths.items()}
    font["hmtx"] = hmtx
    return font


def make_name_font() -> TTFont:
    """Create a minimal font with name and head tables."""
    font = TTFont()
    name = newTable("name")
    name.names = []
    font["name"] = name
    head = newTable("head")
    head.fontRevision = 1.0
    font["head"] = head
    return font


def make_style_font() -> TTFont:
    """Create a minimal font with head and OS/2 tables."""
    font = TTFont()
    head = newTable("head")
    head.macStyle = 0
    font["head"] = head
    os2 = newTable("OS/2")
    os2.fsSelection = 1 << 6
    os2.usWeightClass = 400
    font["OS/2"] = os2
    return font


def test_default_variants_cover_full_matrix() -> None:
    suffixes = [variant.output_suffix for variant in DEFAULT_VARIANTS]

    assert len(DEFAULT_VARIANTS) == 10
    assert suffixes == [
        "ExtraLight",
        "ExtraLightItalic",
        "Light",
        "LightItalic",
        "Regular",
        "Italic",
        "SemiBold",
        "SemiBoldItalic",
        "Bold",
        "BoldItalic",
    ]


def test_regular_italic_variant_uses_special_source_filename() -> None:
    variant = make_font_variant("Regular", "italic")

    assert variant.output_suffix == "Italic"
    assert variant.subfamily_name == "Italic"
    assert variant.latin_filename == "CaskaydiaCoveNerdFontMono-Italic.ttf"
    assert variant.cjk_weight_name == "Regular"
    assert variant.css_weight == 400
    assert variant.is_italic is True


def test_get_variants_by_names_rejects_unknown_variant() -> None:
    with pytest.raises(ValueError, match="Unsupported variant"):
        get_variants_by_names(["Regular", "BookItalic"])


def test_is_cjk_supported_ranges() -> None:
    assert is_cjk(0xAC00) is True
    assert is_cjk(0xD7A3) is True
    assert is_cjk(0x1100) is True
    assert is_cjk(0x3131) is True
    assert is_cjk(0xA960) is True
    assert is_cjk(0xD7FF) is True
    assert is_cjk(0x4E00) is True
    assert is_cjk(0x3001) is True
    assert is_cjk(0xFF01) is True
    assert is_cjk(ord("A")) is False


def test_collect_cjk_codepoints_adds_required_jamo() -> None:
    codepoints = collect_cjk_codepoints({0xAC00: "uniAC00", ord("A"): "A"})
    assert 0xAC00 in codepoints
    assert 0x1100 in codepoints
    assert 0x1161 in codepoints
    assert 0x11A8 in codepoints
    assert ord("A") not in codepoints


def test_derive_latin_advance_from_monospaced_sample() -> None:
    font = make_width_font({char: 600 for char in " A0Hinmw"})
    assert derive_latin_advance(font) == 600


def test_derive_latin_advance_rejects_non_monospaced_sample() -> None:
    font = make_width_font({char: 600 for char in " A0Hinmw"})
    font["hmtx"].metrics["m"] = (700, 0)
    with pytest.raises(ValueError, match="not monospaced"):
        derive_latin_advance(font)


def test_calculate_korean_target_width() -> None:
    assert calculate_korean_target_width(600) == 1200


def test_calculate_korean_target_width_rejects_invalid_advance() -> None:
    with pytest.raises(ValueError, match="positive"):
        calculate_korean_target_width(0)


def test_fitted_transform_centers_uncapped_glyph() -> None:
    fitted = calculate_fitted_transform(
        (100, -100, 900, 700),
        target_width=1200,
        requested_scale=1.0,
        safe_ymin=-300,
        safe_ymax=900,
        side_bearing_guard=20,
    )

    assert fitted.capped is False
    assert fitted.transformed_bounds == pytest.approx((200, -100, 1000, 700))
    assert fitted.left_side_bearing == 200


def test_fitted_transform_caps_unsafe_scale() -> None:
    fitted = calculate_fitted_transform(
        (0, -100, 1000, 800),
        target_width=1200,
        requested_scale=1.3,
        safe_ymin=-300,
        safe_ymax=900,
        side_bearing_guard=20,
    )

    assert fitted.capped is True
    assert fitted.scale == pytest.approx(1.125)
    assert fitted.transformed_bounds is not None
    assert fitted.transformed_bounds[0] >= 20
    assert fitted.transformed_bounds[2] <= 1180
    assert fitted.transformed_bounds[3] <= 900


def test_update_font_names_sets_required_records() -> None:
    font = make_name_font()
    update_font_names(font, "Covendard", "Regular")

    name_table = font["name"]
    assert name_table.getName(1, 3, 1, 0x409).toUnicode() == "Covendard"
    assert name_table.getName(2, 3, 1, 0x409).toUnicode() == "Regular"
    assert name_table.getName(4, 3, 1, 0x409).toUnicode() == "Covendard Regular"
    assert name_table.getName(6, 3, 1, 0x409).toUnicode() == "Covendard-Regular"
    assert name_table.getName(16, 3, 1, 0x409).toUnicode() == "Covendard"
    assert name_table.getName(17, 3, 1, 0x409).toUnicode() == "Regular"


def test_independent_vertical_cap_preserves_horizontal_enlargement() -> None:
    fitted = calculate_fitted_transform(
        (84, -162, 1736, 1616),
        target_width=2400,
        requested_scale=1.20,
        requested_scale_y=1.25,
        safe_ymin=-480,
        safe_ymax=1900,
        side_bearing_guard=24,
    )
    assert fitted.scale == pytest.approx(1.20)
    assert fitted.scale_y == pytest.approx(1900 / 1616)
    assert fitted.capped
    assert fitted.transformed_bounds[3] == pytest.approx(1900)
    assert fitted.transformed_bounds[2] - fitted.transformed_bounds[0] == pytest.approx(1652 * 1.20)


def test_independent_horizontal_cap_preserves_vertical_scale() -> None:
    fitted = calculate_fitted_transform(
        (0, -100, 1000, 800),
        target_width=1200,
        requested_scale=1.30,
        requested_scale_y=1.10,
        safe_ymin=-300,
        safe_ymax=1000,
        side_bearing_guard=20,
    )
    assert fitted.scale == pytest.approx(1.16)
    assert fitted.scale_y == pytest.approx(1.10)
    assert fitted.capped


@pytest.mark.parametrize("scale", [0, -1, float("nan"), float("inf")])
def test_independent_scale_rejects_invalid_values_even_for_empty_glyphs(scale) -> None:
    with pytest.raises(ValueError, match="finite and positive"):
        calculate_fitted_transform(
            None,
            target_width=2400,
            requested_scale=1.2,
            requested_scale_y=scale,
            safe_ymin=-480,
            safe_ymax=1900,
            side_bearing_guard=24,
        )


def test_update_font_names_supports_italic_postscript_names() -> None:
    font = make_name_font()
    update_font_names(font, "Covendard", "Bold Italic")

    name_table = font["name"]
    assert name_table.getName(2, 3, 1, 0x409).toUnicode() == "Bold Italic"
    assert name_table.getName(4, 3, 1, 0x409).toUnicode() == "Covendard Bold Italic"
    assert name_table.getName(6, 3, 1, 0x409).toUnicode() == "Covendard-BoldItalic"
    assert name_table.getName(17, 3, 1, 0x409).toUnicode() == "Bold Italic"


def test_update_style_metadata_sets_italic_and_bold_bits() -> None:
    font = make_style_font()
    update_style_metadata(font, is_italic=True, css_weight=700)

    assert font["head"].macStyle & (1 << 0)
    assert font["head"].macStyle & (1 << 1)
    assert font["OS/2"].fsSelection & (1 << 0)
    assert font["OS/2"].fsSelection & (1 << 5)
    assert not font["OS/2"].fsSelection & (1 << 6)
    assert font["OS/2"].usWeightClass == 700


def test_update_style_metadata_sets_regular_upright_bits() -> None:
    font = make_style_font()
    update_style_metadata(font, is_italic=False, css_weight=400, is_regular=True)

    assert not font["head"].macStyle & (1 << 0)
    assert not font["head"].macStyle & (1 << 1)
    assert not font["OS/2"].fsSelection & (1 << 0)
    assert not font["OS/2"].fsSelection & (1 << 5)
    assert font["OS/2"].fsSelection & (1 << 6)
    assert font["OS/2"].usWeightClass == 400


def test_enforce_monospace_flags() -> None:
    font = TTFont()
    post = newTable("post")
    post.isFixedPitch = 0
    font["post"] = post
    os2 = newTable("OS/2")
    os2.panose = DummyPanose()
    font["OS/2"] = os2

    enforce_monospace_flags(font)

    assert font["post"].isFixedPitch == 1
    assert font["OS/2"].panose.bProportion == 9


def test_integration_merge_skips_without_upstream_fonts(tmp_path: Path) -> None:
    latin_path = Path("upstream/caskaydiacove/CaskaydiaCoveNerdFontMono-Regular.ttf")
    cjk_path = Path("upstream/pretendard/Pretendard-Regular.ttf")
    if not latin_path.exists() or not cjk_path.exists():
        pytest.skip("upstream fonts have not been downloaded")

    output_path = tmp_path / "Covendard-Regular.ttf"
    stats = merge_fonts(
        latin_path=latin_path,
        cjk_path=cjk_path,
        output_path=output_path,
        family_name="Covendard",
        subfamily_name="Regular",
    )

    font = TTFont(str(output_path))
    cmap = font.getBestCmap()
    features = [record.FeatureTag for record in font["GSUB"].table.FeatureList.FeatureRecord]
    assert stats.copied_count > 10_000
    assert font["hmtx"].metrics[cmap[ord("가")]][0] == font["hmtx"].metrics[cmap[ord("A")]][0] * 2
    assert font["name"].getName(1, 3, 1, 0x409).toUnicode() == "Covendard"
    assert font["post"].isFixedPitch == 1
    assert "calt" in features
    assert "ccmp" in features
    font.close()


def test_integration_merge_italic_metadata_skips_without_upstream_fonts(tmp_path: Path) -> None:
    variant = make_font_variant("Regular", "italic")
    latin_path = Path("upstream/caskaydiacove") / variant.latin_filename
    cjk_path = Path("upstream/pretendard/Pretendard-Regular.ttf")
    if not latin_path.exists() or not cjk_path.exists():
        pytest.skip("upstream italic fonts have not been downloaded")

    output_path = tmp_path / "Covendard-Italic.ttf"
    stats = merge_fonts(
        latin_path=latin_path,
        cjk_path=cjk_path,
        output_path=output_path,
        family_name="Covendard",
        subfamily_name=variant.subfamily_name,
        typographic_subfamily_name=variant.typographic_subfamily_name,
        is_italic=variant.is_italic,
        css_weight=variant.css_weight,
    )

    font = TTFont(str(output_path))
    cmap = font.getBestCmap()
    features = [record.FeatureTag for record in font["GSUB"].table.FeatureList.FeatureRecord]
    assert stats.copied_count > 10_000
    assert font["hmtx"].metrics[cmap[ord("가")]][0] == font["hmtx"].metrics[cmap[ord("A")]][0] * 2
    assert font["name"].getName(2, 3, 1, 0x409).toUnicode() == "Italic"
    assert font["name"].getName(6, 3, 1, 0x409).toUnicode() == "Covendard-Italic"
    assert font["head"].macStyle & (1 << 1)
    assert font["OS/2"].fsSelection & (1 << 0)
    assert "calt" in features
    assert "ccmp" in features
    font.close()


def test_full_matrix_integration_when_enabled(tmp_path: Path) -> None:
    if os.environ.get("COVENDARD_RUN_FULL_INTEGRATION") != "1":
        pytest.skip("set COVENDARD_RUN_FULL_INTEGRATION=1 to build the full variant matrix")

    missing_sources: list[Path] = []
    for variant in DEFAULT_VARIANTS:
        latin_path = Path("upstream/caskaydiacove") / variant.latin_filename
        cjk_path = Path("upstream/pretendard") / f"Pretendard-{variant.cjk_weight_name}.ttf"
        if not latin_path.exists():
            missing_sources.append(latin_path)
        if not cjk_path.exists():
            missing_sources.append(cjk_path)
    if missing_sources:
        preview = ", ".join(str(path) for path in missing_sources[:4])
        pytest.skip(f"upstream fonts missing: {preview}")

    for variant in DEFAULT_VARIANTS:
        latin_path = Path("upstream/caskaydiacove") / variant.latin_filename
        cjk_path = Path("upstream/pretendard") / f"Pretendard-{variant.cjk_weight_name}.ttf"
        output_path = tmp_path / f"Covendard-{variant.output_suffix}.ttf"
        merge_fonts(
            latin_path=latin_path,
            cjk_path=cjk_path,
            output_path=output_path,
            family_name="Covendard",
            subfamily_name=variant.subfamily_name,
            typographic_subfamily_name=variant.typographic_subfamily_name,
            is_italic=variant.is_italic,
            css_weight=variant.css_weight,
        )

        font = TTFont(str(output_path))
        cmap = font.getBestCmap()
        features = [record.FeatureTag for record in font["GSUB"].table.FeatureList.FeatureRecord]
        assert font["hmtx"].metrics[cmap[ord("가")]][0] == (
            font["hmtx"].metrics[cmap[ord("A")]][0] * 2
        )
        assert bool(font["head"].macStyle & (1 << 1)) is variant.is_italic
        assert bool(font["OS/2"].fsSelection & (1 << 0)) is variant.is_italic
        assert cmap[0xE0B0]
        assert "ccmp" in features
        font.close()
