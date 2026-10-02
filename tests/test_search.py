"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: unit tests for the synced files tree searching capabilities.
"""

import tempfile
import unittest

from builders import MD5_A
from builders import MD5_C
from builders import STABLE_DELETED_FILE
from builders import STABLE_NOTES_FILE
from builders import STABLE_ORPHAN_CHILD
from builders import STABLE_ORPHAN_DIR
from builders import STABLE_PROJECTS_DIR
from builders import STABLE_REPORT_FILE
from builders import STABLE_REPORT_SHORTCUT
from builders import STABLE_SHARED_FILE
from builders import build_logged_in_fixture

from drivefs_sleuth.investigation import Investigation


class BaseSearchTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.fixture = build_logged_in_fixture(self.tmp.name)
        self.investigation = Investigation(self.fixture.drivefs_path)
        self.tree = self.investigation.get_accounts()[0].get_synced_files_tree()

    def tearDown(self):
        self.tmp.cleanup()

    def search(self, conditions):
        return [item.get_stable_id() for item in self.tree.search(conditions)]


class TestFilenameSearch(BaseSearchTestCase):
    def test_contains_matches_files_links_and_recovered_deleted(self):
        results = self.search(
            [{"TYPE": "filename", "TARGET": ["report"], "CONTAINS": True, "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(
            results,
            [STABLE_REPORT_FILE, STABLE_REPORT_SHORTCUT, STABLE_REPORT_FILE, STABLE_DELETED_FILE],
        )

    def test_contains_is_case_insensitive(self):
        results = self.search(
            [{"TYPE": "filename", "TARGET": ["REPORT.DOCX"], "CONTAINS": True, "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(results, [STABLE_REPORT_FILE, STABLE_REPORT_FILE])

    def test_exact_matches_only_exact_titles(self):
        results = self.search(
            [{"TYPE": "filename", "TARGET": ["report.docx"], "CONTAINS": False, "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(results, [STABLE_REPORT_FILE, STABLE_REPORT_FILE])
        results = self.search(
            [{"TYPE": "filename", "TARGET": ["report"], "CONTAINS": False, "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(results, [])

    def test_folder_match_lists_sub_items(self):
        results = self.search(
            [{"TYPE": "filename", "TARGET": ["projects"], "CONTAINS": True, "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(results, [STABLE_PROJECTS_DIR, STABLE_NOTES_FILE])

    def test_folder_match_without_sub_items(self):
        results = self.search(
            [{"TYPE": "filename", "TARGET": ["projects"], "CONTAINS": True, "LIST_SUB_ITEMS": False}]
        )
        self.assertEqual(results, [STABLE_PROJECTS_DIR])


class TestRegexSearch(BaseSearchTestCase):
    def test_regex_matches_orphan_directory_and_children(self):
        results = self.search(
            [{"TYPE": "regex", "TARGET": ["^Orphan"], "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(results, [STABLE_ORPHAN_DIR, STABLE_ORPHAN_CHILD])

    def test_regex_without_sub_items(self):
        results = self.search(
            [{"TYPE": "regex", "TARGET": ["^Orphan"], "LIST_SUB_ITEMS": False}]
        )
        self.assertEqual(results, [STABLE_ORPHAN_DIR])

    def test_regex_is_case_sensitive(self):
        results = self.search(
            [{"TYPE": "regex", "TARGET": ["^orphan"], "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(results, [STABLE_ORPHAN_CHILD])


class TestUrlIdSearch(BaseSearchTestCase):
    def test_url_id_matches_exact_id(self):
        results = self.search(
            [{"TYPE": "urlid", "TARGET": ["url-id-200"], "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(results, [STABLE_REPORT_FILE, STABLE_REPORT_FILE])

    def test_url_id_match_is_case_insensitive(self):
        results = self.search(
            [{"TYPE": "urlid", "TARGET": ["URL-ID-200"], "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(results, [STABLE_REPORT_FILE, STABLE_REPORT_FILE])

    def test_unknown_url_id_returns_nothing(self):
        results = self.search(
            [{"TYPE": "urlid", "TARGET": ["url-id-999"], "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(results, [])


class TestMd5Search(BaseSearchTestCase):
    def test_md5_matches_file(self):
        results = self.search([{"TYPE": "md5", "TARGET": [MD5_A]}])
        self.assertEqual(results, [STABLE_NOTES_FILE])

    def test_md5_matches_recovered_deleted_file(self):
        results = self.search([{"TYPE": "md5", "TARGET": [MD5_C]}])
        self.assertEqual(results, [STABLE_DELETED_FILE])

    def test_unknown_md5_returns_nothing(self):
        results = self.search([{"TYPE": "md5", "TARGET": ["f" * 32]}])
        self.assertEqual(results, [])


class TestBranchCoverageSearch(BaseSearchTestCase):
    def test_shared_with_me_items_are_searched(self):
        results = self.search(
            [{"TYPE": "filename", "TARGET": ["shareddoc"], "CONTAINS": True, "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(results, [STABLE_SHARED_FILE])

    def test_orphan_children_are_searched(self):
        results = self.search(
            [{"TYPE": "filename", "TARGET": ["orphan_child"], "CONTAINS": True, "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(results, [STABLE_ORPHAN_CHILD])

    def test_recovered_deleted_items_are_searched(self):
        results = self.search(
            [{"TYPE": "filename", "TARGET": ["deleted"], "CONTAINS": True, "LIST_SUB_ITEMS": True}]
        )
        self.assertEqual(
            set(results),
            {STABLE_DELETED_FILE, 820},
        )

    def test_multiple_targets_in_single_criteria(self):
        results = self.search(
            [{"TYPE": "filename", "TARGET": ["report", "orphan"], "CONTAINS": True, "LIST_SUB_ITEMS": False}]
        )
        self.assertEqual(
            results,
            [STABLE_REPORT_FILE, STABLE_REPORT_SHORTCUT, STABLE_REPORT_FILE, STABLE_ORPHAN_DIR,
             STABLE_ORPHAN_CHILD, STABLE_DELETED_FILE],
        )


if __name__ == "__main__":
    unittest.main()
