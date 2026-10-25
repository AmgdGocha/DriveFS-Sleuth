"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: tests for deleted files and orphan files (inactive-content-entries) model.
"""

import csv
import hashlib
import json
import os
import sqlite3
import tempfile
import unittest

from builders import LAST_SYNC_MS
from builders import MD5_A
from builders import MODERN_ACCOUNT_ID
from builders import MODERN_EMAIL
from builders import MODERN_INACTIVE_CONTENT
from builders import MODERN_INACTIVE_KEY
from builders import MODERN_ORPHAN_CONTENT
from builders import MODERN_ORPHAN_KEY
from builders import MODERN_STALE_CONTENT
from builders import MODERN_STALE_KEY
from builders import MODERN_UNREACHABLE_CONTENT
from builders import MODERN_UNREACHABLE_KEY
from builders import MODERN_ZOMBIE_CONTENT
from builders import MODERN_ZOMBIE_ITEM
from builders import MODERN_ZOMBIE_KEY
from builders import STABLE_MODERN_FILE
from builders import STABLE_MODERN_ORPHAN_ITEM
from builders import STABLE_MODERN_STALE
from builders import TITLE_MODERN_FILE
from builders import TITLE_MODERN_ORPHAN_ITEM
from builders import TITLE_MODERN_STALE
from builders import build_modern_layout_fixture

from drivefs_sleuth.investigation import Investigation
from drivefs_sleuth.tasks import generate_csv_report
from drivefs_sleuth.tasks import generate_html_report
from drivefs_sleuth.utils import ProfileMetadata
from drivefs_sleuth.utils import compute_md5
from drivefs_sleuth.utils import detect_file_type
from drivefs_sleuth.utils import get_alternate_data_streams


class BaseDeletedOrphanTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_modern_layout_fixture(self.tmp.name)
        self.investigation = Investigation(self.fixture.drivefs_path)
        self.account = self.investigation.get_accounts()[0]
        self.tree = self.account.get_synced_files_tree()
        self.output_dir = os.path.join(self.tmp.name, "out")
        os.makedirs(self.output_dir)

    def tearDown(self):
        self.tmp.cleanup()


class TestProfileMetadataInactiveEntries(BaseDeletedOrphanTestCase):
    def test_inactive_content_entries_are_decoded_at_load(self):
        metadata = ProfileMetadata(self.account.get_profile_path())
        entries = metadata.get_all_inactive_content_entries()
        decoded = {}
        for item_stable_id, item_entries in entries:
            decoded.setdefault(str(item_stable_id), []).extend(item_entries)
        self.assertIn(str(STABLE_MODERN_FILE), decoded)
        correlated = decoded[str(STABLE_MODERN_FILE)]
        self.assertEqual(len(correlated), 1)
        self.assertEqual(correlated[0]["cache_key"], str(MODERN_INACTIVE_KEY))
        self.assertEqual(correlated[0]["content_blob_id"], "blob-7777")
        self.assertEqual(correlated[0]["content_id"], "content-7777")
        self.assertEqual(correlated[0]["size"], len(MODERN_INACTIVE_CONTENT))
        self.assertIn(str(MODERN_ZOMBIE_ITEM), decoded)
        self.assertEqual(
            decoded[str(MODERN_ZOMBIE_ITEM)][0]["cache_key"], str(MODERN_ZOMBIE_KEY)
        )
        self.assertIn(str(STABLE_MODERN_ORPHAN_ITEM), decoded)
        self.assertEqual(
            decoded[str(STABLE_MODERN_ORPHAN_ITEM)][0]["cache_key"],
            str(MODERN_UNREACHABLE_KEY),
        )
        self.assertIn(str(STABLE_MODERN_STALE), decoded)
        self.assertEqual(
            decoded[str(STABLE_MODERN_STALE)][0]["cache_key"], str(MODERN_STALE_KEY)
        )

    def test_item_properties_expose_decoded_json_string(self):
        metadata = ProfileMetadata(self.account.get_profile_path())
        properties = metadata.get_item_properties(STABLE_MODERN_FILE)
        raw = properties["inactive-content-entries"]
        self.assertIsInstance(raw, str)
        parsed = json.loads(raw)
        self.assertEqual(parsed[0]["cache_key"], str(MODERN_INACTIVE_KEY))
        self.assertEqual(parsed[0]["size"], len(MODERN_INACTIVE_CONTENT))

    def test_cache_key_sets(self):
        metadata = ProfileMetadata(self.account.get_profile_path())
        self.assertEqual(
            metadata.get_active_content_cache_keys(), {"206", "19307"}
        )
        self.assertEqual(
            metadata.get_inactive_content_cache_keys(),
            {
                str(MODERN_INACTIVE_KEY),
                str(MODERN_ZOMBIE_KEY),
                str(MODERN_UNREACHABLE_KEY),
                str(MODERN_STALE_KEY),
            },
        )

    def test_malformed_inactive_row_is_skipped(self):
        profile_path = self.account.get_profile_path()
        db = sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db"))
        db.execute(
            "INSERT INTO item_properties (item_stable_id, key, value, value_type) VALUES (?, ?, ?, ?)",
            (MODERN_ZOMBIE_ITEM + 1, "inactive-content-entries", b"\xff\xfe\x00garbage", 4),
        )
        db.commit()
        db.close()
        metadata = ProfileMetadata(profile_path)
        self.assertEqual(len(metadata.get_all_inactive_content_entries()), 4)


class TestDeletedFilesModel(BaseDeletedOrphanTestCase):
    def test_deleted_files_contain_zombie_and_metadata_less_entries(self):
        deleted_files = self.tree.get_deleted_files()
        self.assertEqual(len(deleted_files), 2)

        zombie = next(
            file_item
            for file_item in deleted_files
            if file_item.get_stable_id() == MODERN_ZOMBIE_ITEM
        )
        self.assertEqual(zombie.local_title, f"{MODERN_ZOMBIE_KEY}.png")
        self.assertEqual(zombie.tree_path, f"Unknown - {MODERN_ZOMBIE_KEY}.png")
        self.assertEqual(zombie.get_content_cache_path(), self.fixture.zombie_cache_path)
        self.assertEqual(
            zombie.md5, hashlib.md5(MODERN_ZOMBIE_CONTENT).hexdigest()
        )
        self.assertEqual(zombie.detected_type, "png")
        self.assertEqual(zombie.detected_mime, "image/png")
        self.assertEqual(zombie.file_size, len(MODERN_ZOMBIE_CONTENT))
        zombie_json = json.loads(zombie.properties["inactive-content-entries"])
        self.assertEqual(zombie_json[0]["cache_key"], str(MODERN_ZOMBIE_KEY))

        metadata_less = next(
            file_item
            for file_item in deleted_files
            if file_item.get_stable_id() == f"orphan-{MODERN_ORPHAN_KEY}"
        )
        self.assertEqual(metadata_less.local_title, f"{MODERN_ORPHAN_KEY}.bin.png")
        self.assertEqual(
            metadata_less.tree_path, f"Unknown - {MODERN_ORPHAN_KEY}.bin.png"
        )
        self.assertEqual(
            metadata_less.get_content_cache_path(), self.fixture.orphan_cache_path
        )
        self.assertEqual(
            metadata_less.md5, hashlib.md5(MODERN_ORPHAN_CONTENT).hexdigest()
        )
        self.assertEqual(metadata_less.detected_type, "png")
        self.assertEqual(metadata_less.file_size, len(MODERN_ORPHAN_CONTENT))

    def test_reachable_inactive_entries_are_not_deleted_or_orphan(self):
        deleted_paths = [
            file_item.get_content_cache_path()
            for file_item in self.tree.get_deleted_files()
        ]
        orphan_paths = [
            file_item.get_content_cache_path()
            for file_item in self.tree.get_orphan_cache_files()
        ]
        self.assertNotIn(self.fixture.inactive_cache_path, deleted_paths)
        self.assertNotIn(self.fixture.inactive_cache_path, orphan_paths)
        self.assertNotIn(self.fixture.stale_cache_path, deleted_paths)
        self.assertNotIn(self.fixture.stale_cache_path, orphan_paths)

    def test_empty_cache_file_is_not_listed_anywhere(self):
        deleted_stems = [
            file_item.get_stable_id() for file_item in self.tree.get_deleted_files()
        ]
        orphan_stems = [
            file_item.get_stable_id() for file_item in self.tree.get_orphan_cache_files()
        ]
        self.assertNotIn("orphan-6666", deleted_stems)
        self.assertNotIn("orphan-6666", orphan_stems)

    def test_deleted_files_are_searchable_by_name(self):
        results = self.tree.search(
            [{"TYPE": "filename", "TARGET": ["8888.png"], "CONTAINS": False, "LIST_SUB_ITEMS": False}]
        )
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].get_stable_id(), MODERN_ZOMBIE_ITEM)


class TestOrphanCacheFilesModel(BaseDeletedOrphanTestCase):
    def test_unreachable_item_stale_version_is_an_orphan_with_owner_info(self):
        orphan_files = self.tree.get_orphan_cache_files()
        self.assertEqual(len(orphan_files), 1)
        orphan_file = orphan_files[0]
        self.assertEqual(orphan_file.get_stable_id(), f"orphan-{MODERN_UNREACHABLE_KEY}")
        self.assertEqual(orphan_file.local_title, TITLE_MODERN_ORPHAN_ITEM)
        self.assertEqual(
            orphan_file.tree_path, f"Orphan Files\\{TITLE_MODERN_ORPHAN_ITEM}"
        )
        self.assertEqual(
            orphan_file.get_content_cache_path(), self.fixture.unreachable_cache_path
        )
        self.assertEqual(
            orphan_file.md5, hashlib.md5(MODERN_UNREACHABLE_CONTENT).hexdigest()
        )
        self.assertEqual(orphan_file.detected_type, "png")
        self.assertEqual(orphan_file.detected_mime, "image/png")
        self.assertEqual(orphan_file.file_size, len(MODERN_UNREACHABLE_CONTENT))
        self.assertEqual(orphan_file.modified_date, LAST_SYNC_MS)
        self.assertEqual(orphan_file.trashed, 0)
        parsed = json.loads(orphan_file.properties["inactive-content-entries"])
        self.assertEqual(parsed[0]["cache_key"], str(MODERN_UNREACHABLE_KEY))
        self.assertTrue(orphan_file.cache_mtime)

    def test_orphan_files_root_exists_only_with_orphans(self):
        root = self.tree.get_orphan_files_root()
        self.assertIsNotNone(root)
        self.assertEqual(root.local_title, "Orphan Files")
        self.assertEqual(root.get_stable_id(), "orphan-files-root")
        self.assertEqual(len(root.get_sub_items()), 1)

    def test_deleted_files_are_not_treated_as_orphans(self):
        orphan_paths = [
            file_item.get_content_cache_path()
            for file_item in self.tree.get_orphan_cache_files()
        ]
        self.assertNotIn(self.fixture.orphan_cache_path, orphan_paths)
        self.assertNotIn(self.fixture.zombie_cache_path, orphan_paths)

    def test_orphan_file_is_searchable_by_md5(self):
        orphan_md5 = hashlib.md5(MODERN_UNREACHABLE_CONTENT).hexdigest()
        results = self.tree.search([{"TYPE": "md5", "TARGET": [orphan_md5]}])
        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].get_stable_id(), f"orphan-{MODERN_UNREACHABLE_KEY}"
        )


class TestReachableStaleVersionModel(BaseDeletedOrphanTestCase):
    def test_stale_content_is_attached_to_live_item_without_active_content(self):
        stale_item = self.tree.get_item_by_id(STABLE_MODERN_STALE)
        self.assertIsNotNone(stale_item)
        self.assertEqual(stale_item.get_content_cache_path(), self.fixture.stale_cache_path)
        self.assertIn(
            stale_item, self.tree.get_recoverable_items_from_cache()
        )

    def test_live_item_with_active_content_keeps_its_own_cache(self):
        live_item = self.tree.get_item_by_id(STABLE_MODERN_FILE)
        self.assertEqual(live_item.get_content_cache_path(), self.fixture.single_cache_path)

    def test_orphan_files_root_does_not_contain_reachable_versions(self):
        root = self.tree.get_orphan_files_root()
        titles = [item.local_title for item in root.get_sub_items()]
        self.assertNotIn(TITLE_MODERN_FILE, titles)
        self.assertNotIn(TITLE_MODERN_STALE, titles)


class TestDeletedAndOrphanCsvReport(BaseDeletedOrphanTestCase):
    def test_deleted_and_orphan_csv_is_generated_alongside_main_csv(self):
        output_file = os.path.join(self.output_dir, "csv_report.csv")
        generate_csv_report(self.investigation, output_file)
        deleted_csv = os.path.join(self.output_dir, "deleted_and_orphan_files.csv")
        self.assertTrue(os.path.exists(deleted_csv))
        self.assertTrue(os.path.exists(output_file))

        with open(deleted_csv, newline="", encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertEqual(len(rows), 3, "2 deleted files + 1 orphan file")
        for row in rows:
            self.assertEqual(row["account_id"], MODERN_ACCOUNT_ID)
            self.assertEqual(row["email"], MODERN_EMAIL)
            self.assertEqual(row["type"], "File")

        stable_ids = {row["stable_id"] for row in rows}
        self.assertIn(str(MODERN_ZOMBIE_ITEM), stable_ids)
        self.assertIn(f"orphan-{MODERN_ORPHAN_KEY}", stable_ids)
        self.assertIn(f"orphan-{MODERN_UNREACHABLE_KEY}", stable_ids)

        deleted_row = next(
            row for row in rows if row["stable_id"] == f"orphan-{MODERN_ORPHAN_KEY}"
        )
        self.assertEqual(deleted_row["local_title"], f"{MODERN_ORPHAN_KEY}.bin.png")
        self.assertEqual(deleted_row["detected_type"], "png")
        self.assertEqual(
            deleted_row["md5"], hashlib.md5(MODERN_ORPHAN_CONTENT).hexdigest()
        )
        self.assertEqual(deleted_row["path_in_content_cache"], self.fixture.orphan_cache_path)

        orphan_row = next(
            row for row in rows if row["stable_id"] == f"orphan-{MODERN_UNREACHABLE_KEY}"
        )
        self.assertEqual(orphan_row["local_title"], TITLE_MODERN_ORPHAN_ITEM)
        self.assertEqual(
            orphan_row["tree_path"], f"Orphan Files\\{TITLE_MODERN_ORPHAN_ITEM}"
        )
        self.assertEqual(
            orphan_row["md5"], hashlib.md5(MODERN_UNREACHABLE_CONTENT).hexdigest()
        )

    def test_decoded_inactive_json_survives_csv_round_trip(self):
        output_file = os.path.join(self.output_dir, "csv_report.csv")
        generate_csv_report(self.investigation, output_file)
        deleted_csv = os.path.join(self.output_dir, "deleted_and_orphan_files.csv")
        with open(deleted_csv, newline="", encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))
        orphan_row = next(
            row for row in rows if row["stable_id"] == f"orphan-{MODERN_UNREACHABLE_KEY}"
        )
        parsed = json.loads(orphan_row["inactive-content-entries"])
        self.assertEqual(parsed[0]["cache_key"], str(MODERN_UNREACHABLE_KEY))
        self.assertEqual(parsed[0]["size"], len(MODERN_UNREACHABLE_CONTENT))

    def test_main_csv_excludes_deleted_and_orphan_rows(self):
        output_file = os.path.join(self.output_dir, "csv_report.csv")
        generate_csv_report(self.investigation, output_file)
        with open(output_file, newline="", encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))
        stable_ids = {row["stable_id"] for row in rows}
        self.assertNotIn(f"orphan-{MODERN_ORPHAN_KEY}", stable_ids)
        self.assertNotIn(str(MODERN_ZOMBIE_ITEM), stable_ids)
        self.assertNotIn(f"orphan-{MODERN_UNREACHABLE_KEY}", stable_ids)


class TestHtmlReportSections(BaseDeletedOrphanTestCase):
    def test_html_report_contains_orphan_files_root_and_deleted_files(self):
        output_file = os.path.join(self.output_dir, "html_report.html")
        generate_html_report(self.investigation, output_file)
        with open(output_file, encoding="utf-8") as html_file:
            content = html_file.read()
        self.assertIn("Orphan Files", content)
        self.assertIn(TITLE_MODERN_ORPHAN_ITEM, content)
        self.assertIn("Deleted Items", content)
        self.assertIn(f"{MODERN_ZOMBIE_KEY}.png", content)
        self.assertIn(f"{MODERN_ORPHAN_KEY}.bin.png", content)
        self.assertIn(f"orphan-{MODERN_UNREACHABLE_KEY}", content)
        self.assertIn(f"orphan-{MODERN_ORPHAN_KEY}", content)
        self.assertNotIn(f"orphan-{MODERN_INACTIVE_KEY}", content)


class TestEnrichmentHelpers(unittest.TestCase):
    def test_compute_md5_missing_file_returns_none(self):
        self.assertIsNone(compute_md5(os.path.join(tempfile.gettempdir(), "no-such-file-xyz")))

    def test_detect_file_type_png(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "file.bin")
            with open(path, "wb") as handle:
                handle.write(MODERN_ORPHAN_CONTENT)
            detected = detect_file_type(path)
            self.assertEqual(detected["extension"], "png")
            self.assertEqual(detected["mime_type"], "image/png")

    def test_detect_file_type_unknown_returns_empty(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "file.bin")
            with open(path, "wb") as handle:
                handle.write(b"\x00\x01\x02\x03\x00\x00\x00\x00")
            detected = detect_file_type(path)
            self.assertIsInstance(detected, dict)

    def test_alternate_data_streams_returns_dict(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = os.path.join(tmp_dir, "file.bin")
            with open(path, "wb") as handle:
                handle.write(MODERN_ORPHAN_CONTENT)
            self.assertIsInstance(get_alternate_data_streams(path), dict)


if __name__ == "__main__":
    unittest.main()
