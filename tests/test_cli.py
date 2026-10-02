"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: end-to-end tests for the DriveFS Sleuth command line interface.
"""

import csv
import os
import subprocess
import sys
import tempfile
import unittest

from builders import CACHE_CONTENT_400
from builders import THUMBNAIL_CONTENT_400
from builders import UNKNOWN_ACCOUNT_ID
from builders import build_logged_in_fixture

from drivefs_sleuth import __version__

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DEV_RUNNER = os.path.join(REPO_ROOT, "drivefs_sleuth.py")


def run_cli(arguments):
    return subprocess.run(
        [sys.executable, DEV_RUNNER] + arguments,
        capture_output=True,
        text=True,
        cwd=REPO_ROOT,
    )


class BaseCliTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(os.path.join(self.tmp.name, "drivefs"))
        self.output_dir = os.path.join(self.tmp.name, "out")
        os.makedirs(self.output_dir)

    def tearDown(self):
        self.tmp.cleanup()


class TestCliVersion(BaseCliTestCase):
    def test_version_flag_prints_package_version(self):
        result = run_cli(["--version"])
        self.assertEqual(result.returncode, 0)
        self.assertIn(__version__, result.stdout)


class TestCliReports(BaseCliTestCase):
    def test_full_html_and_csv_run(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--html", "--csv"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("completed the process", result.stdout)
        html_path = os.path.join(self.output_dir, "html_report.html")
        csv_path = os.path.join(self.output_dir, "csv_report.csv")
        self.assertTrue(os.path.exists(html_path))
        self.assertTrue(os.path.exists(csv_path))
        with open(csv_path, "r", encoding="utf-8", newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertEqual(len(rows), 9)

    def test_search_results_csv_is_generated(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--html", "--csv",
             "-q", "report"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        search_csv_path = os.path.join(self.output_dir, "search_results.csv")
        self.assertTrue(os.path.exists(search_csv_path))
        with open(search_csv_path, "r", encoding="utf-8", newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertEqual(len(rows), 4)

    def test_accounts_filter(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "--accounts",
             UNKNOWN_ACCOUNT_ID]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        with open(os.path.join(self.output_dir, "csv_report.csv"), "r", encoding="utf-8",
                  newline="") as csv_file:
            rows = list(csv.DictReader(csv_file))
        self.assertEqual(rows, [])


class TestCliRecovery(BaseCliTestCase):
    def test_recover_from_cache(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "--recover-from-cache"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        recovered_file = os.path.join(self.output_dir, "recovery", "Test User", "notes.txt")
        self.assertTrue(os.path.exists(recovered_file))
        with open(recovered_file, "rb") as recovered:
            self.assertEqual(recovered.read(), CACHE_CONTENT_400)
        recovered_thumbnail = os.path.join(
            self.output_dir, "recovery", "Test User", "thumbnails", "notes.txt"
        )
        self.assertTrue(os.path.exists(recovered_thumbnail))
        with open(recovered_thumbnail, "rb") as recovered:
            self.assertEqual(recovered.read(), THUMBNAIL_CONTENT_400)

    def test_recover_search_results(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "-q", "notes",
             "--recover-search-results"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        recovered_file = os.path.join(
            self.output_dir, "search_results_recovery", "testuser@example.com", "notes.txt"
        )
        self.assertTrue(os.path.exists(recovered_file))
        with open(recovered_file, "rb") as recovered:
            self.assertEqual(recovered.read(), CACHE_CONTENT_400)


class TestCliArgumentValidation(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(os.path.join(self.tmp.name, "drivefs"))
        self.addCleanup(self.tmp.cleanup)

    def test_exact_without_query_by_name_exits_2(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", os.path.join(self.tmp.name, "out"), "--csv", "--exact"]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--exact", result.stdout)

    def test_missing_output_format_exits_2(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", os.path.join(self.tmp.name, "out")]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--csv or --html", result.stdout)

    def test_recover_search_results_without_criteria_exits_2(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", os.path.join(self.tmp.name, "out"), "--csv",
             "--recover-search-results"]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--recover-search-results", result.stdout)

    def test_output_pointing_to_file_exits_2(self):
        existing_file = os.path.join(self.tmp.name, "afile.txt")
        with open(existing_file, "w", encoding="utf-8") as file_handle:
            file_handle.write("x")
        result = run_cli([self.fixture.drivefs_path, "-o", existing_file, "--csv"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a file", result.stdout)


if __name__ == "__main__":
    unittest.main()
