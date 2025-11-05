#pragma once

#include <vector>
#include <time.h>
#include <string>
#include "build_mdd.hpp"

namespace htminer {

using std::vector;

float give_time(clock_t kk);
bool check_parent(unsigned int cur_arc, unsigned int str_pnt,
                  unsigned int start, vector<unsigned int>& strpnt_vec);

// pattern collection for Python
extern vector<vector<int>> collectedPatterns;

void ClearCollected();
const vector<vector<int>>& GetCollected();

} // namespace htminer
