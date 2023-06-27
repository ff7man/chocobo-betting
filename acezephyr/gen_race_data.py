# RE'd by AceZephyr
class RNG:

    def rng(self):
        a = 0x41C64E6D
        b = 0x3039

        self.rng_incrs += 1
        self.rng_state = (a * self.rng_state + b) & 0xFFFFFFFF
        return (self.rng_state >> 0x10) & 0x7FFF

    def __init__(self, seed=0):
        self.rng_state = seed
        self.rng_incrs = 0


class ChocoboData:

    def __init__(self):
        self.unknown = None
        self.running_animation = None
        self.stamina = None
        self.ai_type = None
        self.dash_speed = None
        self.speed = None

    def __repr__(self):
        return ",".join([str(None) if x is None else hex(x)[2:].upper().zfill(4) for x in
                         [self.speed, self.dash_speed, self.stamina, self.ai_type]])


RACER_NAMES = ['SAM',
               'ELEN',
               'BLUES',
               'TOM',
               'JOHN',
               'GARY',
               'MIKE',
               'SANDY',
               'JU',
               'LY',
               'JOEL',
               'GREY',
               'EDWARD',
               'JAMES',
               'HARVEY',
               'DAN',
               'RUDY',
               'GRAHAM',
               'FOX',
               'CLIVE',
               'SEAN',
               'YOUNG',
               'ROBIN',
               'DARIO',
               'ARL',
               'SARA',
               'MARIE',
               'SAMMY',
               'LIA',
               'KNIGHT',
               'PAULA',
               'PAU',
               'LE',
               'PETER',
               'AIMEE',
               'TERRY',
               'ANDY',
               'NANCY',
               'TIM',
               'ROBER',
               'GEORGE',
               'JENNY',
               'RICA',
               'JULIA']

PRIZE_NAMES = [
    "Sprint Shoes",
    "Counter Attack",
    "Magic Counter",
    "Precious Watch",
    "Cat's Bell",
    "Enemy Away",
    "Sneak Attack",
    "Chocobracelet",
    "Ether",
    "Elixir",
    "Hero Drink",
    "Bolt Plume",
    "Fire Fang",
    "Antarctic Wind",
    "Swift Bolt",
    "Fire Veil",
    "Ice Crystal",
    "Megalixer",
    "Turbo Ether",
    "Potion",
    "Phoenix Down",
    "Hyper",
    "Tranquilizer",
    "Hi-Potion"
]

REWARD_TABLES = {
    "C": [
        [0x17, 0x00, 0x05, 0x01],
        [0x08, 0x00, 0x14, 0x01],
        [0x15, 0x00, 0x0A, 0x00],
        [0x16, 0x00, 0x0A, 0x00],
        [0x14, 0x00, 0x14, 0x00],
        [0x0B, 0x00, 0x05, 0x01],
        [0x0C, 0x00, 0x05, 0x00],
        [0x0D, 0x00, 0x05, 0x00],
        [0x13, 0x00, 0x05, 0x01],
        [0x14, 0x00, 0x14, 0x01],
    ], "B": [
        [0x08, 0x00, 0x1E, 0x00],
        [0x0A, 0x00, 0x0A, 0x00],
        [0x14, 0x00, 0x14, 0x00],
        [0x12, 0x00, 0x05, 0x01],
        [0x08, 0x00, 0x1E, 0x00],
        [0x17, 0x00, 0x05, 0x00],
        [0x15, 0x00, 0x0A, 0x00],
        [0x16, 0x00, 0x0A, 0x00],
        [0x17, 0x00, 0x05, 0x00],
        [0x0B, 0x00, 0x0A, 0x01],
        [0x0C, 0x00, 0x0A, 0x00],
        [0x0D, 0x00, 0x0A, 0x00],
        [0x09, 0x00, 0x0A, 0x01],
        [0x05, 0x01, 0x05, 0x01],
        [0x17, 0x00, 0x05, 0x00],
    ], "A": [
        [0x08, 0x00, 0x14, 0x00],
        [0x0A, 0x00, 0x0A, 0x00],
        [0x0E, 0x01, 0x0A, 0x00],
        [0x0F, 0x01, 0x0A, 0x00],
        [0x0C, 0x00, 0x0A, 0x00],
        [0x10, 0x01, 0x0A, 0x00],
        [0x01, 0x00, 0x0A, 0x01],
        [0x05, 0x01, 0x05, 0x01],
        [0x0B, 0x00, 0x0A, 0x00],
        [0x0C, 0x00, 0x0A, 0x00],
        [0x0D, 0x00, 0x0A, 0x00],
        [0x09, 0x00, 0x0A, 0x01],
        [0x17, 0x00, 0x05, 0x00],
        [0x08, 0x00, 0x14, 0x00],
        [0x00, 0x01, 0x07, 0x01],
        [0x09, 0x00, 0x05, 0x01],
        [0x14, 0x00, 0x14, 0x00],
        [0x0C, 0x00, 0x0A, 0x00],
        [0x04, 0x01, 0x07, 0x01],
        [0x06, 0x01, 0x07, 0x01],
    ], "S": [
        [0x12, 0x01, 0x05, 0x00],
        [0x0A, 0x00, 0x05, 0x00],
        [0x09, 0x00, 0x05, 0x01],
        [0x01, 0x00, 0x05, 0x01],
        [0x05, 0x01, 0x05, 0x01],
        [0x06, 0x01, 0x05, 0x01],
        [0x0E, 0x01, 0x05, 0x00],
        [0x0F, 0x01, 0x05, 0x00],
        [0x0B, 0x00, 0x02, 0x00],
        [0x0F, 0x01, 0x05, 0x00],
        [0x14, 0x00, 0x14, 0x00],
        [0x10, 0x00, 0x05, 0x00],
        [0x11, 0x01, 0x05, 0x01],
        [0x12, 0x00, 0x05, 0x00],
        [0x00, 0x01, 0x05, 0x01],
        [0x0E, 0x00, 0x05, 0x00],
        [0x04, 0x01, 0x05, 0x01],
        [0x09, 0x00, 0x05, 0x01],
        [0x07, 0x01, 0x05, 0x01],
        [0x10, 0x01, 0x05, 0x00],
        [0x03, 0x01, 0x05, 0x01],
        [0x02, 0x01, 0x05, 0x01],
    ]
}

