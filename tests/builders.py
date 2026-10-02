"""
Author: Amged Wageh
Email: amged_wageh@outlook.com
LinkedIn: https://www.linkedin.com/in/amgedwageh/
Description: synthetic, PII-free DriveFS artifact builders used by the test suite.
"""

import os
import sys

_TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
_SRC_DIR = os.path.abspath(os.path.join(_TESTS_DIR, os.pardir, "src"))
for _dir in (_SRC_DIR, _TESTS_DIR):
    if _dir not in sys.path:
        sys.path.insert(0, _dir)

import sqlite3

import blackboxprotobuf

ACCOUNT_ID_1 = "111111111111111111111"
ACCOUNT_ID_2 = "222222222222222222222"
UNKNOWN_ACCOUNT_ID = "999999999999999999999"
EMAIL_1 = "testuser@example.com"
EMAIL_2 = "seconduser@example.com"
DISPLAY_NAME_1 = "Test User"
DISPLAY_NAME_2 = "Second User"
PHOTO_URL_1 = "https://example.com/avatar1.png"
PHOTO_URL_2 = "https://example.com/avatar2.png"

LAST_SYNC_SECONDS = 1704067200
LAST_SYNC_MS = 1704067200000
LAST_SYNC_UTC_STR = "2024-01-01 00:00:00+00:00"
LAST_PID = "4242"

FOLDER_MIME = "application/vnd.google-apps.folder"
SHORTCUT_MIME = "application/vnd.google-apps.shortcut"
DOCX_MIME = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
TXT_MIME = "text/plain"
PDF_MIME = "application/pdf"

MD5_A = "a" * 32
MD5_B = "b" * 32
MD5_C = "c" * 32
MD5_D = "d" * 32
MD5_E = "e" * 32

STABLE_ROOT_1 = 100
STABLE_REPORT_FILE = 200
STABLE_PROJECTS_DIR = 300
STABLE_NOTES_FILE = 400
STABLE_REPORT_SHORTCUT = 500
STABLE_SHARED_FILE = 600
STABLE_ORPHAN_DIR = 700
STABLE_ORPHAN_CHILD = 750
STABLE_DELETED_FILE = 800
STABLE_DELETED_FOLDER = 820
STABLE_MISSING_CHILD = 900

TITLE_ROOT_1 = "My Drive"
TITLE_REPORT_FILE = "Report.docx"
TITLE_PROJECTS_DIR = "Projects"
TITLE_NOTES_FILE = "notes.txt"
TITLE_REPORT_SHORTCUT = "Report Shortcut"
TITLE_SHARED_FILE = "SharedDoc.pdf"
TITLE_ORPHAN_DIR = "Orphan Folder"
TITLE_ORPHAN_CHILD = "orphan_child.txt"
TITLE_DELETED_FILE = "Deleted Report.pdf"
TITLE_DELETED_FOLDER = "Deleted Folder"

URL_ID_PREFIX = "url-id-"

CACHE_FILE_400 = "cachefile-400"
CACHE_CONTENT_400 = b"FAKE CACHED CONTENT FOR NOTES.TXT"
THUMBNAIL_CONTENT_400 = b"FAKE THUMBNAIL BYTES"

MIRROR_MD5_LOCAL = "11" * 16
MIRROR_MD5_CLOUD = "22" * 16

MEDIA_ID = "media-1"
MEDIA_NAME = "Local Disk"
MEDIA_MOUNT_POINT = "C:\\"
MEDIA_CAPACITY = 500000000000
MEDIA_CAPACITY_GB = 500.0

MIRROR_ROOT_TITLE = "My Drive Mirror"
MIRROR_ROOT_PATH = "C:\\DriveMirror"

