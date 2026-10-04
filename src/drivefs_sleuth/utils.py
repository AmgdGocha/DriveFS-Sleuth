"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: this module contains the auxiliary utilities for executing drivefs-sleuth.
"""

import re
import os
import shutil
import sqlite3
import tempfile
from pathlib import Path

import blackboxprotobuf


class _TempDatabaseConnection:
    def __init__(self, connection, temp_dir):
        self.__connection = connection
        self.__temp_dir = temp_dir

    def cursor(self):
        return self.__connection.cursor()

    def close(self):
        self.__connection.close()
        shutil.rmtree(self.__temp_dir, ignore_errors=True)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def decode_utf8(value):
    return value.decode('utf-8', errors='replace')


def __text_factory(value):
    return decode_utf8(value)


def __is_wal_database(db_path):
    try:
        with open(db_path, "rb") as db_file:
            header = db_file.read(20)
            if len(header) < 20 or header[:16] != b"SQLite format 3\x00":
                return False
            return header[18] == 2
    except OSError:
        return False


def __open_read_only(db_uri):
    connection = sqlite3.connect(db_uri, uri=True)
    connection.text_factory = __text_factory
    return connection


def _connect_read_only(db_path):
    if not os.path.exists(db_path):
        raise sqlite3.OperationalError(f"database file not found: {db_path}")
    db_uri = Path(os.path.abspath(db_path)).as_uri()
    wal_path = db_path + "-wal"
    shm_path = db_path + "-shm"

    if __is_wal_database(db_path):
        if os.path.exists(shm_path):
            return __open_read_only(db_uri + "?mode=ro")
        if os.path.exists(wal_path) and os.path.getsize(wal_path) > 0:
            temp_dir = tempfile.mkdtemp()
            temp_db = os.path.join(temp_dir, "db")
            try:
                shutil.copy2(db_path, temp_db)
                shutil.copy2(wal_path, temp_db + "-wal")
                connection = __open_read_only(Path(os.path.abspath(temp_db)).as_uri() + "?mode=ro")
            except (sqlite3.Error, OSError):
                shutil.rmtree(temp_dir, ignore_errors=True)
                connection = __open_read_only(db_uri + "?mode=ro&immutable=1")
            else:
                return _TempDatabaseConnection(connection, temp_dir)
            return connection
        return __open_read_only(db_uri + "?mode=ro&immutable=1")

    try:
        return __open_read_only(db_uri + "?mode=ro")
    except sqlite3.Error:
        return __open_read_only(db_uri + "?mode=ro&immutable=1")


_SHARED_WITH_ME_QUERY = (
    "SELECT is_folder, stable_id, id, local_title, mime_type, is_owner, file_size, modified_date, "
    "viewed_by_me_date, trashed, proto FROM items "
    "WHERE items.is_owner=0 AND items.shared_with_me_date=1 "
    "AND NOT EXISTS (SELECT 1 FROM stable_parents sp WHERE sp.item_stable_id = items.stable_id) "
    "AND NOT EXISTS (SELECT 1 FROM shortcut_details sd WHERE sd.target_stable_id = items.stable_id) "
    "ORDER BY items.stable_id"
)


class ProfileMetadata:
    def __init__(self, profile_path):
        self.__items = {}
        self.__parent_relationships = []
        self.__item_properties = {}
        self.__shortcut_targets = {}
        self.__deleted_items = []
        self.__shared_with_me = []
        self.__load_errors = []
        try:
            metadata_sqlite_db = _connect_read_only(os.path.join(profile_path, "metadata_sqlite_db"))
        except sqlite3.Error:
            self.__load_errors.append('metadata_sqlite_db')
            return
        with metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            try:
                cursor.execute("SELECT is_folder, stable_id, id, local_title, mime_type, is_owner, file_size, "
                               "modified_date, viewed_by_me_date, trashed, proto FROM items")
                for item_info in cursor.fetchall():
                    self.__items[item_info[1]] = item_info
            except sqlite3.Error:
                self.__load_errors.append('items')
            try:
                cursor.execute("SELECT parent_stable_id, item_stable_id FROM stable_parents "
                               "ORDER BY parent_stable_id, item_stable_id")
                self.__parent_relationships = cursor.fetchall()
            except sqlite3.Error:
                self.__load_errors.append('stable_parents')
            try:
                cursor.execute("SELECT item_stable_id, key, value FROM item_properties")
                for item_stable_id, key, value in cursor.fetchall():
                    self.__item_properties.setdefault(item_stable_id, {})[key] = value
            except sqlite3.Error:
                self.__load_errors.append('item_properties')
            try:
                cursor.execute("SELECT shortcut_stable_id, target_stable_id FROM shortcut_details")
                self.__shortcut_targets = dict(cursor.fetchall())
            except sqlite3.Error:
                self.__load_errors.append('shortcut_details')
            try:
                cursor.execute("SELECT stable_id, proto FROM deleted_items")
                self.__deleted_items = cursor.fetchall()
            except sqlite3.Error:
                self.__load_errors.append('deleted_items')
            try:
                cursor.execute(_SHARED_WITH_ME_QUERY)
                self.__shared_with_me = cursor.fetchall()
            except sqlite3.Error:
                self.__load_errors.append('shared_with_me')

    def __normalize_id(self, stable_id):
        if stable_id in self.__items:
            return stable_id
        try:
            return int(stable_id)
        except (TypeError, ValueError):
            return stable_id

    def get_load_errors(self):
        return list(self.__load_errors)

    def get_item_info(self, stable_id):
        return self.__items.get(self.__normalize_id(stable_id), ())

    def get_parent_relationships(self):
        return self.__parent_relationships

    def get_item_properties(self, item_id):
        return self.__item_properties.get(self.__normalize_id(item_id), {})

    def get_target_stable_id(self, shortcut_stable_id):
        target_stable_id = self.__shortcut_targets.get(self.__normalize_id(shortcut_stable_id))
        if target_stable_id is None:
            return 0
        try:
            return int(target_stable_id)
        except (TypeError, ValueError):
            return 0

    def get_deleted_items(self):
        return self.__deleted_items

    def get_shared_with_me_without_link(self):
        return self.__shared_with_me


def get_experiment_account_ids(drivefs_path):
    try:
        with _connect_read_only(os.path.join(drivefs_path, "experiments.db")) as experiments_db:
            cursor = experiments_db.cursor()
            cursor.execute("SELECT value FROM PhenotypeValues WHERE key='account_ids'")
            rows = cursor.fetchall()
            if not rows:
                return []
            value = rows[0][0]
            if isinstance(value, bytes):
                value = value.decode('utf-8', errors='replace')
            else:
                value = str(value)
            return re.findall(r'\d+', value)
    except sqlite3.Error as e:
        return []


def get_available_profiles(drivefs_path):
    profiles = []
    for subdir in os.listdir(drivefs_path):
        if subdir.isdigit() and len(subdir) == 21:
            profiles.append(subdir)
    return profiles


def lookup_account_id(drivefs_path, account_id):
    logs_dir = os.path.join(drivefs_path, "Logs")
    for _, _, files in os.walk(logs_dir):
        for file in files:
            if file.startswith("drive_fs") and file.endswith(".txt"):
                try:
                    with open(os.path.join(logs_dir, file), 'r', encoding="utf8", errors="replace") as logs_file:
                        logs = logs_file.read()
                        match = re.search(r"([\w\.-]+@[\w\.-]+\.\w+) \(" + account_id + r"\)", logs)
                        if match:
                            return match.group(1)
                except OSError:
                    continue
    return ''


def get_synced_files(profile_path):
    try:
        with _connect_read_only(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute("SELECT is_folder, stable_id, local_title, mime_type, is_owner, file_size, modified_date, "
                           "viewed_by_me_date, trashed, proto FROM items")
            return cursor.fetchall()
    except sqlite3.Error:
        return []


def get_parent_relationships(profile_path):
    try:
        with _connect_read_only(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute(
                "SELECT parent_stable_id, item_stable_id FROM stable_parents ORDER BY parent_stable_id, item_stable_id"
            )
            return cursor.fetchall()
    except sqlite3.Error:
        return []


def get_item_info(profile_path, stable_id):
    try:
        with _connect_read_only(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute("SELECT is_folder, stable_id, id, local_title, mime_type, is_owner, file_size, "
                           "modified_date, viewed_by_me_date, trashed, proto FROM items WHERE stable_id=?",
                           (stable_id,))
            return cursor.fetchone()
    except sqlite3.Error:
        return ()


def get_last_sync(drivefs_path):
    try:
        with _connect_read_only(os.path.join(drivefs_path, "experiments.db")) as experiments_db:
            cursor = experiments_db.cursor()
            cursor.execute("SELECT value FROM PhenotypeValues WHERE key='last_sync'")
            row = cursor.fetchone()
            if row is None:
                return -1
            try:
                return int(row[0])
            except (TypeError, ValueError):
                return -1
    except sqlite3.Error:
        return -1


def get_last_pid(drivefs_path):
    try:
        with open(os.path.join(drivefs_path, 'pid.txt')) as pid_file:
            return pid_file.read().strip()
    except OSError:
        return -1


def get_connected_devices(drivefs_path):
    try:
        with _connect_read_only(os.path.join(drivefs_path, "root_preference_sqlite.db")) as root_preference_db:
            cursor = root_preference_db.cursor()
            cursor.execute("SELECT media_id, name, last_mount_point, capacity, ignored FROM media")
            return cursor.fetchall()
    except sqlite3.Error:
        return []


def get_max_root_ids(drivefs_path):
    try:
        with _connect_read_only(os.path.join(drivefs_path, "root_preference_sqlite.db")) as root_preference_db:
            cursor = root_preference_db.cursor()
            cursor.execute("SELECT value FROM max_ids WHERE id_type='max_root_id'")
            max_root_ids = cursor.fetchone()
            if max_root_ids:
                try:
                    return int(max_root_ids[0])
                except (TypeError, ValueError):
                    return None
            return None
    except sqlite3.Error:
        return None


def get_mirroring_roots_for_account(drivefs_path, account_id):
    try:
        with _connect_read_only(os.path.join(drivefs_path, "root_preference_sqlite.db")) as root_preference_db:
            cursor = root_preference_db.cursor()
            cursor.execute("SELECT account_token, root_id, media_id, title, root_path, sync_type, destination, "
                           "last_seen_absolute_path FROM roots WHERE account_token=?", (account_id,))
            return cursor.fetchall()
    except sqlite3.Error:
        return []


def get_item_properties(profile_path, item_id):
    try:
        with _connect_read_only(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute("SELECT key, value FROM item_properties WHERE item_stable_id=?", (item_id,))
            item_properties = {}
            for item_property in cursor.fetchall():
                item_properties[item_property[0]] = item_property[1]
            return item_properties
    except sqlite3.Error:
        return {}


def get_target_stable_id(profile_path, shortcut_stable_id):
    try:
        with _connect_read_only(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute("SELECT target_stable_id FROM shortcut_details "
                           "WHERE shortcut_stable_id=?", (shortcut_stable_id,))
            shortcut_stable_id = cursor.fetchone()
            if shortcut_stable_id:
                try:
                    return int(shortcut_stable_id[0])
                except (TypeError, ValueError):
                    return 0
            return 0
    except sqlite3.Error:
        return 0


def get_shared_with_me_without_link(profile_path):
    try:
        with _connect_read_only(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute(_SHARED_WITH_ME_QUERY)
            return cursor.fetchall()
    except sqlite3.Error:
        return []


def get_properties_list(profile_path):
    try:
        with _connect_read_only(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute("SELECT DISTINCT key FROM item_properties")
            return [prop[0] for prop in cursor.fetchall()]
    except sqlite3.Error:
        return []


def get_mirrored_items(profile_path):
    try:
        with _connect_read_only(os.path.join(profile_path, "mirror_sqlite.db")) as mirror_sqlite_db:
            cursor = mirror_sqlite_db.cursor()
            cursor.execute("SELECT local_stable_id, stable_id, volume, parent_local_stable_id, local_filename, "
                           "cloud_filename, local_mtime_ms, cloud_mtime_ms, local_md5_checksum, cloud_md5_checksum,"
                           "local_size, cloud_size, local_version, cloud_version, shared, read_only, is_root "
                           "FROM mirror_item")
            return cursor.fetchall()
    except sqlite3.Error:
        return []


def parse_protobuf(protobuf):
    if not protobuf:
        return {}

    try:
        return blackboxprotobuf.decode_message(protobuf)[0]
    except Exception:
        return {}


def get_account_properties(profile_path):
    properties = {
        'name': '',
        'photo_url': ''
    }
    try:
        try:
            with _connect_read_only(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
                cursor = metadata_sqlite_db.cursor()
                cursor.execute("SELECT value FROM properties WHERE property = 'driveway_account'")

                driveway_account = parse_protobuf(cursor.fetchone()[0])
                name = driveway_account['2']['1']['3']
                if isinstance(name, str):
                    properties['name'] = name
                properties['photo_url'] = driveway_account['2']['1']['5']

        except sqlite3.Error:
            try:
                with _connect_read_only(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
                    cursor = metadata_sqlite_db.cursor()
                    cursor.execute("SELECT value FROM properties WHERE property = 'account'")

                    account = parse_protobuf(cursor.fetchone()[0])
                    name = account['1']['3']
                    if isinstance(name, str):
                        properties['name'] = name
                    properties['photo_url'] = account['1']['5']

            except sqlite3.Error:
                return properties

    except TypeError:
        return properties

    except (KeyError, AttributeError):
        return properties

    return properties


def get_deleted_items(profile_path):
    try:
        with _connect_read_only(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute("SELECT stable_id, proto FROM deleted_items")
            return cursor.fetchall()
    except sqlite3.Error:
        return []


def __collect_cache_paths(cache_dir, paths):
    try:
        entries = os.scandir(cache_dir)
    except OSError:
        return
    subdirs = []
    for entry in entries:
        try:
            is_dir = entry.is_dir(follow_symlinks=False)
        except OSError:
            is_dir = False
        if is_dir:
            subdirs.append(entry.path)
        else:
            paths.setdefault(entry.name, os.path.abspath(entry.path))
    entries.close()
    for subdir in subdirs:
        __collect_cache_paths(subdir, paths)


def get_content_caches_paths(content_cache_dir):
    content_caches_paths = {}
    __collect_cache_paths(content_cache_dir, content_caches_paths)

    content_caches_paths.pop('chunks.db', None)
    content_caches_paths.pop('chunks.db-shm', None)
    content_caches_paths.pop('chunks.db-wal', None)

    return content_caches_paths


def get_thumbnails_paths(thumbnails_dir):
    thumbnails_paths = {}
    __collect_cache_paths(thumbnails_dir, thumbnails_paths)

    thumbnails_paths.pop('chunks.db', None)
    thumbnails_paths.pop('chunks.db-shm', None)
    thumbnails_paths.pop('chunks.db-wal', None)

    return thumbnails_paths


def get_file_content_cache_path(content_entry, content_caches_paths):
    if content_entry:
        parsed_content_entry = parse_protobuf(content_entry)
        content_entry_filename = parsed_content_entry.get('1', '')
        if isinstance(content_entry_filename, bytes):
            content_entry_filename = content_entry_filename.decode('utf-8', errors='replace')
        elif not isinstance(content_entry_filename, str):
            return ''
        return content_caches_paths.get(content_entry_filename, '')
    return ''


def copy_file(file_path, dest_filename, recovery_path=''):
    if not recovery_path:
        recovery_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recovered_items')

    dest_filename = re.sub(r'[<>:"/\\|?*]', '_', str(dest_filename or 'recovered_item'))
    dest_path = os.path.join(recovery_path, dest_filename)

    try:
        if not os.path.exists(recovery_path):
            os.makedirs(recovery_path)

        basename, extension = os.path.splitext(dest_filename)
        counter = 1
        while os.path.exists(dest_path):
            dest_path = os.path.join(recovery_path, f'{basename} ({counter}){extension}')
            counter += 1

        shutil.copy2(file_path, dest_path)
    except OSError:
        return False
    return True
