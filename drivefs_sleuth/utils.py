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

import blackboxprotobuf


def get_experiment_account_ids(drivefs_path):
    try:
        with sqlite3.connect(os.path.join(drivefs_path, "experiments.db")) as experiments_db:
            cursor = experiments_db.cursor()
            cursor.execute("SELECT value FROM PhenotypeValues WHERE key='account_ids'")
            return re.findall(r'\d+', cursor.fetchall()[0][0].decode('utf-8'))
    except sqlite3.OperationalError as e:
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
                with open(os.path.join(logs_dir, file), 'r', encoding="utf8") as logs_file:
                    logs = logs_file.read()
                    match = re.search(r"([\w\.-]+@[\w\.-]+\.\w+) \(" + account_id + r"\)", logs)
                    if match:
                        return match.group(1)
    return ''


def get_synced_files(profile_path):
    try:
        with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute("SELECT is_folder, stable_id, local_title, mime_type, is_owner, file_size, modified_date, "
                           "viewed_by_me_date, trashed, proto FROM items")
            return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def get_parent_relationships(profile_path):
    try:
        with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute(
                "SELECT parent_stable_id, item_stable_id FROM stable_parents ORDER BY parent_stable_id, item_stable_id"
            )
            return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def get_item_info(profile_path, stable_id):
    try:
        with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute(f"SELECT is_folder, stable_id, id, local_title, mime_type, is_owner, file_size, "
                           f"modified_date, viewed_by_me_date, trashed, proto FROM items WHERE stable_id={stable_id}")
            return cursor.fetchone()
    except sqlite3.OperationalError:
        return ()


def get_last_sync(drivefs_path):
    try:
        with sqlite3.connect(os.path.join(drivefs_path, "experiments.db")) as experiments_db:
            cursor = experiments_db.cursor()
            cursor.execute("SELECT value FROM PhenotypeValues WHERE key='last_sync'")
            return int(cursor.fetchone()[0])
    except sqlite3.OperationalError:
        return -1


def get_last_pid(drivefs_path):
    try:
        with open(os.path.join(drivefs_path, 'pid.txt')) as pid_file:
            return pid_file.read()
    except OSError:
        return -1


def get_connected_devices(drivefs_path):
    try:
        with sqlite3.connect(os.path.join(drivefs_path, "root_preference_sqlite.db")) as root_preference_db:
            cursor = root_preference_db.cursor()
            cursor.execute("SELECT media_id, name, last_mount_point, capacity, ignored FROM media")
            return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def get_max_root_ids(drivefs_path):
    try:
        with sqlite3.connect(os.path.join(drivefs_path, "root_preference_sqlite.db")) as root_preference_db:
            cursor = root_preference_db.cursor()
            cursor.execute("SELECT value FROM max_ids WHERE id_type='max_root_id'")
            max_root_ids = cursor.fetchone()
            if max_root_ids:
                return int(max_root_ids[0])
            return None
    except sqlite3.OperationalError:
        return None


def get_mirroring_roots_for_account(drivefs_path, account_id):
    try:
        with sqlite3.connect(os.path.join(drivefs_path, "root_preference_sqlite.db")) as root_preference_db:
            cursor = root_preference_db.cursor()
            cursor.execute("SELECT account_token, root_id, media_id, title, root_path, sync_type, destination, "
                           f"last_seen_absolute_path FROM roots WHERE account_token=\"{account_id}\"")
            return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def get_item_properties(profile_path, item_id):
    try:
        with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute(f"SELECT key, value FROM item_properties WHERE item_stable_id={item_id}")
            item_properties = {}
            for item_property in cursor.fetchall():
                item_properties[item_property[0]] = item_property[1]
            return item_properties
    except sqlite3.OperationalError:
        return {}


def get_target_stable_id(profile_path, shortcut_stable_id):
    try:
        with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute(f"SELECT target_stable_id FROM shortcut_details "
                           f"WHERE shortcut_stable_id={shortcut_stable_id}")
            shortcut_stable_id = cursor.fetchone()
            if shortcut_stable_id:
                return int(shortcut_stable_id[0])
            return 0
    except sqlite3.OperationalError:
        return 0


