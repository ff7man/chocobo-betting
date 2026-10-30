// Initial PC FFVII chocobo field generator based on ff7man/ff7-chocobo.
// This reproduces entrant setup from a Windows CRT rand() seed. It does not
// yet simulate the race or advance the RNG through race updates.

const CLASS_STATS = {
  C: { topSpeed: [2500, 500], speed: [1700, 200], stamina: 2500 },
  B: { topSpeed: [3000, 600], speed: [2200, 300], stamina: 3000 },
  A: { topSpeed: [3500, 700], speed: [3000, 500], stamina: 3500 },
  S: { topSpeed: [5000, 800], speed: [4000, 500], stamina: 5000 },
};

const PC_RACER_NAMES = [
  'SAM', 'ELEN', 'BLUES', 'TOM', 'JOHN', 'GARY', 'MIKE', 'SANDY', 'JU', 'LY',
  'JOEL', 'GREY', 'EDWARD', 'JAMES', 'HARVEY', 'DAN', 'RUDY', 'GRAHAM', 'FOX',
  'CLIVE', 'SEAN', 'YOUNG', 'ROBIN', 'DARIO', 'K', 'ARL', 'SARA', 'MARIE',
  'SAMMY', 'LIA', 'KNIGHT', 'PAULA', 'PAU', 'LE', 'PETER', 'AIMEE', 'TERRY',
  'ANDY', 'NANCY', 'TIM', 'ROBER', 'T', 'GEORGE', 'JENNY', 'RICA',
];
// AI type values are zero-based in the PC data; the labels use the mapping
// requested for the existing betting interface (1 Silver, 2 Gold, 3 Bronze, 4 Platinum).
const AI_TYPE_INFO = [
  { label: 'Silver', color: '#718fca', rank: 2 },
  { label: 'Gold', color: '#f0d43a', rank: 3 },
  { label: 'Bronze', color: '#a96e3c', rank: 1 },
  { label: 'Platinum', color: '#85878a', rank: 4 },
];

// PC reward records from ff7-chocobo/NEWFF7/D_0097C8A8.cpp. Each row stores
// item ID and move-to-last; duplicates remain because random selection indexes
// the complete table uniformly. Rank indices are C=0, B=1, A=2, S=3.
const PC_PRIZE_NAMES = [
  'Sprint Shoes', 'Counter Attack Materia', 'Magic Counter Materia', 'Precious Watch',
  'Ether', 'Hero Drink', 'Bolt Plume', 'Elixir', 'Fire Fang', 'Antarctic Wind',
  'Potion', 'Phoenix Down', 'Hyper', 'Tranquilizer', "Cat's Bell", 'Enemy Away Materia',
  'Sneak Attack Materia', 'Chocobracelet', 'Swift Bolt', 'Fire Veil', 'Megalixir',
  'Turbo Ether', 'Hi-Potion', 'Ice Crystal',
];
const CLASS_PRIZE_TABLES = {
  C: [[23,1],[8,1],[21,0],[22,0],[20,1],[11,1],[12,0],[13,0],[20,1]],
  B: [[8,0],[10,0],[20,0],[18,1],[8,0],[23,0],[21,0],[22,0],[23,0],[11,1],[12,0],[13,0],[9,1],[5,1],[23,0]],
  A: [[8,0],[10,0],[14,0],[15,0],[12,0],[16,0],[1,1],[5,1],[11,0],[12,0],[13,0],[9,1],[23,0],[8,0],[0,1],[9,1],[20,0],[12,0],[4,1],[6,1]],
  S: [[18,0],[10,0],[9,1],[1,1],[5,1],[6,1],[14,0],[15,0],[11,0],[15,0],[20,0],[16,0],[17,1],[18,0],[0,1],[14,0],[4,1],[9,1],[7,1],[16,0],[3,1],[2,1]],
};
const CLASS_PRIZE_NAMES = Object.fromEntries(Object.entries(CLASS_PRIZE_TABLES).map(([rank, rows]) => [
  rank,
  [...new Set(rows.map(([id]) => PC_PRIZE_NAMES[id]))].sort((a, b) => a.localeCompare(b)),
]));

/** Windows Visual C runtime rand(), as used by the decompiled PC game. */
class WindowsCRand {
  constructor(seed) {
    this.state = Number(seed) >>> 0;
  }

  next() {
    this.state = (Math.imul(this.state, 214013) + 2531011) >>> 0;
    return (this.state >>> 16) & 0x7fff;
  }
}

