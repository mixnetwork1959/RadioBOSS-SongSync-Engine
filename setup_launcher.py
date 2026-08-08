from __future__ import annotations

import sys
import traceback
from pathlib import Path


def application_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def log(message: str) -> None:
    try:
        path = application_dir() / "setup-debug.log"
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(message.rstrip() + "\n")
    except Exception:
        pass


def main() -> int:
    log("=== SongSync Setup starting ===")
    log(f"Python: {sys.version}")
    log(f"Executable: {sys.executable}")
    log(f"Frozen: {getattr(sys, 'frozen', False)}")

    try:
        log("Importing tkinter...")
        import tkinter
        log("tkinter import OK")

        log("Importing mysql.connector...")
        import mysql.connector
        log(f"mysql.connector import OK: {getattr(mysql.connector, '__version__', 'unknown')}")

        log("Importing setup_wizard...")
        from setup_wizard import run_setup
        log("setup_wizard import OK")

        ok = run_setup(application_dir())
        log(f"Wizard finished. success={ok}")
        return 0 if ok else 1

    except BaseException as exc:
        details = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
        log("FATAL ERROR:")
        log(details)

        try:
            import tkinter as tk
            from tkinter import messagebox

            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "RadioBOSS SongSync Setup",
                "The Setup Wizard failed.\n\n"
                "See setup-debug.log next to the EXE for details.",
            )
            root.destroy()
        except Exception:
            pass

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
