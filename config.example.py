# ==========================================================
# RadioBOSS SongSync Engine
# Version 1.0.0
# Example configuration
# ==========================================================
#
# Copy this file to config.py and enter your own settings.
# Never upload config.py to GitHub.
# ==========================================================

DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "radioboss"
DB_USER = "radioboss_readonly"
DB_PASSWORD = "CHANGE_ME"
DB_CHARSET = "utf8mb4"

# Public files may be uploaded into the song request web folder.
PUBLIC_EXPORT_DIR = "exports/public"

# Private files contain local RadioBOSS file paths.
# They must never be publicly downloadable.
PRIVATE_EXPORT_DIR = "exports/private"

SHOW_EXAMPLES = True
EXAMPLE_LIMIT = 10
