const seedInput = document.querySelector('#pc-seed-time');
const generateButton = document.querySelector('#pc-predict-button');
const status = document.querySelector('#pc-seed-search-detail');
const field = document.querySelector('#pc-race-list');
const prizeOutput = document.querySelector('#pc-predict-prizes');
const resultsPanel = document.querySelector('.pc-game-screen');
const mainBetGrid = document.querySelector('#pc-main-bet-grid');
const mainSeedValue = document.querySelector('#pc-found-seed');
const mainSeedTime = document.querySelector('#pc-found-seed-time');
const liveClock = document.querySelector('#pc-live-clock');
const resultBanner = document.querySelector('#pc-result-banner');
const gapSearchButton = document.querySelector('#pc-gap-search');
const gapCancelButton = document.querySelector('#pc-gap-cancel');
const gapStatus = document.querySelector('#pc-gap-status');
const gapResult = document.querySelector('#pc-gap-result');
const gapResultDetails = document.querySelector('#pc-gap-result-details');
const gapField = document.querySelector('#pc-gap-field');
const gapPrizes = document.querySelector('#pc-gap-prizes');
const gapPopulateButton = document.querySelector('#pc-gap-populate');
const gapCandidatePicker = document.querySelector('#pc-gap-candidate');
const gapCandidateLabel = document.querySelector('.candidate-picker');
const rankInput = document.querySelector('#rank');
let currentRunContext = null;
let cancelGapSearch = false;
let matchingGapCandidates = [];
let cancelSeedSearch = false;

function localDateTimeValue(date) {
  const local = new Date(date.getTime() - date.getTimezoneOffset() * 60000);
  return local.toISOString().slice(0, 19);
}

// datetime-local uses local wall time; initialize it from the machine clock.
seedInput.value = localDateTimeValue(new Date());

function renderRacers(target, entrants) {
  const aiTypes = window.PcRaceModel.AI_TYPE_INFO;
  target.replaceChildren(...entrants.map((entrant) => {
    const listItem = target.tagName === 'OL' ? document.createElement('li') : null;
    const row = document.createElement('article');
    row.className = 'racer-card';
    const markers = document.createElement('div');
    markers.className = 'racer-markers';
    const avatar = document.createElement('img');
    avatar.className = `racer-avatar${entrant.slot === 2 ? ' racer-avatar--2' : ''}`;
    avatar.src = `assets/racer-icons/${entrant.slot}.png`;
    avatar.alt = `Chocobo ${entrant.slot}`;
    const type = document.createElement('span');
    const aiType = entrant.aiType === null ? null : aiTypes[entrant.aiType];
    type.className = 'jockey-swatch';
    if (aiType) {
      type.style.setProperty('--jockey-color', aiType.color);
      type.setAttribute('aria-label', `${aiType.label} jockey color`);
    } else if (entrant.isPlaceholder) {
      type.style.setProperty('--jockey-color', '#777');
      type.setAttribute('aria-label', 'Jockey color not found yet');
    } else {
      type.setAttribute('aria-label', 'Player jockey color');
    }
    markers.append(avatar, type);
    const copy = document.createElement('div');
    copy.className = 'racer-copy';
    const top = document.createElement('div');
    top.className = 'racer-top';
    const number = document.createElement('span');
    number.className = 'racer-number';
    number.textContent = String(entrant.slot).padStart(2, '0');
    const name = document.createElement('span');
    name.className = 'racer-name';
    name.textContent = `${entrant.name}${entrant.isPlayer ? ' · You' : ''}`;
    top.append(number, name);
    const stats = document.createElement('div');
    stats.className = 'racer-stats';
    stats.innerHTML = `<span>SPD <b>${entrant.topSpeed}</b></span><span>STA <b>${entrant.stamina}</b></span>`;
    const ai = document.createElement('span');
    ai.className = 'ai-tag';
    ai.textContent = entrant.isPlaceholder ? '—' : aiType ? aiType.label.toUpperCase() : 'PLAYER';
    const sprint = document.createElement('span');
    sprint.className = `sprint-tag${entrant.runningAnimation === 2 ? ' is-sprinting' : ''}`;
    sprint.textContent = entrant.isPlaceholder ? 'SPRINT —' : entrant.runningAnimation === 2 ? 'SPRINTING' : 'NOT SPRINTING';
    copy.append(top, stats, ai, sprint);
    row.append(markers, copy);
    if (listItem) { listItem.append(row); return listItem; }
    return row;
  }));
}

