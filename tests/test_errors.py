"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: tests for DriveFS Sleuth error handling; verifies corrupt or invalid input never
produces an unhandled exception. PII-free, synthetic fixtures only.
"""

import contextlib
import csv
import io
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

from builders import ACCOUNT_ID_1
from builders import ACCOUNT_ID_2
from builders import DELETED_ITEM_TYPEDEF
from builders import DOCX_MIME
from builders import ITEMS_DDL
from builders import LAST_SYNC_MS
from builders import MD5_C
from builders import STABLE_PROJECTS_DIR
from builders import STABLE_ROOT_1
from builders import TITLE_NOTES_FILE
from builders import TXT_MIME
from builders import _encode
from builders import build_logged_in_fixture
from builders import url_id

from drivefs_sleuth.executor import execute
from drivefs_sleuth.investigation import Investigation
from drivefs_sleuth.synced_files_tree import File
from drivefs_sleuth.tasks import generate_csv_report
from drivefs_sleuth.tasks import recover_from_content_cache
from drivefs_sleuth.utils import copy_file
from drivefs_sleuth.utils import get_deleted_items
from drivefs_sleuth.utils import get_item_info
from drivefs_sleuth.utils import get_item_properties
from drivefs_sleuth.utils import get_parent_relationships

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DEV_RUNNER = os.path.join(REPO_ROOT, "drivefs_sleuth.py")


def run_cli(arguments):
    return subprocess.run(
        [sys.executable, DEV_RUNNER] + arguments,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


def _corrupt_file(file_path):
    with open(file_path, "wb") as corrupt_file:
        corrupt_file.write(b"this is not a sqlite database, just garbage bytes")


def _insert_deleted_item(profile_path, stable_id, proto):
    db = sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db"))
    db.execute(
        "INSERT INTO deleted_items (stable_id, proto) VALUES (?, ?)",
        (stable_id, proto),
    )
    db.commit()
    db.close()


def _encode_raw_fields(fields):
    def _varint(value):
        result = bytearray()
        while value > 0x7F:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value)
        return bytes(result)

    output = b""
    for number, payload in fields:
        output += _varint((number << 3) | 2) + _varint(len(payload)) + payload
    return output


class CliErrorHandlingTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(os.path.join(self.tmp.name, "drivefs"))
        self.addCleanup(self.tmp.cleanup)

    def test_nonexistent_path_exits_2(self):
        result = run_cli(
            [os.path.join(self.tmp.name, "does_not_exist"), "-o", self.tmp.name, "--csv"]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("doesn't exist", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_path_pointing_to_file_exits_2(self):
        file_path = os.path.join(self.tmp.name, "afile.txt")
        with open(file_path, "w", encoding="utf-8") as file_handle:
            file_handle.write("x")
        result = run_cli([file_path, "-o", self.tmp.name, "--csv"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a directory", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_invalid_regex_exits_2(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.tmp.name, "--csv", "--regex", "("]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Invalid regular expression", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_missing_search_csv_exits_2(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.tmp.name, "--csv", "--search-csv",
             os.path.join(self.tmp.name, "missing.csv")]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("couldn't read the searching criteria CSV", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_search_csv_pointing_to_directory_exits_2(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.tmp.name, "--csv", "--search-csv", self.tmp.name]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("couldn't read the searching criteria CSV", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_search_csv_with_wrong_headers_exits_2(self):
        csv_path = os.path.join(self.tmp.name, "bad_headers.csv")
        with open(csv_path, "w", encoding="utf-8") as csv_file:
            csv_file.write("FOO,BAR\n1,2\n")
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.tmp.name, "--csv", "--search-csv", csv_path]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("TYPE,TARGET,CONTAINS,LIST_SUB_ITEMS", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_corrupt_metadata_db_completes_without_traceback(self):
        _corrupt_file(os.path.join(self.fixture.profile_path(), "metadata_sqlite_db"))
        result = run_cli([self.fixture.drivefs_path, "-o", self.tmp.name, "--csv", "--html"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("completed the process", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)
        with open(os.path.join(self.tmp.name, "csv_report.csv"), encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertEqual(len(rows), 0)

    def test_corrupt_root_dbs_complete_without_traceback(self):
        _corrupt_file(os.path.join(self.fixture.drivefs_path, "experiments.db"))
        _corrupt_file(os.path.join(self.fixture.drivefs_path, "root_preference_sqlite.db"))
        result = run_cli([self.fixture.drivefs_path, "-o", self.tmp.name, "--csv"])
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("completed the process", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)

    def test_recovery_with_deleted_cache_file_completes(self):
        os.remove(self.fixture.cache_file_path_400)
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.tmp.name, "--csv", "--recover-from-cache"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("completed the process", result.stdout)
        self.assertNotIn("Traceback", result.stdout + result.stderr)


class ExecutorGlobalHandlerTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.input_dir = os.path.join(self.tmp.name, "input")
        os.makedirs(self.input_dir)
        self.addCleanup(self.tmp.cleanup)

    def test_runtime_error_prints_friendly_message_and_exits_1(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with mock.patch.object(sys, "argv", ["drivefs-sleuth", self.input_dir, "-o",
                                                 self.tmp.name, "--csv"]):
                with mock.patch(
                    "drivefs_sleuth.executor.Investigation",
                    side_effect=RuntimeError("boom"),
                ):
                    with self.assertRaises(SystemExit) as raised:
                        execute()
        self.assertEqual(raised.exception.code, 1)
        self.assertIn("DriveFS Sleuth: error: boom", output.getvalue())
        self.assertNotIn("Traceback", output.getvalue())

    def test_debug_flag_reraises_the_exception(self):
        with mock.patch.object(sys, "argv", ["drivefs-sleuth", self.input_dir, "-o",
                                             self.tmp.name, "--csv", "--debug"]):
            with mock.patch(
                "drivefs_sleuth.executor.Investigation",
                side_effect=RuntimeError("boom"),
            ):
                with contextlib.redirect_stdout(io.StringIO()):
                    with self.assertRaises(RuntimeError):
                        execute()


class CorruptArtifactsToleranceTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(os.path.join(self.tmp.name, "drivefs"))
        self.addCleanup(self.tmp.cleanup)

    def test_missing_database_files_are_not_created(self):
        profile_path = os.path.join(self.tmp.name, "drivefs", ACCOUNT_ID_2)
        os.makedirs(profile_path, exist_ok=True)
        metadata_db_path = os.path.join(profile_path, "metadata_sqlite_db")
        self.assertEqual(get_parent_relationships(profile_path), [])
        self.assertEqual(get_item_info(profile_path, 1), ())
        self.assertEqual(get_item_properties(profile_path, 1), {})
        self.assertEqual(get_deleted_items(profile_path), [])
        self.assertFalse(os.path.exists(metadata_db_path))

    def test_wal_database_without_shm_is_read_without_touching_evidence(self):
        live_dir = os.path.join(self.tmp.name, "live")
        os.makedirs(live_dir)
        live_db_path = os.path.join(live_dir, "metadata_sqlite_db")
        db = sqlite3.connect(live_db_path)
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("PRAGMA wal_autocheckpoint=0")
        db.executescript(ITEMS_DDL)
        db.execute(
            "INSERT INTO items (stable_id, id, proto, trashed, is_owner, mime_type, is_folder, "
            "modified_date, shared_with_me_date, viewed_by_me_date, file_size, is_tombstone, "
            "local_title, subscribed) VALUES (?, ?, NULL, 0, 1, ?, 0, ?, 0, ?, 100, 0, ?, 1)",
            (901, "url-901", TXT_MIME, LAST_SYNC_MS, LAST_SYNC_MS, "WalOnly.txt"),
        )
        db.commit()
        triage_dir = os.path.join(self.tmp.name, "triage")
        os.makedirs(triage_dir)
        shutil.copy2(live_db_path, os.path.join(triage_dir, "metadata_sqlite_db"))
        shutil.copy2(live_db_path + "-wal", os.path.join(triage_dir, "metadata_sqlite_db-wal"))
        db.close()
        row = get_item_info(triage_dir, 901)
        self.assertEqual(row[3], "WalOnly.txt")
        self.assertFalse(os.path.exists(os.path.join(triage_dir, "metadata_sqlite_db-shm")))

    def test_corrupt_metadata_db_returns_empty_defaults(self):
        _corrupt_file(os.path.join(self.fixture.profile_path(), "metadata_sqlite_db"))
        self.assertEqual(get_parent_relationships(self.fixture.profile_path()), [])
        self.assertEqual(get_item_info(self.fixture.profile_path(), 1), ())
        self.assertEqual(get_item_properties(self.fixture.profile_path(), 1), {})
        self.assertEqual(get_deleted_items(self.fixture.profile_path()), [])
        with contextlib.redirect_stdout(io.StringIO()):
            investigation = Investigation(self.fixture.drivefs_path)
        self.assertEqual(len(investigation.get_accounts()), 1)
        self.assertIsNone(investigation.get_accounts()[0].get_synced_files_tree())
        self.assertEqual(investigation.get_accounts()[0].get_metadata_load_errors(),
                         ["items", "stable_parents", "item_properties", "shortcut_details",
                          "deleted_items", "shared_with_me"])

    def test_deleted_item_with_missing_mime_field_does_not_crash(self):
        value = {
            "1": url_id(801),
            "3": "No Mime.pdf",
            "5": 1,
            "7": 1,
            "14": 999,
            "48": MD5_C,
        }
        proto = _encode(value, DELETED_ITEM_TYPEDEF)
        _insert_deleted_item(self.fixture.profile_path(), 801, proto)
        investigation = Investigation(self.fixture.drivefs_path)
        tree = investigation.get_accounts()[0].get_synced_files_tree()
        rows = list(tree.generate_synced_files_tree_dicts())
        self.assertFalse(any(row.get("stable_id") == 801 for row in rows))
        recovered = tree.get_recovered_deleted_items()
        self.assertTrue(any(item.get_stable_id() == 801 for item in recovered))

    def test_deleted_item_with_non_utf8_title_is_recoverable_and_searchable(self):
        proto = _encode_raw_fields(
            [(1, url_id(802).encode("utf-8")), (3, b"\xff\xfeBroken.txt"), (4, b"text/plain")]
        )
        _insert_deleted_item(self.fixture.profile_path(), 802, proto)
        investigation = Investigation(self.fixture.drivefs_path)
        tree = investigation.get_accounts()[0].get_synced_files_tree()
        recovered = tree.get_recovered_deleted_items()
        item = next(rec for rec in recovered if rec.get_stable_id() == 802)
        self.assertIn("Broken.txt", item.local_title)
        results = tree.search(
            [{"TYPE": "filename", "TARGET": ["Broken"], "CONTAINS": True, "LIST_SUB_ITEMS": False}]
        )
        self.assertTrue(any(result.get_stable_id() == 802 for result in results))

    def test_deleted_item_with_malformed_field_55_does_not_crash(self):
        typedef = dict(DELETED_ITEM_TYPEDEF)
        typedef["55"] = {
            "type": "message",
            "message_typedef": {"1": {"type": "string"}, "2": {"type": "bytes"}},
        }
        value = {
            "1": url_id(803),
            "3": "Malformed Props.pdf",
            "4": TXT_MIME,
            "5": 1,
            "7": 1,
            "14": 999,
            "48": MD5_C,
            "55": [{"1": "key-without-value"}],
        }
        proto = _encode(value, typedef)
        _insert_deleted_item(self.fixture.profile_path(), 803, proto)
        investigation = Investigation(self.fixture.drivefs_path)
        tree = investigation.get_accounts()[0].get_synced_files_tree()
        recovered = tree.get_recovered_deleted_items()
        item = next(rec for rec in recovered if rec.get_stable_id() == 803)
        self.assertEqual(item.properties, {})

    def test_deleted_item_with_non_dict_target_field_does_not_crash(self):
        typedef = dict(DELETED_ITEM_TYPEDEF)
        typedef["132"] = {"type": "bytes"}
        value = {
            "1": url_id(804),
            "3": "Shortcut",
            "4": "application/vnd.google-apps.shortcut",
            "5": 1,
            "7": 1,
            "132": b"not-a-message",
        }
        proto = _encode(value, typedef)
        _insert_deleted_item(self.fixture.profile_path(), 804, proto)
        investigation = Investigation(self.fixture.drivefs_path)
        tree = investigation.get_accounts()[0].get_synced_files_tree()
        recovered = tree.get_recovered_deleted_items()
        item = next(rec for rec in recovered if rec.get_stable_id() == 804)
        self.assertEqual(item.get_target_item().get_stable_id(), "-1")

    def test_stable_parents_cycle_is_detected_and_broken(self):
        profile_path = self.fixture.profile_path()
        db = sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db"))
        db.execute(
            "INSERT INTO stable_parents (item_stable_id, parent_stable_id, local_title_hash) "
            "VALUES (?, ?, ?)",
            (STABLE_ROOT_1, STABLE_PROJECTS_DIR, 0),
        )
        db.commit()
        db.close()
        investigation = Investigation(self.fixture.drivefs_path)
        tree = investigation.get_accounts()[0].get_synced_files_tree()
        root = tree.get_root()
        self.assertFalse(
            any(item.get_stable_id() == STABLE_ROOT_1
                for item in root.get_sub_items())
        )
        self.assertTrue(
            any(item.get_stable_id() == STABLE_ROOT_1 for item in tree.get_deleted_items())
        )
        list(tree.generate_synced_files_tree_dicts())
        tree.search(
            [{"TYPE": "filename", "TARGET": ["notes"], "CONTAINS": True, "LIST_SUB_ITEMS": False}]
        )

    def test_account_worker_failure_warns_and_continues(self):
        from drivefs_sleuth import investigation as investigation_module

        real_account = investigation_module.Account

        def fake_account(drivefs_path, account_id, email, is_logged_in, mirroring_roots, properties):
            if account_id == ACCOUNT_ID_1:
                raise RuntimeError("broken account")
            return real_account(drivefs_path, account_id, email, is_logged_in, mirroring_roots,
                                properties)

        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            with mock.patch.object(investigation_module, "Account", side_effect=fake_account):
                investigation = investigation_module.Investigation(self.fixture.drivefs_path)
        self.assertIn(f"[WARNING] Failed to process account {ACCOUNT_ID_1}: broken account",
                      output.getvalue())
        self.assertEqual(len(investigation.get_accounts()), 0)

    def test_csv_report_ignores_extra_property_keys(self):
        investigation = Investigation(self.fixture.drivefs_path)
        tree = investigation.get_accounts()[0].get_synced_files_tree()
        extra_file = File(
            777, "url-777", "Extra.txt", TXT_MIME, 1, 100, LAST_SYNC_MS, LAST_SYNC_MS, 0,
            {"never-a-header-key": "x"}, "My Drive\\Extra.txt", "", "", b""
        )
        tree.get_root().add_item(extra_file)
        output_file = os.path.join(self.tmp.name, "report.csv")
        generate_csv_report(investigation, output_file)
        with open(output_file, encoding="utf-8") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertNotIn("never-a-header-key", rows[0].keys())
        self.assertTrue(any(row["stable_id"] == "777" for row in rows))


class RecoveryResilienceTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(os.path.join(self.tmp.name, "drivefs"))
        self.addCleanup(self.tmp.cleanup)

    def test_copy_file_missing_source_returns_false(self):
        recovery_dir = os.path.join(self.tmp.name, "recovery")
        self.assertFalse(
            copy_file(os.path.join(self.tmp.name, "missing_source"), "target.txt", recovery_dir)
        )
        self.assertFalse(os.path.exists(os.path.join(recovery_dir, "target.txt")))

    def test_recover_from_content_cache_skips_missing_files_with_warning(self):
        missing_cache = os.path.join(self.tmp.name, "gone_cache_file")
        item = File(
            900, "url-900", TITLE_NOTES_FILE, TXT_MIME, 1, 100, LAST_SYNC_MS, LAST_SYNC_MS, 0,
            {}, "My Drive\\notes.txt", missing_cache, "", b""
        )
        recovery_dir = os.path.join(self.tmp.name, "recovery")
        os.makedirs(recovery_dir)
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            recover_from_content_cache([item], recovery_dir)
        self.assertIn(f"Couldn't recover {TITLE_NOTES_FILE}", output.getvalue())
        self.assertFalse(os.path.exists(os.path.join(recovery_dir, TITLE_NOTES_FILE)))


if __name__ == "__main__":
    unittest.main()
