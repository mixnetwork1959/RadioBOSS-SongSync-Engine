# ==========================================================
# RadioBOSS SongSync Engine
# Version 1.0.0
# songsync.py
# ==========================================================

from __future__ import annotations

import hashlib
import json
import sys
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    print("ERROR: mysql-connector-python is not installed.")
    print("Install it with:")
    print("    py -m pip install -r requirements.txt")
    raise SystemExit(1)


VERSION = "1.0.0"


def load_config():
    try:
        import config
    except ModuleNotFoundError as exc:
        if exc.name == "config":
            print("ERROR: config.py was not found.")
            print("Copy config.example.py to config.py and enter your settings.")
            raise SystemExit(1) from exc

        print("ERROR while loading config.py:")
        print(exc)
        raise SystemExit(1) from exc
    except Exception as exc:
        print("ERROR while loading config.py:")
        print(f"{type(exc).__name__}: {exc}")
        raise SystemExit(1) from exc

    required = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "DB_CHARSET",
        "PUBLIC_EXPORT_DIR",
        "PRIVATE_EXPORT_DIR",
        "SHOW_EXAMPLES",
        "EXAMPLE_LIMIT",
    ]

    missing = [name for name in required if not hasattr(config, name)]

    if missing:
        print("ERROR: Missing setting(s) in config.py:")
        for name in missing:
            print(f"  - {name}")
        raise SystemExit(1)

    return config


CONFIG = load_config()

PUBLIC_DIR = Path(CONFIG.PUBLIC_EXPORT_DIR)
PRIVATE_DIR = Path(CONFIG.PRIVATE_EXPORT_DIR)

SONGS_FILE = PUBLIC_DIR / "songs.json"
ARTISTS_FILE = PUBLIC_DIR / "artists.json"
GENRES_FILE = PUBLIC_DIR / "genres.json"
INFO_FILE = PUBLIC_DIR / "info.json"

LOOKUP_FILE = PRIVATE_DIR / "lookup.json"
DUPLICATE_LOG_FILE = PRIVATE_DIR / "duplicates.log"


@dataclass(frozen=True)
class Song:
    track_id: int
    artist: str
    title: str
    filename: str
    genre: str
    valid: int | None
    disabled: int | None

    @property
    def duplicate_key(self) -> tuple[str, str]:
        return (
            normalize_text(self.artist),
            normalize_text(self.title),
        )


def normalize_text(value: str) -> str:
    return " ".join((value or "").casefold().split())


def connect_database():
    return mysql.connector.connect(
        host=CONFIG.DB_HOST,
        port=CONFIG.DB_PORT,
        database=CONFIG.DB_NAME,
        user=CONFIG.DB_USER,
        password=CONFIG.DB_PASSWORD,
        charset=CONFIG.DB_CHARSET,
        use_unicode=True,
        use_pure=True,
        autocommit=True,
        connection_timeout=10,
    )


