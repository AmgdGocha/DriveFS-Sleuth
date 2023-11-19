import os
import re
from collections import OrderedDict
from jinja2 import Environment
from jinja2 import FileSystemLoader
from drivefs_sleuth.utils import get_item_info
from drivefs_sleuth.utils import get_synced_files
from drivefs_sleuth.utils import get_item_properties
from drivefs_sleuth.utils import get_parent_relationships
from drivefs_sleuth.utils import get_target_stable_id
from drivefs_sleuth.synced_files_tree import File
from drivefs_sleuth.synced_files_tree import Link
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


def __construct_synced_files_tree(synced_files_tree, parent_relationships, drivefs_path, account_id):
    parent_relationships_dict = OrderedDict()
    for parent, child in parent_relationships:
        if parent not in parent_relationships_dict.keys():
            parent_relationships_dict[parent] = []

        parent_relationships_dict[parent].append(child)

    added_dirs = {synced_files_tree.get_root().get_stable_id(): synced_files_tree.get_root()}
    orphan_dirs = {}
    current_parent_dir = synced_files_tree.get_root()

    for parent_id, childs_ids in parent_relationships_dict.items():

        if parent_id != current_parent_dir.get_stable_id():
            if parent_id in added_dirs:
                current_parent_dir = added_dirs[parent_id]
            elif parent_id in orphan_dirs:
                current_parent_dir = orphan_dirs[parent_id]
            else:
                parent_info = get_item_info(drivefs_path, account_id, parent_id)
                # handle is_owner == 0
                if not parent_info:
                    # TODO handle the parent in the tree when the parent is deleted, maybe creating a dummy parent
                    synced_files_tree.add_deleted_item(parent_id)
                else:
                    current_parent_dir = Directory(parent_info[1], parent_info[2], parent_info[3], parent_info[4],
                                                   parent_info[5], parent_info[6], parent_info[7], parent_info[8],
                                                   parent_info[9], get_item_properties(drivefs_path, account_id,
                                                                                       parent_id), parent_info[3])
                    orphan_dirs[parent_id] = current_parent_dir

        for child_id in childs_ids:
            child_info = get_item_info(drivefs_path, account_id, child_id)
            if not child_info:
                synced_files_tree.add_deleted_item(child_id)
                continue

            if child_info[0] == 0:
                current_parent_dir.add_item(
                    File(child_info[1], child_info[2], child_info[3], child_info[4], child_info[5], child_info[6],
                         child_info[7], child_info[8], child_info[9],
                         get_item_properties(drivefs_path, account_id, child_id),
                         f'{current_parent_dir.tree_path}\\{child_info[3]}')
                )
            else:
                if child_info[4] == 'application/vnd.google-apps.shortcut':
                    target_stable_id = get_target_stable_id(drivefs_path, account_id, child_info[1])
                    if target_stable_id:
                        target = orphan_dirs.get(target_stable_id, None)
                        if target:
                            del orphan_dirs[target_stable_id]

                        else:
                            target_info = get_item_info(drivefs_path, account_id, target_stable_id)
                            target = Directory(target_info[1], target_info[2], target_info[3], target_info[4],
                                               target_info[5], target_info[6], target_info[7], target_info[8],
                                               target_info[9], get_item_properties(drivefs_path, account_id, child_id),
                                               f'{current_parent_dir.tree_path}\\{target_info[3]}')

                        child = Link(child_info[1], child_info[2], child_info[3], child_info[4], child_info[5],
                                     child_info[6], child_info[7], child_info[8], child_info[9],
                                     get_item_properties(drivefs_path, account_id, child_id),
                                     f'{current_parent_dir.tree_path}\\{child_info[3]}', target)
                        added_dirs[target_stable_id] = target
                    else:
                        # TODO what if there is no target info, maybe create a dummy target
                        pass
                else:
                    child = orphan_dirs.get(child_id, None)
                    if child:
                        child.tree_path = f'{current_parent_dir.tree_path}\\{child.local_title}'
                        del orphan_dirs[child_id]
                    else:
                        child = Directory(child_info[1], child_info[2], child_info[3], child_info[4], child_info[5],
                                          child_info[6], child_info[7], child_info[8], child_info[9],
                                          get_item_properties(drivefs_path, account_id, child_id),
                                          f'{current_parent_dir.tree_path}\\{child_info[3]}')

                added_dirs[child_id] = child
                current_parent_dir.add_item(child)

    for orphan_id, orphan_dir in orphan_dirs.items():
        synced_files_tree.add_orphan_item(orphan_dir)


# TODO: check orphan items from the synced_files
def construct_synced_files_trees(drivefs_path):
    synced_trees = []
    syncing_accounts = get_logged_in_accounts(drivefs_path)
    for account_id, account_email in syncing_accounts.items():
        parent_relationships = get_parent_relationships(drivefs_path, account_id)
        root_info = get_item_info(drivefs_path, account_id, parent_relationships[0][0])
        root = Directory(root_info[1], root_info[2], root_info[3], root_info[4], root_info[5], root_info[6],
                         root_info[7], root_info[8], root_info[9],
                         get_item_properties(drivefs_path, account_id, root_info[1]), root_info[3])
        synced_files_tree = SyncedFilesTree(root)
        __construct_synced_files_tree(synced_files_tree, parent_relationships, drivefs_path, account_id)
        synced_trees.append(synced_files_tree)

    return synced_trees


def generate_html_report(profile):
    env = Environment(loader=FileSystemLoader("html_resources/"))
    template = env.get_template("report_template.html")
    with open("report.html", 'w', encoding='utf-8') as report_file:
        for tree in profile.get_synced_trees():
            report_file.write(template.render(account_email=profile.get_account_email(),
                                              account_id=profile.get_account_id(),
                                              last_sync_datetime=profile.get_last_sync_date(),
                                              last_pid=profile.get_last_pid(),
                                              items=[tree.get_root()] + tree.get_orphan_items()))


