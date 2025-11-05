#!/usr/bin/env python3
"""Strip metadata fields unsupported by legacy PyPI validators."""
from __future__ import annotations

import base64
import csv
import hashlib
import io
import shutil
import tarfile
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

DIST_DIR = Path("dist")


def _strip_license_lines(text: str) -> str:
    lines = [line for line in text.splitlines() if not line.lower().startswith("license-file:")]
    return "\n".join(lines) + "\n"


def sanitize_wheel(path: Path) -> None:
    extract_dir = Path(tempfile.mkdtemp())
    try:
        with ZipFile(path) as zf:
            zf.extractall(extract_dir)
        metadata_paths = list(extract_dir.rglob("*.dist-info/METADATA"))
        if not metadata_paths:
            return
        changed = False
        for metadata_path in metadata_paths:
            original = metadata_path.read_text(encoding="utf-8")
            stripped = _strip_license_lines(original)
            if stripped != original:
                metadata_path.write_text(stripped, encoding="utf-8")
                changed = True
        if not changed:
            return
        # Update RECORD with fresh hashes for all files in the archive
        record_path = next(extract_dir.rglob("*.dist-info/RECORD"))
        records: list[tuple[str, str, str]] = []
        record_entry = None
        for file_path in sorted(extract_dir.rglob("*")):
            if file_path.is_dir():
                continue
            relative = file_path.relative_to(extract_dir).as_posix()
            if relative.endswith(".dist-info/RECORD"):
                record_entry = relative
                continue
            data = file_path.read_bytes()
            digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
            records.append((relative, f"sha256={digest}", str(len(data))))
        # RECORD should reference itself without hash
        if record_entry is None:
            record_entry = record_path.relative_to(extract_dir).as_posix()
        records.append((record_entry, "", ""))
        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerows(records)
        record_path.write_text(output.getvalue(), encoding="utf-8")
        output_path = path.with_suffix(path.suffix + ".tmp")
        with ZipFile(output_path, "w", compression=ZIP_DEFLATED) as zf:
            for file_path in sorted(extract_dir.rglob("*")):
                if file_path.is_dir():
                    continue
                relative = file_path.relative_to(extract_dir).as_posix()
                zf.write(file_path, arcname=relative)
        shutil.move(output_path, path)
    finally:
        shutil.rmtree(extract_dir)


def sanitize_sdist(path: Path) -> None:
    extract_dir = Path(tempfile.mkdtemp())
    try:
        with tarfile.open(path) as tf:
            tf.extractall(extract_dir)
        pkg_infos = list(extract_dir.rglob("PKG-INFO"))
        if not pkg_infos:
            return
        changed = False
        for pkg_info in pkg_infos:
            original = pkg_info.read_text(encoding="utf-8")
            stripped = _strip_license_lines(original)
            if stripped != original:
                pkg_info.write_text(stripped, encoding="utf-8")
                changed = True
        if not changed:
            return
        output_path = path.with_suffix(path.suffix + ".tmp")
        with tarfile.open(output_path, "w:gz") as tf:
            for file_path in sorted(extract_dir.rglob("*")):
                if file_path.is_dir():
                    continue
                tf.add(file_path, arcname=file_path.relative_to(extract_dir))
        shutil.move(output_path, path)
    finally:
        shutil.rmtree(extract_dir)


def main() -> None:
    if not DIST_DIR.exists():
        return
    for path in DIST_DIR.iterdir():
        if path.suffix == ".whl":
            sanitize_wheel(path)
        elif path.suffixes[-2:] == [".tar", ".gz"]:
            sanitize_sdist(path)


if __name__ == "__main__":
    main()
