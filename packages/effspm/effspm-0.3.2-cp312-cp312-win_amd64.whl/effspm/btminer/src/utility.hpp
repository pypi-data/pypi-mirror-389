#pragma once

#include <vector>
#include <time.h>
#include <string>
#include "build_mdd.hpp"

namespace btminer {

using std::vector;

int   find_ID(vector<int>& vec, int itm);
float give_time(clock_t kk);
bool  check_parent(int cur_arc, int str_pnt, int start, vector<int>& strpnt_vec);

} // namespace btminer
