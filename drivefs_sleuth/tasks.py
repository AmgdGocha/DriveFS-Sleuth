import os

from jinja2 import Environment
from jinja2 import FileSystemLoader

from drivefs_sleuth.utils import get_account_ids
from drivefs_sleuth.utils import lookup_account_id
from drivefs_sleuth.utils import get_properties_list
from drivefs_sleuth.utils import get_available_profiles


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


# TODO: properly handle the headers (remove extra properties per account)
def generate_html_report(setup, search_results=None):
    if search_results is None:
        search_results = {}
    env = Environment(loader=FileSystemLoader("html_resources/"))
    template = env.get_template("report_template.html")
    headers = ['id', 'type', 'url_id', 'title', 'mime_type', 'is_owner', 'file_size', 'modified_date',
               'viewed_by_me_date', 'trashed', 'tree_path']
    for account in setup.get_accounts():
        headers += get_properties_list(os.path.join(setup.get_drivefs_path(), account.get_account_id()))

    with open("report.html", 'w', encoding='utf-8') as report_file:
        report_file.write(template.render(setup=setup,
                                          search_results=search_results,
                                          headers=list(set(headers))))


from drivefs_sleuth.utils import get_mirroring_roots_for_account
from drivefs_sleuth.setup import Account, Setup

# drivefs_path = 'C:\\Amged\\Private\\Research\\DriveFS_Forensics\\2ed_login\\DriveFS'
# drivefs_path = 'C:\\Users\\Amged Wageh\\AppData\\Local\\Google\DriveFS'
# accounts = []
# for account_id, account_info in get_accounts(drivefs_path).items():
#     accounts.append(
#         Account(
#             drivefs_path,
#             account_id,
#             account_info['email'],
#             account_info['logged_in'],
#             get_mirroring_roots_for_account(drivefs_path, account_id)
#         ))
# setup = Setup(drivefs_path, accounts)
# generate_html_report(setup)
