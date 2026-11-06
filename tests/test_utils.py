"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: unit tests for the drivefs_sleuth utility functions.
"""

import os
import tempfile
import unittest

from builders import ACCOUNT_ID_1
from builders import CACHE_FILE_400
from builders import EMAIL_1
from builders import build_logged_in_fixture
from builders import encode_content_entry

from drivefs_sleuth.utils import copy_file
from drivefs_sleuth.utils import get_available_profiles
from drivefs_sleuth.utils import get_content_caches_paths
from drivefs_sleuth.utils import get_file_content_cache_path
from drivefs_sleuth.utils import get_last_pid
from drivefs_sleuth.utils import get_last_sync
from drivefs_sleuth.utils import get_tree_path_rel_dir
from drivefs_sleuth.utils import lookup_account_id
from drivefs_sleuth.utils import parse_protobuf
from drivefs_sleuth.utils import redact_local_path
from drivefs_sleuth.utils import redact_local_paths_in_text


class TestParseProtobuf(unittest.TestCase):
    def test_empty_values_return_empty_dict(self):
        self.assertEqual(parse_protobuf(None), {})
        self.assertEqual(parse_protobuf(b""), {})

    def test_invalid_bytes_return_empty_dict(self):
        self.assertEqual(parse_protobuf(b"\x99\x99\x99\x99 not a protobuf"), {})

    def test_valid_blob_decodes(self):
        blob = encode_content_entry(CACHE_FILE_400)
        parsed = parse_protobuf(blob)
        self.assertEqual(parsed.get("1"), CACHE_FILE_400)


class TestLookupAccountId(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_existing_account_email_is_found(self):
        self.assertEqual(lookup_account_id(self.fixture.drivefs_path, ACCOUNT_ID_1), EMAIL_1)

    def test_unknown_account_returns_empty_string(self):
        self.assertEqual(lookup_account_id(self.fixture.drivefs_path, "999999999999999999999"), "")

    def test_missing_logs_directory_returns_empty_string(self):
        empty_tmp = tempfile.TemporaryDirectory()
        self.addCleanup(empty_tmp.cleanup)
        self.assertEqual(lookup_account_id(empty_tmp.name, ACCOUNT_ID_1), "")


class TestGetFileContentCachePath(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.content_caches_paths = {CACHE_FILE_400: os.path.join(self.tmp.name, CACHE_FILE_400)}

    def test_valid_content_entry_maps_to_cache_path(self):
        blob = encode_content_entry(CACHE_FILE_400)
        self.assertEqual(
            get_file_content_cache_path(blob, self.content_caches_paths),
            os.path.join(self.tmp.name, CACHE_FILE_400),
        )

    def test_missing_content_entry_returns_empty_string(self):
        self.assertEqual(get_file_content_cache_path(None, self.content_caches_paths), "")

    def test_unknown_cache_filename_returns_empty_string(self):
        blob = encode_content_entry("does-not-exist")
        self.assertEqual(get_file_content_cache_path(blob, self.content_caches_paths), "")


class TestGetAvailableProfiles(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_only_21_digit_directories_are_returned(self):
        os.makedirs(os.path.join(self.tmp.name, "111111111111111111111"))
        os.makedirs(os.path.join(self.tmp.name, "222222222222222222222"))
        os.makedirs(os.path.join(self.tmp.name, "12345"))
        os.makedirs(os.path.join(self.tmp.name, "not-a-profile"))
        profiles = get_available_profiles(self.tmp.name)
        self.assertEqual(sorted(profiles), ["111111111111111111111", "222222222222222222222"])


class TestGetLastSyncAndPid(unittest.TestCase):
    def test_missing_files_return_defaults(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.assertEqual(get_last_sync(tmp.name), -1)
        self.assertEqual(get_last_pid(tmp.name), -1)


class TestGetContentCachesPaths(unittest.TestCase):
    def test_chunks_db_is_excluded_and_files_are_indexed(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        nested = os.path.join(tmp.name, "d0")
        os.makedirs(nested)
        for filename in ["chunks.db", "chunks.db-shm", "chunks.db-wal", "cachefile-1", "cachefile-2"]:
            with open(os.path.join(nested, filename), "wb") as cache_file:
                cache_file.write(b"x")
        paths = get_content_caches_paths(nested)
        self.assertNotIn("chunks.db", paths)
        self.assertNotIn("chunks.db-shm", paths)
        self.assertNotIn("chunks.db-wal", paths)
        self.assertIn("cachefile-1", paths)
        self.assertIn("cachefile-2", paths)
        self.assertEqual(paths["cachefile-1"], os.path.abspath(os.path.join(nested, "cachefile-1")))


class TestGetTreePathRelDir(unittest.TestCase):
    def test_nested_tree_path_returns_dir_components(self):
        self.assertEqual(
            get_tree_path_rel_dir("My Drive\\Work\\Reports\\notes.txt"),
            ("My Drive", "Work", "Reports"),
        )

    def test_single_component_path_returns_empty_tuple(self):
        self.assertEqual(get_tree_path_rel_dir("Unknown - 42.bin"), ())

    def test_unknown_and_empty_paths_return_empty_tuple(self):
        self.assertEqual(get_tree_path_rel_dir("Unknown"), ())
        self.assertEqual(get_tree_path_rel_dir(""), ())
        self.assertEqual(get_tree_path_rel_dir(None), ())

    def test_dot_components_are_dropped(self):
        self.assertEqual(
            get_tree_path_rel_dir("My Drive\\..\\Work\\.\\notes.txt"),
            ("My Drive", "Work"),
        )

    def test_invalid_chars_are_sanitized(self):
        self.assertEqual(
            get_tree_path_rel_dir("My Drive\\Bad<Dir>\\notes.txt"),
            ("My Drive", "Bad_Dir_"),
        )


class TestRedactLocalPath(unittest.TestCase):
    def test_path_under_drivefs_is_prefixed(self):
        self.assertEqual(
            redact_local_path(
                os.path.join("/tmp", "DriveFS", "111", "content_cache", "abc"),
                "/tmp/DriveFS",
            ),
            "<DriveFS>/111/content_cache/abc",
        )

    def test_exact_drivefs_path_returns_marker(self):
        self.assertEqual(redact_local_path("/tmp/DriveFS", "/tmp/DriveFS"), "<DriveFS>")

    def test_trailing_slash_drivefs_still_matches(self):
        self.assertEqual(
            redact_local_path("/tmp/DriveFS/111/content_cache/abc", "/tmp/DriveFS/"),
            "<DriveFS>/111/content_cache/abc",
        )

    @unittest.skipUnless(os.path.expanduser("~") != os.sep, "home directory is the filesystem root")
    def test_path_under_home_is_prefixed(self):
        home = os.path.expanduser("~")
        self.assertEqual(
            redact_local_path(os.path.join(home, "Documents", "mirror"), "/tmp/DriveFS"),
            "<home>/Documents/mirror",
        )
        self.assertEqual(redact_local_path(home, "/tmp/DriveFS"), "<home>")

    def test_unmatched_absolute_path_is_redacted(self):
        self.assertEqual(
            redact_local_path("/media/analyst/EXTERNAL", "/tmp/DriveFS"), "<redacted>"
        )

    def test_windows_style_path_is_redacted(self):
        self.assertEqual(
            redact_local_path("C:\\Users\\Analyst\\mirror", "/tmp/DriveFS"), "<redacted>"
        )
        self.assertEqual(redact_local_path("C:\\", "/tmp/DriveFS"), "<redacted>")

    def test_relative_unmatched_path_is_unchanged(self):
        self.assertEqual(
            redact_local_path("relative/notes.txt", "/tmp/DriveFS"), "relative/notes.txt"
        )

    def test_falsy_and_non_string_values_are_unchanged(self):
        self.assertEqual(redact_local_path(None, "/tmp/DriveFS"), None)
        self.assertEqual(redact_local_path("", "/tmp/DriveFS"), "")


class TestRedactLocalPathsInText(unittest.TestCase):
    def test_drivefs_occurrences_inside_message_are_prefixed(self):
        self.assertEqual(
            redact_local_paths_in_text(
                "[Errno 13] Permission denied: '/tmp/DriveFS/111/content_cache/x'",
                "/tmp/DriveFS",
            ),
            "[Errno 13] Permission denied: '<DriveFS>/111/content_cache/x'",
        )

    def test_home_occurrences_inside_message_are_prefixed(self):
        home = os.path.expanduser("~")
        self.assertEqual(
            redact_local_paths_in_text(
                f"failed to open {os.path.join(home, 'Documents', 'x')}", "/tmp/DriveFS"
            ),
            f"failed to open <home>{os.sep}Documents{os.sep}x",
        )

    def test_plain_text_without_paths_is_unchanged(self):
        self.assertEqual(
            redact_local_paths_in_text("some error happened", "/tmp/DriveFS"),
            "some error happened",
        )

    def test_falsy_and_non_string_values_are_unchanged(self):
        self.assertEqual(redact_local_paths_in_text(None, "/tmp/DriveFS"), None)
        self.assertEqual(redact_local_paths_in_text("", "/tmp/DriveFS"), "")


class TestCopyFile(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = os.path.join(self.tmp.name, "source.txt")
        with open(self.source, "wb") as source_file:
            source_file.write(b"content")
        self.recovery_path = os.path.join(self.tmp.name, "recovery")

    def test_copy_creates_destination_file(self):
        copy_file(self.source, "copied.txt", self.recovery_path)
        copied_path = os.path.join(self.recovery_path, "copied.txt")
        self.assertTrue(os.path.exists(copied_path))
        with open(copied_path, "rb") as copied_file:
            self.assertEqual(copied_file.read(), b"content")

    def test_duplicate_filenames_are_suffixed(self):
        copy_file(self.source, "copied.txt", self.recovery_path)
        copy_file(self.source, "copied.txt", self.recovery_path)
        copy_file(self.source, "copied.txt", self.recovery_path)
        self.assertTrue(os.path.exists(os.path.join(self.recovery_path, "copied.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.recovery_path, "copied (1).txt")))
        self.assertTrue(os.path.exists(os.path.join(self.recovery_path, "copied (2).txt")))

    def test_invalid_filename_characters_are_sanitized(self):
        copy_file(self.source, 'bad<>:"/\\|?*name.txt', self.recovery_path)
        self.assertTrue(os.path.exists(os.path.join(self.recovery_path, "bad_________name.txt")))

    def test_used_names_claim_continues_numbering(self):
        used_names = {"copied.txt"}
        copy_file(self.source, "copied.txt", self.recovery_path, used_names=used_names)
        copy_file(self.source, "copied.txt", self.recovery_path, used_names=used_names)
        self.assertTrue(os.path.exists(os.path.join(self.recovery_path, "copied (1).txt")))
        self.assertTrue(os.path.exists(os.path.join(self.recovery_path, "copied (2).txt")))
        self.assertFalse(os.path.exists(os.path.join(self.recovery_path, "copied.txt")))
        self.assertEqual(used_names, {"copied.txt", "copied (1).txt", "copied (2).txt"})

    def test_used_names_seeded_with_existing_files(self):
        os.makedirs(self.recovery_path)
        with open(os.path.join(self.recovery_path, "copied.txt"), "wb") as existing:
            existing.write(b"pre-existing")
        used_names = {name for name in os.listdir(self.recovery_path)}
        copy_file(self.source, "copied.txt", self.recovery_path, used_names=used_names)
        self.assertTrue(os.path.exists(os.path.join(self.recovery_path, "copied (1).txt")))
        with open(os.path.join(self.recovery_path, "copied.txt"), "rb") as existing:
            self.assertEqual(existing.read(), b"pre-existing")


if __name__ == "__main__":
    unittest.main()
