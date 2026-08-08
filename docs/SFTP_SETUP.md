# RadioBOSS SongSync Engine – SFTP Setup Guide

This guide explains how to upload the generated SongSync catalog automatically to the RadioBOSS Song Request System.

SongSync supports:

- SFTP password authentication
- SSH private-key authentication
- Automatic server-key verification
- Separate public and private target directories
- Temporary uploads before replacing live files

> [!IMPORTANT]
> Complete the local export test before enabling SFTP.

The local export must finish successfully with:

```text
Export completed. No RadioBOSS data was changed.
```

## Required remote directories

The RadioBOSS Song Request System requires:

```text
songrequest/
|
`-- data/
    |-- public/
    `-- private/
```

The public directory receives:

```text
songs.json
artists.json
genres.json
info.json
```

The private directory receives:

```text
lookup.json
```

The private directory must be protected against browser access.

## 1. Find the SFTP connection details

Obtain these values from the web-hosting provider:

- SFTP hostname
- SFTP port
- SFTP username
- SFTP password
- Remote website path

Standard SFTP normally uses:

```text
Port 22
```

Do not assume that FTP and SFTP use the same hostname or account.

Test the connection first with an SFTP program such as FileZilla.

## 2. Configure the SFTP server

Open the private `config.py`.

Enter:

```python
SFTP_HOST = "your-sftp-server.example"
SFTP_PORT = 22
```

Use the exact hostname and port supplied by the hosting provider.

## 3. Configure the SFTP account

Enter:

```python
SFTP_USERNAME = "CHANGE_ME"
SFTP_PASSWORD = "CHANGE_ME"
```

If a password contains a backslash, use a Python raw string:

```python
SFTP_PASSWORD = r"your\password"
```

Never copy the complete private configuration into:

- GitHub
- A forum
- An issue report
- A chat message
- A public website

## 4. Find the remote target directories

Connect to the server using FileZilla or another SFTP program.

Navigate to the request system’s public data directory.

Copy the complete remote path into:

```python
SFTP_REMOTE_PUBLIC_DIR = (
    "/path/to/songrequest/data/public"
)
```

Navigate to the private data directory and enter:

```python
SFTP_REMOTE_PRIVATE_DIR = (
    "/path/to/songrequest/data/private"
)
```

The directories must already exist.

SongSync intentionally does not create the complete website structure automatically. This prevents an incorrect configuration from creating directories in the wrong server location.

## 5. Configure the connection timeout

Default:

```python
SFTP_TIMEOUT = 20
```

Increase this value only when the server or internet connection is unusually slow.

Example:

```python
SFTP_TIMEOUT = 30
```

## 6. Configure server-key verification

Recommended:

```python
SFTP_TRUST_ON_FIRST_USE = True
SFTP_KNOWN_HOSTS_FILE = "sftp_known_hosts"
```

During the first successful connection, SongSync saves the SFTP server identity.

Future connections verify that the same server responds.

If the server key changes unexpectedly, SongSync stops the upload.

> [!WARNING]
> Do not delete `sftp_known_hosts` merely to bypass an unexpected server-key warning. First confirm with the hosting provider that the server key was legitimately changed.

## 7. First password-authentication test

Leave private-key authentication empty:

```python
SFTP_PRIVATE_KEY_FILE = ""
SFTP_PRIVATE_KEY_PASSPHRASE = ""
```

Enable SFTP:

```python
SFTP_ENABLED = True
```

Run the portable launcher:

```bat
run_songsync.bat
```

The launcher uses `RadioBOSS-SongSync.exe` when available and
otherwise starts the Python source version.

A successful upload displays:

```text
Connecting to SFTP server...
Uploading songs.json...
Uploading artists.json...
Uploading genres.json...
Uploading info.json...
Uploading lookup.json...
SFTP upload completed successfully.
```

## SSH private-key authentication

Some hosting providers may reject automated password authentication even when the same account works in FileZilla.

In that case, configure SSH private-key authentication.

STRATO hosting is one example where SSH-key authentication may be required for reliable automated uploads.

## 8. Create an SSH key on Windows

Open a command prompt in the SongSync directory.

Example:

```bat
ssh-keygen -t ed25519 -f sftp_key -N ""
```

This creates:

```text
sftp_key
sftp_key.pub
```

### sftp_key

This is the private key.

It must remain only on the SongSync computer.

Never upload it to:

- GitHub
- The web server
- The public website
- A support forum
- A chat message

### sftp_key.pub

This is the public key.

It may be installed on the SFTP server.

## 9. Install the public key on the server

Connect using FileZilla.

Go to the start directory of the SFTP account.

Enable the display of hidden files if necessary.

Create:

```text
.ssh
```

Open the `.ssh` directory.

Upload:

```text
sftp_key.pub
```

Rename the uploaded file to:

```text
authorized_keys
```

The final remote path must be:

```text
.ssh/authorized_keys
```

