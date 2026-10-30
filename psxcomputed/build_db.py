#!/usr/bin/env python3
"""Build a compact PSX Chocobo winner database from race.lua CSV exports.

Each frame occupies six bytes: four 12-bit class words (long 1st/2nd,
short 1st/2nd). A zero racer ID means that course is absent from the dataset.
CSV historical frame labels are aligned to generator seeds by matching every
racer's raw dash speed, stamina, jockey, sprint flag, and name.
"""

from __future__ import annotations

import argparse
import csv
import json
import struct
from collections import defaultdict
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

NAMES = [
    "SAM", "ELEN", "BLUES", "TOM", "JOHN", "GARY", "MIKE", "SANDY", "JU",
    "LY", "JOEL", "GREY", "EDWARD", "JAMES", "HARVEY", "DAN", "RUDY",
    "GRAHAM", "FOX", "CLIVE", "SEAN", "YOUNG", "ROBIN", "DARIO", "ARL",
    "SARA", "MARIE", "SAMMY", "LIA", "KNIGHT", "PAULA", "PAU", "LE",
    "PETER", "AIMEE", "TERRY", "ANDY", "NANCY", "TIM", "ROBER", "GEORGE",
    "JENNY", "RICA",
]
STATS = {
    "c": (0x09C4, 0x01F4, 0x06A4, 0x00C8),
    "b": (0x0BB8, 0x0258, 0x0898, 0x012C),
    "a": (0x0DAC, 0x02BC, 0x0BB8, 0x01F4),
    "s": (0x1388, 0x0320, 0x0FA0, 0x01F4),
}
RANKS = ("c", "b", "a", "s")
COURSES_PER_RANK = {"c": ("short",), "b": ("long", "short"), "a": ("long", "short"), "s": ("long", "short")}
MASK = 0xFFFFFFFF
PROJECT_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PROJECT_ROOT.parent


