# PC calibration sample 1

- Clock set to: January 1, 2023, 12:25:05 PM CST
- Class: C
- Race length: short
- Gifts shown: Hi-Potion, Turbo Ether, Megalixir

Observed field, in the order recorded:

| Top speed (km) | Stamina | Name |
| ---: | ---: | --- |
| 85 | 273 | Terry |
| 78 | 263 | T |
| 76 | 264 | Tim |
| 74 | 276 | John |
| 84 | 272 | Ju |
| 82 | 256 | George |

Winner and whether one of these entries is the player's chocobo were not specified in the note.

## Seed search result

Searching Unix-second seeds within 24 hours of the supplied clock time found an exact match at `1672597506`, one second after the time set. The current Windows CRT field model reproduces all six recorded names, speeds, and stamina values in the recorded order. This is a strong candidate for the seed used to generate the field, though the one-second offset could reflect when the game called `time()` rather than a fixed seed adjustment.

## Race 2 from the same run

- Class: C
- Race length: short
- Gifts shown: Tranquilizer, Hyper, Phoenix Down
- Candidate first-race seed: `1672597506`

| Top speed (km) | Stamina | Name |
| ---: | ---: | --- |
| 80 | 275 | T |
| 80 | 276 | LE |
| 79 | 259 | ROBER |
| 74 | 267 | TOM |
| 79 | 252 | K |
| 76 | 253 | Gary |

Searching the same independent-field model across seeds from `1672597506` through `1672598106` (the following ten minutes) found no exact match. A continuation search does reproduce Race 2 exactly: after Race 1's 516 field-setup draws, advancing **17,908** more `rand()` calls produces the six Race 2 entrants in order. This total includes any intervening menu, race, and result-screen calls; it is not a race-only count. The reproducible search is [`../scripts/search-race-call-gap.js`](../scripts/search-race-call-gap.js).

This backs the continuing-RNG hypothesis, but the 17,908-call gap is inferred from the observed Race 2 field. It is not yet derived from a frame-accurate simulation of the race. The next step is to account for the per-racer update branches and compare their total against the observed short-race duration.

## More Race 2 samples

Two additional Race 2 records were provided. The user confirmed both runs used the same Race 1 seed (`1672597506`), so the gaps below are exact field matches found by advancing that seed's RNG stream. They remain backsolved from the observations, not directly counted from a running game.

| Run | Gifts | Entrants in recorded order (speed / stamina / name) | Candidate calls from Race 1 field |
| --- | --- | --- | ---: |
| 2 | Tranquilizer, Turbo Ether, Ice Crystal | 81/268 Fox; 83/250 Lia; 88/261 Pau; 79/279 Sean; 82/255 George; 75/277 Ju | 18,017 |
| 3 | Hyper, Tranquilizer, Hi-Potion | 83/265 T; 74/274 Peter; 76/276 Rober; 80/272 James; 81/261 Harvey; 82/277 Edward | 17,964 |

These values differ from the first recorded Race 2 gap (17,908) even though the runs shared the Race 1 seed. This indicates the RNG stream advances by a different number of calls before Race 2's field is generated in these runs. Advancing to each candidate field and then generating the class C prizes also reproduces each recorded gift set. The gaps count all calls between the Race 1 and Race 2 field setups, including prize/menu, race, and transition work; they are not race-only counts.

## Predicting the first-race prizes

The PC decompilation selects three distinct items from the class C prize table, then shuffles the 15 bet tiles with 100 pairs of `rand()` calls. With the candidate seed and the recorded Race 1 field, the class C prize model predicts the same three-item set: **Hi-Potion, Turbo Ether, and Megalixir**. Prize selection itself takes 5 calls for this sample; tile shuffling takes another 200. The generator preserves the game’s selected-slot ordering, so the model may list the same three prizes in a different display order than notes taken from the screen.

That match supports predicting the initial prize set from the seed. It does not yet validate every later race’s prizes: we still need the exact seed and call stream at each return to the bet menu, plus the prize-generation point relative to race setup. The class C prize generator is recorded in `../pc-race-model.js`.
