#pragma once

#include <vector>
#include <time.h>
#include <string>
#include "build_mdd.hpp"

namespace largehm {

using std::vector;
using std::string;

// time helper
float give_time(clock_t kk);

// ancestor-check helper
bool check_parent(unsigned long long int cur_anct,
                  unsigned long long int str_pnt,
                  unsigned long long int start,
                  vector<unsigned long long int>& strpnt_vec);

// pattern collection for Python wrapper
extern std::vector<std::vector<int>> collectedPatterns;

// clear collected patterns between runs
void ClearCollected();

// get collected patterns after mining
const std::vector<std::vector<int>>& GetCollected();

} // namespace largehm
