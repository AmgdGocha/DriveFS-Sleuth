import datetime
from enum import Enum
from drivefs_sleuth.tasks import get_logged_in_accounts
from drivefs_sleuth.tasks import construct_synced_files_trees
from drivefs_sleuth.utils import get_connected_devices
from drivefs_sleuth.utils import get_max_root_ids
from drivefs_sleuth.utils import get_last_sync
from drivefs_sleuth.utils import get_last_pid
from drivefs_sleuth.utils import get_mirroring_roots
from drivefs_sleuth.tasks import generate_html_report


class StorageDestinations(Enum):
    DRIVE = "DRIVE"
    PHOTOS = "PHOTOS"


class Profile:
    def __init__(self, drivefs_path):
        self.__drivefs_path = drivefs_path
        # TODO: handle if more than account are logged in
        # TODO: handle if there is no logged in account
        self.__account_id, self.__account_email = list(get_logged_in_accounts(drivefs_path).items())[0]
        self.__synced_trees = construct_synced_files_trees(drivefs_path)
        self.__last_sync_date = datetime.datetime.fromtimestamp(get_last_sync(drivefs_path), datetime.timezone.utc)
        self.__last_pid = get_last_pid(drivefs_path)
        self.__max_root_ids = get_max_root_ids(drivefs_path)

        self.__connected_devices = []
        for connected_device in get_connected_devices(drivefs_path):
            self.__connected_devices.append({
                "media_id": connected_device[0],
                "name": connected_device[1],
                "last_mount_point": connected_device[2],
                "capacity": connected_device[3],
                "ignore": connected_device[4],
            })

        self.__mirroring_roots = {}
        for mirror_root in get_mirroring_roots(drivefs_path):
            if mirror_root[0] not in self.__mirroring_roots:
                self.__mirroring_roots[mirror_root[0]] = []

            mirror_info = {
                'root_id': mirror_root[1],
                'media_id': mirror_root[2],
                'title': mirror_root[3],
                'root_path': mirror_root[4],
                'sync_type': mirror_root[5],
                # 'destination': mirror_root[6],
                'last_seen_absolute_path': mirror_root[7],
            }
            if mirror_root[5] == 1:
                mirror_info['destination'] = StorageDestinations.DRIVE.value
            else:
                mirror_info['destination'] = StorageDestinations.PHOTOS.value

            self.__mirroring_roots[mirror_root[0]].append(mirror_info)

    def get_drivefs_path(self):
        return self.__drivefs_path

    def get_account_id(self):
        return self.__account_id

    def get_account_email(self):
        return self.__account_email

    def get_connected_devices(self):
        return self.__connected_devices

    def get_last_sync_date(self):
        return self.__last_sync_date

    def get_synced_trees(self):
        return self.__synced_trees

    def get_last_pid(self):
        return self.__last_pid

    def get_max_root_ids(self):
        return self.__max_root_ids

    def get_mirroring_roots(self):
        return self.__mirroring_roots

    # TODO: handle if no max ides or roots
    def is_mirroring_roots_modified(self):
        return False if self.get_max_root_ids() == sum(len(roots) for roots in self.get_mirroring_roots().values()) \
            else True


profile = Profile("C:\\Users\\Amged Wageh\\AppData\\Local\\Google\\DriveFS")
generate_html_report(profile)
# synced_trees = profile.get_synced_trees()
# print('~~~~SEARCHING THE TREE~~~~')
# for tree in synced_trees:
#     tree.print_synced_files_tree()
#     generate_html_report(profile.get_account_email(), [tree.get_root()] + tree.get_orphan_items())
#     items = tree.search_item_by_name('files_215.zip')
#     for item in items:
#         print(f'{item.local_title} - {item.tree_path}')
#
# print(f"Gmail Account: {profile.get_account_email()}")
# print(f"Last Sync: {profile.get_last_sync_date()}")