CHOCO_STAT_TABLE = {
    "C": [0x09C4, 0x01F4, 0x06A4, 0x00C8],
    "B": [0x0BB8, 0x0258, 0x0898, 0x012C],
    "A": [0x0DAC, 0x02BC, 0x0BB8, 0x01F4],
    "S": [0x1388, 0x0320, 0x0FA0, 0x01F4]
}


def generate_chocobo_race_data(rng=None, rank="C", _B747C=0xffffffff):
    chodata = [ChocoboData() for _ in range(6)]

    if rng is None:
        rng = RNG()

    for _ in range(0x28):
        rng.rng()
        rng.rng()

    chodata[0].ai_type = rng.rng() % 4
    for x in range(5):
        chodata[x + 1].dash_speed = CHOCO_STAT_TABLE[rank][0] + (rng.rng() % CHOCO_STAT_TABLE[rank][1])
        chodata[x + 1].speed = CHOCO_STAT_TABLE[rank][2] + (rng.rng() % CHOCO_STAT_TABLE[rank][3])
        chodata[x + 1].ai_type = rng.rng() % 4
        chodata[x + 1].stamina = CHOCO_STAT_TABLE[rank][0] + (rng.rng() % 300)
        chodata[x + 1].running_animation = (1 if rng.rng() & 7 == 0 else 0) * 2
        chodata[x + 1].unknown = ((rng.rng() & 1) * 50) + 50

    names = [x for x in range(43)]

    x = 0
    while x < 0xC8:
        x += 1
        swap1 = rng.rng() % 43
        swap2 = rng.rng() % 43
        a0 = names[swap2]
        a1 = names[swap1]
        names[swap1] = a0
        names[swap2] = a1

    reward_table = REWARD_TABLES[rank]
    reward_pool = [
        0xFF, 0xFF, 0xFF
    ]

    items_in = 0  # s1
    s2 = 0
    s3 = 0xffffffff
    while items_in != 3:
        v0 = rng.rng() % len(reward_table)
        item = reward_table[v0]
        if reward_pool[0] == item[0] or reward_pool[1] == item[0] or reward_pool[2] == item[0]:
            continue
        if reward_table[v0][1] != 0:
            if s2 != 0:
                if item[3] != 0:
                    continue
            # AB5A8
            if _B747C != 0:
                reward_pool[items_in] = item[0]
                items_in += 1
            # AB5C8
            if reward_table[v0][3] == 0:
                continue
            # set rare item
            s3 = item[0]
            s2 = 0xffffffff
            continue
        # AB5F0
        if s2 != 0:
            if reward_table[v0][3] != 0:
                continue
        # AB608
        reward_pool[items_in] = item[0]
        items_in += 1
        if reward_table[v0][3] == 0:
            continue
        # set rare item
        s3 = item[0]
        s2 = 0xffffffff
    # AB634

    reward_pool.sort()

    # there's a jump back up here but i don't think it can ever be taken
    # AB714

    if s3 != 0xffffffff:
        if reward_pool[0] == s3:
            v0 = reward_pool[2]
            reward_pool[2] = s3
            reward_pool[0] = v0
        elif reward_pool[1] == s3:  # AB74C
            v0 = reward_pool[2]
            reward_pool[2] = s3
            reward_pool[1] = v0
    # AB778
    tile_buffer_items = []
    tile_buffer_cards = []
    for i in range(7):
        tile_buffer_items.append(reward_pool[0])
        tile_buffer_cards.append(0)
    for i in range(5):
        tile_buffer_items.append(reward_pool[1])
        tile_buffer_cards.append(1)
    for i in range(3):
        tile_buffer_items.append(reward_pool[2])
        tile_buffer_cards.append(2)

    x = 0
    while x < 100:
        x += 2
        swap1 = rng.rng() % 15
        swap2 = rng.rng() % 15
        a2 = tile_buffer_items[swap1]
        v0 = tile_buffer_items[swap2]
        tile_buffer_items[swap1] = v0
        v0 = tile_buffer_cards[swap2]
        tile_buffer_items[swap2] = a2
        a2 = tile_buffer_cards[swap1]
        tile_buffer_cards[swap1] = v0
        tile_buffer_cards[swap2] = a2
        swap1 = rng.rng() % 15
        swap2 = rng.rng() % 15
        a2 = tile_buffer_items[swap1]
        v0 = tile_buffer_items[swap2]
        tile_buffer_items[swap1] = v0
        v0 = tile_buffer_cards[swap2]
        tile_buffer_items[swap2] = a2
        a2 = tile_buffer_cards[swap1]
        tile_buffer_cards[swap1] = v0
        tile_buffer_cards[swap2] = a2

    return {"items": reward_pool, "tile_cards": tile_buffer_cards, "names": names[1:6], "chocobo_data": chodata}
print(generate_chocobo_race_data(RNG(1000), rank="A", _B747C=0xffffffff))
