"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: unit tests for the Investigation/Account classes and the synced files tree building.
"""

import os
import sqlite3
import tempfile
import unittest

from builders import ACCOUNT_ID_1
from builders import ACCOUNT_ID_2
from builders import CACHE_FILE_400
from builders import DISPLAY_NAME_1
from builders import DISPLAY_NAME_2
from builders import EMAIL_1
from builders import EMAIL_2
from builders import FOLDER_MIME
from builders import LAST_PID
from builders import LAST_SYNC_UTC_STR
from builders import MD5_A
from builders import MD5_B
from builders import MD5_C
from builders import MD5_D
from builders import MEDIA_ID
from builders import MEDIA_NAME
from builders import MEDIA_MOUNT_POINT
from builders import MIRROR_MD5_CLOUD
from builders import MIRROR_MD5_LOCAL
from builders import MIRROR_ROOT_PATH
from builders import MIRROR_ROOT_TITLE
from builders import PHOTO_URL_1
from builders import SHORTCUT_MIME
from builders import STABLE_DELETED_FILE
from builders import STABLE_DELETED_FOLDER
from builders import STABLE_MISSING_CHILD
from builders import STABLE_NOTES_FILE
from builders import STABLE_ORPHAN_CHILD
from builders import STABLE_ORPHAN_DIR
from builders import STABLE_PROJECTS_DIR
from builders import STABLE_REPORT_FILE
from builders import STABLE_REPORT_SHORTCUT
from builders import STABLE_ROOT_1
from builders import STABLE_SHARED_FILE
from builders import TITLE_DELETED_FILE
from builders import TITLE_DELETED_FOLDER
from builders import TITLE_ORPHAN_CHILD
from builders import TITLE_ORPHAN_DIR
from builders import TITLE_PROJECTS_DIR
from builders import TITLE_REPORT_FILE
from builders import TITLE_REPORT_SHORTCUT
from builders import TITLE_ROOT_1
from builders import TITLE_SHARED_FILE
from builders import build_empty_fixture
from builders import build_logged_in_fixture
from builders import build_not_logged_in_fixture

from drivefs_sleuth.investigation import Investigation
from drivefs_sleuth.investigation import StorageDestinations
from drivefs_sleuth.synced_files_tree import Directory
from drivefs_sleuth.synced_files_tree import File
from drivefs_sleuth.synced_files_tree import Link
from drivefs_sleuth.synced_files_tree import MirrorItem


class BaseInvestigationTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(self.tmp.name)
        self.investigation = Investigation(self.fixture.drivefs_path)

    def tearDown(self):
        self.tmp.cleanup()


class TestInvestigationGlobals(BaseInvestigationTestCase):
    def test_accounts_discovery(self):
        accounts = self.investigation.get_accounts()
        self.assertEqual(len(accounts), 1)
        account = accounts[0]
        self.assertEqual(account.get_account_id(), ACCOUNT_ID_1)
        self.assertEqual(account.get_account_email(), EMAIL_1)
        self.assertTrue(account.is_logged_in())
        self.assertEqual(account.get_name(), DISPLAY_NAME_1)
        self.assertEqual(account.get_photo_url(), PHOTO_URL_1)
        self.assertEqual(account.get_profile_path(), os.path.join(self.fixture.drivefs_path, ACCOUNT_ID_1))

    def test_last_sync_date(self):
        self.assertEqual(str(self.investigation.get_last_sync_date()), LAST_SYNC_UTC_STR)

    def test_max_root_ids_and_pid(self):
        self.assertEqual(self.investigation.get_max_root_ids(), 1)
        self.assertEqual(self.investigation.get_last_pid(), LAST_PID)

    def test_connected_devices(self):
        devices = self.investigation.get_connected_devices()
        self.assertEqual(len(devices), 1)
        device = devices[0]
        self.assertEqual(device["media_id"], MEDIA_ID)
        self.assertEqual(device["name"], MEDIA_NAME)
        self.assertEqual(device["last_mount_point"], MEDIA_MOUNT_POINT)
        self.assertEqual(device["capacity"], 500.0)
        self.assertEqual(device["ignore"], 0)

    def test_mirroring_roots_not_modified(self):
        self.assertFalse(self.investigation.is_mirroring_roots_modified())

    def test_mirroring_roots(self):
        account = self.investigation.get_accounts()[0]
        roots = account.get_mirroring_roots()
        self.assertEqual(len(roots), 1)
        root = roots[0]
        self.assertEqual(root["root_id"], 1)
        self.assertEqual(root["media_id"], MEDIA_ID)
        self.assertEqual(root["title"], MIRROR_ROOT_TITLE)
        self.assertEqual(root["root_path"], MIRROR_ROOT_PATH)
        self.assertEqual(root["sync_type"], 1)
        self.assertEqual(root["last_seen_absolute_path"], MIRROR_ROOT_PATH)
        self.assertEqual(root["destination"], StorageDestinations.DRIVE.value)

    def test_photos_mirroring_root_and_modified_flag(self):
        db = sqlite3.connect(os.path.join(self.fixture.drivefs_path, "root_preference_sqlite.db"))
        db.execute(
            "INSERT INTO roots (root_id, metadata, media_id, title, root_path, account_token, sync_type, "
            "destination, medium, state, one_shot, is_my_drive, doc_id, last_seen_absolute_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (2, None, MEDIA_ID, "Photos Mirror", "C:\\PhotosMirror", ACCOUNT_ID_1, 1, 2, 1, 1, 0, 0, "root-2",
             "C:\\PhotosMirror"),
        )
        db.commit()
        db.close()

        investigation = Investigation(self.fixture.drivefs_path)
        self.assertTrue(investigation.is_mirroring_roots_modified())
        roots = investigation.get_accounts()[0].get_mirroring_roots()
        self.assertEqual(len(roots), 2)
        destinations = {root["destination"] for root in roots}
        self.assertEqual(
            destinations,
            {StorageDestinations.DRIVE.value, StorageDestinations.PHOTOS.value},
        )


class TestSyncedFilesTree(BaseInvestigationTestCase):
    def setUp(self):
        super().setUp()
        account = self.investigation.get_accounts()[0]
        self.tree = account.get_synced_files_tree()
        self.rows = list(self.tree.generate_synced_files_tree_dicts())

    def test_root_directory(self):
        root = self.tree.get_root()
        self.assertIsInstance(root, Directory)
        self.assertEqual(root.get_stable_id(), STABLE_ROOT_1)
        self.assertEqual(root.local_title, TITLE_ROOT_1)
        self.assertEqual(root.tree_path, TITLE_ROOT_1)
        self.assertEqual(root.mime_type, FOLDER_MIME)

    def test_tree_paths_use_windows_backslash_separators(self):
        paths = {row["stable_id"]: row["tree_path"] for row in self.rows}
        self.assertEqual(paths[STABLE_REPORT_FILE], f"{TITLE_ROOT_1}\\{TITLE_REPORT_FILE}")
        self.assertEqual(paths[STABLE_PROJECTS_DIR], f"{TITLE_ROOT_1}\\{TITLE_PROJECTS_DIR}")
        self.assertEqual(
            paths[STABLE_NOTES_FILE],
            f"{TITLE_ROOT_1}\\{TITLE_PROJECTS_DIR}\\notes.txt",
        )
        self.assertEqual(paths[STABLE_REPORT_SHORTCUT], f"{TITLE_ROOT_1}\\{TITLE_REPORT_SHORTCUT}")
        self.assertEqual(paths[STABLE_ORPHAN_CHILD], f"{TITLE_ORPHAN_DIR}\\orphan_child.txt")
        self.assertEqual(paths[STABLE_SHARED_FILE], f"Shared with me\\SharedDoc.pdf")

    def test_file_fields(self):
        report_file = self.tree.get_item_by_id(STABLE_REPORT_FILE)
        self.assertIsInstance(report_file, File)
        self.assertEqual(report_file.local_title, TITLE_REPORT_FILE)
        self.assertEqual(report_file.md5, MD5_B)
        self.assertEqual(report_file.get_file_size_mb(), 0.12)
        self.assertEqual(str(report_file.get_modified_date_utc()), LAST_SYNC_UTC_STR)
        self.assertEqual(report_file.get_file_type(), "docx")

    def test_shortcut_becomes_link_to_target_file(self):
        link = self.tree.get_item_by_id(STABLE_REPORT_SHORTCUT)
        self.assertIsInstance(link, Link)
        self.assertEqual(link.local_title, TITLE_REPORT_SHORTCUT)
        self.assertEqual(link.mime_type, SHORTCUT_MIME)
        target = link.get_target_item()
        self.assertIsInstance(target, File)
        self.assertEqual(target.get_stable_id(), STABLE_REPORT_FILE)
        self.assertEqual(link.tree_path, f"{TITLE_ROOT_1}\\{TITLE_REPORT_SHORTCUT}")

    def test_nested_folder_contains_child(self):
        projects_dir = self.tree.get_item_by_id(STABLE_PROJECTS_DIR)
        self.assertIsInstance(projects_dir, Directory)
        children = projects_dir.get_sub_items()
        self.assertEqual([child.get_stable_id() for child in children], [STABLE_NOTES_FILE])
        notes_file = children[0]
        self.assertEqual(notes_file.md5, MD5_A)
        self.assertEqual(notes_file.tree_path, f"{TITLE_ROOT_1}\\{TITLE_PROJECTS_DIR}\\notes.txt")

    def test_content_cache_and_thumbnail_paths(self):
        notes_file = self.tree.get_item_by_id(STABLE_NOTES_FILE)
        self.assertEqual(
            notes_file.get_content_cache_path(),
            self.fixture.cache_file_path_400,
        )
        self.assertEqual(
            notes_file.get_thumbnail_path(),
            self.fixture.thumbnail_file_path_400,
        )

    def test_orphan_items(self):
        orphans = self.tree.get_orphan_items()
        self.assertEqual(len(orphans), 1)
        orphan_dir = orphans[0]
        self.assertIsInstance(orphan_dir, Directory)
        self.assertEqual(orphan_dir.get_stable_id(), STABLE_ORPHAN_DIR)
        self.assertEqual(orphan_dir.local_title, TITLE_ORPHAN_DIR)
        orphan_children = orphan_dir.get_sub_items()
        self.assertEqual([child.get_stable_id() for child in orphan_children], [STABLE_ORPHAN_CHILD])
        self.assertEqual(orphan_children[0].local_title, TITLE_ORPHAN_CHILD)
        self.assertEqual(orphan_children[0].tree_path, f"{TITLE_ORPHAN_DIR}\\{TITLE_ORPHAN_CHILD}")

    def test_shared_with_me_items(self):
        shared_items = self.tree.get_shared_with_me_items()
        self.assertEqual(len(shared_items), 1)
        shared_file = shared_items[0]
        self.assertIsInstance(shared_file, File)
        self.assertEqual(shared_file.get_stable_id(), STABLE_SHARED_FILE)
        self.assertEqual(shared_file.local_title, TITLE_SHARED_FILE)
        self.assertEqual(shared_file.md5, MD5_D)
        self.assertEqual(shared_file.tree_path, f"Shared with me\\{TITLE_SHARED_FILE}")

    def test_deleted_items(self):
        deleted_ids = [item.get_stable_id() for item in self.tree.get_deleted_items()]
        self.assertEqual(deleted_ids, [STABLE_MISSING_CHILD])

    def test_recovered_deleted_items(self):
        recovered = {item.get_stable_id(): item for item in self.tree.get_recovered_deleted_items()}
        self.assertEqual(set(recovered.keys()), {STABLE_DELETED_FILE, STABLE_DELETED_FOLDER})
        recovered_file = recovered[STABLE_DELETED_FILE]
        self.assertIsInstance(recovered_file, File)
        self.assertEqual(recovered_file.local_title, TITLE_DELETED_FILE)
        self.assertEqual(recovered_file.md5, MD5_C)
        self.assertEqual(recovered_file.tree_path, TITLE_DELETED_FILE)
        recovered_folder = recovered[STABLE_DELETED_FOLDER]
        self.assertIsInstance(recovered_folder, Directory)
        self.assertEqual(recovered_folder.local_title, TITLE_DELETED_FOLDER)

    def test_recoverable_from_cache_and_thumbnails(self):
        recoverable = [item.get_stable_id() for item in self.tree.get_recoverable_items_from_cache()]
        self.assertEqual(recoverable, [STABLE_NOTES_FILE])
        thumbnails = [item.get_stable_id() for item in self.tree.get_thumbnail_items()]
        self.assertEqual(thumbnails, [STABLE_NOTES_FILE])

    def test_mirrored_items(self):
        mirrored = self.tree.get_mirrored_items()
        self.assertEqual(len(mirrored), 1)
        item = mirrored[0]
        self.assertIsInstance(item, MirrorItem)
        self.assertEqual(item.local_stable_id, 1)
        self.assertEqual(item.stable_id, 888)
        self.assertEqual(item.volume, "C:")
        self.assertEqual(item.parent, STABLE_ROOT_1)
        self.assertEqual(item.local_filename, "local_doc.docx")
        self.assertEqual(item.cloud_filename, "cloud_doc.docx")
        self.assertEqual(item.local_md5, MIRROR_MD5_LOCAL)
        self.assertEqual(item.cloud_md5, MIRROR_MD5_CLOUD)
        self.assertEqual(str(item.get_local_mtime_utc()), LAST_SYNC_UTC_STR)
        self.assertEqual(str(item.get_cloud_mtime_utc()), LAST_SYNC_UTC_STR)


class TestTwoAccounts(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(self.tmp.name, two_accounts=True)
        self.investigation = Investigation(self.fixture.drivefs_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_both_accounts_discovered_and_sorted(self):
        accounts = self.investigation.get_accounts()
        self.assertEqual([account.get_account_id() for account in accounts], [ACCOUNT_ID_1, ACCOUNT_ID_2])
        self.assertEqual([account.get_account_email() for account in accounts], [EMAIL_1, EMAIL_2])
        self.assertEqual([account.get_name() for account in accounts], [DISPLAY_NAME_1, DISPLAY_NAME_2])
        self.assertTrue(all(account.is_logged_in() for account in accounts))

    def test_second_account_tree(self):
        second_account = self.investigation.get_accounts()[1]
        tree = second_account.get_synced_files_tree()
        rows = list(tree.generate_synced_files_tree_dicts())
        self.assertEqual([row["local_title"] for row in rows], ["Other Drive", "SecondFile.txt"])


class TestNotLoggedIn(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_not_logged_in_fixture(self.tmp.name)
        self.investigation = Investigation(self.fixture.drivefs_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_account_is_discovered_but_logged_out(self):
        accounts = self.investigation.get_accounts()
        self.assertEqual(len(accounts), 1)
        account = accounts[0]
        self.assertEqual(account.get_account_id(), ACCOUNT_ID_1)
        self.assertEqual(account.get_account_email(), EMAIL_1)
        self.assertFalse(account.is_logged_in())
        self.assertIsNone(account.get_synced_files_tree())


class TestEmptyInstallation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_empty_fixture(self.tmp.name)
        self.investigation = Investigation(self.fixture.drivefs_path)

    def tearDown(self):
        self.tmp.cleanup()

    def test_no_accounts(self):
        self.assertEqual(self.investigation.get_accounts(), [])

    def test_no_last_sync(self):
        self.assertIsNone(self.investigation.get_last_sync_date())

    def test_no_max_root_ids(self):
        self.assertIsNone(self.investigation.get_max_root_ids())
        self.assertFalse(self.investigation.is_mirroring_roots_modified())


if __name__ == "__main__":
    unittest.main()
