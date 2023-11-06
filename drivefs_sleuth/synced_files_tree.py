class Item:
    def __init__(self, stable_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date, trashed):
        self.__stable_id = stable_id
        self.local_title = local_title
        self.mime_type = mime_type
        self.is_owner = is_owner
        self.file_size = file_size
        self.modified_date = modified_date
        self.viewed_by_me_date = viewed_by_me_date
        self.trashed = trashed

    def get_stable_id(self):
        return self.__stable_id

    def is_dir(self):
        return isinstance(self, Directory)


class File(Item):
    def __init__(self, stable_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                 trashed):
        super().__init__(stable_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                         trashed)


class Directory(Item):
    def __init__(self, stable_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                 trashed):
        super().__init__(stable_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                         trashed)
        self.__sub_items = []

    # TODO: do proper check for the added items
    def add_item(self, item):
        self.__sub_items.append(item)
    # def add_item(self, item_info):
    #     if item_info[0] == 0:
    #         item = File(item_info[1], item_info[2], item_info[3], item_info[4], item_info[5], item_info[6],
    #                     item_info[7], item_info[8])
    #     else:
    #         item = Directory(item_info[1], item_info[2], item_info[3], item_info[4], item_info[5], item_info[6],
    #                          item_info[7], item_info[8])
    #     self.__sub_items.append(item)
    #     return item

    def remove_item(self, stable_id):
        for item in self.__sub_items:
            if item.get_stable_id() == stable_id:
                self.__sub_items.remove(item)

    def get_sub_items(self):
        return self.__sub_items


def _print_tree(roots, indent=''):
    if isinstance(roots, File):
        print(f'{indent}- ({roots.get_stable_id()}) {roots.local_title}')

    elif isinstance(roots, Directory):
        print(f'{indent}+ ({roots.get_stable_id()}) {roots.local_title}')

        for sub_item in roots.get_sub_items():
            _print_tree(sub_item, indent + f'\t')

    else:
        for item in roots:
            _print_tree(item, indent)


class SyncedFilesTree:
    def __init__(self, root_info, account_id, account_email):
        self.__root = Directory(root_info[1], root_info[2], root_info[3], root_info[4], root_info[5], root_info[6],
                                root_info[7], root_info[8])
        self.__account_id = account_id
        self.__account_email = account_email
        self.__orphan_items = []
        self.__deleted_items = []

    def get_root(self):
        return self.__root

    def get_account_id(self):
        return self.__account_id

    def get_account_email(self):
        return self.__account_email

    def get_orphan_items(self):
        return self.__orphan_items

    def add_orphan_item(self, item):
        self.__orphan_items.append(item)

    def add_deleted_item(self, stable_id):
        self.__deleted_items.append(stable_id)

    def get_item_by_id(self, target_id, orphan=False):
        if not orphan:
            dirs_queue = [self.get_root()] + self.get_orphan_items()
        else:
            dirs_queue = self.get_orphan_items()

        while dirs_queue:
            current_dir = dirs_queue.pop(0)

            for item in current_dir.get_sub_items():
                if item.get_stable_id() == target_id:
                    return item

                else:
                    if item.is_dir():
                        dirs_queue.append(item)

        return None

    def print_synced_files_tree(self):
        print(f'Account ID: {self.get_account_id()}')
        print(f'Account Email: {self.get_account_email()}')

        print('\n----------Synced Items----------\n')

        _print_tree([self.get_root()] + self.get_orphan_items())

        print('\n----------Deleted Items----------\n')

        for deleted_item in self.__deleted_items:
            print(f'- {deleted_item}')

        print('\n----------Orphan Items----------\n')

        for orphan in self.get_orphan_items():
            print(f'- ({orphan.get_stable_id()}) {orphan.local_title}')
