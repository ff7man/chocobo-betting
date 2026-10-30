#!/usr/bin/env python3
"""Read the FFVII Chocobo frame counter around the suspected 2^22 boundary."""
from __future__ import annotations

import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
DUCKSTATION_DIR = ROOT / "duckstation"
BIN_CANDIDATES = (DUCKSTATION_DIR / "bin", DUCKSTATION_DIR / "build" / "bin")
BIN_DIR = next((path for path in BIN_CANDIDATES if (path / "duckstation-qt").is_file()), BIN_CANDIDATES[-1])
BASE_EXE = BIN_DIR / "duckstation-qt"
WORKER_DIR = ROOT / "workers" / "PROBE"
BIOS_DIR = Path.home() / "Library/Application Support/DuckStation/bios"
SAVE_FILE = Path.home() / "Library/Application Support/DuckStation/savestates/SCUS-94165_2.sav"
DEFAULT_GAME = Path.home() / "Downloads/games/Final Fantasy VII (USA) (Disc 3)/Final Fantasy VII (USA) (Disc 3).cue"


def link_asset(name: str) -> None:
    link = WORKER_DIR / name
    if link.is_symlink() or link.exists():
        if link.is_symlink() or link.is_file():
            link.unlink()
        elif link.is_dir():
            shutil.rmtree(link)
    link.symlink_to(BIN_DIR / name, target_is_directory=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--game", type=Path, default=DEFAULT_GAME, help="FFVII .cue or .chd image")
    parser.add_argument("--start", type=int, default=0x400000 - 8, help="counter value to write before sampling")
    parser.add_argument("--samples", type=int, default=24, help="number of emulated frames to sample")
    parser.add_argument("--circle-frames", type=int, default=5, help="hold Circle for this many initial frames")
    args = parser.parse_args()

    game = args.game.expanduser().resolve()
    if not BASE_EXE.is_file():
        parser.error(f"DuckStation executable is missing: {BASE_EXE}")
    if not game.is_file():
        parser.error(f"game image is missing: {game}")
    if not SAVE_FILE.is_file():
        parser.error(f"Class C save state is missing: {SAVE_FILE}")
    if not BIOS_DIR.is_dir():
        parser.error(f"BIOS folder is missing: {BIOS_DIR}")
    if args.start < 0 or args.start > 0xFFFFFFFF or args.samples < 1 or args.circle_frames < 0 or args.circle_frames > args.samples:
        parser.error("start must fit in 32 bits, samples must be positive, and Circle frames must be within the sample count")

    WORKER_DIR.mkdir(parents=True, exist_ok=True)
    executable = WORKER_DIR / "duckstation-qt"
    shutil.copy2(BASE_EXE, executable)
    for name in ("resources", "translations", "updater"):
        link_asset(name)
    (WORKER_DIR / "portable.txt").touch(exist_ok=True)
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
StateFile = {SAVE_FILE}
FrameCounterProbe = true
ProbeStartFrame = {args.start}
ProbeFrameCount = {args.samples}
ProbeCircleFrames = {args.circle_frames}
"""
    (WORKER_DIR / "settings.ini").write_text(settings, encoding="utf-8")

    print(f"Probing 0x80051568 from {args.start} (0x{args.start:08X}) for {args.samples} frames.", flush=True)
    return subprocess.run(
        [str(executable), "-nogui", "-batch", "--", str(game)],
        cwd=WORKER_DIR,
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
