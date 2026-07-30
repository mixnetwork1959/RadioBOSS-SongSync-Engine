# ==========================================================
# RadioBOSS SongSync Engine
# Version 1.4.0
# Example configuration
# ==========================================================
#
# Copy this file to config.py and enter your own settings.
# Never upload config.py to GitHub.
# ==========================================================


# ----------------------------------------------------------
# Database type
# ----------------------------------------------------------
#
# Choose:
# "sqlite" = standard RadioBOSS tracks.db database
# "mysql"  = RadioBOSS database hosted on MySQL/MariaDB
#

DB_TYPE = "sqlite"


# ----------------------------------------------------------
# RadioBOSS SQLite database
# ----------------------------------------------------------
#
# SQLITE_MODE:
# "dedicated" = database inside a RadioBOSS profile folder
# "shared"    = shared database in the djsoft.net folder
#
# SQLITE_DATABASE:
# "auto" lets SongSync find tracks.db automatically.
# Enter a complete path only if more than one dedicated
# RadioBOSS database is installed for the Windows user.
#

SQLITE_MODE = "dedicated"
SQLITE_DATABASE = "auto"


# ----------------------------------------------------------
# RadioBOSS MySQL/MariaDB database
# ----------------------------------------------------------
#
# These settings are used only when DB_TYPE = "mysql".
#

DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "radioboss"
DB_USER = "radioboss_readonly"
DB_PASSWORD = "CHANGE_ME"
DB_CHARSET = "utf8mb4"


# ----------------------------------------------------------
# Local export directories
# ----------------------------------------------------------
#
# Public files:
# songs.json, artists.json, genres.json and info.json
#
# Private files:
# lookup.json and duplicates.log
#

PUBLIC_EXPORT_DIR = "exports/public"
PRIVATE_EXPORT_DIR = "exports/private"


# ----------------------------------------------------------
# Console output
# ----------------------------------------------------------

SHOW_EXAMPLES = True
EXAMPLE_LIMIT = 10


# ----------------------------------------------------------
# Automatic SFTP upload
# ----------------------------------------------------------
#
# Set to True to upload the generated files automatically
# after a successful SongSync export.
#
# Keep False until all SFTP settings have been entered and
# tested.
#

SFTP_ENABLED = False


# SFTP server
SFTP_HOST = "your-sftp-server.example"
SFTP_PORT = 22


# SFTP login
SFTP_USERNAME = "CHANGE_ME"
SFTP_PASSWORD = "CHANGE_ME"

# Optional private-key login. Leave empty when using a
# password.
SFTP_PRIVATE_KEY_FILE = ""
SFTP_PRIVATE_KEY_PASSPHRASE = ""


# ----------------------------------------------------------
# Remote website directories
# ----------------------------------------------------------
#
# Enter the remote directories exactly as shown by your
# SFTP program.
#
# Public target receives:
# - songs.json
# - artists.json
# - genres.json
# - info.json
#
# Private target receives:
# - lookup.json
#

SFTP_REMOTE_PUBLIC_DIR = (
    "/path/to/songrequest/data/public"
)

SFTP_REMOTE_PRIVATE_DIR = (
    "/path/to/songrequest/data/private"
)


# ----------------------------------------------------------
# SFTP connection
# ----------------------------------------------------------

SFTP_TIMEOUT = 20


# ----------------------------------------------------------
# SFTP host-key security
# ----------------------------------------------------------
#
# When enabled, the server key is trusted during the first
# successful connection and saved locally.
#
# Future connections verify that the server still presents
# the same key.
#
# If the server key changes unexpectedly, SongSync stops the
# upload instead of silently connecting to another server.
#

SFTP_TRUST_ON_FIRST_USE = True

SFTP_KNOWN_HOSTS_FILE = "sftp_known_hosts"
