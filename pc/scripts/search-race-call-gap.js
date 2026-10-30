#!/usr/bin/env node

// Find how many Windows CRT rand() calls between two field generations make
// the second recorded field appear. This infers a draw gap; it does not yet
// explain which per-frame game branches consume those draws.

const fs = require('node:fs');
const path = require('node:path');
const PcRaceModel = require('../pc-race-model.js');

const dataPath = process.argv[2] || path.join(__dirname, '..', 'data', 'class-c-race-sequence.json');
const maxCalls = Number(process.argv[3] || 1000000);
if (!Number.isSafeInteger(maxCalls) || maxCalls < 0) {
  throw new Error('maxCalls must be a non-negative integer.');
}

const data = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
if (!data.races || data.races.length < 2) throw new Error('Input data must contain at least two races.');
const [observedFirst, observedSecond] = data.races;
const firstRng = new PcRaceModel.WindowsCRand(data.seedSeconds);
const generatedFirst = PcRaceModel.generatePcFieldWithRandom(firstRng, data.rank);

function sameField(generated, observed) {
  return generated.entrants.length === observed.length && generated.entrants.every((entrant, index) => {
    const target = observed[index];
    return entrant.name === target.name.toUpperCase()
      && entrant.topSpeed === target.topSpeed
      && entrant.stamina === target.stamina;
  });
}

if (!sameField(generatedFirst, observedFirst.entrants)) {
  throw new Error('The input seed does not reproduce Race 1. Verify seed, rank, and entrant order.');
}

let gapState = firstRng.state;
for (let gap = 0; gap <= maxCalls; gap += 1) {
  const candidateRng = new PcRaceModel.WindowsCRand(0);
  candidateRng.state = gapState;
  const generatedSecond = PcRaceModel.generatePcFieldWithRandom(candidateRng, data.rank);
  if (sameField(generatedSecond, observedSecond.entrants)) {
    console.log(`Exact Race 2 match after ${gap.toLocaleString()} intervening rand() calls.`);
    console.log(`Seed: ${data.seedSeconds}; class: ${data.rank}; race length: ${data.raceLength}.`);
    console.log(`Race 1 field setup used ${generatedFirst.rngCallsForSetup} rand() calls.`);
    console.log('This is the inferred gap, not yet a frame-accurate simulation of the race.');
    process.exit(0);
  }
  const nextGapState = new PcRaceModel.WindowsCRand(gapState);
  nextGapState.next();
  gapState = nextGapState.state;
}

console.log(`No exact field match for 0–${maxCalls.toLocaleString()} intervening rand() calls.`);
process.exitCode = 1;
