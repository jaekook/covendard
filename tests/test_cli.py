"""Tests for the Jetendard CLI helpers."""

from __future__ import annotations

import pytest

from jetendard.builder import DEFAULT_VARIANTS, get_variants_by_names
from jetendard.cli import (
    family_file_stem,
    select_variants,
    validate_styles,
    validate_weights,
    write_css,
)


def test_family_file_stem_removes_spaces() -> None:
    assert family_file_stem("Jetendard Mono") == "JetendardMono"


def test_validate_weights_accepts_supported_weights() -> None:
    assert validate_weights(["Regular", "Light", "Bold"]) == ["Regular", "Light", "Bold"]


def test_validate_weights_rejects_unknown_weight() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        validate_weights(["Regular", "Book"])


def test_validate_weights_rejects_black_until_matching_latin_source_exists() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        validate_weights(["Black"])


def test_validate_styles_accepts_supported_styles() -> None:
    assert validate_styles(["normal", "italic", "normal"]) == ["normal", "italic"]


def test_validate_styles_rejects_unknown_style() -> None:
    with pytest.raises(ValueError, match="Unsupported"):
        validate_styles(["oblique"])


def test_select_variants_defaults_to_full_coverage() -> None:
    assert select_variants() == list(DEFAULT_VARIANTS)


def test_select_variants_weights_default_to_upright() -> None:
    variants = select_variants(weights=["Regular", "Bold"])
    assert [variant.output_suffix for variant in variants] == ["Regular", "Bold"]


def test_select_variants_weights_and_styles_cross_product() -> None:
    variants = select_variants(weights=["Regular", "Bold"], styles=["normal", "italic"])
    assert [variant.output_suffix for variant in variants] == [
        "Regular",
        "Italic",
        "Bold",
        "BoldItalic",
    ]


def test_select_variants_explicit_names() -> None:
    variants = select_variants(variant_names=["Regular", "BoldItalic"])
    assert [variant.output_suffix for variant in variants] == ["Regular", "BoldItalic"]


def test_select_variants_rejects_ambiguous_combinations() -> None:
    with pytest.raises(ValueError, match="--all cannot be combined"):
        select_variants(all_variants=True, weights=["Regular"])
    with pytest.raises(ValueError, match="--variants cannot be combined"):
        select_variants(variant_names=["Regular"], styles=["italic"])


def test_caskaydiacove_selects_matching_sources() -> None:
    variants = select_variants(
        latin_family="caskaydiacove", weights=["Regular", "Bold"], styles=["normal", "italic"]
    )
    assert [variant.latin_filename for variant in variants] == [
        "CaskaydiaCoveNerdFontMono-Regular.ttf",
        "CaskaydiaCoveNerdFontMono-Italic.ttf",
        "CaskaydiaCoveNerdFontMono-Bold.ttf",
        "CaskaydiaCoveNerdFontMono-BoldItalic.ttf",
    ]
    assert [variant.cjk_weight_name for variant in variants] == ["Regular"] * 2 + ["Bold"] * 2
    assert [variant.css_weight for variant in variants] == [400, 400, 700, 700]


def test_caskaydiacove_all_uses_only_matching_weights() -> None:
    variants = select_variants(latin_family="caskaydiacove", all_variants=True)
    assert len(variants) == 10
    assert {variant.weight_name for variant in variants} == {
        "ExtraLight",
        "Light",
        "Regular",
        "SemiBold",
        "Bold",
    }


@pytest.mark.parametrize("weight", ["Thin", "Medium", "ExtraBold", "SemiLight"])
def test_caskaydiacove_rejects_unmatched_weights_and_variants(weight: str) -> None:
    with pytest.raises(ValueError, match="Unsupported weight"):
        select_variants(latin_family="caskaydiacove", weights=[weight])
    with pytest.raises(ValueError, match="Unsupported variant"):
        select_variants(latin_family="caskaydiacove", variant_names=[weight])


def test_caskaydiacove_explicit_variants_preserve_order_and_dedupe() -> None:
    variants = select_variants(
        latin_family="caskaydiacove", variant_names=["BoldItalic", "Regular", "BoldItalic"]
    )
    assert [variant.output_suffix for variant in variants] == ["BoldItalic", "Regular"]
    assert all(
        variant.latin_filename.startswith("CaskaydiaCoveNerdFontMono-") for variant in variants
    )


def test_write_css_generates_font_face_rules(tmp_path) -> None:
    variants = get_variants_by_names(["Regular", "Italic", "BoldItalic"])
    css_path = write_css(tmp_path, "Jetendard", variants)
    content = css_path.read_text(encoding="utf-8")

    assert css_path.name == "jetendard.css"
    assert "font-family: 'Jetendard';" in content
    assert "Jetendard-Regular.woff2" in content
    assert "font-weight: 400;" in content
    assert "font-style: normal;" in content
    assert "Jetendard-Italic.woff2" in content
    assert "font-style: italic;" in content
    assert "Jetendard-BoldItalic.woff2" in content
    assert "font-weight: 700;" in content