function renderPcBetGrid(rank, prizePrediction = null, bets = null) {
  const pairs = [];
  for (let a = 1; a <= 6; a += 1) for (let b = a + 1; b <= 6; b += 1) pairs.push(`${a}-${b}`);
  const suggested = new Set(bets?.suggestedPairs ?? []);
  const avoid = new Set(bets?.avoidPairs ?? []);
  const folder = String(rank).toLowerCase();
  mainBetGrid.replaceChildren(...pairs.map((pair, index) => {
    const cell = document.createElement('div');
    cell.className = 'bet-cell';
    cell.setAttribute('aria-label', `Chocobos ${pair}`);
    if (avoid.has(pair)) cell.classList.add('has-bronze');
    if (suggested.has(pair)) cell.classList.add('is-predicted');
    const tile = document.createElement('img');
    tile.className = 'tile-image';
    tile.alt = '';
    tile.src = `assets/class-${folder}/tiles/${pair}.png`;
    cell.append(tile);
    if (prizePrediction) {
      const prizeName = prizePrediction.tilePrizes[index];
      const prizeIndex = prizePrediction.prizes.indexOf(prizeName);
      if (prizeIndex >= 0) {
        const roman = rank === 'C';
        const badge = document.createElement('img');
        badge.className = 'bet-badge';
        badge.alt = `${prizeName}, gift ${prizeIndex + 1}`;
        badge.src = `assets/class-${folder}/${roman ? 'badges' : 'item-icons'}/${roman ? ['i','ii','iii'][prizeIndex] : ['one','two','three'][prizeIndex]}.png`;
        cell.append(badge);
        cell.setAttribute('aria-label', `Chocobos ${pair}, prize ${prizeName}${suggested.has(pair) ? ', suggested bet' : ''}${avoid.has(pair) ? ', avoid lowest jockey' : ''}`);
      }
    }
    return cell;
  }));
}

function renderPcGameScreen(entrants, rank, prizes, seedSeconds, bets) {
  document.body.dataset.rank = rank;
  renderRacers(field, entrants);
  renderPcBetGrid(rank, prizes, bets);
  const giftNames = prizes?.prizes ?? [];
  prizeOutput.replaceChildren(...giftNames.map((name) => {
    const chip = document.createElement('span');
    chip.className = 'prize-chip';
    chip.textContent = prizeLabel(name);
    return chip;
  }));
  observedGiftSelects.forEach((select, index) => {
    const giftName = giftNames[index];
    if (giftName && Array.from(select.options).some((option) => option.value === giftName)) {
      select.value = giftName;
      select.dataset.autoPredictedGift = giftName;
    }
  });
  updateGiftGpLabels();
  if (seedSeconds !== null && seedSeconds !== undefined) {
    mainSeedValue.replaceChildren(document.createTextNode(seedSeconds.toLocaleString()));
    const unit = document.createElement('small');
    unit.textContent = 'UNIX';
    mainSeedValue.append(unit);
    mainSeedTime.innerHTML = `FOUND TIME <span>${new Date(seedSeconds * 1000).toLocaleString()}</span>`;
  }
}

function setPcBanner(kind, title, detail) {
  resultBanner.className = `result-banner${kind ? ` is-${kind}` : ''}`;
  document.querySelector('#pc-seed-search-status').textContent = title;
  status.textContent = detail;
  document.querySelector('#pc-banner-mark').textContent = kind === 'searching' ? '◌' : kind === 'success' ? '✓' : kind === 'error' ? '!' : '↳';
}

document.body.dataset.rank = rankInput.value;
renderPcBetGrid(rankInput.value);
renderRacers(field, Array.from({ length: 6 }, (_, index) => ({
  slot: index + 1, name: '—', topSpeed: '—', stamina: '—', aiType: null, runningAnimation: null, isPlaceholder: true,
})));

function renderRaceTiles(target, pairs, rank, suggestedPairs = [], avoidPairs = []) {
  const suggested = new Set(suggestedPairs);
  const avoid = new Set(avoidPairs);
  target.replaceChildren(...pairs.map((pair) => {
    const tile = document.createElement('div');
    const isAvoid = avoid.has(pair);
    const isSuggested = suggested.has(pair);
    tile.className = `pair-tile${isAvoid ? ' is-avoid' : ''}${isSuggested ? ' is-suggested' : ''}`;
    tile.style.setProperty('--pair-tile-art', `url("assets/class-${String(rank).toLowerCase()}/tiles/${pair}.png")`);
    tile.setAttribute('aria-label', `Chocobo bet ${pair}${isAvoid ? ', avoid: includes lowest jockey rank' : ''}${isSuggested ? ', suggested bet' : ''}`);
    if (isAvoid) {
      const marker = document.createElement('span');
      marker.className = 'pair-marker avoid-marker';
      marker.setAttribute('aria-hidden', 'true');
      tile.append(marker);
    }
    if (isSuggested) {
      const marker = document.createElement('span');
      marker.className = 'pair-marker suggested-marker';
      marker.setAttribute('aria-hidden', 'true');
      tile.append(marker);
    }
    return tile;
  }));
}

