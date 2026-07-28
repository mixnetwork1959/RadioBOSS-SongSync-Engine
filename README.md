# RadioBOSS SongSync

Automatic song database synchronization for RadioBOSS.

## Version 0.1.0

This first development version analyzes a RadioBOSS MySQL database.

It:

- connects to the local RadioBOSS MySQL database;
- reads `tracks2` and `taginfo`;
- uses `track_id` as the unique RadioBOSS identifier;
- reads artist, title and the full filename;
- counts usable and invalid records;
- detects duplicate artist/title combinations;
- never changes the RadioBOSS database.

Website synchronization is not included yet.

## Requirements

- Windows 10 or Windows 11
- Python 3.11 or newer
- RadioBOSS using MySQL for additional track information
- MySQL user with read permission

A MySQL account with `SELECT` permission only is recommended.

## Installation

1. Download or clone this repository.
2. Open a command prompt in the project folder.
3. Install the dependency:

```text
py -m pip install -r requirements.txt
```

4. Copy:

```text
config.example.py
```

to:

```text
config.py
```

5. Enter the RadioBOSS MySQL connection details in `config.py`.
6. Run:

```text
py songsync.py
```

## Database query

SongSync joins the two RadioBOSS tables through `track_id`:

```sql
SELECT
    t.track_id,
    t.fn AS filename,
    t.valid,
    t.disablesong,
    i.artist,
    i.title
FROM tracks2 AS t
LEFT JOIN taginfo AS i
    ON i.track_id = t.track_id;
```

The `library_*` tables are deliberately not used for the song request
catalog. They only represent RadioBOSS library membership and may contain
old references after files or tracks have changed.

## Duplicate handling

`track_id` remains unique internally.

For the public song search, records with the same normalized artist and
title can later be displayed only once. Version 0.1.0 reports these duplicate
groups but does not remove or modify anything.

## Planned

- SQLite support
- HTTPS synchronization with the PHP website
- automatic synchronization after database changes
- Windows tray application
- start with Windows
- synchronization log and status display

## Security

Never commit `config.py`.

Do not expose the RadioBOSS MySQL server to the public internet. SongSync is
intended to run locally on the RadioBOSS computer.

## License

MIT License