def get_shared_with_me_without_link(profile_path):
    try:
        with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute("SELECT is_folder, stable_id, id, local_title, mime_type, is_owner, file_size, modified_date"
                           ", viewed_by_me_date, trashed, proto FROM items "
                           "LEFT JOIN stable_parents ON items.stable_id = stable_parents.item_stable_id "
                           "LEFT JOIN shortcut_details ON items.stable_id = shortcut_details.target_stable_id "
                           "WHERE items.is_owner=0 AND items.shared_with_me_date=1 "
                           "AND stable_parents.item_stable_id IS NULL "
                           "AND shortcut_details.target_stable_id IS NULL "
                           "ORDER BY items.stable_id")
            return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def get_properties_list(profile_path):
    try:
        with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute("SELECT DISTINCT key FROM item_properties")
            return [prop[0] for prop in cursor.fetchall()]
    except sqlite3.OperationalError:
        return []


def get_mirrored_items(profile_path):
    try:
        with sqlite3.connect(os.path.join(profile_path, "mirror_sqlite.db")) as mirror_sqlite_db:
            cursor = mirror_sqlite_db.cursor()
            cursor.execute("SELECT local_stable_id, stable_id, volume, parent_local_stable_id, local_filename, "
                           "cloud_filename, local_mtime_ms, cloud_mtime_ms, local_md5_checksum, cloud_md5_checksum,"
                           "local_size, cloud_size, local_version, cloud_version, shared, read_only, is_root "
                           "FROM mirror_item")
            return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def parse_protobuf(protobuf):
    if not protobuf:
        return {}

    return blackboxprotobuf.decode_message(protobuf)[0]


def get_account_properties(profile_path):
    properties = {
        'name': '',
        'photo_url': ''
    }
    try:
        try:
            with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
                cursor = metadata_sqlite_db.cursor()
                cursor.execute("SELECT value FROM properties WHERE property = 'driveway_account'")

                driveway_account = parse_protobuf(cursor.fetchone()[0])
                name = driveway_account['2']['1']['3']
                if isinstance(name, str):
                    properties['name'] = name
                properties['photo_url'] = driveway_account['2']['1']['5']

        except sqlite3.OperationalError:
            try:
                with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
                    cursor = metadata_sqlite_db.cursor()
                    cursor.execute("SELECT value FROM properties WHERE property = 'account'")

                    account = parse_protobuf(cursor.fetchone()[0])
                    name = account['1']['3']
                    if isinstance(name, str):
                        properties['name'] = name
                    properties['photo_url'] = account['1']['5']

            except sqlite3.OperationalError:
                return properties

    except TypeError:
        return properties

    return properties


def get_deleted_items(profile_path):
    try:
        with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
            cursor = metadata_sqlite_db.cursor()
            cursor.execute("SELECT stable_id, proto FROM deleted_items")
            return cursor.fetchall()
    except sqlite3.OperationalError:
        return []


def get_content_caches_paths(content_cache_dir):
    content_caches_paths = {}

    for root, _, content_caches in os.walk(content_cache_dir):
        for content_cache in content_caches:
            content_caches_paths[content_cache] = os.path.abspath(os.path.join(root, content_cache))

    content_caches_paths.pop('chunks.db', None)
    content_caches_paths.pop('chunks.db-shm', None)
    content_caches_paths.pop('chunks.db-wal', None)

    return content_caches_paths


def get_thumbnails_paths(thumbnails_dir):
    thumbnails_paths = {}

    for root, _, thumbnails in os.walk(thumbnails_dir):
        for thumbnail in thumbnails:
            thumbnails_paths[thumbnail] = os.path.abspath(os.path.join(root, thumbnail))

    thumbnails_paths.pop('chunks.db', None)
    thumbnails_paths.pop('chunks.db-shm', None)
    thumbnails_paths.pop('chunks.db-wal', None)

    return thumbnails_paths


def get_file_content_cache_path(content_entry, content_caches_paths):
    if content_entry:
        parsed_content_entry = parse_protobuf(content_entry)
        content_entry_filename = str(parsed_content_entry['1'])
        return content_caches_paths.get(content_entry_filename, '')
    return ''


def copy_file(file_path, dest_filename, recovery_path=''):
    if not recovery_path:
        recovery_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'recovered_items')

    if not os.path.exists(recovery_path):
        os.makedirs(recovery_path)

    shutil.copy2(file_path, os.path.join(recovery_path, dest_filename))
