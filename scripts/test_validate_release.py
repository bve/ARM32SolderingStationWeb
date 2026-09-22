"""Exercise release checks with synthetic, key-free packages."""

import hashlib
from pathlib import Path
import tempfile
import unittest

import validate_release as validator


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.tag = "v1.0.1.4"
        self.directory = self.root / "packages" / self.tag
        self.directory.mkdir(parents=True)
        self.notes = self.root / "release-notes" / f"{self.tag}.md"
        self.notes.parent.mkdir()
        self.notes.write_text("Compatibility notes")
        for board in (1, 2, 3):
            header = validator.MANIFEST.pack(
                0x4F544150, 1, board, 0, 1, 0, 1, 4, 1, 0, 0, 0,
                0x8000, 16, 512, 1, 1, bytes(16), bytes(32), bytes(32), bytes(8))
            (self.directory / f"{validator.PREFIX}-board_v{board}-{self.tag}.ota").write_bytes(header + bytes(16))
        payload = bytes(256)
        header = validator.WEB_HEADER.pack(
            b"SWEBOTA1", 1, 80, 5, 1, len(payload), b"1.0.1.4".ljust(24, b"\0"),
            hashlib.sha256(payload).digest(), 0)
        self.web = self.directory / f"{validator.PREFIX}-esp32c3-{self.tag}.espota"
        self.web.write_bytes(header + payload)
        self.write_sums()

    def write_sums(self):
        packages = sorted(path for path in self.directory.iterdir() if path.suffix in (".ota", ".espota"))
        lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}" for path in packages]
        (self.directory / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")

    def test_valid(self):
        validator.validate(self.root, self.tag)

    def test_extra_factory_file(self):
        (self.directory / "private.hcf").write_bytes(b"not a public asset")
        with self.assertRaises(ValueError):
            validator.validate(self.root, self.tag)

    def test_missing_package(self):
        self.web.unlink()
        with self.assertRaises(ValueError):
            validator.validate(self.root, self.tag)

    def test_corrupt_web_payload_even_with_matching_file_checksum(self):
        data = bytearray(self.web.read_bytes()); data[-1] ^= 1
        self.web.write_bytes(data); self.write_sums()
        with self.assertRaises(ValueError):
            validator.validate(self.root, self.tag)

    def test_legacy_layout_even_with_matching_file_checksum(self):
        station = self.directory / f"{validator.PREFIX}-board_v1-{self.tag}.ota"
        data = bytearray(station.read_bytes())
        data[24:28] = (0x10000).to_bytes(4, "little")
        station.write_bytes(data); self.write_sums()
        with self.assertRaises(ValueError):
            validator.validate(self.root, self.tag)

    def test_invalid_tag(self):
        for tag in ("../secret", "v1.0", "v1.0.1.4; false", "v65536.0.0.0"):
            with self.subTest(tag=tag), self.assertRaises(ValueError):
                validator.validate(self.root, tag)

    def test_missing_checksum_entry(self):
        (self.directory / "SHA256SUMS.txt").write_text("")
        with self.assertRaises(ValueError):
            validator.validate(self.root, self.tag)


if __name__ == "__main__":
    unittest.main()