ITEMS_DDL = """
CREATE TABLE items (
    stable_id INTEGER PRIMARY KEY NOT NULL,
    id TEXT UNIQUE NOT NULL,
    proto BLOB,
    trashed BOOLEAN NOT NULL,
    is_owner BOOLEAN NOT NULL,
    mime_type TEXT NOT NULL COLLATE NOCASE,
    is_folder BOOLEAN NOT NULL,
    modified_date INTEGER,
    shared_with_me_date INTEGER,
    viewed_by_me_date INTEGER,
    file_size INTEGER,
    is_tombstone BOOLEAN NOT NULL,
    local_title TEXT,
    subscribed BOOLEAN NOT NULL,
    team_drive_stable_id INTEGER,
    local_title_tokenized TEXT
);
CREATE TABLE stable_parents (
    item_stable_id INTEGER NOT NULL,
    parent_stable_id INTEGER NOT NULL,
    local_title_hash INTEGER NOT NULL,
    PRIMARY KEY (item_stable_id, parent_stable_id)
);
CREATE TABLE properties (
    property TEXT PRIMARY KEY NOT NULL,
    value BLOB
);
CREATE TABLE item_properties (
    item_stable_id INTEGER NOT NULL,
    key TEXT NOT NULL,
    value BLOB NOT NULL,
    value_type INTEGER NOT NULL,
    PRIMARY KEY (item_stable_id, key)
);
CREATE TABLE deleted_items (
    stable_id INTEGER PRIMARY KEY NOT NULL,
    proto BLOB
);
CREATE TABLE shortcut_details (
    shortcut_stable_id INTEGER PRIMARY KEY NOT NULL,
    target_stable_id INTEGER NOT NULL,
    target_mime_type TEXT NOT NULL
);
"""

MIRROR_DDL = """
CREATE TABLE mirror_item (
    local_stable_id INTEGER PRIMARY KEY,
    stable_id INTEGER NOT NULL,
    inode INTEGER NOT NULL,
    volume TEXT NOT NULL,
    parent_local_stable_id INTEGER,
    local_filename TEXT,
    cloud_filename TEXT,
    local_mtime_ms INTEGER,
    cloud_mtime_ms INTEGER,
    local_md5_checksum TEXT,
    cloud_md5_checksum TEXT,
    local_size INTEGER,
    cloud_size INTEGER,
    local_type INTEGER NOT NULL,
    cloud_type INTEGER NOT NULL,
    local_version INTEGER NOT NULL,
    cloud_version INTEGER NOT NULL,
    storage_policy INTEGER NOT NULL,
    shared BOOLEAN,
    read_only BOOLEAN,
    target_version INTEGER,
    is_root BOOLEAN,
    UNIQUE (stable_id, parent_local_stable_id),
    UNIQUE (parent_local_stable_id, local_filename)
);
"""

EXPERIMENTS_DDL = """
CREATE TABLE PhenotypeValues (
    Key TEXT PRIMARY KEY NOT NULL,
    Value BLOB NOT NULL
);
"""

ROOT_PREFERENCE_DDL = """
CREATE TABLE media (
    media_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    last_mount_point TEXT NOT NULL,
    fs_type INTEGER NOT NULL,
    device_type INTEGER NOT NULL,
    capacity INTEGER NOT NULL,
    ignored BOOL NOT NULL
);
CREATE TABLE max_ids (
    id_type TEXT PRIMARY KEY,
    value INTEGER NOT NULL
);
CREATE TABLE roots (
    root_id INTEGER PRIMARY KEY,
    metadata BLOB,
    media_id TEXT NOT NULL,
    title TEXT NOT NULL,
    root_path TEXT NOT NULL,
    account_token TEXT NOT NULL,
    sync_type INTEGER NOT NULL,
    destination INTEGER NOT NULL,
    medium INTEGER NOT NULL,
    state INTEGER NOT NULL,
    one_shot BOOL NOT NULL,
    is_my_drive BOOL NOT NULL,
    doc_id TEXT NOT NULL,
    last_seen_absolute_path TEXT NOT NULL,
    UNIQUE (media_id, root_path, destination)
);
"""

