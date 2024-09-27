"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: this module contains tasks related to the drivefs-sleuth execution.
"""

import os
import csv

from jinja2 import Environment
from jinja2 import FileSystemLoader

from drivefs_sleuth.utils import copy_file
from drivefs_sleuth.utils import lookup_account_id
from drivefs_sleuth.utils import get_properties_list
from drivefs_sleuth.utils import get_account_properties
from drivefs_sleuth.utils import get_available_profiles
from drivefs_sleuth.utils import get_experiment_account_ids

from drivefs_sleuth.synced_files_tree import File


def get_accounts(drivefs_path):
    accounts = {}
    experiments_ids = get_experiment_account_ids(drivefs_path)
    profiles = get_available_profiles(drivefs_path)
    available_accounts = set(experiments_ids + profiles)
    for account_id in available_accounts:
        accounts[account_id] = {
            'email': lookup_account_id(drivefs_path, account_id)
        }
        logged_in = account_id in profiles
        accounts[account_id]['logged_in'] = logged_in
        accounts[account_id]['properties'] = get_account_properties(os.path.join(drivefs_path, account_id))
    return accounts


def __build_headers(setup):
    headers = ['stable_id', 'type', 'url_id', 'local_title', 'mime_type', 'path_in_content_cache', 'thumbnail_path',
               'is_owner', 'file_size', 'modified_date', 'viewed_by_me_date', 'trashed', 'tree_path', 'md5']
    for account in setup.get_accounts():
        if account.is_logged_in():
            for prop in get_properties_list(os.path.join(setup.get_drivefs_path(), account.get_account_id())):
                if prop not in headers:
                    headers.append(prop)
    return headers


def __generate_csv_search_results_report(setup, output_file, search_results):
    search_results_headers = ['account_id', 'email'] + __build_headers(setup)
    with open(output_file, 'w', encoding='utf-8', newline='') as search_results_csv_file:
        csv_writer = csv.DictWriter(search_results_csv_file, fieldnames=search_results_headers)
        csv_writer.writeheader()
        for account, results in search_results.items():
            for result in results:
                row = result.to_dict()
                row['account_id'] = account[0]
                row['email'] = account[1]
                if result.is_file():
                    row['type'] = 'File'
                    if result.get_content_cache_path():
                        row['path_in_content_cache'] = result.get_content_cache_path()
                    if result.get_content_cache_path():
                        row['thumbnail_path'] = result.get_thumbnail_path()
                elif result.is_link():
                    row['type'] = 'Link'
                else:
                    row['type'] = 'Directory'
                csv_writer.writerow(row)


def __generate_csv_report_gen(setup, output_file):
    headers = ['account_id', 'email'] + __build_headers(setup)
    with open(output_file, 'w', encoding='utf-8', newline='') as csv_report_file:
        csv_writer = csv.DictWriter(csv_report_file, fieldnames=headers)
        csv_writer.writeheader()

        for account in setup.get_accounts():
            if account.is_logged_in():
                files_tree = account.get_synced_files_tree()
                for row in files_tree.generate_synced_files_tree_dicts():
                    row['account_id'] = account.get_account_id()
                    row['email'] = account.get_account_email()
                    csv_writer.writerow(row)


def generate_csv_report(setup, output_file, search_results=None):
    if search_results is None:
        search_results = {}

    if search_results:
        parent_dir = os.path.abspath(os.path.join(output_file, os.pardir))
        search_results_csv_path = os.path.join(parent_dir, 'search_results.csv')
        __generate_csv_search_results_report(setup, search_results_csv_path, search_results)

    __generate_csv_report_gen(setup, output_file)


def generate_html_report(setup, output_file, search_results=None):
    if search_results is None:
        search_results = {}
    print(f"{os.path.join(os.path.dirname(__file__), 'html_resources')}")
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'html_resources')))
    template = env.get_template("report_template.html")
    headers = __build_headers(setup)

    stream_template = template.stream(
        setup=setup,
        search_results=search_results,
        headers=headers
    )
    stream_template.dump(output_file)


def recover_from_content_cache(recoverable_items, recovery_path):
    for item in recoverable_items:
        if isinstance(item, File):
            if item.get_content_cache_path():
                copy_file(
                    item.get_content_cache_path(),
                    item.local_title,
                    recovery_path
                )


def recover_thumbnail(recoverable_items, recovery_path):
    for item in recoverable_items:
        if isinstance(item, File):
            if item.get_thumbnail_path():
                copy_file(
                    item.get_thumbnail_path(),
                    item.local_title,
                    recovery_path
                )
