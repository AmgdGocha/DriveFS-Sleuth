import re
import os
import sqlite3


def get_account_ids(drivefs_path):
    with sqlite3.connect(os.path.join(drivefs_path, "experiments.db")) as experiments_db:
        cursor = experiments_db.cursor()
        cursor.execute("SELECT value FROM PhenotypeValues WHERE key='account_ids'")
        return re.findall(r'\d+', cursor.fetchall()[0][0].decode('utf-8'))


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
                with open(os.path.join(logs_dir, file), 'r') as logs_file:
                    logs = logs_file.read()
                    match = re.search(r"([\w\.-]+@[\w\.-]+\.\w+) \(" + account_id + r"\)", logs)
                    if match:
                        return match.group(1)
    return ''


def get_synced_files(profile_path):
    with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
        cursor = metadata_sqlite_db.cursor()
        cursor.execute("SELECT is_folder, stable_id, local_title, mime_type, is_owner, file_size, modified_date, "
                       "viewed_by_me_date, trashed FROM items")
        return cursor.fetchall()


def get_parent_relationships(profile_path):
    with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
        cursor = metadata_sqlite_db.cursor()
        cursor.execute(
            "SELECT parent_stable_id, item_stable_id FROM stable_parents ORDER BY parent_stable_id, item_stable_id"
        )
        return cursor.fetchall()


def get_item_info(profile_path, stable_id):
    with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
        cursor = metadata_sqlite_db.cursor()
        cursor.execute(f"SELECT is_folder, stable_id, id, local_title, mime_type, is_owner, file_size, modified_date, "
                       f"viewed_by_me_date, trashed FROM items WHERE stable_id={stable_id}")
        return cursor.fetchone()


def get_last_sync(drivefs_path):
    with sqlite3.connect(os.path.join(drivefs_path, "experiments.db")) as experiments_db:
        cursor = experiments_db.cursor()
        cursor.execute("SELECT value FROM PhenotypeValues WHERE key='last_sync'")
        return int(cursor.fetchone()[0])


def get_last_pid(drivefs_path):
    with open(os.path.join(drivefs_path, 'pid.txt')) as pid_file:
        return pid_file.read()


def get_connected_devices(drivefs_path):
    with sqlite3.connect(os.path.join(drivefs_path, "root_preference_sqlite.db")) as root_preference_db:
        cursor = root_preference_db.cursor()
        cursor.execute("SELECT media_id, name, last_mount_point, capacity, ignored FROM media")
        return cursor.fetchall()


def get_max_root_ids(drivefs_path):
    with sqlite3.connect(os.path.join(drivefs_path, "root_preference_sqlite.db")) as root_preference_db:
        cursor = root_preference_db.cursor()
        cursor.execute("SELECT value FROM max_ids WHERE id_type='max_root_id'")
        max_root_ids = cursor.fetchone()
        if max_root_ids:
            return int(max_root_ids[0])
        return None


def get_mirroring_roots_for_account(drivefs_path, account_id):
    with sqlite3.connect(os.path.join(drivefs_path, "root_preference_sqlite.db")) as root_preference_db:
        cursor = root_preference_db.cursor()
        cursor.execute("SELECT account_token, root_id, media_id, title, root_path, sync_type, destination, "
                       f"last_seen_absolute_path FROM roots WHERE account_token=\"{account_id}\"")
        return cursor.fetchall()


def get_item_properties(profile_path, item_id):
    with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
        cursor = metadata_sqlite_db.cursor()
        cursor.execute(f"SELECT key, value FROM item_properties WHERE item_stable_id={item_id}")
        item_properties = {}
        for item_property in cursor.fetchall():
            item_properties[item_property[0]] = item_property[1]
        return item_properties


def get_target_stable_id(profile_path, shortcut_stable_id):
    with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
        cursor = metadata_sqlite_db.cursor()
        cursor.execute(f"SELECT target_stable_id FROM shortcut_details WHERE shortcut_stable_id={shortcut_stable_id}")
        shortcut_stable_id = cursor.fetchone()
        if shortcut_stable_id:
            return int(shortcut_stable_id[0])
        return 0


def get_shared_with_me_without_link(profile_path):
    with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
        cursor = metadata_sqlite_db.cursor()
        cursor.execute("SELECT is_folder, stable_id, id, local_title, mime_type, is_owner, file_size, modified_date, "
                       "viewed_by_me_date, trashed FROM items "
                       "LEFT JOIN stable_parents ON items.stable_id = stable_parents.item_stable_id "
                       "LEFT JOIN shortcut_details ON items.stable_id = shortcut_details.target_stable_id "
                       "WHERE items.is_owner=0 AND items.shared_with_me_date=1 AND stable_parents.item_stable_id IS NULL "
                       "AND shortcut_details.target_stable_id IS NULL "
                       "ORDER BY items.stable_id")
        return cursor.fetchall()


def get_properties_list(profile_path):
    with sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db")) as metadata_sqlite_db:
        cursor = metadata_sqlite_db.cursor()
        cursor.execute("SELECT DISTINCT key FROM item_properties")
        return [prop[0] for prop in cursor.fetchall() if prop[0] != 'version-counter']
