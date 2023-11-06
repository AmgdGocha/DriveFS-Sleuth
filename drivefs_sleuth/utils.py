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
    cursor.execute("SELECT parent_stable_id, item_stable_id FROM stable_parents ORDER BY parent_stable_id")
    return cursor.fetchall()


def get_item_info(drivefs_path, account_id, stable_id):
    account_profile = os.path.join(drivefs_path, account_id)
    metadata_sqlite_db = sqlite3.connect(os.path.join(account_profile, "metadata_sqlite_db"))
    cursor = metadata_sqlite_db.cursor()
    cursor.execute(f"SELECT is_folder, stable_id, local_title, mime_type, is_owner, file_size, modified_date, "
                   f"viewed_by_me_date, trashed FROM items WHERE stable_id={stable_id}")
    return cursor.fetchone()


# TODO: check if there is multiple logged in accounts
def get_last_sync(drivefs_path):
    experiments_db = sqlite3.connect(os.path.join(drivefs_path, "experiments.db"))
    cursor = experiments_db.cursor()
    cursor.execute("SELECT value FROM PhenotypeValues WHERE key='last_sync'")
    return int(cursor.fetchone()[0])
