# Changelog

## 1.6.0

- Added graphical Windows Setup Wizard.
- Added automatic SQLite database detection.
- Added SQLite and MySQL/MariaDB connection tests.
- Added guided SFTP configuration and connection test.
- Added password and SSH private-key authentication setup.
- Updated MySQL Connector packaging for PyInstaller compatibility.
- Normal `RadioBOSS-SongSync.exe` now runs without a CMD window.
- Normal runs write status and errors to `songsync.log`.
- Added automatic log rotation to `songsync-old.log`.
- Added `RadioBOSS-SongSync-Debug.exe` for console troubleshooting.
- Kept manual `config.example.py` configuration fully supported.

# Changelog

## v1.5.0

- Added improved Windows OpenSSH support for SSH private-key SFTP uploads.
- Improved compatibility with RadioBOSS SQLite shared and dedicated databases.
- Added `plays` to every public song record from `tracks2.playcount`.
- Added `last_played` from `tracks2.lastplayed`.
- Added `play_history` from `tracks2.lastplayedhistory` as a JSON array.
- Included airplay data in the catalog hash so changes trigger a fresh export/upload.
- Prepared SongSync data for automatic charts and future rotation analysis.
- Updated generic installation, SFTP and automation documentation.
- Kept hosting-provider-specific guidance optional; STRATO is documented only as an example.