ACCOUNT_TYPEDEF = {
    "1": {"type": "int"},
    "2": {
        "type": "message",
        "field_order": ["1"],
        "message_typedef": {
            "1": {
                "type": "message",
                "field_order": ["1", "2", "3", "5", "8"],
                "message_typedef": {
                    "1": {"type": "int"},
                    "2": {"type": "string"},
                    "3": {"type": "string"},
                    "5": {"type": "string"},
                    "8": {"type": "string"},
                },
            }
        },
    },
}

CONTENT_ENTRY_TYPEDEF = {
    "1": {"type": "string"},
    "2": {"type": "string"},
    "3": {"type": "string"},
    "4": {"type": "int"},
}

ITEM_PROTO_TYPEDEF = {
    "1": {"type": "string"},
    "3": {"type": "string"},
    "4": {"type": "string"},
    "45": {"type": "string"},
    "48": {"type": "string"},
}

DELETED_ITEM_TYPEDEF = {
    "1": {"type": "string"},
    "2": {"type": "string"},
    "3": {"type": "string"},
    "4": {"type": "string"},
    "5": {"type": "int"},
    "7": {"type": "int"},
    "10": {"type": "int"},
    "11": {"type": "int"},
    "13": {"type": "int"},
    "14": {"type": "int"},
    "48": {"type": "string"},
    "63": {"type": "int"},
}


def _encode(value, message_type):
    return blackboxprotobuf.encode_message(value, message_type)


def encode_account_proto(display_name, photo_url):
    return _encode(
        {
            "1": 1,
            "2": {"1": {"1": 1, "2": "", "3": display_name, "5": photo_url, "8": ""}},
        },
        ACCOUNT_TYPEDEF,
    )


def encode_item_proto(url_id, title, mime_type, file_type, md5):
    return _encode(
        {"1": url_id, "3": title, "4": mime_type, "45": file_type, "48": md5},
        ITEM_PROTO_TYPEDEF,
    )


def encode_content_entry(cache_filename):
    return _encode(
        {"1": cache_filename, "2": "", "3": "", "4": 1},
        CONTENT_ENTRY_TYPEDEF,
    )


def encode_deleted_item_proto(url_id, title, mime_type, md5="", is_folder=False):
    value = {
        "1": url_id,
        "2": "",
        "3": title,
        "4": mime_type,
        "5": 1,
        "7": 1,
        "10": 0,
        "11": LAST_SYNC_MS,
        "13": LAST_SYNC_MS,
        "63": 1,
    }
    if not is_folder:
        value["14"] = 999
        value["48"] = md5
    return _encode(value, DELETED_ITEM_TYPEDEF)


def url_id(stable_id):
    return f"{URL_ID_PREFIX}{stable_id}"


def _insert_item(db, stable_id, title, mime_type, is_folder, is_owner, file_size,
                 modified_ms, viewed_ms, trashed, shared_with_me_date, proto):
    db.execute(
        "INSERT INTO items (stable_id, id, proto, trashed, is_owner, mime_type, is_folder, modified_date, "
        "shared_with_me_date, viewed_by_me_date, file_size, is_tombstone, local_title, subscribed, "
        "team_drive_stable_id, local_title_tokenized) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (stable_id, url_id(stable_id), proto, trashed, is_owner, mime_type, is_folder, modified_ms,
         shared_with_me_date, viewed_ms, file_size, 0, title, 1, None, None),
    )


def _write_experiments_db(drivefs_path, accounts, last_sync_seconds):
    db = sqlite3.connect(os.path.join(drivefs_path, "experiments.db"))
    db.executescript(EXPERIMENTS_DDL)
    if accounts:
        db.execute(
            "INSERT INTO PhenotypeValues (Key, Value) VALUES (?, ?)",
            ("account_ids", ",".join(accounts).encode("utf-8")),
        )
    if last_sync_seconds is not None:
        db.execute(
            "INSERT INTO PhenotypeValues (Key, Value) VALUES (?, ?)",
            ("last_sync", str(last_sync_seconds).encode("utf-8")),
        )
    db.commit()
    db.close()


