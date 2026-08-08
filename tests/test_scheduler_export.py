from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scheduler_export import (
    classify_playlist_action,
    create_scheduler_payload,
)


class SchedulerExportTests(unittest.TestCase):
    def test_supported_playlist_actions(self):
        self.assertEqual(
            classify_playlist_action("generate Morning"),
            ("generate", "Morning"),
        )
        self.assertEqual(
            classify_playlist_action(r"getrandomplaylist D:\Radio\Playlists\Morning"),
            ("random_playlist", "Morning"),
        )
        self.assertEqual(
            classify_playlist_action(r"load D:\Radio\Playlists\Day.m3u8"),
            ("load_playlist", "Day.m3u8"),
        )
        self.assertEqual(
            classify_playlist_action(r"D:\Radio\Playlists\Night.m3u"),
            ("playlist_file", "Night.m3u"),
        )
        self.assertEqual(
            classify_playlist_action(r"generate D:\Private\Presets\Morning.prf"),
            ("generate", "Morning.prf"),
        )

    def test_non_music_load_actions_are_rejected(self):
        self.assertIsNone(classify_playlist_action("load OtherSchedule.sdl"))
        self.assertIsNone(classify_playlist_action("load Studio.prf"))
        self.assertIsNone(classify_playlist_action("weather Varna,BG"))

    def test_payload_is_path_safe_and_preserves_schedule(self):
        sdl = """\ufeff[event0]
EnabledEvent=1
DateTime=2026-08-08 00:00:00
FileName=generate Morning
TaskName=01 Morning
UseDate=0
EveryYear=0
UseDaysOfWeek=1
Days=1111111
Hours=000000111110000000000000
Minutes=0
Seconds=8
ID=MORNING-ID
[event1]
EnabledEvent=0
DateTime=2026-08-08 00:00:00
FileName=getrandomplaylist D:\\Private\\Playlists\\Night
TaskName=Random Night
UseDate=0
EveryYear=0
UseDaysOfWeek=1
Days=1000001
Hours=000000000000000000000010
Minutes=15,45
Seconds=0
ID=NIGHT-ID
[event3]
EnabledEvent=1
FileName=generate D:\\Private\\Presets\\Secret.prf
TaskName=D:\\Private\\Names\\Secret block
ID=D:\\Private\\Identifiers\\SECRET-ID
Days=1111111
Hours=000000000000000100000000
Minutes=0
[event2]
EnabledEvent=1
FileName=load OtherSchedule.sdl
TaskName=Not Music
ID=SDL-ID
"""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "Admin.sdl"
            path.write_text(sdl, encoding="utf-8", newline="\n")
            payload = create_scheduler_payload(path, "1.7.0")

        self.assertEqual(payload["schema_version"], 1)
        self.assertEqual(payload["event_count"], 3)
        self.assertEqual(payload["events"][0]["id"], "MORNING-ID")
        self.assertEqual(payload["events"][0]["order"], 0)
        self.assertEqual(payload["events"][0]["hours"], "000000111110000000000000")
        self.assertEqual(payload["events"][1]["source"], "Night")
        self.assertEqual(payload["events"][1]["minutes"], [15, 45])
        self.assertFalse(payload["events"][1]["enabled"])
        self.assertEqual(payload["events"][2]["source"], "Secret.prf")
        self.assertEqual(payload["events"][2]["name"], "Secret.prf")
        self.assertTrue(payload["events"][2]["id"].startswith("generated-"))

        exported = json.dumps(payload)
        self.assertNotIn("D:\\\\Private", exported)
        self.assertNotIn("OtherSchedule.sdl", exported)


if __name__ == "__main__":
    unittest.main()
