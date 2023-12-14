import sqlite3
from collections import OrderedDict
from jinja2 import Environment
from jinja2 import FileSystemLoader
from drivefs_sleuth.utils import get_item_info
from drivefs_sleuth.utils import get_account_ids
from drivefs_sleuth.utils import lookup_account_id
from drivefs_sleuth.utils import get_item_properties
from drivefs_sleuth.utils import get_properties_list
from drivefs_sleuth.utils import get_target_stable_id
from drivefs_sleuth.utils import get_available_profiles
from drivefs_sleuth.utils import get_parent_relationships
from drivefs_sleuth.utils import get_shared_with_me_without_link
from drivefs_sleuth.synced_files_tree import File
from drivefs_sleuth.synced_files_tree import Link
from drivefs_sleuth.synced_files_tree import Directory
from drivefs_sleuth.synced_files_tree import SyncedFilesTree


# TODO handle if there are multiple logged-in accounts
# def get_logged_in_accounts(drivefs_path):
#     accounts = {}
#     # TODO: what if there is no directory with the numbers
#     for subdir in os.listdir(drivefs_path):
#         if subdir.isdigit():
#             accounts[subdir] = ''
#
#     # TODO: what if the logs are not there
#     logs_dir = os.path.join(drivefs_path, "Logs")
#     for _, _, files in os.walk(logs_dir):
#         for file in files:
#             if file.startswith("drive_fs") and file.endswith(".txt"):
#                 with open(os.path.join(logs_dir, file), 'r') as log_file:
#                     logs = log_file.read()
#                     for account_id in accounts.keys():
#                         match = re.search(r"([\w\.-]+@[\w\.-]+\.\w+) \(" + account_id + r"\)", logs)
#                         if match:
#                             accounts[account_id] = match.group(1)
#
#     return accounts

def get_accounts(drivefs_path):
    accounts = {}
    experiments_ids = get_account_ids(drivefs_path)
    profiles = get_available_profiles(drivefs_path)
    for account_id in experiments_ids:
        accounts[account_id] = {
            'logged_in': account_id in profiles,
            'email': lookup_account_id(drivefs_path, account_id)
        }
    return accounts


#
# def build_items_db(drivefs_path, account_id, tree):
#     with sqlite3.connect('items_db') as items_db:
#         cursor = items_db.cursor()
#         properties = get_properties_list(drivefs_path, account_id)
#
#         cursor.execute('''
#             CREATE TABLE items (
#                 item_id INTEGER PRIMARY KEY,
#                 url_id TEXT NOT NULL,
#                 local_title TEXT,
#                 mime_type TEXT,
#                 is_owner TEXT,
#                 file_size TEXT,
#                 modified_date TEXT,
#                 viewed_by_me_date TEXT,
#                 trashed TEXT,
#                 tree_path TEXT
#             )
#         ''')
#
#         item_values = (1, 'example_url_id', 'Example Title', 'text/plain', 'true', '1024', '2023-11-22', '2023-11-22', 'false', '/example/path')
#
#         cursor.execute('''
#             INSERT INTO items (item_id, url_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date, trashed, tree_path)
#             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
#         ''', item_values)
#
#         items_db.commit()


# TODO: apply the new changes (no profile)
def generate_html_report(profile, search_results=None):
    if search_results is None:
        search_results = []
    env = Environment(loader=FileSystemLoader("html_resources/"))
    template = env.get_template("report_template.html")
    headers = ['id', 'type', 'url_id', 'title', 'mime_type', 'is_owner', 'file_size', 'modified_date',
              'viewed_by_me_date', 'trashed', 'tree_path'] + get_properties_list(
        profile.get_drivefs_path(), profile.get_account_id())
    with open("report.html", 'w', encoding='utf-8') as report_file:
        for tree in profile.get_synced_trees():
            report_file.write(template.render(profile=profile,
                                              tree=tree,
                                              search_results=search_results,
                                              headers=headers))

