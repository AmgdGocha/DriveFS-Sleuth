import os
import sqlite3


def get_synced_files(drivefs_path, account_id):
    account_profile = os.path.join(drivefs_path, account_id)
    metadata_sqlite_db = sqlite3.connect(os.path.join(account_profile, "metadata_sqlite_db"))
    cursor = metadata_sqlite_db.cursor()
    cursor.execute("SELECT is_folder, stable_id, local_title, mime_type, is_owner, file_size, modified_date, "
                   "viewed_by_me_date, trashed FROM items")
    return cursor.fetchall()


def get_parent_relationships(drivefs_path, account_id):
    account_profile = os.path.join(drivefs_path, account_id)
    metadata_sqlite_db = sqlite3.connect(os.path.join(account_profile, "metadata_sqlite_db"))
    cursor = metadata_sqlite_db.cursor()
    cursor.execute(
        "SELECT parent_stable_id, item_stable_id FROM stable_parents ORDER BY parent_stable_id, item_stable_id"
    )
    return cursor.fetchall()


def get_item_info(drivefs_path, account_id, stable_id):
    account_profile = os.path.join(drivefs_path, account_id)
    metadata_sqlite_db = sqlite3.connect(os.path.join(account_profile, "metadata_sqlite_db"))
    cursor = metadata_sqlite_db.cursor()
    cursor.execute(f"SELECT is_folder, stable_id, id, local_title, mime_type, is_owner, file_size, modified_date, "
                   f"viewed_by_me_date, trashed FROM items WHERE stable_id={stable_id}")
    return cursor.fetchone()


# TODO: check if there is multiple logged in accounts
def get_last_sync(drivefs_path):
    experiments_db = sqlite3.connect(os.path.join(drivefs_path, "experiments.db"))
    cursor = experiments_db.cursor()
    cursor.execute("SELECT value FROM PhenotypeValues WHERE key='last_sync'")
    return int(cursor.fetchone()[0])


def get_last_pid(drivefs_path):
    with open(os.path.join(drivefs_path, 'pid.txt')) as pid_file:
        return pid_file.read()


# TODO: complete after finalizing the roots research
def get_connected_devices(drivefs_path):
    root_preference_db = sqlite3.connect(os.path.join(drivefs_path, "root_preference_sqlite.db"))
    cursor = root_preference_db.cursor()
    cursor.execute("SELECT media_id, name, last_mount_point, capacity, ignored FROM media")
    return cursor.fetchall()


def get_max_root_ids(drivefs_path):
    root_preference_db = sqlite3.connect(os.path.join(drivefs_path, "root_preference_sqlite.db"))
    cursor = root_preference_db.cursor()
    cursor.execute("SELECT value FROM max_ids WHERE id_type='max_root_id'")
    max_root_ids = cursor.fetchone()
    if max_root_ids:
        return int(max_root_ids[0])
    return -1


def get_mirroring_roots(drivefs_path):
    root_preference_db = sqlite3.connect(os.path.join(drivefs_path, "root_preference_sqlite.db"))
    cursor = root_preference_db.cursor()
    cursor.execute("SELECT account_token, root_id, media_id, title, root_path, sync_type, destination, "
                   "last_seen_absolute_path FROM roots")
    return cursor.fetchall()


def get_item_properties(drivefs_path, account_id, item_id):
    account_profile = os.path.join(drivefs_path, account_id)
    metadata_sqlite_db = sqlite3.connect(os.path.join(account_profile, "metadata_sqlite_db"))
    cursor = metadata_sqlite_db.cursor()
    cursor.execute(f"SELECT key, value FROM item_properties WHERE item_stable_id={item_id}")
    item_properties = {}
    for item_property in cursor.fetchall():
        item_properties[item_property[0]] = item_property[1]
    return item_properties


def get_target_stable_id(drivefs_path, account_id, shortcut_stable_id):
    account_profile = os.path.join(drivefs_path, account_id)
    metadata_sqlite_db = sqlite3.connect(os.path.join(account_profile, "metadata_sqlite_db"))
    cursor = metadata_sqlite_db.cursor()
    cursor.execute(f"SELECT target_stable_id FROM shortcut_details WHERE shortcut_stable_id={shortcut_stable_id}")
    shortcut_stable_id = cursor.fetchone()
    if shortcut_stable_id:
        return int(shortcut_stable_id[0])
    return 0


def get_shared_with_me_without_link(drivefs_path, account_id):
    account_profile = os.path.join(drivefs_path, account_id)
    metadata_sqlite_db = sqlite3.connect(os.path.join(account_profile, "metadata_sqlite_db"))
    cursor = metadata_sqlite_db.cursor()
    cursor.execute("SELECT is_folder, stable_id, id, local_title, mime_type, is_owner, file_size, modified_date, "
                   "viewed_by_me_date, trashed FROM items "
                   "LEFT JOIN stable_parents ON items.stable_id = stable_parents.item_stable_id "
                   "LEFT JOIN shortcut_details ON items.stable_id = shortcut_details.target_stable_id "
                   "WHERE items.is_owner=0 AND items.shared_with_me_date=1 AND stable_parents.item_stable_id IS NULL "
                   "AND shortcut_details.target_stable_id IS NULL "
                   "ORDER BY items.stable_id")
    return cursor.fetchall()
