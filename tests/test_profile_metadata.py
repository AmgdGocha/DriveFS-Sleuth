"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: unit tests for the bulk metadata loading, invalid UTF-8 text handling,
single protobuf parsing and cache path collection used by the performance refactor.
"""

import contextlib
import io
import os
import sqlite3
import tempfile
import unittest
from unittest import mock

from builders import ACCOUNT_ID_1
from builders import ITEMS_DDL
from builders import MD5_B
from builders import STABLE_MISSING_CHILD
from builders import STABLE_NOTES_FILE
from builders import STABLE_REPORT_FILE
from builders import STABLE_ROOT_1
from builders import STABLE_SHARED_FILE
from builders import TITLE_NOTES_FILE
from builders import TITLE_REPORT_FILE
from builders import TITLE_SHARED_FILE
from builders import build_logged_in_fixture

from drivefs_sleuth.investigation import Investigation
from drivefs_sleuth.synced_files_tree import Directory
from drivefs_sleuth.synced_files_tree import File
from drivefs_sleuth.tasks import generate_html_report
from drivefs_sleuth.utils import ProfileMetadata
from drivefs_sleuth.utils import decode_utf8
from drivefs_sleuth.utils import get_content_caches_paths
from drivefs_sleuth.utils import get_deleted_items
from drivefs_sleuth.utils import get_item_info
from drivefs_sleuth.utils import get_item_properties
from drivefs_sleuth.utils import get_parent_relationships
from drivefs_sleuth.utils import get_shared_with_me_without_link
from drivefs_sleuth.utils import get_target_stable_id


def _insert_invalid_utf8_item(profile_path, stable_id):
    db = sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db"))
    bad_bytes = b'\x00\x01\x02BAD\xff\xfe TITLE'
    db.execute(
        "INSERT INTO items (stable_id, id, proto, trashed, is_owner, mime_type, is_folder, modified_date, "
        "shared_with_me_date, viewed_by_me_date, file_size, is_tombstone, local_title, subscribed, "
        "team_drive_stable_id, local_title_tokenized) "
        "VALUES (?, ?, CAST(? AS TEXT), 0, 1, 'text/plain', 0, 0, 0, 0, 10, 0, CAST(? AS TEXT), 1, NULL, NULL)",
        (stable_id, f"url-id-{stable_id}", bad_bytes, bad_bytes),
    )
    db.execute(
        "INSERT INTO stable_parents (item_stable_id, parent_stable_id, local_title_hash) VALUES (?, ?, 0)",
        (stable_id, STABLE_ROOT_1),
    )
    db.commit()
    db.close()


class TestProfileMetadataEquivalence(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(self.tmp.name)
        self.metadata = ProfileMetadata(self.fixture.profile_path())

    def tearDown(self):
        self.tmp.cleanup()

    def test_accessors_match_legacy_functions(self):
        profile_path = self.fixture.profile_path()
        self.assertEqual(self.metadata.get_parent_relationships(),
                         get_parent_relationships(profile_path))
        self.assertEqual(self.metadata.get_deleted_items(), get_deleted_items(profile_path))
        self.assertEqual(self.metadata.get_shared_with_me_without_link(),
                         get_shared_with_me_without_link(profile_path))

        db = sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db"))
        stable_ids = [row[0] for row in db.execute("SELECT stable_id FROM items")]
        db.close()
        for stable_id in stable_ids:
            self.assertEqual(self.metadata.get_item_info(stable_id),
                             get_item_info(profile_path, stable_id))
            self.assertEqual(self.metadata.get_item_properties(stable_id),
                             get_item_properties(profile_path, stable_id))
            self.assertEqual(self.metadata.get_target_stable_id(stable_id),
                             get_target_stable_id(profile_path, stable_id))

    def test_missing_item_returns_empty_tuple(self):
        self.assertEqual(self.metadata.get_item_info(STABLE_MISSING_CHILD + 9999), ())
        self.assertEqual(self.metadata.get_item_properties(STABLE_MISSING_CHILD + 9999), {})

    def test_string_stable_id_normalization(self):
        self.assertEqual(self.metadata.get_item_info(str(STABLE_NOTES_FILE))[1], STABLE_NOTES_FILE)


class TestSharedWithMeRewrite(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.profile_path = os.path.join(self.tmp.name, ACCOUNT_ID_1)
        os.makedirs(self.profile_path, exist_ok=True)
        db = sqlite3.connect(os.path.join(self.profile_path, "metadata_sqlite_db"))
        db.executescript(ITEMS_DDL)
        db.close()

    def tearDown(self):
        self.tmp.cleanup()

    def __insert(self, db, stable_id, is_owner, shared_with_me_date):
        db.execute(
            "INSERT INTO items (stable_id, id, proto, trashed, is_owner, mime_type, is_folder, modified_date, "
            "shared_with_me_date, viewed_by_me_date, file_size, is_tombstone, local_title, subscribed, "
            "team_drive_stable_id, local_title_tokenized) "
            "VALUES (?, ?, NULL, 0, ?, 'application/pdf', 0, 0, ?, 0, 1, 0, ?, 1, NULL, NULL)",
            (stable_id, f"url-id-{stable_id}", is_owner, shared_with_me_date, f"item-{stable_id}"),
        )

    def test_matches_left_join_semantics(self):
        db = sqlite3.connect(os.path.join(self.profile_path, "metadata_sqlite_db"))
        for stable_id, is_owner, shared in [(1, 0, 1), (2, 0, 1), (3, 0, 1), (4, 1, 1),
                                            (5, 0, 0), (6, 0, 1)]:
            self.__insert(db, stable_id, is_owner, shared)
        db.execute("INSERT INTO stable_parents (item_stable_id, parent_stable_id, local_title_hash) "
                   "VALUES (2, 100, 0), (6, 100, 0), (6, 200, 0)")
        db.execute("INSERT INTO shortcut_details (shortcut_stable_id, target_stable_id, target_mime_type) "
                   "VALUES (50, 3, 'application/pdf')")
        db.commit()
        db.close()

        legacy = get_shared_with_me_without_link(self.profile_path)
        bulk = ProfileMetadata(self.profile_path).get_shared_with_me_without_link()
        self.assertEqual(legacy, bulk)
        self.assertEqual([row[1] for row in legacy], [1])
        self.assertEqual(legacy[0][3], "item-1")


class TestInvalidUtf8TextCells(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(self.tmp.name)
        _insert_invalid_utf8_item(self.fixture.profile_path(), 901)

    def tearDown(self):
        self.tmp.cleanup()

    def test_legacy_get_item_info_returns_row_with_replacement_characters(self):
        row = get_item_info(self.fixture.profile_path(), 901)
        self.assertTrue(row)
        self.assertIsInstance(row[3], str)
        self.assertIn("\ufffd", row[3])

    def test_profile_metadata_returns_row(self):
        row = ProfileMetadata(self.fixture.profile_path()).get_item_info(901)
        self.assertTrue(row)
        self.assertIsInstance(row[3], str)
        self.assertIn("\ufffd", row[3])

    def test_investigation_builds_real_item_instead_of_dummy(self):
        investigation = Investigation(self.fixture.drivefs_path)
        tree = investigation.get_accounts()[0].get_synced_files_tree()
        item = tree.get_item_by_id(901)
        self.assertIsInstance(item, File)
        self.assertIn("\ufffd", item.local_title)
        deleted_ids = [deleted_item.get_stable_id() for deleted_item in tree.get_deleted_items()]
        self.assertNotIn(901, deleted_ids)
        rows = {row["stable_id"]: row for row in tree.generate_synced_files_tree_dicts()}
        self.assertIn(901, rows)


class TestSingleProtoParsing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_each_item_proto_parsed_exactly_once(self):
        with mock.patch(
            "drivefs_sleuth.synced_files_tree.parse_protobuf",
            side_effect=lambda value: {"48": "mocked"} if value else {},
        ) as parse_mock:
            investigation = Investigation(self.fixture.drivefs_path)
        self.assertEqual(parse_mock.call_count, 12)
        tree = investigation.get_accounts()[0].get_synced_files_tree()
        self.assertEqual(tree.get_item_by_id(STABLE_NOTES_FILE).md5, "mocked")
        self.assertEqual(tree.get_item_by_id(STABLE_SHARED_FILE).get_file_type(), "")


class TestCachePathsCollection(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_nested_files_are_indexed_and_chunks_db_excluded(self):
        content_cache_dir = os.path.join(self.tmp.name, "content_cache")
        os.makedirs(os.path.join(content_cache_dir, "d0"))
        os.makedirs(os.path.join(content_cache_dir, "d1"))
        for directory, filename in [("d0", "cachefile-1"), ("d0", "chunks.db"),
                                    ("d0", "chunks.db-shm"), ("d1", "cachefile-2")]:
            with open(os.path.join(content_cache_dir, directory, filename), "wb") as cache_file:
                cache_file.write(b"x")
        paths = get_content_caches_paths(content_cache_dir)
        self.assertNotIn("chunks.db", paths)
        self.assertNotIn("chunks.db-shm", paths)
        self.assertNotIn("chunks.db-wal", paths)
        self.assertEqual(paths["cachefile-1"],
                         os.path.abspath(os.path.join(content_cache_dir, "d0", "cachefile-1")))
        self.assertEqual(paths["cachefile-2"],
                         os.path.abspath(os.path.join(content_cache_dir, "d1", "cachefile-2")))

    def test_symlinked_directory_is_not_descended(self):
        content_cache_dir = os.path.join(self.tmp.name, "content_cache")
        real_dir = os.path.join(self.tmp.name, "real")
        os.makedirs(real_dir)
        with open(os.path.join(real_dir, "hidden-file"), "wb") as hidden_file:
            hidden_file.write(b"x")
        os.makedirs(content_cache_dir, exist_ok=True)
        try:
            os.symlink(real_dir, os.path.join(content_cache_dir, "link"))
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are not supported on this platform")
        paths = get_content_caches_paths(content_cache_dir)
        self.assertNotIn("hidden-file", paths)
        self.assertIn("link", paths)


class TestProfileMetadataGranularLoading(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.profile_path = os.path.join(self.tmp.name, ACCOUNT_ID_1)
        os.makedirs(self.profile_path, exist_ok=True)

    def __write_partial_db(self):
        db = sqlite3.connect(os.path.join(self.profile_path, "metadata_sqlite_db"))
        db.executescript(ITEMS_DDL)
        db.execute(
            "INSERT INTO items (stable_id, id, proto, trashed, is_owner, mime_type, is_folder, modified_date, "
            "shared_with_me_date, viewed_by_me_date, file_size, is_tombstone, local_title, subscribed, "
            "team_drive_stable_id, local_title_tokenized) "
            "VALUES (1, 'u', NULL, 0, 1, 'application/vnd.google-apps.folder', 1, 0, 0, 0, 0, 0, 'Root', 1, NULL, NULL)"
        )
        db.execute("INSERT INTO stable_parents (item_stable_id, parent_stable_id, local_title_hash) VALUES (1, 1, 0)")
        db.commit()
        db.close()
        db = sqlite3.connect(os.path.join(self.profile_path, "metadata_sqlite_db"))
        db.execute("DROP TABLE item_properties")
        db.execute("DROP TABLE shortcut_details")
        db.commit()
        db.close()

    def test_failing_tables_are_reported_and_others_still_load(self):
        self.__write_partial_db()
        metadata = ProfileMetadata(self.profile_path)
        self.assertEqual(set(metadata.get_load_errors()),
                         {"item_properties", "shortcut_details", "shared_with_me"})
        self.assertEqual(metadata.get_item_info(1)[3], "Root")
        self.assertEqual(metadata.get_parent_relationships(), [(1, 1)])

    def test_missing_database_is_reported(self):
        metadata = ProfileMetadata(self.profile_path)
        self.assertEqual(metadata.get_load_errors(), ["metadata_sqlite_db"])
        self.assertEqual(metadata.get_parent_relationships(), [])
        self.assertEqual(metadata.get_item_info(1), ())


class TestMetadataLoadFailureSurfacing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.fixture = build_logged_in_fixture(self.tmp.name)
        os.remove(os.path.join(self.fixture.profile_path(), "metadata_sqlite_db"))

    def test_console_warning_is_printed_for_logged_in_account(self):
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            investigation = Investigation(self.fixture.drivefs_path)
        account = investigation.get_accounts()[0]
        self.assertEqual(account.get_metadata_load_errors(), ["metadata_sqlite_db"])
        self.assertIsNone(account.get_synced_files_tree())
        self.assertIn(f"Failed to fully load metadata for account {ACCOUNT_ID_1}: metadata_sqlite_db",
                      captured.getvalue())

    def test_html_report_contains_visible_warning(self):
        captured = io.StringIO()
        with contextlib.redirect_stdout(captured):
            investigation = Investigation(self.fixture.drivefs_path)
            output_file = os.path.join(self.tmp.name, "html_report.html")
            generate_html_report(investigation, output_file)
        with open(output_file, encoding="utf-8") as report_file:
            report = report_file.read()
        self.assertIn("Synced files metadata could not be fully loaded for this account", report)
        self.assertIn("Affected tables: metadata_sqlite_db", report)


class TestProtoRelease(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(self.tmp.name)
        self.investigation = Investigation(self.fixture.drivefs_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_file_type_survives_release(self):
        tree = self.investigation.get_accounts()[0].get_synced_files_tree()
        report_file = tree.get_item_by_id(STABLE_REPORT_FILE)
        self.assertIsInstance(report_file, File)
        self.assertEqual(report_file.md5, MD5_B)
        self.assertEqual(report_file.get_file_type(), "docx")
        self.assertEqual(report_file._get_proto_field("45"), "")

    def test_directory_md5_survives_release(self):
        tree = self.investigation.get_accounts()[0].get_synced_files_tree()
        projects_dir = tree.get_item_by_id(300)
        self.assertIsInstance(projects_dir, Directory)
        self.assertEqual(projects_dir.md5, "")
        self.assertEqual(projects_dir._get_proto_field("48"), "")


class TestDecodeUtf8(unittest.TestCase):
    def test_valid_utf8_returns_string(self):
        self.assertEqual(decode_utf8(b"plain text"), "plain text")

    def test_invalid_utf8_is_replaced(self):
        self.assertEqual(decode_utf8(b"\xff\xfe bad"), "\ufffd\ufffd bad")


if __name__ == "__main__":
    unittest.main()
