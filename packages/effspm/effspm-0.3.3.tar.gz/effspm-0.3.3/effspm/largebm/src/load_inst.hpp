#pragma once
#include <vector>
#include <string>
#include <ctime>

namespace largebm {

class Pattern; // forward
// [2025-10-25 NEW]: match the real definition (class, not struct) to avoid ABI warnings
class Arc;     // was: struct Arc;

// Config & state (single definitions in load_inst.cpp)
extern std::string        out_file, folder;
extern bool               use_list;
extern bool               b_disp, b_write, use_dic, just_build, pre_pro, itmset_exists;
extern unsigned int       M, L, time_limit;
extern unsigned long long N, num_nodes, theta, E;
extern std::clock_t       start_time;

extern std::vector<std::vector<int>> items;
extern std::vector<int>              item_dic;
extern std::vector<int>              inv_item_dic;
extern std::vector<Pattern>          DFS;
extern std::vector<std::vector<int>> collected;

// Loader API
bool Load_instance(const std::string& items_file, double thresh);
bool Preprocess(const std::string& fname, double thresh);
void Load_items_pre(const std::string& fname);
bool Load_items(const std::string& fname);

void ClearCollected();
const std::vector<std::vector<int>>& GetCollected();

} // namespace largebm