/**
 * Generate a PC-version field from the Unix-time seed in seconds.
 *
 * `player` may be null (six computer-controlled entrants), or an object with
 * `{ name, topSpeed, stamina }` in the same displayed units as the game. When
 * supplied, the player occupies slot 1 and five AI fields are generated, as in
 * the decompiled player-race path.
 */
function generatePcFieldWithRandom(random, rank, player = null) {
  const stats = CLASS_STATS[String(rank).toUpperCase()];
  if (!stats) throw new RangeError(`Unknown race class: ${rank}`);

  const lanes = Array.from({ length: 6 }, (_, i) => Math.floor((i * 0xe0) / 6) + 0x10);
  for (let i = 0; i < 40; i++) {
    const a = random.next() % 6;
    const b = random.next() % 6;
    [lanes[a], lanes[b]] = [lanes[b], lanes[a]];
  }

  const entrants = [];
  for (let i = 0; i < 6; i++) {
    const lane = lanes[i];
    if (player && i === 0) {
      entrants.push({
        slot: i + 1,
        name: String(player.name ?? 'PLAYER').toUpperCase(),
        isPlayer: true,
        lane,
        topSpeed: Number(player.topSpeed),
        stamina: Number(player.stamina),
        coatColor: random.next() % 4,
        aiType: null,
      });
      continue;
    }

    const rawTopSpeed = stats.topSpeed[0] + (random.next() % stats.topSpeed[1]);
    const rawSpeed = stats.speed[0] + (random.next() % stats.speed[1]);
    const coatColor = random.next() % 4;
    const rawStamina = stats.stamina + (random.next() % 300);
    const runningAnimation = (random.next() & 7) === 0 ? 2 : 0;
    const vigor = ((random.next() & 1) * 50) + 50;
    entrants.push({
      slot: i + 1,
      name: null,
      isPlayer: false,
      lane,
      rawTopSpeed,
      rawSpeed,
      rawStamina,
      topSpeed: Math.trunc(rawTopSpeed / 34),
      stamina: Math.trunc(rawStamina / 10),
      coatColor,
      aiType: coatColor,
      runningAnimation,
      vigor,
    });
  }

  const nameOrder = Array.from({ length: PC_RACER_NAMES.length }, (_, i) => i);
  for (let i = 0; i < 200; i++) {
    const a = random.next() % PC_RACER_NAMES.length;
    const b = random.next() % PC_RACER_NAMES.length;
    [nameOrder[a], nameOrder[b]] = [nameOrder[b], nameOrder[a]];
  }
  for (let i = 0; i < entrants.length; i++) {
    if (player && i === 0) continue;
    entrants[i].name = PC_RACER_NAMES[nameOrder[i]];
  }

  return {
    rank: String(rank).toUpperCase(),
    rngCallsForSetup: player ? 511 : 516,
    entrants,
  };
}

/** Infer a class from the displayed top-speed/stamina ranges, or return null if ambiguous. */
function inferPcClass(topSpeed, stamina) {
  const hasTopSpeed = topSpeed !== null && topSpeed !== undefined && topSpeed !== '' && Number.isFinite(Number(topSpeed));
  const hasStamina = stamina !== null && stamina !== undefined && stamina !== '' && Number.isFinite(Number(stamina));
  if (!hasTopSpeed && !hasStamina) return null;

  const speed = Number(topSpeed);
  const staminaValue = Number(stamina);
  const matches = Object.entries(CLASS_STATS).filter(([, stats]) => {
    const speedMin = Math.trunc(stats.topSpeed[0] / 34);
    const speedMax = Math.trunc((stats.topSpeed[0] + stats.topSpeed[1] - 1) / 34);
    const staminaMin = Math.trunc(stats.stamina / 10);
    const staminaMax = Math.trunc((stats.stamina + 299) / 10);
    return (!hasTopSpeed || (speed >= speedMin && speed <= speedMax))
      && (!hasStamina || (staminaValue >= staminaMin && staminaValue <= staminaMax));
  });
  return matches.length === 1 ? matches[0][0] : null;
}

