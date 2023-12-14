import datetime
import os.path
from enum import Enum
from collections import OrderedDict

from drivefs_sleuth.utils import get_last_pid, get_target_stable_id, get_shared_with_me_without_link
from drivefs_sleuth.utils import get_item_info
from drivefs_sleuth.utils import get_last_sync
from drivefs_sleuth.utils import get_max_root_ids
from drivefs_sleuth.utils import get_item_properties
from drivefs_sleuth.utils import get_connected_devices
from drivefs_sleuth.utils import get_parent_relationships

from drivefs_sleuth.synced_files_tree import File
from drivefs_sleuth.synced_files_tree import Link
from drivefs_sleuth.synced_files_tree import Directory
from drivefs_sleuth.synced_files_tree import SyncedFilesTree


class StorageDestinations(Enum):
    DRIVE = "DRIVE"
    PHOTOS = "PHOTOS"


class Account:
    def __init__(self, drivefs_path, account_id, email, is_logged_in, mirroring_roots):
        self.__profile_path = os.path.join(drivefs_path, account_id)
        self.__account_id = account_id
        self.__account_email = email
        self.__is_logged_in = is_logged_in
        self.__synced_files_tree = None
        if is_logged_in:
            self.construct_synced_files_trees()
        # TODO: enrich the roots from the mirror_sqlite.db
        self.__mirroring_roots = []
        for mirroring_root in mirroring_roots:
            mirroring_root_info = {
                'root_id': mirroring_root[1],
                'media_id': mirroring_root[2],
                'title': mirroring_root[3],
                'root_path': mirroring_root[4],
                'sync_type': mirroring_root[5],
                'last_seen_absolute_path': mirroring_root[7],
            }
            if mirroring_root[6] == 1:
                mirroring_root_info['destination'] = StorageDestinations.DRIVE.value
            else:
                mirroring_root_info['destination'] = StorageDestinations.PHOTOS.value

            self.__mirroring_roots.append(mirroring_root_info)

    def get_profile_path(self):
        return self.__profile_path

    def get_account_id(self):
        return self.__account_id

    def get_account_email(self):
        return self.__account_email

    def is_logged_in(self):
        return self.__is_logged_in

    def get_synced_files_tree(self):
        return self.__synced_files_tree

    def get_mirroring_roots(self):
        return self.__mirroring_roots

    def construct_synced_files_trees(self):
        parent_relationships = get_parent_relationships(self.__profile_path)
        root_info = get_item_info(self.__profile_path, parent_relationships[0][0])
        root = Directory(root_info[1], root_info[2], root_info[3], root_info[4], root_info[5], root_info[6],
                         root_info[7], root_info[8], root_info[9],
                         get_item_properties(self.__profile_path, root_info[1]), root_info[3])
        self.__synced_files_tree = SyncedFilesTree(root)

        parent_relationships_dict = OrderedDict()
        for parent, child in parent_relationships:
            if parent not in parent_relationships_dict.keys():
                parent_relationships_dict[parent] = []

            parent_relationships_dict[parent].append(child)

        added_dirs = {self.__synced_files_tree.get_root().get_stable_id(): self.__synced_files_tree.get_root()}
        orphan_dirs = {}
        current_parent_dir = self.__synced_files_tree.get_root()

        for parent_id, childs_ids in parent_relationships_dict.items():

            if parent_id != current_parent_dir.get_stable_id():
                if parent_id in added_dirs:
                    current_parent_dir = added_dirs[parent_id]
                elif parent_id in orphan_dirs:
                    current_parent_dir = orphan_dirs[parent_id]
                else:
                    parent_info = get_item_info(self.__profile_path, parent_id)
                    if not parent_info:
                        # TODO handle the parent in the tree when the parent is deleted, maybe creating a dummy parent
                        self.__synced_files_tree.add_deleted_item(parent_id)
                    else:
                        current_parent_dir = Directory(parent_info[1], parent_info[2], parent_info[3], parent_info[4],
                                                       parent_info[5], parent_info[6], parent_info[7], parent_info[8],
                                                       parent_info[9], get_item_properties(self.__profile_path,
                                                                                           parent_id), parent_info[3])
                        orphan_dirs[parent_id] = current_parent_dir

            for child_id in childs_ids:
                child_info = get_item_info(self.__profile_path, child_id)
                if not child_info:
                    self.__synced_files_tree.add_deleted_item(child_id)
                    continue

                if child_info[0] == 0:
                    current_parent_dir.add_item(
                        File(child_info[1], child_info[2], child_info[3], child_info[4], child_info[5], child_info[6],
                             child_info[7], child_info[8], child_info[9],
                             get_item_properties(self.__profile_path, child_id),
                             f'{current_parent_dir.tree_path}\\{child_info[3]}')
                    )
                else:
                    if child_info[4] == 'application/vnd.google-apps.shortcut':
                        target_stable_id = get_target_stable_id(self.__profile_path, child_info[1])
                        if target_stable_id:
                            target = orphan_dirs.get(target_stable_id, None)
                            if target:
                                del orphan_dirs[target_stable_id]

                            else:
                                target_info = get_item_info(self.__profile_path, target_stable_id)
                                target = Directory(target_info[1], target_info[2], target_info[3], target_info[4],
                                                   target_info[5], target_info[6], target_info[7], target_info[8],
                                                   target_info[9], get_item_properties(self.__profile_path, child_id),
                                                   f'{current_parent_dir.tree_path}\\{target_info[3]}')

                            child = Link(child_info[1], child_info[2], child_info[3], child_info[4], child_info[5],
                                         child_info[6], child_info[7], child_info[8], child_info[9],
                                         get_item_properties(self.__profile_path, child_id),
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
                                              get_item_properties(self.__profile_path, child_id),
                                              f'{current_parent_dir.tree_path}\\{child_info[3]}')

                    added_dirs[child_id] = child
                    current_parent_dir.add_item(child)

        # TODO: check if I can add a link in the shared with me
        for shared_with_me_item_info in get_shared_with_me_without_link(self.__profile_path):
            if shared_with_me_item_info[0] == 0:
                self.__synced_files_tree.add_shared_with_me_item(
                    File(shared_with_me_item_info[1], shared_with_me_item_info[2], shared_with_me_item_info[3],
                         shared_with_me_item_info[4], shared_with_me_item_info[5], shared_with_me_item_info[6],
                         shared_with_me_item_info[7], shared_with_me_item_info[8], shared_with_me_item_info[9],
                         get_item_properties(self.__profile_path, shared_with_me_item_info[1]),
                         f'Shared with me\\{shared_with_me_item_info[3]}')
                )
            else:
                shared_with_me_item = orphan_dirs.get(shared_with_me_item_info[1], None)
                if shared_with_me_item:
                    del orphan_dirs[shared_with_me_item_info[1]]
                else:
                    shared_with_me_item = Directory(shared_with_me_item_info[1], shared_with_me_item_info[2],
                                                    shared_with_me_item_info[3], shared_with_me_item_info[4],
                                                    shared_with_me_item_info[5], shared_with_me_item_info[6],
                                                    shared_with_me_item_info[7], shared_with_me_item_info[8],
                                                    shared_with_me_item_info[9],
                                                    get_item_properties(
                                                        self.__profile_path, shared_with_me_item_info[1]),
                                                    f'{current_parent_dir.tree_path}\\{shared_with_me_item_info[3]}')
                self.__synced_files_tree.add_shared_with_me_item(shared_with_me_item)

        for orphan_id, orphan_dir in orphan_dirs.items():
            self.__synced_files_tree.add_orphan_item(orphan_dir)


