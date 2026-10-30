#!/usr/bin/env python3
"""Run or resume four isolated DuckStation data generators (C/B/A/S)."""
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
import re
import shutil
import subprocess
import threading
import time

ROOT = Path(__file__).resolve().parent
DUCKSTATION_DIR = ROOT / "duckstation"
BIN_CANDIDATES = (DUCKSTATION_DIR / "bin", DUCKSTATION_DIR / "build" / "bin")
BIN_DIR = next((path for path in BIN_CANDIDATES if (path / "duckstation-qt").is_file()), BIN_CANDIDATES[-1])
BASE_EXE = BIN_DIR / "duckstation-qt"
WORKERS_DIR = ROOT / "workers"
DATA_DIR = ROOT / "data"
BIOS_DIR = Path.home() / "Library/Application Support/DuckStation/bios"
SAVE_DIR = Path.home() / "Library/Application Support/DuckStation/savestates"
DEFAULT_GAME = Path.home() / "Downloads/games/Final Fantasy VII (USA) (Disc 3)/Final Fantasy VII (USA) (Disc 3).cue"
CLASSES = ("c", "b", "a", "s")
SLOTS = {"c": 2, "b": 3, "a": 4, "s": 5}
PROGRESS_RE = re.compile(r"Progress: (\d+) complete / (\d+) total \| ([\d.]+) races/s")
CSV_HEADER = "raceid,ts,rs2,rs1,acc,coop,intel,stamina1,stamina2,sprinting,course,jockey,winorder,pos,name,rank,frame,random"


def duration_text(seconds: float) -> str:
    value = max(0, int(seconds))
    days, value = divmod(value, 86400)
    hours, value = divmod(value, 3600)
    minutes, seconds = divmod(value, 60)
    return f"{days}d {hours:02}:{minutes:02}:{seconds:02}"


def write_settings(path: Path, rank: str, start: int, end: int, start_course: int, output: Path,
                   first_race_id: int) -> None:
    state = SAVE_DIR / f"SCUS-94165_{SLOTS[rank]}.sav"
    settings = f"""[Main]
SetupWizardIncomplete = false
SettingsVersion = 1
ApplyGameSettings = true
EnableDiscordPresence = false
SaveStateOnExit = false
ConfirmPowerOff = false

[UI]
UnofficialBuildWarningConfirmed = true

[BIOS]
SearchDirectory = {BIOS_DIR}

[Audio]
Backend = Null

[GPU]
Renderer = Hardware

[ChocoPatch]
Enabled = true
Headless = true
StateFile = {state}
AutoRun = true
AutoStartDelayFrames = 595
CaptureDelayFrames = 100
FrameOffset = auto
DataGeneration = true
DataRank = {rank}
DataStartFrame = {start}
DataEndFrame = {end}
DataStartCourseValue = {start_course}
DataCourseMode = both
DataFirstRaceId = {first_race_id}
ExportPath = {output}
"""
    path.write_text(settings, encoding="utf-8")


def prepare_worker(rank: str, start: int, end: int, start_course: int, output: Path,
                   first_race_id: int) -> Path:
    worker_dir = WORKERS_DIR / rank.upper()
    worker_dir.mkdir(parents=True, exist_ok=True)
    worker_exe = worker_dir / "duckstation-qt"
    shutil.copy2(BASE_EXE, worker_exe)

    # Each executable's portable data root is separate; immutable assets are shared.
    for name in ("resources", "translations", "updater"):
        link = worker_dir / name
        source = BIN_DIR / name
        if link.is_symlink() or link.exists():
            if link.is_symlink() or link.is_file():
                link.unlink()
            elif link.is_dir():
                shutil.rmtree(link)
        link.symlink_to(source, target_is_directory=True)

    (worker_dir / "portable.txt").touch(exist_ok=True)
    csv_path = output / f"rank{rank}.csv"
    write_settings(worker_dir / "settings.ini", rank, start, end, start_course,
                   csv_path, first_race_id)
    for writable in ("bios", "cache", "cheats", "covers", "gameicons", "gamesettings",
                     "inputprofiles", "memcards", "patches", "savestates", "screenshots",
                     "shaders", "subchannels", "textures", "videos"):
        (worker_dir / writable).mkdir(exist_ok=True)
    return worker_exe


