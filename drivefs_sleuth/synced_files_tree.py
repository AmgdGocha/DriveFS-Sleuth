import re
import datetime

from drivefs_sleuth.utils import parse_protobuf


class Item:
    def __init__(self, stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                 trashed, properties, tree_path, proto):
        self.__stable_id = stable_id
        self.url_id = url_id
        self.local_title = local_title
        self.mime_type = mime_type
        self.is_owner = is_owner
        self.file_size = file_size
        self.modified_date = modified_date
        self.viewed_by_me_date = viewed_by_me_date
        self.trashed = trashed
        self.properties = properties
        self.tree_path = tree_path
        self.md5 = parse_protobuf(proto).get('48', '')

    def get_stable_id(self):
        return self.__stable_id

    def is_file(self):
        return isinstance(self, File)

    def is_dir(self):
        return isinstance(self, Directory)

    def is_link(self):
        return isinstance(self, Link)

    def get_modified_date_utc(self):
        return datetime.datetime.fromtimestamp(int(self.modified_date)/1000.0, datetime.timezone.utc)

    def get_viewed_by_me_date_utc(self):
        return datetime.datetime.fromtimestamp(int(self.viewed_by_me_date)/1000.0, datetime.timezone.utc)

    def get_file_size_mb(self):
        return round(int(self.file_size) / 1e+6, 2)

    def to_dict(self):
        item_dict = {
            'stable_id': self.get_stable_id(),
            'url_id': self.url_id,
            'local_title': self.local_title,
            'mime_type': self.mime_type,
            'is_owner': self.is_owner,
            'file_size': self.file_size,
            'modified_date': self.get_modified_date_utc(),
            'viewed_by_me_date': self.get_viewed_by_me_date_utc(),
            'trashed': self.trashed,
            'tree_path': self.tree_path,
            'md5': self.md5
        }
        for prop_name, prop_value in self.properties.items():
            item_dict[prop_name] = prop_value

        return item_dict


class File(Item):
    def __init__(self, stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                 trashed, properties, tree_path, content_cache_path, proto):
        super().__init__(stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date,
                         viewed_by_me_date, trashed, properties, tree_path, proto)

        self.__content_cache_path = content_cache_path
        self.__file_type = parse_protobuf(proto).get('45', '')

    def get_content_cache_path(self):
        return self.__content_cache_path

    def get_file_type(self):
        return self.__file_type


class Directory(Item):
    def __init__(self, stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                 trashed, properties, tree_path, proto):
        super().__init__(stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date,
                         viewed_by_me_date, trashed, properties, tree_path, proto)
        self.__sub_items = []

    def add_item(self, item):
        self.__sub_items.append(item)

    def remove_item(self, stable_id):
        for item in self.__sub_items:
            if item.get_stable_id() == stable_id:
                self.__sub_items.remove(item)

    def get_sub_items(self):
        return self.__sub_items


class DummyItem(Item):
    def __init__(self, stable_id):
        super().__init__(stable_id, '', 'DELETED_ITEM', '', '', '', '', '', '', '', '', '')

    def get_sub_items(self):
        return []


class Link(Item):
    def __init__(self, stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date, viewed_by_me_date,
                 trashed, properties, tree_path, target_item, proto):
        super().__init__(stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date,
                         viewed_by_me_date, trashed, properties, tree_path, proto)
        self.__target_item = target_item

    def get_target_item(self):
        return self.__target_item


class MirrorItem:
    def __init__(self, local_stable_id, stable_id, volume, parent, local_filename, cloud_filename, local_mtime,
                 cloud_mtime, local_md5, cloud_md5, local_size, cloud_size, local_version, cloud_version, shared,
                 read_only, is_root):
        self.local_stable_id = local_stable_id
        self.stable_id = stable_id
        self.volume = volume
        self.parent = parent
        self.local_filename = local_filename
        self.cloud_filename = cloud_filename
        self.local_mtime = local_mtime
        self.cloud_mtime = cloud_mtime
        self.local_md5 = local_md5
        self.cloud_md5 = cloud_md5
        self.local_size = local_size
        self.cloud_size = cloud_size
        self.local_version = local_version
        self.cloud_version = cloud_version
        self.shared = shared
        self.read_only = read_only
        self.is_root = is_root

    def get_local_mtime_utc(self):
        return datetime.datetime.fromtimestamp(int(self.local_mtime)/1000.0, datetime.timezone.utc)

    def get_cloud_mtime_utc(self):
        return datetime.datetime.fromtimestamp(int(self.cloud_mtime)/1000.0, datetime.timezone.utc)


