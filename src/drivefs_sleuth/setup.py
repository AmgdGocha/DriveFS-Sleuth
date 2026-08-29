"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/setup
Description: this module contains a class to represent an investigation.
"""

import os.path
import datetime
import threading
from queue import Queue
from enum import Enum
from collections import OrderedDict

from drivefs_sleuth.utils import get_last_pid
from drivefs_sleuth.utils import get_item_info
from drivefs_sleuth.utils import get_last_sync
from drivefs_sleuth.utils import parse_protobuf
from drivefs_sleuth.utils import get_max_root_ids
from drivefs_sleuth.utils import get_deleted_items
from drivefs_sleuth.utils import get_mirrored_items
from drivefs_sleuth.utils import get_item_properties
from drivefs_sleuth.utils import get_thumbnails_paths
from drivefs_sleuth.utils import get_target_stable_id
from drivefs_sleuth.utils import get_connected_devices
from drivefs_sleuth.utils import get_parent_relationships
from drivefs_sleuth.utils import get_content_caches_paths
from drivefs_sleuth.utils import get_file_content_cache_path
from drivefs_sleuth.utils import get_shared_with_me_without_link
from drivefs_sleuth.utils import get_mirroring_roots_for_account

from drivefs_sleuth.synced_files_tree import File
from drivefs_sleuth.synced_files_tree import Link
from drivefs_sleuth.synced_files_tree import Directory
from drivefs_sleuth.synced_files_tree import DummyItem
from drivefs_sleuth.synced_files_tree import MirrorItem
from drivefs_sleuth.synced_files_tree import SyncedFilesTree

from drivefs_sleuth.tasks import get_accounts


class StorageDestinations(Enum):
    DRIVE = "DRIVE"
    PHOTOS = "PHOTOS"


class Account:
    def __init__(self, drivefs_path, account_id, email, is_logged_in, mirroring_roots, properties):
        self.__profile_path = os.path.join(drivefs_path, account_id)
        self.__account_id = account_id
        self.__account_email = email
        self.__is_logged_in = is_logged_in
        self.__synced_files_tree = None
        if is_logged_in:
            self._construct_synced_files_trees()
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
        self.__name = properties['name']
        self.__photo_url = properties['photo_url']

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

    def get_name(self):
        return self.__name

    def get_photo_url(self):
        return self.__photo_url

    def _construct_synced_files_trees(self):
        parent_relationships = get_parent_relationships(self.__profile_path)
        root_info = get_item_info(self.__profile_path, parent_relationships[0][0])
        root = Directory(root_info[1], root_info[2], root_info[3], root_info[4], root_info[5], root_info[6],
                         root_info[7], root_info[8], root_info[9],
                         get_item_properties(self.__profile_path, root_info[1]), root_info[3], root_info[10])
        self.__synced_files_tree = SyncedFilesTree(root)

        content_caches_paths = get_content_caches_paths(os.path.join(self.__profile_path, 'content_cache'))
        thumbnails_paths = get_thumbnails_paths(os.path.join(self.__profile_path, 'thumbnails_cache'))

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
                        self.__synced_files_tree.add_deleted_item(DummyItem(parent_id))
                    else:
                        current_parent_dir = Directory(parent_info[1], parent_info[2], parent_info[3], parent_info[4],
                                                       parent_info[5], parent_info[6], parent_info[7], parent_info[8],
                                                       parent_info[9], get_item_properties(self.__profile_path,
                                                                                           parent_id), parent_info[3],
                                                       parent_info[10])
                        if parent_info[9] == 1:
                            self.__synced_files_tree.add_recovered_deleted_item(current_parent_dir)
                        orphan_dirs[parent_id] = current_parent_dir

            for child_id in childs_ids:
                child_info = get_item_info(self.__profile_path, child_id)
                child_properties = get_item_properties(self.__profile_path, child_id)

                if not child_info:
                    self.__synced_files_tree.add_deleted_item(DummyItem(child_id))
                    continue

                if child_info[0] == 0:
                    content_cache_path = get_file_content_cache_path(
                        child_properties.get('content-entry', None), content_caches_paths)
                    thumbnail_path = thumbnails_paths.get(str(child_info[1]), '')
                    child_file = File(child_info[1], child_info[2], child_info[3], child_info[4], child_info[5],
                                      child_info[6], child_info[7], child_info[8], child_info[9], child_properties,
                                      f'{current_parent_dir.tree_path}\\{child_info[3]}', content_cache_path,
                                      thumbnail_path, child_info[10])
                    current_parent_dir.add_item(child_file)
                    if child_info[9] == 1:
                        self.__synced_files_tree.add_recovered_deleted_item(child_file)
                    if content_cache_path:
                        self.__synced_files_tree.add_recoverable_item_from_cache(child_file)
                    if thumbnail_path:
                        self.__synced_files_tree.add_thumbnail_item(child_file)
                else:
                    if child_info[4] == 'application/vnd.google-apps.shortcut':
                        target_stable_id = get_target_stable_id(self.__profile_path, child_info[1])
                        if target_stable_id:
                            target = orphan_dirs.get(target_stable_id, None)
                            if target:
                                added_dirs[target_stable_id] = target
                                del orphan_dirs[target_stable_id]

                            else:
                                target_info = get_item_info(self.__profile_path, target_stable_id)
                                if target_info:
                                    if target_info[0] == 0:
                                        content_cache_path = get_file_content_cache_path(
                                            child_properties.get('content-entry', None), content_caches_paths)
                                        thumbnail_path = thumbnails_paths.get(str(target_info[1]), '')
                                        target = File(target_info[1], target_info[2], target_info[3], target_info[4],
                                                      target_info[5], target_info[6], target_info[7], target_info[8],
                                                      target_info[9],
                                                      get_item_properties(self.__profile_path, target_info[1]),
                                                      f'{current_parent_dir.tree_path}\\{target_info[3]}',
                                                      content_cache_path, thumbnail_path, target_info[10])
                                        if content_cache_path:
                                            self.__synced_files_tree.add_recoverable_item_from_cache(target)
                                        if thumbnail_path:
                                            self.__synced_files_tree.add_thumbnail_item(target)
                                    else:
                                        target = Directory(target_info[1], target_info[2], target_info[3],
                                                           target_info[4], target_info[5], target_info[6],
                                                           target_info[7], target_info[8], target_info[9],
                                                           get_item_properties(self.__profile_path, target_info[1]),
                                                           f'{current_parent_dir.tree_path}\\{target_info[3]}',
                                                           target_info[10])
                                        added_dirs[target_stable_id] = target
                                        if target_info[9] == 1:
                                            self.__synced_files_tree.add_recovered_deleted_item(target)
                                else:
                                    target = DummyItem(target_stable_id)
                                    self.__synced_files_tree.add_deleted_item(target)

                            child = Link(child_info[1], child_info[2], child_info[3], child_info[4], child_info[5],
                                         child_info[6], child_info[7], child_info[8], child_info[9], child_properties,
                                         f'{current_parent_dir.tree_path}\\{child_info[3]}', target, child_info[10])
                        else:
                            target = DummyItem('-1')
                            child = Link(child_info[1], child_info[2], child_info[3], child_info[4], child_info[5],
                                         child_info[6], child_info[7], child_info[8], child_info[9], child_properties,
                                         f'{current_parent_dir.tree_path}\\{child_info[3]}', target, child_info[10])
                    else:
                        child = orphan_dirs.get(child_id, None)
                        if child:
                            child.tree_path = f'{current_parent_dir.tree_path}\\{child.local_title}'
                            del orphan_dirs[child_id]
                        else:
                            child = Directory(child_info[1], child_info[2], child_info[3], child_info[4], child_info[5],
                                              child_info[6], child_info[7], child_info[8], child_info[9],
                                              child_properties,
                                              f'{current_parent_dir.tree_path}\\{child_info[3]}', child_info[10])

                    added_dirs[child_id] = child
                    current_parent_dir.add_item(child)
                    if child_info[9] == 1:
                        self.__synced_files_tree.add_recovered_deleted_item(child)

        # TODO: check if I can add a link in the shared with me
        for shared_with_me_item_info in get_shared_with_me_without_link(self.__profile_path):
            shared_with_me_item_properties = get_item_properties(self.__profile_path, shared_with_me_item_info[1])

            if shared_with_me_item_info[0] == 0:
                content_cache_path = get_file_content_cache_path(
                    shared_with_me_item_properties.get('content-entry', None), content_caches_paths)
                thumbnail_path = thumbnails_paths.get(str(shared_with_me_item_info[1]), '')
                shared_with_me_file = File(shared_with_me_item_info[1], shared_with_me_item_info[2],
                                           shared_with_me_item_info[3], shared_with_me_item_info[4],
                                           shared_with_me_item_info[5], shared_with_me_item_info[6],
                                           shared_with_me_item_info[7], shared_with_me_item_info[8],
                                           shared_with_me_item_info[9], shared_with_me_item_properties,
                                           f'Shared with me\\{shared_with_me_item_info[3]}', content_cache_path,
                                           thumbnail_path, shared_with_me_item_info[10])
                self.__synced_files_tree.add_shared_with_me_item(shared_with_me_file)
                if content_cache_path:
                    self.__synced_files_tree.add_recoverable_item_from_cache(shared_with_me_file)
                if thumbnail_path:
                    self.__synced_files_tree.add_thumbnail_item(shared_with_me_file)
                if shared_with_me_item_info[9] == 1:
                    self.__synced_files_tree.add_recovered_deleted_item(shared_with_me_file)
            else:
                shared_with_me_item = orphan_dirs.get(shared_with_me_item_info[1], None)
                if shared_with_me_item:
                    del orphan_dirs[shared_with_me_item_info[1]]
                else:
                    shared_with_me_item = Directory(shared_with_me_item_info[1], shared_with_me_item_info[2],
                                                    shared_with_me_item_info[3], shared_with_me_item_info[4],
                                                    shared_with_me_item_info[5], shared_with_me_item_info[6],
                                                    shared_with_me_item_info[7], shared_with_me_item_info[8],
                                                    shared_with_me_item_info[9], shared_with_me_item_properties,
                                                    f'{current_parent_dir.tree_path}\\{shared_with_me_item_info[3]}',
                                                    shared_with_me_item_info[10])
                    if shared_with_me_item_info[9] == 1:
                        self.__synced_files_tree.add_recovered_deleted_item(shared_with_me_item)
                self.__synced_files_tree.add_shared_with_me_item(shared_with_me_item)

        for orphan_id, orphan_dir in orphan_dirs.items():
            self.__synced_files_tree.add_orphan_item(orphan_dir)

        mirrored_items = get_mirrored_items(self.__profile_path)
        for item in mirrored_items:
            self.__synced_files_tree.add_mirrored_item(
                MirrorItem(item[0], item[1], item[2], item[3], item[4], item[5], item[6], item[7], item[8], item[9],
                           item[10], item[11], item[12], item[13], item[14], item[15], item[16]
                           )
            )

        for deleted_item in get_deleted_items(self.__profile_path):
            parsed_buf = parse_protobuf(deleted_item[1])
            properties = {}
            for index, props in parsed_buf.items():
                if index == '55' or index.startswith('55-'):
                    for prop in props:
                        if isinstance(prop, dict):
                            properties[prop['1']] = prop[[key for key in prop.keys() if key != '1'][0]]
                        elif isinstance(prop, list):
                            for p in prop:
                                properties[p['1']] = p[[key for key in p.keys() if key != '1'][0]]
            if parsed_buf['4'] == 'application/vnd.google-apps.folder':
                self.__synced_files_tree.add_recovered_deleted_item(
                    Directory(deleted_item[0], parsed_buf.get('1', ''), parsed_buf.get('3', ''),
                              parsed_buf.get('4', ''), parsed_buf.get('63', 0), parsed_buf.get('14', 0),
                              parsed_buf.get('11', 0), parsed_buf.get('13', 0), parsed_buf.get('7', 1),
                              properties, parsed_buf.get('3', ''), deleted_item[1])
                )
            elif parsed_buf['4'] == 'application/vnd.google-apps.shortcut':
                target_item = None
                target_info = parsed_buf.get('132', None)
                if target_info:
                    target_item = self.__synced_files_tree.get_item_by_id(target_info['2'])
                self.__synced_files_tree.add_recovered_deleted_item(
                    Link(deleted_item[0], parsed_buf.get('1', ''), parsed_buf.get('3', ''), parsed_buf.get('4', ''),
                         parsed_buf.get('63', 0), parsed_buf.get('14', 0), parsed_buf.get('11', 0),
                         parsed_buf.get('13', 0), parsed_buf.get('7', 1), properties, parsed_buf.get('3', ''),
                         target_item, deleted_item[1])
                )
            else:
                content_cache_path = get_file_content_cache_path(
                    properties.get('content-entry', None), content_caches_paths)
                thumbnail_path = thumbnails_paths.get(str(deleted_item[0]), '')
                recovered_file = File(deleted_item[0], parsed_buf.get('1', ''), parsed_buf.get('3', ''),
                                      parsed_buf.get('4', ''), parsed_buf.get('63', 0), parsed_buf.get('14', 0),
                                      parsed_buf.get('11', 0), parsed_buf.get('13', 0), parsed_buf.get('7', 1),
                                      properties, parsed_buf.get('3', ''), content_cache_path, thumbnail_path,
                                      deleted_item[1])
                self.__synced_files_tree.add_recovered_deleted_item(recovered_file)
                if content_cache_path:
                    self.__synced_files_tree.add_recoverable_item_from_cache(recovered_file)
                if thumbnail_path:
                    self.__synced_files_tree.add_thumbnail_item(recovered_file)


class Setup:
    def __init__(self, drivefs_path, accounts=None):
        self.__drivefs_path = drivefs_path
        self.__last_sync_date = datetime.datetime.fromtimestamp(get_last_sync(drivefs_path), datetime.timezone.utc)
        self.__max_root_ids = get_max_root_ids(drivefs_path)
        self.__last_pid = get_last_pid(drivefs_path)
        self.__connected_devices = []

        for connected_device in get_connected_devices(drivefs_path):
            device = {
                "media_id": connected_device[0],
                "name": connected_device[1],
                "last_mount_point": connected_device[2],
                "ignore": connected_device[4],
            }
            if int(connected_device[3]) == -1:
                device["capacity"] = connected_device[3]
            else:
                device["capacity"] = round(int(connected_device[3]) / 1e+9, 2)

            self.__connected_devices.append(device)

        if not accounts:
            accounts = []
        self.__accounts = []

        account_queue = Queue()
        threads = []

        for account_id, account_info in get_accounts(drivefs_path).items():
            if accounts and not (account_id in accounts or account_info['email'] in accounts):
                continue

            thread = threading.Thread(
                target=self.__account_worker,
                args=(account_queue, account_id, account_info)
            )
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        while not account_queue.empty():
            self.__accounts.append(account_queue.get())

    def __account_worker(self, queue, account_id, account_info):
        account = Account(self.__drivefs_path, account_id, account_info['email'], account_info['logged_in'],
                          get_mirroring_roots_for_account(self.__drivefs_path, account_id), account_info['properties'])
        queue.put(account)

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