def display_path(path: Path) -> str:
    """Keep generated metadata portable and free of workstation paths."""
    try:
        return path.resolve().relative_to(REPOSITORY_ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def rng(seed: int):
    state = seed & MASK

    def next_value() -> int:
        nonlocal state
        state = (state * 0x41C64E6D + 0x3039) & MASK
        return (state >> 16) & 0x7FFF

    return next_value


def signature(seed: int, rank: str) -> tuple[tuple[int, int, int, int, str], ...]:
    random = rng(seed)
    for _ in range(0x28):
        random(); random()
    dash_base, dash_range, _speed_base, _speed_range = STATS[rank]
    racers = []
    for _ in range(6):
        dash = dash_base + random() % dash_range
        random()  # ordinary speed
        jockey = random() % 4
        stamina = (dash_base + random() % 300) * 2
        sprint = 2 if random() & 7 == 0 else 0
        random()  # unknown stat
        racers.append([dash, stamina, jockey, sprint, ""])
    names = list(range(43))
    for _ in range(0xC8):
        a, b = random() % 43, random() % 43
        names[a], names[b] = names[b], names[a]
    for index, racer in enumerate(racers):
        racer[4] = NAMES[names[index]]
    return tuple(tuple(row) for row in racers)


def group_signature(rows: list[dict[str, str]]) -> tuple[tuple[int, int, int, int, str], ...]:
    return tuple((int(row["ts"], 10), int(row["stamina1"], 10), int(row["jockey"], 16),
                  int(row["sprinting"], 16), row["name"].strip().upper()) for row in rows)


def read_groups(path: Path, rank: str) -> dict[tuple[int, int], list[dict[str, str]]]:
    groups: dict[tuple[int, int], list[dict[str, str]]] = defaultdict(list)
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.DictReader(handle):
            row_rank = row.get("rank", rank).strip().lower()
            if row_rank != rank:
                continue
            frame = int(row["frame"])
            random_mode = int(row["random"])
            groups[(frame, random_mode)].append(row)
    return groups


def winners(rows: list[dict[str, str]]) -> tuple[int, int]:
    ordered = sorted(rows, key=lambda row: int(row["winorder"]))
    if len(ordered) != 6 or [int(row["winorder"]) for row in ordered[:2]] != [1, 2]:
        raise ValueError("race group must contain six racers with finish positions 1 through 6")
    # CSV row ordering is the original chocobo slot ordering, retained above.
    first = next(index + 1 for index, row in enumerate(rows) if int(row["winorder"]) == 1)
    second = next(index + 1 for index, row in enumerate(rows) if int(row["winorder"]) == 2)
    return first, second


def align_groups(groups: dict[tuple[int, int], list[dict[str, str]]], rank: str):
    """Infer the frame offset from exact race signatures; follow local changes."""
    usable = [(key, rows) for key, rows in sorted(groups.items()) if key[0] >= 2 and len(rows) == 6]
    if not usable:
        raise ValueError(f"{rank.upper()}: no complete groups after startup frame 1")
    first_key, first_rows = usable[0]
    wanted = group_signature(first_rows)
    frame = first_key[0]
    # Search a generous offset range once, using both nearby values if a dataset
    # begins in the known one-frame discontinuity.
    candidates = range(max(0, frame - 256), frame + 513)
    matches = [seed for seed in candidates if signature(seed, rank) == wanted]
    if len(matches) != 1:
        raise ValueError(f"{rank.upper()} frame {frame}: expected one exact alignment seed, found {matches[:8]}")
    offset = matches[0] - frame
    aligned = {}
    adjustments = []
    for (csv_frame, mode), rows in usable:
        wanted = group_signature(rows)
        seed = None
        for delta in (0, -1, 1, -2, 2):
            candidate = csv_frame + offset + delta
            if candidate >= 0 and signature(candidate, rank) == wanted:
                seed = candidate
                break
        if seed is None:
            # The dataset may contain a one-frame discontinuity. Calibrate a
            # wider local window, but refuse ambiguous or non-matching records.
            for delta in range(-8, 9):
                candidate = csv_frame + offset + delta
                if candidate >= 0 and signature(candidate, rank) == wanted:
                    seed = candidate
                    break
        if seed is None:
            raise ValueError(f"{rank.upper()} frame {csv_frame}/{mode}: no unique exact seed near offset {offset}")
        new_offset = seed - csv_frame
        if new_offset != offset:
            adjustments.append({"csv_frame": csv_frame, "from": offset, "to": new_offset})
            offset = new_offset
        aligned[(seed, mode)] = rows
    return aligned, adjustments, len(usable)


def rank_index(rank: str) -> int:
    return RANKS.index(rank)


def pack_course(existing: int, first: int, second: int, shift: int) -> int:
    mask = 0x3F << shift
    value = (first & 7) | ((second & 7) << 3)
    if existing & mask and ((existing >> shift) & 0x3F) != value:
        raise ValueError("conflicting winner data for aligned seed")
    return (existing & ~mask) | (value << shift)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-dir", action="append", type=Path, help="directory with rankc.csv, rankb.csv, ranka.csv, ranks.csv (repeatable)")
    parser.add_argument("--output", type=Path, default=Path(__file__).parent / "webapp" / "data" / "winners.zip")
    parser.add_argument("--metadata", type=Path, default=Path(__file__).parent / "webapp" / "data" / "winners.json")
    parser.add_argument("--prefer-later-input", action="store_true", help="when aligned records disagree, let a later --input-dir replace earlier results")
    args = parser.parse_args()
    local_source = PROJECT_ROOT / "data" / "source"
    shared_ml = REPOSITORY_ROOT / "ml"
    default_source = local_source if (local_source / "rankc.csv").is_file() else shared_ml
    dirs = args.input_dir or [default_source]
    records: dict[tuple[str, int, str], tuple[int, int]] = {}
    rank_reports = {}
    overrides_by_rank = defaultdict(int)
    max_seed = 0
    for rank in RANKS:
        groups: dict[tuple[int, int], list[dict[str, str]]] = {}
        files = [directory / f"rank{rank}.csv" for directory in dirs if (directory / f"rank{rank}.csv").is_file()]
        if not files:
            rank_reports[rank.upper()] = {"available": False, "files": []}
            continue
        all_alignments = []
        total_groups = 0
        for path in files:
            file_groups = read_groups(path, rank)
            aligned, adjustments, count = align_groups(file_groups, rank)
            all_alignments.append({"file": display_path(path), "adjustments": adjustments, "groups": count})
            total_groups += count
            for (seed, mode), rows in aligned.items():
                course = "short" if rank == "c" or mode == 6 else "long"
                pair = winners(rows)
                key = (rank, seed, course)
                old = records.get(key)
                if old and old != pair:
                    if not args.prefer_later_input:
                        raise ValueError(f"conflicting {rank.upper()} {course} winners at seed {seed}: {old} vs {pair} (use --prefer-later-input to make later directories authoritative)")
                    overrides_by_rank[rank] += 1
                records[key] = pair
                max_seed = max(max_seed, seed)
        rank_records = [key for key in records if key[0] == rank]
        rank_reports[rank.upper()] = {
            "available": True,
            "files": all_alignments,
            "winnerRecords": len(rank_records),
            "seedRange": [min(key[1] for key in rank_records), max(key[1] for key in rank_records)] if rank_records else None,
            "long": rank != "c",
            "short": True,
            "laterInputOverrides": overrides_by_rank[rank],
        }

    # Per rank: 6 bits are long first/second and 6 bits are short first/second.
    # Four 12-bit rank words are bit-packed little-endian = six bytes per seed.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    raw_path = args.output.with_name(args.output.name + ".raw.tmp")
    with raw_path.open("wb") as output:
        output.write(b"PSCDB1\0\0")
        output.write(struct.pack("<I", max_seed + 1))
        for seed in range(max_seed + 1):
            packed = 0
            for rank in RANKS:
                word = 0
                for course, shift in (("long", 0), ("short", 6)):
                    pair = records.get((rank, seed, course))
                    if pair:
                        word = pack_course(word, *pair, shift)
                bit_offset = rank_index(rank) * 12
                packed |= word << bit_offset
            output.write(packed.to_bytes(6, "little"))

    raw_bytes = raw_path.stat().st_size
    with ZipFile(args.output, "w", compression=ZIP_DEFLATED, compresslevel=9) as archive:
        archive.write(raw_path, arcname="winners.bin", compress_type=ZIP_DEFLATED, compresslevel=9)
    raw_path.unlink()

    metadata = {
        "format": "PSCDB1",
        "version": 1,
        "maxSeedExclusive": max_seed + 1,
        "bytesPerSeed": 6,
        "byteOrder": "little-endian",
        "rankOrder": ["C", "B", "A", "S"],
        "rankWordBits": "each rank has 12 bits: bits 0-2 long first, 3-5 long second, 6-8 short first, 9-11 short second; zero means unavailable",
        "startupFramesSkipped": [0, 1],
        "sourceFiles": [display_path(path) for directory in dirs for rank in RANKS if (path := directory / f"rank{rank}.csv").is_file()],
        "ranks": rank_reports,
        "recordCount": len(records),
        "databaseBytes": raw_bytes,
        "compressedBytes": args.output.stat().st_size,
        "compression": "zip-deflate",
    }
    args.metadata.parent.mkdir(parents=True, exist_ok=True)
    args.metadata.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"database": str(args.output), "metadata": str(args.metadata), "rawBytes": metadata["databaseBytes"], "compressedBytes": metadata["compressedBytes"], "records": len(records), "maxSeedExclusive": max_seed + 1, "ranks": rank_reports}, indent=2))


if __name__ == "__main__":
    main()
