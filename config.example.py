# ==========================================================
# RadioBOSS SongSync
# Version 0.1.0
# Example configuration
# ==========================================================
#
# Copy this file to:
#
#     config.py
#
# Then enter the connection details of the MySQL database
# used by RadioBOSS.
#
# Never upload config.py to GitHub.
# ==========================================================

DB_HOST = "127.0.0.1"
DB_PORT = 3306
DB_NAME = "radioboss"
DB_USER = "radioboss_readonly"
DB_PASSWORD = "CHANGE_ME"
DB_CHARSET = "utf8mb4"

# Show sample songs and duplicate groups in the console.
SHOW_EXAMPLES = True
EXAMPLE_LIMIT = 10