def _write_root_preference_db(drivefs_path, mirroring_account=None):
    db = sqlite3.connect(os.path.join(drivefs_path, "root_preference_sqlite.db"))
    db.executescript(ROOT_PREFERENCE_DDL)
    db.execute(
        "INSERT INTO media (media_id, name, last_mount_point, fs_type, device_type, capacity, ignored) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (MEDIA_ID, MEDIA_NAME, MEDIA_MOUNT_POINT, 3, 1, MEDIA_CAPACITY, 0),
    )
    db.execute(
        "INSERT INTO max_ids (id_type, value) VALUES (?, ?)",
        ("max_root_id", 1),
    )
    if mirroring_account:
        db.execute(
            "INSERT INTO roots (root_id, metadata, media_id, title, root_path, account_token, sync_type, "
            "destination, medium, state, one_shot, is_my_drive, doc_id, last_seen_absolute_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (1, None, MEDIA_ID, MIRROR_ROOT_TITLE, MIRROR_ROOT_PATH, mirroring_account,
             1, 1, 1, 1, 0, 1, "root-1", MIRROR_ROOT_PATH),
        )
    db.commit()
    db.close()


def _write_root_files(drivefs_path, accounts, last_sync_seconds=LAST_SYNC_SECONDS,
                      with_preferences=True, mirroring_account=None):
    os.makedirs(os.path.join(drivefs_path, "Logs"), exist_ok=True)
    with open(os.path.join(drivefs_path, "Logs", "drive_fs.txt"), "w", encoding="utf-8") as logs_file:
        for account_id, email in accounts:
            logs_file.write(
                f"2024-01-01 00:00:00 INFO drive_fs[1234]: sign in detected: {email} ({account_id})\n"
            )
    with open(os.path.join(drivefs_path, "pid.txt"), "w", encoding="utf-8") as pid_file:
        pid_file.write(LAST_PID)
    _write_experiments_db(drivefs_path, [account_id for account_id, _ in accounts], last_sync_seconds)
    if with_preferences:
        _write_root_preference_db(drivefs_path, mirroring_account=mirroring_account)


def _write_metadata_db(profile_path, items, parents, item_properties, shortcut_details, deleted_items,
                       account_blob):
    db = sqlite3.connect(os.path.join(profile_path, "metadata_sqlite_db"))
    db.executescript(ITEMS_DDL)
    for item in items:
        _insert_item(db, *item)
    for parent_stable_id, item_stable_id in parents:
        db.execute(
            "INSERT INTO stable_parents (item_stable_id, parent_stable_id, local_title_hash) VALUES (?, ?, ?)",
            (item_stable_id, parent_stable_id, 0),
        )
    for item_stable_id, key, value, value_type in item_properties:
        db.execute(
            "INSERT INTO item_properties (item_stable_id, key, value, value_type) VALUES (?, ?, ?, ?)",
            (item_stable_id, key, value, value_type),
        )
    for shortcut_stable_id, target_stable_id, target_mime_type in shortcut_details:
        db.execute(
            "INSERT INTO shortcut_details (shortcut_stable_id, target_stable_id, target_mime_type) "
            "VALUES (?, ?, ?)",
            (shortcut_stable_id, target_stable_id, target_mime_type),
        )
    for stable_id, proto in deleted_items:
        db.execute(
            "INSERT INTO deleted_items (stable_id, proto) VALUES (?, ?)",
            (stable_id, proto),
        )
    if account_blob is not None:
        db.execute(
            "INSERT INTO properties (property, value) VALUES (?, ?)",
            ("driveway_account", account_blob),
        )
    db.commit()
    db.close()