function renderGapCandidate(match) {
  gapResult.hidden = false;
  gapResultDetails.textContent = `Seed ${currentRunContext.seedSeconds} · Class ${currentRunContext.rank} · RNG call ${match.gap.toLocaleString()} from the starting field.`;
  renderRacers(gapField, match.field.entrants);
  if (match.prizes) {
    gapPrizes.replaceChildren(...match.prizes.prizes.map((name) => {
      const item = document.createElement('span');
      item.className = 'prize-chip';
      item.textContent = prizeLabel(name);
      return item;
    }));
  } else {
    gapPrizes.textContent = `Class ${currentRunContext.rank} prize prediction isn't modeled yet.`;
  }
}

gapCandidatePicker.addEventListener('change', () => {
  const match = matchingGapCandidates[Number(gapCandidatePicker.value)];
  if (match) renderGapCandidate(match);
});

gapPopulateButton.addEventListener('click', () => {
  const match = matchingGapCandidates[Number(gapCandidatePicker.value || 0)];
  if (!match || !currentRunContext) return;

  const nextStartingCall = match.gap + match.field.rngCallsForSetup;
  const bets = window.PcRaceModel.predictBetRecommendations(match.field.entrants);
  seedInput.value = localDateTimeValue(new Date(currentRunContext.seedSeconds * 1000));
  rankInput.value = currentRunContext.rank;
  document.body.dataset.rank = currentRunContext.rank;
  firstRaceSpeed.value = match.field.entrants[0].topSpeed;
  firstRaceStamina.value = match.field.entrants[0].stamina;
  document.querySelector('#pc-seed-racer-name').value = match.field.entrants[0].name;
  updateObservedGiftOptions();
  renderPcGameScreen(match.field.entrants, currentRunContext.rank, match.prizes, currentRunContext.seedSeconds, bets);
  document.querySelector('#pc-gap-start').value = String(nextStartingCall);
  document.querySelectorAll('[data-racer="1"][data-key]').forEach((input) => { input.value = ''; });
  mainSeedTime.innerHTML = `FOUND TIME <span>${new Date(currentRunContext.seedSeconds * 1000).toLocaleString()}</span> · RNG CALL <span>${nextStartingCall.toLocaleString()}</span>`;
  setPcBanner('success', `Race loaded · Class ${currentRunContext.rank}`, `Starting RNG call ${nextStartingCall.toLocaleString()} is set for the following race. Enter its chocobo #1, then search again.`);
  gapStatus.textContent = `Loaded this race above. Starting RNG call ${nextStartingCall.toLocaleString()} is ready for the next race.`;
  resultsPanel.scrollIntoView({ block: 'start', behavior: 'smooth' });
});

const futurePrizeSelect = document.querySelector('#pc-future-prize');
const futureRankSelect = document.querySelector('#pc-future-rank');
const futureSearchButton = document.querySelector('#pc-future-search');
const futureCancelButton = document.querySelector('#pc-future-cancel');
const futureStatus = document.querySelector('#pc-future-status');
const futureResults = document.querySelector('#pc-future-results');
function updateFuturePrizeOptions() {
  const previous = futurePrizeSelect.value;
  const prizes = window.PcRaceModel.CLASS_PRIZE_NAMES[futureRankSelect.value];
  futurePrizeSelect.replaceChildren(...prizes.map((name) => new Option(name, name)));
  if (prizes.includes(previous)) futurePrizeSelect.value = previous;
}
updateFuturePrizeOptions();
futureRankSelect.addEventListener('change', () => {
  updateFuturePrizeOptions();
  futureResults.replaceChildren();
});
let cancelFutureSearch = false;

function renderFutureMatch(match) {
  const card = document.createElement('article');
  card.className = 'future-match';
  const title = document.createElement('h3');
  title.textContent = new Date(match.seedSeconds * 1000).toLocaleString();
  const seed = document.createElement('p');
  seed.className = 'future-seed';
  seed.textContent = `Opening-race seed: ${match.seedSeconds}`;
  const bets = document.createElement('p');
  bets.className = 'future-winning-pairs';
  bets.append('Target prize on green bet: ');
  match.greenPairs.forEach((pair, index) => {
    if (index) bets.append(', ');
    const strong = document.createElement('strong');
    strong.textContent = pair;
    bets.append(strong);
  });
  const prizeLine = document.createElement('p');
  prizeLine.textContent = `Predicted class ${match.rank} prizes: ${match.prizes.prizes.map(prizeLabel).join(', ')}`;
  const racers = document.createElement('ol');
  racers.className = 'pc-racer-strip';
  renderRacers(racers, match.field.entrants);
  const useButton = document.createElement('button');
  useButton.type = 'button';
  useButton.textContent = 'USE THIS TIME IN FIELD PREDICTOR';
  useButton.addEventListener('click', () => {
    rankInput.value = match.rank;
    rankInput.dispatchEvent(new Event('change', { bubbles: true }));
    seedInput.value = localDateTimeValue(new Date(match.seedSeconds * 1000));
    seedInput.dispatchEvent(new Event('change', { bubbles: true }));
    resultsPanel.scrollIntoView({ block: 'start', behavior: 'smooth' });
  });
  card.append(title, seed, bets, prizeLine, racers, useButton);
  return card;
}

