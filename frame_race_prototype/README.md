# Frame Race Prototype

![Sample Class A frame 21767 short-race output](sample-frame.png)

A small source patch for DuckStation that loads a selected FFVII Chocobo race frame, runs the race at unlimited speed, and reads the actual finish order from game memory. It can run headless and export full race results as JSON Lines. Class B, A, and S can run both course lengths; Class C is short-only.

This is the emulator-side race runner. A frame finder such as [`psx/`](../psx/) can identify a candidate from observed chocobo stats, then this patch emulates that frame to confirm the real winners. Valid target frames are `0`–`4,194,303`.

## Sample frame result

The screenshot is from an actual Class A short-course run at target frame **21,767**. Automatic calibration wrote frame **21,704** (offset `+63`). The game simulation returned:

- Winner: **TIM**
- Top-two bet: **Chocobo 6–5**
- Finish order: TIM, JENNY, SAMMY, SANDY, LE, ELEN
- Zero-based end positions in finish order: `0, 1, 2, 4, 3, 5`

The screenshot includes each racer's speed, stamina, jockey color, sprint status, and end position.

## Build from the pinned DuckStation revision

This folder contains only the patch, README, and sample screenshot. It does not vendor DuckStation's source tree or include compiled binaries, dependency libraries, game files, BIOS files, or save states.

On macOS, install Xcode Command Line Tools, CMake, and Ninja. Clone the DuckStation revision used by this patch, apply the patch, then build:

```sh
git clone https://github.com/stenzek/duckstation.git duckstation
cd duckstation
git checkout 87bc8379b138860b242d7c7aea299e5872e9ae75
git apply /path/to/chocobo-betting/frame_race_prototype/duckstation-chocobo-runner.patch
```

DuckStation requires its platform dependency pack. Download the macOS dependency archive from [DuckStation's dependencies project](https://github.com/duckstation/dependencies) and extract it under `dep/prebuilt/` so the `macos-universal` folder is at `dep/prebuilt/macos-universal/`. Then build the Qt app:

```sh
cmake -S . -B build -G Ninja -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF
cmake --build build --target duckstation-qt -j4
```

The executable is `build/bin/duckstation-qt`.

## Configure a target frame

Add this to the active DuckStation `settings.ini` (Tools → Open Data Directory), replacing the save-state and export paths with local paths:

```ini
[ChocoPatch]
Enabled=true
StateFile=/path/to/savestates/SCUS-94165_4.sav
UseTargetFrame=true
TargetFrame=21767
FrameOffset=auto
CourseLengthWriteWidth=1
CourseLengthValue=6
CaptureDelayFrames=100
AutoRun=true
RunBothCourses=false
AutoStartDelayFrames=595
ExitAfterCapture=true
Headless=true
ExportPath=/tmp/chocobo-race-results.jsonl
```

### What the settings do

| Setting | Effect |
| --- | --- |
| `Enabled` | Turns on the Chocobo runner patch. |
| `StateFile` | Loads the class checkpoint (slots 2/3/4/5 for C/B/A/S). |
| `UseTargetFrame` / `TargetFrame` | Uses the requested generator frame instead of legacy `FrameValue`; valid frames are `0`–`4,194,303`. |
| `FrameOffset` | `auto` subtracts 63 frames for C/B/A or 64 for S before writing the counter. A number overrides the correction. |
| `CourseLengthWriteWidth` / `CourseLengthValue` | Writes the selector as one byte: `6` short, `0` long. |
| `AutoRun` / `AutoStartDelayFrames` | Starts automatically after the betting screen loads and waits the configured frames (595 here). |
| `CaptureDelayFrames` | With `AutoRun=false`, waits this many frames at the betting screen, then pauses for you to start manually. |
| `RunBothCourses` | With auto-run, reloads the checkpoint and runs the other course; supported for B/A/S, not C. |
| `Headless` | Suppresses audio and video output for unattended runs. |
| `ExitAfterCapture` | Closes DuckStation after reading the final race result. |
| `ExportPath` | Appends race data as JSON Lines; leave empty to disable file export. |

Run the build with an FFVII disc image (`.cue` or `.chd`):

```sh
build/bin/duckstation-qt -nogui -batch -- "/path/to/Final Fantasy VII.cue"
```

`FrameOffset=auto` subtracts `63` frames for Classes C/B/A and `64` for S, modulo the 4,194,304-frame counter cycle. Course value `6` selects short and `0` selects long. To run both courses, set `RunBothCourses=true` for B/A/S; Class C is short-only. The required game image, BIOS, and save states are supplied locally and are not included.