> [!WARNING]
> If `authorized_keys` already exists, do not overwrite it.
> Add the new public-key line to the existing file instead.

Only the public key belongs in `authorized_keys`.

## 10. Configure the private key in SongSync

In `config.py`, enter:

```python
SFTP_PRIVATE_KEY_FILE = "sftp_key"
SFTP_PRIVATE_KEY_PASSPHRASE = ""
```

If the private key was created with a passphrase:

```python
SFTP_PRIVATE_KEY_PASSPHRASE = "CHANGE_ME"
```

The private-key passphrase is different from the SFTP account password.

SongSync may keep the account password configured as a fallback.
When private-key authentication works, `SFTP_PASSWORD` may also be
left empty.

## 11. Test the SSH-key connection

Run:

```bat
run_songsync.bat
```

A successful result displays:

```text
Connecting to SFTP server...
Uploading songs.json...
Uploading artists.json...
Uploading genres.json...
Uploading info.json...
Uploading lookup.json...
SFTP upload completed successfully.
```

## 12. Verify the uploaded catalog

Open the public request website.

Check that the displayed song count matches:

```text
unique_songs
```

inside the newly generated:

```text
exports/public/info.json
```

Search for a recently added or changed title.

Do not try to open `lookup.json` publicly. The private directory must deny browser access.

## How live files are replaced

SongSync uploads each file using a temporary name:

```text
songs.json.tmp
```

After the transfer completes, the temporary file replaces the previous live file.

This reduces the chance that the website reads a partially uploaded JSON file.

If an upload fails:

- Local exports remain available
- Previous successfully uploaded website files remain available
- SongSync displays an error
- The next successful run can upload the catalog again

## Optional example: STRATO setup summary

STRATO normally provides:

- A personalized SFTP hostname
- Port 22
- An SFTP username
- An SFTP password
- A configurable start directory

Recommended STRATO setup:

1. Confirm that FileZilla can connect.
2. Use the exact server, port and username from the STRATO customer area.
3. Create an Ed25519 SSH key.
4. Upload the public key as `.ssh/authorized_keys`.
5. Keep the private key on the SongSync computer.
6. Configure `SFTP_PRIVATE_KEY_FILE`.
7. Run a manual SongSync test.
8. Configure automatic RadioBOSS execution only after the manual test succeeds.

## Troubleshooting

### Permission denied

Example:

```text
PermissionDenied: Permission denied for user
```

Check:

- Correct hostname
- Correct port
- Correct username
- Correct password
- Password was changed but not updated in `config.py`
- Public key is installed in `.ssh/authorized_keys`
- Correct private-key file is configured
- SFTP account is enabled
- The SFTP account has access to its configured start directory

Test the same credentials again in FileZilla.

### Private key was not found

Example:

```text
SFTP private key file was not found
```

Check:

```python
SFTP_PRIVATE_KEY_FILE = "sftp_key"
```

Confirm that `sftp_key` is in the same directory as
`RadioBOSS-SongSync.exe` or `songsync.py`.

An absolute path may also be used:

```python
SFTP_PRIVATE_KEY_FILE = (
    r"D:\radioboss-song-sync\sftp_key"
)
```

### Remote public directory does not exist

Check:

```python
SFTP_REMOTE_PUBLIC_DIR
```

Copy the exact remote path shown by the SFTP program.

Do not use the public website URL.

Incorrect:

```text
https://example.com/songrequest/data/public
```

Correct format:

```text
/home/www/public/songrequest/data/public
```

The exact path depends on the hosting provider.

### Remote private directory does not exist

Check:

```python
SFTP_REMOTE_PRIVATE_DIR
```

The private directory must already exist on the server.

### Upload permission denied

The SFTP account can connect but cannot write to the configured directory.

Check:

- SFTP account start directory
- Remote folder ownership
- Remote folder permissions
- Whether the account is restricted to another project directory

### Server-key verification failed

Do not immediately delete the known-hosts file.

First confirm:

- The hostname has not changed
- The hosting provider changed the server
- The provider announced an SSH host-key change
- The connection is not being redirected

Only after confirming a legitimate server change should the old local host entry be removed and trusted again.

### FileZilla works but SongSync password authentication fails

Configure SSH private-key authentication.

This avoids provider-specific automated password-authentication behavior.

### SFTP upload is disabled

Confirm:

```python
SFTP_ENABLED = True
```

### AsyncSSH is not installed

This message applies only to the Python source version. The Windows
EXE already includes the required SFTP components.

Run:

```bat
py -m pip install -r requirements.txt
```

## Security checklist

Before enabling automatic uploads:

- `config.py` is ignored by Git
- `sftp_key` is ignored by Git
- `sftp_key.pub` is ignored by Git
- `sftp_known_hosts` is ignored by Git
- `exports/` is ignored by Git
- The private web directory is protected
- The SFTP account is restricted where possible
- The private key has not been uploaded anywhere
- A manual upload test completed successfully