futureCancelButton.addEventListener('click', () => { cancelFutureSearch = true; });
futureSearchButton.addEventListener('click', () => {
  const targetPrize = futurePrizeSelect.value;
  const rank = futureRankSelect.value;
  const hours = Number(document.querySelector('#pc-future-hours').value);
  const wanted = Number(document.querySelector('#pc-future-count').value);
  if (!targetPrize || !Number.isInteger(hours) || hours < 1 || hours > 168
      || !Number.isInteger(wanted) || wanted < 1 || wanted > 50) {
    futureStatus.textContent = 'Choose a prize, a look-ahead window from 1–168 hours, and 1–50 results.';
    return;
  }

  cancelFutureSearch = false;
  futureSearchButton.disabled = true;
  futureCancelButton.hidden = false;
  futureResults.replaceChildren();
  const startSeed = Math.floor(Date.now() / 1000) + 1;
  const endSeed = startSeed + hours * 3600 - 1;
  const matches = [];
  let seed = startSeed;
  let checked = 0;
  const batchSize = 200;
  const finish = (stopped) => {
    futureSearchButton.disabled = false;
    futureCancelButton.hidden = true;
    if (!matches.length) {
      futureStatus.textContent = stopped
        ? `Stopped after checking ${checked.toLocaleString()} seconds; no matching times found yet.`
        : `No green-bet opportunities for ${targetPrize} in class ${rank} found in the next ${hours} hours. Try a longer window or another prize.`;
      return;
    }
    const reachedCount = matches.length >= wanted;
    futureStatus.textContent = `${matches.length} upcoming ${matches.length === 1 ? 'opportunity' : 'opportunities'} found for ${targetPrize} in class ${rank}${reachedCount ? ` (the next ${wanted})` : stopped ? ' before stopping' : ` in the next ${hours} hours`}. Compare the generated fields and green pair labels below.`;
    futureResults.replaceChildren(...matches.map(renderFutureMatch));
  };
  const processBatch = () => {
    let processed = 0;
    for (; seed <= endSeed && processed < batchSize; seed += 1, processed += 1) {
      if (cancelFutureSearch) { finish(true); return; }
      const random = new window.PcRaceModel.WindowsCRand(seed);
      const raceField = window.PcRaceModel.generatePcFieldWithRandom(random, rank, null);
      const prizes = window.PcRaceModel.generatePcPrizesWithRandom(random, rank);
      const bets = window.PcRaceModel.predictBetRecommendations(raceField.entrants);
      const green = new Set(bets.suggestedPairs);
      const pairLabels = [];
      for (let a = 1; a <= 6; a += 1) {
        for (let b = a + 1; b <= 6; b += 1) pairLabels.push(`${a}-${b}`);
      }
      const greenPairs = pairLabels.filter((pair, index) => green.has(pair) && prizes.tilePrizes[index] === targetPrize);
      if (greenPairs.length) matches.push({ seedSeconds: seed, rank, field: raceField, prizes, greenPairs });
      checked += 1;
      if (matches.length >= wanted) { seed += 1; finish(false); return; }
    }
    futureStatus.textContent = `Checked ${checked.toLocaleString()} / ${(endSeed - startSeed + 1).toLocaleString()} future seconds… found ${matches.length} so far.`;
    if (seed <= endSeed) window.setTimeout(processBatch, 0);
    else finish(false);
  };
  futureStatus.textContent = `Searching the next ${hours} hours for ${targetPrize} in class ${rank} on a green bet…`;
  window.setTimeout(processBatch, 0);
});

const seedSearchButton = document.querySelector('#pc-seed-search');
const seedSearchResults = document.querySelector('#pc-seed-search-results');
const seedSearchList = document.querySelector('#pc-seed-search-list');
const seedSearchCancel = document.querySelector('#pc-seed-search-cancel');
seedSearchCancel.addEventListener('click', () => { cancelSeedSearch = true; });

