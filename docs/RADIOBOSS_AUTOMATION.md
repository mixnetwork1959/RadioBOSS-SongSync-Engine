# RadioBOSS SongSync Engine – Automation Guide

This guide explains how to run SongSync automatically from the RadioBOSS Scheduler.

Before creating an automatic event, confirm that both operations work manually:

1. Database export (SQLite or MySQL/MariaDB)
2. SFTP upload

A successful manual run must end with:

```text
SFTP upload completed successfully.
```

## How automation works

RadioBOSS starts a Windows batch file at a configured time.

The batch file:

1. Opens the SongSync directory
2. Starts `RadioBOSS-SongSync.exe` or the Python source version
3. Reads the selected RadioBOSS library
4. Generates the JSON catalog
5. Uploads the files using SFTP
6. Closes automatically

Typical workflow:

```text
RadioBOSS Scheduler
        |
        v
run_songsync.bat
        |
        v
RadioBOSS-SongSync.exe
        |
        +-- Database export
        |
        +-- JSON generation
        |
        `-- SFTP upload
```

## Requirements

- RadioBOSS computer remains switched on
- SongSync works manually
- `config.py` is complete
- The selected RadioBOSS database is available
- Internet connection is available
- SFTP authentication works
- The RadioBOSS Scheduler is enabled

Python is required only when using `songsync.py`. It is not required
for the recommended Windows EXE.

## 1. Create the batch file

In the SongSync directory, create:

```text
run_songsync.bat
```

Example project directory:

```text
D:\radioboss-song-sync
```

Use this portable batch-file content:

```bat
@echo off
cd /d "%~dp0"

if exist "RadioBOSS-SongSync.exe" (
    RadioBOSS-SongSync.exe
) else (
    py songsync.py
)
```

`%~dp0` means the directory containing the batch file.

The batch file starts the Windows EXE when it exists. Otherwise, it
starts the Python source version.

When RadioBOSS starts this file, a command window opens, SongSync
runs and the window closes when processing finishes.

## Batch file with a last-run log

Scheduled command windows normally close immediately after SongSync finishes.

To keep the output from the latest run, use:

```bat
@echo off
cd /d "%~dp0"

if not exist "logs" mkdir "logs"

