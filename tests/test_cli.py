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
from builders import EMAIL_1
from builders import MD5_A
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
        recovered_file = os.path.join(self.output_dir, "recovery", EMAIL_1, "notes.txt")
        self.assertTrue(os.path.exists(recovered_file))
        with open(recovered_file, "rb") as recovered:
            self.assertEqual(recovered.read(), CACHE_CONTENT_400)
        recovered_thumbnail = os.path.join(
            self.output_dir, "recovery", EMAIL_1, "thumbnails", "notes.txt"
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

    def test_recover_search_results_prints_summary(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "-q", "notes",
             "--recover-search-results"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("[RECOVERY] Recovered 1 items, 1 thumbnails for account", result.stdout)

    def test_recover_search_results_no_match(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "-q", "zzzznomatch",
             "--recover-search-results"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertIn("no results available", result.stdout)
        self.assertFalse(os.path.exists(os.path.join(self.output_dir, "search_results_recovery")))

    def test_recover_search_results_workers_produce_identical_output(self):
        default_out = os.path.join(self.output_dir, "default")
        workers_out = os.path.join(self.output_dir, "workers")
        result = run_cli(
            [self.fixture.drivefs_path, "-o", default_out, "--csv", "-q", "notes",
             "--recover-search-results", "--recovery-workers", "8"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        result = run_cli(
            [self.fixture.drivefs_path, "-o", workers_out, "--csv", "-q", "notes",
             "--recover-search-results", "--recovery-workers", "1"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        default_files = []
        for root, _, files in os.walk(os.path.join(default_out, "search_results_recovery")):
            for name in files:
                default_files.append(os.path.relpath(os.path.join(root, name), default_out))
        self.assertTrue(default_files)
        for rel in default_files:
            with open(os.path.join(default_out, rel), "rb") as file_a, open(
                os.path.join(workers_out, rel), "rb"
            ) as file_b:
                self.assertEqual(file_a.read(), file_b.read())

    def test_recover_from_cache_workers_produce_identical_output(self):
        default_out = os.path.join(self.output_dir, "default")
        workers_out = os.path.join(self.output_dir, "workers")
        result = run_cli(
            [self.fixture.drivefs_path, "-o", default_out, "--csv", "--recover-from-cache",
             "--recovery-workers", "8"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        result = run_cli(
            [self.fixture.drivefs_path, "-o", workers_out, "--csv", "--recover-from-cache",
             "--recovery-workers", "1"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        expected_file = os.path.join(workers_out, "recovery", EMAIL_1, "notes.txt")
        self.assertTrue(os.path.exists(expected_file))
        default_files = []
        for root, _, files in os.walk(os.path.join(default_out, "recovery")):
            for name in files:
                default_files.append(os.path.relpath(os.path.join(root, name), default_out))
        self.assertTrue(default_files)
        for rel in default_files:
            with open(os.path.join(default_out, rel), "rb") as file_a, open(
                os.path.join(workers_out, rel), "rb"
            ) as file_b:
                self.assertEqual(file_a.read(), file_b.read())


class TestCliSearch(BaseCliTestCase):
    def search_rows(self, out_dir):
        search_csv_path = os.path.join(out_dir, "search_results.csv")
        if not os.path.exists(search_csv_path):
            return []
        with open(search_csv_path, "r", encoding="utf-8", newline="") as csv_file:
            return list(csv.DictReader(csv_file))

    def test_regex_search(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "--regex", "^notes"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(len(self.search_rows(self.output_dir)), 1)

    def test_regex_search_is_case_sensitive(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "--regex", "^NOTES"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(self.search_rows(self.output_dir), [])

    def test_md5_search(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "--md5", MD5_A]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(len(self.search_rows(self.output_dir)), 1)

    def test_url_id_search(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "--url-id", "url-id-400"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(len(self.search_rows(self.output_dir)), 1)

    def test_exact_query_by_name(self):
        exact_out = os.path.join(self.output_dir, "exact")
        contains_out = os.path.join(self.output_dir, "contains")
        result = run_cli(
            [self.fixture.drivefs_path, "-o", exact_out, "--csv", "-q", "notes.txt",
             "--exact"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(len(self.search_rows(exact_out)), 1)
        result = run_cli(
            [self.fixture.drivefs_path, "-o", contains_out, "--csv", "-q", "notes",
             "--exact"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(self.search_rows(contains_out), [])

    def test_dont_list_sub_items(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "-q", "projects"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(len(self.search_rows(self.output_dir)), 2)
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "-q", "projects",
             "--dont-list-sub-items"]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(len(self.search_rows(self.output_dir)), 1)

    def test_search_csv_with_all_criteria_types(self):
        search_csv_path = os.path.join(self.tmp.name, "criteria.csv")
        with open(search_csv_path, "w", encoding="utf-8", newline="") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["TYPE", "TARGET", "CONTAINS", "LIST_SUB_ITEMS"])
            writer.writerow(["filename", "report", "True", "True"])
            writer.writerow(["regex", "^notes", "", "True"])
            writer.writerow(["md5", MD5_A, "", ""])
            writer.writerow(["urlid", "url-id-400", "", "False"])
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "--search-csv",
             search_csv_path]
        )
        self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)
        self.assertEqual(len(self.search_rows(self.output_dir)), 5)

    def test_search_csv_without_contains_columns_shows_usage(self):
        search_csv_path = os.path.join(self.tmp.name, "criteria.csv")
        with open(search_csv_path, "w", encoding="utf-8", newline="") as csv_file:
            csv_file.write("TYPE,TARGET\n")
            csv_file.write("filename,report\n")
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "--search-csv",
             search_csv_path]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("TYPE,TARGET,CONTAINS,LIST_SUB_ITEMS", result.stdout)

    def test_search_csv_row_missing_target_shows_usage(self):
        search_csv_path = os.path.join(self.tmp.name, "criteria.csv")
        with open(search_csv_path, "w", encoding="utf-8", newline="") as csv_file:
            csv_file.write("TYPE,TARGET,CONTAINS,LIST_SUB_ITEMS\n")
            csv_file.write("filename,,True,True\n")
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "--search-csv",
             search_csv_path]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("TYPE,TARGET,CONTAINS,LIST_SUB_ITEMS", result.stdout)

    def test_search_csv_missing_file_shows_error(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "--search-csv",
             os.path.join(self.tmp.name, "nope.csv")]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("couldn't read the searching criteria CSV file", result.stdout)

    def test_invalid_regex_exits_2(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", self.output_dir, "--csv", "--regex", "("]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("Invalid regular expression", result.stdout)


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

    def test_invalid_recovery_workers_exits_2(self):
        result = run_cli(
            [self.fixture.drivefs_path, "-o", os.path.join(self.tmp.name, "out"), "--csv",
             "--recover-from-cache", "--recovery-workers", "0"]
        )
        self.assertEqual(result.returncode, 2)
        self.assertIn("--recovery-workers", result.stdout)

    def test_output_pointing_to_file_exits_2(self):
        existing_file = os.path.join(self.tmp.name, "afile.txt")
        with open(existing_file, "w", encoding="utf-8") as file_handle:
            file_handle.write("x")
        result = run_cli([self.fixture.drivefs_path, "-o", existing_file, "--csv"])
        self.assertEqual(result.returncode, 2)
        self.assertIn("not a file", result.stdout)


if __name__ == "__main__":
    unittest.main()