seedSearchButton.addEventListener('click', () => {
  const name = document.querySelector('#pc-seed-racer-name').value.trim().toUpperCase();
  const speedValue = document.querySelector('#pc-seed-racer-speed').value.trim();
  const staminaValue = document.querySelector('#pc-seed-racer-stamina').value.trim();
  const topSpeed = Number(speedValue);
  const stamina = Number(staminaValue);
  const hours = Number(document.querySelector('#pc-seed-lookback').value);
  const rank = rankInput.value;
  if (!name || !speedValue || !staminaValue || !Number.isFinite(topSpeed) || !Number.isFinite(stamina)) {
    setPcBanner('error', 'Enter chocobo #1', 'Fill in the name, top speed, and stamina to search.');
    return;
  }
  if (hours !== 1) {
    setPcBanner('error', 'Check the search range', 'The initial seed search looks back one hour from the live PC clock.');
    return;
  }
  const observedGifts = observedGiftSelects.map((select) => (
    select.dataset.autoPredictedGift === select.value ? '' : select.value
  ));

  invalidateCurrentRun();
  cancelSeedSearch = false;
  seedSearchButton.disabled = true;
  seedSearchCancel.hidden = false;
  seedSearchResults.replaceChildren();
  seedSearchList.hidden = true;
  seedSearchList.open = false;
  const endSeed = Math.floor(Date.now() / 1000);
  const startSeed = endSeed - hours * 3600;
  const candidates = [];
  let seed = endSeed;
  const batchSize = 500;
  const finish = (wasCancelled) => {
    seedSearchButton.disabled = false;
    seedSearchCancel.hidden = true;
    if (!candidates.length) {
      seedSearchList.hidden = true;
      setPcBanner('error', 'No matching seed found', wasCancelled
        ? `Stopped after checking ${Math.min(endSeed - seed + 1, endSeed - startSeed + 1).toLocaleString()} seconds.`
        : `No match in the last ${hours} hours. Check chocobo #1's data or widen the search.`);
      return;
    }
    const match = candidates[0];
    const bets = window.PcRaceModel.predictBetRecommendations(match.prediction.entrants);
    currentRunContext = { seedSeconds: match.seedSeconds, rank, stateAfterInitialField: match.prediction.rngStateAfterSetup, player: null };
    document.querySelector('#pc-gap-start').value = '0';
    renderPcGameScreen(match.prediction.entrants, rank, match.prizes, match.seedSeconds, bets);
    const additionalMatches = candidates.slice(1);
    const giftsWereChecked = observedGifts.some(Boolean);
    const matchNoun = giftsWereChecked ? 'seed match' : 'stats match';
    const matchTitle = additionalMatches.length
      ? `${candidates.length} ${matchNoun}${candidates.length === 1 ? '' : 'es'} · ${additionalMatches.length} below`
      : `${candidates.length} ${matchNoun}${candidates.length === 1 ? '' : 'es'}`;
    const matchDetail = giftsWereChecked
      ? 'First chocobo and selected gifts match.'
      : 'First chocobo stats match only; no gifts were selected to rule out collisions.';
    setPcBanner('success', matchTitle, `${wasCancelled ? 'Search stopped' : `Searched ${hours} hour`} · ${matchDetail}`);
    gapStatus.textContent = 'Ready to search the next race from this seed.';
    seedSearchList.hidden = candidates.length <= 1;
    seedSearchList.open = false;
    if (additionalMatches.length) {
      const newestAdditional = additionalMatches[0].seedSeconds;
      seedSearchList.querySelector('summary').textContent = `Potential seed values to use (${additionalMatches.length} additional) · ${new Date(newestAdditional * 1000).toLocaleString()} · Unix ${newestAdditional}`;
    }
    additionalMatches.forEach(({ seedSeconds, prediction, prizes }) => {
      const card = document.createElement('article');
      card.className = 'seed-candidate';
      const heading = document.createElement('h4');
      heading.textContent = `${new Date(seedSeconds * 1000).toLocaleString()} · Unix seed ${seedSeconds}`;
      const list = document.createElement('ol');
      list.className = 'pc-racer-strip';
      renderRacers(list, prediction.entrants);
      const useButton = document.createElement('button');
      useButton.type = 'button';
      useButton.textContent = 'USE THIS SEED';
      useButton.addEventListener('click', () => {
        rankInput.value = rank;
        rankInput.dispatchEvent(new Event('change', { bubbles: true }));
        seedInput.value = localDateTimeValue(new Date(seedSeconds * 1000));
        seedInput.dispatchEvent(new Event('change', { bubbles: true }));
        resultsPanel.scrollIntoView({ block: 'start', behavior: 'smooth' });
      });
      const gifts = document.createElement('p');
    gifts.textContent = `Gifts: ${prizes.prizes.map(prizeLabel).join(', ')}`;
      card.append(heading, gifts, list, useButton);
      seedSearchResults.append(card);
    });
  };
  const processBatch = () => {
    let checked = 0;
    for (; seed >= startSeed && checked < batchSize; seed -= 1, checked += 1) {
      if (cancelSeedSearch) { finish(true); return; }
      const random = new window.PcRaceModel.WindowsCRand(seed);
      const prediction = window.PcRaceModel.generatePcFieldWithRandom(random, rank, null);
      const first = prediction.entrants[0];
      if (first.name === name && first.topSpeed === topSpeed && first.stamina === stamina) {
        const stateAfterInitialField = random.state;
        const prizes = window.PcRaceModel.generatePcPrizesWithRandom(random, rank);
        const giftsMatch = observedGifts.every((prize) => !prize || prizes.prizes.includes(prize));
        if (giftsMatch) {
          prediction.rngStateAfterSetup = stateAfterInitialField;
          candidates.push({ seedSeconds: seed, prediction, prizes });
        }
      }
    }
    const scanned = endSeed - Math.max(seed, startSeed - 1);
    setPcBanner('searching', 'Searching backward from live time', `Checked ${scanned.toLocaleString()} / ${(endSeed - startSeed + 1).toLocaleString()} seconds · ${candidates.length} matches so far.`);
    if (seed >= startSeed) window.setTimeout(processBatch, 0);
    else finish(false);
  };
  setPcBanner('searching', 'Searching backward from live time', new Date(endSeed * 1000).toLocaleString());
  window.setTimeout(processBatch, 0);
});

