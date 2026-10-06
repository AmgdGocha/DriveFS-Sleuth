"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: tests for the modern (chunked) DriveFS content cache layout support.
"""

import contextlib
import csv
import io
import os
import subprocess
import sys
import tempfile
import unittest

from builders import MODERN_ACCOUNT_ID
from builders import MODERN_CACHE_CONTENT_SINGLE
from builders import MODERN_CACHE_KEY_SINGLE
from builders import MODERN_CACHE_MULTI_EXPECTED
from builders import MODERN_CACHE_MULTI_TOTAL
from builders import MODERN_CACHE_PART_1
from builders import MODERN_DISPLAY_NAME
from builders import MODERN_EMAIL
from builders import MODERN_EMPTY_ORPHAN_KEY
from builders import MODERN_ORPHAN_CONTENT
from builders import MODERN_ORPHAN_KEY
from builders import MODERN_THUMBNAIL_CONTENT
from builders import STABLE_MODERN_FILE
from builders import STABLE_MODERN_MULTI
from builders import TITLE_MODERN_FILE
from builders import TITLE_MODERN_MULTI
from builders import build_modern_layout_fixture

from drivefs_sleuth.investigation import Investigation
from drivefs_sleuth.tasks import recover_from_content_cache
from drivefs_sleuth.tasks import recover_orphaned_cache
from drivefs_sleuth.tasks import recover_thumbnail
from drivefs_sleuth.utils import get_content_cache_stem_paths
from drivefs_sleuth.utils import get_file_content_cache_path
from drivefs_sleuth.utils import load_cache_ranges

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DEV_RUNNER = os.path.join(REPO_ROOT, "drivefs_sleuth.py")


def run_cli(arguments):
    return subprocess.run(
        [sys.executable, DEV_RUNNER] + arguments,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


class BaseModernTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_modern_layout_fixture(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()


class TestModernUtils(BaseModernTestCase):
    def test_load_cache_ranges_parses_single_and_multi_chunk_rows(self):
        ranges = load_cache_ranges(self.fixture.content_chunks_db)
        self.assertEqual(ranges[str(MODERN_CACHE_KEY_SINGLE)],
                         (len(MODERN_CACHE_CONTENT_SINGLE), [(0, len(MODERN_CACHE_CONTENT_SINGLE))]))
        size, chunks = ranges["19307"]
        self.assertEqual(size, MODERN_CACHE_MULTI_TOTAL)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(chunks[0][1], len(MODERN_CACHE_PART_1))

    def test_load_cache_ranges_missing_db_returns_empty(self):
        self.assertEqual(load_cache_ranges(os.path.join(self.tmp.name, "missing.db")), {})

    def test_load_cache_ranges_corrupt_db_returns_empty(self):
        corrupt_path = os.path.join(self.tmp.name, "corrupt.db")
        with open(corrupt_path, "wb") as corrupt_file:
            corrupt_file.write(b"not a sqlite database")
        self.assertEqual(load_cache_ranges(corrupt_path), {})

    def test_stem_paths_map_keys_by_stem_and_skips_internal_files(self):
        stems = get_content_cache_stem_paths(
            os.path.join(self.fixture.drivefs_path, MODERN_ACCOUNT_ID, "content_cache")
        )
        self.assertEqual(stems.get(str(MODERN_CACHE_KEY_SINGLE)), self.fixture.single_cache_path)
        self.assertEqual(stems.get("19307"), self.fixture.multi_cache_path)
        self.assertEqual(stems.get(str(MODERN_ORPHAN_KEY)), self.fixture.orphan_cache_path)
        self.assertNotIn("METADATA", stems)
        self.assertNotIn("chunks.db", stems)

    def test_get_file_content_cache_path_resolves_int_key_via_stems(self):
        import builders
        stems = get_content_cache_stem_paths(
            os.path.join(self.fixture.drivefs_path, MODERN_ACCOUNT_ID, "content_cache")
        )
        blob = builders.encode_modern_content_entry(MODERN_CACHE_KEY_SINGLE)
        self.assertEqual(
            get_file_content_cache_path(blob, {}, stems),
            self.fixture.single_cache_path,
        )
        self.assertEqual(
            get_file_content_cache_path(builders.encode_modern_content_entry(999999), {}, stems),
            "",
        )

    def test_get_file_content_cache_path_str_key_keeps_legacy_basename_lookup(self):
        import builders
        paths = {"cachefile-400": "/tmp/cachefile-400"}
        self.assertEqual(
            get_file_content_cache_path(builders.encode_content_entry("cachefile-400"), paths, {}),
            "/tmp/cachefile-400",
        )


class TestModernInvestigation(BaseModernTestCase):
    def test_account_and_cache_paths(self):
        investigation = Investigation(self.fixture.drivefs_path)
        accounts = investigation.get_accounts()
        self.assertEqual(len(accounts), 1)
        account = accounts[0]
        self.assertEqual(account.get_name(), MODERN_DISPLAY_NAME)
        self.assertEqual(account.get_account_id(), MODERN_ACCOUNT_ID)
        self.assertEqual(account.get_account_email(), MODERN_EMAIL)
        tree = account.get_synced_files_tree()

        single_file = tree.get_item_by_id(STABLE_MODERN_FILE)
        self.assertEqual(single_file.get_content_cache_path(), self.fixture.single_cache_path)
        self.assertEqual(single_file.get_thumbnail_path(), self.fixture.thumbnail_cache_path)

        multi_file = tree.get_item_by_id(STABLE_MODERN_MULTI)
        self.assertEqual(multi_file.get_content_cache_path(), self.fixture.multi_cache_path)

        self.assertEqual(len(tree.get_recoverable_items_from_cache()), 2)
        self.assertEqual(len(tree.get_thumbnail_items()), 1)


class TestModernRecovery(BaseModernTestCase):
    def setUp(self):
        super().setUp()
        self.investigation = Investigation(self.fixture.drivefs_path)
        self.account = self.investigation.get_accounts()[0]
        self.tree = self.account.get_synced_files_tree()
        self.recovery_dir = os.path.join(self.tmp.name, "recovery")
        self.content_ranges = load_cache_ranges(self.fixture.content_chunks_db)

    def test_single_chunk_copied_whole_and_multi_chunk_concatenated(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            recover_from_content_cache(
                self.tree.get_recoverable_items_from_cache(),
                self.recovery_dir,
                workers=2,
                cache_ranges=self.content_ranges,
            )
        with open(os.path.join(self.recovery_dir, TITLE_MODERN_FILE), "rb") as recovered:
            self.assertEqual(recovered.read(), MODERN_CACHE_CONTENT_SINGLE)
        with open(os.path.join(self.recovery_dir, TITLE_MODERN_MULTI), "rb") as recovered:
            self.assertEqual(recovered.read(), MODERN_CACHE_MULTI_EXPECTED)
        self.assertIn("Recovered partial content", output.getvalue())

    def test_thumbnail_recovery_uses_stem_lookup(self):
        recover_thumbnail(
            self.tree.get_thumbnail_items(), self.recovery_dir, workers=2
        )
        with open(os.path.join(self.recovery_dir, TITLE_MODERN_FILE), "rb") as recovered:
            self.assertEqual(recovered.read(), MODERN_THUMBNAIL_CONTENT)

    def test_orphan_recovery_into_orphaned_cache_folder(self):
        recover_orphaned_cache([self.fixture.orphan_cache_path], self.recovery_dir, workers=2)
        with open(os.path.join(self.recovery_dir, "orphaned_cache",
                               f"{MODERN_ORPHAN_KEY}.bin"), "rb") as recovered:
            self.assertEqual(recovered.read(), MODERN_ORPHAN_CONTENT)

    def test_orphan_recovery_without_files_creates_no_folder(self):
        recover_orphaned_cache([], self.recovery_dir, workers=2)
        self.assertFalse(os.path.exists(os.path.join(self.recovery_dir, "orphaned_cache")))

    def test_parallel_and_sequential_recovery_produce_identical_output(self):
        sequential_dir = os.path.join(self.tmp.name, "sequential")
        parallel_dir = os.path.join(self.tmp.name, "parallel")
        recover_from_content_cache(
            self.tree.get_recoverable_items_from_cache(), sequential_dir, workers=1,
            cache_ranges=self.content_ranges,
        )
        recover_from_content_cache(
            self.tree.get_recoverable_items_from_cache(), parallel_dir, workers=8,
            cache_ranges=self.content_ranges,
        )
        self.assertEqual(sorted(os.listdir(sequential_dir)), sorted(os.listdir(parallel_dir)))
        for name in sorted(os.listdir(sequential_dir)):
            with open(os.path.join(sequential_dir, name), "rb") as file_a, open(
                os.path.join(parallel_dir, name), "rb"
            ) as file_b:
                self.assertEqual(file_a.read(), file_b.read())


class TestModernCli(BaseModernTestCase):
    def test_recover_from_cache_end_to_end(self):
        output_dir = os.path.join(self.tmp.name, "out")
        result = run_cli(
            [self.fixture.drivefs_path, "-o", output_dir, "--csv", "--recover-from-cache"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("Recovered 2 items, 1 thumbnails, and 1 orphaned cache files",
                      result.stdout)

        account_dir = os.path.join(output_dir, "recovery", MODERN_DISPLAY_NAME)
        with open(os.path.join(account_dir, TITLE_MODERN_FILE), "rb") as recovered:
            self.assertEqual(recovered.read(), MODERN_CACHE_CONTENT_SINGLE)
        with open(os.path.join(account_dir, TITLE_MODERN_MULTI), "rb") as recovered:
            self.assertEqual(recovered.read(), MODERN_CACHE_MULTI_EXPECTED)
        with open(os.path.join(account_dir, "thumbnails", TITLE_MODERN_FILE), "rb") as recovered:
            self.assertEqual(recovered.read(), MODERN_THUMBNAIL_CONTENT)
        with open(os.path.join(account_dir, "orphaned_cache",
                               f"{MODERN_ORPHAN_KEY}.bin"), "rb") as recovered:
            self.assertEqual(recovered.read(), MODERN_ORPHAN_CONTENT)
        self.assertFalse(os.path.exists(os.path.join(
            account_dir, "orphaned_cache", f"{MODERN_EMPTY_ORPHAN_KEY}.dat"
        )))
        self.assertFalse(os.path.exists(os.path.join(account_dir, "orphaned_cache", "METADATA")))
        self.assertFalse(os.path.exists(os.path.join(account_dir, "METADATA")))

    def test_csv_report_populates_modern_cache_paths(self):
        output_dir = os.path.join(self.tmp.name, "out")
        result = run_cli(
            [self.fixture.drivefs_path, "-o", output_dir, "--csv"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        with open(os.path.join(output_dir, "csv_report.csv"), newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        single_row = next(row for row in rows if row["local_title"] == TITLE_MODERN_FILE)
        self.assertEqual(single_row["path_in_content_cache"], self.fixture.single_cache_path)
        self.assertEqual(single_row["thumbnail_path"], self.fixture.thumbnail_cache_path)
