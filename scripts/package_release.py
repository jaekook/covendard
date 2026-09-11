"""Package four release styles with licenses and optionally sync static site assets."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STYLES = ("Regular", "Italic", "Bold", "BoldItalic")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--site-dir", type=Path)
    args = parser.parse_args()
    entries: dict[str, Path] = {}
    for folder, extension in (("ttf", "ttf"), ("webfont", "woff2")):
        for style in STYLES:
            name = f"Covendard-{style}.{extension}"
            entries[f"{folder}/{name}"] = ROOT / "fonts" / folder / name
    entries["webfont/covendard.css"] = ROOT / "fonts/webfont/covendard.css"
    entries.update({name: ROOT / name for name in ("LICENSE", "README.md", "README.ko.md")})
    entries.update({f"licenses/{path.name}": path for path in (ROOT / "licenses").glob("*.txt")})
    for path in entries.values():
        if not path.is_file():
            parser.error(f"Missing release input: {path}; run make run first")
    output = ROOT / "dist"
    output.mkdir(exist_ok=True)
    archive = output / "Covendard.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        for name, path in sorted(entries.items()):
            info = zipfile.ZipInfo(f"Covendard/{name}", (2026, 9, 11, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            bundle.writestr(info, path.read_bytes())
    if archive.stat().st_size > 25 * 1024 * 1024:
        parser.error("Release ZIP exceeds the Cloudflare 25 MiB asset limit")
    checksum = hashlib.sha256(archive.read_bytes()).hexdigest()
    checksum_file = output / "Covendard.zip.sha256"
    checksum_file.write_text(f"{checksum}  Covendard.zip\n")
    if args.site_dir:
        downloads = args.site_dir / "downloads"
        downloads.mkdir(parents=True, exist_ok=True)
        for path in (archive, checksum_file):
            shutil.copy2(path, downloads / path.name)
        for name, path in entries.items():
            if name.startswith(("webfont/", "licenses/")) or name == "LICENSE":
                target = args.site_dir / name
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
    print(f"{archive}: {archive.stat().st_size:,} bytes; SHA-256 {checksum}")


if __name__ == "__main__":
    main()