function invalidateCurrentRun() {
  currentRunContext = null;
  seedSearchList.hidden = true;
  seedSearchList.open = false;
  seedSearchResults.replaceChildren();
  gapResult.hidden = true;
  gapStatus.textContent = 'Find a seed above or generate a field from an exact seed before searching.';
  renderPcBetGrid(rankInput.value);
  renderRacers(field, Array.from({ length: 6 }, (_, index) => ({
    slot: index + 1, name: '—', topSpeed: '—', stamina: '—', aiType: null, runningAnimation: null, isPlaceholder: true,
  })));
  prizeOutput.replaceChildren();
  updateGiftGpLabels();
  mainSeedValue.replaceChildren(document.createTextNode('—'));
  const unit = document.createElement('small');
  unit.textContent = 'UNIX';
  mainSeedValue.append(unit);
  mainSeedTime.innerHTML = 'Current PC time <span>—</span>';
  setPcBanner('', 'Ready when you are', 'Enter chocobo #1 and search backward from the live PC clock.');
}

const observedGiftSelects = [...document.querySelectorAll('[data-observed-gift]')];
const PRIZE_GP_VALUES = {
  Potion: 5,
  'Phoenix Down': 10,
  Hyper: 10,
  Tranquilizer: 10,
  'Hi-Potion': 15,
  'Hero Drink': 15,
  'Antarctic Wind': 20,
  'Bolt Plume': 20,
  'Fire Fang': 20,
  Ether: 30,
  'Ice Crystal': 50,
  'Fire Veil': 50,
  'Swift Bolt': 50,
  'Turbo Ether': 150,
  Elixir: 200,
  Megalixir: 300,
  'Enemy Away Materia': 300,
  'Counter Attack Materia': 300,
  'Sneak Attack Materia': 300,
  'Precious Watch': 300,
  Chocobracelet: 400,
  "Cat's Bell": 500,
  'Sprint Shoes': 500,
  'Magic Counter Materia': 500,
};
function prizeLabel(name) {
  const value = PRIZE_GP_VALUES[name];
  return value === undefined ? name : `${name} · ${value} GP`;
}
function updateGiftGpLabels() {
  observedGiftSelects.forEach((select, index) => {
    const output = document.querySelector(`[data-predicted-gift="${index + 1}"]`);
    const value = PRIZE_GP_VALUES[select.value];
    if (output) output.textContent = value === undefined ? '' : `${value} GP`;
  });
}

function updateObservedGiftOptions() {
  observedGiftSelects.forEach((select) => {
    const previous = select.value;
    const prizes = window.PcRaceModel.CLASS_PRIZE_NAMES[rankInput.value];
    select.replaceChildren(new Option('Any gift', ''), ...prizes.map((name) => new Option(name, name)));
    if (prizes.includes(previous)) select.value = previous;
  });
}
updateObservedGiftOptions();
function updateClassArt() {
  const folder = rankInput.value.toLowerCase();
  document.querySelectorAll('.gift-field img').forEach((image, index) => {
    image.src = `assets/class-${folder}/item-icons/${['one','two','three'][index]}.png`;
  });
}
updateClassArt();
function updateLiveClock() { liveClock.textContent = new Date().toLocaleTimeString(); }
updateLiveClock();
window.setInterval(updateLiveClock, 1000);

