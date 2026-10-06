"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: guards that ensure the test suite stays free of real/personal information.
"""

import os
import re
import tempfile
import unittest

from builders import ACCOUNT_ID_1
from builders import ACCOUNT_ID_2
from builders import EMAIL_1
from builders import EMAIL_2
from builders import UNKNOWN_ACCOUNT_ID
from builders import MODERN_ACCOUNT_ID
from builders import MODERN_EMAIL
from builders import build_logged_in_fixture

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))

ALLOWED_ACCOUNT_IDS = {ACCOUNT_ID_1, ACCOUNT_ID_2, UNKNOWN_ACCOUNT_ID, MODERN_ACCOUNT_ID}
ALLOWED_EMAILS = {EMAIL_1, EMAIL_2, MODERN_EMAIL, "amged_wageh@outlook.com"}
ALLOWED_DOMAINS = {"example.com", "outlook.com"}

LOCAL_DATA_DIR_NAME = "_" + "tests"
PERSONAL_DATA_DIR_NAME = "DriveFS_" + "Forensics"

EMAIL_REGEX = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")
TWENTY_ONE_DIGITS_REGEX = re.compile(r"\d{21}")


def read_tests_sources():
    sources = {}
    for root, _, files in os.walk(TESTS_DIR):
        for filename in files:
            if not filename.endswith(".py") or filename == "test_no_pii.py":
                continue
            with open(os.path.join(root, filename), "r", encoding="utf-8") as source_file:
                sources[filename] = source_file.read()
    return sources


class TestNoPersonalInformation(unittest.TestCase):
    def test_source_files_do_not_reference_local_personal_data(self):
        for filename, source in read_tests_sources().items():
            self.assertNotIn(LOCAL_DATA_DIR_NAME, source,
                             msg=f"{filename} references the local {LOCAL_DATA_DIR_NAME} directory")
            self.assertNotIn(PERSONAL_DATA_DIR_NAME, source,
                             msg=f"{filename} references the local personal data directory")

    def test_source_files_contain_only_placeholder_account_ids(self):
        for filename, source in read_tests_sources().items():
            found_ids = set(TWENTY_ONE_DIGITS_REGEX.findall(source))
            self.assertTrue(
                found_ids <= ALLOWED_ACCOUNT_IDS,
                msg=f"{filename} contains unexpected 21-digit account ids: "
                    f"{found_ids - ALLOWED_ACCOUNT_IDS}",
            )

    def test_source_files_contain_only_placeholder_emails(self):
        for filename, source in read_tests_sources().items():
            found_emails = set(EMAIL_REGEX.findall(source))
            self.assertTrue(
                found_emails <= ALLOWED_EMAILS,
                msg=f"{filename} contains unexpected emails: {found_emails - ALLOWED_EMAILS}",
            )

    def test_generated_fixture_contains_only_placeholder_account_ids(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = build_logged_in_fixture(tmp)
            for root, dirs, _ in os.walk(fixture.drivefs_path):
                for dirname in dirs:
                    if len(dirname) == 21 and dirname.isdigit():
                        self.assertIn(dirname, ALLOWED_ACCOUNT_IDS)

    def test_generated_fixture_contains_only_placeholder_emails(self):
        with tempfile.TemporaryDirectory() as tmp:
            fixture = build_logged_in_fixture(tmp)
            logs_path = os.path.join(fixture.drivefs_path, "Logs", "drive_fs.txt")
            with open(logs_path, "r", encoding="utf-8") as logs_file:
                logs = logs_file.read()
            found_emails = set(EMAIL_REGEX.findall(logs))
            self.assertTrue(found_emails <= ALLOWED_EMAILS)

    def test_all_builder_placeholder_values_use_allowed_domains(self):
        import builders

        for constant_name in dir(builders):
            constant_value = getattr(builders, constant_name)
            if not isinstance(constant_value, str) or constant_name.startswith("_"):
                continue
            for found_email in EMAIL_REGEX.findall(constant_value):
                domain = found_email.rsplit("@", 1)[1]
                self.assertIn(domain, ALLOWED_DOMAINS,
                              msg=f"{constant_name} uses a non-placeholder domain")


if __name__ == "__main__":
    unittest.main()
