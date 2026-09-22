#!/usr/bin/env python3
"""Validate the public release allowlist without private firmware keys."""

import hashlib
from pathlib import Path
import re
import struct
import sys


PREFIX = "ARM32SolderingStationWeb"
MANIFEST = struct.Struct("<I H B B 4H 4H I I H B B 16s 32s 32s 8s")
WEB_HEADER = struct.Struct("<8sHHHHI24s32sI")


def validate(root: Path, tag: str) -> None:
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+", tag):
        raise ValueError("Expected a four-component version tag")
    version = tuple(int(part) for part in tag[1:].split("."))
    if any(part > 65535 for part in version):
        raise ValueError("Version component out of range")
    directory = root / "packages" / tag
    packages = {f"{PREFIX}-board_v{board}-{tag}.ota": board for board in (1, 2, 3)}
    web_name = f"{PREFIX}-esp32c3-{tag}.espota"
    packages[web_name] = 0
    expected = set(packages) | {"SHA256SUMS.txt"}
    if {path.name for path in directory.iterdir()} != expected:
        raise ValueError("Release must contain exactly four packages and SHA256SUMS.txt")
    if any(path.is_symlink() or not path.is_file() for path in directory.iterdir()):
        raise ValueError("Only regular release files are allowed")
    notes = root / "release-notes" / f"{tag}.md"
    if notes.is_symlink() or not notes.is_file() or not notes.read_text().strip():
        raise ValueError("Release notes are required")
    expected_sums = []
    for name, board in packages.items():
        data = (directory / name).read_bytes()
        if board:
            fields = MANIFEST.unpack_from(data)
            if (fields[0:4] != (0x4F544150, 1, board, 0)
                    or fields[4:8] != version or fields[12] != 0x8000
                    or not 8 <= fields[13] <= 0x72000
                    or len(data) != MANIFEST.size + fields[13]
                    or not 1 <= fields[14] <= 512 or fields[15:17] != (1, 1)):
                raise ValueError(f"Invalid station manifest: {name}")
        else:
            magic, fmt, size, chip, layout, length, encoded, digest, reserved = WEB_HEADER.unpack_from(data)
            payload = data[WEB_HEADER.size:]
            if ((magic, fmt, size, chip, layout, reserved) != (b"SWEBOTA1", 1, 80, 5, 1, 0)
                    or encoded != tag[1:].encode().ljust(24, b"\0")
                    or not 256 <= length <= 0x180000 or length != len(payload)
                    or hashlib.sha256(payload).digest() != digest):
                raise ValueError(f"Invalid web package: {name}")
        expected_sums.append(f"{hashlib.sha256(data).hexdigest()}  {name}")
    actual_sums = (directory / "SHA256SUMS.txt").read_text().splitlines()
    if sorted(actual_sums) != sorted(expected_sums):
        raise ValueError("SHA256SUMS.txt does not match the exact package set")
    print(f"Validated {tag}: three encrypted station packages and one web package")


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            raise ValueError("Usage: validate_release.py v<version>")
        validate(Path(__file__).resolve().parents[1], sys.argv[1])
    except (OSError, ValueError, struct.error) as error:
        sys.exit(str(error))
