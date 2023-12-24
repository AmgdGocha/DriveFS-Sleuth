import os
import csv

from jinja2 import Environment
from jinja2 import FileSystemLoader

from drivefs_sleuth.utils import lookup_account_id
from drivefs_sleuth.utils import get_properties_list
from drivefs_sleuth.utils import get_available_profiles
from drivefs_sleuth.utils import get_experiment_account_ids

from drivefs_sleuth.synced_files_tree import File
from drivefs_sleuth.synced_files_tree import Link


def get_accounts(drivefs_path):
    accounts = {}
    experiments_ids = get_experiment_account_ids(drivefs_path)
    profiles = get_available_profiles(drivefs_path)
    available_accounts = set(experiments_ids + profiles)
    for account_id in available_accounts:
        accounts[account_id] = {
            'logged_in': account_id in profiles,
            'email': lookup_account_id(drivefs_path, account_id)
        }
    return accounts


def __build_headers(setup):
    headers = ['stable_id', 'type', 'url_id', 'local_title', 'mime_type', 'is_owner', 'file_size', 'modified_date',
               'viewed_by_me_date', 'trashed', 'tree_path']
    for account in setup.get_accounts():
        if account.is_logged_in():
            for prop in get_properties_list(os.path.join(setup.get_drivefs_path(), account.get_account_id())):
                if prop not in headers:
                    headers.append(prop)
    return headers


def __generate_csv_search_results_report(setup, output_file, search_results):
    search_results_headers = ['account_id', 'email'] + __build_headers(setup)
    with open(output_file, 'w', encoding='utf-8') as search_results_csv_file:
        csv_writer = csv.DictWriter(search_results_csv_file, fieldnames=search_results_headers)
        csv_writer.writeheader()
        for account, results in search_results.items():
            for result in results:
                row = result.to_dict()
                row['account_id'] = account[0]
                row['email'] = account[1]
                if not result.is_dir():
                    row['type'] = 'File'
                elif result.is_link():
                    row['type'] = 'Link'
                else:
                    row['type'] = 'Directory'
                csv_writer.writerow(row)


def __generate_csv_report(setup, output_file):
    headers = ['account_id', 'email'] + __build_headers(setup)
    with open(output_file, 'w', encoding='utf-8') as csv_report_file:
        csv_writer = csv.DictWriter(csv_report_file, fieldnames=headers)
        csv_writer.writeheader()
        rows = []

        def __generate_csv_dict(roots, account_id, email):
            if isinstance(roots, list):
                for item in roots:
                    __generate_csv_dict(item, account_id, email)
            else:
                row = roots.to_dict()
                row['account_id'] = account_id
                row['email'] = email
                if isinstance(roots, File):
                    row['type'] = 'File'
                    rows.append(row)
                    return
                elif isinstance(roots, Link):
                    row['type'] = 'Link'
                    rows.append(row)
                    for sub_item in roots.get_target_item().get_sub_items():
                        __generate_csv_dict(sub_item, account_id, email)
                else:
                    row['type'] = 'Directory'
                    rows.append(row)
                    for sub_item in roots.get_sub_items():
                        __generate_csv_dict(sub_item, account_id, email)

        for account in setup.get_accounts():
            files_tree = account.get_synced_files_tree()
            __generate_csv_dict(
                [files_tree.get_root()] + files_tree.get_orphan_items() + files_tree.get_shared_with_me_items(),
                account.get_account_id(),
                account.get_account_email()
            )

        csv_writer.writerows(rows)


def generate_csv_report(setup, output_file, search_results=None):
    if search_results is None:
        search_results = {}

    if search_results:
        parent_dir = os.path.abspath(os.path.join(output_file, os.pardir))
        search_results_csv_path = os.path.join(parent_dir, 'search_results.csv')
        __generate_csv_search_results_report(setup, search_results_csv_path, search_results)

    __generate_csv_report(setup, output_file)


def generate_html_report(setup, output_file, search_results=None):
    if search_results is None:
        search_results = {}
    env = Environment(loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), 'html_resources')))
    template = env.get_template("report_template.html")
    headers = __build_headers(setup)

    with open(output_file, 'w', encoding='utf-8') as report_file:
        report_file.write(template.render(setup=setup,
                                          search_results=search_results,
                                          headers=headers))
