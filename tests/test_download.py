"""Source selection and recovery tests without network downloads."""

from __future__ import annotations

import importlib.util
import zipfile
from pathlib import Path

import pytest

from jetendard.builder import get_source_variants


@pytest.fixture
def downloader(tmp_path, monkeypatch):
    script = Path(__file__).resolve().parents[1] / "download_upstream.py"
    spec = importlib.util.spec_from_file_location("download_upstream", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "UPSTREAM_DIR", tmp_path)
    monkeypatch.setattr(module, "ARCHIVE_DIR", tmp_path / "_archives")
    monkeypatch.setattr(module, "PRETENDARD_DIR", tmp_path / "pretendard")
    return module


def test_caskaydiacove_download_selection_and_partial_recovery(downloader, monkeypatch, tmp_path):
    requested_urls = []
    variants = get_source_variants("caskaydiacove")

    def download_fixture(url, output_path):
        requested_urls.append(url)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        if "CascadiaCode.zip" in url:
            filenames = {variant.latin_filename for variant in variants}
            filenames.add("CaskaydiaCoveNerdFont-Regular.ttf")
        else:
            filenames = {f"Pretendard-{variant.cjk_weight_name}.ttf" for variant in variants}
            filenames.add("PretendardVariable.ttf")
        with zipfile.ZipFile(output_path, "w") as archive:
            for filename in filenames:
                archive.writestr(f"nested/{filename}", b"font fixture")

    monkeypatch.setattr(downloader, "download_file", download_fixture)
    args = ["--latin-family", "caskaydiacove", "--ensure"]
    assert downloader.main(args) == 0
    assert requested_urls[0].endswith("/v3.4.0/CascadiaCode.zip")
    latin_dir = tmp_path / "caskaydiacove"
    assert {path.name for path in latin_dir.iterdir()} == {
        variant.latin_filename for variant in variants
    }
    assert not (tmp_path / "jetbrainsmono").exists()
    assert "CaskaydiaCoveNerdFontMono" in (tmp_path / "SOURCES-caskaydiacove.md").read_text(
        encoding="utf-8"
    )

    requested_urls.clear()
    assert downloader.main(args) == 0
    assert requested_urls == []

    missing = latin_dir / "CaskaydiaCoveNerdFontMono-Regular.ttf"
    missing.unlink()
    assert downloader.main(args) == 0
    assert missing.read_bytes() == b"font fixture"
    assert len(requested_urls) == 2