def _write_mirror_db(profile_path):
    db = sqlite3.connect(os.path.join(profile_path, "mirror_sqlite.db"))
    db.executescript(MIRROR_DDL)
    db.execute(
        "INSERT INTO mirror_item (local_stable_id, stable_id, inode, volume, parent_local_stable_id, "
        "local_filename, cloud_filename, local_mtime_ms, cloud_mtime_ms, local_md5_checksum, "
        "cloud_md5_checksum, local_size, cloud_size, local_type, cloud_type, local_version, cloud_version, "
        "storage_policy, shared, read_only, target_version, is_root) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (1, 888, 1, "C:", STABLE_ROOT_1, "local_doc.docx", "cloud_doc.docx", LAST_SYNC_MS, LAST_SYNC_MS,
         MIRROR_MD5_LOCAL, MIRROR_MD5_CLOUD, 100, 200, 1, 2, 1, 2, 0, 0, 0, None, 0),
    )
    db.commit()
    db.close()


class Fixture:
    def __init__(self, drivefs_path):
        self.drivefs_path = drivefs_path
        self.content_entry_blob_400 = None
        self.cache_file_path_400 = None
        self.thumbnail_file_path_400 = None

    def profile_path(self, account_id=ACCOUNT_ID_1):
        return os.path.join(self.drivefs_path, account_id)

    def content_cache_path(self, filename):
        return os.path.abspath(os.path.join(self.profile_path(), "content_cache", "d0", filename))

    def thumbnail_path(self, filename):
        return os.path.abspath(os.path.join(self.profile_path(), "thumbnails_cache", "d0", filename))


def _build_main_profile(drivefs_path):
    profile_path = os.path.join(drivefs_path, ACCOUNT_ID_1)
    os.makedirs(profile_path, exist_ok=True)

    items = [
        (STABLE_ROOT_1, TITLE_ROOT_1, FOLDER_MIME, 1, 1, 0, LAST_SYNC_MS, LAST_SYNC_MS, 0, 0, None),
        (STABLE_REPORT_FILE, TITLE_REPORT_FILE, DOCX_MIME, 0, 1, 123456, LAST_SYNC_MS, LAST_SYNC_MS, 0, 0,
         encode_item_proto(url_id(STABLE_REPORT_FILE), TITLE_REPORT_FILE, DOCX_MIME, "docx", MD5_B)),
        (STABLE_PROJECTS_DIR, TITLE_PROJECTS_DIR, FOLDER_MIME, 1, 1, 0, LAST_SYNC_MS, LAST_SYNC_MS, 0, 0, None),
        (STABLE_NOTES_FILE, TITLE_NOTES_FILE, TXT_MIME, 0, 1, 5000000, LAST_SYNC_MS, LAST_SYNC_MS, 0, 0,
         encode_item_proto(url_id(STABLE_NOTES_FILE), TITLE_NOTES_FILE, TXT_MIME, "txt", MD5_A)),
        (STABLE_REPORT_SHORTCUT, TITLE_REPORT_SHORTCUT, SHORTCUT_MIME, 1, 1, 0, LAST_SYNC_MS, LAST_SYNC_MS, 0, 0,
         None),
        (STABLE_SHARED_FILE, TITLE_SHARED_FILE, PDF_MIME, 0, 0, 654321, LAST_SYNC_MS, LAST_SYNC_MS, 0, 1,
         encode_item_proto(url_id(STABLE_SHARED_FILE), TITLE_SHARED_FILE, PDF_MIME, "pdf", MD5_D)),
        (STABLE_ORPHAN_DIR, TITLE_ORPHAN_DIR, FOLDER_MIME, 1, 1, 0, LAST_SYNC_MS, LAST_SYNC_MS, 0, 0, None),
        (STABLE_ORPHAN_CHILD, TITLE_ORPHAN_CHILD, TXT_MIME, 0, 1, 10, LAST_SYNC_MS, LAST_SYNC_MS, 0, 0, None),
    ]
    parents = [
        (STABLE_ROOT_1, STABLE_REPORT_FILE),
        (STABLE_ROOT_1, STABLE_PROJECTS_DIR),
        (STABLE_ROOT_1, STABLE_REPORT_SHORTCUT),
        (STABLE_ROOT_1, STABLE_MISSING_CHILD),
        (STABLE_PROJECTS_DIR, STABLE_NOTES_FILE),
        (STABLE_ORPHAN_DIR, STABLE_ORPHAN_CHILD),
    ]
    content_entry_blob = encode_content_entry(CACHE_FILE_400)
    item_properties = [
        (STABLE_NOTES_FILE, "content-entry", content_entry_blob, 1),
        (STABLE_PROJECTS_DIR, "folder_queried", "1", 1),
    ]
    shortcut_details = [(STABLE_REPORT_SHORTCUT, STABLE_REPORT_FILE, DOCX_MIME)]
    deleted_items = [
        (STABLE_DELETED_FILE,
         encode_deleted_item_proto(url_id(STABLE_DELETED_FILE), TITLE_DELETED_FILE, PDF_MIME, md5=MD5_C)),
        (STABLE_DELETED_FOLDER,
         encode_deleted_item_proto(url_id(STABLE_DELETED_FOLDER), TITLE_DELETED_FOLDER, FOLDER_MIME,
                                   is_folder=True)),
    ]
    account_blob = encode_account_proto(DISPLAY_NAME_1, PHOTO_URL_1)

    _write_metadata_db(profile_path, items, parents, item_properties, shortcut_details, deleted_items,
                       account_blob)
    _write_mirror_db(profile_path)

    cache_dir = os.path.join(profile_path, "content_cache", "d0")
    os.makedirs(cache_dir, exist_ok=True)
    cache_file_path = os.path.join(cache_dir, CACHE_FILE_400)
    with open(cache_file_path, "wb") as cache_file:
        cache_file.write(CACHE_CONTENT_400)

    thumbnails_dir = os.path.join(profile_path, "thumbnails_cache", "d0")
    os.makedirs(thumbnails_dir, exist_ok=True)
    thumbnail_file_path = os.path.join(thumbnails_dir, str(STABLE_NOTES_FILE))
    with open(thumbnail_file_path, "wb") as thumbnail_file:
        thumbnail_file.write(THUMBNAIL_CONTENT_400)

    return content_entry_blob, cache_file_path, thumbnail_file_path