seedInput.addEventListener('change', () => generateButton.click());
observedGiftSelects.forEach((select) => {
  const markAsUserSelected = () => { delete select.dataset.autoPredictedGift; };
  select.addEventListener('input', markAsUserSelected);
  select.addEventListener('change', markAsUserSelected);
});
document.querySelectorAll('.pc-observed-stats input, [data-observed-gift]').forEach((input) => {
  input.addEventListener('input', invalidateCurrentRun);
  input.addEventListener('change', invalidateCurrentRun);
});
rankInput.addEventListener('change', () => {
  document.body.dataset.rank = rankInput.value;
  updateObservedGiftOptions();
  updateClassArt();
  invalidateCurrentRun();
});
function autoSelectClassFromStats(speedInput, staminaInput) {
  const inferredRank = window.PcRaceModel.inferPcClass(speedInput.value, staminaInput.value);
  if (inferredRank && rankInput.value !== inferredRank) {
    rankInput.value = inferredRank;
    rankInput.dispatchEvent(new Event('change', { bubbles: true }));
  }
}
const firstRaceSpeed = document.querySelector('#pc-seed-racer-speed');
const firstRaceStamina = document.querySelector('#pc-seed-racer-stamina');
const nextRaceSpeed = document.querySelector('[data-racer="1"][data-key="speed"]');
const nextRaceStamina = document.querySelector('[data-racer="1"][data-key="stamina"]');
[
  [firstRaceSpeed, firstRaceStamina],
  [nextRaceSpeed, nextRaceStamina],
].forEach(([speedInput, staminaInput]) => {
  const updateClass = () => autoSelectClassFromStats(speedInput, staminaInput);
  speedInput.addEventListener('input', updateClass);
  speedInput.addEventListener('change', updateClass);
  staminaInput.addEventListener('input', updateClass);
  staminaInput.addEventListener('change', updateClass);
});
generateButton.addEventListener('click', () => {
  const date = new Date(seedInput.value);
  if (!seedInput.value || Number.isNaN(date.getTime())) {
    setPcBanner('error', 'Enter a seed time', 'Choose the local date and time used for this PC run.');
    field.replaceChildren();
    prizeOutput.replaceChildren();
    return;
  }

  const seedSeconds = Math.floor(date.getTime() / 1000);
  const rank = document.querySelector('#rank').value;
  document.body.dataset.rank = rank;
  let prediction;
  let prizePrediction;
  let betPrediction;
  let stateAfterInitialField;
  try {
    const random = new window.PcRaceModel.WindowsCRand(seedSeconds);
    prediction = window.PcRaceModel.generatePcFieldWithRandom(random, rank, null);
    stateAfterInitialField = random.state;
    betPrediction = window.PcRaceModel.predictBetRecommendations(prediction.entrants);
    prizePrediction = window.PcRaceModel.generatePcPrizesWithRandom(random, rank);
  } catch (error) {
    setPcBanner('error', 'Could not generate the field', error.message);
    field.replaceChildren();
    prizeOutput.replaceChildren();
    return;
  }

  setPcBanner('success', `Seed field ready · Class ${rank}`, `${prediction.rngCallsForSetup} setup RNG calls · Opening gifts predicted; finish order is not simulated.`);
  currentRunContext = { seedSeconds, rank, stateAfterInitialField, player: null };
  document.querySelector('#pc-gap-start').value = '0';
  gapStatus.textContent = 'Ready to search from this field and seed.';
  gapResult.hidden = true;
  renderPcGameScreen(prediction.entrants, rank, prizePrediction, seedSeconds, betPrediction);
  resultsPanel.scrollIntoView({ block: 'start', behavior: 'smooth' });
});

gapCancelButton.addEventListener('click', () => {
  cancelGapSearch = true;
});

