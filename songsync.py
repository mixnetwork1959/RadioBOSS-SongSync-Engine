# ==========================================================
# RadioBOSS SongSync
# Version 0.1.0
# songsync.py
# ==========================================================

from __future__ import annotations

import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

try:
    import mysql.connector
    from mysql.connector import Error as MySQLError
except ImportError:
    print("ERROR: mysql-connector-python is not installed.")
    print("Install it with:")
    print("    py -m pip install -r requirements.txt")
    sys.exit(1)

try:
    from config import (
        DB_HOST,
        DB_PORT,
        DB_NAME,
        DB_USER,
        DB_PASSWORD,
        DB_CHARSET,
        SHOW_EXAMPLES,
        EXAMPLE_LIMIT,
    )
except ImportError:
    print("ERROR: config.py was not found.")
    print("Copy config.example.py to config.py and enter your MySQL settings.")
    sys.exit(1)


VERSION = "0.1.0"


@dataclass(frozen=True)
class Song:
    track_id: int
    artist: str
    title: str
    filename: str
    valid: int | None
    disabled: int | None

    @property
    def display_key(self) -> tuple[str, str]:
        return (
            normalize_text(self.artist),
            normalize_text(self.title),
        )


def normalize_text(value: str) -> str:
    """Normalize text for duplicate comparison without altering source data."""
    return " ".join((value or "").casefold().split())


def connect_database():
    """Open a read-only-use MySQL connection.

    The MySQL account itself should ideally have SELECT permission only.
    """
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        charset=DB_CHARSET,
        use_unicode=True,
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
        (DB_NAME,),
    )

    found = {row[0] for row in cursor.fetchall()}
    cursor.close()

    missing = required - found

    if missing:
        raise RuntimeError(
            "Required RadioBOSS table(s) missing: " + ", ".join(sorted(missing))
        )


def load_songs(connection) -> list[Song]:
    """Read the fields needed by the website song request system."""
    sql = """
        SELECT
            t.track_id,
            t.fn AS filename,
            t.valid,
            t.disablesong,
            COALESCE(i.artist, '') AS artist,
            COALESCE(i.title, '') AS title
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
                valid=row["valid"],
                disabled=row["disablesong"],
            )
        )

    cursor.close()
    return songs


def is_usable(song: Song) -> bool:
    """A song is usable for the online request database."""
    if not song.filename:
        return False

    if not song.artist or not song.title:
        return False

    if song.valid is not None and int(song.valid) == 0:
        return False

    if song.disabled is not None and int(song.disabled) != 0:
        return False

    return True


def group_duplicates(songs: Iterable[Song]) -> dict[tuple[str, str], list[Song]]:
    groups: dict[tuple[str, str], list[Song]] = defaultdict(list)

    for song in songs:
        groups[song.display_key].append(song)

    return {
        key: entries
        for key, entries in groups.items()
        if len(entries) > 1
    }


def print_report(all_songs: list[Song]) -> None:
    usable = [song for song in all_songs if is_usable(song)]

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

    groups: dict[tuple[str, str], list[Song]] = defaultdict(list)
    for song in usable:
        groups[song.display_key].append(song)

    unique_songs = len(groups)
    duplicate_records = len(usable) - unique_songs
    duplicate_groups = sum(1 for entries in groups.values() if len(entries) > 1)

    print()
    print("=" * 62)
    print(f"RadioBOSS SongSync v{VERSION}")
    print("=" * 62)
    print(f"Database:                 {DB_NAME}")
    print(f"Database records:         {len(all_songs):>10}")
    print(f"Usable song records:      {len(usable):>10}")
    print(f"Unique artist/title:      {unique_songs:>10}")
    print(f"Duplicate records:        {duplicate_records:>10}")
    print(f"Duplicate groups:         {duplicate_groups:>10}")
    print(f"Missing filename:         {missing_filename:>10}")
    print(f"Missing artist/title:     {missing_metadata:>10}")
    print(f"Invalid records:          {invalid:>10}")
    print(f"Disabled records:         {disabled:>10}")
    print("=" * 62)

    if SHOW_EXAMPLES:
        print()
        print(f"First {min(EXAMPLE_LIMIT, len(usable))} usable songs:")
        print("-" * 62)

        for song in usable[:EXAMPLE_LIMIT]:
            print(
                f"{song.track_id:>8} | "
                f"{song.artist} - {song.title}"
            )
            print(f"         {song.filename}")

    duplicates = group_duplicates(usable)

    if SHOW_EXAMPLES and duplicates:
        print()
        print(f"First {min(EXAMPLE_LIMIT, len(duplicates))} duplicate groups:")
        print("-" * 62)

        for entries in list(duplicates.values())[:EXAMPLE_LIMIT]:
            first = entries[0]
            print(f"{first.artist} - {first.title}")

            for song in entries:
                print(f"  Track ID {song.track_id}: {song.filename}")

    print()
    print("Analysis completed. No RadioBOSS data was changed.")


def main() -> int:
    print(f"RadioBOSS SongSync v{VERSION}")
    print("Connecting to RadioBOSS MySQL database...")

    connection = None

    try:
        connection = connect_database()

        if not connection.is_connected():
            raise RuntimeError("MySQL connection was not established.")

        verify_required_tables(connection)

        print("Connection successful.")
        print("Reading tracks2 and taginfo...")

        songs = load_songs(connection)
        print_report(songs)

        return 0

    except MySQLError as exc:
        print()
        print("MYSQL ERROR:")
        print(exc)
        return 1

    except Exception as exc:
        print()
        print("ERROR:")
        print(exc)
        return 1

    finally:
        if connection is not None and connection.is_connected():
            connection.close()


if __name__ == "__main__":
    raise SystemExit(main())
