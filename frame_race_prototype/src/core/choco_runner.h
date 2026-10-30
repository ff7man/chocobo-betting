// SPDX-FileCopyrightText: 2026 OpenAI
// SPDX-License-Identifier: CC-BY-NC-ND-4.0

#pragma once

namespace ChocoRunner {

/// Advances the optional Chocobo seed patch and racer-memory capture by one frame.
void OnFrame();

/// Returns whether Chocobo runner output should be silent and not presented.
bool IsHeadlessEnabled();

} // namespace ChocoRunner
