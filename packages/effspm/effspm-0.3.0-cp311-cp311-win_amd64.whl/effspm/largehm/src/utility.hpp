#pragma once

#include <vector>
#include <time.h>
#include <string>
#include "build_mdd.hpp"

namespace largehm {
using namespace std;

  extern std::vector<std::vector<int>> collected;

  // Helpers to clear and fetch collected patterns from Python:
  inline void ClearCollected() {
    collected.clear();
  }
  inline const std::vector<std::vector<int>>& GetCollected() {
    return collected;
  }

  // A small timer helper:
  inline float give_time(clock_t kk) {
    float ll = ((float)kk) / CLOCKS_PER_SEC;
    return ll;
  }
bool check_parent(unsigned long long int cur_anct, unsigned long long int str_pnt, unsigned long long int start, vector<unsigned long long int>& strpnt_vec);


}