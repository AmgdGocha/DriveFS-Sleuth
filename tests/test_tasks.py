"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: unit tests for the orphaned cache recovery tasks and the magic-based extension sniffing.
"""

import os
import tempfile
import unittest

from drivefs_sleuth.tasks import __append_detected_extension as append_detected_extension
from drivefs_sleuth.tasks import __detect_orphan_extension as detect_orphan_extension
from drivefs_sleuth.tasks import recover_orphaned_cache


PNG_HEADER = b"\x89PNG\r\n\x1a\n"
JPEG_HEADER = b"\xff\xd8\xff\xe0"
ASCII_GARBAGE = b"NOT A KNOWN MAGIC HEADER AT ALL"
BINARY_GARBAGE = b"\x00\x01\x02binary\x00garbage"


class DetectOrphanExtensionTestCase(unittest.TestCase):
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
        self.assertEqual(detect_orphan_extension(path), "png")

    def test_jpeg_content_detected(self):
        path = self._write("5555", JPEG_HEADER + b"payload")
        self.assertEqual(detect_orphan_extension(path), "jfif")

    def test_unknown_binary_content_returns_none(self):
        path = self._write("5555.bin", BINARY_GARBAGE)
        self.assertIsNone(detect_orphan_extension(path))

    def test_ascii_content_detected_as_text(self):
        path = self._write("5555.bin", ASCII_GARBAGE)
        self.assertEqual(detect_orphan_extension(path), "txt")

    def test_misleading_extension_is_ignored(self):
        path = self._write("5555.dat", PNG_HEADER + b"payload")
        self.assertEqual(detect_orphan_extension(path), "png")

    def test_empty_file_returns_none(self):
        path = self._write("5555.bin", b"")
        self.assertIsNone(detect_orphan_extension(path))

    def test_missing_file_returns_none(self):
        path = os.path.join(self.tmp.name, "does_not_exist")
        self.assertIsNone(detect_orphan_extension(path))

    def test_directory_returns_none(self):
        self.assertIsNone(detect_orphan_extension(self.tmp.name))


class AppendDetectedExtensionTestCase(unittest.TestCase):
    def test_appends_extension(self):
        self.assertEqual(append_detected_extension("5555", "png"), "5555.png")

    def test_appends_to_existing_unrelated_extension(self):
        self.assertEqual(append_detected_extension("5555.bin", "png"), "5555.bin.png")

    def test_keeps_name_when_extension_already_present(self):
        self.assertEqual(append_detected_extension("5555.png", "png"), "5555.png")

    def test_keeps_name_when_extension_already_present_case_insensitive(self):
        self.assertEqual(append_detected_extension("5555.PNG", "png"), "5555.PNG")

    def test_keeps_name_without_detected_extension(self):
        self.assertEqual(append_detected_extension("5555", None), "5555")
        self.assertEqual(append_detected_extension("5555", ""), "5555")


class RecoverOrphanedCacheTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source_dir = os.path.join(self.tmp.name, "source")
        self.recovery_dir = os.path.join(self.tmp.name, "recovery")
        os.makedirs(self.source_dir)
        self.png_path = os.path.join(self.source_dir, "5555.bin")
        with open(self.png_path, "wb") as handle:
            handle.write(PNG_HEADER + b"payload")
        self.garbage_path = os.path.join(self.source_dir, "6666")
        with open(self.garbage_path, "wb") as handle:
            handle.write(BINARY_GARBAGE)

    def test_recovers_orphans_with_sniffed_extensions(self):
        count = recover_orphaned_cache(
            [self.png_path, self.garbage_path], self.recovery_dir
        )
        self.assertEqual(count, 2)
        recovered_png = os.path.join(
            self.recovery_dir, "orphaned_cache", "5555.bin.png"
        )
        with open(recovered_png, "rb") as recovered:
            self.assertEqual(recovered.read(), PNG_HEADER + b"payload")
        self.assertTrue(
            os.path.exists(os.path.join(self.recovery_dir, "orphaned_cache", "6666"))
        )

    def test_recovers_no_orphans_for_empty_list(self):
        self.assertEqual(recover_orphaned_cache([], self.recovery_dir), 0)
        self.assertFalse(
            os.path.exists(os.path.join(self.recovery_dir, "orphaned_cache"))
        )

    def test_parallel_and_sequential_recovery_produce_identical_output(self):
        sources = [self.png_path, self.garbage_path]
        for index in range(6):
            path = os.path.join(self.source_dir, f"{7000 + index}.bin")
            with open(path, "wb") as handle:
                handle.write(PNG_HEADER + bytes([index]) * 64)
            sources.append(path)
        parallel_dir = os.path.join(self.tmp.name, "parallel")
        sequential_dir = os.path.join(self.tmp.name, "sequential")
        self.assertEqual(recover_orphaned_cache(sources, parallel_dir, workers=8), 8)
        self.assertEqual(recover_orphaned_cache(sources, sequential_dir, workers=1), 8)
        parallel_files = {}
        for root, _, files in os.walk(os.path.join(parallel_dir, "orphaned_cache")):
            for name in files:
                path = os.path.join(root, name)
                with open(path, "rb") as handle:
                    parallel_files[os.path.relpath(path, parallel_dir)] = handle.read()
        self.assertTrue(parallel_files)
        for rel, content in parallel_files.items():
            with open(os.path.join(sequential_dir, rel), "rb") as handle:
                self.assertEqual(handle.read(), content)


if __name__ == "__main__":
    unittest.main()
