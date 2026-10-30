#!/usr/bin/env python3
"""List which prizes can appear in each generated prize slot.

Reads the reward tables and display names directly from app.js so this report
stays in sync with the browser implementation. Slot I/II/III correspond to
pool[0]/pool[1]/pool[2] in generateRaceData().
"""

from __future__ import annotations

import ast
import itertools
import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / "app.js").read_text(encoding="utf-8")


def read_js_constant(pattern: str, description: str) -> str:
    match = re.search(pattern, SOURCE, re.DOTALL)
    if not match:
        raise RuntimeError(f"Could not find {description} in app.js")
    return match.group(1)


reward_source = read_js_constant(
    r"const REWARD_TABLES\s*=\s*(\{.*?\n\});", "REWARD_TABLES"
)
reward_json = re.sub(r"\b([CBAS]):", r'"\1":', reward_source)
reward_tables = json.loads(reward_json)
prize_source = read_js_constant(
    r"const PRIZE_NAMES\s*=\s*(\[.*?\]);", "PRIZE_NAMES"
)
prize_names = ast.literal_eval(prize_source)


def reachable_slot_gifts(table: list[list[int]]) -> tuple[list[set[int]], set[tuple[int, int, int]]]:
    """Enumerate valid prize triples and their final slot positions.

    Each reward row is [gift_id, special_rule, weight, move_to_last]. The
    generator can select at most one move_to_last row; it moves that gift to
    slot III after sorting. All other selected gifts are sorted into I and II.
    Duplicate gift IDs are rejected by the generator.
    """
    modes_by_gift: dict[int, set[bool]] = {}
    for gift_id, _special_rule, _weight, move_to_last in table:
        modes_by_gift.setdefault(gift_id, set()).add(bool(move_to_last))

    normal_gifts = sorted(gift for gift, modes in modes_by_gift.items() if False in modes)
    special_gifts = {gift for gift, modes in modes_by_gift.items() if True in modes}
    slots = [set(), set(), set()]
    triples: set[tuple[int, int, int]] = set()

    # No move-to-last reward was selected: all three gifts sort by gift ID.
    for trio in itertools.combinations(normal_gifts, 3):
        ordered = tuple(sorted(trio))
        triples.add(ordered)
        for slot, gift in enumerate(ordered):
            slots[slot].add(gift)

    # One move-to-last reward was selected: the other two sort into I and II.
    for final_gift in special_gifts:
        others = [gift for gift in normal_gifts if gift != final_gift]
        for first, second in itertools.combinations(others, 2):
            ordered = (min(first, second), max(first, second), final_gift)
            triples.add(ordered)
            for slot, gift in enumerate(ordered):
                slots[slot].add(gift)

    return slots, triples


for rank in ("C", "B", "A", "S"):
    slots, triples = reachable_slot_gifts(reward_tables[rank])
    print(f"Class {rank}: {len(triples)} reachable prize triples")
    for index, gifts in enumerate(slots, start=1):
        names = ", ".join(prize_names[gift] for gift in sorted(gifts))
        print(f"  Slot {index} ({len(gifts)} gifts): {names}")
    print()
