"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: this module contains classes used to represent parsed items and construct them into a tree.
"""

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
                 trashed, properties, tree_path, content_cache_path, thumbnail_path, proto):
        super().__init__(stable_id, url_id, local_title, mime_type, is_owner, file_size, modified_date,
                         viewed_by_me_date, trashed, properties, tree_path, proto)

        self.__content_cache_path = content_cache_path
        self.__thumbnail_path = thumbnail_path
        self.__file_type = parse_protobuf(proto).get('45', '')

    def get_content_cache_path(self):
        return self.__content_cache_path

    def get_thumbnail_path(self):
        return self.__thumbnail_path

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
        super().__init__(stable_id, '', 'DELETED_ITEM', '', '', '', '', '', '', '', 'DELETED_ITEM', '')

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


class SyncedFilesTree:
    def __init__(self, root):
        self.__root = root
        self.__orphan_items = []
        self.__shared_with_me = []
        self.__recovered_deleted_items = []
        self.__deleted_items = []
        self.__mirror_items = []
        self.__recoverable_items_from_cache = []
        self.__thumbnail_items = []

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

    def search(self, conditions):
        items = []

        def append_item_childes(item):
            items.append(item)
            if isinstance(item, File):
                return

            elif isinstance(item, Link):
                target = item.get_target_item()
                if isinstance(item, File):
                    append_item_childes(target)
                else:
                    for sub_item in target.get_sub_items():
                        append_item_childes(sub_item)

            elif isinstance(item, Directory):
                for sub_item in item.get_sub_items():
                    append_item_childes(sub_item)

            else:
                for sub_item in item:
                    append_item_childes(sub_item)

        def add_sub_items(item):
            if isinstance(item, Link):
                target = item.get_target_item()
                if isinstance(target, File):
                    append_item_childes(target)
                else:
                    for sub_item in target.get_sub_items():
                        append_item_childes(sub_item)

            elif isinstance(item, Directory):
                for sub_item in item.get_sub_items():
                    append_item_childes(sub_item)

        def __search(current_item):
            for condition in [(target, c['LIST_SUB_ITEMS']) for c in conditions if c['TYPE'] == 'regex' for target in c['TARGET']]:
                match = re.search(condition[0], current_item.local_title)
                if match:
                    items.append(current_item)
                    if condition[1]:
                        add_sub_items(current_item)

            for condition in [(target.lower(), c['LIST_SUB_ITEMS']) for c in conditions if c['TYPE'] == 'urlid' for target in c['TARGET']]:
                if condition[0] == current_item.url_id.lower():
                    items.append(current_item)
                    if condition[1]:
                        add_sub_items(current_item)

            for condition in [(target.lower(), c['LIST_SUB_ITEMS'], c['CONTAINS']) for c in conditions if c['TYPE'] == 'filename' for target in c['TARGET']]:
                if condition[2]:
                    if condition[0] in current_item.local_title.lower():
                        items.append(current_item)
                        if condition[1]:
                            add_sub_items(current_item)
                else:
                    if condition[0] == current_item.local_title.lower():
                        items.append(current_item)
                        if condition[1]:
                            add_sub_items(current_item)

            for condition in [target.lower() for c in conditions if c['TYPE'] == 'md5' for target in c['TARGET']]:
                if isinstance(current_item, File):
                    if condition == current_item.md5:
                        items.append(current_item)

            if isinstance(current_item, File):
                return

            if isinstance(current_item, Link):
                target = current_item.get_target_item()
                if isinstance(target, File):
                    __search(target)
                else:
                    for sub_item in target.get_sub_items():
                        __search(sub_item)
            else:
                for sub_item in current_item.get_sub_items():
                    __search(sub_item)

        __search(self.get_root())
        for orphan_item in self.get_orphan_items():
            __search(orphan_item)

        for shared_item in self.get_shared_with_me_items():
            __search(shared_item)

        for recovered_deleted_item in self.get_recovered_deleted_items():
            __search(recovered_deleted_item)

        return items

    def add_mirrored_item(self, mirrored_item):
        self.__mirror_items.append(mirrored_item)

    def get_mirrored_items(self):
        return self.__mirror_items

    def add_recoverable_item_from_cache(self, recoverable_from_cache_item):
        self.__recoverable_items_from_cache.append(recoverable_from_cache_item)

    def add_thumbnail_item(self, thumbnail_item):
        self.__thumbnail_items.append(thumbnail_item)

    def get_recoverable_items_from_cache(self):
        return self.__recoverable_items_from_cache

    def get_thumbnail_items(self):
        return self.__thumbnail_items

    def print_synced_files_tree(self):
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

    def generate_synced_files_tree_dicts(self):
        def _traverse_tree(node):
            if isinstance(node, File):
                row = node.to_dict()
                row['type'] = 'File'
                if node.get_content_cache_path():
                    row['path_in_content_cache'] = node.get_content_cache_path()
                if node.get_thumbnail_path():
                    row['thumbnail_path'] = node.get_thumbnail_path()
                yield row

            elif isinstance(node, Link):
                row = node.to_dict()
                row['type'] = 'Link'
                yield row
                target = node.get_target_item()
                if isinstance(target, File):
                    yield from _traverse_tree(target)
                else:
                    for sub_item in target.get_sub_items():
                        yield from _traverse_tree(sub_item)

            elif isinstance(node, Directory):
                row = node.to_dict()
                row['type'] = 'Directory'
                yield row
                for sub_item in node.get_sub_items():
                    yield from _traverse_tree(sub_item)

            elif isinstance(node, list):
                for item in node:
                    yield from _traverse_tree(item)

        for node in [self.get_root()] + self.get_orphan_items() + self.get_shared_with_me_items():
            yield from _traverse_tree(node)
