import re


class Item:
    def __init__(self, stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                 trashed, properties, tree_path):
        self.__stable_id = stable_id
        self.__id = url_id
        self.local_title = local_title
        self.mime_type = mime_type
        self.is_owner = is_owner
        self.file_size = file_size
        self.modified_date = modified_date
        self.viewed_by_me_date = viewed_by_me_date
        self.trashed = trashed
        self.properties = properties
        self.tree_path = tree_path

    def get_stable_id(self):
        return self.__stable_id

    def is_dir(self):
        return isinstance(self, Directory)

    def is_link(self):
        return isinstance(self, Link)


class File(Item):
    def __init__(self, stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                 trashed, properties, tree_path):
        super().__init__(stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date,
                         viewed_by_me_date, trashed, properties, tree_path)


class Directory(Item):
    def __init__(self, stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                 trashed, properties, tree_path):
        super().__init__(stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date,
                         viewed_by_me_date, trashed, properties, tree_path)
        self.__sub_items = []

    # TODO: do proper check for the added items
    def add_item(self, item):
        self.__sub_items.append(item)

    def remove_item(self, stable_id):
        for item in self.__sub_items:
            if item.get_stable_id() == stable_id:
                self.__sub_items.remove(item)

    def get_sub_items(self):
        return self.__sub_items


class Link(Item):
    def __init__(self, stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                 trashed, properties, tree_path, target_item):
        super().__init__(stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date,
                         viewed_by_me_date, trashed, properties, tree_path)
        self.__target_item = target_item

    def get_target_item(self):
        return self.__target_item


def _print_tree(roots, indent=''):
    if isinstance(roots, File):
        print(f'{indent}- ({roots.get_stable_id()}) {roots.local_title} - ({roots.tree_path})')

    elif isinstance(roots, Link):
        print(f'{indent}+ ({roots.get_stable_id()}) {roots.local_title} - ({roots.tree_path})')

        for sub_item in roots.get_target_item().get_sub_items():
            _print_tree(sub_item, indent + f'\t')

    elif isinstance(roots, Directory):
        print(f'{indent}+ ({roots.get_stable_id()}) {roots.local_title} - ({roots.tree_path})')

        for sub_item in roots.get_sub_items():
            _print_tree(sub_item, indent + f'\t')

    else:
        for item in roots:
            _print_tree(item, indent)


class SyncedFilesTree:
    def __init__(self, root):
        self.__root = root
        self.__orphan_items = []
        self.__deleted_items = []
        # TODO: add a list of shared with me items

    def get_root(self):
        return self.__root

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

    def search_item_by_name(self, target, contains=True, regex=False, list_sub_items=True):
        items = []

        def append_item_childs(item):
            if isinstance(item, File):
                items.append(item)
                return

            items.append(item)
            for sub_item in item:
                append_item_childs(sub_item)

        def search(current_item):
            hit = False
            if regex:
                match = re.search(target, current_item.local_title)
                if match:
                    items.append(current_item)
                    hit = True
            elif contains:
                if target.lower() in current_item.local_title.lower():
                    items.append(current_item)
                    hit = True
            else:
                if target.lower() == current_item.local_title.lower():
                    items.append(current_item)
                    hit = True

            if isinstance(current_item, File):
                return

            if isinstance(current_item, Directory) and hit and list_sub_items:
                for sub_item in current_item.get_sub_items():
                    append_item_childs(sub_item)

            else:
                for sub_item in current_item.get_sub_items():
                    search(sub_item)

        search(self.get_root())
        for orphan_item in self.get_orphan_items():
            search(orphan_item)

        return items

    def print_synced_files_tree(self):
        print('\n----------Synced Items----------\n')

        _print_tree([self.get_root()] + self.get_orphan_items())

        print('\n----------Deleted Items----------\n')

        for deleted_item in self.__deleted_items:
            print(f'- {deleted_item}')

        print('\n----------Orphan Items----------\n')

        for orphan in self.get_orphan_items():
            print(f'- ({orphan.get_stable_id()}) {orphan.local_title}')
