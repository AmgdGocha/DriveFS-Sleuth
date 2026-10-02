"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: tests for the CSV and HTML report generation.
"""

import csv
import os
import tempfile
import unittest

from builders import ACCOUNT_ID_1
from builders import ACCOUNT_ID_2
from builders import DISPLAY_NAME_1
from builders import DISPLAY_NAME_2
from builders import EMAIL_1
from builders import EMAIL_2
from builders import FOLDER_MIME
from builders import LAST_PID
from builders import LAST_SYNC_UTC_STR
from builders import MD5_A
from builders import MD5_B
from builders import MD5_D
from builders import MEDIA_ID
from builders import MEDIA_NAME
from builders import STABLE_DELETED_FILE
from builders import STABLE_NOTES_FILE
from builders import STABLE_ORPHAN_CHILD
from builders import STABLE_ORPHAN_DIR
from builders import STABLE_PROJECTS_DIR
from builders import STABLE_REPORT_FILE
from builders import STABLE_REPORT_SHORTCUT
from builders import STABLE_ROOT_1
from builders import STABLE_SHARED_FILE
from builders import TITLE_DELETED_FILE
from builders import TITLE_ORPHAN_DIR
from builders import TITLE_PROJECTS_DIR
from builders import TITLE_REPORT_FILE
from builders import TITLE_ROOT_1
from builders import build_empty_fixture
from builders import build_logged_in_fixture
from builders import build_not_logged_in_fixture

from drivefs_sleuth.investigation import Investigation
from drivefs_sleuth.tasks import generate_csv_report
from drivefs_sleuth.tasks import generate_html_report

BASE_HEADERS = [
    "account_id", "email", "stable_id", "type", "url_id", "local_title", "mime_type",
    "path_in_content_cache", "thumbnail_path", "is_owner", "file_size", "modified_date",
    "viewed_by_me_date", "trashed", "tree_path", "md5", "folder_queried", "content-entry",
]


class BaseReportTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(self.tmp.name)
        self.investigation = Investigation(self.fixture.drivefs_path)
        self.output_dir = os.path.join(self.tmp.name, "out")
        os.makedirs(self.output_dir)

    def tearDown(self):
        self.tmp.cleanup()

    def read_csv_rows(self, output_file):
        with open(output_file, "r", encoding="utf-8", newline="") as csv_file:
            reader = csv.DictReader(csv_file)
            rows = list(reader)
            headers = reader.fieldnames
        return headers, rows

    def rows_by_stable_id(self, rows, stable_id):
        return [row for row in rows if row["stable_id"] == str(stable_id)]


class TestCsvReport(BaseReportTestCase):
    def test_csv_report_headers_and_rows(self):
        output_file = os.path.join(self.output_dir, "csv_report.csv")
        generate_csv_report(self.investigation, output_file)
        headers, rows = self.read_csv_rows(output_file)

        self.assertEqual(headers, BASE_HEADERS)
        self.assertEqual(len(rows), 9)

    def test_csv_report_content(self):
        output_file = os.path.join(self.output_dir, "csv_report.csv")
        generate_csv_report(self.investigation, output_file)
        _, rows = self.read_csv_rows(output_file)

        for row in rows:
            self.assertEqual(row["account_id"], ACCOUNT_ID_1)
            self.assertEqual(row["email"], EMAIL_1)

        root_row = self.rows_by_stable_id(rows, STABLE_ROOT_1)[0]
        self.assertEqual(root_row["type"], "Directory")
        self.assertEqual(root_row["url_id"], "url-id-100")
        self.assertEqual(root_row["local_title"], TITLE_ROOT_1)
        self.assertEqual(root_row["mime_type"], FOLDER_MIME)
        self.assertEqual(root_row["tree_path"], TITLE_ROOT_1)
        self.assertEqual(root_row["is_owner"], "1")
        self.assertEqual(root_row["modified_date"], LAST_SYNC_UTC_STR)
        self.assertEqual(root_row["viewed_by_me_date"], LAST_SYNC_UTC_STR)
        self.assertEqual(root_row["trashed"], "0")
        self.assertEqual(root_row["md5"], "")

        report_rows = self.rows_by_stable_id(rows, STABLE_REPORT_FILE)
        self.assertEqual(len(report_rows), 2, "the file appears once in the tree and once as a link target")
        for row in report_rows:
            self.assertEqual(row["type"], "File")
            self.assertEqual(row["local_title"], TITLE_REPORT_FILE)
            self.assertEqual(row["tree_path"], f"{TITLE_ROOT_1}\\{TITLE_REPORT_FILE}")
            self.assertEqual(row["md5"], MD5_B)
            self.assertEqual(row["file_size"], "123456")
            self.assertEqual(row["path_in_content_cache"], "")

        projects_row = self.rows_by_stable_id(rows, STABLE_PROJECTS_DIR)[0]
        self.assertEqual(projects_row["type"], "Directory")
        self.assertEqual(projects_row["tree_path"], f"{TITLE_ROOT_1}\\{TITLE_PROJECTS_DIR}")
        self.assertEqual(projects_row["folder_queried"], "1")
        self.assertEqual(projects_row["content-entry"], "")

        notes_row = self.rows_by_stable_id(rows, STABLE_NOTES_FILE)[0]
        self.assertEqual(notes_row["type"], "File")
        self.assertEqual(notes_row["tree_path"], f"{TITLE_ROOT_1}\\{TITLE_PROJECTS_DIR}\\notes.txt")
        self.assertEqual(notes_row["md5"], MD5_A)
        self.assertEqual(notes_row["file_size"], "5000000")
        self.assertEqual(notes_row["path_in_content_cache"], self.fixture.cache_file_path_400)
        self.assertEqual(notes_row["thumbnail_path"], self.fixture.thumbnail_file_path_400)
        self.assertEqual(notes_row["content-entry"], str(self.fixture.content_entry_blob_400))

        shortcut_row = self.rows_by_stable_id(rows, STABLE_REPORT_SHORTCUT)[0]
        self.assertEqual(shortcut_row["type"], "Link")
        self.assertEqual(shortcut_row["tree_path"], f"{TITLE_ROOT_1}\\Report Shortcut")

        orphan_row = self.rows_by_stable_id(rows, STABLE_ORPHAN_DIR)[0]
        self.assertEqual(orphan_row["type"], "Directory")
        self.assertEqual(orphan_row["tree_path"], TITLE_ORPHAN_DIR)

        orphan_child_row = self.rows_by_stable_id(rows, STABLE_ORPHAN_CHILD)[0]
        self.assertEqual(orphan_child_row["type"], "File")
        self.assertEqual(orphan_child_row["tree_path"], f"{TITLE_ORPHAN_DIR}\\orphan_child.txt")
        self.assertEqual(orphan_child_row["file_size"], "10")

        shared_row = self.rows_by_stable_id(rows, STABLE_SHARED_FILE)[0]
        self.assertEqual(shared_row["type"], "File")
        self.assertEqual(shared_row["tree_path"], f"Shared with me\\SharedDoc.pdf")
        self.assertEqual(shared_row["is_owner"], "0")
        self.assertEqual(shared_row["md5"], MD5_D)

    def test_csv_report_with_search_results(self):
        tree = self.investigation.get_accounts()[0].get_synced_files_tree()
        search_results = {
            ACCOUNT_ID_1: tree.search(
                [{"TYPE": "filename", "TARGET": ["report"], "CONTAINS": True, "LIST_SUB_ITEMS": True}]
            )
        }
        output_file = os.path.join(self.output_dir, "csv_report.csv")
        generate_csv_report(self.investigation, output_file, search_results)

        search_output = os.path.join(self.output_dir, "search_results.csv")
        self.assertTrue(os.path.exists(search_output))
        headers, rows = self.read_csv_rows(search_output)
        self.assertEqual(headers[0], "account_id")
        self.assertEqual(headers[1], "email")
        self.assertEqual(len(rows), 4)
        self.assertEqual(
            [row["stable_id"] for row in rows],
            [str(STABLE_REPORT_FILE), str(STABLE_REPORT_SHORTCUT), str(STABLE_REPORT_FILE),
             str(STABLE_DELETED_FILE)],
        )


class TestHtmlReport(BaseReportTestCase):
    def read_html(self):
        output_file = os.path.join(self.output_dir, "html_report.html")
        generate_html_report(self.investigation, output_file)
        with open(output_file, "r", encoding="utf-8") as html_file:
            return html_file.read()

    def test_global_configuration_section(self):
        html = self.read_html()
        self.assertIn("DriveFS Global Configuration", html)
        self.assertIn(self.fixture.drivefs_path, html)
        self.assertIn(LAST_SYNC_UTC_STR, html)
        self.assertIn("Max Root IDs", html)
        self.assertIn("Not Modified", html)
        self.assertIn(LAST_PID, html)

    def test_connected_devices_section(self):
        html = self.read_html()
        self.assertIn("Connected Devices", html)
        self.assertIn(MEDIA_ID, html)
        self.assertIn(MEDIA_NAME, html)

    def test_account_section(self):
        html = self.read_html()
        self.assertIn(EMAIL_1, html)
        self.assertIn(DISPLAY_NAME_1, html)
        self.assertIn(ACCOUNT_ID_1, html)
        self.assertIn("Currently Logged-In", html)
        self.assertIn("Mirroring Roots", html)
        self.assertIn("My Drive Mirror", html)
        self.assertIn("DRIVE", html)
        self.assertIn("Mirrored Items", html)
        self.assertIn("local_doc.docx", html)
        self.assertIn("cloud_doc.docx", html)

    def test_tree_and_deleted_sections(self):
        html = self.read_html()
        self.assertIn("Synced Files Tree", html)
        self.assertIn(TITLE_ROOT_1, html)
        self.assertIn(TITLE_REPORT_FILE, html)
        self.assertIn("Shared with me files", html)
        self.assertIn("SharedDoc.pdf", html)
        self.assertIn("Deleted Items", html)
        self.assertIn(TITLE_DELETED_FILE, html)
        self.assertIn("900", html)

    def test_items_details_json_payload(self):
        html = self.read_html()
        self.assertIn('id="data-source-1"', html)
        self.assertIn(f'"{STABLE_REPORT_FILE}"', html)
        self.assertIn(TITLE_REPORT_FILE, html)


class TestHtmlReportVariants(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.output_dir = os.path.join(self.tmp.name, "out")
        os.makedirs(self.output_dir)

    def generate_html(self, investigation):
        output_file = os.path.join(self.output_dir, "html_report.html")
        generate_html_report(investigation, output_file)
        with open(output_file, "r", encoding="utf-8") as html_file:
            return html_file.read()

    def test_two_accounts(self):
        fixture = build_logged_in_fixture(os.path.join(self.tmp.name, "two"), two_accounts=True)
        html = self.generate_html(Investigation(fixture.drivefs_path))
        self.assertIn(EMAIL_1, html)
        self.assertIn(EMAIL_2, html)
        self.assertIn(DISPLAY_NAME_1, html)
        self.assertIn(DISPLAY_NAME_2, html)
        self.assertIn(ACCOUNT_ID_2, html)
        self.assertIn('id="data-source-2"', html)
        self.assertIn("Other Drive", html)

    def test_not_logged_in_account(self):
        fixture = build_not_logged_in_fixture(os.path.join(self.tmp.name, "loggedout"))
        html = self.generate_html(Investigation(fixture.drivefs_path))
        self.assertIn(EMAIL_1, html)
        self.assertIn("Logged Out", html)
        self.assertNotIn("Synced Files Tree", html)

    def test_empty_installation(self):
        fixture = build_empty_fixture(os.path.join(self.tmp.name, "empty"))
        html = self.generate_html(Investigation(fixture.drivefs_path))
        self.assertIn("Unknown", html)
        self.assertIn(">None</span>", html)
        self.assertNotIn("<details", html)
        self.assertNotIn("<h2>Connected Devices</h2>", html)


if __name__ == "__main__":
    unittest.main()