gapSearchButton.addEventListener('click', () => {
  if (!currentRunContext) {
    gapStatus.textContent = 'Generate the first field from the seed above before searching.';
    return;
  }

  const startCalls = Number(document.querySelector('#pc-gap-start').value);
  const maxCalls = Number(document.querySelector('#pc-gap-limit').value);
  if (!Number.isSafeInteger(startCalls) || startCalls < 0 || startCalls > 1000000
      || !Number.isSafeInteger(maxCalls) || maxCalls < 0 || maxCalls > 1000000
      || startCalls > maxCalls) {
    gapStatus.textContent = 'Enter a starting RNG call and maximum from 0 to 1,000,000; the maximum must be at least the start.';
    return;
  }

  const read = (key) => document.querySelector(`[data-racer="1"][data-key="${key}"]`).value.trim();
  const speedValue = read('speed');
  const staminaValue = read('stamina');
  const observed = {
    name: read('name').toUpperCase(),
    topSpeed: Number(speedValue),
    stamina: Number(staminaValue),
  };
  if (!observed.name || !speedValue || !staminaValue || !Number.isFinite(observed.topSpeed) || !Number.isFinite(observed.stamina)) {
    gapStatus.textContent = 'Enter chocobo #1 name, top speed, and stamina.';
    return;
  }

  const observedGifts = [...document.querySelectorAll('[data-observed-gift]')]
    .map((select) => select.dataset.autoPredictedGift === select.value ? '' : select.value)
    .filter(Boolean);
  cancelGapSearch = false;
  matchingGapCandidates = [];
  gapSearchButton.disabled = true;
  gapCancelButton.hidden = false;
  gapResult.hidden = true;
  gapCandidateLabel.hidden = true;
  gapCandidatePicker.replaceChildren();
  gapField.replaceChildren();
  gapPrizes.replaceChildren();
  let gap = startCalls;
  let gapState = currentRunContext.stateAfterInitialField;
  const seekRandom = new window.PcRaceModel.WindowsCRand(0);
  seekRandom.state = gapState;
  for (let calls = 0; calls < startCalls; calls += 1) seekRandom.next();
  gapState = seekRandom.state;
  const batchSize = 1500;

  const finishSearch = (wasCancelled) => {
    gapSearchButton.disabled = false;
    gapCancelButton.hidden = true;
    if (matchingGapCandidates.length === 0) {
      gapStatus.textContent = wasCancelled
        ? `Search stopped after ${Math.max(0, gap - startCalls).toLocaleString()} candidates in ${startCalls.toLocaleString()}–${maxCalls.toLocaleString()} calls; no matching field found yet.`
        : `No matching field found in ${startCalls.toLocaleString()}–${maxCalls.toLocaleString()} calls. Check the seed and chocobo #1 data, or increase the search range.`;
      return;
    }
    const rangeText = wasCancelled
      ? `before stopping at ${Math.max(startCalls, gap - 1).toLocaleString()} calls`
      : `in ${startCalls.toLocaleString()}–${maxCalls.toLocaleString()} calls`;
    gapStatus.textContent = `${matchingGapCandidates.length} candidate gap${matchingGapCandidates.length === 1 ? '' : 's'} matched ${rangeText}: ${matchingGapCandidates.map(({ gap: candidateGap }) => candidateGap.toLocaleString()).join(', ')}. Compare the full generated fields below to confirm the other racers.`;
    matchingGapCandidates.forEach((match, index) => {
      gapCandidatePicker.add(new Option(`${match.gap.toLocaleString()} calls`, String(index)));
    });
    if (matchingGapCandidates.length > 1) gapCandidateLabel.hidden = false;
    renderGapCandidate(matchingGapCandidates[0]);
  };

  const processBatch = () => {
    const end = Math.min(maxCalls, gap + batchSize - 1);
    for (; gap <= end; gap += 1) {
      if (cancelGapSearch) { finishSearch(true); return; }
      const candidateRandom = new window.PcRaceModel.WindowsCRand(0);
      candidateRandom.state = gapState;
      const candidateField = window.PcRaceModel.generatePcFieldWithRandom(candidateRandom, currentRunContext.rank, currentRunContext.player);
      const first = candidateField.entrants[0];
      const firstMatches = first.name === observed.name
        && first.topSpeed === observed.topSpeed
        && first.stamina === observed.stamina;
      if (firstMatches) {
        const candidatePrizes = window.PcRaceModel.generatePcPrizesWithRandom(candidateRandom, currentRunContext.rank);
        const giftsMatch = observedGifts.every((gift) => candidatePrizes?.prizes.includes(gift));
        if (giftsMatch) matchingGapCandidates.push({ gap, field: candidateField, prizes: candidatePrizes });
      }
      const advance = new window.PcRaceModel.WindowsCRand(0);
      advance.state = gapState;
      advance.next();
      gapState = advance.state;
    }
    gapStatus.textContent = `Searched ${(gap - startCalls).toLocaleString()} / ${(maxCalls - startCalls + 1).toLocaleString()} call gaps (${startCalls.toLocaleString()}–${maxCalls.toLocaleString()})… ${matchingGapCandidates.length} candidate match${matchingGapCandidates.length === 1 ? '' : 'es'} so far.`;
    if (gap <= maxCalls) window.setTimeout(processBatch, 0);
    else finishSearch(false);
  };

  gapStatus.textContent = `Searching ${startCalls.toLocaleString()}–${maxCalls.toLocaleString()} intervening calls…`;
  window.setTimeout(processBatch, 0);
});