if exist "RadioBOSS-SongSync.exe" (
    RadioBOSS-SongSync.exe > "logs\songsync-last-run.log" 2>&1
) else (
    py songsync.py > "logs\songsync-last-run.log" 2>&1
)
```

The latest result is stored in:

```text
logs\songsync-last-run.log
```

Each new run replaces the previous log.

The `.gitignore` should contain:

```gitignore
logs/
*.log
```

## 2. Test the batch file manually

Double-click:

```text
run_songsync.bat
```

Or run it from a command prompt:

```bat
run_songsync.bat
```

Confirm that SongSync completes successfully.

When using the log version, open:

```text
logs\songsync-last-run.log
```

The final line should be:

```text
SFTP upload completed successfully.
```

Do not create the RadioBOSS event until the batch file works manually.

## 3. Create a RadioBOSS Scheduler event

Open the RadioBOSS Scheduler.

Create a new event.

Use the command:

```text
run D:\radioboss-song-sync\run_songsync.bat
```

When using another installation directory, adjust the path.

If the directory contains spaces, use:

```text
run cmd.exe /c "D:\Path With Spaces\run_songsync.bat"
```

## 4. Configure the event time

Run SongSync at a quiet time when:

- The RadioBOSS computer is running
- The selected RadioBOSS database is available
- No database maintenance is running
- Internet access is normally available

If RadioBOSS creates a database backup at 04:20, SongSync may run later.

Example:

```text
RadioBOSS backup: 04:20
SongSync update:  04:40
```

This prevents the two tasks from starting simultaneously.

## 5. Configure repetition

Recommended:

```text
Once per day
```

A daily update is sufficient for stations which do not change the music library continuously.

Possible schedules:

- Once per day
- Every 12 hours
- After planned library maintenance
- Manually after a large music import

Avoid running SongSync unnecessarily every few minutes.

## 6. Create a test event

Before setting the final daily time:

1. Create an event a few minutes in the future.
2. Save the event.
3. Wait for RadioBOSS to start it.
4. Confirm that the command window opens.
5. Confirm that SongSync runs.
6. Confirm that the command window closes.
7. Check the last-run log when enabled.
8. Check the request website.

After the test succeeds, change the event to the final daily time.

## 7. Verify the website update

After the scheduled run, open the request website.

Check:

- Song count
- Recently added titles
- Recently removed titles
- Artist search
- Title search
- Request button
- Request submission

The public song count should match:

```text
unique_songs
```

inside:

```text
exports/public/info.json
```

## 8. Verify the export time

Open:

```text
exports/public/info.json
```

Check:

```json
"generated_at": "..."
```

This timestamp confirms when SongSync generated the catalog.

The uploaded `info.json` on the web server should contain the same timestamp.

## 9. Recommended RadioBOSS event settings

Suggested configuration:

```text
Event name:     SongSync Update
Command:        run D:\radioboss-song-sync\run_songsync.bat
Time:           04:40
Repeat:         Daily
Enabled:        Yes
```

Choose a time appropriate for the station.

## 10. Manual update

SongSync can still be run manually at any time:

```bat
run_songsync.bat
```

This is useful after:

- Adding many songs
- Deleting songs
- Retagging artist or title information
- Disabling tracks
- Correcting filenames
- Importing a new music category

The next automatic run remains unaffected.

## Failure behavior

### Database connection fails

If the selected database cannot be read:

- New JSON files are not completed
- SFTP upload does not start
- Existing website files remain available
- SongSync returns an error

### Local export fails

If JSON generation fails:

- SFTP upload does not start
- Existing website files remain available
- Local error information is written to the console or log

### SFTP connection fails

If SFTP cannot connect:

- Local JSON files remain available
- Existing website files remain available
- The next scheduled run can try again

### Individual file upload fails

SongSync stops and reports the error.

Files are uploaded using temporary `.tmp` names before replacing the live files. This reduces the chance of publishing an incomplete JSON file.

## Troubleshooting

### RadioBOSS event starts but nothing happens

Test the batch file manually:

```bat
D:\radioboss-song-sync\run_songsync.bat
```

Check that the file path in the RadioBOSS event is correct.

### The py command is not found

This error applies only to the Python source version.

The recommended solution is to use `RadioBOSS-SongSync.exe`, which
does not require Python.

Alternatively, use the full Python executable path in the batch
file.

Example:

```bat
@echo off
cd /d "%~dp0"
"C:\Path\To\Python\python.exe" songsync.py
```

Find the Python executable with:

```bat
where python
where py
```

### Command window closes too quickly

Use the logging batch file:

```bat
@echo off
cd /d "%~dp0"

if not exist "logs" mkdir "logs"

if exist "RadioBOSS-SongSync.exe" (
    RadioBOSS-SongSync.exe > "logs\songsync-last-run.log" 2>&1
) else (
    py songsync.py > "logs\songsync-last-run.log" 2>&1
)
```

Then inspect:

```text
logs\songsync-last-run.log
```

For manual troubleshooting only, temporarily add:

```bat
pause
```

Do not normally use `pause` for an automatic RadioBOSS event because it prevents the command window from closing.

### RadioBOSS cannot start a BAT file directly

Use:

```text
run cmd.exe /c "D:\radioboss-song-sync\run_songsync.bat"
```

### SongSync starts in the wrong directory

Ensure the batch file contains:

```bat
cd /d "%~dp0"
```

This is important when `config.py`, `sftp_key` and local export paths are relative to the SongSync directory.

### The website still shows the old song count

Check:

- `SFTP upload completed successfully`
- Remote target directories
- Browser cache
- Uploaded `info.json`
- Uploaded `songs.json`
- Website `PUBLIC_SONGS_URL`
- Whether another SongSync installation uploaded older files afterward

## Recommended maintenance

Regularly check:

- Last-run log
- Export timestamp
- Song count
- SFTP authentication
- RadioBOSS Scheduler event status
- Available disk space
- Database availability

After changing credentials or paths, always run a manual test.

## Security checklist

- The batch file contains no password
- Credentials remain only in `config.py`
- The private SSH key remains local
- `config.py` is ignored by Git
- `sftp_key` is ignored by Git
- Logs do not contain passwords
- The Scheduler event points to the correct directory
- The private website directory remains protected
