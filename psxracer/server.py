#!/usr/bin/env python3
"""Local web server and isolated DuckStation bridge for PSX race predictions."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parent
WEB_ROOT = ROOT / "webapp"
DUCK_ROOT = ROOT / "duckstation"
BIN_CANDIDATES = (DUCK_ROOT / "bin", DUCK_ROOT / "build" / "bin")
BIN_ROOT = next((path for path in BIN_CANDIDATES if (path / "duckstation-qt").is_file()), BIN_CANDIDATES[-1])
EXECUTABLE = BIN_ROOT / "duckstation-qt"
CONFIG_PATH = ROOT / "config.json"
MAX_FRAME = 4_194_303
RANK_SLOT = {"C": 2, "B": 3, "A": 4, "S": 5}
RUN_LOCK = threading.Lock()


def update_settings_ini(updates: dict[str, dict[str, str]]) -> None:
    """Update selected INI keys while keeping DuckStation's saved settings intact."""
    settings_path = BIN_ROOT / "settings.ini"
    try:
        original_lines = settings_path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        original_lines = []

    output: list[str] = []
    seen_sections: set[str] = set()
    written_keys: dict[str, set[str]] = {section: set() for section in updates}
    current_section: str | None = None

    def append_missing_keys(section: str | None) -> None:
        if section not in updates:
            return
        for key, value in updates[section].items():
            if key not in written_keys[section]:
                output.append(f"{key} = {value}")
                written_keys[section].add(key)

    for line in original_lines:
        stripped = line.strip()
        if stripped.startswith("[") and stripped.endswith("]"):
            append_missing_keys(current_section)
            current_section = stripped[1:-1]
            seen_sections.add(current_section)
            output.append(line)
            continue

        if current_section in updates and "=" in line and not stripped.startswith((";", "#")):
            key = line.split("=", 1)[0].strip()
            if key in updates[current_section]:
                if key not in written_keys[current_section]:
                    output.append(f"{key} = {updates[current_section][key]}")
                    written_keys[current_section].add(key)
                continue
        output.append(line)

    append_missing_keys(current_section)
    for section, values in updates.items():
        if section not in seen_sections:
            if output and output[-1] != "":
                output.append("")
            output.append(f"[{section}]")
            output.extend(f"{key} = {value}" for key, value in values.items())

    temporary_path = settings_path.with_suffix(".ini.tmp")
    temporary_path.write_text("\n".join(output).rstrip() + "\n", encoding="utf-8")
    temporary_path.replace(settings_path)


def load_config() -> dict:
    try:
        return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RuntimeError(f"Create {CONFIG_PATH.name} from config.example.json first.") from exc


def run_races(rank: str, frame: int) -> dict:
    config = load_config()
    game_image = Path(config.get("game_image", "")).expanduser()
    save_dir = Path(config.get("save_state_directory", "")).expanduser()
    if not game_image.is_file():
        raise RuntimeError("Set game_image in psxracer/config.json to your FFVII disc image (.cue or .chd).")
    if not EXECUTABLE.is_file():
        raise RuntimeError(f"DuckStation executable is missing: {EXECUTABLE}")
    state_file = save_dir / f"SCUS-94165_{RANK_SLOT[rank]}.sav"
    if not state_file.is_file():
        raise RuntimeError(f"Save state for Class {rank} was not found: {state_file}")

    # DuckStation reads this project-local settings.ini beside the copied binary.
    # The lock keeps each request's frame, state, and JSONL output isolated.
    with RUN_LOCK, tempfile.TemporaryDirectory(prefix="psxracer-") as temp_dir:
        export_path = Path(temp_dir) / "race-results.jsonl"
        course_value = 0 if rank == "C" else 6
        run_both = "false" if rank == "C" else "true"
        bios_dir = Path(config.get("bios_directory", "")).expanduser()
        update_settings_ini({
            "Main": {"SetupWizardIncomplete": "false"},
            "BIOS": {"SearchDirectory": str(bios_dir)},
            "ChocoPatch": {
                "Enabled": "true",
                "StateFile": str(state_file),
                "UseTargetFrame": "true",
                "TargetFrame": str(frame),
                "FrameOffset": "auto",
                "CourseLengthWriteWidth": "1",
                "CourseLengthValue": str(course_value),
                "CaptureDelayFrames": "100",
                "AutoRun": "true",
                "RunBothCourses": run_both,
                "AutoStartDelayFrames": "595",
                "ExitAfterCapture": "true",
                "Headless": "true",
                "ExportPath": str(export_path),
            },
        })
        try:
            completed = subprocess.run(
                [str(EXECUTABLE), "-nogui", "-batch", str(game_image)],
                cwd=BIN_ROOT,
                capture_output=True,
                text=True,
                timeout=int(config.get("runner_timeout_seconds", 90)),
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError("DuckStation did not finish the race run before the timeout.") from exc

        if completed.returncode != 0:
            details = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(f"DuckStation exited with code {completed.returncode}. {details[-1200:]}")
        if not export_path.exists():
            details = (completed.stderr or completed.stdout or "").strip()
            raise RuntimeError(f"DuckStation finished without exporting race data. {details[-1200:]}")

        rows = [json.loads(line) for line in export_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        races = []
        for row in rows:
            racers = row.get("racers", [])
            by_finish_order = {
                racer.get("finish_order"): racer
                for racer in racers
                if isinstance(racer.get("finish_order"), int)
            }
            first = by_finish_order.get(1)
            second = by_finish_order.get(2)
            pair = None
            if first and second:
                ids = sorted((int(first["racer"]), int(second["racer"])))
                pair = f"{ids[0]}-{ids[1]}"
            races.append({
                "course": row.get("course"),
                "winner_pair": pair,
                "racers": racers,
            })

        # C class has no long-course variant in the supplied checkpoint setup.
        expected = 1 if rank == "C" else 2
        if len(races) != expected or any(not race["winner_pair"] for race in races):
            raise RuntimeError("Race data was incomplete; check DuckStation output and the class save-state setup.")
        return {"frame": frame, "class": rank, "races": races}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(WEB_ROOT), **kwargs)

    def do_POST(self):
        if urlparse(self.path).path != "/api/race-results":
            self.send_error(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if length < 1 or length > 4096:
                raise ValueError("Request body must be a small JSON object.")
            body = json.loads(self.rfile.read(length))
            rank = str(body.get("class", "")).upper()
            frame = body.get("frame")
            if rank not in RANK_SLOT:
                raise ValueError("Class must be C, B, A, or S.")
            if isinstance(frame, bool) or not isinstance(frame, int) or not 0 <= frame <= MAX_FRAME:
                raise ValueError(f"Frame must be an integer between 0 and {MAX_FRAME:,}.")
            result = run_races(rank, frame)
            self._json(200, result)
        except (ValueError, RuntimeError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover - surfaced to the local UI for diagnosis
            self._json(500, {"error": f"Unexpected local runner error: {exc}"})

    def _json(self, status: int, payload: dict):
        data = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Access-Control-Allow-Origin", "null")
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt: str, *args):
        print(f"[{self.log_date_time_string()}] {fmt % args}")


def main():
    if not CONFIG_PATH.exists():
        example = ROOT / "config.example.json"
        print(f"Setup required: copy {example.name} to {CONFIG_PATH.name} and set game_image.")
    host = os.environ.get("PSXRACER_HOST", "127.0.0.1")
    port = int(os.environ.get("PSXRACER_PORT", "8765"))
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"PSX Chocobo Racer running at http://{host}:{port}/")
    print("Only local connections are accepted by default; press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping PSX Chocobo Racer.")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