def _print_tree(roots, indent=''):
    if isinstance(roots, File):
        print(f'{indent}- ({roots.get_stable_id()}) {roots.local_title} - ({roots.tree_path})')

    elif isinstance(roots, Link):
        print(f'{indent}+ ({roots.get_stable_id()}) {roots.local_title} - ({roots.tree_path})')

        target = roots.get_target_item()

        if isinstance(target, File):
            print(f'{indent}- ({target.get_stable_id()}) {target.local_title} - ({target.tree_path})')

        else:
            for sub_item in target.get_sub_items():
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
        self.__shared_with_me = []
        self.__recovered_deleted_items = []
        self.__deleted_items = []
        self.__mirror_items = []
        self.__recoverable_items_from_cache = []

    def get_root(self):
        return self.__root

    def get_orphan_items(self):
        return self.__orphan_items

    def add_orphan_item(self, item):
        self.__orphan_items.append(item)

    def add_deleted_item(self, stable_id):
        self.__deleted_items.append(stable_id)

    def add_recovered_deleted_item(self, item):
        self.__recovered_deleted_items.append(item)

    def add_shared_with_me_item(self, item):
        self.__shared_with_me.append(item)

    def get_shared_with_me_items(self):
        return self.__shared_with_me

    def get_deleted_items(self):
        return self.__deleted_items

    def get_recovered_deleted_items(self):
        return self.__recovered_deleted_items

    def get_item_by_id(self, target_id, is_owner=False):
        if not is_owner:
            queue = [self.get_root()] + self.get_orphan_items() + self.get_shared_with_me_items()
        else:
            queue = [self.get_root()]

        while queue:
            current_item = queue.pop(0)

            if current_item.get_stable_id() == target_id:
                return current_item

            if current_item.is_file():
                continue

            elif current_item.is_dir():
                queue += current_item.get_sub_items()

            elif current_item.is_link():
                queue += current_item.get_target_item()

        return None

    def search_item_by_name(self, filenames=None, regex=None, contains=True, list_sub_items=True):
        if filenames is None:
            filenames = []
        if regex is None:
            regex = []
        items = []

        def append_item_childs(item):
            items.append(item)
            if isinstance(item, File):
                return

            elif isinstance(item, Link):
                target = item.get_target_item()
                if isinstance(item, File):
                    append_item_childs(target)
                else:
                    for sub_item in target.get_sub_items():
                        append_item_childs(sub_item)

            elif isinstance(item, Directory):
                for sub_item in item.get_sub_items():
                    append_item_childs(sub_item)

            else:
                for sub_item in item:
                    append_item_childs(sub_item)

        def search(current_item):
            hit = False
            if regex:
                for exp in regex:
                    match = re.search(exp, current_item.local_title)
                    if match:
                        items.append(current_item)
                        hit = True

            if contains:
                for filename in filenames:
                    if filename.lower() in current_item.local_title.lower():
                        items.append(current_item)
                        hit = True
            else:
                for filename in filenames:
                    if filename.lower() == current_item.local_title.lower():
                        items.append(current_item)
                        hit = True

            if isinstance(current_item, File):
                return

            elif isinstance(current_item, Link) and hit and list_sub_items:
                target = current_item.get_target_item()
                if isinstance(target, File):
                    append_item_childs(target)
                else:
                    for sub_item in target.get_sub_items():
                        append_item_childs(sub_item)

            elif isinstance(current_item, Directory) and hit and list_sub_items:
                for sub_item in current_item.get_sub_items():
                    append_item_childs(sub_item)

            else:
                if isinstance(current_item, Link):
                    target = current_item.get_target_item()
                    if isinstance(target, File):
                        search(target)
                    else:
                        for sub_item in target.get_sub_items():
                            search(sub_item)
                else:
                    for sub_item in current_item.get_sub_items():
                        search(sub_item)

        search(self.get_root())
        for orphan_item in self.get_orphan_items():
            search(orphan_item)

        for shared_item in self.get_shared_with_me_items():
            search(shared_item)

        for recovered_deleted_item in self.get_recovered_deleted_items():
            search(recovered_deleted_item)

        return items

    def add_mirrored_item(self, mirrored_item):
        self.__mirror_items.append(mirrored_item)

    def get_mirrored_items(self):
        return self.__mirror_items

    def add_recoverable_item_from_cache(self, recoverable_from_cache_item):
        self.__recoverable_items_from_cache.append(recoverable_from_cache_item)

    def get_recoverable_items_from_cache(self):
        return self.__recoverable_items_from_cache

    def print_synced_files_tree(self):
        print('\n----------Synced Items----------\n')

        _print_tree([self.get_root()] + self.get_orphan_items())

        print('\n----------Deleted Items----------\n')

        for recovered_deleted_items in self.__recovered_deleted_items:
            print(f'- ({recovered_deleted_items.get_stable_id()}) {recovered_deleted_items.local_title}')

        for deleted_item in self.__deleted_items:
            print(f'- {deleted_item}')

        print('\n----------Orphan Items----------\n')

        for orphan in self.get_orphan_items():
            print(f'- ({orphan.get_stable_id()}) {orphan.local_title}')

        print('\n----------Shared With Me Items----------\n')

        for shared_with_me_item in self.get_shared_with_me_items():
            print(f'- ({shared_with_me_item.get_stable_id()}) {shared_with_me_item.local_title}')
