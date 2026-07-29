@echo off
cd /d "%~dp0"

if exist "RadioBOSS-SongSync.exe" (
    RadioBOSS-SongSync.exe
) else (
    py songsync.py
)
