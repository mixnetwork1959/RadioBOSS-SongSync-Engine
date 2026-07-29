# RadioBOSS SongSync Engine

## Version 1.0.0

RadioBOSS SongSync Engine reads the RadioBOSS MySQL database and creates
JSON files for a database-free website song request system.

## Data flow

```text
RadioBOSS MySQL
       |
       v
SongSync Engine
       |
       +-- public/songs.json
       +-- public/artists.json
       +-- public/genres.json
       +-- public/info.json
       |
       +-- private/lookup.json
       +-- private/duplicates.log
```

## Public files

### `songs.json`

Contains only:

```json
{
  "track_id": 11698,
  "artist": "2pac",
  "title": "Dear Mama"
}
```

It does not reveal local filenames.

### `artists.json`

Unique artist names for autocomplete or filters.

### `genres.json`

Unique genres from RadioBOSS tags.

### `info.json`

Contains generation time, counts and a catalog hash.

## Private files

### `lookup.json`

Maps a `track_id` to the local RadioBOSS filename:

```json
{
  "11698": {
    "filename": "d:\\music\\top_10\\70-1999\\2pac - dear mama.mp3"
  }
}
```

This file must not be publicly downloadable.

### `duplicates.log`

Shows which RadioBOSS record was retained and which equal artist/title
records were ignored.

## Duplicate rule

```text
same normalized artist + same normalized title = one public song
```

The first matching RadioBOSS record is retained. Its real `track_id` and
filename stay together.

## Installation

Install the dependency:

```text
py -m pip install -r requirements.txt
```

Copy:

```text
config.example.py
```

to:

```text
config.py
```

Enter the MySQL settings and run:

```text
py songsync.py
```

## Security

- Never upload `config.py`.
- Use a MySQL user with `SELECT` permission only.
- Never place `lookup.json` in a publicly downloadable directory.
- Do not expose the RadioBOSS MySQL server to the internet.

## Next step

The website frontend will load `songs.json` in JavaScript. When a listener
requests a song, the browser sends only the `track_id` to PHP. PHP resolves
the filename from the protected `lookup.json` and sends the request to
RadioBOSS.
