"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: unit tests for the magic-based file type detection used by the deleted and orphan files model.
"""

import os
import tempfile
import unittest

from drivefs_sleuth.utils import detect_file_type


PNG_HEADER = b"\x89PNG\r\n\x1a\n"
JPEG_HEADER = b"\xff\xd8\xff\xe0"
ASCII_GARBAGE = b"NOT A KNOWN MAGIC HEADER AT ALL"
BINARY_GARBAGE = b"\x00\x01\x02binary\x00garbage"


class DetectFileTypeTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def _write(self, name, content):
        path = os.path.join(self.tmp.name, name)
        with open(path, "wb") as handle:
            handle.write(content)
        return path

    def test_png_content_detected_as_png(self):
        path = self._write("5555.bin", PNG_HEADER + b"payload")
        self.assertEqual(detect_file_type(path)["extension"], "png")

    def test_jpeg_content_detected(self):
        path = self._write("5555", JPEG_HEADER + b"payload")
        self.assertEqual(detect_file_type(path)["extension"], "jfif")

    def test_unknown_binary_content_has_no_extension(self):
        path = self._write("5555.bin", BINARY_GARBAGE)
        self.assertFalse(detect_file_type(path).get("extension"))

    def test_ascii_content_detected_as_text(self):
        path = self._write("5555.bin", ASCII_GARBAGE)
        self.assertEqual(detect_file_type(path)["extension"], "txt")

    def test_misleading_extension_is_ignored(self):
        path = self._write("5555.dat", PNG_HEADER + b"payload")
        self.assertEqual(detect_file_type(path)["extension"], "png")

    def test_empty_file_has_no_extension(self):
        path = self._write("5555.bin", b"")
        self.assertFalse(detect_file_type(path).get("extension"))

    def test_missing_file_returns_empty_dict(self):
        path = os.path.join(self.tmp.name, "does_not_exist")
        self.assertEqual(detect_file_type(path), {})

    def test_directory_returns_empty_dict(self):
        self.assertEqual(detect_file_type(self.tmp.name), {})


if __name__ == "__main__":
    unittest.main()