def inspect_csv(path: Path, rank: str, start: int, end: int) -> tuple[int, int | None, int]:
    """Validate the sequential CSV prefix, trim any incomplete tail, return resume cursor."""
    courses = (0,) if rank == "c" else (0, 6)
    frame = start
    course_index = 0
    complete_races = 0
    if not path.exists() or path.stat().st_size == 0:
        return complete_races, frame, courses[course_index]

    with path.open("rb") as source:
        header_line = source.readline()
        if header_line.decode("utf-8", errors="replace").rstrip("\r\n") != CSV_HEADER:
            raise ValueError(f"{path} has an unexpected CSV header")
        valid_end = source.tell()
        stopped = False
        while not stopped:
            group_start = source.tell()
            raw_group = [source.readline() for _ in range(6)]
            if not raw_group[0]:
                break
            if any(not line for line in raw_group):
                stopped = True
                break
            try:
                group = [line.decode("utf-8").rstrip("\r\n").split(",") for line in raw_group]
                key = (int(group[0][16]), int(group[0][17]))
                race_id = int(group[0][0])
                valid = len(group[0]) == 18 and key == (frame, courses[course_index]) and race_id == complete_races
                names = set()
                for row in group:
                    valid = valid and len(row) == 18
                    valid = valid and int(row[0]) == race_id
                    valid = valid and int(row[16]) == key[0] and int(row[17]) == key[1]
                    valid = valid and row[15] == rank
                    names.add(row[14])
                valid = valid and len(names) == 6
            except (UnicodeDecodeError, IndexError, ValueError):
                valid = False

            if not valid:
                stopped = True
                source.seek(group_start)
                break

            complete_races += 1
            valid_end = source.tell()
            course_index += 1
            if course_index == len(courses):
                course_index = 0
                frame += 1

        file_size = path.stat().st_size

    if file_size > valid_end:
        backup = path.with_suffix(path.suffix + ".partial-backup")
        if not backup.exists():
            shutil.copy2(path, backup)
        with path.open("r+b") as output:
            output.truncate(valid_end)
        print(f"Recovered {path.name}: kept {complete_races:,} complete races; incomplete tail saved as {backup.name}.")

    next_frame = frame if frame <= end else None
    next_course = courses[course_index] if next_frame is not None else None
    return complete_races, next_frame, next_course


