#pragma once
#include <vector>
#include <ctime>

namespace largebm {

double give_time(std::clock_t ticks);

// Check if `str_pnt` is an ancestor of `cur_arc` respecting itemset boundaries
bool check_parent(unsigned long long cur_arc,
                  unsigned long long str_pnt,
                  unsigned long long start,
                  std::vector<unsigned long long>& strpnt_vec);

} // namespace largebm