def verify_required_tables(connection) -> None:
    required = {"tracks2", "taginfo"}

    cursor = connection.cursor()
    cursor.execute(
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_name IN ('tracks2', 'taginfo')
        """,
        (CONFIG.DB_NAME,),
    )

    found = {row[0] for row in cursor.fetchall()}
    cursor.close()

    missing = required - found

    if missing:
        raise RuntimeError(
            "Required RadioBOSS table(s) missing: " + ", ".join(sorted(missing))
        )


def load_songs(connection) -> list[Song]:
    sql = """
        SELECT
            t.track_id,
            t.fn AS filename,
            t.valid,
            t.disablesong,
            COALESCE(i.artist, '') AS artist,
            COALESCE(i.title, '') AS title,
            COALESCE(i.genre, '') AS genre
        FROM tracks2 AS t
        LEFT JOIN taginfo AS i
            ON i.track_id = t.track_id
        ORDER BY t.track_id
    """

    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql)

    songs: list[Song] = []

    for row in cursor:
        songs.append(
            Song(
                track_id=int(row["track_id"]),
                artist=(row["artist"] or "").strip(),
                title=(row["title"] or "").strip(),
                filename=(row["filename"] or "").strip(),
                genre=(row["genre"] or "").strip(),
                valid=row["valid"],
                disabled=row["disablesong"],
            )
        )

    cursor.close()
    return songs


def is_usable(song: Song) -> bool:
    if not song.filename:
        return False

    if not song.artist or not song.title:
        return False

    if song.valid is not None and int(song.valid) == 0:
        return False

    if song.disabled is not None and int(song.disabled) != 0:
        return False

    return True


def create_unique_catalog(
    songs: Iterable[Song],
) -> tuple[list[Song], dict[tuple[str, str], list[Song]]]:
    unique: dict[tuple[str, str], Song] = {}
    groups: dict[tuple[str, str], list[Song]] = defaultdict(list)

    for song in songs:
        key = song.duplicate_key
        groups[key].append(song)

        if key not in unique:
            unique[key] = song

    duplicate_groups = {
        key: entries
        for key, entries in groups.items()
        if len(entries) > 1
    }

    return list(unique.values()), duplicate_groups


def atomic_json_write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")

    with temp_path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write("\n")

    temp_path.replace(path)


def catalog_hash(unique_songs: list[Song]) -> str:
    digest = hashlib.sha256()

    for song in unique_songs:
        row = (
            f"{song.track_id}\0{song.artist}\0{song.title}\0"
            f"{song.filename}\0{song.genre}\n"
        )
        digest.update(row.encode("utf-8"))

    return digest.hexdigest()


def write_exports(
    all_songs: list[Song],
    usable_songs: list[Song],
    unique_songs: list[Song],
    duplicate_groups: dict[tuple[str, str], list[Song]],
) -> None:
    generated_at = datetime.now().astimezone().isoformat(timespec="seconds")

    public_songs = [
        {
            "track_id": song.track_id,
            "artist": song.artist,
            "title": song.title,
        }
        for song in unique_songs
    ]

    private_lookup = {
        str(song.track_id): {
            "filename": song.filename,
        }
        for song in unique_songs
    }

    artists = sorted(
        {song.artist for song in unique_songs if song.artist},
        key=str.casefold,
    )

    genres = sorted(
        {song.genre for song in unique_songs if song.genre},
        key=str.casefold,
    )

    info = {
        "generator": "RadioBOSS SongSync Engine",
        "version": VERSION,
        "generated_at": generated_at,
        "database": CONFIG.DB_NAME,
        "database_records": len(all_songs),
        "usable_records": len(usable_songs),
        "unique_songs": len(unique_songs),
        "duplicate_records": len(usable_songs) - len(unique_songs),
        "duplicate_groups": len(duplicate_groups),
        "artists": len(artists),
        "genres": len(genres),
        "catalog_hash": catalog_hash(unique_songs),
    }

    atomic_json_write(SONGS_FILE, public_songs)
    atomic_json_write(LOOKUP_FILE, private_lookup)
    atomic_json_write(ARTISTS_FILE, artists)
    atomic_json_write(GENRES_FILE, genres)
    atomic_json_write(INFO_FILE, info)


def write_duplicate_log(
    duplicate_groups: dict[tuple[str, str], list[Song]],
) -> None:
    DUPLICATE_LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    with DUPLICATE_LOG_FILE.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(f"RadioBOSS SongSync Engine v{VERSION}\n")
        handle.write("Duplicate report\n")
        handle.write("=" * 72 + "\n\n")

        for entries in duplicate_groups.values():
            kept = entries[0]

            handle.write(f"{kept.artist} - {kept.title}\n")
            handle.write(
                f"KEPT    Track ID {kept.track_id}: {kept.filename}\n"
            )

            for ignored in entries[1:]:
                handle.write(
                    f"IGNORED Track ID {ignored.track_id}: {ignored.filename}\n"
                )

            handle.write("\n")


def print_report(
    all_songs: list[Song],
    usable_songs: list[Song],
    unique_songs: list[Song],
    duplicate_groups: dict[tuple[str, str], list[Song]],
) -> None:
    missing_filename = sum(1 for song in all_songs if not song.filename)
    missing_metadata = sum(
        1 for song in all_songs if not song.artist or not song.title
    )
    invalid = sum(
        1
        for song in all_songs
        if song.valid is not None and int(song.valid) == 0
    )
    disabled = sum(
        1
        for song in all_songs
        if song.disabled is not None and int(song.disabled) != 0
    )

    print()
    print("=" * 66)
    print(f"RadioBOSS SongSync Engine v{VERSION}")
    print("=" * 66)
    print(f"Database:                     {CONFIG.DB_NAME}")
    print(f"Database records:             {len(all_songs):>10}")
    print(f"Usable song records:          {len(usable_songs):>10}")
    print(f"Unique artist/title:          {len(unique_songs):>10}")
    print(f"Duplicate records ignored:    {len(usable_songs)-len(unique_songs):>10}")
    print(f"Duplicate groups:             {len(duplicate_groups):>10}")
    print(f"Missing filename:             {missing_filename:>10}")
    print(f"Missing artist/title:         {missing_metadata:>10}")
    print(f"Invalid records:              {invalid:>10}")
    print(f"Disabled records:             {disabled:>10}")
    print("=" * 66)

    if CONFIG.SHOW_EXAMPLES:
        limit = min(CONFIG.EXAMPLE_LIMIT, len(unique_songs))
        print()
        print(f"First {limit} public search entries:")
        print("-" * 66)

        for song in unique_songs[:limit]:
            print(f"{song.track_id:>8} | {song.artist} - {song.title}")

    print()
    print("Public files:")
    print(f"  {SONGS_FILE.resolve()}")
    print(f"  {ARTISTS_FILE.resolve()}")
    print(f"  {GENRES_FILE.resolve()}")
    print(f"  {INFO_FILE.resolve()}")
    print()
    print("Private files:")
    print(f"  {LOOKUP_FILE.resolve()}")
    print(f"  {DUPLICATE_LOG_FILE.resolve()}")
    print()
    print("Export completed. No RadioBOSS data was changed.")


def main() -> int:
    print(f"RadioBOSS SongSync Engine v{VERSION}")
    print("Connecting to RadioBOSS MySQL database...")

    connection = None

    try:
        connection = connect_database()

        if not connection.is_connected():
            raise RuntimeError("MySQL connection was not established.")

        verify_required_tables(connection)

        print("Connection successful.")
        print("Reading tracks2 and taginfo...")

        all_songs = load_songs(connection)
        usable_songs = [song for song in all_songs if is_usable(song)]

        print("Creating unique song catalog...")
        unique_songs, duplicate_groups = create_unique_catalog(usable_songs)

        print("Writing public and private JSON files...")
        write_exports(
            all_songs,
            usable_songs,
            unique_songs,
            duplicate_groups,
        )
        write_duplicate_log(duplicate_groups)

        print_report(
            all_songs,
            usable_songs,
            unique_songs,
            duplicate_groups,
        )

        return 0

    except MySQLError as exc:
        print()
        print("MYSQL ERROR:")
        print(exc)
        return 1

    except Exception as exc:
        print()
        print("ERROR:")
        print(f"{type(exc).__name__}: {exc}")
        return 1

    finally:
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
