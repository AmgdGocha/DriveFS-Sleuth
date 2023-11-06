import os
import re
import sys
import sqlite3
from collections import OrderedDict
from jinja2 import Template
from drivefs_sleuth.utils import get_item_info
from drivefs_sleuth.utils import get_synced_files
from drivefs_sleuth.utils import get_parent_relationships
from drivefs_sleuth.synced_files_tree import File
from drivefs_sleuth.synced_files_tree import Directory
from drivefs_sleuth.synced_files_tree import SyncedFilesTree


def get_logged_in_accounts(drivefs_path):
    accounts = {}
    # TODO: what if there is no directory with the numbers
    for subdir in os.listdir(drivefs_path):
        if subdir.isdigit():
            accounts[subdir] = ''

    # TODO: what if the logs are not there
    logs_dir = os.path.join(drivefs_path, "Logs")
    for _, _, files in os.walk(logs_dir):
        for file in files:
            if file.startswith("drive_fs") and file.endswith(".txt"):
                with open(os.path.join(logs_dir, file), 'r') as log_file:
                    logs = log_file.read()
                    for account_id in accounts.keys():
                        match = re.search(r"([\w\.-]+@[\w\.-]+\.\w+) \(" + account_id + r"\)", logs)
                        if match:
                            accounts[account_id] = match.group(1)

    return accounts


# TODO: complete after finalizing the roots research
def get_connected_devices(drivefs_path):
    root_preference_db = sqlite3.connect(os.path.join(drivefs_path, "root_preference_sqlite.db"))
    cursor = root_preference_db.cursor()
    cursor.execute("SELECT * FROM media")
    connected_devices = cursor.fetchall()

    for connected_device in connected_devices:
        print(connected_device)


def __construct_synced_files_tree(synced_files_tree, parent_relationships, drivefs_path, account_id):
    parent_relationships_dict = OrderedDict()
    for parent, child in parent_relationships:
        if parent not in parent_relationships_dict.keys():
            parent_relationships_dict[parent] = []

        parent_relationships_dict[parent].append(child)

    added_dirs = {synced_files_tree.get_root().get_stable_id(): synced_files_tree.get_root()}
    orphan_dirs = {}
    last_added_dir = synced_files_tree.get_root()

    for parent_id, childs_ids in parent_relationships_dict.items():

        if parent_id != last_added_dir.get_stable_id():
            if parent_id in added_dirs:
                last_added_dir = added_dirs[parent_id]
            elif parent_id in orphan_dirs:
                last_added_dir = orphan_dirs[parent_id]
            else:
                parent_info = get_item_info(drivefs_path, account_id, parent_id)
                # handle is_owner == 0
                if not parent_info:
                    synced_files_tree.add_deleted_item(parent_id)
                else:
                    last_added_dir = Directory(parent_info[1], parent_info[2], parent_info[3], parent_info[4],
                                               parent_info[5], parent_info[6], parent_info[7], parent_info[8])

                    orphan_dirs[parent_id] = last_added_dir

        for child_id in childs_ids:
            child_info = get_item_info(drivefs_path, account_id, child_id)
            if not child_info:
                synced_files_tree.add_deleted_item(child_id)
                continue

            if child_info[0] == 0:
                last_added_dir.add_item(
                    File(child_info[1], child_info[2], child_info[3], child_info[4], child_info[5], child_info[6],
                         child_info[7], child_info[8])
                )
            else:
                child = orphan_dirs.get(child_id, None)
                if child:
                    del orphan_dirs[child_id]
                if not child:
                    child = Directory(child_info[1], child_info[2], child_info[3], child_info[4], child_info[5],
                                      child_info[6], child_info[7], child_info[8])

                added_dirs[child_id] = child
                last_added_dir.add_item(child)

    for orphan_id, orphan_dir in orphan_dirs.items():
        synced_files_tree.add_orphan_item(orphan_dir)


# TODO: check orphan items from the synced_files
def construct_synced_files_trees(drivefs_path):
    synced_trees = []
    syncing_accounts = get_logged_in_accounts(drivefs_path)
    for account_id, account_email in syncing_accounts.items():
        parent_relationships = get_parent_relationships(drivefs_path, account_id)
        root_info = get_item_info(drivefs_path, account_id, parent_relationships[0][0])
        synced_files_tree = SyncedFilesTree(root_info, account_id, account_email)
        __construct_synced_files_tree(synced_files_tree, parent_relationships, drivefs_path, account_id)
        synced_trees.append(synced_files_tree)

    return synced_trees


def generate_html_report(synced_files):
    template = """
        <html>
        <head>
            <script>
                function toggleCollapse(id) {
                    var x = document.getElementById(id);
                    if (x.style.display === "none") {
                        x.style.display = "block";
                    } else {
                        x.style.display = "none";
                    }
                }
            </script>
        </head>
        <body>
            <ul>
                {% for item in nested_lists %}
                    <li>
                        {% if item is iterable and item is not string %}
                            <a href="javascript:void(0);" onclick="toggleCollapse('list_{{ loop.index }}')">[+]</a>
                            {{ loop.index }}
                            <ul id="list_{{ loop.index }}" style="display: none;">
                                {% for sub_item in item %}
                                    <li>
                                        {% if sub_item is iterable and sub_item is not string %}
                                            <a href="javascript:void(0);" onclick="toggleCollapse('sublist_{{ loop.index }}_{{ loop.index0 }}')">[+]</a>
                                            {{ loop.index0 }}
                                            <ul id="sublist_{{ loop.index }}_{{ loop.index0 }}" style="display: none;">
                                                {% for sub_sub_item in sub_item %}
                                                    <li>{{ sub_sub_item }}</li>
                                                {% endfor %}
                                            </ul>
                                        {% else %}
                                            {{ sub_item }}
                                        {% endif %}
                                    </li>
                                {% endfor %}
                            </ul>
                        {% else %}
                            {{ item }}
                        {% endif %}
                    </li>
                {% endfor %}
            </ul>
        </body>
        </html>
        """

    template = Template(template)
    return template.render(nested_lists=synced_files)

# tree = construct_synced_files_tree("C:\\Users\\Amged Wageh\\AppData\\Local\\Google\\DriveFS", "108658046744402996075")
# tree = construct_synced_files_tree("C:\\Amged\\Incidents\\DriveFS\\Triage\\ry-lp-223350a\\DriveFS", "106203366528331438369")
# accounts = get_logged_in_accounts("C:\\Users\\Amged Wageh\\AppData\\Local\\Google\\DriveFS")
# print(accounts)
synced_trees = construct_synced_files_trees("C:\\Users\\Amged Wageh\\AppData\\Local\\Google\\DriveFS")
for tree in synced_trees:
    tree.print_synced_files_tree()
# print(f'Orphans = {len(tree.get_orphan_items())}')
# html_report = generate_html_report([tree.get_root()] + tree.get_orphan_items())
# print('Report Generated.')
# with open("synced_files_tree.html", "w") as file:
#     file.write(html_report)
# print("Report Saved")