class Setup:
    def __init__(self, drivefs_path, accounts):
        self.__drivefs_path = drivefs_path
        self.__accounts = accounts
        self.__last_sync_date = datetime.datetime.fromtimestamp(get_last_sync(drivefs_path), datetime.timezone.utc)
        self.__max_root_ids = get_max_root_ids(drivefs_path)
        self.__last_pid = get_last_pid(drivefs_path)
        self.__connected_devices = []
        for connected_device in get_connected_devices(drivefs_path):
            self.__connected_devices.append({
                "media_id": connected_device[0],
                "name": connected_device[1],
                "last_mount_point": connected_device[2],
                "capacity": round(int(connected_device[3]) / 1e+9, 2),
                "ignore": connected_device[4],
            })

    def get_drivefs_path(self):
        return self.__drivefs_path

    def get_accounts(self):
        return self.__accounts

    def get_last_sync_date(self):
        return self.__last_sync_date

    def get_max_root_ids(self):
        return self.__max_root_ids

    def get_last_pid(self):
        return self.__last_pid

    def get_connected_devices(self):
        return self.__connected_devices

    def is_mirroring_roots_modified(self):
        return False if not self.get_max_root_ids() or self.get_max_root_ids() == sum(
            [len(account.get_mirroring_roots()) for account in self.get_accounts()]) else True


