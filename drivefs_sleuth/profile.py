from drivefs_sleuth.tasks import get_logged_in_accounts
from drivefs_sleuth.tasks import get_connected_devices
from drivefs_sleuth.tasks import construct_synced_files_trees


class Profile:
    def __init__(self, drivefs_path):
        self.__drivefs_path = drivefs_path
        # TODO: handle if more than account are logged in
        self.__account_id, self.__account_email = list(get_logged_in_accounts(drivefs_path).items())[0]
        # TODO: reformat the connected devices
        self.__connected_devices = get_connected_devices(drivefs_path)
        self.__synced_trees = construct_synced_files_trees(drivefs_path)

    def get_drivefs_path(self):
        return self.__drivefs_path

    def get_account_id(self):
        return self.__account_id

    def get_account_email(self):
        return self.__account_email

    def get_connected_devices(self):
        return self.__connected_devices

    def get_synced_trees(self):
        return self.__synced_trees


profile = Profile("C:\\Users\\Amged Wageh\\AppData\\Local\\Google\\DriveFS")
synced_trees = profile.get_synced_trees()
for tree in synced_trees:
    tree.print_synced_files_tree()
