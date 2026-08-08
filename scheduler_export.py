"""Private, path-safe RadioBOSS scheduler export for rotation analytics."""

from __future__ import annotations

import hashlib
import ntpath
import re
from datetime import datetime
from pathlib import Path


SCHEMA_NAME = "radioboss.scheduler-events"
SCHEMA_VERSION = 1
PLAYLIST_EXTENSIONS = (".m3u", ".m3u8", ".pls")


def _read_sdl_text(path: Path) -> str:
    raw = path.read_bytes()

    if len(raw) > 10 * 1024 * 1024:
        raise ValueError("The RadioBOSS SDL file is larger than 10 MiB.")

    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError("The RadioBOSS SDL file encoding is not supported.")


def parse_sdl_events(path: Path) -> list[dict[str, str]]:
    """Read every key/value pair from every [eventN] SDL section."""

    events: list[dict[str, str]] = []
    current: dict[str, str] | None = None

    for raw_line in _read_sdl_text(path).splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if re.fullmatch(r"\[event\d+\]", line, flags=re.IGNORECASE):
            if current is not None:
                events.append(current)
            current = {}
            continue

        if current is None or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()

        if key:
            current[key] = value.strip()

    if current is not None:
        events.append(current)

    return events


def _without_options(value: str) -> str:
    return value.split("|", 1)[0].strip().strip('"').strip("'")


def _contains_windows_path(value: str) -> bool:
    return bool(re.search(r"(?:[A-Za-z]:[\\/]|\\\\[^\\/]+[\\/])", value))


def _safe_path_label(value: str) -> str:
    clean = _without_options(value).rstrip("\\/")
    label = ntpath.basename(clean)
    return label[:160]


def _looks_like_playlist(value: str) -> bool:
    clean = _without_options(value)
    clean = re.sub(r"\?[+-]\d+[ymdhn]$", "", clean, flags=re.IGNORECASE)
    return clean.casefold().endswith(PLAYLIST_EXTENSIONS)


def classify_playlist_action(command: str) -> tuple[str, str] | None:
    """Classify only actions which can start a music playlist block."""

    command = command.strip()
    if not command:
        return None

    match = re.match(r"^generate\s+(.+)$", command, flags=re.IGNORECASE)
    if match:
        preset = _without_options(match.group(1))
        if _contains_windows_path(preset):
            preset = _safe_path_label(preset)
        preset = preset[:160]
        return ("generate", preset) if preset else None

    match = re.match(
        r"^getrandomplaylist\s+(.+)$",
        command,
        flags=re.IGNORECASE,
    )
    if match:
        label = _safe_path_label(match.group(1))
        return ("random_playlist", label) if label else None

    match = re.match(r"^load\s+(.+)$", command, flags=re.IGNORECASE)
    if match and _looks_like_playlist(match.group(1)):
        label = _safe_path_label(match.group(1))
        return ("load_playlist", label) if label else None

    if _looks_like_playlist(command):
        label = _safe_path_label(command)
        return ("playlist_file", label) if label else None

    return None


def _int(value: str, default: int = 0) -> int:
    try:
        return int(value.strip())
    except (AttributeError, TypeError, ValueError):
        return default


def _event_id(event: dict[str, str]) -> str:
    event_id = event.get("ID", "").strip()
    if event_id and not _contains_windows_path(event_id):
        return event_id[:80]

    identity = "\0".join(
        event.get(key, "")
        for key in ("TaskName", "FileName", "Days", "Hours", "Minutes")
    )
    return "generated-" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:20]


def _mask(value: str, length: int) -> str:
    clean = "".join(character for character in value if character in "01")
    return clean[:length].ljust(length, "0")


def _minutes(value: str) -> list[int]:
    result = []
    for part in value.split(","):
        minute = _int(part, -1)
        if 0 <= minute <= 59 and minute not in result:
            result.append(minute)
    return sorted(result) or [0]


def sanitize_scheduler_event(
    event: dict[str, str],
    order: int = 0,
) -> dict | None:
    classified = classify_playlist_action(event.get("FileName", ""))
    if classified is None:
        return None

    action, source = classified
    event_id = _event_id(event)
    name = event.get("TaskName", "").strip()
    if not name or _contains_windows_path(name):
        name = source or event_id

    return {
        "id": event_id,
        "order": max(0, order),
        "name": name[:200],
        "enabled": event.get("EnabledEvent", "0").strip() == "1",
        "action": action,
        "source": source,
        "date_time": event.get("DateTime", "").strip()[:32],
        "use_date": event.get("UseDate", "0").strip() == "1",
        "every_year": event.get("EveryYear", "0").strip() == "1",
        "use_days_of_week": event.get("UseDaysOfWeek", "0").strip() == "1",
        "days": _mask(event.get("Days", ""), 7),
        "hours": _mask(event.get("Hours", ""), 24),
        "minutes": _minutes(event.get("Minutes", "0")),
        "seconds": max(0, min(59, _int(event.get("Seconds", "0")))),
    }


def create_scheduler_payload(
    sdl_path: Path,
    generator_version: str,
) -> dict:
    if not sdl_path.is_file():
        raise FileNotFoundError(f"RadioBOSS SDL file was not found: {sdl_path}")

    events = []
    for order, event in enumerate(parse_sdl_events(sdl_path)):
        sanitized = sanitize_scheduler_event(event, order)
        if sanitized is not None:
            events.append(sanitized)

    events.sort(key=lambda item: (item["order"], item["id"]))
    source_updated_at = datetime.fromtimestamp(
        sdl_path.stat().st_mtime
    ).astimezone().isoformat(timespec="seconds")

    return {
        "schema": SCHEMA_NAME,
        "schema_version": SCHEMA_VERSION,
        "generator": "RadioBOSS SongSync Engine",
        "generator_version": generator_version,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_updated_at": source_updated_at,
        "event_count": len(events),
        "events": events,
    }