/** Apply the existing top-speed / lowest-jockey / jockey-rank bet heuristic. */
function predictBetRecommendations(entrants) {
  const racers = entrants.map((entrant, index) => {
    const jockey = entrant.aiType === null ? null : AI_TYPE_INFO[entrant.aiType];
    return {
      slot: index + 1,
      name: entrant.name,
      speed: entrant.topSpeed,
      jockey: jockey?.label ?? 'Player',
      jockeyRank: jockey?.rank ?? 4,
    };
  });
  const lowestRank = Math.min(...racers.map((racer) => racer.jockeyRank));
  const excludedSlots = lowestRank < 4
    ? racers.filter((racer) => racer.jockeyRank === lowestRank).map((racer) => racer.slot)
    : [];
  let candidates = lowestRank < 4
    ? racers.filter((racer) => racer.jockeyRank !== lowestRank)
    : racers;
  if (candidates.length < 3) candidates = racers;
  candidates.sort((a, b) => b.speed - a.speed || b.jockeyRank - a.jockeyRank);
  const topThree = candidates.slice(0, 3);
  const suggestedPairs = [
    [topThree[0], topThree[1]],
    [topThree[0], topThree[2]],
    [topThree[1], topThree[2]],
  ].map(([a, b]) => [a.slot, b.slot].sort((x, y) => x - y).join('-'));
  const avoidPairs = [];
  for (let a = 1; a <= racers.length; a += 1) {
    for (let b = a + 1; b <= racers.length; b += 1) {
      if (excludedSlots.includes(a) || excludedSlots.includes(b)) avoidPairs.push(`${a}-${b}`);
    }
  }
  return { racers, topThree, suggestedPairs, excludedSlots, avoidPairs };
}

function generatePcField(seedSeconds, rank, player = null) {
  if (!Number.isSafeInteger(Number(seedSeconds)) || Number(seedSeconds) < 0) {
    throw new RangeError('Seed must be a non-negative integer Unix time in seconds.');
  }

  const random = new WindowsCRand(seedSeconds);
  const generated = generatePcFieldWithRandom(random, rank, player);
  return {
    version: 'PC Windows CRT rand model',
    seedSeconds: Number(seedSeconds),
    rngStateAfterSetup: random.state,
    ...generated,
  };
}

/** Generate three distinct prizes for a PC class and shuffle the bet grid. */
function generatePcPrizesWithRandom(random, rank) {
  const table = CLASS_PRIZE_TABLES[String(rank).toUpperCase()];
  if (!table) throw new RangeError(`Unknown prize class: ${rank}`);
  const selected = [];
  let moveLastId = -1;
  let hasMoveLast = false;
  let selectionCalls = 0;

  while (selected.length < 3) {
    const [id, moveLast] = table[random.next() % table.length];
    selectionCalls += 1;
    if (selected.some((prize) => prize.id === id)) continue;
    if (hasMoveLast && moveLast) continue;

    selected.push({ id, name: PC_PRIZE_NAMES[id], moveLast: Boolean(moveLast) });
    if (moveLast) {
      moveLastId = id;
      hasMoveLast = true;
    }
  }

  // The PC game sorts selected prize IDs first, then moves the flagged reward
  // to the final slot. Keep that ordering for the prize list and tile groups.
  selected.sort((a, b) => a.id - b.id);
  if (moveLastId !== -1) {
    const lastIndex = selected.findIndex((prize) => prize.id === moveLastId);
    selected.push(selected.splice(lastIndex, 1)[0]);
  }

  // The PC decomp shuffles fifteen bet tiles using 100 pairs of rand() calls.
  const tilePrizeIds = [
    ...Array(7).fill(selected[0].id),
    ...Array(5).fill(selected[1].id),
    ...Array(3).fill(selected[2].id),
  ];
  for (let i = 0; i < 100; i += 1) {
    const a = random.next() % 15;
    const b = random.next() % 15;
    [tilePrizeIds[a], tilePrizeIds[b]] = [tilePrizeIds[b], tilePrizeIds[a]];
  }

  return {
    prizes: selected.map(({ name }) => name),
    selectionCalls,
    gridShuffleCalls: 200,
    totalCalls: selectionCalls + 200,
    tilePrizeIds,
    tilePrizes: tilePrizeIds.map((id) => PC_PRIZE_NAMES[id]),
  };
}

function generatePcClassCPrizesWithRandom(random) {
  return generatePcPrizesWithRandom(random, 'C');
}

const PcRaceModel = {
  WindowsCRand,
  AI_TYPE_INFO,
  CLASS_PRIZE_NAMES,
  inferPcClass,
  generatePcField,
  generatePcFieldWithRandom,
  generatePcClassCPrizesWithRandom,
  generatePcPrizesWithRandom,
  predictBetRecommendations,
};
if (typeof window !== 'undefined') window.PcRaceModel = PcRaceModel;
if (typeof module !== 'undefined' && module.exports) module.exports = PcRaceModel;
