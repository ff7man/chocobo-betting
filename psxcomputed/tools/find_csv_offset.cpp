#include <array>
#include <cstdint>
#include <fstream>
#include <iostream>
#include <sstream>
#include <string>
#include <vector>

struct Stats { int dash, speed, stamina, jockey, sprint; };
struct Row { int dash, stamina, jockey, sprint; std::string name; };

static constexpr std::array<const char*, 43> NAMES = {
  "SAM","ELEN","BLUES","TOM","JOHN","GARY","MIKE","SANDY","JU","LY","JOEL","GREY",
  "EDWARD","JAMES","HARVEY","DAN","RUDY","GRAHAM","FOX","CLIVE","SEAN","YOUNG","ROBIN",
  "DARIO","ARL","SARA","MARIE","SAMMY","LIA","KNIGHT","PAULA","PAU","LE","PETER","AIMEE",
  "TERRY","ANDY","NANCY","TIM","ROBER","GEORGE","JENNY","RICA"};

static std::vector<std::string> Split(const std::string& s)
{
  std::vector<std::string> out;
  std::stringstream ss(s);
  std::string part;
  while (std::getline(ss, part, ',')) out.push_back(part);
  return out;
}

static uint32_t Next(uint32_t& state)
{
  state = state * 0x41C64E6Du + 0x3039u;
  return (state >> 16) & 0x7FFFu;
}

static bool ParseHex(const std::string& text, int* value)
{
  try { *value = std::stoi(text, nullptr, 16); return true; }
  catch (...) { return false; }
}

int main(int argc, char** argv)
{
  if (argc != 3 && argc != 5) { std::cerr << "Usage: find_csv_offset <rank.csv> <C|B|A|S> [csv-frame random]\n"; return 2; }
  const std::string rank = argv[2];
  int dash_base, dash_range, speed_base, speed_range;
  if (rank == "C" || rank == "c") { dash_base=0x09c4; dash_range=0x01f4; speed_base=0x06a4; speed_range=0x00c8; }
  else if (rank == "B" || rank == "b") { dash_base=0x0bb8; dash_range=0x0258; speed_base=0x0898; speed_range=0x012c; }
  else if (rank == "A" || rank == "a") { dash_base=0x0dac; dash_range=0x02bc; speed_base=0x0bb8; speed_range=0x01f4; }
  else if (rank == "S" || rank == "s") { dash_base=0x1388; dash_range=0x0320; speed_base=0x0fa0; speed_range=0x01f4; }
  else { std::cerr << "rank must be C, B, A, or S\n"; return 2; }

  std::ifstream input(argv[1]);
  std::string line;
  std::getline(input, line);
  const int requested_frame = argc == 5 ? std::stoi(argv[3]) : -1;
  const int requested_random = argc == 5 ? std::stoi(argv[4]) : -1;
  std::array<Row, 6> rows{};
  int count=0, csv_frame=-1;
  while (std::getline(input, line))
  {
    auto c=Split(line);
    if (c.size()!=18 || c[15] != (rank=="C"||rank=="c"?"c":rank=="B"||rank=="b"?"b":rank=="A"||rank=="a"?"a":"s")) continue;
    if (requested_frame >= 0 && (std::stoi(c[16]) != requested_frame || std::stoi(c[17]) != requested_random)) continue;
    if (count == 6) break;
    int sprint=0, jockey=0;
    if (!ParseHex(c[9], &sprint) || !ParseHex(c[11], &jockey)) continue;
    rows[count++] = {std::stoi(c[1]), std::stoi(c[7]), jockey, sprint, c[14]};
    csv_frame=std::stoi(c[16]);
  }
  if (count!=6) { std::cerr << "Could not read first six racer rows from " << argv[1] << "\n"; return 1; }
  constexpr uint32_t cycle=0x400000;
  int matches=0;
  for (uint32_t seed=0; seed<cycle; seed++)
  {
    uint32_t state=seed;
    for (int i=0;i<0x28;i++) { Next(state); Next(state); }
    std::array<Stats,6> expected{};
    bool stats_match=true;
    for (int i=0;i<6;i++)
    {
      Stats& x=expected[i];
      x.dash=dash_base+(Next(state)%dash_range);
      x.speed=speed_base+(Next(state)%speed_range);
      x.jockey=Next(state)%4;
      x.stamina=dash_base+(Next(state)%300);
      x.sprint=((Next(state)&7)==0)?2:0;
      Next(state); // unknown stat
      if (x.dash!=rows[i].dash || x.stamina*2!=rows[i].stamina ||
          x.jockey!=rows[i].jockey || x.sprint!=rows[i].sprint)
        stats_match=false;
    }
    if (!stats_match) continue;

    std::array<int,43> names{};
    for (int i=0;i<43;i++) names[i]=i;
    for (int i=0;i<0xc8;i++)
    {
      const int a=Next(state)%43, b=Next(state)%43;
      std::swap(names[a],names[b]);
    }
    bool names_match=true;
    for (int i=0;i<6;i++) if (rows[i].name!=NAMES[names[i]]) names_match=false;
    if (!names_match) continue;

    const uint32_t offset=(seed + cycle - (static_cast<uint32_t>(csv_frame)%cycle))%cycle;
    std::cout << "match seed=" << seed << " csv_frame=" << csv_frame << " offset=" << offset << "\n";
    matches++;
  }
  std::cout << "matches=" << matches << "\n";
  return matches ? 0 : 1;
}
