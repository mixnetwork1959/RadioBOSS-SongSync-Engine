from __future__ import annotations

import contextlib
import sys
import traceback
from datetime import datetime
from pathlib import Path


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def rotate_log(path: Path, max_bytes: int = 2_000_000) -> None:
    try:
        if path.is_file() and path.stat().st_size >= max_bytes:
            backup = path.with_name("songsync-old.log")
            if backup.exists():
                backup.unlink()
            path.replace(backup)
    except OSError:
        pass


def run() -> int:
    app_dir = application_dir()
    log_path = app_dir / "songsync.log"
    rotate_log(log_path)

    try:
        handle = log_path.open("a", encoding="utf-8", newline="\n")
    except OSError:
        # Last-resort fallback. In a windowed EXE there may be no console,
        # but SongSync can still attempt to run.
        import songsync
        return int(songsync.main())

    with handle, contextlib.redirect_stdout(handle), contextlib.redirect_stderr(handle):
        print()
        print("=" * 66)
        print(f"SongSync run started: {datetime.now().isoformat(timespec='seconds')}")
        print("=" * 66)

        try:
            import songsync
            result = int(songsync.main())
        except SystemExit as exc:
            code = exc.code
            result = int(code) if isinstance(code, int) else 1
        except BaseException as exc:
            print()
            print("FATAL ERROR:")
            traceback.print_exception(type(exc), exc, exc.__traceback__, file=handle)
            result = 1

        print()
        print(f"SongSync exit code: {result}")
        print(f"SongSync run finished: {datetime.now().isoformat(timespec='seconds')}")
        handle.flush()
        return result


if __name__ == "__main__":
    raise SystemExit(run())
