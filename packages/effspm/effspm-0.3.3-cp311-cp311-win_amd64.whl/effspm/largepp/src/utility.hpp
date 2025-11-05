#pragma once
#include <vector>
#include <ctime>
#include <string>

namespace largepp {

// Flag & option globals (only declare here – actual values in utility.cpp)
extern bool b_disp, b_write, use_dic, just_build, ovr_count, pre_pro;
extern bool use_list;                  // ← NEW (large-prefix needs this)
extern unsigned int time_limit;

// Pattern buffer that _effspm.cpp_ returns to Python
extern std::vector<std::vector<int>> collected;

// Helper functions every source file uses
void ClearCollected();                                   // wipe buffer
const std::vector<std::vector<int>>& GetCollected();     // read buffer
double give_time(std::clock_t ticks);                    // secs from clocks

} // namespace largepp
