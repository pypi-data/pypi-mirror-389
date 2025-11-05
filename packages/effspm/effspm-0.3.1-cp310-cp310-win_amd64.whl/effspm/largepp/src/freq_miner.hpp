#pragma once

#include <vector>
#include <string>

#include "pattern.hpp"   // defines largepp::Pattern
#include "load_inst.hpp" // declares externs: items, L, theta, DFS, etc.
#include "utility.hpp"   // flags, collected buffer, timers, helpers

namespace largepp {

// Public entry point
void Freq_miner();

// (defined in the .cpp)
extern unsigned long long int num_patt;

} // namespace largepp
