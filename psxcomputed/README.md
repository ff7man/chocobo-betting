# PSX Computed Winner Lookup

![Screenshot of the PSX Computed Winner Lookup](screenshot.png)

PSX-style race finder that looks up cached long/short winners instead of
launching DuckStation. Enter the observed class, first chocobo stats, and any
known gifts; the app searches for a matching frame, then marks the matching
bet tiles with `L` and `S` from the database.

## Open it

The hosted app is at <https://ff7man.github.io/psxcomputed/>. For local use,
run `./run.sh` from this folder and open <http://127.0.0.1:8766>.

## Rebuild the database

The binary database is in `webapp/data/winners.zip`; the browser unpacks it
with the bundled JSZip library and keeps the decoded data in memory. Rebuild
it from this folder with:

```sh
python3 build_db.py
```

If `data/source/` is present, the builder uses it. Otherwise it uses the
repository's existing `../ml/` race.lua CSVs. It aligns the CSV frames to
generator seeds by matching all six racers' stats and names, skips anomalous
startup frame 1, and reports detected offset changes in `winners.json`.

To merge a DuckStation-generated folder after a data run, put it after the old
CSV source and use `--prefer-later-input`, so later emulator winners replace
old results at overlapping aligned seeds:

```sh
python3 build_db.py --input-dir ../ml \
  --input-dir ../psxdatagen/data/<run-folder> \
  --prefer-later-input
```

The packed database stores only the winning chocobo IDs (1–6): six bytes per
frame for all four classes and both course lengths. A zero value means that
course has no imported result. The hosted version currently contains the
bundled historical CSV results; it does not simulate finishes or infer missing
winner data. The current data reaches only about the first 7 minutes after
reset at most, and coverage ends earlier for some classes (B: about 3:44,
A: 4:41, S: 5:29). Frames without imported winners cannot return a result.
Use DuckStation-generated records to extend coverage and replace historical
results where they disagree.

The browser app and artwork are in `webapp/`. The top-level `index.html`
redirects to the app for convenient folder-level access.