def latest_run_directory() -> Path | None:
    candidates = sorted(DATA_DIR.glob("parallel-*/run.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0].parent if candidates else None


def tail(path: Path, count: int = 20) -> str:
    try:
        return "".join(path.read_text(encoding="utf-8", errors="replace").splitlines(keepends=True)[-count:])
    except OSError:
        return "(no worker log available)\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate or resume C/B/A/S CSVs concurrently in isolated DuckStation profiles.")
    parser.add_argument("--start-frame", type=int, help="first inclusive seed frame (new run default: 600)")
    parser.add_argument("--end-frame", type=int, help="last inclusive seed frame (new run default: 215999)")
    parser.add_argument("--game", type=Path, help="FFVII .cue or .chd image")
    parser.add_argument("--output-dir", type=Path, help="output directory for a new run")
    parser.add_argument("--resume", nargs="?", const="latest", help="resume a run folder, or the latest folder if omitted")
    args = parser.parse_args()

    if not BASE_EXE.is_file():
        parser.error(f"DuckStation executable is missing: {BASE_EXE}")
    if args.resume and args.output_dir:
        parser.error("use either --resume or --output-dir, not both")

    if args.resume:
        run_dir = latest_run_directory() if args.resume == "latest" else Path(args.resume).expanduser().resolve()
        if not run_dir or not (run_dir / "run.json").is_file():
            parser.error("could not find run metadata; use --resume /path/to/parallel-run-folder")
        try:
            metadata = json.loads((run_dir / "run.json").read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            parser.error(f"could not read resume metadata: {exc}")
        original_start, original_end = int(metadata["start_frame"]), int(metadata["end_frame"])
        if args.start_frame is not None and args.start_frame != original_start:
            parser.error(f"resume range starts at {original_start}; requested start {args.start_frame} differs")
        if args.end_frame is not None and args.end_frame != original_end:
            parser.error(f"resume range ends at {original_end}; requested end {args.end_frame} differs")
        start, end = original_start, original_end
        game = args.game.resolve() if args.game else Path(metadata["game"])
        output_dir = run_dir
    else:
        start = args.start_frame if args.start_frame is not None else 600
        end = args.end_frame if args.end_frame is not None else 215999
        game = (args.game or DEFAULT_GAME).expanduser().resolve()
        output_dir = args.output_dir.expanduser().resolve() if args.output_dir else DATA_DIR / dt.datetime.now().strftime("parallel-%Y%m%d-%H%M%S-%f")
        output_dir.mkdir(parents=True, exist_ok=True)
        if any(output_dir.glob("rank*.csv")):
            parser.error("output directory already contains rank CSVs; choose a new folder or resume it")
        metadata = {"start_frame": start, "end_frame": end, "game": str(game), "created": dt.datetime.now().isoformat(timespec="seconds")}
        (output_dir / "run.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")

    if not game.is_file():
        parser.error(f"game image is missing: {game}")
    if start < 0 or end < start or end >= 0x400000:
        parser.error("frame range must be inclusive and within 0..4,194,303")
    if not BIOS_DIR.is_dir():
        parser.error(f"BIOS folder is missing: {BIOS_DIR}")
    for rank, slot in SLOTS.items():
        state = SAVE_DIR / f"SCUS-94165_{slot}.sav"
        if not state.is_file():
            parser.error(f"Class {rank.upper()} save state is missing: {state}")

    frames = end - start + 1
    total = frames * 7  # C is short-only; B/A/S each run long and short.
    print(f"Run range: frames {start}–{end} ({frames:,} frames).")
    print(f"Output directory: {output_dir}")

    processes = {}
    logs = {}
    latest = {}
    initial_complete = {}
    totals_by_class = {rank: frames * (1 if rank == "c" else 2) for rank in CLASSES}
    jobs = {}
    for rank in CLASSES:
        csv_path = output_dir / f"rank{rank}.csv"
        try:
            count, next_frame, next_course = inspect_csv(csv_path, rank, start, end)
        except ValueError as exc:
            parser.error(str(exc))
        initial_complete[rank] = count
        if next_frame is None:
            latest[rank] = {"complete": totals_by_class[rank], "total": totals_by_class[rank]}
            print(f"Class {rank.upper()}: already complete ({count:,} races); skipping.")
        else:
            remaining = (end - next_frame + 1) * (1 if rank == "c" else 2)
            if rank != "c" and next_course == 6:
                remaining -= 1
            latest[rank] = {"complete": count, "total": totals_by_class[rank]}
            jobs[rank] = (next_frame, next_course, count, remaining)
            print(f"Class {rank.upper()}: resume at frame {next_frame}, course {next_course} ({remaining:,} races remain).")

    lock = threading.Lock()
    readers = []
    started = time.monotonic()

    try:
        for rank in CLASSES:
            if rank not in jobs:
                continue
            worker_start, worker_course, race_id, remaining = jobs[rank]
            exe = prepare_worker(rank, worker_start, end, worker_course, output_dir, race_id)
            log_path = output_dir / f"duckstation-{rank}.log"
            log = log_path.open("a", encoding="utf-8")
            log.write(f"\n=== run/resume started {dt.datetime.now().isoformat(timespec='seconds')} at frame {worker_start}, course {worker_course} ===\n")
            log.flush()
            logs[rank] = log
            proc = subprocess.Popen(
                [str(exe), "-nogui", "-batch", "--", str(game)],
                cwd=exe.parent,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
            processes[rank] = proc

            def pump(output_rank=rank, output_proc=proc, output_log=log):
                assert output_proc.stdout is not None
                for line in output_proc.stdout:
                    output_log.write(line)
                    output_log.flush()
                    match = PROGRESS_RE.search(line)
                    if match:
                        with lock:
                            latest[output_rank] = {
                                "complete": initial_complete[output_rank] + int(match.group(1)),
                                "total": totals_by_class[output_rank],
                            }
            thread = threading.Thread(target=pump, name=f"progress-{rank}", daemon=True)
            thread.start()
            readers.append(thread)
            print(f"Class {rank.upper()} started (PID {proc.pid})")

        last_report = time.monotonic()
        while any(proc.poll() is None for proc in processes.values()):
            now = time.monotonic()
            if now - last_report >= 10:
                with lock:
                    complete = sum(item["complete"] for item in latest.values())
                    newly_complete = sum(
                        latest[rank]["complete"] - initial_complete[rank] for rank in CLASSES
                    )
                    by_class = " | ".join(
                        f"{rank.upper()} {latest[rank]['complete']:,}/{latest[rank]['total']:,}"
                        for rank in CLASSES
                    )
                elapsed = now - started
                rate = newly_complete / elapsed if elapsed > 0 else 0.0
                eta = (total - complete) / rate if rate > 0 else 0.0
                eta_text = duration_text(eta) if rate > 0 else "calculating"
                print(f"Progress: {by_class} | {complete:,} complete / {total:,} total | "
                      f"{rate:.2f} races/s | ETA {eta_text}", flush=True)
                last_report = now
            time.sleep(0.5)

        for proc in processes.values():
            proc.wait()
        for thread in readers:
            thread.join(timeout=2)

    except KeyboardInterrupt:
        print("Stopping all four workers…", flush=True)
        for proc in processes.values():
            if proc.poll() is None:
                proc.terminate()
        for proc in processes.values():
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait()
        for thread in readers:
            thread.join(timeout=2)
        return 130
    finally:
        for log in logs.values():
            log.close()

    failed = [rank for rank, proc in processes.items() if proc.returncode != 0]
    if failed:
        for rank in failed:
            print(f"Class {rank.upper()} exited with code {processes[rank].returncode}; last log lines:\n{tail(output_dir / f'duckstation-{rank}.log')}")
        return 1

    print(f"All requested class runs finished. CSVs and per-worker logs are in: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
