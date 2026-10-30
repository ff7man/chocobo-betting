// SPDX-FileCopyrightText: 2026 OpenAI
// SPDX-License-Identifier: CC-BY-NC-ND-4.0

#include "choco_runner.h"

#include "controller.h"
#include "core.h"
#include "cpu_core.h"
#include "digital_controller.h"
#include "fullscreenui.h"
#include "system.h"

#include "common/error.h"
#include "common/log.h"

#include <array>
#include <algorithm>
#include <charconv>
#include <cstdio>
#include <fstream>
#include <numeric>
#include <string>
#include <string_view>

#include <fmt/format.h>

LOG_CHANNEL(System);

namespace ChocoRunner {
namespace {

// The Lua reference writes PSX RAM offsets 0x51568 and 0x95DC8 before pressing
// Circle to enter the betting screen. DuckStation uses the KSEG0 alias here.
constexpr u32 FRAME_COUNTER_ADDRESS = 0x80051568;
constexpr u32 COURSE_LENGTH_ADDRESS = 0x80095DC8;
constexpr u32 CHOCOBO_RACER_BASE = 0x800B7654;
constexpr u32 CHOCOBO_RACER_STRIDE = 0xA4;
constexpr u32 RACER_COUNT = 6;
constexpr u32 RACER_STATUS_BASE = 0x800B763C;
constexpr u32 BETTING_SCREEN_CONFIRM_FRAMES = 5;
constexpr u32 AUTO_RACE_START_FRAMES = 10;
constexpr u32 FRAME_CYCLE = 0x400000;

enum class Stage : u8
{
  NotStarted,
  OpeningBettingScreen,
  WaitingForStats,
  StartingRace,
  AwaitingRaceFinish,
  Finished,
  Disabled
};

struct PatchState
{
  bool initialized = false;
  Stage stage = Stage::NotStarted;
  u32 frame_value = 0;
  u32 target_frame = 0;
  u32 frame_offset = 0;
  u32 frames_until_capture = 0;
  u32 capture_delay_frames = 100;
  u32 auto_start_delay_frames = 595;
  u32 betting_screen_frames = 0;
  u32 race_start_frames = 0;
  u32 race_frames = 0;
  u32 course_value = 0;
  bool auto_run = false;
  bool run_both_courses = false;
  bool exit_after_capture = false;
  bool export_enabled = false;
  bool restore_fast_forward = false;
  u32 races_completed = 0;
  std::string state_path;
  std::string export_path;
};

PatchState s_patch;

void SetControllerButtons(u32 bits)
{
  Controller* controller = System::GetController(0);
  if (!controller)
    return;

  for (u32 button = 0; button < static_cast<u32>(DigitalController::Button::Count); button++)
  {
    const bool pressed = (bits & (u32(1) << button)) != 0;
    controller->SetBindState(button, pressed ? 1.0f : 0.0f);
  }
}

bool WriteCourseLengthValue(u32 width, u32 value)
{
  switch (width)
  {
    case 0:
      return true;
    case 1:
      return CPU::SafeWriteMemoryByte(COURSE_LENGTH_ADDRESS, static_cast<u8>(value));
    case 2:
      return CPU::SafeWriteMemoryHalfWord(COURSE_LENGTH_ADDRESS, static_cast<u16>(value));
    case 4:
      return CPU::SafeWriteMemoryWord(COURSE_LENGTH_ADDRESS, value);
    default:
      return false;
  }
}

bool ReadCourseLengthWord(u32* value)
{
  return CPU::SafeReadMemoryWord(COURSE_LENGTH_ADDRESS, value);
}

void FinishWithError(const std::string& message)
{
  ERROR_LOG("Chocobo memory patch: {}", message);
  SetControllerButtons(0);
  if (s_patch.restore_fast_forward)
  {
    System::SetFastForwardEnabled(false);
    s_patch.restore_fast_forward = false;
  }
  s_patch.stage = Stage::Finished;
  if (System::IsRunning())
    System::PauseSystem(true);
}

std::string DecodeRacerName(u32 address)
{
  // Same character table used by ml/race.lua's decodeName().
  static constexpr std::string_view char_map =
    R"( !"#$%&'()*+,-./0123456789:;<=>?@ABCDEFGHIJKLMNOPQRSTUVWXYZ[\]^_`abcdefghijklmnopqrstuvwxyz{|}~)";

  std::string name;
  name.reserve(6);
  for (u32 offset = 0; offset < 6; offset++)
  {
    u8 value = 0;
    if (!CPU::SafeReadMemoryByte(address + offset, &value))
      return "<unreadable>";
    if (value == 0xFF)
      continue;

    name.push_back(value < char_map.size() ? char_map[value] : char_map[0]);
  }

  return name;
}

struct RacerData
{
  std::string name;
  u16 top_speed = 0;
  u16 stamina = 0;
  u8 jockey = 0;
  u8 sprint = 0;
  u8 finish_order = 0;
  u8 position = 0;
  bool speed_ok = false;
  bool stamina_ok = false;
  bool jockey_ok = false;
  bool sprint_ok = false;
  bool finish_order_ok = false;
  bool position_ok = false;
};

const char* GetJockeyColorName(u8 jockey_type)
{
  static constexpr std::array<const char*, 4> names = {"Silver", "Gold", "Bronze", "Platinum"};
  return jockey_type < names.size() ? names[jockey_type] : "Unknown";
}

const char* GetCourseName()
{
  // Class C's checkpoint always runs the short course, even with the Lua value 0.
  if (s_patch.state_path.find("_2.sav") != std::string::npos || s_patch.course_value == 6)
    return "Short";
  return "Long";
}

std::string JsonEscape(std::string_view value)
{
  std::string result;
  result.reserve(value.size());
  for (const char ch : value)
  {
    if (ch == '"' || ch == '\\')
      result.push_back('\\');
    if (static_cast<unsigned char>(ch) >= 0x20)
      result.push_back(ch);
  }
  return result;
}

void CaptureRacerStats()
{
  INFO_LOG("Chocobo stats captured after race finish (patched frame {}).", s_patch.frame_value);
  std::array<RacerData, RACER_COUNT> racers;
  for (u32 i = 0; i < RACER_COUNT; i++)
  {
    const u32 base = CHOCOBO_RACER_BASE + i * CHOCOBO_RACER_STRIDE;
    RacerData& racer = racers[i];
    racer.speed_ok = CPU::SafeReadMemoryHalfWord(base - 48, &racer.top_speed);
    racer.stamina_ok = CPU::SafeReadMemoryHalfWord(base - 28, &racer.stamina);
    racer.jockey_ok = CPU::SafeReadMemoryByte(base - 130, &racer.jockey);
    racer.sprint_ok = CPU::SafeReadMemoryByte(base - 60, &racer.sprint);
    racer.finish_order_ok = CPU::SafeReadMemoryByte(base - 24, &racer.finish_order);
    racer.position_ok = CPU::SafeReadMemoryByte(base - 6, &racer.position);
    racer.name = DecodeRacerName(base);

    INFO_LOG("Racer {}: name={}, speed_raw={} display_speed={}, stamina_raw={} display_stamina={}, "
             "jockey_type={}, sprint_flag={}, finish_order={}, position={} "
             "(reads: speed={}, stamina={}, jockey={}, sprint={}, finish_order={}, position={}).",
             i + 1, racer.name,
             racer.speed_ok ? fmt::format("{}", racer.top_speed) : "unreadable",
             racer.speed_ok ? fmt::format("{}", racer.top_speed / 34) : "unreadable",
             racer.stamina_ok ? fmt::format("{}", racer.stamina) : "unreadable",
             racer.stamina_ok ? fmt::format("{}", racer.stamina / 20) : "unreadable",
             racer.jockey_ok ? fmt::format("{}", racer.jockey) : "unreadable",
             racer.sprint_ok ? fmt::format("0x{:02X}", racer.sprint) : "unreadable",
             racer.finish_order_ok ? fmt::format("{}", racer.finish_order) : "unreadable",
             racer.position_ok ? fmt::format("{}", racer.position) : "unreadable",
             racer.speed_ok, racer.stamina_ok, racer.jockey_ok, racer.sprint_ok,
             racer.finish_order_ok, racer.position_ok);
  }

  std::array<u32, RACER_COUNT> finish_order_indices;
  std::iota(finish_order_indices.begin(), finish_order_indices.end(), 0);
  std::sort(finish_order_indices.begin(), finish_order_indices.end(), [&racers](u32 lhs, u32 rhs) {
    if (racers[lhs].finish_order_ok && racers[rhs].finish_order_ok &&
        racers[lhs].finish_order != racers[rhs].finish_order)
      return racers[lhs].finish_order < racers[rhs].finish_order;
    if (racers[lhs].finish_order_ok != racers[rhs].finish_order_ok)
      return racers[lhs].finish_order_ok;
    return lhs < rhs;
  });

  const RacerData* winner = nullptr;
  for (const u32 i : finish_order_indices)
  {
    if (racers[i].finish_order_ok && racers[i].finish_order == 1)
    {
      winner = &racers[i];
      break;
    }
  }

  std::printf("\n%s race results (race %u): target frame %u (patched %u, offset +%u)\n",
              GetCourseName(), s_patch.races_completed, s_patch.target_frame, s_patch.frame_value,
              s_patch.frame_offset);
  if (winner)
    std::printf("Winner (%s): %s\n", GetCourseName(), winner->name.c_str());
  else
    std::printf("Winner (%s): unavailable (finish-order field was unreadable)\n", GetCourseName());
  for (const u32 i : finish_order_indices)
  {
    const RacerData& racer = racers[i];
    if (racer.position_ok)
    {
      std::printf("%u. %s | speed %u km | stamina %u | jockey %s (AI %u) | sprinting %s | end position (%u)\n",
                  racer.finish_order_ok ? racer.finish_order : (i + 1), racer.name.c_str(),
                  racer.speed_ok ? racer.top_speed / 34 : 0,
                  racer.stamina_ok ? racer.stamina / 20 : 0,
                  racer.jockey_ok ? GetJockeyColorName(racer.jockey) : "unknown",
                  racer.jockey_ok ? static_cast<unsigned>(racer.jockey + 1) : 0,
                  racer.sprint_ok && racer.sprint != 0 ? "yes" : "no",
                  static_cast<unsigned>(racer.position));
    }
    else
    {
      std::printf("%u. %s | speed %u km | stamina %u | jockey %s (AI %u) | sprinting %s | end position (unavailable)\n",
                  racer.finish_order_ok ? racer.finish_order : (i + 1), racer.name.c_str(),
                  racer.speed_ok ? racer.top_speed / 34 : 0,
                  racer.stamina_ok ? racer.stamina / 20 : 0,
                  racer.jockey_ok ? GetJockeyColorName(racer.jockey) : "unknown",
                  racer.jockey_ok ? static_cast<unsigned>(racer.jockey + 1) : 0,
                  racer.sprint_ok && racer.sprint != 0 ? "yes" : "no");
    }
  }
  const RacerData* first_place = nullptr;
  const RacerData* second_place = nullptr;
  for (const RacerData& racer : racers)
  {
    if (!racer.finish_order_ok)
      continue;
    if (racer.finish_order == 1)
      first_place = &racer;
    else if (racer.finish_order == 2)
      second_place = &racer;
  }
  if (first_place && second_place)
  {
    const u32 first_chocobo = static_cast<u32>(first_place - racers.data()) + 1;
    const u32 second_chocobo = static_cast<u32>(second_place - racers.data()) + 1;
    std::printf("Top two winners (%s race): Chocobo %u and Chocobo %u (%u-%u)\n",
                GetCourseName(), first_chocobo, second_chocobo, first_chocobo, second_chocobo);
  }
  else
  {
    std::printf("Top two winners (%s race): unavailable\n", GetCourseName());
  }
  std::fflush(stdout);

  if (!s_patch.export_enabled)
    return;

  std::ofstream output(s_patch.export_path, std::ios::out | std::ios::app);
  if (!output)
  {
    ERROR_LOG("Could not append Chocobo race export to '{}'.", s_patch.export_path);
    return;
  }

  output << fmt::format("{{\"race_number\":{},\"course\":\"{}\",\"winner\":{},"
                        "\"target_frame\":{},\"patched_frame\":{},\"frame_offset\":{},"
                        "\"course_value\":{},\"state_file\":\"{}\",\"racers\":[",
                        s_patch.races_completed, GetCourseName(),
                        winner ? fmt::format("\"{}\"", JsonEscape(winner->name)) : "null",
                        s_patch.target_frame, s_patch.frame_value, s_patch.frame_offset,
                        s_patch.course_value, JsonEscape(s_patch.state_path));
  for (u32 i = 0; i < RACER_COUNT; i++)
  {
    const RacerData& racer = racers[i];
    if (i != 0)
      output << ',';
    output << fmt::format("{{\"racer\":{},\"name\":\"{}\",\"top_speed_raw\":{},"
                          "\"top_speed\":{},\"stamina_raw\":{},\"stamina\":{},"
                          "\"jockey_type\":{},\"jockey_color\":\"{}\",\"sprint_flag\":{},"
                          "\"finish_order\":{},\"position\":{}}}",
                          i + 1, JsonEscape(racer.name),
                          racer.speed_ok ? fmt::format("{}", racer.top_speed) : "null",
                          racer.speed_ok ? fmt::format("{}", racer.top_speed / 34) : "null",
                          racer.stamina_ok ? fmt::format("{}", racer.stamina) : "null",
                          racer.stamina_ok ? fmt::format("{}", racer.stamina / 20) : "null",
                          racer.jockey_ok ? fmt::format("{}", racer.jockey) : "null",
                          racer.jockey_ok ? GetJockeyColorName(racer.jockey) : "Unknown",
                          racer.sprint_ok ? fmt::format("{}", racer.sprint) : "null",
                          racer.finish_order_ok ? fmt::format("{}", racer.finish_order) : "null",
                          racer.position_ok ? fmt::format("{}", racer.position) : "null");
  }
  output << "]}\n";
  INFO_LOG("Appended race data export to '{}'.", s_patch.export_path);
}

bool ReloadCheckpointForCourse(u32 course_value)
{
  Error error;
  const std::optional<bool> loaded = System::LoadState(s_patch.state_path.c_str(), &error, false, false);
  if (!loaded.has_value() || !loaded.value())
  {
    FinishWithError(fmt::format("failed to reload '{}' for the second course{}{}", s_patch.state_path,
                                error.IsValid() ? ": " : "", error.GetDescription()));
    return false;
  }
  if (!CPU::SafeWriteMemoryWord(FRAME_COUNTER_ADDRESS, s_patch.frame_value) ||
      !WriteCourseLengthValue(1, course_value))
  {
    FinishWithError(fmt::format("couldn't patch frame {} and course {} for the second race.",
                                s_patch.frame_value, course_value));
    return false;
  }

  s_patch.course_value = course_value;
  s_patch.betting_screen_frames = 0;
  s_patch.frames_until_capture = s_patch.capture_delay_frames;
  s_patch.race_start_frames = 0;
  s_patch.race_frames = 0;
  s_patch.stage = Stage::OpeningBettingScreen;
  SetControllerButtons(u32(1) << static_cast<u32>(DigitalController::Button::Circle));
  INFO_LOG("Reloaded checkpoint for the {} race at target frame {}; course value {}. Opening betting screen.",
           GetCourseName(), s_patch.target_frame, course_value);
  return true;
}

void ApplyPatch()
{
  const std::string state_path = Core::GetBaseStringSettingValue("ChocoPatch", "StateFile", "");
  const bool use_target_frame = Core::GetBaseBoolSettingValue("ChocoPatch", "UseTargetFrame", false);
  const u32 configured_target_frame = Core::GetBaseUIntSettingValue("ChocoPatch", "TargetFrame", 0);
  const u32 legacy_frame_value = Core::GetBaseUIntSettingValue("ChocoPatch", "FrameValue", 0);
  const u32 course_width = Core::GetBaseUIntSettingValue("ChocoPatch", "CourseLengthWriteWidth", 0);
  const u32 course_value = Core::GetBaseUIntSettingValue("ChocoPatch", "CourseLengthValue", 0);
  const u32 capture_delay = Core::GetBaseUIntSettingValue("ChocoPatch", "CaptureDelayFrames", 100);
  const u32 auto_start_delay = Core::GetBaseUIntSettingValue("ChocoPatch", "AutoStartDelayFrames", 595);
  const bool auto_run = Core::GetBaseBoolSettingValue("ChocoPatch", "AutoRun", false);
  const bool run_both_courses = Core::GetBaseBoolSettingValue("ChocoPatch", "RunBothCourses", false);
  const bool exit_after_capture = Core::GetBaseBoolSettingValue("ChocoPatch", "ExitAfterCapture", false);
  const std::string frame_offset_setting = Core::GetBaseStringSettingValue("ChocoPatch", "FrameOffset", "auto");
  const std::string export_path = Core::GetBaseStringSettingValue("ChocoPatch", "ExportPath", "");

  if (state_path.empty())
  {
    FinishWithError("set StateFile in the [ChocoPatch] section of settings.ini.");
    return;
  }
  if (course_width != 0 && course_width != 1 && course_width != 2 && course_width != 4)
  {
    FinishWithError("CourseLengthWriteWidth must be 0 (unchanged), 1, 2, or 4 bytes.");
    return;
  }
  if (run_both_courses && (course_width != 1 || (course_value != 0 && course_value != 6)))
  {
    FinishWithError("RunBothCourses requires a one-byte CourseLengthValue of 0 or 6.");
    return;
  }
  if (run_both_courses && state_path.find("_2.sav") != std::string::npos)
  {
    FinishWithError("Class C always runs short and cannot run both course lengths.");
    return;
  }
  if (run_both_courses && !auto_run)
  {
    FinishWithError("RunBothCourses requires AutoRun=true.");
    return;
  }

  u32 frame_offset = 0;
  if (frame_offset_setting == "auto")
  {
    // Calibration so far: C/B/A = +63; S = +64 from written frame to generated seed.
    frame_offset = (state_path.find("_5.sav") != std::string::npos) ? 64 : 63;
  }
  else
  {
    const char* begin = frame_offset_setting.data();
    const char* end = begin + frame_offset_setting.size();
    const auto parse_result = std::from_chars(begin, end, frame_offset);
    if (parse_result.ec != std::errc{} || parse_result.ptr != end)
    {
      FinishWithError("FrameOffset must be 'auto' or an unsigned integer.");
      return;
    }
  }

  const u32 target_frame = use_target_frame ? configured_target_frame : (legacy_frame_value + frame_offset) % FRAME_CYCLE;
  if (target_frame >= FRAME_CYCLE)
  {
    FinishWithError(fmt::format("TargetFrame must be less than the {}-frame cycle.", FRAME_CYCLE));
    return;
  }
  const u32 frame_value = use_target_frame ? (target_frame + FRAME_CYCLE - (frame_offset % FRAME_CYCLE)) % FRAME_CYCLE : legacy_frame_value;

  Error error;
  const std::optional<bool> loaded = System::LoadState(state_path.c_str(), &error, false, false);
  if (!loaded.has_value() || !loaded.value())
  {
    FinishWithError(fmt::format("failed to load '{}'{}{}", state_path,
                                error.IsValid() ? ": " : "", error.GetDescription()));
    return;
  }

  u32 original_frame = 0;
  u32 original_course_word = 0;
  const bool read_frame = CPU::SafeReadMemoryWord(FRAME_COUNTER_ADDRESS, &original_frame);
  const bool read_course = ReadCourseLengthWord(&original_course_word);

  if (!CPU::SafeWriteMemoryWord(FRAME_COUNTER_ADDRESS, frame_value))
  {
    FinishWithError(fmt::format("couldn't write frame value {} to 0x{:08X}.", frame_value,
                                FRAME_COUNTER_ADDRESS));
    return;
  }
  if (!WriteCourseLengthValue(course_width, course_value))
  {
    FinishWithError(fmt::format("couldn't write course value {} ({} bytes) to 0x{:08X}.",
                                course_value, course_width, COURSE_LENGTH_ADDRESS));
    return;
  }

  u32 patched_frame = 0;
  u32 patched_course_word = 0;
  const bool read_patched_frame = CPU::SafeReadMemoryWord(FRAME_COUNTER_ADDRESS, &patched_frame);
  const bool read_patched_course = ReadCourseLengthWord(&patched_course_word);
  INFO_LOG("Chocobo checkpoint loaded. Target race frame {}; frame 0x{:08X}: {} -> {} (readback {}; offset +{}). Course word at "
           "0x{:08X}: {} -> {} ({}-byte course write; value {}). Opening betting screen with Circle.",
           target_frame,
           FRAME_COUNTER_ADDRESS,
           read_frame ? fmt::format("0x{:08X}", original_frame) : "unreadable", frame_value,
           read_patched_frame ? fmt::format("0x{:08X}", patched_frame) : "unreadable",
           frame_offset,
           COURSE_LENGTH_ADDRESS,
           read_course ? fmt::format("0x{:08X}", original_course_word) : "unreadable",
           read_patched_course ? fmt::format("0x{:08X}", patched_course_word) : "unreadable",
           course_width, course_value);

  s_patch.frame_value = frame_value;
  s_patch.target_frame = target_frame;
  s_patch.frame_offset = frame_offset;
  s_patch.course_value = course_value;
  s_patch.state_path = state_path;
  s_patch.auto_run = auto_run;
  s_patch.run_both_courses = run_both_courses;
  s_patch.races_completed = 0;
  s_patch.exit_after_capture = exit_after_capture;
  s_patch.export_path = export_path;
  s_patch.export_enabled = !export_path.empty();
  s_patch.capture_delay_frames = capture_delay;
  s_patch.frames_until_capture = capture_delay;
  s_patch.auto_start_delay_frames = auto_start_delay;
  s_patch.betting_screen_frames = 0;
  s_patch.stage = Stage::OpeningBettingScreen;
  SetControllerButtons(u32(1) << static_cast<u32>(DigitalController::Button::Circle));
}

} // namespace

bool IsHeadlessEnabled()
{
  return Core::GetBaseBoolSettingValue("ChocoPatch", "Headless", false);
}

void OnFrame()
{
  if (!s_patch.initialized)
  {
    s_patch.initialized = true;
    if (!Core::GetBaseBoolSettingValue("ChocoPatch", "Enabled", false))
    {
      s_patch.stage = Stage::Disabled;
      return;
    }

    s_patch.stage = Stage::NotStarted;
    INFO_LOG("Chocobo checkpoint patch is armed; it will load the configured state and generate its betting screen.");
  }

  if (s_patch.stage == Stage::NotStarted && System::IsRunning())
  {
    ApplyPatch();
    return;
  }

  if (s_patch.stage == Stage::OpeningBettingScreen)
  {
    s_patch.betting_screen_frames++;
    if (s_patch.betting_screen_frames >= BETTING_SCREEN_CONFIRM_FRAMES)
    {
      SetControllerButtons(0);
      s_patch.stage = Stage::WaitingForStats;
      if (s_patch.auto_run)
      {
        s_patch.frames_until_capture = s_patch.auto_start_delay_frames;
        s_patch.restore_fast_forward = !System::IsFastForwardEnabled();
        if (s_patch.restore_fast_forward)
          System::SetFastForwardEnabled(true);
        INFO_LOG("Betting screen opened. Fast-forwarding {} frames to the automatic Start input.",
                 s_patch.frames_until_capture);
        INFO_LOG("Betting screen confirm sent for {} frames.", BETTING_SCREEN_CONFIRM_FRAMES);
      }
      else
      {
        INFO_LOG("Betting screen confirm sent for {} frames; waiting {} frames before reading generated racers.",
                 BETTING_SCREEN_CONFIRM_FRAMES, s_patch.frames_until_capture);
      }
    }
    return;
  }

  if (s_patch.stage == Stage::WaitingForStats && s_patch.frames_until_capture > 0)
  {
    s_patch.frames_until_capture--;
    if (s_patch.frames_until_capture == 0)
    {
      SetControllerButtons(0);
      if (s_patch.auto_run)
      {
        s_patch.stage = Stage::StartingRace;
        s_patch.race_start_frames = 0;
        SetControllerButtons(u32(1) << static_cast<u32>(DigitalController::Button::Start));
        INFO_LOG("Betting screen is ready. Auto-starting race with Start.");
      }
      else
      {
        s_patch.stage = Stage::AwaitingRaceFinish;
        s_patch.race_frames = 0;
        INFO_LOG("Betting screen is ready. Start the race manually; racer memory will be captured when it finishes.");
        System::PauseSystem(true);
      }
    }
    return;
  }

  if (s_patch.stage == Stage::StartingRace)
  {
    s_patch.race_start_frames++;
    if (s_patch.race_start_frames >= AUTO_RACE_START_FRAMES)
    {
      SetControllerButtons(0);
      s_patch.stage = Stage::AwaitingRaceFinish;
      s_patch.race_frames = 0;
      INFO_LOG("Race start held with Start for {} frames; waiting for finish status.", AUTO_RACE_START_FRAMES);
    }
    return;
  }

  if (s_patch.stage == Stage::AwaitingRaceFinish && System::IsRunning())
  {
    bool race_finished = false;
    for (u32 i = 0; i < RACER_COUNT; i++)
    {
      u8 status = 0;
      if (CPU::SafeReadMemoryByte(RACER_STATUS_BASE + i * CHOCOBO_RACER_STRIDE, &status) && status == 6)
      {
        race_finished = true;
        break;
      }
    }

    if (race_finished)
    {
      s_patch.races_completed++;
      CaptureRacerStats();
      if (s_patch.run_both_courses && s_patch.races_completed == 1)
      {
        const u32 other_course_value = (s_patch.course_value == 6) ? 0 : 6;
        ReloadCheckpointForCourse(other_course_value);
        return;
      }
      if (s_patch.restore_fast_forward)
      {
        System::SetFastForwardEnabled(false);
        s_patch.restore_fast_forward = false;
      }
      s_patch.stage = Stage::Finished;
      if (s_patch.exit_after_capture)
      {
        INFO_LOG("Race capture complete. Closing DuckStation as configured.");
        Host::RequestExitApplication(false);
      }
      else
      {
        System::PauseSystem(true);
      }
    }
    else if (++s_patch.race_frames == 60 * 60 * 3)
    {
      ERROR_LOG("Chocobo memory capture timed out before a finish status appeared.");
      s_patch.stage = Stage::Finished;
      System::PauseSystem(true);
    }
  }
}

} // namespace ChocoRunner