def _build_secondary_profile(drivefs_path):
    profile_path = os.path.join(drivefs_path, ACCOUNT_ID_2)
    os.makedirs(profile_path, exist_ok=True)

    items = [
        (STABLE_ROOT_1, "Other Drive", FOLDER_MIME, 1, 1, 0, LAST_SYNC_MS, LAST_SYNC_MS, 0, 0, None),
        (210, "SecondFile.txt", TXT_MIME, 0, 1, 1024, LAST_SYNC_MS, LAST_SYNC_MS, 0, 0,
         encode_item_proto(url_id(210), "SecondFile.txt", TXT_MIME, "txt", MD5_E)),
    ]
    parents = [(STABLE_ROOT_1, 210)]
    account_blob = encode_account_proto(DISPLAY_NAME_2, PHOTO_URL_2)
    _write_metadata_db(profile_path, items, parents, [], [], [], account_blob)


def build_logged_in_fixture(drivefs_path, two_accounts=False):
    accounts = [(ACCOUNT_ID_1, EMAIL_1)]
    if two_accounts:
        accounts.append((ACCOUNT_ID_2, EMAIL_2))
    _write_root_files(drivefs_path, accounts, mirroring_account=ACCOUNT_ID_1)

    fixture = Fixture(drivefs_path)
    fixture.content_entry_blob_400, fixture.cache_file_path_400, fixture.thumbnail_file_path_400 = (
        _build_main_profile(drivefs_path)
    )
    if two_accounts:
        _build_secondary_profile(drivefs_path)
    return fixture


def build_not_logged_in_fixture(drivefs_path):
    _write_root_files(drivefs_path, [(ACCOUNT_ID_1, EMAIL_1)])
    return Fixture(drivefs_path)


def build_empty_fixture(drivefs_path):
    _write_root_files(drivefs_path, [], last_sync_seconds=None, with_preferences=False)
    return Fixture(drivefs_path)
